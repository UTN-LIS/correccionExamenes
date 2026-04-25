import mlflow
from datetime import datetime

class MLFlowClient:
    def __init__(self, experiment_name):
        mlflow.set_experiment(experiment_name)

    def log_metricas(self, metricas: dict):
        with mlflow.start_run():
            for k, v in metricas.items():
                if isinstance(v, (int, float)):
                    mlflow.log_metric(k, v)

            mlflow.set_tag("timestamp", datetime.now().isoformat())