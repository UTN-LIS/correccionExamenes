import mlflow

mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("Pregunta simple")

def main():
    print("Hello from proyectolis!")

    with mlflow.start_run():
        mlflow.log_param("test_param", "test_value")
        print("✓ Successfully connected to MLflow!")
if __name__ == "__main__":
    main()
