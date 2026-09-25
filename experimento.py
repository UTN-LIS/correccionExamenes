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
            'pregunta',
            'respuesta',
            'esperado',
            # ... tus columnas anteriores (id, pregunta, respuesta, etc.)
            'nota_directa',
            'tiempo',
            # Nuevas columnas de métricas
            'entropia',
            'perplejidad',
            'masa_acumulada_top_3',
            'masa_notas',
            'masa_no_notas',
            'margen_logit',
            'diferencia_probabilidad',
            'top_3_vocabulario_json',
            'top_3_notas_json'
        ]
        self.dataset_cliente.crear_csv_resultados(fieldnames)


        buffer_salidas = []
        step = 0

        for q_id, pregunta, conceptos, respuesta, esperado, ideal_answer in self.dataset_cliente.dataset_batch():

            if max_items and step >= max_items:
                break


            # ---- EJECUTAR EXPERIMENTOS INDEPENDIENTES ----
            res_nota_directa = evaluar_nota_directa(self.cliente_llm, pregunta, ideal_answer, respuesta)
            metricas = res_nota_directa.get('metricas', {})

            fila_resultado = {
                'step': step,
                'pregunta': pregunta,
                'respuesta': respuesta,
                'esperado': esperado,
                'nota_directa': res_nota_directa['nota_directa'],
                'tiempo': round(res_nota_directa['tiempo'], 3),
                'entropia': metricas.get('entropia'),
                'perplejidad': metricas.get('perplejidad'),
                'masa_acumulada_top_3': metricas.get('masa_acumulada_top_x'),
                'masa_notas': metricas.get('masa_notas'),
                'masa_no_notas': metricas.get('masa_no_notas'),
                'margen_logit': metricas.get('margen_logit'),
                'diferencia_probabilidad': metricas.get('diferencia_probabilidad'),
                'top_3_vocabulario_json': json.dumps(metricas.get('candidatos_vocabulario', []), ensure_ascii=False),
                'top_3_notas_json': json.dumps(metricas.get('candidatos_notas_top_x', []), ensure_ascii=False)
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
