import time, json
from grading_logic import  evaluar_nota_directa

class Experimento:
    def __init__(self, cliente_llm, dataset_cliente, modelo="Modelo_XYZ"):
        self.dataset_cliente = dataset_cliente
        self.cliente_llm = cliente_llm
        self.modelo = modelo

    def ejecutar_dataset(self, max_items=None):
        """
        Itera el dataset y ejecuta la evaluación en experimentos independientes:
        Experimento: Obtener la nota final directa.

        """

        # Las columnas del CSV incluyen campos principales, rango, salida (nota final) 
        fieldnames = [
            'step',
            'q_id',
            'pregunta',
            'respuesta',
            'esperado',
            # ... tus columnas anteriores (id, pregunta, respuesta, etc.)
            'nota_directa',
            'tiempo',
        ]
        self.dataset_cliente.crear_csv_resultados(fieldnames)


        buffer_salidas = []
        step = 0

        for q_id, pregunta, respuesta, esperado, ideal_answer in self.dataset_cliente.dataset_batch():

            if max_items and step >= max_items:
                break


            # ---- EJECUTAR EXPERIMENTOS INDEPENDIENTES ----
            res_nota_directa = evaluar_nota_directa(self.cliente_llm, pregunta, ideal_answer, respuesta)

            fila_resultado = {
                'step': step,
                'q_id': q_id,
                'pregunta': pregunta,
                'respuesta': respuesta,
                'esperado': esperado,
                'nota_directa': res_nota_directa['nota_directa'],
                'tiempo': round(res_nota_directa['tiempo'], 3),
            }
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
