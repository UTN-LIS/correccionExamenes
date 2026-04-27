import re
from .base import Metrica

class ErrorNota(Metrica):
    def calcular(self):
        if not self.esperado:
            return {}

        notaSalida = float((re.search(r'\d+\.?\d*', self.salida)).group()) 
        notaEsperada = float(self.esperado)
        return {
            "error_nota": abs(notaSalida - notaEsperada)
        }