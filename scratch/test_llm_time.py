import requests
import time
import json

URL = "https://transmarginally-unrebuffed-else.ngrok-free.dev"

system_prompt = """
Eres un profesor universitario y evaluador académico experto en ingeniería de software.
Tu tarea es analizar una PREGUNTA de examen y su RESPUESTA CORRECTA ESPERADA (pauta de corrección), y generar una lista de conceptos clave (entre 3 y 5 conceptos) que un estudiante debe mencionar o explicar en su respuesta para ser calificado positivamente.

Para cada concepto clave debes definir:
1. Un tag: Una palabra corta en mayúsculas, usando guiones bajos si es necesario.
2. Una descripción: Una frase clara y corta (máximo 20 palabras) que explique qué aspecto de la respuesta correcta cubre este concepto.

Además, debes incluir siempre al final de la lista un concepto con el tag "ERROR" y la descripción: "Plantea algún concepto de forma ambigua o erróneamente".

Debes responder ÚNICAMENTE con un objeto JSON válido con la estructura exacta:
{
  "conceptos": [
    {
      "tag": "TAG_1",
      "descripcion": "Descripción del concepto 1"
    },
    ...
  ]
}
""".strip()

user_msg = """## PREGUNTA
¿Qué es el ciclo de desarrollo iterativo en TDD y cuáles son sus fases?

## RESPUESTA CORRECTA ESPERADA
El desarrollo en TDD es un ciclo iterativo compuesto por tres fases principales: Rojo (escribir un test que falle porque la funcionalidad no existe), Verde (programar el código mínimo indispensable para que el test pase) y Refactor (limpiar y mejorar el diseño del código sin alterar su funcionalidad externa)."""

payload = {
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg}
    ]
}

print(f"Connecting to: {URL}/chat")
inicio = time.time()
try:
    response = requests.post(
        URL + "/chat",
        json=payload,
        headers={
            "Content-Type": "application/json",
            "ngrok-skip-browser-warning": "69420"
        },
        timeout=180.0
    )
    print("Status Code:", response.status_code)
    elapsed = time.time() - inicio
    print(f"Elapsed time: {elapsed:.2f} seconds")
    print("Response text:")
    print(response.text)
except Exception as e:
    elapsed = time.time() - inicio
    print(f"Failed after {elapsed:.2f} seconds with error: {e}")
