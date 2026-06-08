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
        
        messages = [
        {
            "role": "system",
            "content": [
                {"type": "text", "text": f"{[messages[0], messages[1]]}"}
            ]
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"{[messages[2], messages[3]]}"}
            ]
        }
        ]

        payload = {
            "messages": messages
        }
        inicio = time.time()
 
        try:
            response = requests.post(
                self.url + "/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            ).json()
            tiempo = time.time() - inicio
            return response["response"], tiempo
            
        except Exception as e:
            tiempo = time.time() - inicio
            return {
                "response": "respuesta no obtenida"
            }, int(tiempo)