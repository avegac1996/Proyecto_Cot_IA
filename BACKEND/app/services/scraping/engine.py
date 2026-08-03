import asyncio
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
SCRAPE_TIMEOUT_SECONDS = 15
MAX_PRODUCT_PAGE_VISITS = 3

# Cache en memoria por término (TTL 30 min)
_cache_termino: dict[str, tuple[datetime, list[dict]]] = {}
CACHE_TERMINO_TTL = timedelta(minutes=30)


async def buscar_precios(db: AsyncSession, producto: Producto) -> list[dict]:
    """Devuelve precios/disponibilidad por tienda para un producto.

    Primero consulta el cache de scraping en BD (respetando el TTL).
    Si no hay cache vigente, ejecuta scraping en vivo contra la tienda
    (BeautifulSoup para sitios estáticos, Playwright para dinámicos).
    """
    result = await db.execute(select(Tienda).where(Tienda.activa.is_(True)))
    tiendas = result.scalars().all()

    # Separar tiendas con cache vigente de las que necesitan scraping
    proveedores_cache: list[dict] = []
    tiendas_a_scrapear: list[Tienda] = []

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
            proveedores_cache.append({
                "tienda": tienda.nombre,
                "precio_unitario": float(entrada.precio) if entrada.precio is not None else None,
                "disponible": bool(entrada.disponible),
                "url": entrada.url_producto,
                "fuente": "cache",
            })
        else:
            tiendas_a_scrapear.append(tienda)

    # Scrapear todas las tiendas sin cache en paralelo
    async def _scrape_one(tienda: Tienda) -> dict:
        scraped_results: list[dict] = []
        try:
            scraper = await get_scraper(
                tienda.nombre,
                tienda.url_base,
                tienda.selectores,
                tienda.usa_javascript,
            )
            scraped_results = await asyncio.wait_for(
                scraper.scrape(producto.nombre),
                timeout=SCRAPE_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            logger.warning("Timeout scrapeando %s para '%s'", tienda.nombre, producto.nombre)
        except Exception as exc:
            logger.warning("Scraping falló para %s: %s", tienda.nombre, exc)

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

        return {
            "tienda": tienda.nombre,
            "precio_unitario": float(first["precio"]) if first["precio"] is not None else None,
            "disponible": first["disponible"],
            "url": first["url"],
            "fuente": "web_scraping",
        }

    resultados_scraping = await asyncio.gather(*[_scrape_one(t) for t in tiendas_a_scrapear])
    return proveedores_cache + resultados_scraping


async def _scrape_tienda(tienda: Tienda, termino: str) -> list[dict]:
    """Scrapea una sola tienda con timeout. Retorna lista de resultados."""
    try:
        scraper = await get_scraper(
            tienda.nombre,
            tienda.url_base,
            tienda.selectores,
            tienda.usa_javascript,
        )
        results = await asyncio.wait_for(
            scraper.scrape(termino),
            timeout=SCRAPE_TIMEOUT_SECONDS,
        )
        return results[:MAX_RESULTADOS_POR_TIENDA]
    except asyncio.TimeoutError:
        logger.warning("Timeout scrapeando %s para '%s'", tienda.nombre, termino)
        return []
    except Exception as exc:
        logger.warning("Scraping por término falló para %s: %s", tienda.nombre, exc)
        return []


async def buscar_por_termino(db: AsyncSession, termino: str) -> dict:
    """Busca un término libre en todas las tiendas activas.

    Usa cache en memoria (30 min TTL) y scraping paralelo con timeout.
    """
    # Verificar cache en memoria
    cache_key = termino.lower().strip()
    if cache_key in _cache_termino:
        cached_at, cached_opts = _cache_termino[cache_key]
        if datetime.now() - cached_at < CACHE_TERMINO_TTL:
            logger.info("Cache hit para término '%s'", termino)
            return {"termino": termino, "opciones": cached_opts, "fuente": "cache"}

    result = await db.execute(select(Tienda).where(Tienda.activa.is_(True)))
    tiendas = result.scalars().all()

    # Scraping paralelo: todas las tiendas al mismo tiempo
    tasks = [_scrape_tienda(tienda, termino) for tienda in tiendas]
    resultados_por_tienda = await asyncio.gather(*tasks, return_exceptions=False)

    opciones: list[dict] = []
    for tienda, scraped_results in zip(tiendas, resultados_por_tienda):
        for item in scraped_results:
            opciones.append({
                "tienda": tienda.nombre,
                "nombre_producto": item.get("nombre_producto") or termino,
                "precio_base": float(item["precio"]) if item["precio"] is not None else None,
                "disponible": item["disponible"],
                "url": item["url"],
            })

    # Guardar en cache
    _cache_termino[cache_key] = (datetime.now(), opciones)

    return {"termino": termino, "opciones": opciones, "fuente": "web_scraping"}
