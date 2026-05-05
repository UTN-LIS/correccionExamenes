class Experimento:
    def __init__(self, cliente_llm, mlflow_client, modelo="Modelo_XYZ"):
        self.entradas = []
        self.contextos = []
        self.salidas = []

        self.cliente_llm = cliente_llm
        self.mlflow = mlflow_client

        self.metricas = []  # lista de clases de métricas
        self.modelo = modelo

    def registrar_metricas(self, metricas):
        """
        metricas: lista de clases (no instancias)
        Ej: [ExactMatch, Latencia]
        """
        self.metricas = metricas

    def crear_experimento(self, entradas, contextos):
        # en desuso
        self.entradas = entradas
        self.contextos = contextos

    def generar_salida(self, messages):

        salida, tiempo = self.cliente_llm.generar_salida(messages)
        return salida, tiempo

    def tomar_metricas(self, entrada, contexto, salida, esperado, tiempo, step=None):
        resultados = {}

        for metrica_cls in self.metricas:
            metrica = metrica_cls(entrada, contexto, salida, esperado, tiempo)
            resultados.update(metrica.calcular())

        self.mlflow.log_metricas(resultados, step=step)
        return resultados
    
    def ejecutar_dataset(self, dataset_generator, max_items=None):
        """
        dataset_generator: yield (entrada, contexto, esperado)
        """
        buffer_salidas = []
        step = 0

        for entrada, contexto, esperado in dataset_generator.dataset_batch():

            # corte opcional (para testing o batch controlado)
            if max_items and step >= max_items:
                break


            salida, tiempo = self.generar_salida(entrada, contexto)

            self.tomar_metricas(entrada, contexto, salida, esperado, tiempo, step)

            buffer_salidas.append({
                "entrada": entrada,
                "contexto": contexto,
                "salida": salida
            })

            # flush cada N elementos
            if len(buffer_salidas) >= 50:
                self.mlflow.log_lote(buffer_salidas.copy())
                buffer_salidas.clear()
            
            step += 1

        # flush final
        if buffer_salidas:
            print(buffer_salidas)
            self.mlflow.log_lote(buffer_salidas)

        self.mlflow.cerrar()

    def ejecutar_dataset1(self, dataset_generator, max_items=None):
        """
        dataset_generator: yield (entrada, contextoDinamico, esperado)
        """
        buffer_salidas = []
        step = 0
        fieldnames = ['step', 'entrada', 'contexto', 'salida', 'esperado', 'tiempo']

        contextoEstatico = "Eres un profesor experto que corrige exámenes de estudiantes. Evalúa la respuesta del estudiante en base a la pregunta dada y da una justificacion de tu evaluacion"

        dataset_generator.crear_csv_resultados(fieldnames)

        for entrada, contextoDinamico, esperado in dataset_generator.dataset_batch():

            # corte opcional (para testing o batch controlado)
            if max_items and step >= max_items:
                break
            
            messagesForLLM = [ contextoEstatico, contextoDinamico,  entrada]

            salida, tiempo = self.generar_salida(messagesForLLM)



            # Usar diccionario 
            buffer_salidas.append({
                'step': step,
                'entrada': entrada,
                'contexto': contextoDinamico,
                'salida': salida,
                'esperado': esperado,
                'tiempo': tiempo
            })
            
            # Flush cada 50 elementos
            if len(buffer_salidas) >= 50:
                dataset_generator.guardar_buffer_csv(buffer_salidas, fieldnames)
                buffer_salidas.clear()
                print(f"Progreso: {step + 1} ejemplos procesados")
            
            step += 1
        
        # Flush final
        if buffer_salidas:
            dataset_generator.guardar_buffer_csv(buffer_salidas, fieldnames)


        dataset_generator.guardar_configuracion(self.modelo, contextoEstatico)