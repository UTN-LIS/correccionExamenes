import re
from prompts import (
    SYSTEM_PROMPT_CONCEPTOS,
    SYSTEM_PROMPT_RANGO_INDEPENDIENTE,
    SYSTEM_PROMPT_NOTA_DIRECTA,
    construir_user_message_conceptos,
    construir_user_message_rango_independiente,
    construir_user_message_nota_directa,
)

# Mapeo de rangos a valores numéricos (centro de cada intervalo)
RANGO_A_NOTA = {
    "<INSUFICIENTE>": 1.5,   # Rango 0 a 3 (el centro es 1.5)
    "<ACEPTABLE>": 5.0,      # Rango 4 a 6
    "<BUENO>": 7.5,          # Rango 7 a 8
    "<EXCELENTE>": 9.5       # Rango 9 a 10
}

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

def evaluar_conceptos(cliente_llm, pregunta_text: str, conceptos: list, respuesta_estudiante: str) -> dict:
    """
    Experimento 1 (Etiquetas): Evalúa la presencia/ausencia de conceptos clave.
    Retorna un diccionario con los resultados individuales por concepto, 
    la cobertura (0.0 a 1.0) y la nota proporcional (0.0 a 10.0).
    """
    if not conceptos:
        return {
            "conceptos_evaluados": {},
            "cobertura": 0.0,
            "nota_conceptos": 0.0,
            "tiempo": 0.0
        }
        
    if es_respuesta_vacia_o_evasiva(respuesta_estudiante):
        return {
            "conceptos_evaluados": {c['tag']: "no" for c in conceptos},
            "cobertura": 0.0,
            "nota_conceptos": 0.0,
            "tiempo": 0.0
        }
        
    conceptos_evaluados = {}
    tiempo_total = 0.0
    
    for concepto in conceptos:
        tag = concepto['tag']
        user_msg = construir_user_message_conceptos(pregunta_text, concepto, respuesta_estudiante)
        salida, tiempo = cliente_llm.generar_salida(SYSTEM_PROMPT_CONCEPTOS, user_msg)
        
        clean_val = salida.strip().lower().rstrip('.')
        if clean_val not in ("sí", "no", "sí|", "no|"):
            print(f"Advertencia: Respuesta de conceptos no válida o fallida para concepto '{tag}' ('{salida}'). Usando fallback 'no'.")
            clean_val = "no"  # fallback
            
        conceptos_evaluados[tag] = clean_val
        tiempo_total += tiempo
        
    # Calcular cobertura, invirtiendo la interpretación para el tag ERROR:
    # para conceptos normales, "sí" = cumple (suma cobertura);
    # para ERROR, "no" (no cometió el error) = cumple (suma cobertura),
    # y "sí" (sí cometió el error) = no cumple (resta cobertura).
    total_conceptos = len(conceptos)
    conceptos_si = 0
    for concepto in conceptos:
        tag = concepto['tag']
        val = conceptos_evaluados[tag]
        es_afirmativo = val in ("sí", "sí|")
        
        if tag == "ERROR":
            # ERROR se invierte: "no" cuenta como positivo, "sí" cuenta como negativo
            if not es_afirmativo:
                conceptos_si += 1
        else:
            if es_afirmativo:
                conceptos_si += 1
    
    cobertura = conceptos_si / total_conceptos
    
    # Mapear linealmente cobertura [0.0, 1.0] a la nota [0.0, 10.0]
    nota_conceptos = 10.0 * cobertura
    
    return {
        "conceptos_evaluados": conceptos_evaluados,
        "cobertura": round(cobertura, 4),
        "nota_conceptos": round(nota_conceptos, 2),
        "tiempo": round(tiempo_total, 3)
    }

def evaluar_rango(cliente_llm, pregunta_text: str, respuesta_correcta: str, respuesta_estudiante: str) -> dict:
    """
    Experimento 2 (Rango): Clasifica la respuesta dentro de los rangos de calificación.
    Retorna la etiqueta del rango y el valor numérico correspondiente.
    """
    if es_respuesta_vacia_o_evasiva(respuesta_estudiante):
        return {
            "rango": "<INSUFICIENTE>",
            "nota_rango": 0.0,
            "tiempo": 0.0
        }
        
    user_msg = construir_user_message_rango_independiente(pregunta_text, respuesta_correcta, respuesta_estudiante)
    salida, tiempo = cliente_llm.generar_salida(SYSTEM_PROMPT_RANGO_INDEPENDIENTE, user_msg)
    
    clean_r = salida.strip().replace("\n", "").strip()
    
    # Encontrar la etiqueta que coincide en el texto
    rango_detectado = "<INSUFICIENTE>"  # fallback por defecto
    hubo_coincidencia = False
    clean_r_upper = clean_r.upper()
    for tag in RANGO_A_NOTA.keys():
        if tag in clean_r_upper or tag.strip("<>") in clean_r_upper:
            rango_detectado = tag
            hubo_coincidencia = True
            break
            
    if not hubo_coincidencia:
        print(f"Advertencia: Respuesta de rango no válida o fallida ('{salida}'). Usando fallback '<INSUFICIENTE>'.")
        
    # Si detectó insuficiente y es evasiva o nula, o si es normal
    nota_rango = RANGO_A_NOTA[rango_detectado]
    
    return {
        "rango": rango_detectado,
        "nota_rango": nota_rango,
        "tiempo": round(tiempo, 3)
    }

def evaluar_nota_directa(cliente_llm, pregunta_text: str, respuesta_correcta: str, respuesta_estudiante: str) -> dict:
    """
    Experimento 3 (Nota directa): Pide al LLM una calificación directa de 0 a 10
    basada en su criterio pedagógico.
    """
    if es_respuesta_vacia_o_evasiva(respuesta_estudiante):
        return {
            "nota_directa": 0.0,
            "tiempo": 0.0
        }
        
    user_msg = construir_user_message_nota_directa(pregunta_text, respuesta_correcta, respuesta_estudiante)
    salida, tiempo = cliente_llm.generar_salida(SYSTEM_PROMPT_NOTA_DIRECTA, user_msg)
    
    clean_n = salida.strip().replace("\n", "").strip()
    
    try:
        nota_directa = float(clean_n)
        if nota_directa < 0.0 or nota_directa > 10.0:
            print(f"Advertencia: Nota directa '{nota_directa}' fuera de rango [0.0, 10.0]. Usando fallback 0.0.")
            nota_directa = 0.0
    except ValueError:
        # Intentar extraer el primer número
        numeros = re.findall(r'\d+', clean_n)
        if numeros:
            nota_directa = float(numeros[0])
            if nota_directa < 0.0 or nota_directa > 10.0:
                print(f"Advertencia: Nota directa extraída '{nota_directa}' fuera de rango. Usando fallback 0.0.")
                nota_directa = 0.0
        else:
            print(f"Advertencia: No se pudo extraer número de nota directa ('{salida}'). Usando fallback 0.0.")
            nota_directa = 0.0
        
    return {
        "nota_directa": nota_directa,
        "tiempo": round(tiempo, 3)
    }

def ensamblar_nota_final(
    res_conceptos: dict, 
    #res_rango: dict, 
    res_nota_directa: dict, 
    w1: float = 0.10, 
    w2: float = 0.05, 
    w3: float = 0.85
) -> dict:
    """
    Calcula la nota final combinada aplicando una fórmula ponderada:
    Nota_Final = (w1 * res_exp1) + (w2 * res_exp2) + (w3 * res_exp3)
    
    Retorna la nota final combinada (redondeada al entero más cercano) y el desglose de los experimentos.
    """
    # Validar que los pesos sumen aproximadamente 1
    suma_pesos = w1 + w2 + w3
    if not (0.99 <= suma_pesos <= 1.01):
        # Si no están normalizados, normalizar
        w1, w2, w3 = w1/suma_pesos, w2/suma_pesos, w3/suma_pesos

    # Si no hay conceptos definidos para la pregunta, la nota es 100% la nota directa
    if not res_conceptos.get("conceptos_evaluados"):
        nota_final_valor = round(n_directa, 2)
        nota_final_valor = max(0.0, min(10.0, nota_final_valor))
        return {
            "nota_final": nota_final_valor,
            "desglose": {
                "experimento_conceptos": {
                    "nota_obtenida": n_directa,
                    "cobertura": 0.0,
                    "conceptos_evaluados": {}
                },
                "experimento_rango": {
                    "nota_obtenida": "nulo",
                    "rango_clasificado": "nulo"
                },
                "experimento_nota_directa": {
                    "nota_obtenida": n_directa
                }
            },
            "configuracion": {
                "algoritmo_usado": "nota_directa_exclusiva",
                "pesos": {
                    "w1_conceptos": 0.0,
                    "w2_rango": 0.0,
                    "w3_nota_directa": 1.0
                }
            }
        }

    n_conceptos = res_conceptos["nota_conceptos"]
    #n_rango = res_rango["nota_rango"]
    n_directa = res_nota_directa["nota_directa"]
    
    diff_conceptos = abs(n_directa - n_conceptos)
    #diff_rango = abs(n_directa - n_rango)
    
    if diff_conceptos >= 2.0: # or diff_rango >= 2.0:
        nota_final = (w1 * n_conceptos) +  (w3 * n_directa) # + (w2 * n_rango) 
        algoritmo_usado = "pesos"
    else:
        # Promedio entre nota directa y conceptos (los dos valores principales de nota)
        nota_final = (n_directa + n_conceptos) / 2.0
        algoritmo_usado = "promedio"
        
    # Guardar la nota final con decimales, redondeada a 2 dígitos
    nota_final_valor = round(nota_final, 2)
    
    # Asegurar límites del examen (0 a 10)
    nota_final_valor = max(0.0, min(10.0, nota_final_valor))
    
    return {
        "nota_final": nota_final_valor,
        "desglose": {
            "experimento_conceptos": {
                "nota_obtenida": n_conceptos,
                "cobertura": res_conceptos["cobertura"],
                "conceptos_evaluados": res_conceptos["conceptos_evaluados"]
            },
            "experimento_rango": {
                "nota_obtenida": "nulo", # res_rango
                "rango_clasificado": "nulo" # res_rango["rango"]
            },
            "experimento_nota_directa": {
                "nota_obtenida": n_directa
            }
        },
        "configuracion": {
            "algoritmo_usado": algoritmo_usado,
            "pesos": {
                "w1_conceptos": round(w1, 3),
                "w2_rango": round(w2, 3),
                "w3_nota_directa": round(w3, 3)
            }
        }
    }

if __name__ == "__main__":
    # Ejemplo rápido de cómo se invoca esta función de ensamble
    print("Ejemplo de uso de la función de ensamble:")
    
    # Datos simulados de los experimentos
    conceptos_simulados = {
        "conceptos_evaluados": {"TDD_ROJO": "sí", "TDD_VERDE": "sí", "TDD_REFACTOR": "no"},
        "cobertura": 0.67,
        "nota_conceptos": 6.7,
        "tiempo": 0.8
    }
    
    rango_simulado = {
        "rango": "<BUENO>",
        "nota_rango": 7.5,
        "tiempo": 0.4
    }
    
    nota_directa_simulada = {
        "nota_directa": 8.0,
        "tiempo": 0.4
    }
    
    # Llamar al ensamble
    resultado = ensamblar_nota_final(
        conceptos_simulados, 
        rango_simulado, 
        nota_directa_simulada, 
        w1=0.10, 
        w2=0.05, 
        w3=0.85
    )
    
    import json
    print(json.dumps(resultado, indent=4, ensure_ascii=False))
