import pandas as pd
import os
from dotenv import load_dotenv

class generadorCSV:
    def __init__(self):
        load_dotenv()
        self.df = pd.read_csv(os.getenv("DATASET_CSV"))

    def dataset_batch(self):
        for _, row in self.df.iterrows():
            entrada = {"role": "user", "content": row["student_answer"]}
            contexto = {"role": "system", "content": row["question_text"]}
            esperado = row.get("teacher_grade")

            yield entrada, contexto, esperado