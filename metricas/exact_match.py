from .base import Metrica

class ExactMatch(Metrica):
    def calcular(self):
        if not self.esperado:
            return {}

        return {
            "exact_match": 1.0 if str(self.salida).lower() == str(self.esperado).lower() else 0.0
        }