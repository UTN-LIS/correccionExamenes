from cliente_llm import ClienteLLM
from experimento import Experimento
from generador_csv import generadorCSV


def main():
    cliente = ClienteLLM()
    experimento = Experimento(cliente, modelo="gemma-3-12b")
    dataset_generator = generadorCSV()
    experimento.ejecutar_dataset(dataset_generator)


if __name__ == "__main__":
    main()

