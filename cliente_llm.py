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
        
        formateados = []
        for i in messages[0:-1]:
            formateados.append({"type": "text", "text": f"{i}"})

        messages = [
        {
            "role": "system",
            "content": formateados
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"{messages[-1]}"}
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