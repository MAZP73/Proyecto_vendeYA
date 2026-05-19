from database.client_supabase import get_supabase
from core.exceptions import ProductoNoEncontradoError, SesionNoEncontradaError
from core.logger import get_logger

logger = get_logger(__name__)


class CatalogRepository:

    async def validar_sesion(self, sesion_id: str) -> dict:
        logger.debug(f"[REPO] Validando sesion_id={sesion_id}")
        try:
            resp = (
                get_supabase().table("sesiones")
                .select("id, estado")
                .eq("id", sesion_id)
                .single()
                .execute()
            )
        except Exception as e:
            logger.error(f"[REPO] Error DB al validar sesión {sesion_id}: {e}")
            raise SesionNoEncontradaError(f"Error de DB al validar sesión {sesion_id}: {e}")

        if not resp.data:
            logger.error(f"[REPO] Sesión no encontrada | sesion_id={sesion_id}")
            raise SesionNoEncontradaError(f"Sesión {sesion_id} no existe")

        if resp.data["estado"] != "activa":
            logger.error(
                f"[REPO] Estado incorrecto | sesion_id={sesion_id} "
                f"| estado_actual={resp.data['estado']}"
            )
            raise SesionNoEncontradaError(
                f"Sesión {sesion_id} no está activa (estado: {resp.data['estado']})"
            )

        logger.info(f"[REPO] Sesión válida | sesion_id={sesion_id}")
        return resp.data

    async def get_producto(self, producto_id: str) -> dict:
        logger.debug(f"[REPO] Consultando producto_id={producto_id}")
        try:
            resp = (
                get_supabase().table("productos_catalogo")
                .select("id, nombre, sku, precio_unitario, iva, activo")
                .eq("id", producto_id)
                .single()
                .execute()
            )
        except Exception as e:
            logger.error(f"[REPO] Error DB para producto_id={producto_id}: {e}")
            raise ProductoNoEncontradoError(f"Error de DB al buscar {producto_id}: {e}")

        if not resp.data:
            logger.warning(f"[REPO] Producto no encontrado | producto_id={producto_id}")
            raise ProductoNoEncontradoError(f"Producto {producto_id} no existe en catálogo")

        if not resp.data.get("activo", False):
            logger.warning(f"[REPO] Producto inactivo | producto_id={producto_id}")
            raise ProductoNoEncontradoError(f"Producto {producto_id} está inactivo")

        logger.debug(
            f"[REPO] Producto OK | producto_id={producto_id} "
            f"| sku={resp.data['sku']} | precio={resp.data['precio_unitario']}"
        )
        return resp.data

    async def get_stock(self, producto_id: str) -> int:
        logger.debug(f"[REPO] Consultando stock | producto_id={producto_id}")
        try:
            resp = (
                get_supabase().table("inventario")
                .select("stock_actual")
                .eq("producto_id", producto_id)
                .single()
                .execute()
            )
        except Exception as e:
            logger.warning(f"[REPO] No se pudo consultar stock {producto_id}: {e}. Asume 0")
            return 0
        stock = resp.data["stock_actual"] if resp.data else 0
        logger.debug(f"[REPO] Stock={stock} | producto_id={producto_id}")
        return stock
