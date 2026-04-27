import json
import tempfile
import mlflow
import os

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


        tmp_file = tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            suffix=".json",
            encoding="utf-8"
        )

        try:
            json.dump(datos, tmp_file, ensure_ascii=False, indent=2)

            tmp_file.flush()
            tmp_file.close()  # 🔥 CLAVE (especialmente en Windows)

            mlflow.log_artifact(
                tmp_file.name,
                artifact_path=f"outputs/chunk_{self.chunk_id}"
            )

        finally:
            os.unlink(tmp_file.name)  # limpiar archivo local

        self.chunk_id += 1
        return

    def cerrar(self):
        mlflow.end_run()