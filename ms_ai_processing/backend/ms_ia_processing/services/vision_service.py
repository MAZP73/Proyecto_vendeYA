from clients.gemini_client import procesar_imagen_con_gemini
from schemas.scan_schema import RespuestaGemini, ProductoGemini
from core.exceptions import (
    ImagenInvalidaError,
    GeminiResponseError,
    ProductosNoDetectadosError,
    SinProductosError,
    CalidadInsuficienteError
)
from core.logger import get_logger
from database.client_supabase import obtener_inventario
from PIL import Image
import io

logger = get_logger(__name__)

UMBRAL_BAJA = 80        # % de productos con confianza baja para cortar el flujo
UMBRAL_MINIMO_ALTAS = 1 # mínimo de productos con confianza alta para continuar


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

    # Validar resultado y aplicar reglas de calidad
    respuesta = _validar_respuesta_gemini(resultado_gemini)

    return respuesta


def _validar_imagen(imagen_bytes: bytes) -> None:
    logger.debug("Validando imagen")

    try:
        imagen = Image.open(io.BytesIO(imagen_bytes))
        imagen.verify()
    except Exception:
        logger.error("Los bytes recibidos no corresponden a una imagen válida")
        raise ImagenInvalidaError("El archivo recibido no es una imagen válida")

    imagen = Image.open(io.BytesIO(imagen_bytes))
    ancho, alto = imagen.size

    if ancho < 100 or alto < 100:
        logger.error(f"Imagen demasiado pequeña: {ancho}x{alto}px")
        raise ImagenInvalidaError(
            f"La imagen es demasiado pequeña ({ancho}x{alto}px). "
            "Se requiere mínimo 100x100px."
        )

    logger.debug(f"Imagen válida: {ancho}x{alto}px")


def _calcular_resumen(productos: list[ProductoGemini]) -> dict:
    total  = len(productos)
    altas  = sum(1 for p in productos if p.confianza == "alta")
    medias = sum(1 for p in productos if p.confianza == "media")
    bajas  = sum(1 for p in productos if p.confianza == "baja")

    pct_alta  = round(altas  / total * 100, 1) if total > 0 else 0
    pct_media = round(medias / total * 100, 1) if total > 0 else 0
    pct_baja  = round(bajas  / total * 100, 1) if total > 0 else 0

    return {
        "total"    : total,
        "alta"     : altas,
        "media"    : medias,
        "baja"     : bajas,
        "pct_alta" : pct_alta,
        "pct_media": pct_media,
        "pct_baja" : pct_baja
    }


def _validar_calidad_deteccion(productos: list[ProductoGemini]) -> None:
    resumen = _calcular_resumen(productos)

    logger.debug(
        f"Calidad de detección | "
        f"alta: {resumen['alta']} ({resumen['pct_alta']}%) | "
        f"media: {resumen['media']} ({resumen['pct_media']}%) | "
        f"baja: {resumen['baja']} ({resumen['pct_baja']}%)"
    )

    # Cortar si no hay ningún producto con confianza alta
    if resumen["alta"] < UMBRAL_MINIMO_ALTAS:
        logger.warning(
            f"Ningún producto con confianza alta detectado | "
            f"total: {resumen['total']} | baja: {resumen['baja']}"
        )
        raise CalidadInsuficienteError(
            mensaje=(
                "No se identificó ningún producto con certeza. "
                "Intente con mejor iluminación, acérquese más a los productos "
                "o evite que se tapen entre sí."
            ),
            resumen=resumen
        )

    # Cortar si el porcentaje de confianza baja supera el umbral
    if resumen["pct_baja"] >= UMBRAL_BAJA:
        logger.warning(
            f"Porcentaje de confianza baja supera umbral | "
            f"pct_baja: {resumen['pct_baja']}% | umbral: {UMBRAL_BAJA}%"
        )
        raise CalidadInsuficienteError(
            mensaje=(
                f"El {resumen['pct_baja']}% de los productos no pudieron identificarse "
                f"con certeza. Intente con mejor iluminación, acérquese más a los "
                f"productos o evite que se tapen entre sí."
            ),
            resumen=resumen
        )

    logger.info(
        f"Calidad de detección aceptable | "
        f"alta: {resumen['alta']} ({resumen['pct_alta']}%) | "
        f"baja: {resumen['baja']} ({resumen['pct_baja']}%)"
    )


def _validar_respuesta_gemini(resultado: dict) -> RespuestaGemini:
    logger.debug("Validando estructura de respuesta de Gemini")

    # Caso 1 — Gemini reportó error general (imagen sin productos, oscura, borrosa)
    if resultado.get("error_general"):
        logger.warning(f"Gemini reportó error general: {resultado['error_general']}")
        raise SinProductosError(
            mensaje="No se detectaron productos en la imagen.",
            detalle=resultado["error_general"]
        )

    productos_raw = resultado.get("productos", [])

    # Caso 2 — Array vacío sin error_general (caso inesperado)
    if not productos_raw:
        logger.warning("Gemini retornó array de productos vacío sin error_general")
        raise SinProductosError(
            mensaje="No se detectaron productos en la imagen.",
            detalle="El modelo no identificó ningún producto ni reportó el motivo. "
                    "Intente tomar la foto más cerca de los productos."
        )

    # Mapear cada producto al schema
    productos = []
    for p in productos_raw:
        try:
            producto = ProductoGemini(
                producto_id    =p.get("producto_id"),
                nombre_detectado=p.get("nombre_detectado"),
                nombre_catalogo =p.get("nombre_catalogo"),
                cantidad       =p.get("cantidad"),
                confianza      =p.get("confianza"),
                advertencia    =p.get("advertencia")
            )
            productos.append(producto)
        except Exception as e:
            logger.warning(f"Producto con estructura inválida ignorado: {e}")
            continue

    # Caso 3 — Todos los productos fallaron la validación de estructura
    if not productos:
        logger.error("Ningún producto pasó la validación de estructura")
        raise GeminiResponseError(
            "La respuesta de Gemini no contiene productos con estructura válida"
        )

    # Caso 4 — Validar calidad de detección
    _validar_calidad_deteccion(productos)

    # Todo bien
    resumen = _calcular_resumen(productos)
    logger.info(
        f"Validación exitosa | total: {resumen['total']} | "
        f"alta: {resumen['alta']} | media: {resumen['media']} | baja: {resumen['baja']}"
    )

    return RespuestaGemini(
        productos=productos,
        error_general=None
    )