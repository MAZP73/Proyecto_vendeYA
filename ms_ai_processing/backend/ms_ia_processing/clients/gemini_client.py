import google.generativeai as genai
import json
from core.config import settings
from core.logger import get_logger
from core.exceptions import GeminiResponseError
from utils.build_prompt import SYSTEM_INSTRUCTIONS, RESPONSE_SCHEMA, build_user_prompt

logger = get_logger(__name__)


def inicializar_gemini() -> None:
    genai.configure(api_key=settings.gemini_api_key)
    logger.info("Gemini configurado correctamente")


def get_model() -> genai.GenerativeModel:
    generation_config = genai.GenerationConfig(
        temperature=0,
        response_mime_type="application/json",
        response_schema=RESPONSE_SCHEMA
    )

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config=generation_config,
        system_instruction=SYSTEM_INSTRUCTIONS
    )

    logger.debug("Modelo Gemini inicializado")
    return model


async def procesar_imagen_con_gemini(
    imagen_bytes: bytes,
    content_type: str,
    inventario: list[dict]
) -> dict:

    logger.info("Iniciando llamada a Gemini")

    try:
        model = get_model()

        # Construir contenido: imagen + prompt con inventario embebido
        contenido = [
            {
                "mime_type": content_type,
                "data": imagen_bytes
            },
            build_user_prompt(inventario)
        ]

        logger.debug(f"Enviando imagen de {len(imagen_bytes) / 1024:.1f}KB a Gemini")
        logger.debug(f"Inventario enviado: {len(inventario)} productos")

        respuesta = model.generate_content(contenido)

        logger.debug(f"Respuesta cruda de Gemini: {respuesta.text}")

        # Parsear JSON
        resultado = json.loads(respuesta.text)

        # Normalizar "null" a None en error_general
        if resultado.get("error_general") == "null":
            resultado["error_general"] = None

        # Validar campos obligatorios
        if "productos" not in resultado or "error_general" not in resultado:
            raise GeminiResponseError("La respuesta de Gemini no tiene la estructura esperada")

        total     = len(resultado["productos"])
        altas     = sum(1 for p in resultado["productos"] if p.get("confianza") == "alta")
        medias    = sum(1 for p in resultado["productos"] if p.get("confianza") == "media")
        bajas     = sum(1 for p in resultado["productos"] if p.get("confianza") == "baja")

        logger.info(f"Gemini detectó {total} productos | alta: {altas} | media: {medias} | baja: {bajas}")

        return resultado

    except json.JSONDecodeError as e:
        logger.error(f"Gemini no retornó JSON válido: {e}")
        raise GeminiResponseError("Gemini retornó una respuesta con formato inválido")

    except GeminiResponseError:
        raise

    except Exception as e:
        logger.error(f"Error inesperado llamando a Gemini: {e}", exc_info=True)
        raise GeminiResponseError(f"Error al procesar la imagen con Gemini: {str(e)}")