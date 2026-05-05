from cliente_llm import ClienteLLM
from experimento import Experimento
from mlflow_client import MLFlowClient
from generador_csv import generadorCSV

from metricas.latencia import Latencia
from metricas.error_nota import ErrorNota
from metricas.tamaño_entrada import TamañoE
from metricas.tamaño_contexto import TamañoC


def main():
    cliente = ClienteLLM()
    mlflow_client = MLFlowClient("Primera_prueba_real", "gemma-3-4b")

    experimento = Experimento(cliente, mlflow_client, modelo="gemma-3-4b")

    # Registrar métricas dinámicamente
    experimento.registrar_metricas([
        Latencia,
        ErrorNota,
        TamañoE,
        TamañoC
    ])
    dataset_generator = generadorCSV()

    experimento.ejecutar_dataset1(dataset_generator)


if __name__ == "__main__":
    main()

