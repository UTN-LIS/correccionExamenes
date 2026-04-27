from .base import Metrica

class TamañoC(Metrica):
    def calcular(self):
        if not self.contexto:
            return {}

        return {
            "tamaño_contexto": len(str(self.contexto))
        }