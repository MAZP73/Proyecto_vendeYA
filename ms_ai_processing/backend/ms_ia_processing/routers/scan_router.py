from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from schemas.scan_schema import RespuestaGemini
from services.vision_service import procesar_imagen
from core.exceptions import (
    ImagenInvalidaError,
    GeminiResponseError,
    ProductosNoDetectadosError
)
from core.logger import get_logger
import httpx
from core.config import settings

router = APIRouter(prefix="/scan", tags=["scan"])
logger = get_logger(__name__)
security = HTTPBearer()

FORMATOS_PERMITIDOS = {"image/jpeg", "image/png", "image/webp"}


@router.post("/", response_model=RespuestaGemini)
async def scan(
    file: UploadFile = File(...),
    sesion_id: str = Form(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    jwt_token = credentials.credentials
    logger.info(f"Solicitud recibida | sesion_id: {sesion_id} | archivo: {file.filename} | tipo: {file.content_type}")

    # Validar formato de imagen
    if file.content_type not in FORMATOS_PERMITIDOS:
        logger.warning(f"Formato no permitido: {file.content_type}")
        raise HTTPException(
            status_code=415,
            detail=f"Formato no soportado: {file.content_type}. Use JPEG, PNG o WebP."
        )

    # Leer y validar tamaño
    contenido = await file.read()
    tamanio_mb = len(contenido) / (1024 * 1024)
    logger.debug(f"Tamaño de imagen recibida: {tamanio_mb:.2f}MB")

    if len(contenido) > 10 * 1024 * 1024:
        logger.warning(f"Imagen supera tamaño máximo: {tamanio_mb:.2f}MB")
        raise HTTPException(
            status_code=413,
            detail="La imagen supera el tamaño máximo permitido de 10MB."
        )

    try:
        # Procesar imagen con Gemini
        logger.info("Enviando imagen a vision_service")
        respuesta_gemini: RespuestaGemini = await procesar_imagen(
            imagen_bytes=contenido,
            content_type=file.content_type
        )

        # Si Gemini reportó error general retornarlo limpiamente
        if respuesta_gemini.error_general:
            logger.warning(f"Gemini reportó error general: {respuesta_gemini.error_general}")
            raise HTTPException(
                status_code=422,
                detail=respuesta_gemini.error_general
            )

        # Log resumen de productos detectados
        total  = len(respuesta_gemini.productos)
        altas  = sum(1 for p in respuesta_gemini.productos if p.confianza == "alta")
        medias = sum(1 for p in respuesta_gemini.productos if p.confianza == "media")
        bajas  = sum(1 for p in respuesta_gemini.productos if p.confianza == "baja")
        logger.info(
            f"Procesamiento exitoso | total: {total} | "
            f"alta: {altas} | media: {medias} | baja: {bajas}"
        )


        # Reenviar a ms_post_processing con sesion_id y JWT
        logger.info(f"Reenviando resultado a ms_post_processing | sesion_id: {sesion_id}")

        async with httpx.AsyncClient() as client:
            respuesta_post = await client.post(
                "http://ms_post_processing:8000/api/v1/procesar",
                json={
                    **respuesta_gemini.model_dump(),
                    "sesion_id": sesion_id
                },
                headers={"Authorization": f"Bearer {jwt_token}"},
                timeout=30.0
            )
            respuesta_post.raise_for_status()

        logger.info(f"Respuesta de ms_post_processing recibida | sesion_id: {sesion_id}")
        return respuesta_post.json()

    except ImagenInvalidaError as e:
        logger.error(f"Imagen inválida | sesion_id: {sesion_id} | detalle: {e.mensaje}")
        raise HTTPException(status_code=400, detail=e.mensaje)

    except GeminiResponseError as e:
        logger.error(f"Error en respuesta de Gemini | sesion_id: {sesion_id} | detalle: {e.mensaje}")
        raise HTTPException(status_code=502, detail=e.mensaje)

    except ProductosNoDetectadosError as e:
        logger.warning(f"Sin productos detectados | sesion_id: {sesion_id} | detalle: {e.mensaje}")
        raise HTTPException(status_code=422, detail=e.mensaje)

    except httpx.HTTPStatusError as e:
        logger.error(
            f"Error HTTP en ms_post_processing | sesion_id: {sesion_id} | "
            f"status: {e.response.status_code}"
        )
        raise HTTPException(
            status_code=502,
            detail=f"Error comunicándose con ms_post_processing: {e.response.status_code}"
        )

    except httpx.TimeoutException:
        logger.error(f"Timeout esperando ms_post_processing | sesion_id: {sesion_id}")
        raise HTTPException(
            status_code=504,
            detail="ms_post_processing no respondió a tiempo."
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error inesperado | sesion_id: {sesion_id} | detalle: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor."
        )