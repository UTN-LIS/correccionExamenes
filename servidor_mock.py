# ejecutar con : uvicorn servidor_mock:app --reload --host localhost --port 8000
from fastapi import FastAPI, Body

app = FastAPI()

@app.post("/chat")
async def chat(body = Body(...)):
    messages = body.get("messages", [])
    user_content = ""
    for msg in messages:
        if msg.get("role") == "user":
            user_content = msg.get("content", "")

    # Determinar el paso de evaluación según el contenido del prompt
    if "RANGO DE NOTA SUGERIDO" in user_content:
        # Paso 3: Nota final
        return {"response": "8"}
    elif "EVALUACIÓN DE CONCEPTOS CLAVE" in user_content:
        # Paso 2: Rango de nota
        return {"response": "<ACEPTABLE>"}
    else:
        # Paso 1: Conceptos individuales
        return {"response": "sí"}