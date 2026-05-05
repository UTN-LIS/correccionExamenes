import re
from .base import Metrica

class ErrorNota(Metrica):
    def calcular(self):
        if not self.esperado:
            return {}
        print(self.salida)
        notaSalida = float(self.salida["Nota"]["content"].strip())
        notaEsperada = float(self.esperado)
        return {
            "error_nota": abs(notaSalida - notaEsperada)
        }