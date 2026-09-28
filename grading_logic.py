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
    salida_dict, tiempo = cliente_llm.puntuar(pregunta_text, respuesta_correcta, respuesta_estudiante )
    
    salida_texto = salida_dict.get("logit", "")
    
        
    return {
        "nota_directa": salida_texto,
        "tiempo": round(tiempo, 3),
    }



