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
        user_message = construir_user_message(pregunta, respuesta)
        salida, tiempo = self.cliente_llm.generar_salida(SYSTEM_PROMPT, user_message)
        return salida, tiempo

    def ejecutar_dataset(self, max_items=None):
        """
        Itera el dataset, llama al LLM por cada item y guarda los resultados en CSV.
        """
        buffer_salidas = []
        step = 0
        fieldnames = ['step', 'pregunta', 'respuesta', 'salida', 'esperado', 'tiempo']

        self.dataset_cliente.crear_csv_resultados(fieldnames)
        self.dataset_cliente.guardar_configuracion(self.modelo, SYSTEM_PROMPT)

        for pregunta, conceptos, respuesta, esperado in self.dataset_cliente.dataset_batch():

            if max_items and step >= max_items:
                break

            salida, tiempo = self.generar_salida(pregunta, conceptos, respuesta)

            buffer_salidas.append({
                'step':      step,
                'pregunta':  pregunta,
                'respuesta': respuesta,
                'salida':    salida,
                'esperado':  esperado,
                'tiempo':    tiempo
            })

            # Flush cada 20 elementos
            if len(buffer_salidas) >= 20:
                self.dataset_cliente.guardar_buffer_csv(buffer_salidas, fieldnames)
                buffer_salidas.clear()

            print(f"Progreso: {step + 1} ejemplos procesados")
            step += 1

        # Flush final con lo que quede en el buffer
        if buffer_salidas:
            self.dataset_cliente.guardar_buffer_csv(buffer_salidas, fieldnames)
