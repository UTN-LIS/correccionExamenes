from abc import ABC, abstractmethod

class Metrica(ABC):
    def __init__(self, entrada, salida, esperado=None, tiempo=None):
        self.entrada = entrada
        self.salida = salida
        self.esperado = esperado
        self.tiempo = tiempo

    @abstractmethod
    def calcular(self):
        pass