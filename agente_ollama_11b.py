import os
import uvicorn
import json
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# 1. Esquema de Salida con Pydantic (sin justificacion_pedagogica)
class EvaluacionExamenUTN(BaseModel):
    razonamiento_previo: str = Field(
        ..., 
        description="Espacio para implementar Chain-of-Thought. El modelo debe analizar analíticamente la respuesta del estudiante contrastada con los apuntes ANTES de calcular la nota."
    )
    conceptos_clave_encontrados: List[str] = Field(
        ..., 
        description="Términos o ideas requeridas presentes en la respuesta del alumno."
    )
    conceptos_clave_omitidos: List[str] = Field(
        ..., 
        description="Conceptos obligatorios de los apuntes que el estudiante no mencionó."
    )
    nota_numeral: int = Field(
        ..., 
        ge=1, 
        le=10, 
        description="Calificación final numérica obligatoriamente en el rango del 1 al 10."
    )
    nivel_de_confianza: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Grado de certeza del modelo en su propia corrección en el rango de 0.0 a 1.0."
    )
    fuera_de_contexto: bool = Field(
        ..., 
        description="Un flag True/False que indique si el alumno respondió algo correcto de internet pero que NO estaba en los apuntes oficiales de la cátedra."
    )

# Esquema para recibir los 4 parámetros dinámicos
class EvaluacionRequest(BaseModel):
    apuntes: str
    rubrica: str
    pregunta: str
    respuesta_alumno: str

# 2. Inicialización del Modelo Local de Transformers (google/gemma-4-12B-it)
from transformers import AutoProcessor, AutoModelForMultimodalLM

print("Cargando procesador y modelo google/gemma-4-12B-it...")
processor = AutoProcessor.from_pretrained("google/gemma-4-12B-it")
model = AutoModelForMultimodalLM.from_pretrained("google/gemma-4-12B-it",
                                                device_map="auto",
                                                max_memory={
                                                    0: "13GiB",
                                                    1: "13GiB",
                                                    "cpu": "30GiB"
                                                },
                                                trust_remote_code=True,
                                            )

# 3. Clase Wrapper de LangChain para Salida Estructurada
class StructuredGemma:
    def __init__(self, model, processor, schema):
        self.model = model
        self.processor = processor
        self.schema = schema

    def invoke(self, prompt_value):
        # Convertir PromptValue a la estructura de mensajes del template
        messages = []
        for msg in prompt_value.to_messages():
            role = "user" if msg.type == "human" else "system" if msg.type == "system" else "assistant"
            messages.append({"role": role, "content": msg.content})
        
        # Inyectar instrucción JSON basada en el esquema de Pydantic
        schema_json = json.dumps(self.schema.model_json_schema(), indent=2, ensure_ascii=False)
        json_instruction = (
            f"\n\nDebes responder UNICAMENTE con un objeto JSON plano que cumpla estrictamente "
            f"con el siguiente esquema de Pydantic:\n{schema_json}\n"
            "No agregues texto explicativo, markdown ni bloques de código. Solo el JSON plano."
        )
        if messages and messages[-1]["role"] == "user":
            messages[-1]["content"] += json_instruction
        else:
            messages.append({"role": "user", "content": json_instruction})

        # Preparar inputs con el procesador según lo solicitado por el usuario
        inputs = self.processor.apply_chat_template(
            messages,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
            add_generation_prompt=True,
            enable_thinking=False
        ).to(self.model.device)
        input_len = inputs["input_ids"].shape[-1]
        
        # Generar salida
        outputs = self.model.generate(**inputs, max_new_tokens=1024)
        response = self.processor.decode(outputs[0][input_len:], skip_special_tokens=False)
        
        # Limpieza de la salida
        clean_response = response.strip()
        clean_response = clean_response.replace("<|im_end|>", "").replace("<|eot_id|>", "").strip()
        
        if "```json" in clean_response:
            clean_response = clean_response.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_response:
            clean_response = clean_response.split("```")[1].split("```")[0].strip()
            
        try:
            return self.schema.model_validate_json(clean_response)
        except Exception:
            return self.schema.parse_raw(clean_response)

class ChatGemma:
    def __init__(self, model, processor):
        self.model = model
        self.processor = processor

    def with_structured_output(self, schema):
        return StructuredGemma(self.model, self.processor, schema)

chat_model = ChatGemma(model, processor)

# 4. Prompt de Sistema y Construcción de la Cadena
from langchain_core.prompts import ChatPromptTemplate

system_prompt = (
    "Eres un Agente Evaluador de la UTN (Universidad Tecnológica Nacional), experto en corrección de exámenes universitarios.\n"
    "Tu tarea es evaluar la respuesta del estudiante contrastándola minuciosamente con los apuntes oficiales y la rúbrica de evaluación provista.\n"
    "Es obligatorio que uses razonamiento analítico (Chain-of-Thought) en el campo razonamiento_previo ANTES de definir la nota y determinar qué conceptos se omitieron o se incluyeron.\n"
    "Sé extremadamente preciso y asegúrate de que el formato coincida estrictamente con el esquema requerido."
)

user_prompt = """
Utiliza la siguiente información para realizar la evaluación estructurada de la respuesta del estudiante:

### APUNTES OFICIALES DE LA CÁTEDRA:
{apuntes}

### RÚBRICA DE EVALUACIÓN:
{rubrica}

### PREGUNTA DEL EXAMEN:
{pregunta}

### RESPUESTA DEL ESTUDIANTE A EVALUAR:
{respuesta_alumno}

Analiza con cuidado y genera el objeto estructurado.
"""

prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", user_prompt)
])

# Unimos el prompt y el modelo forzando salida estructurada
chain = prompt_template | chat_model.with_structured_output(EvaluacionExamenUTN)

# 5. Inicialización de FastAPI
from pyngrok import ngrok
import nest_asyncio

ngrok.set_auth_token("344HT0PzWr1pGVLwZBa7KWXfxXE_4FMsfMKfHFpG8ZAQXrpS7")
nest_asyncio.apply()

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Hola desde Colab + FastAPI + LangChain + Gemma4!"}

@app.post("/evaluar", response_model=EvaluacionExamenUTN)
async def evaluar_examen(body: EvaluacionRequest):
    inputs = {
        "apuntes": body.apuntes,
        "rubrica": body.rubrica,
        "pregunta": body.pregunta,
        "respuesta_alumno": body.respuesta_alumno
    }
    try:
        resultado = chain.invoke(inputs)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mantenemos también el endpoint POST /chat para compatibilidad
@app.post("/chat", response_model=EvaluacionExamenUTN)
async def chat(body: EvaluacionRequest):
    return await evaluar_examen(body)

if __name__ == "__main__":
    # Crear túnel en el puerto 3000
    public_url = ngrok.connect(3000)
    print("URL pública:", public_url)

    config = uvicorn.Config(app=app, host="0.0.0.0", port=3000)
    server = uvicorn.Server(config)
    uvicorn.run(app, host="0.0.0.0", port=3000)