"""Scraper vía Wayback Machine para sitios protegidos por captcha.

Cuando una tienda tiene protección anti-bot (SiteGuard, Cloudflare, etc),
este scraper usa los snapshots cacheados de archive.org para obtener
los productos de la tienda.
"""

import logging
import re
import time

import httpx
from bs4 import BeautifulSoup

from app.services.scraping.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}

# Cache en memoria: {termino: (timestamp, [resultados])}
_wayback_cache: dict[str, tuple[float, list[dict]]] = {}
_WAYBACK_CACHE_TTL = 3600  # 1 hora

# Cache de todos los productos de la tienda (cargado una vez)
_all_products_cache: list[dict] | None = None
_all_products_cache_time: float = 0


def _clean_wayback_url(url: str) -> str:
    """Extrae la URL original de una URL de Wayback Machine."""
    match = re.search(r"/web/\d+/(https?://.+)", url)
    if match:
        return match.group(1)
    return url


class WaybackScraper(BaseScraper):
    """Scraper que usa Wayback Machine para evadir protecciones anti-bot.

    Estrategia:
    1. Carga todos los productos del snapshot más reciente de /store/
    2. Filtra por el término de búsqueda
    3. Los resultados se cachean en memoria por 1 hora
    """

    async def _load_all_products(self) -> list[dict]:
        """Carga todos los productos desde Wayback Machine."""
        global _all_products_cache, _all_products_cache_time

        now = time.time()
        if _all_products_cache is not None and (now - _all_products_cache_time) < _WAYBACK_CACHE_TTL:
            return _all_products_cache

        products: list[dict] = []
        store_path = self.selectores.get("store_path", "/store/")
        card_sel = self.selectores.get("product_card", "li.product")
        link_sel = self.selectores.get("product_url", "h2 a, h2, .woocommerce-loop-product__title a")
        price_sel = self.selectores.get("price", ".woocommerce-Price-amount, .price ins .woocommerce-Price-amount, .price")
        stock_in_classes = self.selectores.get("stock_in_classes", True)

        try:
            async with httpx.AsyncClient(headers=HEADERS, timeout=60, follow_redirects=True) as client:
                # Buscar el snapshot más reciente con la availability API
                r = await client.get(
                    f"https://archive.org/wayback/available?url={self.url_base}{store_path}"
                )
                data = r.json()
                snapshots = data.get("archived_snapshots", {})
                closest = snapshots.get("closest", {})
                if not closest or not closest.get("available"):
                    logger.warning("No hay snapshots de Wayback para %s", self.url_base)
                    return products

                timestamp = closest.get("timestamp", "")
                if not timestamp:
                    logger.warning("No se obtuvo timestamp de Wayback")
                    return products

                logger.info("Usando snapshot de Wayback %s para %s", timestamp, self.url_base)

                # Paginar todas las páginas de la tienda
                page_num = 1
                while True:
                    if page_num == 1:
                        url = f"https://web.archive.org/web/{timestamp}/{self.url_base}{store_path}"
                    else:
                        url = f"https://web.archive.org/web/{timestamp}/{self.url_base}{store_path}page/{page_num}/"

                    try:
                        r = await client.get(url)
                        if r.status_code != 200:
                            break

                        soup = BeautifulSoup(r.text, "html.parser")
                        cards = soup.select(card_sel)
                        logger.info("Wayback página %d: %d cards encontrados", page_num, len(cards))
                        if not cards:
                            break

                        for card in cards:
                            # Nombre y URL - intentar múltiples selectores
                            name_el = None
                            for sel in link_sel.split(","):
                                sel = sel.strip()
                                if sel:
                                    name_el = card.select_one(sel)
                                    if name_el:
                                        break
                            
                            # Fallback: buscar h2 directamente
                            if not name_el:
                                name_el = card.select_one("h2")
                            
                            nombre = name_el.get_text(strip=True) if name_el else None
                            url_producto = None
                            if name_el and name_el.name == "a":
                                url_producto = _clean_wayback_url(name_el.get("href", ""))
                            if not url_producto:
                                # Buscar cualquier enlace dentro del card
                                link_el = card.select_one("a[href]")
                                if link_el:
                                    url_producto = _clean_wayback_url(link_el.get("href", ""))

                            # Precio - intentar múltiples selectores
                            precio = None
                            if price_sel:
                                for sel in price_sel.split(","):
                                    sel = sel.strip()
                                    if sel:
                                        price_el = card.select_one(sel)
                                        if price_el:
                                            precio = self._parse_price(price_el.get_text(strip=True))
                                            if precio is not None:
                                                break

                            # Disponibilidad
                            disponible = True
                            if stock_in_classes and hasattr(card, "get"):
                                classes = card.get("class", []) or []
                                disponible = "instock" in classes and "outofstock" not in classes

                            if nombre and precio is not None:
                                products.append({
                                    "nombre_producto": nombre,
                                    "precio": precio,
                                    "disponible": disponible,
                                    "url": url_producto,
                                })
                            elif nombre:
                                logger.debug("Wayback: producto '%s' sin precio (price_sel=%s)", nombre, price_sel)

                        # Verificar si hay siguiente página
                        next_links = soup.select("a.next.page-numbers, ul.page-numbers a.next, a.next")
                        if not next_links:
                            break
                        page_num += 1

                    except Exception as exc:
                        logger.warning("Error cargando página %d de Wayback: %s", page_num, exc)
                        break

        except Exception as exc:
            logger.error("Error cargando productos de Wayback: %s", exc)

        logger.info("Cargados %d productos de %s vía Wayback", len(products), self.url_base)
        _all_products_cache = products
        _all_products_cache_time = now
        return products

    async def scrape(self, query: str) -> list[dict]:
        """Busca productos filtrando el catálogo cacheado de Wayback."""
        # Verificar cache de búsqueda
        cache_key = query.lower().strip()
        now = time.time()
        if cache_key in _wayback_cache:
            cached_at, cached_results = _wayback_cache[cache_key]
            if now - cached_at < _WAYBACK_CACHE_TTL:
                return cached_results

        all_products = await self._load_all_products()
        if not all_products:
            return []

        query_lower = query.lower()
        query_words = [w for w in query_lower.split() if len(w) > 2]

        results: list[dict] = []
        for prod in all_products:
            name_lower = prod["nombre_producto"].lower()
            # Match: término completo o cualquier palabra significativa
            if query_lower in name_lower or any(w in name_lower for w in query_words):
                results.append({
                    "precio": prod["precio"],
                    "disponible": prod["disponible"],
                    "url": prod["url"],
                    "nombre_producto": prod["nombre_producto"],
                })

        # Si no hay match exacto, buscar productos que compartan al menos una palabra
        if not results and query_words:
            for prod in all_products:
                name_lower = prod["nombre_producto"].lower()
                if any(w in name_lower for w in query_words):
                    results.append({
                        "precio": prod["precio"],
                        "disponible": prod["disponible"],
                        "url": prod["url"],
                        "nombre_producto": prod["nombre_producto"],
                    })

        _wayback_cache[cache_key] = (now, results[:10])
        return results[:10]
