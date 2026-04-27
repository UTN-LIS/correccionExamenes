from cliente_llm import ClienteLLM
from experimento import Experimento
from mlflow_client import MLFlowClient

from metricas.latencia import Latencia
from metricas.error_nota import ErrorNota
from metricas.tamaño_entrada import TamañoE


def main():
    cliente = ClienteLLM()
    mlflow_client = MLFlowClient("Primera prueba llm")

    experimento = Experimento(cliente, mlflow_client)

    # Registrar métricas dinámicamente
    experimento.registrar_metricas([
        Latencia,
        ErrorNota,
        TamañoE
    ])

    entrada = {"role": "user", "content": "pregunta 'Explica el ciclo TDD  y su importancia en el desarrollo de software.' respuesta 'El TDD en inglés es Test-Driven Development, es un mecanismo de test independientes para el proceso de un proyecto. En primer lugar, está el test en rojo, es decir, los test de la práctica están fallando porque no está implementado. En segundo lugar, el test verde, es decir, se ha implementado los métodos necesarios para probar la ejecución. No importaría el largo del código sino su funcionamiento. Y, por último, está el refactor, se ha corregido dicha implementación para mejorar el código y su implementación. En otras palabras, no se modifica su funcionamiento, pero sí el código para hacerlo más dinámico. Es un ciclo el cuál empieza en rojo -> verde -> refactor. Nos ayuda a comprobar si los métodos implementados han sido utilizados en los test y qué está fallando.'"}
    contexto = [{"role": "system", "content": "Eres un asistente útil que califica respuestas a examenes como si fuera un profesor. responde unicamente con la nota numerica del 1 al 10"}]

    salida, tiempo = experimento.generar_salida(entrada, contexto)

    metricas = experimento.tomar_metricas(
        entrada,
        contexto,
        salida,
        esperado="7.0",
        tiempo=tiempo
    )
    mlflow_client.cerrar()
    print("Salida:", salida)
    print("Métricas:", metricas)


if __name__ == "__main__":
    main()


"""
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
"""