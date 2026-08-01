# ejecutar con : uvicorn servidor_mock:app --reload --host localhost --port 8000
from fastapi import FastAPI, Body

app = FastAPI()

@app.post("/chat")
async def chat(body = Body(...)):
    messages = body.get("messages", [])
    user_content = ""
    system_content = ""
    for msg in messages:
        if msg.get("role") == "user":
            user_content = msg.get("content", "")
        elif msg.get("role") == "system":
            system_content = msg.get("content", "")

    # Determinar el paso de evaluación
    if "RANGO DE NOTA SUGERIDO" in user_content or "criterio pedagógico" in system_content or "calificación final" in system_content:
        # Experimento 3: Nota directa o final
        return {"response": "8"}
    elif "EVALUACIÓN DE CONCEPTOS CLAVE" in user_content or "rango" in system_content.lower():
        # Experimento 2: Rango de nota
        return {"response": "<ACEPTABLE>"}
    else:
        # Experimento 1: Conceptos individuales
        return {"response": "sí"}