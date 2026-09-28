import time, json
from grading_logic import insertar_ordenado
from collections import defaultdict

class Experimento:
    def __init__(self, cliente_llm, dataset_cliente, modelo="Modelo_XYZ"):
        self.dataset_cliente = dataset_cliente
        self.cliente_llm = cliente_llm
        self.modelo = modelo
    
    def ejecutar_dataset(self, max_items=None):
        """
        Itera el dataset y va rankeando cada respuesta contra una lista ordenada
        persistente, usando inserción por búsqueda binaria.
        """
        fieldnames = [
            "step",
            "q_id",
            "pregunta",
            "respuesta",
            "esperado",
            "tiempo",
            "posicion",
            "tam_lista_pregunta",
            "n_comparaciones",
        ]
        self.dataset_cliente.crear_csv_resultados(fieldnames)
    
        # IMPORTANTE: estas dos estructuras tienen ciclos de vida distintos.
        # listas_ordenadas: persiste TODO el run, nunca se limpia (es la referencia
        #                 para comparar respuestas futuras). Una lista POR PREGUNTA
        #                 (q_id) -- nunca mezclar respuestas de preguntas distintas
        #                 en la misma lista, porque el comparador solo tiene sentido
        #                 entre respuestas a la MISMA pregunta (así lo asume su
        #                 system prompt).
        # filas_pendientes: solo las filas nuevas desde el último flush a CSV.
        listas_ordenadas = defaultdict(list)
        filas_pendientes = []
        step = 0
    
        for q_id, pregunta, respuesta, esperado, ideal_answer in self.dataset_cliente.dataset_batch():
            if max_items and step >= max_items:
                break
    
            tam_lista_pregunta = len(listas_ordenadas[q_id])  # tamaño ANTES de insertar
    
            idx, tiempo, n_comp = insertar_ordenado(
                self.cliente_llm, pregunta, ideal_answer, respuesta, listas_ordenadas[q_id]
            )
    
            fila_resultado = {
                "step": step,
                "q_id": q_id,
                "pregunta": pregunta,
                "respuesta": respuesta,
                "esperado": esperado,
                "tiempo": tiempo,
                "posicion": idx,  # 0 = mejor respuesta a ESTA pregunta vista hasta el momento
                "tam_lista_pregunta": tam_lista_pregunta,  # para normalizar: posicion / tam_lista_pregunta
                "n_comparaciones": n_comp,
            }
            filas_pendientes.append(fila_resultado)
    
            # Flush cada 20 filas nuevas (bug original: usaba '&' en vez de '%')
            if len(filas_pendientes) % 20 == 0:
                self.dataset_cliente.guardar_buffer_csv(filas_pendientes, fieldnames)
                filas_pendientes.clear()
    
            print(f"Progreso: {step + 1} ejemplos procesados (posición: {idx}, comparaciones: {n_comp})")
            step += 1
    
        if filas_pendientes:
            self.dataset_cliente.guardar_buffer_csv(filas_pendientes, fieldnames)