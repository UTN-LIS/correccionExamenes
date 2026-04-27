from abc import ABC, abstractmethod

class Metrica(ABC):
    def __init__(self, entrada, contexto, salida, esperado=None, tiempo=None):
        self.entrada = entrada
        self.contexto = contexto
        self.salida = salida
        self.esperado = esperado
        self.tiempo = tiempo

    @abstractmethod
    def calcular(self):
        pass