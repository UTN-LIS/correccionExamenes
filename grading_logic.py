import re
from prompts import (
    SYSTEM_PROMPT_CONCEPTOS,
    SYSTEM_PROMPT_RANGO_INDEPENDIENTE,
    SYSTEM_PROMPT_NOTA_DIRECTA,
    construir_user_message_nota_directa,
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



