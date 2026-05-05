import time
import requests
import os
import json
from dotenv import load_dotenv

class ClienteLLM:
    def __init__(self):
        load_dotenv()
        self.url = os.getenv("URL_LLM")


    def generar_salida(self, messages):
        payload = {
            "messages": messages
        }

        inicio = time.time()

        response = requests.post(
            self.url + "/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        ).json()

        tiempo = time.time() - inicio


        return response["response"], tiempo