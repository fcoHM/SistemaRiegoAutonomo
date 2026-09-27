# esta clase representa un objeto de la configuracion 

class Configuracion():
     def __init__(self, nodo, object, value:int):
        self.nodo = nodo # a quien le pertenece ese configurable
        self.object = object # confihurable
        self.value = value # valor del configurable