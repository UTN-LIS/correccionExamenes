import time
from grading_logic import evaluar_conceptos, evaluar_rango, evaluar_nota_directa, ensamblar_nota_final

class Experimento:
    def __init__(self, cliente_llm, dataset_cliente, modelo="Modelo_XYZ"):
        self.dataset_cliente = dataset_cliente
        self.cliente_llm = cliente_llm
        self.modelo = modelo

    def ejecutar_dataset(self, max_items=None, w1=0.10, w2=0.05, w3=0.85):
        """
        Itera el dataset y ejecuta la evaluación en 3 experimentos independientes:
        Experimento 1: Evaluar conceptos clave uno a uno y obtener cobertura.
        Experimento 2: Evaluar rango de nota de forma independiente.
        Experimento 3: Obtener la nota final directa.
        Consolida la nota usando la combinación lineal ponderada.
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
        fieldnames = ['step', 'pregunta', 'respuesta', 'rango_nota', 'nota_conceptos', 'nota_rango', 'nota_directa', 'salida', 'esperado', 'tiempo'] + unique_tags

        self.dataset_cliente.crear_csv_resultados(fieldnames)
        
        # Guardar configuración descriptiva con los pesos del ensamble
        prompt_config_desc = (
            f"Ensamble Ponderado: Nota_Final = (w1 * conceptos) + (w2 * rango) + (w3 * nota_directa)\n"
            f"Pesos configurados: w1={w1}, w2={w2}, w3={w3}"
        )
        self.dataset_cliente.guardar_configuracion(self.modelo, prompt_config_desc)

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
                'nota_conceptos': 0.0,
                'nota_rango': 0.0,
                'nota_directa': 0.0,
                'salida': "",
                'tiempo': 0.0
            }
            for tag in unique_tags:
                fila_resultado[tag] = ""

            # ---- EJECUTAR EXPERIMENTOS INDEPENDIENTES ----
            # En esta rama, solo ejecutamos evaluar_nota_directa para ahorrar tiempo y llamadas
            res_conceptos = {
                "conceptos_evaluados": {},
                "cobertura": 0.0,
                "nota_conceptos": 0.0,
                "tiempo": 0.0
            }
            res_rango = {
                "rango": "<INSUFICIENTE>",
                "nota_rango": 0.0,
                "tiempo": 0.0
            }
            res_nota_directa = evaluar_nota_directa(self.cliente_llm, pregunta, respuesta)

            # ---- ENSAMBLE PONDERADO ----
            res_ensemble = ensamblar_nota_final(
                res_conceptos,
                res_rango,
                res_nota_directa,
                w1=w1,
                w2=w2,
                w3=w3
            )

            # Llenar la fila del resultado
            fila_resultado['rango_nota'] = res_rango['rango']
            fila_resultado['nota_conceptos'] = res_conceptos['nota_conceptos']
            fila_resultado['nota_rango'] = res_rango['nota_rango']
            fila_resultado['nota_directa'] = res_nota_directa['nota_directa']
            fila_resultado['salida'] = res_ensemble['nota_final']
            fila_resultado['tiempo'] = round(res_conceptos['tiempo'] + res_rango['tiempo'] + res_nota_directa['tiempo'], 3)

            # Rellenar los tags correspondientes
            for tag, val in res_conceptos['conceptos_evaluados'].items():
                if tag in unique_tags:
                    fila_resultado[tag] = val


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
