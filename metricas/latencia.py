from .base import Metrica

class Latencia(Metrica):
    def calcular(self):
        if not self.tiempo:
            return {}

        return {
            "latencia_ms": self.tiempo * 1000
        }