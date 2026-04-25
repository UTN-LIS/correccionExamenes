class Experimento:
    def __init__(self, cliente_llm, mlflow_client):
        self.entradas = []
        self.contextos = []
        self.salidas = []

        self.cliente_llm = cliente_llm
        self.mlflow = mlflow_client

        self.metricas = []  # lista de clases de métricas

    def registrar_metricas(self, metricas):
        """
        metricas: lista de clases (no instancias)
        Ej: [ExactMatch, Latencia]
        """
        self.metricas = metricas

    def crear_experimento(self, entradas, contextos):
        self.entradas = entradas
        self.contextos = contextos

    def generar_salida(self, entrada, contextos):
        self.cliente_llm.entrada = entrada
        self.cliente_llm.contextos = contextos

        salida, tiempo = self.cliente_llm.generar_salida()
        self.salidas.append(salida)

        return salida, tiempo

    def tomar_metricas(self, entrada, salida, esperado, tiempo):
        resultados = {}

        for metrica_cls in self.metricas:
            metrica = metrica_cls(entrada, salida, esperado, tiempo)
            resultados.update(metrica.calcular())

        self.mlflow.log_metricas(resultados)
        return resultados