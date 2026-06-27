import os


class Experimento:
    def __init__(self, cliente_llm, dataset_cliente, modelo="Modelo_XYZ"):
        self.dataset_cliente = dataset_cliente
        self.cliente_llm = cliente_llm
        self.modelo = modelo

    def generar_salida(self, apuntes: str, rubrica: str, pregunta: str, respuesta_alumno: str):
        """
        Llama al cliente LLM con el nuevo formato estructurado.
        Retorna (resultado: dict, tiempo: float).
        """
        resultado, tiempo = self.cliente_llm.generar_salida(
            apuntes=apuntes,
            rubrica=rubrica,
            pregunta=pregunta,
            respuesta_alumno=respuesta_alumno
        )
        return resultado, tiempo

    def ejecutar_dataset(self, max_items=None):
        """
        Itera el dataset, llama al LLM usando la cadena estructurada y guarda los resultados en CSV.
        Mantiene compatibilidad con las columnas de conceptos y con procesar_metricas.py.
        """
        from conceptos import CONCEPTOS_POR_PREGUNTA

        # Obtener todos los conceptos únicos para usarlos como encabezados de columnas (retrocompatibilidad)
        unique_tags = []
        for lista in CONCEPTOS_POR_PREGUNTA.values():
            for c in lista:
                if c["tag"] not in unique_tags:
                    unique_tags.append(c["tag"])
        unique_tags.sort()

        # Los encabezados de salida ahora tienen tanto las columnas tradicionales de conceptos
        # como los nuevos campos enriquecidos de la evaluación y la columna 'salida' requerida por procesar_metricas.py.
        fieldnames = [
            'step', 'pregunta', 'respuesta', 'esperado', 'salida', 'tiempo',
            'razonamiento_previo', 'conceptos_clave_encontrados', 'conceptos_clave_omitidos',
            'nota_numeral', 'nivel_de_confianza', 'fuera_de_contexto'
        ] + unique_tags

        self.dataset_cliente.crear_csv_resultados(fieldnames)
        self.dataset_cliente.guardar_configuracion(self.modelo, "Evaluación estructurada LangChain UTN")

        buffer_salidas = []
        step = 0

        for pregunta, conceptos, respuesta, esperado, ideal in self.dataset_cliente.dataset_batch():

            if max_items and step >= max_items:
                break

            # Construir apuntes (usando ideal_answer) y rubrica (usando la lista de conceptos)
            apuntes = ideal if (ideal and str(ideal).strip()) else "No se proveyeron apuntes específicos de la cátedra."
            rubrica = "\n".join([f"- {c['tag']}: {c['descripcion']}" for c in conceptos]) if conceptos else "Evaluar coherencia general con la pregunta."

            # Hacer la consulta única al LLM
            resultado_dict, tiempo = self.generar_salida(
                apuntes=apuntes,
                rubrica=rubrica,
                pregunta=pregunta,
                respuesta_alumno=respuesta
            )

            # Extraer campos de la respuesta estructurada o inicializar valores seguros por defecto
            razonamiento = resultado_dict.get("razonamiento_previo", "")
            encontrados = resultado_dict.get("conceptos_clave_encontrados", [])
            omitidos = resultado_dict.get("conceptos_clave_omitidos", [])
            nota = resultado_dict.get("nota_numeral", 1)
            confianza = resultado_dict.get("nivel_de_confianza", 0.0)
            fuera_contexto = resultado_dict.get("fuera_de_contexto", False)

            # Columna 'salida' formateada para que procesar_metricas.py pueda extraer la nota con regex
            salida_formateada = f"Nota: {nota}"

            # Fila de resultados base
            fila_resultado = {
                'step': step,
                'pregunta': pregunta,
                'respuesta': respuesta,
                'esperado': esperado,
                'salida': salida_formateada,
                'tiempo': tiempo,
                'razonamiento_previo': razonamiento,
                'conceptos_clave_encontrados': str(encontrados),
                'conceptos_clave_omitidos': str(omitidos),
                'nota_numeral': nota,
                'nivel_de_confianza': confianza,
                'fuera_de_contexto': fuera_contexto
            }

            # Rellenar cada tag de concepto (retrocompatibilidad)
            for tag in unique_tags:
                encontrado = False
                # Comprobar de forma flexible si el tag se menciona en los conceptos encontrados
                for c_enc in encontrados:
                    if tag.lower() in c_enc.lower() or c_enc.lower() in tag.lower():
                        encontrado = True
                        break
                fila_resultado[tag] = "sí" if encontrado else "no"

            buffer_salidas.append(fila_resultado)

            # Flush cada 20 elementos
            if len(buffer_salidas) >= 20:
                self.dataset_cliente.guardar_buffer_csv(buffer_salidas, fieldnames)
                buffer_salidas.clear()

            print(f"Progreso: {step + 1} ejemplos procesados")
            step += 1

        # Flush final con lo que quede en el buffer
        if buffer_salidas:
            self.dataset_cliente.guardar_buffer_csv(buffer_salidas, fieldnames)

