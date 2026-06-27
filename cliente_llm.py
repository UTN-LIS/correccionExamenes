import time
import requests
import os
from dotenv import load_dotenv


class ClienteLLM:
    def __init__(self):
        load_dotenv()
        self.url = os.getenv("URL_LLM")

    def generar_salida(self, apuntes: str, rubrica: str, pregunta: str, respuesta_alumno: str):
        """
        Llama al LLM (servidor FastAPI) expuesto en /evaluar enviando el EvaluacionRequest.
        Retorna (evaluacion: dict, tiempo: float).
        """
        payload = {
            "apuntes": apuntes,
            "rubrica": rubrica,
            "pregunta": pregunta,
            "respuesta_alumno": respuesta_alumno
        }
        inicio = time.time()

        try:
            response = requests.post(
                self.url + "/evaluar",
                json=payload,
                headers={"Content-Type": "application/json"}
            ).json()
            tiempo = time.time() - inicio
            return response, tiempo

        except Exception as e:
            tiempo = time.time() - inicio
            print(f"Error al llamar al LLM: {e}")
            return {}, tiempo
