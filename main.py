import os
from cliente_llm import ClienteLLM
from experimento import Experimento
from generador_csv import GeneradorCSV
from procesar_metricas import procesar_csv

def main():
    cliente          = ClienteLLM()
    dataset_cliente  = GeneradorCSV()
    experimento      = Experimento(cliente, dataset_cliente, modelo="gemma-3-12b")

    experimento.ejecutar_dataset()
    
    # Procesar métricas automáticamente al finalizar
    csv_resultados = dataset_cliente.csvResultados
    if csv_resultados and os.path.exists(csv_resultados):
        print("\n" + "="*60)
        print("PROCESANDO MÉTRICAS AUTOMÁTICAMENTE AL FINALIZAR EL EXPERIMENTO")
        print("="*60)
        procesar_csv(csv_resultados)

if __name__ == "__main__":
    main()
