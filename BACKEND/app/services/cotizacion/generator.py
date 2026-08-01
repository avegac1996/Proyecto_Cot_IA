from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.producto import Producto
from app.models.sesion import Sesion
from app.models.cotizacion import Cotizacion, CotizacionItem
from app.services.scraping.engine import buscar_precios


def _nombre_producto(comp: dict) -> str:
    partes = [comp.get("tipo", "desconocido").capitalize()]
    if comp.get("valor"):
        partes.append(f"{comp['valor']}{comp.get('unidad') or ''}")
    if comp.get("color"):
        partes.append(comp["color"].capitalize())
    if comp.get("tamano"):
        partes.append(comp["tamano"])
    if comp.get("tipo_o_modelo"):
        partes.append(comp["tipo_o_modelo"].upper())
    return " ".join(partes)


async def _buscar_producto(db: AsyncSession, comp: dict) -> Producto | None:
    """Busca el producto del catálogo que mejor corresponde al componente."""
    tipo = comp.get("tipo")
    if not tipo or tipo == "desconocido":
        return None

    query = select(Producto).where(
        Producto.activo.is_(True),
        func.lower(Producto.categoria) == tipo.lower(),
    )
    result = await db.execute(query)
    candidatos = result.scalars().all()

    if not candidatos:
        return None

    valor = comp.get("valor")
    if valor:
        con_valor = [
            p for p in candidatos
            if str(p.especificaciones.get("valor", "")).lower() == str(valor).lower()
        ]
        if con_valor:
            candidatos = con_valor

    color = comp.get("color")
    if color:
        con_color = [
            p for p in candidatos
            if str(p.especificaciones.get("color", "")).lower() == color.lower()
        ]
        if con_color:
            candidatos = con_color

    return candidatos[0]


async def generar_cotizacion(
    db: AsyncSession, sesion: Sesion, usuario_id: int
) -> Cotizacion:
    """Genera y persiste la cotización de una sesión.

    Por cada componente: busca el producto en catálogo, obtiene precios por
    tienda (cache de scraping), aplica el margen de competencia y selecciona
    el proveedor más barato disponible.
    """
    margen = Decimal(str(settings.MARGEN_COMPETENCIA)) / Decimal(100)

    cotizacion = Cotizacion(
        session_id=sesion.id,
        usuario_id=usuario_id,
        estado="completada",
        total=Decimal(0),
    )
    db.add(cotizacion)
    await db.flush()

    total = Decimal(0)
    for comp in sesion.componentes_json:
        producto = await _buscar_producto(db, comp)
        nombre = producto.nombre if producto else _nombre_producto(comp)
        cantidad = int(comp.get("cantidad", 1))

        proveedores = []
        if producto is not None:
            proveedores = await buscar_precios(db, producto.id)

        # Precio final por proveedor con margen aplicado
        disponibles = []
        for prov in proveedores:
            precio = prov["precio_unitario"]
            if prov["disponible"] and precio is not None:
                precio_final = Decimal(str(precio)) * (1 + margen)
                disponibles.append((prov, precio_final.quantize(Decimal("0.01"))))

        if disponibles:
            mejor, precio_unit = min(disponibles, key=lambda dp: dp[1])
            subtotal = (precio_unit * cantidad).quantize(Decimal("0.01"))
            item = CotizacionItem(
                cotizacion_id=cotizacion.id,
                producto_id=producto.id if producto else None,
                producto_nombre=nombre,
                cantidad=cantidad,
                precio_unitario=precio_unit,
                proveedor=mejor["tienda"],
                margen_aplicado=settings.MARGEN_COMPETENCIA,
                subtotal=subtotal,
                disponible=True,
            )
            total += subtotal
        else:
            item = CotizacionItem(
                cotizacion_id=cotizacion.id,
                producto_id=producto.id if producto else None,
                producto_nombre=nombre,
                cantidad=cantidad,
                precio_unitario=Decimal(0),
                proveedor="",
                margen_aplicado=Decimal(0),
                subtotal=Decimal(0),
                disponible=False,
            )

        cotizacion.items.append(item)

    cotizacion.total = total
    sesion.estado = "completada"
    sesion.ambiguedades_resueltas = True
    await db.commit()
    await db.refresh(cotizacion)
    return cotizacion
