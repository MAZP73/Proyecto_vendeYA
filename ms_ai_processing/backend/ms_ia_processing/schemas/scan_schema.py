from pydantic import BaseModel
from typing import Optional

class ProductoGemini(BaseModel):
    producto_id: Optional[str]
    nombre_detectado: Optional[str]
    nombre_catalogo: Optional[str]
    cantidad: Optional[int]
    confianza: str
    advertencia: Optional[str]

class RespuestaGemini(BaseModel):
    productos: list[ProductoGemini]
    error_general: Optional[str]