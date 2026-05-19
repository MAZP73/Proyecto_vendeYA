from core.logger import get_logger

logger = get_logger(__name__)


class PricingService:

    def calcular(self, precio_unitario: float, cantidad: int) -> float:
        subtotal = round(precio_unitario * cantidad, 2)
        logger.debug(f"[PRICING] {precio_unitario} × {cantidad} = {subtotal}")
        return subtotal
