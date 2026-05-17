from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from routers.process_router import router
from logger import get_logger
from exceptions import SesionNoEncontradaError, ProductosInsuficientesError

logger = get_logger(__name__)
app = FastAPI(title="ms_post_processing")


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
logger.info("ms_post_processing iniciado y listo para recibir requests")
