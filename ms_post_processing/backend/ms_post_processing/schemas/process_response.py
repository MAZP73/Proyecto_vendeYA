from pydantic import BaseModel
from typing import List, Optional


class ProductoSalida(BaseModel):
    producto_id: str
    sku: str
    nombre_detectado: Optional[str]
    nombre_catalogo: Optional[str]
    cantidad: int
    precio_unitario: float
    iva: float
    subtotal: float
    confianza: str
    advertencia: Optional[str]


class FacturaSalida(BaseModel):
    numero_factura: str
    subtotal: float
    iva_total: float
    total: float
    estado: str = "pagada"


class ProcessResponse(BaseModel):
    sesion_id: str
    estado: str = "completada"
    productos: List[ProductoSalida]
    factura: FacturaSalida
