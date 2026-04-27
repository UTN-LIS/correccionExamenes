from fastapi import FastAPI, Body
# para no ejecutar el servidor llm real
app = FastAPI()

@app.get("/")
def root():
    return {"mensaje": "Hola desde FastAPI"}

@app.post("/chat")
async def chat(body= Body(...)):
    return {
        "response": "7.3",
        "session_id": 1
    }


# ejecutar con : uvicorn servidor_mock:app --reload --host localhost --port 8000