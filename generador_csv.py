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
        Yields tuplas (question_id, pregunta, conceptos, respuesta, esperado, ideal_answer) por cada fila del dataset.

        Espera las columnas: question_id, question_text, student_answer, teacher_grade.
        Los conceptos se resuelven desde CONCEPTOS_POR_PREGUNTA usando question_id.
        Si el question_id no tiene conceptos definidos, se retorna lista vacía.
        """
        import json
        preguntas_db = {}
        if os.path.exists("documentacion/web_app_db.json"):
            try:
                with open("documentacion/web_app_db.json", "r", encoding="utf-8") as f:
                    preguntas_db = json.load(f).get("preguntas", {})
            except Exception:
                pass

        for _, row in self.df.iterrows():
            question_id = str(row.get("question_id", "")).strip()
            pregunta    = row["question_text"]
            respuesta   = row["student_answer"]
            esperado    = row.get("teacher_grade")
            conceptos   = CONCEPTOS_POR_PREGUNTA.get(question_id, [])
            
            # Intentar obtener ideal_answer
            ideal_answer = row.get("ideal_answer")
            if not ideal_answer or pd.isna(ideal_answer):
                ideal_answer = preguntas_db.get(question_id, {}).get("ideal_answer", "")
            if not ideal_answer:
                ideal_answer = "Respuesta ideal de la cátedra."
                
            yield question_id, pregunta, conceptos, respuesta, esperado, ideal_answer

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