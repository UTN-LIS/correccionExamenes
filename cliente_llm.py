import time
import requests
import os
from dotenv import load_dotenv


class ClienteLLM:
    def __init__(self):
        load_dotenv()
        self.url = os.getenv("URL_LLM")

    def generar_salida(self, system_prompt: str, user_message: str):
        """
        Llama al LLM con un system prompt y un user message ya construidos.
        Retorna (respuesta: str, tiempo: float).
        """
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_message
            }
        ]

        payload = {"messages": messages}
        inicio = time.time()

        try:
            response = requests.post(
                self.url + "/chat",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "ngrok-skip-browser-warning": "69420"
                }
            ).json()
            tiempo = time.time() - inicio
            return response["response"], tiempo

        except Exception as e:
            tiempo = time.time() - inicio
            print(f"Error al llamar al LLM: {e}")
            return "respuesta no obtenida", tiempo
