"""Scraper estático usando httpx + BeautifulSoup4.

Soporta dos modos:
1. Precio en resultados de búsqueda (un solo request)
2. Precio en página de producto (dos requests: búsqueda -> producto)
El modo se determina por la presencia de 'price' en selectores.
Si no hay 'price' en search, usa 'product_page_price' en la página del producto.
"""

import logging

import httpx
from bs4 import BeautifulSoup

from app.services.scraping.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

MAX_PRODUCT_PAGES = 3

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}


class StaticScraper(BaseScraper):
    """Scraper para sitios que no requieren JavaScript (HTML estático)."""

    async def scrape(self, query: str) -> list[dict]:
        url_busqueda = self._build_search_url(query)
        results: list[dict] = []

        try:
            async with httpx.AsyncClient(
                headers=HEADERS,
                timeout=8.0,
                follow_redirects=True,
            ) as client:
                response = await client.get(url_busqueda)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Error HTTP en %s: %s", self.nombre_tienda, exc)
            return results

        soup = BeautifulSoup(response.text, "html.parser")

        card_selector = self.selectores.get("product_card", "")
        price_selector = self.selectores.get("price", "")
        link_selector = self.selectores.get("product_url", "")
        availability_selector = self.selectores.get("availability", "")

        if not card_selector:
            logger.warning("No hay selector 'product_card' para %s", self.nombre_tienda)
            return results

        cards = soup.select(card_selector)
        if not cards:
            logger.info("No se encontraron productos en %s para query '%s'", self.nombre_tienda, query)
            return results

        # Determinar disponibilidad desde clases del card (WooCommerce)
        stock_in_classes = self.selectores.get("stock_in_classes", False)

        page_visit_count = 0

        for card in cards:
            # Obtener URL del producto
            url_producto = None
            if link_selector:
                link_el = card.select_one(link_selector)
                if link_el and link_el.get("href"):
                    href = link_el["href"]
                    if href.startswith("/"):
                        url_producto = f"{self.url_base}{href}"
                    elif not href.startswith("http"):
                        url_producto = f"{self.url_base}/{href}"
                    else:
                        url_producto = href

            # Nombre del producto
            nombre_producto = None
            if link_selector:
                link_el = card.select_one(link_selector)
                if link_el:
                    nombre_producto = link_el.get_text(strip=True)

            # Disponibilidad
            disponible = True
            if stock_in_classes and hasattr(card, "get"):
                classes = card.get("class", []) or []
                disponible = "instock" in classes and "outofstock" not in classes
            elif availability_selector:
                avail_el = card.select_one(availability_selector)
                if avail_el:
                    disponible = self._parse_availability(avail_el.get_text(strip=True))

            # Precio en búsqueda (si existe el selector)
            if price_selector:
                price_el = card.select_one(price_selector)
                if price_el:
                    precio = self._parse_price(price_el.get_text(strip=True))
                    if precio is not None:
                        results.append({
                            "precio": precio,
                            "disponible": disponible,
                            "url": url_producto,
                            "nombre_producto": nombre_producto,
                        })
                        continue

            # Si no hay precio en búsqueda, visitar página de producto (limitado)
            if url_producto and page_visit_count < MAX_PRODUCT_PAGES:
                page_visit_count += 1
                page_price_selector = self.selectores.get("product_page_price", "p.price")
                page_avail_selector = self.selectores.get("product_page_availability", ".stock")
                precio, page_disponible = await self._scrape_product_page(
                    url_producto, page_price_selector, page_avail_selector
                )
                if precio is not None:
                    results.append({
                        "precio": precio,
                        "disponible": page_disponible if page_disponible is not None else disponible,
                        "url": url_producto,
                        "nombre_producto": nombre_producto,
                    })

        return results

    async def _scrape_product_page(
        self, url: str, price_selector: str, avail_selector: str
    ) -> tuple[float | None, bool | None]:
        """Visita la página de un producto y extrae precio y disponibilidad."""
        try:
            async with httpx.AsyncClient(
                headers=HEADERS,
                timeout=8.0,
                follow_redirects=True,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Error HTTP en página de producto %s: %s", url, exc)
            return None, None

        soup = BeautifulSoup(response.text, "html.parser")

        precio = None
        price_el = soup.select_one(price_selector)
        if price_el:
            precio = self._parse_price(price_el.get_text(strip=True))

        disponible = None
        avail_el = soup.select_one(avail_selector)
        if avail_el:
            disponible = self._parse_availability(avail_el.get_text(strip=True))

        return precio, disponible
