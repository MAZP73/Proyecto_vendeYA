from pydantic import BaseModel, field_validator
from typing import List, Optional


class ProductoEntrada(BaseModel):
    producto_id: Optional[str] = None
    nombre_detectado: Optional[str] = None
    nombre_catalogo: Optional[str] = None
    confianza: str
    advertencia: Optional[str] = None
    cantidad: Optional[int] = None

    @field_validator("advertencia", mode="before")
    @classmethod
    def normalizar_advertencia(cls, v):
        if v == "null" or v == "":
            return None
        return v


class ProcessRequest(BaseModel):
    sesion_id: str
    productos: List[ProductoEntrada]
    error_general: Optional[str] = None

    @field_validator("error_general", mode="before")
    @classmethod
    def normalizar_error_general(cls, v):
        if v == "null" or v == "":
            return None
        return v
