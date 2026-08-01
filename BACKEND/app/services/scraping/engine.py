import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.producto import Producto
from app.models.scraping_cache import ScrapingCache
from app.models.tienda import Tienda
from app.services.scraping.scrapers import get_scraper

logger = logging.getLogger(__name__)

MAX_RESULTADOS_POR_TIENDA = 10


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
            # Scraping en vivo — scrape() ahora retorna list[dict]
            scraped_results: list[dict] = []
            try:
                scraper = await get_scraper(
                    tienda.nombre,
                    tienda.url_base,
                    tienda.selectores,
                    tienda.usa_javascript,
                )
                scraped_results = await scraper.scrape(producto.nombre)
            except Exception as exc:
                logger.warning("Scraping falló para %s: %s", tienda.nombre, exc)

            # Tomar el primer resultado para cachear (compatibilidad)
            first = scraped_results[0] if scraped_results else {"precio": None, "disponible": False, "url": None}

            # Guardar en cache
            nueva_entrada = ScrapingCache(
                producto_id=producto.id,
                tienda=tienda.nombre,
                precio=first["precio"],
                disponible=first["disponible"],
                url_producto=first["url"],
                fecha_consulta=datetime.now(),
                ttl_horas=tienda.ttl_horas,
            )
            db.add(nueva_entrada)
            await db.commit()

            # Retornar el primer resultado para compatibilidad con flujo existente
            proveedores.append({
                "tienda": tienda.nombre,
                "precio_unitario": float(first["precio"]) if first["precio"] is not None else None,
                "disponible": first["disponible"],
                "url": first["url"],
                "fuente": "web_scraping",
            })

    return proveedores


async def buscar_por_termino(db: AsyncSession, termino: str) -> dict:
    """Busca un término libre en todas las tiendas activas.

    A diferencia de buscar_precios, no requiere un Producto en BD.
    Retorna todas las opciones encontradas por tienda.
    """
    result = await db.execute(select(Tienda).where(Tienda.activa.is_(True)))
    tiendas = result.scalars().all()

    opciones: list[dict] = []
    for tienda in tiendas:
        try:
            scraper = await get_scraper(
                tienda.nombre,
                tienda.url_base,
                tienda.selectores,
                tienda.usa_javascript,
            )
            scraped_results = await scraper.scrape(termino)
        except Exception as exc:
            logger.warning("Scraping por término falló para %s: %s", tienda.nombre, exc)
            scraped_results = []

        for item in scraped_results[:MAX_RESULTADOS_POR_TIENDA]:
            opciones.append({
                "tienda": tienda.nombre,
                "nombre_producto": item.get("nombre_producto") or termino,
                "precio_base": float(item["precio"]) if item["precio"] is not None else None,
                "disponible": item["disponible"],
                "url": item["url"],
            })

    return {"termino": termino, "opciones": opciones}
