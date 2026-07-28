import time
from prompts import (
    SYSTEM_PROMPT_CONCEPTOS,
    SYSTEM_PROMPT_RANGO,
    SYSTEM_PROMPT_NOTA,
    construir_user_message_conceptos,
    construir_user_message_rango,
    construir_user_message_nota
)


class Experimento:
    def __init__(self, cliente_llm, dataset_cliente, modelo="Modelo_XYZ"):
        self.dataset_cliente = dataset_cliente
        self.cliente_llm = cliente_llm
        self.modelo = modelo

    def ejecutar_dataset(self, max_items=None):
        """
        Itera el dataset y ejecuta la evaluación secuencial en 3 pasos:
        Paso 1: Evaluar conceptos clave uno a uno.
        Paso 2: Evaluar rango de nota con la información de los conceptos clave.
        Paso 3: Obtener la nota final con toda la información acumulada.
        """
        from conceptos import CONCEPTOS_POR_PREGUNTA

        # Obtener todos los conceptos únicos para usarlos como encabezados de columnas
        unique_tags = []
        for lista in CONCEPTOS_POR_PREGUNTA.values():
            for c in lista:
                if c["tag"] not in unique_tags:
                    unique_tags.append(c["tag"])
        unique_tags.sort()

        # Las columnas del CSV incluyen campos principales, rango, salida (nota final) y tags individuales
        fieldnames = ['step', 'pregunta', 'respuesta', 'rango_nota', 'salida', 'esperado', 'tiempo'] + unique_tags

        self.dataset_cliente.crear_csv_resultados(fieldnames)
        
        # Guardar configuración (usamos el prompt final como referencia de prompt del sistema)
        self.dataset_cliente.guardar_configuracion(self.modelo, SYSTEM_PROMPT_NOTA)

        buffer_salidas = []
        step = 0

        for pregunta, conceptos, respuesta, esperado in self.dataset_cliente.dataset_batch():

            if max_items and step >= max_items:
                break

            # Inicializar la fila del resultado
            fila_resultado = {
                'step': step,
                'pregunta': pregunta,
                'respuesta': respuesta,
                'esperado': esperado,
                'rango_nota': "",
                'salida': "",
                'tiempo': 0.0
            }
            for tag in unique_tags:
                fila_resultado[tag] = ""

            conceptos_resultados = []

            # ---- PASO 1: EVALUAR CONCEPTOS CLAVE ----
            if conceptos:
                for concepto in conceptos:
                    tag = concepto['tag']
                    desc = concepto['descripcion']
                    
                    user_msg_c = construir_user_message_conceptos(pregunta, concepto, respuesta)
                    salida_c, tiempo_c = self.cliente_llm.generar_salida(SYSTEM_PROMPT_CONCEPTOS, user_msg_c)
                    
                    clean_c = salida_c.strip().lower().rstrip('.')
                    fila_resultado[tag] = clean_c
                    fila_resultado['tiempo'] += tiempo_c
                    
                    conceptos_resultados.append(f"- <{tag}> ({desc}): {clean_c}")
            
            if conceptos_resultados:
                conceptos_evaluados_str = "\n".join(conceptos_resultados)
            else:
                conceptos_evaluados_str = "No hay conceptos específicos definidos para esta pregunta."

            # ---- PASO 2: EVALUAR RANGO DE NOTA ----
            user_msg_r = construir_user_message_rango(pregunta, respuesta, conceptos_evaluados_str)
            salida_r, tiempo_r = self.cliente_llm.generar_salida(SYSTEM_PROMPT_RANGO, user_msg_r)
            
            clean_r = salida_r.strip().replace("\n", "").strip()
            fila_resultado['rango_nota'] = clean_r
            fila_resultado['tiempo'] += tiempo_r

            # ---- PASO 3: EVALUAR NOTA FINAL ----
            user_msg_n = construir_user_message_nota(pregunta, respuesta, conceptos_evaluados_str, clean_r)
            salida_n, tiempo_n = self.cliente_llm.generar_salida(SYSTEM_PROMPT_NOTA, user_msg_n)
            
            clean_n = salida_n.strip().replace("\n", "").strip()
            fila_resultado['salida'] = clean_n
            fila_resultado['tiempo'] += tiempo_n

            buffer_salidas.append(fila_resultado)

            # Flush cada 20 elementos
            if len(buffer_salidas) >= 20:
                self.dataset_cliente.guardar_buffer_csv(buffer_salidas, fieldnames)
                buffer_salidas.clear()

            print(f"Progreso: {step + 1} ejemplos procesados")
            step += 1

        # Flush final
        if buffer_salidas:
            self.dataset_cliente.guardar_buffer_csv(buffer_salidas, fieldnames)
