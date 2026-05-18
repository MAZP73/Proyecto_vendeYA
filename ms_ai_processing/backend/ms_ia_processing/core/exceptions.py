class ImagenInvalidaError(Exception):
    def __init__(self, mensaje: str = "La imagen recibida no es válida"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class GeminiResponseError(Exception):
    def __init__(self, mensaje: str = "Gemini retornó una respuesta inesperada"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class ProductosNoDetectadosError(Exception):
    def __init__(self, mensaje: str = "No se detectaron productos en la imagen"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class SinProductosError(Exception):
    def __init__(self, mensaje: str, detalle: str):
        self.mensaje = mensaje
        self.detalle = detalle
        super().__init__(self.mensaje)


class CalidadInsuficienteError(Exception):
    def __init__(self, mensaje: str, resumen: dict):
        self.mensaje = mensaje
        self.resumen = resumen
        super().__init__(self.mensaje)