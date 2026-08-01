import os
import sys

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set LLM URL to local mock server
os.environ["URL_LLM"] = "http://127.0.0.1:8000"

from cliente_llm import ClienteLLM
from generador_csv import GeneradorCSV
from experimento import Experimento

def main():
    print("Iniciando prueba con servidor mock...")
    cliente = ClienteLLM()
    # Cambiar temporalmente la ruta de salida para la prueba
    dataset_cliente = GeneradorCSV()
    dataset_cliente.csvResultados = "./documentacion/resultados_prueba_independiente.csv"
    
    experimento = Experimento(cliente, dataset_cliente, modelo="gemma-3-12b-mock")

    # Ejecutar sólo 3 items para verificar la velocidad y correcto guardado
    print("Ejecutando dataset...")
    experimento.ejecutar_dataset(max_items=3, w1=0.5, w2=0.25, w3=0.25)
    print("Prueba finalizada con éxito. Archivo de resultados guardado en:", dataset_cliente.csvResultados)

if __name__ == "__main__":
    main()
