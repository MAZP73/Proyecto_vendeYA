from schemas.process_request import ProcessRequest
from schemas.process_response import FacturaSalida, ProcessResponse, ProductoSalida
from repositories.catalog_repository import CatalogRepository
from repositories.resultado_repository import ResultadoRepository
from services.pricing_service import PricingService
from services.iva_service import IvaService
from core.exceptions import ProductoNoEncontradoError, ProductosInsuficientesError
from core.logger import get_logger

logger = get_logger(__name__)


class NegocioService:

    async def procesar(self, request: ProcessRequest) -> ProcessResponse:
        logger.info(f"[NEGOCIO] Iniciando | sesion_id={request.sesion_id}")

        repo = CatalogRepository()
        await repo.validar_sesion(request.sesion_id)

        validos, descartados = [], 0
        for p in request.productos:
            if not p.producto_id or p.confianza == "baja" or not p.cantidad or p.cantidad <= 0:
                descartados += 1
                logger.warning(
                    f"[NEGOCIO] Producto descartado | producto_id={p.producto_id} "
                    f"| confianza={p.confianza} | cantidad={p.cantidad}"
                )
            else:
                validos.append(p)

        logger.info(
            f"[NEGOCIO] Filtrado | válidos={len(validos)} | descartados={descartados}"
        )

        if not validos:
            logger.error(f"[NEGOCIO] Sin productos válidos | sesion_id={request.sesion_id}")
            raise ProductosInsuficientesError(
                f"Sesión {request.sesion_id}: ningún producto válido para procesar"
            )

        pricing = PricingService()
        iva_svc = IvaService()
        productos_salida = []

        for p in validos:
            try:
                catalogo = await repo.get_producto(p.producto_id)
            except ProductoNoEncontradoError as e:
                logger.warning(f"[NEGOCIO] {e} — descartado del resultado")
                continue

            subtotal = pricing.calcular(catalogo["precio_unitario"], p.cantidad)
            monto_iva = iva_svc.calcular(subtotal, catalogo["iva"])

            logger.debug(
                f"[NEGOCIO] Cálculo OK | producto_id={p.producto_id} "
                f"| subtotal={subtotal} | iva={monto_iva}"
            )

            productos_salida.append(ProductoSalida(
                producto_id=p.producto_id,
                sku=catalogo["sku"],
                nombre_detectado=p.nombre_detectado,
                nombre_catalogo=catalogo.get("nombre") or p.nombre_catalogo,
                cantidad=p.cantidad,
                precio_unitario=catalogo["precio_unitario"],
                iva=monto_iva,
                subtotal=subtotal,
                confianza=p.confianza,
                advertencia=p.advertencia,
            ))

        if not productos_salida:
            logger.error(
                f"[NEGOCIO] Todos descartados por catálogo | sesion_id={request.sesion_id}"
            )
            raise ProductosInsuficientesError(
                f"Sesión {request.sesion_id}: ningún producto encontrado en catálogo"
            )

        subtotal_total = round(sum(p.subtotal for p in productos_salida), 2)
        iva_total = round(sum(p.iva for p in productos_salida), 2)
        total = round(subtotal_total + iva_total, 2)

        resultado_repo = ResultadoRepository()
        numero_factura = await resultado_repo.obtener_ultimo_numero_factura()

        logger.info(
            f"[NEGOCIO] Factura | numero={numero_factura} "
            f"| subtotal={subtotal_total} | iva={iva_total} | total={total}"
        )

        response = ProcessResponse(
            sesion_id=request.sesion_id,
            estado="completada",
            productos=productos_salida,
            factura=FacturaSalida(
                numero_factura=numero_factura,
                subtotal=subtotal_total,
                iva_total=iva_total,
                total=total,
                estado="pendiente",
            ),
        )

        await resultado_repo.guardar_resultado(response)

        return response
