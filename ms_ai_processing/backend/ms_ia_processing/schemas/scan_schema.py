from pydantic import BaseModel
from typing import Optional

class ProductoGemini(BaseModel):
    producto_id: Optional[str] = None
    nombre_detectado: Optional[str] = None
    nombre_catalogo: Optional[str] = None
    cantidad: Optional[int] = None
    confianza: str
    advertencia: Optional[str] = None

class RespuestaGemini(BaseModel):
    productos: list[ProductoGemini]
    error_general: Optional[str] = None