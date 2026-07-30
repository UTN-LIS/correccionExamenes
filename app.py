import os
import csv
import json
import asyncio
import pandas as pd
from typing import List, Dict, Any, Optional
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
    respuesta_estudiante: str
) -> Dict[str, Any]:
    """Ejecuta los tres pasos de evaluación llamando al LLM de forma no bloqueante."""
    conceptos_resultados = []
    conceptos_evaluados_dict = {}
    tiempo_total = 0.0
    
    # PASO 1: Evaluar conceptos clave uno a uno
    if conceptos:
        for concepto in conceptos:
            tag = concepto['tag']
            desc = concepto['descripcion']
            user_msg_c = construir_user_message_conceptos(pregunta_text, concepto, respuesta_estudiante)
            
            # Ejecutar en hilo de ejecución secundario para no bloquear el bucle de eventos async
            salida_c, tiempo_c = await asyncio.to_thread(
                cliente_llm.generar_salida, SYSTEM_PROMPT_CONCEPTOS, user_msg_c
            )
            clean_c = salida_c.strip().lower().rstrip('.')
            if clean_c not in ("sí", "no"):
                clean_c = "no"  # fallback de consistencia
            conceptos_evaluados_dict[tag] = clean_c
            tiempo_total += tiempo_c
            conceptos_resultados.append(f"- <{tag}> ({desc}): {clean_c}")
    
    if conceptos_resultados:
        conceptos_evaluados_str = "\n".join(conceptos_resultados)
    else:
        conceptos_evaluados_str = "No hay conceptos específicos definidos para esta pregunta."
        
    # PASO 2: Clasificar rango de nota
    user_msg_r = construir_user_message_rango(pregunta_text, respuesta_estudiante, conceptos_evaluados_str)
    salida_r, tiempo_r = await asyncio.to_thread(
        cliente_llm.generar_salida, SYSTEM_PROMPT_RANGO, user_msg_r
    )
    clean_r = salida_r.strip().replace("\n", "").strip()
    tiempo_total += tiempo_r
    
    # PASO 3: Asignar calificación final numérica
    user_msg_n = construir_user_message_nota(pregunta_text, respuesta_estudiante, conceptos_evaluados_str, clean_r)
    salida_n, tiempo_n = await asyncio.to_thread(
        cliente_llm.generar_salida, SYSTEM_PROMPT_NOTA, user_msg_n
    )
    clean_n = salida_n.strip().replace("\n", "").strip()
    tiempo_total += tiempo_n
    
    try:
        nota_final = int(clean_n)
        if nota_final < 1 or nota_final > 10:
            nota_final = 1
    except ValueError:
        # Intentar extraer el primer número
        import re
        numeros = re.findall(r'\d+', clean_n)
        nota_final = int(numeros[0]) if numeros else 1
        
    return {
        "conceptos_evaluados": conceptos_evaluados_dict,
        "rango_nota": clean_r,
        "nota_final": nota_final,
        "tiempo": round(tiempo_total, 3),
        "estado": "completado"
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
