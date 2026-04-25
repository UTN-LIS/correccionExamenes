import time
import requests
import os

class ClienteLLM:
    def __init__(self):
        self.url = os.getenv("URL_LLM")
        self.entrada = None
        self.contextos = []
        self.salida = None

    def generar_salida(self):
        payload = {
            "session_id": "1",
            "summary": "",
            "messages": self.contextos + [self.entrada]
        }

        inicio = time.time()

        response = requests.post(
            self.url + "/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        ).json()

        tiempo = time.time() - inicio

        self.salida = response
        return response, tiempo