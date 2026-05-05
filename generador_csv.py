import pandas as pd
import os
import csv
from dotenv import load_dotenv

class generadorCSV:
    def __init__(self):
        load_dotenv()
        self.df = pd.read_csv(os.getenv("DATASET_CSV_Entradas"))
        self.csvResultados = os.getenv("DATASET_CSV_Resultados")
        self.configuracionModelo = os.getenv("Configuracion_Modelo")

    def dataset_batch(self):
        for _, row in self.df.iterrows():
            entrada = "Respuesta: " + row["student_answer"]
            contexto =  "Pregunta: " + row["question_text"]
            esperado = row.get("teacher_grade")

            yield entrada, contexto, esperado

    def crear_csv_resultados(self, fieldnames):
        """Crea un nuevo archivo CSV con encabezados para los resultados"""

        with open(self.csvResultados, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

    def guardar_buffer_csv(self, buffer, fieldnames):
        """Guarda el buffer de diccionarios en el archivo CSV"""
        with open(self.csvResultados, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writerows(buffer)

    def guardar_configuracion(self, modelo, contextoEstatico):
        """Guarda la configuración del experimento en un archivo de texto"""
        with open(self.configuracionModelo, 'w', encoding='utf-8') as f:
            f.write(f"Modelo: {modelo}\n")
            f.write(f"Contexto Estático: {contextoEstatico}\n")