import json
import os
import pandas as pd
from dotenv import load_dotenv


class GestorResultados:
    def __init__(self):
        load_dotenv()
        self.jsonl_path = os.getenv("DATASET_JSONL_Resultados")
        self.xlsx_path = os.getenv("DATASET_XLSX_Resultados")
        self.configuracion_path = os.getenv("Configuracion_Modelo")

    def crear_archivo_resultados(self):
        """Crea (o vacía) el archivo JSONL de resultados."""
        open(self.jsonl_path, 'w', encoding='utf-8').close()

    def guardar_buffer(self, buffer: list[dict]):
        """Agrega cada dict del buffer como una línea JSON."""
        with open(self.jsonl_path, 'a', encoding='utf-8') as f:
            for fila in buffer:
                f.write(json.dumps(fila, ensure_ascii=False) + "\n")

    def guardar_configuracion(self, modelo: str, system_prompt: str):
        """Guarda la configuración del experimento en un archivo de texto."""
        with open(self.configuracion_path, 'w', encoding='utf-8') as f:
            f.write(f"Modelo: {modelo}\n")
            f.write(f"System Prompt:\n{system_prompt}\n")

    def generar_excel(self):
        """Lee el JSONL completo y genera una vista plana en .xlsx."""
        filas = []
        with open(self.jsonl_path, 'r', encoding='utf-8') as f:
            for linea in f:
                linea = linea.strip()
                if linea:
                    filas.append(json.loads(linea))

        df = pd.json_normalize(filas)

        # Aplana columnas de listas para que se vean bien en Excel
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, list)).any():
                df[col] = df[col].apply(
                    lambda x: "; ".join(map(str, x)) if isinstance(x, list) else x
                )

        df.to_excel(self.xlsx_path, index=False)