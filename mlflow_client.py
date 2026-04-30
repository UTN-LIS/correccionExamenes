import json
import tempfile
import mlflow
import os
import shutil

class MLFlowClient:
    def __init__(self, experiment_name, modelo="no especificado"):
        mlflow.set_experiment(experiment_name)
        mlflow.start_run()

        mlflow.log_param("modelo", modelo)

        self.chunk_id = 0

    def log_metricas(self, metricas, step=None):
        for k, v in metricas.items():
            if isinstance(v, (int, float)):
                mlflow.log_metric(k, v, step=step)

    def log_lote(self, datos):


        if not datos:
            return  # evita archivos vacíos


        tmpdir = tempfile.mkdtemp()
        try:
            # Ruta del archivo con el nombre deseado
            file_path = os.path.join(tmpdir, f"chunk_{self.chunk_id}.json")

            # Escribimos el JSON en ese archivo
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)  # limpiar archivo local

        self.chunk_id += 1
        return

    def cerrar(self):
        mlflow.end_run()