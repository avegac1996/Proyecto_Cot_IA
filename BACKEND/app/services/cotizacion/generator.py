from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.producto import Producto
from app.models.sesion import Sesion
from app.models.cotizacion import Cotizacion, CotizacionItem
from app.services.scraping.engine import buscar_precios

TIENDA_PROPIA = settings.TIENDA_PROPIA


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


def _construir_opcion(prov: dict, margen: Decimal, es_propio: bool) -> dict | None:
    """Construye una opción de proveedor con o sin margen."""
    precio = prov["precio_unitario"]
    if precio is None:
        return None

    if es_propio:
        precio_final = Decimal(str(precio)).quantize(Decimal("0.01"))
        margen_pct = Decimal(0)
    else:
        precio_final = (Decimal(str(precio)) * (1 + margen)).quantize(Decimal("0.01"))
        margen_pct = Decimal(str(settings.MARGEN_COMPETENCIA))

    return {
        "tienda": prov["tienda"],
        "precio_base": float(Decimal(str(precio)).quantize(Decimal("0.01"))),
        "precio_con_margen": float(precio_final),
        "margen_aplicado": float(margen_pct),
        "disponible": prov["disponible"],
        "url": prov.get("url"),
        "es_propio": es_propio,
    }


def _item_sin_datos(producto: Producto | None, nombre: str, cantidad: int) -> CotizacionItem:
    return CotizacionItem(
        producto_id=producto.id if producto else None,
        producto_nombre=nombre,
        cantidad=cantidad,
        precio_unitario=Decimal(0),
        proveedor="",
        margen_aplicado=Decimal(0),
        subtotal=Decimal(0),
        disponible=False,
        es_propio=False,
        seleccionado=True,
        opciones_proveedores=[],
    )


async def generar_cotizacion(
    db: AsyncSession, sesion: Sesion, usuario_id: int
) -> Cotizacion:
    """Genera y persiste la cotización de una sesión.

    Lógica de negocio:
    - AV Electronics (tienda propia): precio sin margen, auto-seleccionado.
    - Otras tiendas: precio + 5% margen.
    - Si AV Electronics tiene el producto → se usa directo (es_propio=True).
    - Si AV no lo tiene pero otras sí → se guardan todas las opciones,
      el usuario debe seleccionar la mejor (seleccionado=False).
    - Si nadie lo tiene → "Sin datos".
    """
    margen = Decimal(str(settings.MARGEN_COMPETENCIA)) / Decimal(100)

    cotizacion = Cotizacion(
        session_id=sesion.id,
        usuario_id=usuario_id,
        estado="borrador",
        total=Decimal(0),
    )

    total = Decimal(0)
    for comp in sesion.componentes_json:
        producto = await _buscar_producto(db, comp)
        nombre = producto.nombre if producto else _nombre_producto(comp)
        cantidad = int(comp.get("cantidad", 1))

        proveedores = []
        if producto is not None:
            proveedores = await buscar_precios(db, producto)

        # Separar tienda propia de otras
        prov_propio = None
        prov_otros = []
        for prov in proveedores:
            if prov["disponible"] and prov["precio_unitario"] is not None:
                if prov["tienda"] == TIENDA_PROPIA:
                    prov_propio = prov
                else:
                    prov_otros.append(prov)

        if prov_propio:
            # AV Electronics tiene el producto → sin margen, auto-seleccionado
            precio_unit = Decimal(str(prov_propio["precio_unitario"])).quantize(Decimal("0.01"))
            subtotal = (precio_unit * cantidad).quantize(Decimal("0.01"))
            item = CotizacionItem(
                producto_id=producto.id if producto else None,
                producto_nombre=nombre,
                cantidad=cantidad,
                precio_unitario=precio_unit,
                proveedor=TIENDA_PROPIA,
                margen_aplicado=Decimal(0),
                subtotal=subtotal,
                disponible=True,
                es_propio=True,
                seleccionado=True,
                opciones_proveedores=[],
            )
            total += subtotal
        elif prov_otros:
            # AV no lo tiene → mostrar todas las opciones con 5% margen
            opciones = []
            for prov in prov_otros:
                op = _construir_opcion(prov, margen, es_propio=False)
                if op:
                    opciones.append(op)

            if opciones:
                opciones.sort(key=lambda o: o["precio_con_margen"])
                mejor = opciones[0]
                precio_unit = Decimal(str(mejor["precio_con_margen"])).quantize(Decimal("0.01"))
                subtotal = (precio_unit * cantidad).quantize(Decimal("0.01"))
                item = CotizacionItem(
                    producto_id=producto.id if producto else None,
                    producto_nombre=nombre,
                    cantidad=cantidad,
                    precio_unitario=precio_unit,
                    proveedor=mejor["tienda"],
                    margen_aplicado=Decimal(str(settings.MARGEN_COMPETENCIA)),
                    subtotal=subtotal,
                    disponible=True,
                    es_propio=False,
                    seleccionado=False,
                    opciones_proveedores=opciones,
                )
                total += subtotal
            else:
                item = _item_sin_datos(producto, nombre, cantidad)
        else:
            item = _item_sin_datos(producto, nombre, cantidad)

        cotizacion.items.append(item)

    cotizacion.total = total
    sesion.estado = "cotizada"
    sesion.ambiguedades_resueltas = True
    db.add(cotizacion)
    await db.commit()
    await db.refresh(cotizacion)
    return cotizacion


async def agregar_item_cotizacion(
    db: AsyncSession, cotizacion: Cotizacion, comp: dict
) -> CotizacionItem:
    """Agrega un nuevo componente a una cotización existente (carrito)."""
    margen = Decimal(str(settings.MARGEN_COMPETENCIA)) / Decimal(100)
    producto = await _buscar_producto(db, comp)
    nombre = producto.nombre if producto else _nombre_producto(comp)
    cantidad = int(comp.get("cantidad", 1))

    proveedores = []
    if producto is not None:
        proveedores = await buscar_precios(db, producto)

    prov_propio = None
    prov_otros = []
    for prov in proveedores:
        if prov["disponible"] and prov["precio_unitario"] is not None:
            if prov["tienda"] == TIENDA_PROPIA:
                prov_propio = prov
            else:
                prov_otros.append(prov)

    if prov_propio:
        precio_unit = Decimal(str(prov_propio["precio_unitario"])).quantize(Decimal("0.01"))
        subtotal = (precio_unit * cantidad).quantize(Decimal("0.01"))
        item = CotizacionItem(
            cotizacion_id=cotizacion.id,
            producto_id=producto.id if producto else None,
            producto_nombre=nombre,
            cantidad=cantidad,
            precio_unitario=precio_unit,
            proveedor=TIENDA_PROPIA,
            margen_aplicado=Decimal(0),
            subtotal=subtotal,
            disponible=True,
            es_propio=True,
            seleccionado=True,
            opciones_proveedores=[],
        )
    elif prov_otros:
        opciones = []
        for prov in prov_otros:
            op = _construir_opcion(prov, margen, es_propio=False)
            if op:
                opciones.append(op)
        if opciones:
            opciones.sort(key=lambda o: o["precio_con_margen"])
            mejor = opciones[0]
            precio_unit = Decimal(str(mejor["precio_con_margen"])).quantize(Decimal("0.01"))
            subtotal = (precio_unit * cantidad).quantize(Decimal("0.01"))
            item = CotizacionItem(
                cotizacion_id=cotizacion.id,
                producto_id=producto.id if producto else None,
                producto_nombre=nombre,
                cantidad=cantidad,
                precio_unitario=precio_unit,
                proveedor=mejor["tienda"],
                margen_aplicado=Decimal(str(settings.MARGEN_COMPETENCIA)),
                subtotal=subtotal,
                disponible=True,
                es_propio=False,
                seleccionado=False,
                opciones_proveedores=opciones,
            )
        else:
            item = _item_sin_datos(producto, nombre, cantidad)
            item.cotizacion_id = cotizacion.id
    else:
        item = _item_sin_datos(producto, nombre, cantidad)
        item.cotizacion_id = cotizacion.id

    db.add(item)
    await db.flush()
    return item


def recalcular_total(cotizacion: Cotizacion) -> None:
    """Recalcula el total de la cotización basado en los items."""
    total = Decimal(0)
    for item in cotizacion.items:
        if item.disponible:
            total += item.subtotal
    cotizacion.total = total
