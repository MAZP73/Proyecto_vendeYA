import os
from supabase import create_client, Client
from dotenv import load_dotenv
from logger import get_logger

load_dotenv()
logger = get_logger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("SUPABASE_URL o SUPABASE_KEY no están definidas en el entorno")
    raise EnvironmentError("Variables de entorno SUPABASE_URL y SUPABASE_KEY son requeridas")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
logger.info("Conexión a Supabase inicializada correctamente")
