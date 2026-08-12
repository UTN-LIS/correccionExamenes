import time
import requests
import os
from dotenv import load_dotenv


class ClienteLLM:
    def __init__(self):
        load_dotenv()
        self.url = os.getenv("URL_LLM")

    def generar_salida(self, system_prompt: str, user_message: str, max_retries: int = 3, backoff_factor: float = 1.5, timeout: float = 180.0):
        """
        Llama al LLM con un system prompt y un user message ya construidos.
        Retorna (respuesta: str, tiempo: float).
        Con reintentos y retroceso exponencial ante fallos de conexión o timeout.
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
        
        for attempt in range(max_retries):
            inicio = time.time()
            try:
                response = requests.post(
                    self.url + "/chat",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "ngrok-skip-browser-warning": "69420"
                    },
                    timeout=timeout  # Evita que se cuelgue indefinidamente
                )
                response.raise_for_status()
                res_json = response.json()
                tiempo = time.time() - inicio
                return res_json["response"], tiempo

            except Exception as e:
                tiempo = time.time() - inicio
                print(f"Advertencia: Error al llamar al LLM (Intento {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    sleep_time = backoff_factor ** attempt
                    print(f"Aguardando {sleep_time:.2f} segundos antes de realizar el intento {attempt + 2}/{max_retries}...")
                    time.sleep(sleep_time)
                else:
                    print(f"Error crítico: Se agotaron los reintentos para la llamada al LLM: {e}")
                    return "respuesta no obtenida", tiempo
