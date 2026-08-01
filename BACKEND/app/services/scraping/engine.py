from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scraping_cache import ScrapingCache
from app.models.tienda import Tienda


async def buscar_precios(db: AsyncSession, producto_id: int) -> list[dict]:
    """Devuelve precios/disponibilidad por tienda para un producto.

    Usa el cache de scraping en BD (respetando el TTL). El scraping en vivo
    contra las tiendas se implementará tras el análisis de cada sitio.
    """
    result = await db.execute(select(Tienda).where(Tienda.activa.is_(True)))
    tiendas = result.scalars().all()

    proveedores: list[dict] = []
    for tienda in tiendas:
        result = await db.execute(
            select(ScrapingCache).where(
                ScrapingCache.producto_id == producto_id,
                ScrapingCache.tienda == tienda.nombre,
            )
        )
        entrada = result.scalar_one_or_none()

        vigente = (
            entrada is not None
            and entrada.fecha_consulta is not None
            and entrada.fecha_consulta + timedelta(hours=entrada.ttl_horas) > datetime.now()
        )

        if vigente:
            proveedores.append({
                "tienda": tienda.nombre,
                "precio_unitario": float(entrada.precio) if entrada.precio is not None else None,
                "disponible": bool(entrada.disponible),
                "url": entrada.url_producto,
                "fuente": "cache",
            })
        else:
            # TODO: scraping en vivo (BeautifulSoup/Playwright) cuando se analicen los sitios
            proveedores.append({
                "tienda": tienda.nombre,
                "precio_unitario": None,
                "disponible": False,
                "url": tienda.url_base,
                "fuente": "sin_datos",
            })

    return proveedores
