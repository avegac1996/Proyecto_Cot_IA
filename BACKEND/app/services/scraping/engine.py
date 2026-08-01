import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.producto import Producto
from app.models.scraping_cache import ScrapingCache
from app.models.tienda import Tienda
from app.services.scraping.scrapers import get_scraper

logger = logging.getLogger(__name__)


async def buscar_precios(db: AsyncSession, producto: Producto) -> list[dict]:
    """Devuelve precios/disponibilidad por tienda para un producto.

    Primero consulta el cache de scraping en BD (respetando el TTL).
    Si no hay cache vigente, ejecuta scraping en vivo contra la tienda
    (BeautifulSoup para sitios estáticos, Playwright para dinámicos).
    """
    result = await db.execute(select(Tienda).where(Tienda.activa.is_(True)))
    tiendas = result.scalars().all()

    proveedores: list[dict] = []
    for tienda in tiendas:
        result = await db.execute(
            select(ScrapingCache).where(
                ScrapingCache.producto_id == producto.id,
                ScrapingCache.tienda == tienda.nombre,
            )
        )
        entrada = result.scalar_one_or_none()

        vigente = (
            entrada is not None
            and entrada.fecha_consulta is not None
            and entrada.fecha_consulta + timedelta(hours=entrada.ttl_horas or 24) > datetime.now()
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
            # Scraping en vivo
            scraped_data = {"precio": None, "disponible": False, "url": None}
            try:
                scraper = await get_scraper(
                    tienda.nombre,
                    tienda.url_base,
                    tienda.selectores,
                    tienda.usa_javascript,
                )
                scraped_data = await scraper.scrape(producto.nombre)
            except Exception as exc:
                logger.warning("Scraping falló para %s: %s", tienda.nombre, exc)

            # Guardar en cache
            nueva_entrada = ScrapingCache(
                producto_id=producto.id,
                tienda=tienda.nombre,
                precio=scraped_data["precio"],
                disponible=scraped_data["disponible"],
                url_producto=scraped_data["url"],
                fecha_consulta=datetime.now(),
                ttl_horas=tienda.ttl_horas,
            )
            db.add(nueva_entrada)
            await db.commit()

            proveedores.append({
                "tienda": tienda.nombre,
                "precio_unitario": float(scraped_data["precio"]) if scraped_data["precio"] is not None else None,
                "disponible": scraped_data["disponible"],
                "url": scraped_data["url"],
                "fuente": "web_scraping",
            })

    return proveedores
