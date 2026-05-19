from fastapi import APIRouter, Depends
from schemas.process_request import ProcessRequest
from schemas.process_response import ProcessResponse
from services.negocio_service import NegocioService
from core.auth import verificar_token
from core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/procesar", response_model=ProcessResponse)
async def process_session(
    request: ProcessRequest,
    token: str = Depends(verificar_token)
):
    logger.info(
        f"[ROUTER] Request recibido | sesion_id={request.sesion_id} "
        f"| productos_recibidos={len(request.productos)}"
    )

    service = NegocioService()
    result = await service.procesar(request)

    logger.info(
        f"[ROUTER] Guardado y completado | sesion_id={request.sesion_id} "
        f"| productos_validos={len(result.productos)} "
        f"| total_factura={result.factura.total}"
    )

    return result
