import time
import requests
import os
from dotenv import load_dotenv

CRITERIO_DOCENTE = """La respuesta debe explicar correctamente el nucleo tecnico de la pregunta segun la respuesta correcta esperada.
No debe contener contradicciones graves con la respuesta correcta.
No debe ser vaga, repetir los terminos de la pregunta ni usar lenguaje academico sin contenido real.
No debe estar incompleta ni cortarse a la mitad."""

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
        inicio = time.time()
        try:
            response = requests.post(
                self.url + "/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            ).json()
            tiempo = time.time() - inicio
            return response, tiempo

        except Exception as e:
            tiempo = time.time() - inicio
            print(f"Error al llamar al LLM: {e}")
            return {"response": "", "metricas": {}, "error": str(e)}, tiempo


    def puntuar(self, pregunta, respuesta_correcta, respuesta_estudiante, criterio=CRITERIO_DOCENTE):
        payload = {
            "instruction": criterio,
            "query": f"Pregunta: {pregunta}\n\nRespuesta correcta esperada: {respuesta_correcta}",
            "document": respuesta_estudiante,
        }
        inicio = time.time()
        try:
            response = requests.post(self.url + "/rerank", json=payload).json()
            return response, time.time() - inicio   # response["logit"] para ordenar
        except Exception as e:
            print(f"Error al llamar al reranker: {e}")
            return {"score": None, "logit": None, "error": str(e)}, time.time() - inicio