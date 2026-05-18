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
            supabase = create_client(settings.supabase_url, settings.supabase_key)
            logger.info("Conexión con Supabase establecida correctamente")
        except Exception as e:
            logger.error(f"Error conectando con Supabase: {e}", exc_info=True)
            raise

    return supabase
