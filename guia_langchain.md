# Guía de Integración de LangChain para Corrección de Exámenes

Este documento describe la arquitectura y el funcionamiento de la integración de **LangChain** implementada en el proyecto de evaluación de exámenes. La solución conecta un orquestador local en Python con un servidor de inferencia de LLM remoto (en Kaggle o Google Colab) mediante túneles seguros de Ngrok.

---

## 1. Arquitectura del Sistema

La solución mantiene la compatibilidad con el pipeline original pero eleva la estructura de prompts y modelos al estándar de LangChain:

```mermaid
graph TD
    subgraph Cliente Local (Tu PC)
        main[main.py] --> exp[experimento.py]
        exp --> client[ClienteLLM]
        client --> lcel[Chain: ChatPromptTemplate | ColabChatModel]
    end

    subgraph Internet
        ngrok[Túnel Ngrok]
    end

    subgraph Servidor de Inferencia (Kaggle / Colab)
        fastapi[FastAPI /chat] --> agent[LangChainAgent]
        agent --> chat_hf[ChatHuggingFace]
        chat_hf --> pipe[HuggingFacePipeline]
        pipe --> model[Qwen2.5-Instruct]
    end

    lcel -- HTTP POST --> ngrok
    ngrok --> fastapi
```

---

## 2. Cambios Implementados

### A. Servidor de Inferencia (`Agente_Qwen3.ipynb`)

1. **Dependencias**: Se agregaron las librerías oficiales de integración de LangChain con Hugging Face (`langchain` y `langchain-huggingface`).
2. **Encapsulamiento del Modelo**: Reemplazamos la llamada manual al template de generación por componentes de LangChain:
   * **`HuggingFacePipeline`**: Envuelve el pipeline de generación de texto nativo.
   * **`ChatHuggingFace`**: Se encarga de aplicar los tokens especiales del template de chat (`<|im_start|>`, `<|im_end|>`) del modelo en Kaggle.
   * **Aumento de Tokens**: Se incrementó el tamaño máximo de salida a `1024` tokens (`max_new_tokens=1024`) en lugar de `40` para poder procesar respuestas estructuradas largas (como explicaciones y JSONs) sin que el texto quede truncado.
3. **Estabilidad de Ngrok**: Se añadió la llamada `ngrok.kill()` antes de crear el túnel para liberar cualquier sesión colgada en el puerto `8000` y evitar el error `ERR_NGROK_334`.

---

### B. Cliente Local (`cliente_llm.py`)

1. **Modelo de Chat de LangChain (`ColabChatModel`)**: 
   Subclase de `BaseChatModel` de LangChain. Este modelo personalizado traduce los mensajes del prompt de LangChain (`SystemMessage`, `HumanMessage`, etc.) al formato JSON que espera tu servidor FastAPI.
2. **Ejecución LCEL (LangChain Expression Language)**:
   La generación de respuestas ahora utiliza el encadenamiento estándar de LangChain:
   ```python
   chain = prompt | self.model
   ```
3. **Soporte Nativo de Salida Estructurada (`with_structured_output`)**:
   Implementamos el método `with_structured_output` dentro de `ColabChatModel`. Al no tener soporte nativo de Tool Calling (API de llamadas a funciones) en un servidor de texto plano, el cliente realiza de manera automática la vinculación con el **`PydanticOutputParser`**:
   * Genera e inyecta las instrucciones de formato JSON al final del prompt.
   * Recibe el string respuesta del LLM y lo parsea automáticamente a una instancia del objeto de **Pydantic** validado.

---

## 3. Instrucciones de Ejecución

### A. Preparación del Entorno
Recuerda que todas las ejecuciones locales deben correrse dentro del entorno virtual del proyecto para disponer de las dependencias correctas (`langchain`, `requests`, `python-dotenv`, etc.).

Activa el entorno virtual:
```bash
source .venv/bin/activate
```

O corre tus scripts usando la ruta directa del ejecutable del entorno virtual:
```bash
.venv/bin/python main.py
```

### B. Cómo probar el experimento tradicional (Bucle de conceptos)
Este experimento evalúa de forma unitaria si un concepto está presente o no.
1. Ejecuta el servidor en Kaggle.
2. Copia la URL de Ngrok y pégala en el `.env` local (`URL_LLM=https://xxxx.ngrok-free.dev`).
3. Ejecuta el experimento desde tu consola local:
   ```bash
   .venv/bin/python main.py
   ```

### C. Cómo probar la corrección estructurada con Pydantic
Si deseas realizar un experimento donde el modelo evalúe múltiples campos en una sola llamada y devuelva un objeto estructurado, puedes ejecutar este bloque en Python usando tu nuevo cliente de LangChain:

```python
from cliente_llm import ClienteLLM
from pydantic import BaseModel, Field
from typing import List
from langchain_core.prompts import ChatPromptTemplate

# 1. Definir el esquema deseado con Pydantic
class EvaluacionExamenUTN(BaseModel):
    razonamiento_previo: str = Field(..., description="Espacio para CoT.")
    conceptos_clave_encontrados: List[str] = Field(..., description="Conceptos correctos.")
    conceptos_clave_omitidos: List[str] = Field(..., description="Conceptos omitidos.")
    nota_numeral: int = Field(..., ge=1, le=10, description="Nota 1-10.")
    nivel_de_confianza: float = Field(..., ge=0.0, le=1.0)
    fuera_de_contexto: bool = Field(...)

# 2. Inicializar el cliente (apunta a la URL_LLM de tu .env)
cliente = ClienteLLM()

# 3. Crear el prompt de chat
prompt = ChatPromptTemplate.from_messages([
    ("system", "Eres un Agente Evaluador de la UTN. Analiza de forma minuciosa."),
    ("user", "Pregunta: {pregunta}\nRespuesta: {respuesta}")
])

# 4. Enlazar el modelo con salida estructurada nativa de LangChain
chain = prompt | cliente.model.with_structured_output(EvaluacionExamenUTN)

# 5. Invocar
resultado = chain.invoke({
    "pregunta": "¿Qué es el ciclo TDD?",
    "respuesta": "TDD consiste en escribir los test primero en rojo, luego el código para verde y finalmente refactor."
})

# El resultado ya es un objeto Pydantic validado con tipado estático
print("Razonamiento previo:", resultado.razonamiento_previo)
print("Nota Numeral:", resultado.nota_numeral)
print("Conceptos encontrados:", resultado.conceptos_clave_encontrados)
```

---

## 4. Dinamismo de los Esquemas de Pydantic

El cliente que construimos **no está atado a un esquema fijo**. Puedes crear cualquier cantidad de experimentos con variables completamente distintas. Solo necesitas definir la clase de Pydantic adecuada para tu experimento:

* **Si necesitas evaluar feedback pedagógico:**
  ```python
  class FeedbackPedagogico(BaseModel):
      fortalezas: List[str] = Field(..., description="Puntos fuertes de la respuesta")
      consejo: str = Field(..., description="Sugerencia de estudio")
  ```

* **Si necesitas una evaluación dicotómica simple:**
  ```python
  class EvaluacionSimple(BaseModel):
      aprobado: bool = Field(..., description="¿El examen está aprobado?")
      observacion: str = Field(..., description="Comentarios generales")
  ```

Al pasar cualquiera de estas clases a `model.with_structured_output(...)`, el sistema automáticamente:
1. Re-genera las instrucciones del formato JSON esperado para el LLM.
2. Parsea la respuesta del texto del modelo en un objeto de esa clase específica.
3. Valida que los tipos de datos coincidan (por ejemplo, convirtiendo el texto de notas a números enteros o flotantes, y strings a booleanos).

