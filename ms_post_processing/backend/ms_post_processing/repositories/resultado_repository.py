from datetime import datetime
from zoneinfo import ZoneInfo

from database.client_supabase import get_supabase
from schemas.process_response import ProcessResponse
from core.exceptions import GuardadoSupabaseError
from core.logger import get_logger

logger = get_logger(__name__)


class ResultadoRepository:

    async def obtener_ultimo_numero_factura(self) -> str:
        """Consulta el ultimo numero_factura en la tabla facturas y retorna el siguiente."""
        logger.debug("[RESULTADO_REPO] Consultando ultimo numero_factura")

        try:
            resp = (
                get_supabase().table("facturas")
                .select("numero_factura")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
        except Exception as e:
            logger.error(f"[RESULTADO_REPO] Error consultando ultimo numero_factura: {e}")
            raise GuardadoSupabaseError(f"Error al consultar ultimo numero_factura: {e}")

        year_actual = datetime.now(ZoneInfo("America/Bogota")).year

        if resp.data and len(resp.data) > 0:
            ultimo = resp.data[0]["numero_factura"]
            try:
                partes = ultimo.split("-")
                year_ultimo = int(partes[1])
                contador = int(partes[2])
            except (IndexError, ValueError):
                logger.warning(f"[RESULTADO_REPO] Formato inesperado en numero_factura: {ultimo}. Reiniciando secuencia.")
                return f"FAC-{year_actual}-0001"

            if year_ultimo != year_actual:
                logger.info(f"[RESULTADO_REPO] Cambio de año ({year_ultimo} -> {year_actual}). Reiniciando secuencia.")
                return f"FAC-{year_actual}-0001"

            siguiente = contador + 1
            numero = f"FAC-{year_actual}-{siguiente:04d}"
            logger.info(f"[RESULTADO_REPO] Siguiente numero_factura: {numero}")
            return numero

        logger.info("[RESULTADO_REPO] No hay facturas previas. Iniciando secuencia en 0001.")
        return f"FAC-{year_actual}-0001"

    async def guardar_resultado(self, result: ProcessResponse) -> None:
        sesion_id = result.sesion_id

        for p in result.productos:
            try:
                get_supabase().table("sesion_productos").insert({
                    "sesion_id": sesion_id,
                    "producto_id": p.producto_id,
                    "nombre_detectado": p.nombre_detectado,
                    "nombre_catalogo": p.nombre_catalogo,
                    "confianza": p.confianza,
                    "advertencia": p.advertencia,
                    "cantidad": p.cantidad,
                    "precio_unitario": p.precio_unitario,
                    "iva": p.iva,
                    "subtotal": p.subtotal,
                }).execute()
            except Exception as e:
                logger.error(f"[RESULTADO_REPO] Error en sesion_productos | sesion_id={sesion_id}: {e}")
                raise GuardadoSupabaseError(f"Error guardando sesion_productos: {e}")

        try:
            resp = get_supabase().table("facturas").insert({
                "sesion_id": sesion_id,
                "numero_factura": result.factura.numero_factura,
                "subtotal": result.factura.subtotal,
                "iva_total": result.factura.iva_total,
                "total": result.factura.total,
                "estado": result.factura.estado,
                "created_at": datetime.now(
                    ZoneInfo("America/Bogota")
                ).isoformat(),
            }).execute()
        except Exception as e:
            logger.error(f"[RESULTADO_REPO] Error en facturas | sesion_id={sesion_id}: {e}")
            raise GuardadoSupabaseError(f"Error guardando factura: {e}")

        factura_id = resp.data[0]["id"]

        for p in result.productos:
            try:
                get_supabase().table("factura_detalle").insert({
                    "factura_id": factura_id,
                    "producto_id": p.producto_id,
                    "cantidad": p.cantidad,
                    "precio_unitario": p.precio_unitario,
                    "iva": p.iva,
                    "subtotal": p.subtotal,
                }).execute()
            except Exception as e:
                logger.error(f"[RESULTADO_REPO] Error en factura_detalle | factura_id={factura_id}: {e}")
                raise GuardadoSupabaseError(f"Error guardando factura_detalle: {e}")

        logger.info(
            f"[RESULTADO_REPO] Guardado OK | sesion_id={sesion_id} | factura_id={factura_id}"
        )
