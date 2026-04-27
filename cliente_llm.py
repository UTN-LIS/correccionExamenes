import time
import requests
import os
import json

class ClienteLLM:
    def __init__(self):
        self.url = os.getenv("URL_LLM")


    def generar_salida(self, entrada, contextos):
        payload = {
            "session_id": "1",
            "summary": "",
            "messages": [{"role": "system", "content": "Eres un asistente útil que califica respuestas a examenes como si fuera un profesor. responde unicamente con la nota numerica"},contextos, entrada]
        }

        inicio = time.time()

        response = requests.post(
            self.url + "/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        ).json()

        tiempo = time.time() - inicio


        return response["response"], tiempo