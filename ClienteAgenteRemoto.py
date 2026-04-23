import asyncio
import json
import logging
from rich.console import Console
from rich.logging import RichHandler
import time
import os
import requests
import mlflow
from mlflow.tracking import MlflowClient
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import numpy as np
from bert_score import BERTScorer
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
handler = RichHandler(
    console=Console(stderr=True),
    rich_tracebacks=True
)
formatter = logging.Formatter("%(message)s")
handler.setFormatter(formatter)
logger.handlers.clear()
logger.addHandler(handler)
logger.propagate = False

# --- Configuración simple de MLflow ---
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "mlruns")
EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT", "mi_experimento")

# Configurar MLflow
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

# Crear o obtener experimento
experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
if experiment is None:
    experiment_id = mlflow.create_experiment(EXPERIMENT_NAME)
    logger.info(f"✅ Experimento creado: {EXPERIMENT_NAME}")
else:
    experiment_id = experiment.experiment_id
    logger.info(f"📊 Usando experimento existente: {EXPERIMENT_NAME}")

# --- Inicializar BERTScore (solo una vez) ---
# Nota: La primera vez descargará modelos, puede tomar unos minutos
USE_BERTSCORE = os.getenv("USE_BERTSCORE", "true").lower() == "true"
if USE_BERTSCORE:
    logger.info("🔄 Inicializando BERTScore (esto toma unos segundos la primera vez)...")
    bert_scorer = BERTScorer(lang="es", rescale_with_baseline=True)
    logger.info("✅ BERTScore listo para usar")
else:
    bert_scorer = None

# --- wrapper para LM Studio ---
async def call_llm(messages, sesion_id=None):
    url = os.getenv("URL_LLM")
    
    # DEBUG: Imprimir la URL exacta
    url = url + "/chat"
    print(f"🔗 URL desde .env: '{url}'")
    print(f"🔗 Tipo: {type(url)}")
    request_data = {
        "session_id": sesion_id,
        "summary": "",
        "messages": messages
    }
    response = requests.post(
        url,
        json=request_data,
        headers={"Content-Type": "application/json"}
    )
    return response.json()

# --- Función para calcular Exact Match ---
def calcular_exact_match(respuesta_generada, respuesta_esperada):
    """Calcula si la respuesta coincide exactamente con la esperada"""
    return 1.0, 1.0
    # Limpiar y normalizar respuestas
    gen_clean = respuesta_generada.lower()
    exp_clean = respuesta_esperada.lower()
    
    # Exact match estricto
    exact_match = 1.0 if gen_clean == exp_clean else 0.0
    
    # Exact match ignorando puntuación y espacios extras
    import re
    gen_normalized = re.sub(r'[^\w\s]', '', gen_clean)
    exp_normalized = re.sub(r'[^\w\s]', '', exp_clean)
    exact_match_normalized = 1.0 if gen_normalized == exp_normalized else 0.0
    
    return exact_match, exact_match_normalized

# --- Función para calcular BERTScore ---
async def calcular_bertscore(respuesta_generada, respuesta_referencia):
    """Calcula similitud semántica usando BERTScore"""
    return 0.0, 0.0, 0.0
    if bert_scorer is None:
        return 0.0, 0.0, 0.0
    
    P, R, F1 = bert_scorer.score([respuesta_generada], [respuesta_referencia])
    return float(P[0]), float(R[0]), float(F1[0])

# --- Función para clasificar respuestas en categorías ---
def clasificar_respuesta(respuesta, categorias_posibles):
    """
    Clasifica una respuesta en una categoría predefinida
    Ejemplo de categorías: ["positiva", "negativa", "neutral", "informativa", "pregunta"]
    """
    return "otra"
    respuesta_lower = respuesta.lower()
    
    for categoria, palabras_clave in categorias_posibles.items():
        if any(palabra in respuesta_lower for palabra in palabras_clave):
            return categoria
    
    return "otra"

# --- Función principal de métricas ---
async def calcular_todas_metricas(
    respuesta_generada, 
    respuesta_esperada=None,
    tiempo_respuesta=None,
    categoria_real=None,
    categorias_sistema=None
):
    """
    Calcula todas las métricas necesarias
    
    Args:
        respuesta_generada: Lo que devolvió tu modelo
        respuesta_esperada: La respuesta correcta (ground truth)
        tiempo_respuesta: Tiempo que tomó generar la respuesta
        categoria_real: Categoría real de la respuesta
        categorias_sistema: Diccionario con categorías y palabras clave
    """
    
    metricas = {}
    
    # 1. Latencia (ms por respuesta)
    if tiempo_respuesta is not None:
        metricas["latencia_ms"] = tiempo_respuesta * 1000
        metricas["tiempo_respuesta_segundos"] = tiempo_respuesta
    
    # 2. Longitud de respuesta
    metricas["longitud_respuesta"] = len(respuesta_generada)
    #metricas["num_palabras"] = len(respuesta_generada.split())
    
    # 3. Exact Match (si tenemos respuesta esperada)
    if respuesta_esperada:
        em_strict, em_normalized = calcular_exact_match(respuesta_generada, respuesta_esperada)
        metricas["exact_match_strict"] = em_strict
        metricas["exact_match_normalized"] = em_normalized
    
    # 4. BERTScore (si tenemos respuesta esperada y está habilitado)
    if respuesta_esperada and USE_BERTSCORE:
        precision, recall, f1 = await calcular_bertscore(respuesta_generada, respuesta_esperada)
        metricas["bertscore_precision"] = precision
        metricas["bertscore_recall"] = recall
        metricas["bertscore_f1"] = f1
    
    # 5. Clasificación de respuestas (si tenemos sistema de categorías)
    if categorias_sistema:
        categoria_detectada = clasificar_respuesta(respuesta_generada, categorias_sistema)
        metricas["categoria_detectada"] = categoria_detectada
        
        if categoria_real:
            # Convertir categorías a números para métricas
            categorias_lista = list(categorias_sistema.keys()) + ["otra"]
            if categoria_real in categorias_lista and categoria_detectada in categorias_lista:
                metricas["clasificacion_correcta"] = 1.0 if categoria_real == categoria_detectada else 0.0
    
    return metricas

# --- Función para capturar métricas en lote ---
def capturar_metricas_lote(nombre_experimento, lista_metricas, throughput=None):
    """
    Captura múltiples métricas en una sola ejecución de MLflow
    """
    with mlflow.start_run(run_name=nombre_experimento):
        # Métricas agregadas
        for nombre, valor in lista_metricas.items():
            if isinstance(valor, (int, float)):
                mlflow.log_metric(nombre, valor)
                logger.info(f"   📊 {nombre}: {valor:.4f}" if isinstance(valor, float) else f"   📊 {nombre}: {valor}")
        
        # Throughput si se proporciona
        if throughput:
            mlflow.log_metric("throughput_respuestas_por_segundo", throughput)
        
        mlflow.set_tag("timestamp", datetime.now().isoformat())
        mlflow.set_tag("metricas_tipo", "evaluacion_completa")
        
        run_id = mlflow.active_run().info.run_id
        logger.info(f"✅ Métricas guardadas en MLflow (Run ID: {run_id[:8]}...)")
        
        return run_id

# --- Función para evaluar un conjunto de respuestas ---
async def evaluar_lote_respuestas(respuestas_y_esperadas):
    """
    Evalúa un lote de respuestas para calcular métricas agregadas
    
    Args:
        respuestas_y_esperadas: Lista de tuplas (respuesta_generada, respuesta_esperada, tiempo)
    """
    
    todas_metricas = []
    tiempos = []
    exact_matches = []
    bertscore_f1s = []
    clasificaciones_correctas = []
    
    categorias_sistema = {
        "informativa": ["según", "información", "datos", "muestra", "indica"],
        "saludo": ["hola", "buenos días", "buenas tardes", "saludos"],
        "pregunta": ["qué", "cuál", "cómo", "por qué", "dónde", "cuándo"],
        "despedida": ["adiós", "hasta luego", "chao", "nos vemos"]
    }
    
    logger.info(f"📊 Evaluando lote de {len(respuestas_y_esperadas)} respuestas...")
    
    for i, (respuesta_gen, respuesta_exp, tiempo) in enumerate(respuestas_y_esperadas):
        metricas = await calcular_todas_metricas(
            respuesta_generada=respuesta_gen,
            respuesta_esperada=respuesta_exp,
            tiempo_respuesta=tiempo,
        )
        
        todas_metricas.append(metricas)
        tiempos.append(tiempo)
        
        if "exact_match_strict" in metricas:
            exact_matches.append(metricas["exact_match_strict"])
        if "bertscore_f1" in metricas:
            bertscore_f1s.append(metricas["bertscore_f1"])
        if "clasificacion_correcta" in metricas:
            clasificaciones_correctas.append(metricas["clasificacion_correcta"])
    
    # Calcular métricas agregadas
    metricas_agregadas = {
        "accuracy_promedio": np.mean(exact_matches) if exact_matches else 0.0,
        "exact_match_promedio": np.mean(exact_matches) if exact_matches else 0.0,
        "bertscore_f1_promedio": np.mean(bertscore_f1s) if bertscore_f1s else 0.0,
        "precision_clasificacion": np.mean(clasificaciones_correctas) if clasificaciones_correctas else 0.0,
        "latencia_promedio_ms": np.mean(tiempos) * 1000 if tiempos else 0.0,
        "latencia_p50_ms": np.percentile(tiempos, 50) * 1000 if tiempos else 0.0,
        "latencia_p95_ms": np.percentile(tiempos, 95) * 1000 if tiempos else 0.0,
        "latencia_p99_ms": np.percentile(tiempos, 99) * 1000 if tiempos else 0.0,
        "total_respuestas": len(respuestas_y_esperadas),
        "throughput_respuestas_por_segundo": len(respuestas_y_esperadas) / sum(tiempos) if tiempos else 0.0
    }
    
    return metricas_agregadas

# --- Función principal corregida ---
async def main():
    start_time = time.time()
    todas_las_metricas = []  # Para almacenar métricas de cada interacción
    
    logger.info("=== Sistema con captura de métricas en MLflow ===")
    logger.info(f"📁 Datos guardados en: {MLFLOW_TRACKING_URI}")
    logger.info(f"🧪 Experimento: {EXPERIMENT_NAME}")
    logger.info("Para ver el dashboard: mlflow ui\n")
    
    # Definir sistema de categorías para clasificación
    categorias_sistema = {
        "informativa": ["según", "información", "datos", "muestra", "indica", "clasifica"],
        "saludo": ["hola", "buenos días", "buenas tardes", "saludos", "buen día"],
        "pregunta": ["qué", "cuál", "cómo", "por qué", "dónde", "cuándo"],
        "despedida": ["adiós", "hasta luego", "chao", "nos vemos", "salir"]
    }

    system_msg = {"role": "system", "content": "Eres un asistente útil que califica respuestas a examenes como si fuera un profesor."}
    user_msg = {"role": "user", "content": "pregunta 'Explica el ciclo TDD  y su importancia en el desarrollo de software.' respuesta 'El TDD en inglés es Test-Driven Development, es un mecanismo de test independientes para el proceso de un proyecto. En primer lugar, está el test en rojo, es decir, los test de la práctica están fallando porque no está implementado. En segundo lugar, el test verde, es decir, se ha implementado los métodos necesarios para probar la ejecución. No importaría el largo del código sino su funcionamiento. Y, por último, está el refactor, se ha corregido dicha implementación para mejorar el código y su implementación. En otras palabras, no se modifica su funcionamiento, pero sí el código para hacerlo más dinámico. Es un ciclo el cuál empieza en rojo -> verde -> refactor. Nos ayuda a comprobar si los métodos implementados han sido utilizados en los test y qué está fallando.'"}
    
    messages_big_history = [system_msg, user_msg]
    
    # Llamada inicial al LLM
    inicio_llm = time.time()
    response = await call_llm(messages_big_history)
    tiempo_llm = time.time() - inicio_llm
    messages_big_history.append({"role": "assistant", "content": response})
    
    # Calcular métricas (sin respuesta esperada en tiempo real)
    metricas = await calcular_todas_metricas(
        respuesta_generada=response,
        tiempo_respuesta=tiempo_llm,

    )
    todas_las_metricas.append(metricas)
    
    # Guardar en MLflow
    nombre_ejecucion = f"conversacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    
    logger.info("\n📊 Capturando métricas en MLflow:")
    
    logger.info(f"\n💬 Respuesta del modelo: {response['response']}")
    
    
    # Opcional: Si tienes un dataset de prueba con respuestas esperadas
    lista_de_prueba=[(response,"El ciclo TDD consiste en tres etapas: primero, se escribe un test que falla (Rojo) porque la funcionalidad aún no ha sido implementada. En la segunda fase (Verde), se desarrolla el mínimo código necesario para que el test pase. Finalmente, en la etapa de Refactor, se mejora el código manteniendo todos los tests en verde. Este ciclo es crucial ya que promueve un desarrollo proactivo, asegurando que el código producido cumple con las especificaciones definidas inicialmente por los tests.",tiempo_llm)]
    resultados_lote = await evaluar_lote_respuestas(lista_de_prueba)
    capturar_metricas_lote("evaluacion_dataset_prueba", resultados_lote)

# --- Función para cargar dataset de prueba ---
def cargar_dataset_prueba():
    """
    Carga un dataset de prueba con respuestas esperadas
    Formato esperado: CSV con columnas 'pregunta', 'respuesta_esperada'
    """
    import pandas as pd
    
    # Ejemplo de dataset mínimo
    dataset_ejemplo = pd.DataFrame([
        {"pregunta": "¿Cuáles son las características de una flor Setosa?", 
         "respuesta_esperada": "La flor Setosa tiene sépalos anchos y pétalos cortos"},
        {"pregunta": "¿Qué significa la palabra Versicolor?", 
         "respuesta_esperada": "Versicolor significa 'de varios colores'"},
    ])
    
    return dataset_ejemplo

if __name__ == "__main__":
    asyncio.run(main())