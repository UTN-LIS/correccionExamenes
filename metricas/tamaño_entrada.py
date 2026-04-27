from .base import Metrica

class TamañoE(Metrica):
    def calcular(self):
        if not self.entrada:
            return {}

        return {
            "tamaño_entrada": len(str(self.entrada))
        }