from prompts import SYSTEM_PROMPT, construir_user_message


class Experimento:
    def __init__(self, cliente_llm, dataset_cliente, modelo="Modelo_XYZ"):
        self.dataset_cliente = dataset_cliente
        self.cliente_llm = cliente_llm
        self.modelo = modelo

    def generar_salida(self, pregunta: str, conceptos: list, respuesta: str):
        """
        Construye los mensajes y llama al LLM.
        Retorna (salida: str, tiempo: float).
        """
        user_message = construir_user_message(pregunta, conceptos, respuesta)
        salida, tiempo = self.cliente_llm.generar_salida(SYSTEM_PROMPT, user_message)
        return salida, tiempo

    def ejecutar_dataset(self, max_items=None):
        """
        Itera el dataset, llama al LLM por cada concepto de cada fila y guarda los resultados en CSV.
        """
        from conceptos import CONCEPTOS_POR_PREGUNTA

        # Obtener todos los conceptos únicos para usarlos como encabezados de columnas
        unique_tags = []
        for lista in CONCEPTOS_POR_PREGUNTA.values():
            for c in lista:
                if c["tag"] not in unique_tags:
                    unique_tags.append(c["tag"])
        unique_tags.sort()

        # Los encabezados de salida ahora no tienen 'salida', sino las columnas de conceptos
        fieldnames = ['step', 'pregunta', 'respuesta', 'esperado', 'tiempo'] + unique_tags

        self.dataset_cliente.crear_csv_resultados(fieldnames)
        self.dataset_cliente.guardar_configuracion(self.modelo, SYSTEM_PROMPT)

        buffer_salidas = []
        step = 0

        for pregunta, conceptos, respuesta, esperado in self.dataset_cliente.dataset_batch():

            if max_items and step >= max_items:
                break

            # Inicializar la fila del resultado con las columnas principales y los tags en vacío
            fila_resultado = {
                'step': step,
                'pregunta': pregunta,
                'respuesta': respuesta,
                'esperado': esperado,
                'tiempo': 0.0
            }
            for tag in unique_tags:
                fila_resultado[tag] = ""

            # Iterar por cada concepto del conjunto de conceptos definidos para esta pregunta
            if conceptos:
                for concepto in conceptos:
                    tag = concepto['tag']
                    # Hacer la consulta para este único concepto
                    salida, tiempo = self.generar_salida(pregunta, [concepto], respuesta)
                    
                    # Limpiar y guardar el resultado binario (sí/no)
                    clean_salida = salida.strip().lower().rstrip('.')
                    fila_resultado[tag] = clean_salida
                    fila_resultado['tiempo'] += tiempo

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

