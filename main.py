from cliente_llm import ClienteLLM
from experimento import Experimento
from generador_csv import GeneradorCSV


def main():
    cliente          = ClienteLLM()
    dataset_cliente  = GeneradorCSV()
    experimento      = Experimento(cliente, dataset_cliente, modelo="gemma-3-12b")

    experimento.ejecutar_dataset()


if __name__ == "__main__":
    main()
