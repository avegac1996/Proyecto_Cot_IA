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
            async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
                # Usar CDX API para listar snapshots, con fallback a availability API
                timestamps: list[str] = []
                try:
                    r = await client.get(
                        f"https://web.archive.org/cdx/search/cdx?url={self.url_base}{store_path}&output=json&limit=20&fl=timestamp"
                    )
                    data = r.json()
                    if len(data) > 1:
                        timestamps = sorted([row[0] for row in data[1:]], reverse=True)
                except Exception:
                    pass

                # Fallback: usar availability API si CDX no devolvió nada
                if not timestamps:
                    try:
                        r = await client.get(
                            f"https://archive.org/wayback/available?url={self.url_base}{store_path}"
                        )
                        data = r.json()
                        closest = data.get("archived_snapshots", {}).get("closest", {})
                        if closest.get("available"):
                            timestamps = [closest.get("timestamp", "")]
                    except Exception:
                        pass

                if not timestamps:
                    logger.warning("No hay snapshots de Wayback para %s", self.url_base)
                    return products

                # Probar cada snapshot hasta encontrar uno con productos
                timestamp = None
                first_page_with_cards = 1
                for ts in timestamps:
                    for try_page in [1, 2]:
                        if try_page == 1:
                            test_url = f"https://web.archive.org/web/{ts}/{self.url_base}{store_path}"
                        else:
                            test_url = f"https://web.archive.org/web/{ts}/{self.url_base}{store_path}page/2/"
                        try:
                            r = await client.get(test_url)
                            if r.status_code == 200:
                                soup = BeautifulSoup(r.text, "html.parser")
                                test_cards = soup.select(card_sel)
                                if test_cards:
                                    timestamp = ts
                                    first_page_with_cards = try_page
                                    logger.info("Usando snapshot de Wayback %s para %s (%d productos en pág %d)",
                                                timestamp, self.url_base, len(test_cards), try_page)
                                    for card in test_cards:
                                        self._process_card(card, link_sel, price_sel, stock_in_classes, products)
                                    break
                        except Exception:
                            continue
                    if timestamp is not None:
                        break

                # Si empezamos en página 2, intentar página 1 de snapshots anteriores
                if first_page_with_cards == 2 and len(timestamps) > 1:
                    for prev_ts in timestamps[1:]:
                        test_url = f"https://web.archive.org/web/{prev_ts}/{self.url_base}{store_path}"
                        try:
                            r = await client.get(test_url)
                            if r.status_code == 200:
                                soup = BeautifulSoup(r.text, "html.parser")
                                test_cards = soup.select(card_sel)
                                if test_cards:
                                    logger.info("Combinando con snapshot %s pág 1 (%d productos)", prev_ts, len(test_cards))
                                    for card in test_cards:
                                        self._process_card(card, link_sel, price_sel, stock_in_classes, products)
                                    # También intentar pág 2 de este snapshot
                                    test_url2 = f"https://web.archive.org/web/{prev_ts}/{self.url_base}{store_path}page/2/"
                                    try:
                                        r2 = await client.get(test_url2)
                                        if r2.status_code == 200:
                                            soup2 = BeautifulSoup(r2.text, "html.parser")
                                            cards2 = soup2.select(card_sel)
                                            if cards2:
                                                logger.info("Combinando con snapshot %s pág 2 (%d productos)", prev_ts, len(cards2))
                                                for card in cards2:
                                                    self._process_card(card, link_sel, price_sel, stock_in_classes, products)
                                    except Exception:
                                        pass
                                    break
                        except Exception:
                            continue
                    # Ya tenemos productos, no seguir paginando
                    timestamp = None

                if not products:
                    logger.warning("Ningún snapshot de Wayback tiene productos para %s", self.url_base)
                    return products

                # Paginar las páginas restantes solo si no combinamos snapshots
                if timestamp is not None:
                    page_num = first_page_with_cards + 1
                    while True:
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
                                self._process_card(card, link_sel, price_sel, stock_in_classes, products)

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

        # Deduplicar por nombre (puede haber overlap entre snapshots)
        seen_names = set()
        unique_products: list[dict] = []
        for p in products:
            key = p["nombre_producto"].lower().strip()
            if key not in seen_names:
                seen_names.add(key)
                unique_products.append(p)

        logger.info("Cargados %d productos de %s vía Wayback (%d duplicados removidos)",
                    len(unique_products), self.url_base, len(products) - len(unique_products))
        _all_products_cache = unique_products
        _all_products_cache_time = now
        return unique_products

    def _process_card(self, card, link_sel: str, price_sel: str, stock_in_classes: bool, products: list[dict]):
        """Extrae nombre, precio, URL y disponibilidad de un card de producto."""
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
