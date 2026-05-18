from database import supabase
from schemas.process_response import ProcessResponse
from exceptions import GuardadoSupabaseError
from logger import get_logger

logger = get_logger(__name__)


class ResultadoRepository:

    async def guardar_resultado(self, result: ProcessResponse) -> None:
        sesion_id = result.sesion_id

        for p in result.productos:
            try:
                supabase.table("sesion_productos").insert({
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
            resp = supabase.table("facturas").insert({
                "sesion_id": sesion_id,
                "numero_factura": result.factura.numero_factura,
                "subtotal": result.factura.subtotal,
                "iva_total": result.factura.iva_total,
                "total": result.factura.total,
                "estado": result.factura.estado,
            }).execute()
        except Exception as e:
            logger.error(f"[RESULTADO_REPO] Error en facturas | sesion_id={sesion_id}: {e}")
            raise GuardadoSupabaseError(f"Error guardando factura: {e}")

        factura_id = resp.data[0]["id"]

        for p in result.productos:
            try:
                supabase.table("factura_detalle").insert({
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
