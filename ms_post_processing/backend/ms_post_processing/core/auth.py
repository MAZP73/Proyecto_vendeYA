from fastapi import Header, HTTPException
from core.logger import get_logger

logger = get_logger(__name__)


async def verificar_token(authorization: str = Header(...)) -> str:
    logger.debug("[AUTH] Validando Authorization header")

    if not authorization.startswith("Bearer "):
        logger.warning("[AUTH] Header Authorization no tiene formato Bearer")
        raise HTTPException(
            status_code=401,
            detail="Authorization header debe tener formato: Bearer <token>"
        )

    token = authorization.split(" ", 1)[1].strip()

    if not token:
        logger.warning("[AUTH] Token vacío en Authorization header")
        raise HTTPException(status_code=401, detail="Token ausente en Authorization header")

    logger.info(f"[AUTH] Token presente | token={token[:8]}...")
    return token
