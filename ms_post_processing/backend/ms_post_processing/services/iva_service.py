from core.logger import get_logger

logger = get_logger(__name__)


class IvaService:

    def calcular(self, subtotal: float, iva_porcentaje: float) -> float:
        monto = round(subtotal * (iva_porcentaje / 100), 2)
        logger.debug(f"[IVA] {subtotal} × {iva_porcentaje}% = {monto}")
        return monto
