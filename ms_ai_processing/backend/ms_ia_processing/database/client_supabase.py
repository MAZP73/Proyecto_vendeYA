from supabase import create_client, Client
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)

supabase: Client = None


def get_supabase() -> Client:
    global supabase

    if supabase is None:
        logger.info("Iniciando conexión con Supabase")
        try:
            supabase = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
            logger.info("Conexión con Supabase establecida correctamente")
        except Exception as e:
            logger.error(f"Error conectando con Supabase: {e}", exc_info=True)
            raise

    return supabase


async def obtener_inventario() -> list[dict]:
    logger.debug("Consultando inventario en Supabase")

    try:
        cliente = get_supabase()

        respuesta = cliente.table("productos_catalogo") \
            .select("id, nombre, sku") \
            .eq("activo", True) \
            .execute()

        if not respuesta.data:
            logger.warning("La consulta de inventario retornó vacío")
            return []

        logger.info(f"Inventario obtenido: {len(respuesta.data)} productos activos")
        return respuesta.data

    except Exception as e:
        logger.error(f"Error consultando inventario: {e}", exc_info=True)
        raise