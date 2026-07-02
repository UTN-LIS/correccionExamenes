import pandas as pd
import os
import csv
from dotenv import load_dotenv
from conceptos import CONCEPTOS_POR_PREGUNTA


class GeneradorCSV:
    def __init__(self):
        load_dotenv()
        self.df = pd.read_csv(os.getenv("DATASET_CSV_Entradas"))
        self.csvResultados = os.getenv("DATASET_CSV_Resultados")
        self.configuracionModelo = os.getenv("Configuracion_Modelo")

    def dataset_batch(self):
        """
        Yields tuplas (pregunta, conceptos, respuesta, esperado) por cada fila del dataset.

        Espera las columnas: question_id, question_text, student_answer, teacher_grade.
        Los conceptos se resuelven desde CONCEPTOS_POR_PREGUNTA usando question_id.
        Si el question_id no tiene conceptos definidos, se retorna lista vacía.
        """
        for _, row in self.df.iterrows():
            question_id = row.get("question_id")
            pregunta    = row["question_text"]
            respuesta   = row["student_answer"]
            esperado    = row.get("teacher_grade")
            yield pregunta, respuesta, esperado

    def crear_csv_resultados(self, fieldnames):
        """Crea el archivo CSV de resultados con encabezados."""
        with open(self.csvResultados, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

    def guardar_buffer_csv(self, buffer, fieldnames):
        """Agrega el buffer de diccionarios al archivo CSV de resultados."""
        with open(self.csvResultados, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writerows(buffer)

    def guardar_configuracion(self, modelo: str, system_prompt: str):
        """Guarda la configuración del experimento en un archivo de texto."""
        with open(self.configuracionModelo, 'w', encoding='utf-8') as f:
            f.write(f"Modelo: {modelo}\n")
            f.write(f"System Prompt:\n{system_prompt}\n")