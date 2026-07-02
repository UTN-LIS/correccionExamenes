# ejecutar con : uvicorn servidor_mock:app --reload --host localhost --port 8000
from fastapi import FastAPI, Body

app = FastAPI()

@app.post("/chat")
async def chat(body = Body(...)):
    # Devuelve un string JSON mockeado que cumple con el esquema EvaluacionExamenUTN
    json_response = """{
        "razonamiento_previo": "El estudiante responde adecuadamente a la consigna.",
        "nota_numeral": 8,
        "nivel_de_confianza": 0.95,
        "fuera_de_contexto": false
    }"""
    return {"response": json_response}