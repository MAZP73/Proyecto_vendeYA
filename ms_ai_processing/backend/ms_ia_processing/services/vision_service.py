from clients.gemini_client import procesar_imagen_con_gemini
from schemas.scan_schema import RespuestaGemini, ProductoGemini
from core.exceptions import (
    ImagenInvalidaError,
    GeminiResponseError,
    ProductosNoDetectadosError
)
from core.logger import get_logger
from database.client_supabase import obtener_inventario
from PIL import Image
import io

logger = get_logger(__name__)


async def procesar_imagen(
    imagen_bytes: bytes,
    content_type: str
) -> RespuestaGemini:

    logger.info("Iniciando procesamiento de imagen")

    # Validar que la imagen es procesable
    _validar_imagen(imagen_bytes)

    # Traer inventario de Supabase
    logger.info("Obteniendo inventario de Supabase")
    inventario = await obtener_inventario()

    if not inventario:
        logger.error("El inventario está vacío")
        raise GeminiResponseError("No hay productos en el inventario para comparar")

    logger.info(f"Inventario obtenido: {len(inventario)} productos")

    # Llamar a Gemini
    resultado_gemini = await procesar_imagen_con_gemini(
        imagen_bytes=imagen_bytes,
        content_type=content_type,
        inventario=inventario
    )

    # Validar resultado
    respuesta = _validar_respuesta_gemini(resultado_gemini)

    return respuesta


def _validar_imagen(imagen_bytes: bytes) -> None:
    logger.debug("Validando imagen")

    # Validar que los bytes corresponden a una imagen real
    try:
        imagen = Image.open(io.BytesIO(imagen_bytes))
        imagen.verify()
    except Exception:
        logger.error("Los bytes recibidos no corresponden a una imagen válida")
        raise ImagenInvalidaError("El archivo recibido no es una imagen válida")

    # Validar dimensiones mínimas
    imagen = Image.open(io.BytesIO(imagen_bytes))
    ancho, alto = imagen.size

    if ancho < 100 or alto < 100:
        logger.error(f"Imagen demasiado pequeña: {ancho}x{alto}px")
        raise ImagenInvalidaError(
            f"La imagen es demasiado pequeña ({ancho}x{alto}px). "
            "Se requiere mínimo 100x100px."
        )

    logger.debug(f"Imagen válida: {ancho}x{alto}px")


def _validar_respuesta_gemini(resultado: dict) -> RespuestaGemini:
    logger.debug("Validando estructura de respuesta de Gemini")

    # Si Gemini reportó error general
    if resultado.get("error_general"):
        logger.warning(f"Gemini reportó error general: {resultado['error_general']}")
        return RespuestaGemini(
            productos=[],
            error_general=resultado["error_general"]
        )

    productos_raw = resultado.get("productos", [])

    # Si no detectó ningún producto
    if not productos_raw:
        logger.warning("Gemini no detectó ningún producto en la imagen")
        raise ProductosNoDetectadosError(
            "No se detectaron productos en la imagen. "
            "Intente con mejor iluminación o acercándose más a los productos."
        )

    # Mapear cada producto al schema
    productos = []
    for p in productos_raw:
        try:
            producto = ProductoGemini(
                producto_id=p.get("producto_id"),
                nombre_detectado=p.get("nombre_detectado"),
                nombre_catalogo=p.get("nombre_catalogo"),
                cantidad=p.get("cantidad"),
                confianza=p.get("confianza"),
                advertencia=p.get("advertencia")
            )
            productos.append(producto)
        except Exception as e:
            logger.warning(f"Producto con estructura inválida ignorado: {e}")
            continue

    # Si todos los productos fallaron la validación
    if not productos:
        logger.error("Ningún producto pasó la validación de estructura")
        raise GeminiResponseError(
            "La respuesta de Gemini no contiene productos con estructura válida"
        )

    # Log resumen
    altas  = sum(1 for p in productos if p.confianza == "alta")
    medias = sum(1 for p in productos if p.confianza == "media")
    bajas  = sum(1 for p in productos if p.confianza == "baja")
    logger.info(
        f"Validación exitosa | total: {len(productos)} | "
        f"alta: {altas} | media: {medias} | baja: {bajas}"
    )

    return RespuestaGemini(
        productos=productos,
        error_general=None
    )