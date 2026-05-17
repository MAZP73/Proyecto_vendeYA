from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.scan_router import router as scan_router
from core.logger import get_logger
from database.client_supabase import get_supabase
from clients.gemini_client import inicializar_gemini  # ← Importar


logger = get_logger(__name__)


app = FastAPI(
    title="ms_ai_processing",
    description="Microservicio de procesamiento de imágenes con Gemini Vision",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scan_router)


@app.on_event("startup")
async def startup():
    inicializar_gemini()
    logger.info("Iniciando ms_ai_processing")
    # Verificar conexión con Supabase al arrancar
    try:
        get_supabase()
        logger.info("Conexión con Supabase verificada")
    except Exception as e:
        logger.error(f"No se pudo conectar con Supabase al iniciar: {e}")
    logger.info("ms_ai_processing corriendo en puerto 8001")
    logger.info("Documentación disponible en http://localhost:8001/docs")


@app.on_event("shutdown")
async def shutdown():
    logger.info("ms_ai_processing detenido")


@app.get("/health", tags=["health"])
async def health():
    # Verificar conexión con Supabase en el health check
    try:
        get_supabase()
        supabase_status = "ok"
    except Exception:
        supabase_status = "error"

    return {
        "status": "ok",
        "servicio": "ms_ai_processing",
        "version": "1.0.0",
        "database": supabase_status
    }