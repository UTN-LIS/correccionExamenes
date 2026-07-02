import time
from pydantic import BaseModel, Field
from prompts import SYSTEM_PROMPT, construir_user_message
from langchain_core.prompts import ChatPromptTemplate


# Esquema de salida Pydantic para el experimento estructurado
class EvaluacionExamenUTN(BaseModel):
    razonamiento_previo: str = Field(..., description="Espacio para CoT.")
    nota_numeral: int = Field(..., ge=1, le=10, description="Nota 1-10.")
    nivel_de_confianza: float = Field(..., ge=0.0, le=1.0)
    fuera_de_contexto: bool = Field(...)


class Experimento:
    def __init__(self, cliente_llm, dataset_cliente, modelo="Modelo_XYZ"):
        self.dataset_cliente = dataset_cliente
        self.cliente_llm = cliente_llm
        self.modelo = modelo

    def generar_salida(self, pregunta: str, respuesta: str, respuesta_esperada: str):
        """
        Construye los mensajes y llama al LLM forzando una salida estructurada.
        Retorna (resultado: EvaluacionExamenUTN, tiempo: float).
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("user", "{user_message}")
        ])

        # Construir la cadena estructurada con el esquema Pydantic
        chain = prompt | self.cliente_llm.model.with_structured_output(EvaluacionExamenUTN)

        user_message = construir_user_message(pregunta, respuesta, respuesta_esperada)
        inicio = time.time()

        try:
            resultado = chain.invoke({"user_message": user_message})
            tiempo = time.time() - inicio
            return resultado, tiempo
        except Exception as e:
            tiempo = time.time() - inicio
            print(f"Error al generar salida estructurada de LangChain: {e}")
            # Fallback en caso de error para no detener la ejecución del lote
            fallback = EvaluacionExamenUTN(
                razonamiento_previo="Error de procesamiento de salida",
                nota_numeral=1,
                nivel_de_confianza=0.0,
                fuera_de_contexto=False
            )
            return fallback, tiempo

    def ejecutar_dataset(self, max_items=None):
        """
        Itera el dataset, llama al LLM por cada item y guarda los resultados en CSV.
        """
        buffer_salidas = []
        step = 0
        fieldnames = [
            'step', 'pregunta', 'respuesta', 'salida', 'esperado', 'tiempo',
            'razonamiento_previo', 'nivel_de_confianza', 'fuera_de_contexto'
        ]

        self.dataset_cliente.crear_csv_resultados(fieldnames)
        self.dataset_cliente.guardar_configuracion(self.modelo, SYSTEM_PROMPT)

        for pregunta, respuesta, esperado in self.dataset_cliente.dataset_batch():

            if max_items and step >= max_items:
                break

            resultado, tiempo = self.generar_salida(pregunta, respuesta, esperado)

            buffer_salidas.append({
                'step':      step,
                'pregunta':  pregunta,
                'respuesta': respuesta,
                'salida':    resultado.nota_numeral,
                'esperado':  esperado,
                'tiempo':    tiempo,
                'razonamiento_previo': resultado.razonamiento_previo,
                'nivel_de_confianza': resultado.nivel_de_confianza,
                'fuera_de_contexto': resultado.fuera_de_contexto
            })

            # Flush cada 20 elementos
            if len(buffer_salidas) >= 20:
                self.dataset_cliente.guardar_buffer_csv(buffer_salidas, fieldnames)
                buffer_salidas.clear()

            print(f"Progreso: {step + 1} ejemplos procesados")
            step += 1

        # Flush final con lo que quede en el buffer
        if buffer_salidas:
            self.dataset_cliente.guardar_buffer_csv(buffer_salidas, fieldnames)
