import re
from prompts import (
    SYSTEM_PROMPT_CONCEPTOS,
    SYSTEM_PROMPT_RANGO_INDEPENDIENTE,
    SYSTEM_PROMPT_NOTA_DIRECTA,
    SYSTEM_PROMPT_COMPARACION,
    construir_user_message_nota_directa,
    construir_user_message_comparacion
)


def es_respuesta_vacia_o_evasiva(respuesta: str) -> bool:
    """
    Detecta si una respuesta está vacía, es extremadamente corta o es evasiva (ej: 'No lo sé').
    """
    if not respuesta:
        return True
    clean_resp = respuesta.strip().lower()
    
    # Eliminar puntuación al final para facilitar coincidencia de prefijos
    clean_resp = clean_resp.rstrip(".?!, ")
    
    # Si tiene menos de 12 caracteres (ej: "no sé", "no se", "vacio", "nada", "ni idea")
    if len(clean_resp) < 12:
        return True
        
    # Frases de evasión comunes que significan que no sabe o no responde
    frases_evasivas = [
        "no lo se", "no sé", "no se", "ni idea", "no tengo idea", "no tengo ni idea",
        "no respondo", "no se nada", "no sé nada", "no respondo a la pregunta",
        "no se que es", "no sé qué es", "no se como", "no sé cómo", "no conozco",
        "no comprendo", "escribo para no dejarlo en blanco", "escribo para no dejar en blanco"
    ]
    
    for frase in frases_evasivas:
        if clean_resp.startswith(frase):
            return True
            
    return False
        

def evaluar_nota_directa(cliente_llm, pregunta_text, respuesta_correcta, respuesta_estudiante):
    user_msg = construir_user_message_nota_directa(pregunta_text, respuesta_correcta, respuesta_estudiante)
    
    # cliente_llm.generar_salida devuelve ahora el dict {"response": ..., "metricas": ...} y el tiempo
    salida_dict, tiempo = cliente_llm.generar_salida(SYSTEM_PROMPT_NOTA_DIRECTA, user_msg)
    
    salida_texto = salida_dict.get("response", "")
    metricas = salida_dict.get("metricas", {})
    
    clean_n = salida_texto.strip().replace("\n", "").strip()
    
    try:
        nota_directa = float(clean_n)
        if nota_directa < 0.0 or nota_directa > 10.0:
            print(f"Advertencia: Nota directa '{nota_directa}' fuera de rango [0.0, 10.0]. Usando fallback 0.0.")
            nota_directa = 0.0
    except ValueError:
        numeros = re.findall(r'\d+', clean_n)
        if numeros:
            nota_directa = float(numeros[0])
            if nota_directa < 0.0 or nota_directa > 10.0:
                print(f"Advertencia: Nota directa extraída '{nota_directa}' fuera de rango. Usando fallback 0.0.")
                nota_directa = 0.0
        else:
            print(f"Advertencia: No se pudo extraer número de nota directa ('{salida_texto}'). Usando fallback 0.0.")
            nota_directa = 0.0
        
    return {
        "nota_directa": nota_directa,
        "tiempo": round(tiempo, 3),
        "metricas": metricas  # Contiene perplejidad, entropia, masa_acumulada_top_x, etc.
    }


def _parsear_respuesta_si_no(texto: str) -> bool:
    """
    Extrae si/no del output del modelo. Prioriza el contenido dentro de
    <respuesta>...</respuesta>; si no está el tag, cae a limpiar todo el texto.
    Es robusto a mayúsculas, tildes y puntuación.
 
    Fallback conservador: si no se puede parsear con confianza, devuelve False
    (trata al estudiante como "no mejor") y deja constancia en consola para
    poder auditar esos casos después.
    """
 
    limpio = texto.strip().lower().replace("í", "i")
    limpio = re.sub(r"[^a-z]", "", limpio)
 
    if limpio == "si":
        return True
    if limpio == "no":
        return False
 
    print(f"Advertencia: no se pudo parsear 'si'/'no' de la salida ('{texto[:80]}...'). Usando fallback False.")
    return False
 
 
def comparar_respuestas(cliente_llm, pregunta_text, respuesta_correcta, respuesta_estudiante, respuesta_comparacion):
    """
    Compara respuesta_estudiante contra respuesta_comparacion.
    Devuelve {"es_mejor": bool, "tiempo": float, "raw": str}
    """
    user_msg = construir_user_message_comparacion(
        pregunta_text, respuesta_correcta, respuesta_estudiante, respuesta_comparacion
    )
 
    salida_dict, tiempo = cliente_llm.generar_salida(SYSTEM_PROMPT_COMPARACION, user_msg)
    salida_texto = salida_dict.get("response", "")

    return {
        "es_mejor": _parsear_respuesta_si_no(salida_texto),
        "tiempo": round(tiempo, 3),
        "raw": salida_texto.strip(),
    }
 
 
# ---------------------------------------------------------------------------
# 4. INSERCIÓN ORDENADA POR BÚSQUEDA BINARIA
# ---------------------------------------------------------------------------
 
def insertar_ordenado(cliente_llm, pregunta, ideal_answer, nueva_respuesta, lista_ordenada, metadata_extra=None):
    """
    Inserta `nueva_respuesta` en `lista_ordenada` (ordenada de MEJOR a PEOR,
    índice 0 = mejor) usando búsqueda binaria: O(log n) comparaciones por
    ítem en vez de O(n).
 
    `lista_ordenada` es una lista de dicts con al menos la clave 'respuesta'
    (el texto). Se modifica in-place y también se devuelve por comodidad.
 
    Nota sobre transitividad: la búsqueda binaria asume que "es_mejor" define
    un orden total consistente. Un juez LLM puede ser inconsistente entre
    llamadas, así que algún ítem puede quedar mal ubicado si el juez se
    contradice. Es un tradeoff aceptable para bajar el costo de O(n) a
    O(log n) llamadas, pero por eso se devuelve n_comparaciones: sirve para
    auditar y, si hace falta, revisar casos con pocas comparaciones y
    resultado dudoso.
 
    Devuelve: (idx_insercion, tiempo_total, n_comparaciones)
    """
    lo, hi = 0, len(lista_ordenada)
    tiempo_total = 0.0
    n_comparaciones = 0
 
    while lo < hi:
        mid = (lo + hi) // 2
        pivote = lista_ordenada[mid]["respuesta"]
 
        res = comparar_respuestas(cliente_llm, pregunta, ideal_answer, nueva_respuesta, pivote)
        tiempo_total += res["tiempo"]
        n_comparaciones += 1
 
        if res["es_mejor"]:
            hi = mid       # nueva_respuesta es mejor que el pivote -> buscar en la mitad "mejor"
            print("buscando en la mitad mejor")
        else:
            lo = mid + 1   # nueva_respuesta no es mejor -> buscar en la mitad "peor"
            print("buscando en la mitad peor")
 
    idx_insercion = lo
    fila = {"respuesta": nueva_respuesta, **(metadata_extra or {})}
    lista_ordenada.insert(idx_insercion, fila)
 
    return idx_insercion, round(tiempo_total, 3), n_comparaciones
 
 


