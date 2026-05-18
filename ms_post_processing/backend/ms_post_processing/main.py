from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from routers.process_router import router
from core.logger import get_logger
from core.exceptions import SesionNoEncontradaError, ProductosInsuficientesError
from database.client_supabase import get_supabase

logger = get_logger(__name__)

app = FastAPI(
    title="ms_post_processing",
    description="Microservicio de post-procesamiento de facturas",
    version="1.0.0"
)


@app.exception_handler(SesionNoEncontradaError)
async def sesion_handler(_request: Request, exc: SesionNoEncontradaError):
    logger.warning(f"[GLOBAL] SesionNoEncontradaError: {exc}")
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ProductosInsuficientesError)
async def productos_handler(_request: Request, exc: ProductosInsuficientesError):
    logger.warning(f"[GLOBAL] ProductosInsuficientesError: {exc}")
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def generic_handler(_request: Request, exc: Exception):
    logger.error(f"[GLOBAL] Error no controlado: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Error interno"})


app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    logger.info("Iniciando ms_post_processing")
    try:
        get_supabase()
        logger.info("Conexión con Supabase verificada")
    except Exception as e:
        logger.error(f"No se pudo conectar con Supabase al iniciar: {e}")
    logger.info("ms_post_processing corriendo en puerto 8000")
    logger.info("Documentación disponible en http://localhost:8000/docs")


@app.on_event("shutdown")
async def shutdown():
    logger.info("ms_post_processing detenido")


@app.get("/health", tags=["health"])
async def health():
    try:
        get_supabase()
        supabase_status = "ok"
    except Exception:
        supabase_status = "error"

    return {
        "status": "ok",
        "servicio": "ms_post_processing",
        "version": "1.0.0",
        "database": supabase_status
    }
