import json
from pydantic import BaseModel, ValidationError
from typing import List, Optional
from prompts import SYSTEM_PROMPT, construir_user_message

class ResultadoEvaluacion(BaseModel):
    razonamiento_previo: str
    conceptos_clave_encontrados: List[str]
    conceptos_clave_omitidos: List[str]
    nota_numeral: int
    nivel_de_confianza: float
    fuera_de_contexto: bool


class Experimento:
    def __init__(self, cliente_llm, dataset_cliente, resultados_cliente, modelo="Modelo_XYZ"):
        self.dataset_cliente = dataset_cliente
        self.resultados_cliente = resultados_cliente
        self.cliente_llm = cliente_llm
        self.modelo = modelo

    def _parsear_salida(self, salida_cruda: str) -> Optional[ResultadoEvaluacion]:
        raw = salida_cruda.strip()
        if raw.startswith("```"):
            raw = raw.strip("`").removeprefix("json").strip()
        try:
            return ResultadoEvaluacion(**json.loads(raw))
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"Salida mal formada: {e}")
            return None

    def generar_salida(self, pregunta: str, conceptos: list, respuesta: str, esperado: str):
        user_message = construir_user_message(pregunta, respuesta, esperado)
        salida, tiempo = self.cliente_llm.generar_salida(SYSTEM_PROMPT, user_message)
        return salida, tiempo

    def ejecutar_dataset(self, max_items=None):
        buffer_salidas = []
        step = 0

        self.resultados_cliente.crear_archivo_resultados()
        self.resultados_cliente.guardar_configuracion(self.modelo, SYSTEM_PROMPT)

        for pregunta, conceptos, respuesta, esperado in self.dataset_cliente.dataset_batch():

            if max_items and step >= max_items:
                break

            salida_cruda, tiempo = self.generar_salida(pregunta, conceptos, respuesta, esperado)
            resultado = self._parsear_salida(salida_cruda)

            fila = {
                'step': step,
                'pregunta': pregunta,
                'respuesta': respuesta,
                'esperado': esperado,
                'tiempo': tiempo,
                'salida_cruda': salida_cruda,
            }

            if resultado:
                fila.update(resultado.model_dump())
            else:
                # deja los campos esperados en None para no romper el aplanado de excel
                fila.update({k: None for k in ResultadoEvaluacion.model_fields})

            buffer_salidas.append(fila)

            if len(buffer_salidas) >= 20:
                self.resultados_cliente.guardar_buffer(buffer_salidas)
                buffer_salidas.clear()

            print(f"Progreso: {step + 1} ejemplos procesados")
            step += 1

        if buffer_salidas:
            self.resultados_cliente.guardar_buffer(buffer_salidas)

        self.resultados_cliente.generar_excel()