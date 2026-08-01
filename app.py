import os
import csv
import json
import asyncio
import pandas as pd
from typing import List, Dict, Any, Optional, Callable
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

import requests

# Importar cliente LLM y prompts existentes
from cliente_llm import ClienteLLM
from conceptos import CONCEPTOS_POR_PREGUNTA
from prompts import (
    SYSTEM_PROMPT_CONCEPTOS,
    SYSTEM_PROMPT_RANGO,
    SYSTEM_PROMPT_NOTA,
    construir_user_message_conceptos,
    construir_user_message_rango,
    construir_user_message_nota
)
from grading_logic import evaluar_conceptos, evaluar_rango, evaluar_nota_directa, ensamblar_nota_final


app = FastAPI(title="Evaluador Académico UTN-LIS con IA")

# Ruta para la persistencia local de datos
DB_PATH = "documentacion/web_app_db.json"

# Estado de corrección en memoria para reportar progreso en tiempo real
class CorreccionState:
    def __init__(self):
        self.status = "idle"  # idle, running, completed, failed
        self.total = 0
        self.procesado = 0
        self.errores = 0

state = CorreccionState()
state_lock = asyncio.Lock()

# Estado de corrección y comparación en vivo
class ComparacionState:
    def __init__(self):
        self.status = "idle"  # idle, running, completed, failed, cancelled
        self.total = 0
        self.procesado = 0
        self.errores = 0
        self.mae = 0.0
        self.cancel_requested = False

state_comp = ComparacionState()
state_comp_lock = asyncio.Lock()

# Asegurar la creación de la carpeta de documentación
os.makedirs("documentacion", exist_ok=True)

def cargar_db() -> Dict[str, Any]:
    """Carga la base de datos JSON o la inicializa sembrando los datos existentes."""
    if not os.path.exists(DB_PATH):
        preguntas_seed = {}
        
        # 1. Intentar sembrar preguntas desde el dataset_filtrado.csv original
        dataset_csv = "documentacion/dataset_filtrado.csv"
        if os.path.exists(dataset_csv):
            try:
                df = pd.read_csv(dataset_csv)
                for _, row in df.iterrows():
                    q_id = str(row.get("question_id")).strip()
                    if q_id and q_id not in preguntas_seed:
                        preguntas_seed[q_id] = {
                            "question_text": str(row.get("question_text")).strip(),
                            "ideal_answer": str(row.get("ideal_answer", "")).strip(),
                            "conceptos": CONCEPTOS_POR_PREGUNTA.get(q_id, [])
                        }
            except Exception as e:
                print(f"Error sembrando desde dataset: {e}")
                
        # 2. Si no se pudo sembrar, usar conceptos predefinidos como respaldo
        if not preguntas_seed:
            for q_id, conceptos in CONCEPTOS_POR_PREGUNTA.items():
                preguntas_seed[q_id] = {
                    "question_text": f"Pregunta de Referencia {q_id}",
                    "ideal_answer": "Respuesta ideal de la cátedra.",
                    "conceptos": conceptos
                }
                
        db = {
            "preguntas": preguntas_seed,
            "respuestas_cargadas": [],
            "resultados": {},
            "url_llm": os.getenv("URL_LLM", "http://localhost:8000"),
            "proceso_correccion": {
                "status": "idle",
                "total": 0,
                "procesado": 0,
                "errores": 0
            }
        }
        guardar_db(db)
        return db
        
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Asegurar existencia de url_llm
            if "url_llm" not in data:
                load_dotenv()
                data["url_llm"] = os.getenv("URL_LLM", "http://localhost:8000")
                guardar_db(data)
            return data
    except Exception as e:
        print(f"Error cargando db.json: {e}")
        # En caso de corrupción, retornar una estructura base
        return {"preguntas": {}, "respuestas_cargadas": [], "resultados": {}, "url_llm": os.getenv("URL_LLM", "http://localhost:8000"), "proceso_correccion": {"status": "idle", "total": 0, "procesado": 0, "errores": 0}}

def guardar_db(db: Dict[str, Any]):
    """Guarda los datos en el archivo JSON."""
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

# Modelos Pydantic para APIs
class PreguntaManual(BaseModel):
    question_id: str
    question_text: str
    ideal_answer: str
    conceptos: List[Dict[str, str]]  # Lista de {"tag": "...", "descripcion": "..."}

# ----------------- ENDPOINTS DE CONFIGURACIÓN -----------------

class ConfigPayload(BaseModel):
    url_llm: str

async def probar_conexion_llm(url: str) -> bool:
    try:
        # Petición rápida de validación
        res = await asyncio.to_thread(
            requests.post,
            f"{url}/chat",
            json={"messages": [{"role": "user", "content": "ping_test"}]},
            headers={
                "Content-Type": "application/json",
                "ngrok-skip-browser-warning": "69420"
            },
            timeout=45.0
        )
        return res.status_code == 200
    except Exception as e:
        print(f"Error en probar_conexion_llm para URL {url}: {e}")
        return False

@app.get("/api/config")
async def get_config():
    """Devuelve la configuración del entorno para verificar la conexión al LLM."""
    db = cargar_db()
    url_llm = db.get("url_llm")
    if not url_llm:
        load_dotenv()
        url_llm = os.getenv("URL_LLM", "http://localhost:8000")
        
    online = await probar_conexion_llm(url_llm)
    return {
        "url_llm": url_llm,
        "online": online,
        "system_prompts": {
            "conceptos": SYSTEM_PROMPT_CONCEPTOS,
            "rango": SYSTEM_PROMPT_RANGO,
            "nota": SYSTEM_PROMPT_NOTA
        }
    }

@app.post("/api/config")
async def update_config(payload: ConfigPayload):
    """Actualiza la URL de conexión y devuelve el nuevo estado de conexión."""
    db = cargar_db()
    url = payload.url_llm.strip().rstrip("/")
    if not url:
        raise HTTPException(status_code=400, detail="La URL no puede estar vacía.")
        
    db["url_llm"] = url
    guardar_db(db)
    
    # Sincronizar env var para cliente LLM
    os.environ["URL_LLM"] = url
    
    online = await probar_conexion_llm(url)
    return {
        "mensaje": "Configuración guardada correctamente.",
        "url_llm": url,
        "online": online
    }

# ----------------- ENDPOINTS DEL BANCO DE PREGUNTAS -----------------

@app.get("/api/preguntas")
async def get_preguntas():
    db = cargar_db()
    return db.get("preguntas", {})

@app.post("/api/preguntas")
async def add_pregunta(pregunta: PreguntaManual):
    db = cargar_db()
    q_id = pregunta.question_id.strip()
    
    if not q_id:
        raise HTTPException(status_code=400, detail="El identificador de pregunta no puede estar vacío.")
        
    db["preguntas"][q_id] = {
        "question_text": pregunta.question_text.strip(),
        "ideal_answer": pregunta.ideal_answer.strip(),
        "conceptos": pregunta.conceptos
    }
    guardar_db(db)
    return {"mensaje": "Pregunta guardada correctamente.", "question_id": q_id}

@app.post("/api/preguntas/upload")
async def upload_preguntas(file: UploadFile = File(...)):
    """Carga preguntas masivamente desde un CSV."""
    try:
        df = pd.read_csv(file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error leyendo archivo CSV de preguntas: {str(e)}")
        
    required = {"question_id", "question_text"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise HTTPException(status_code=400, detail=f"Faltan columnas requeridas en el CSV de preguntas: {', '.join(missing)}")
        
    db = cargar_db()
    contador = 0
    
    for _, row in df.iterrows():
        q_id = str(row["question_id"]).strip()
        q_text = str(row["question_text"]).strip()
        ideal = str(row.get("ideal_answer", "")).strip()
        
        # Opcionalmente procesar conceptos en formato TAG1:desc1;TAG2:desc2
        conceptos_list = []
        conceptos_raw = str(row.get("conceptos", ""))
        if conceptos_raw and conceptos_raw.lower() != "nan":
            parts = conceptos_raw.split(";")
            for part in parts:
                if ":" in part:
                    tag, desc = part.split(":", 1)
                    conceptos_list.append({
                        "tag": tag.strip(),
                        "descripcion": desc.strip()
                    })
                    
        db["preguntas"][q_id] = {
            "question_text": q_text,
            "ideal_answer": ideal,
            "conceptos": conceptos_list
        }
        contador += 1
        
    guardar_db(db)
    return {"mensaje": f"Se cargaron/actualizaron {contador} preguntas en el banco."}

# ----------------- ENDPOINTS DE CARGA DE EXÁMENES -----------------

@app.post("/api/examenes/upload")
async def upload_examenes(file: UploadFile = File(...)):
    """Sube el CSV de respuestas de los alumnos y lo valida contra el banco de preguntas."""
    try:
        # Usar engine python para evitar fallos por codificación
        df = pd.read_csv(file.file, encoding="utf-8-sig")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error leyendo archivo CSV de respuestas: {str(e)}")
        
    required = {"question_id", "alumno_id", "student_answer"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise HTTPException(status_code=400, detail=f"El CSV no contiene las columnas requeridas: {', '.join(missing)}")
        
    db = cargar_db()
    preguntas_db = db.get("preguntas", {})
    
    errores = []
    respuestas_validas = []
    
    for idx, row in df.iterrows():
        q_id = str(row["question_id"]).strip()
        alumno_id = str(row["alumno_id"]).strip()
        student_ans = str(row["student_answer"]).strip()
        
        # Validar existencia de question_id
        if q_id not in preguntas_db:
            errores.append(f"Fila {idx + 2}: El question_id '{q_id}' no existe en el banco de preguntas cargado.")
        else:
            respuestas_validas.append({
                "question_id": q_id,
                "alumno_id": alumno_id,
                "student_answer": student_ans
            })
            
    if errores:
        return JSONResponse(
            status_code=400,
            content={
                "error": "La validación del CSV falló.",
                "detalles": errores
            }
        )
        
    # Guardar en base de datos
    db["respuestas_cargadas"] = respuestas_validas
    db["resultados"] = {}  # Limpiar resultados anteriores
    db["proceso_correccion"] = {
        "status": "idle",
        "total": len(respuestas_validas),
        "procesado": 0,
        "errores": 0
    }
    guardar_db(db)
    
    # Sincronizar estado en memoria
    async with state_lock:
        state.status = "idle"
        state.total = len(respuestas_validas)
        state.procesado = 0
        state.errores = 0
        
    return {
        "mensaje": "Respuestas subidas y validadas con éxito.",
        "total_respuestas": len(respuestas_validas),
        "total_alumnos": len(df["alumno_id"].unique())
    }

# ----------------- PROCESO DE EVALUACIÓN CON IA (ASÍNCRONO) -----------------

async def corregir_respuesta_individual(
    cliente_llm: ClienteLLM,
    pregunta_text: str,
    conceptos: List[Dict[str, str]],
    respuesta_estudiante: str,
    check_cancellation: Optional[Callable[[], bool]] = None
) -> Dict[str, Any]:
    """Ejecuta los tres experimentos de forma atómica e independiente, y los ensambla en una nota final."""
    if check_cancellation and check_cancellation():
        return {"estado": "cancelado"}

    db = cargar_db()
    pesos = db.get("pesos_ensamble", {"w1": 0.10, "w2": 0.05, "w3": 0.85})
    w1 = pesos.get("w1", 0.10)
    w2 = pesos.get("w2", 0.05)
    w3 = pesos.get("w3", 0.85)


    # Lanzar los tres experimentos atómicos en hilos separados para concurrencia
    task_conceptos = asyncio.to_thread(evaluar_conceptos, cliente_llm, pregunta_text, conceptos, respuesta_estudiante)
    task_rango = asyncio.to_thread(evaluar_rango, cliente_llm, pregunta_text, respuesta_estudiante)
    task_nota_directa = asyncio.to_thread(evaluar_nota_directa, cliente_llm, pregunta_text, respuesta_estudiante)

    res_conceptos, res_rango, res_nota_directa = await asyncio.gather(
        task_conceptos, task_rango, task_nota_directa
    )

    if check_cancellation and check_cancellation():
        return {"estado": "cancelado"}

    # Integrar los resultados utilizando el ensamble ponderado
    res_ensemble = ensamblar_nota_final(
        res_conceptos,
        res_rango,
        res_nota_directa,
        w1=w1,
        w2=w2,
        w3=w3
    )

    tiempo_total = res_conceptos["tiempo"] + res_rango["tiempo"] + res_nota_directa["tiempo"]

    return {
        "conceptos_evaluados": res_conceptos["conceptos_evaluados"],
        "rango_nota": res_rango["rango"],
        "nota_final": res_ensemble["nota_final"],
        "tiempo": round(tiempo_total, 3),
        "estado": "completado",
        "desglose": res_ensemble["desglose"],
        "configuracion": res_ensemble["configuracion"]
    }


async def tarea_correccion_lote():
    """Bucle de ejecución asíncrona con limitación de concurrencia y reintentos robustos."""
    global state
    db = cargar_db()
    url_llm = db.get("url_llm")
    if url_llm:
        os.environ["URL_LLM"] = url_llm
        
    respuestas = db.get("respuestas_cargadas", [])
    preguntas_db = db.get("preguntas", {})
    
    if not respuestas:
        async with state_lock:
            state.status = "idle"
        return
        
    cliente_llm = ClienteLLM()
    resultados_temp = {}
    
    # Semáforo para limitar la concurrencia a un máximo de 3 llamadas paralelas al servidor LLM
    sem = asyncio.Semaphore(3)
    
    async def procesar_item(idx: int, resp: Dict[str, Any]):
        global state
        q_id = resp["question_id"]
        alumno_id = resp["alumno_id"]
        student_ans = resp["student_answer"]
        
        pregunta = preguntas_db.get(q_id, {})
        conceptos = pregunta.get("conceptos", [])
        
        # Lógica de reintentos
        intentos = 3
        resultado = None
        
        for inteno in range(intentos):
            try:
                async with sem:
                    resultado = await corregir_respuesta_individual(
                        cliente_llm,
                        pregunta.get("question_text", f"Pregunta {q_id}"),
                        conceptos,
                        student_ans
                    )
                if resultado["estado"] == "completado":
                    break
            except Exception as e:
                print(f"Error corrigiendo respuesta de {alumno_id} (Intento {inteno+1}): {e}")
                await asyncio.sleep(1) # pausa antes de reintentar
                
        if resultado is None or resultado.get("estado") == "error":
            # Fallback en caso de fallo crítico de conexión persistente
            resultado = {
                "conceptos_evaluados": {},
                "rango_nota": "ERROR_CONEXION",
                "nota_final": 1,
                "tiempo": 0.0,
                "estado": "error",
                "error_msg": "No se obtuvo respuesta del LLM tras varios intentos."
            }
            async with state_lock:
                state.errores += 1
                
        # Agregar metadatos del examen para visualización
        resultado["question_id"] = q_id
        resultado["student_answer"] = student_ans
        resultado["question_text"] = pregunta.get("question_text")
        resultado["ideal_answer"] = pregunta.get("ideal_answer")
        
        # Guardar temporalmente agrupado por alumno
        async with state_lock:
            resultados_temp.setdefault(alumno_id, []).append(resultado)
            state.procesado += 1
            
    # Lanzar todas las tareas concurrentemente bajo el semáforo
    tareas = [procesar_item(i, r) for i, r in enumerate(respuestas)]
    await asyncio.gather(*tareas)
    
    # Una vez finalizado el lote, consolidar en base de datos
    db = cargar_db()
    for alumno_id, respuestas_list in resultados_temp.items():
        db["resultados"][alumno_id] = {
            "respuestas": respuestas_list,
            "promedio": round(sum(r["nota_final"] for r in respuestas_list) / len(respuestas_list), 2) if respuestas_list else 0
        }
        
    db["proceso_correccion"]["status"] = "completed" if state.errores < state.total else "failed"
    db["proceso_correccion"]["total"] = state.total
    db["proceso_correccion"]["procesado"] = state.procesado
    db["proceso_correccion"]["errores"] = state.errores
    guardar_db(db)
    
    async with state_lock:
        state.status = db["proceso_correccion"]["status"]

async def tarea_comparar_correccion_lote():
    """Bucle asíncrono para evaluar y comparar notas en tiempo real."""
    global state_comp
    db = cargar_db()
    url_llm = db.get("url_llm")
    if url_llm:
        os.environ["URL_LLM"] = url_llm
        
    respuestas = db.get("respuestas_comparar", [])
    preguntas_db = db.get("preguntas", {})
    
    if not respuestas:
        async with state_comp_lock:
            state_comp.status = "idle"
        return
        
    cliente_llm = ClienteLLM()
    comparaciones_temp = []
    mae_acumulado = 0.0
    
    # Semáforo para limitar la concurrencia a un máximo de 3 llamadas paralelas al servidor LLM
    sem = asyncio.Semaphore(3)
    
    async def procesar_item(idx: int, resp: Dict[str, Any]):
        global state_comp
        nonlocal mae_acumulado
        if state_comp.cancel_requested:
            return
            
        q_id = resp["question_id"]
        student_ans = resp["student_answer"]
        teacher_grade = resp["teacher_grade"]
        
        pregunta = preguntas_db.get(q_id, {})
        conceptos = pregunta.get("conceptos", [])
        
        intentos = 3
        resultado = None
        
        for inteno in range(intentos):
            if state_comp.cancel_requested:
                return
            try:
                async with sem:
                    resultado = await corregir_respuesta_individual(
                        cliente_llm,
                        pregunta.get("question_text", f"Pregunta {q_id}"),
                        conceptos,
                        student_ans,
                        check_cancellation=lambda: state_comp.cancel_requested
                    )
                if resultado["estado"] == "completado" or resultado.get("estado") == "cancelado":
                    break
            except Exception as e:
                print(f"Error corrigiendo para comparación en vivo (Intento {inteno+1}): {e}")
                await asyncio.sleep(1)
                
        if state_comp.cancel_requested or (resultado is not None and resultado.get("estado") == "cancelado"):
            return
            
        if resultado is None or resultado.get("estado") == "error":
            resultado = {
                "conceptos_evaluados": {},
                "rango_nota": "ERROR_CONEXION",
                "nota_final": 1,
                "tiempo": 0.0,
                "estado": "error",
                "error_msg": "No se obtuvo respuesta del LLM tras varios intentos."
            }
            async with state_comp_lock:
                state_comp.errores += 1
                
        agent_grade = float(resultado["nota_final"])
        diff = agent_grade - teacher_grade
        abs_error = abs(diff)
        
        item_comparado = {
            "question_id": q_id,
            "student_answer": student_ans,
            "student_answer_short": student_ans[:120] + "..." if len(student_ans) > 120 else student_ans,
            "teacher_grade": teacher_grade,
            "agent_grade": agent_grade,
            "diff": round(diff, 2),
            "conceptos_evaluados": resultado.get("conceptos_evaluados", {}),
            "rango_nota": resultado.get("rango_nota", ""),
            "nota_conceptos": resultado.get("desglose", {}).get("experimento_conceptos", {}).get("nota_obtenida", 1.0),
            "nota_rango": resultado.get("desglose", {}).get("experimento_rango", {}).get("nota_obtenida", 1.0),
            "nota_directa": resultado.get("desglose", {}).get("experimento_nota_directa", {}).get("nota_obtenida", 1.0)
        }

        
        async with state_comp_lock:
            comparaciones_temp.append(item_comparado)
            state_comp.procesado += 1
            mae_acumulado += abs_error
            state_comp.mae = round(mae_acumulado / state_comp.procesado, 2)
            
    tareas = [procesar_item(i, r) for i, r in enumerate(respuestas)]
    await asyncio.gather(*tareas)
    
    db = cargar_db()
    status_final = "cancelled" if state_comp.cancel_requested else ("completed" if state_comp.errores < state_comp.total else "failed")
    
    db["resultados_comparacion"] = {
        "comparaciones": comparaciones_temp,
        "total_comparados": len(comparaciones_temp),
        "mae": state_comp.mae if comparaciones_temp else 0.0,
        "status": status_final
    }
    db["proceso_comparacion"] = {
        "status": status_final,
        "total": state_comp.total,
        "procesado": state_comp.procesado,
        "errores": state_comp.errores,
        "mae": state_comp.mae if comparaciones_temp else 0.0
    }
    guardar_db(db)
    
    async with state_comp_lock:
        state_comp.status = status_final

class PesosConfig(BaseModel):
    w1: float
    w2: float
    w3: float

@app.get("/api/config/pesos")
async def obtener_pesos():
    """Obtiene los pesos configurados para el ensamble ponderado."""
    db = cargar_db()
    pesos = db.get("pesos_ensamble", {"w1": 0.10, "w2": 0.05, "w3": 0.85})
    return pesos


@app.post("/api/config/pesos")
async def guardar_pesos(req: PesosConfig):
    """Guarda nuevos pesos para el ensamble ponderado."""
    suma = req.w1 + req.w2 + req.w3
    if abs(suma - 1.0) > 0.01:
        # Normalizar automáticamente si no suman 1.0
        w1 = round(req.w1 / suma, 3)
        w2 = round(req.w2 / suma, 3)
        w3 = round(req.w3 / suma, 3)
    else:
        w1 = req.w1
        w2 = req.w2
        w3 = req.w3

    db = cargar_db()
    db["pesos_ensamble"] = {"w1": w1, "w2": w2, "w3": w3}
    guardar_db(db)
    return {"mensaje": "Pesos configurados con éxito.", "pesos": db["pesos_ensamble"]}

@app.post("/api/examenes/corregir")

async def iniciar_correccion(background_tasks: BackgroundTasks):
    """Inicia el proceso de corrección por lotes en segundo plano."""
    global state
    db = cargar_db()
    url_llm = db.get("url_llm")
    if url_llm:
        os.environ["URL_LLM"] = url_llm
        
    if not db.get("respuestas_cargadas"):
        raise HTTPException(status_code=400, detail="No hay respuestas cargadas para corregir.")
        
    async with state_lock:
        if state.status == "running":
            return {"mensaje": "El proceso de corrección ya está en marcha.", "status": state.status}
            
        state.status = "running"
        state.total = len(db["respuestas_cargadas"])
        state.procesado = 0
        state.errores = 0
        
    # Limpiar estado anterior en DB
    db["proceso_correccion"]["status"] = "running"
    db["proceso_correccion"]["total"] = len(db["respuestas_cargadas"])
    db["proceso_correccion"]["procesado"] = 0
    db["proceso_correccion"]["errores"] = 0
    db["resultados"] = {}
    guardar_db(db)
    
    background_tasks.add_task(tarea_correccion_lote)
    return {"mensaje": "Proceso de corrección iniciado.", "status": "running"}

@app.get("/api/examenes/estado")
async def get_estado_correccion():
    """Endpoint de sondeo (polling) para que el frontend monitoree el progreso."""
    async with state_lock:
        return {
            "status": state.status,
            "total": state.total,
            "procesado": state.procesado,
            "errores": state.errores
        }

@app.get("/api/examenes/resultados")
async def get_resultados():
    """Devuelve los resultados consolidados por alumno."""
    db = cargar_db()
    return {
        "resultados": db.get("resultados", {}),
        "status": db.get("proceso_correccion", {}).get("status", "idle")
    }

@app.post("/api/examenes/comparar")
async def comparar_resultados(file: UploadFile = File(...)):
    """
    Recibe un CSV (por ejemplo dataset_filtrado.csv) con notas del profesor (teacher_grade)
    y lo compara con las correcciones ya realizadas por el agente en la base de datos.
    Calcula métricas como MAE, Sesgo, Coincidencia exacta y distribución de la diferencia.
    """
    try:
        df = pd.read_csv(file.file, encoding="utf-8-sig")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error leyendo archivo CSV: {str(e)}")

    required = {"question_id", "student_answer", "teacher_grade"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise HTTPException(status_code=400, detail=f"El CSV no contiene las columnas requeridas: {', '.join(missing)}")

    db = cargar_db()
    resultados_db = db.get("resultados", {})
    
    agente_lookup = {}
    for alumno_id, info in resultados_db.items():
        respuestas = info.get("respuestas", [])
        for r in respuestas:
            q_id = str(r.get("question_id")).strip()
            ans = str(r.get("student_answer")).strip()
            agente_lookup[(q_id, ans)] = r.get("nota_final")

    comparaciones = []
    mae_acumulado = 0.0
    bias_acumulado = 0.0
    coincidencia_exacta = 0
    coincidencia_tolerancia = 0  # +-1 punto
    distribucion_errores = {}

    for idx, row in df.iterrows():
        q_id = str(row["question_id"]).strip()
        ans = str(row["student_answer"]).strip()
        teacher_grade_raw = row["teacher_grade"]
        
        try:
            teacher_grade = float(teacher_grade_raw)
        except (ValueError, TypeError):
            continue

        nota_agente = agente_lookup.get((q_id, ans))
        if nota_agente is not None:
            nota_agente = float(nota_agente)
            diff = nota_agente - teacher_grade
            abs_error = abs(diff)
            
            mae_acumulado += abs_error
            bias_acumulado += diff
            
            if abs_error == 0:
                coincidencia_exacta += 1
            if abs_error <= 1.0:
                coincidencia_tolerancia += 1
                
            error_key = int(round(diff))
            distribucion_errores[error_key] = distribucion_errores.get(error_key, 0) + 1
            
            comparaciones.append({
                "question_id": q_id,
                "student_answer": ans,
                "student_answer_short": ans[:120] + "..." if len(ans) > 120 else ans,
                "teacher_grade": teacher_grade,
                "agent_grade": nota_agente,
                "diff": round(diff, 2)
            })

    total_comparados = len(comparaciones)
    if total_comparados == 0:
        raise HTTPException(
            status_code=400, 
            detail="No se encontraron coincidencias entre el CSV subido y los exámenes ya corregidos por el agente. Asegúrate de haber ejecutado la corrección primero."
        )

    mae = round(mae_acumulado / total_comparados, 2)
    bias = round(bias_acumulado / total_comparados, 2)
    pct_exacto = round((coincidencia_exacta / total_comparados) * 100, 2)
    pct_tolerancia = round((coincidencia_tolerancia / total_comparados) * 100, 2)

    dist_ordenada = {k: distribucion_errores[k] for k in sorted(distribucion_errores.keys())}

    return {
        "total_comparados": total_comparados,
        "mae": mae,
        "bias": bias,
        "pct_exacto": pct_exacto,
        "pct_tolerancia": pct_tolerancia,
        "distribucion_errores": dist_ordenada,
        "comparaciones": comparaciones
    }

@app.post("/api/examenes/comparar-upload")
async def upload_comparar_csv(file: UploadFile = File(...)):
    """
    Sube un CSV (como dataset_filtrado.csv) para realizar la corrección y comparación en vivo.
    """
    try:
        df = pd.read_csv(file.file, encoding="utf-8-sig")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error leyendo archivo CSV: {str(e)}")

    required = {"question_id", "student_answer", "teacher_grade"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise HTTPException(status_code=400, detail=f"El CSV no contiene las columnas requeridas: {', '.join(missing)}")

    respuestas_comp = []
    for idx, row in df.iterrows():
        try:
            tg = float(row["teacher_grade"])
        except (ValueError, TypeError):
            continue
            
        respuestas_comp.append({
            "question_id": str(row["question_id"]).strip(),
            "student_answer": str(row["student_answer"]).strip(),
            "teacher_grade": tg
        })

    if not respuestas_comp:
        raise HTTPException(status_code=400, detail="El CSV no contiene registros válidos para evaluar.")

    db = cargar_db()
    db["respuestas_comparar"] = respuestas_comp
    db["proceso_comparacion"] = {
        "status": "idle",
        "total": len(respuestas_comp),
        "procesado": 0,
        "errores": 0,
        "mae": 0.0
    }
    db["resultados_comparacion"] = {}
    guardar_db(db)

    global state_comp
    async with state_comp_lock:
        state_comp.status = "idle"
        state_comp.total = len(respuestas_comp)
        state_comp.procesado = 0
        state_comp.errores = 0
        state_comp.mae = 0.0

    return {
        "mensaje": "Archivo de comparación cargado exitosamente.",
        "total_registros": len(respuestas_comp)
    }

@app.post("/api/examenes/comparar-corregir")
async def iniciar_correccion_comparacion(background_tasks: BackgroundTasks):
    """
    Inicia el proceso asíncrono de corrección y comparación en vivo de las respuestas cargadas.
    """
    global state_comp
    db = cargar_db()
    if not db.get("respuestas_comparar"):
        raise HTTPException(status_code=400, detail="No hay respuestas cargadas para corregir y comparar.")

    async with state_comp_lock:
        if state_comp.status in ("running", "cancelling"):
            return {"mensaje": "El proceso de corrección y comparación ya está en marcha o cancelándose.", "status": state_comp.status}

        state_comp.status = "running"
        state_comp.total = len(db["respuestas_comparar"])
        state_comp.procesado = 0
        state_comp.errores = 0
        state_comp.mae = 0.0
        state_comp.cancel_requested = False

    # Limpiar estado anterior en DB
    db["proceso_comparacion"]["status"] = "running"
    db["proceso_comparacion"]["total"] = len(db["respuestas_comparar"])
    db["proceso_comparacion"]["procesado"] = 0
    db["proceso_comparacion"]["errores"] = 0
    db["proceso_comparacion"]["mae"] = 0.0
    db["resultados_comparacion"] = {}
    guardar_db(db)

    background_tasks.add_task(tarea_comparar_correccion_lote)
    return {"mensaje": "Proceso de corrección y comparación en vivo iniciado.", "status": "running"}

@app.get("/api/examenes/comparar-estado")
async def get_estado_comparacion():
    """
    Sondea el estado actual del proceso de corrección y comparación en vivo.
    """
    async with state_comp_lock:
        return {
            "status": state_comp.status,
            "total": state_comp.total,
            "procesado": state_comp.procesado,
            "errores": state_comp.errores,
            "mae": state_comp.mae
        }

@app.get("/api/examenes/comparar-resultados")
async def get_resultados_comparacion():
    """
    Devuelve los resultados consolidados de la comparación en vivo.
    """
    db = cargar_db()
    res = db.get("resultados_comparacion", {})
    if not res:
        return {
            "total_comparados": 0,
            "mae": 0.0,
            "bias": 0.0,
            "pct_exacto": 0.0,
            "pct_tolerancia": 0.0,
            "distribucion_errores": {},
            "comparaciones": []
        }
        
    comparaciones = res.get("comparaciones", [])
    total_comparados = len(comparaciones)
    
    if total_comparados == 0:
        return {
            "total_comparados": 0,
            "mae": 0.0,
            "bias": 0.0,
            "pct_exacto": 0.0,
            "pct_tolerancia": 0.0,
            "distribucion_errores": {},
            "comparaciones": []
        }

    mae_acumulado = 0.0
    bias_acumulado = 0.0
    coincidencia_exacta = 0
    coincidencia_tolerancia = 0
    distribucion_errores = {}

    for c in comparaciones:
        teacher_grade = float(c["teacher_grade"])
        agent_grade = float(c["agent_grade"])
        diff = agent_grade - teacher_grade
        abs_error = abs(diff)

        mae_acumulado += abs_error
        bias_acumulado += diff

        if abs_error == 0:
            coincidencia_exacta += 1
        if abs_error <= 1.0:
            coincidencia_tolerancia += 1

        error_key = int(round(diff))
        distribucion_errores[error_key] = distribucion_errores.get(error_key, 0) + 1

    mae = round(mae_acumulado / total_comparados, 2)
    bias = round(bias_acumulado / total_comparados, 2)
    pct_exacto = round((coincidencia_exacta / total_comparados) * 100, 2)
    pct_tolerancia = round((coincidencia_tolerancia / total_comparados) * 100, 2)

    dist_ordenada = {k: distribucion_errores[k] for k in sorted(distribucion_errores.keys())}

    return {
        "total_comparados": total_comparados,
        "mae": mae,
        "bias": bias,
        "pct_exacto": pct_exacto,
        "pct_tolerancia": pct_tolerancia,
        "distribucion_errores": dist_ordenada,
        "comparaciones": comparaciones
    }

@app.post("/api/examenes/comparar-cancelar")
async def cancelar_comparacion():
    """Cancela el proceso de comparación en vivo actual."""
    global state_comp
    async with state_comp_lock:
        if state_comp.status != "running":
            raise HTTPException(status_code=400, detail="No hay ningún proceso de comparación en ejecución.")
        state_comp.cancel_requested = True
        state_comp.status = "cancelling"
    
    # Actualizar estado en base de datos local inmediatamente
    db = cargar_db()
    if "proceso_comparacion" in db:
        db["proceso_comparacion"]["status"] = "cancelling"
    guardar_db(db)
    
    return {"mensaje": "Cancelación solicitada con éxito.", "status": "cancelling"}

# ----------------- ARCHIVOS ESTÁTICOS Y PÁGINA PRINCIPAL -----------------

# Crear directorio de estáticos si no existe
os.makedirs("static", exist_ok=True)

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

# Servir archivos estáticos (JS, CSS) desde la carpeta static/
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    # Iniciar servidor local
    print("Iniciando aplicación web local en http://localhost:5000")
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)
