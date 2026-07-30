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
            conceptos   = CONCEPTOS_POR_PREGUNTA.get(question_id, [])
            yield pregunta, conceptos, respuesta, esperado

