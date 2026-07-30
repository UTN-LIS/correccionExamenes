from cliente_llm import ClienteLLM
from experimento import Experimento
from generador_csv import GeneradorCSV
from gestor_resultados  import GestorResultados


def main():
    cliente          = ClienteLLM()
    dataset_cliente  = GeneradorCSV()
    resultados       = GestorResultados()
    experimento      = Experimento(cliente, dataset_cliente, resultados, modelo="gemma-3-12b")

    experimento.ejecutar_dataset()


if __name__ == "__main__":
    main()
