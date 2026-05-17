import os
import httpx
from exceptions import EnvioDestinoError
from logger import get_logger

logger = get_logger(__name__)


class DestinoClient:

    def __init__(self):
        self.url = os.environ.get("DESTINO_URL")
        if not self.url:
            logger.error("[DESTINO] DESTINO_URL no definida")
            raise EnvironmentError("Variable DESTINO_URL es requerida")

    async def enviar(self, payload, token: str) -> bool:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        logger.info(
            f"[DESTINO] Enviando | url={self.url} | sesion_id={payload.sesion_id}"
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.url,
                    json=payload.dict(),
                    headers=headers,
                    timeout=10.0,
                )

            if response.status_code == 200:
                logger.info(
                    f"[DESTINO] Envío exitoso | sesion_id={payload.sesion_id} "
                    f"| status={response.status_code}"
                )
                return True
            else:
                logger.warning(
                    f"[DESTINO] Status inesperado | sesion_id={payload.sesion_id} "
                    f"| status={response.status_code} | body={response.text[:200]}"
                )
                raise EnvioDestinoError(
                    f"Destino respondió {response.status_code} para sesión {payload.sesion_id}"
                )

        except httpx.TimeoutException:
            logger.warning(f"[DESTINO] Timeout | sesion_id={payload.sesion_id}")
            raise EnvioDestinoError(f"Timeout al enviar sesión {payload.sesion_id}")

        except httpx.RequestError as e:
            logger.error(f"[DESTINO] Error de conexión | sesion_id={payload.sesion_id} | {e}")
            raise EnvioDestinoError(f"Error de conexión: {e}")
