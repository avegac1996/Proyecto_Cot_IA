"""Scraper estático usando httpx + BeautifulSoup4."""

import logging

import httpx
from bs4 import BeautifulSoup

from app.services.scraping.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

# Headers para simular un navegador real
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

    async def scrape(self, query: str) -> dict:
        url_busqueda = self._build_search_url(query)
        result = {"precio": None, "disponible": False, "url": None}

        try:
            async with httpx.AsyncClient(
                headers=HEADERS,
                timeout=10.0,
                follow_redirects=True,
            ) as client:
                response = await client.get(url_busqueda)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Error HTTP en %s: %s", self.nombre_tienda, exc)
            return result

        soup = BeautifulSoup(response.text, "html.parser")

        # Buscar tarjetas de producto usando el selector configurado
        card_selector = self.selectores.get("product_card", "")
        price_selector = self.selectores.get("price", "")
        availability_selector = self.selectores.get("availability", "")
        link_selector = self.selectores.get("product_url", "")

        if not card_selector:
            logger.warning("No hay selector 'product_card' para %s", self.nombre_tienda)
            return result

        cards = soup.select(card_selector)
        if not cards:
            logger.info("No se encontraron productos en %s para query '%s'", self.nombre_tienda, query)
            return result

        # Tomar el primer resultado que tenga precio
        for card in cards:
            price_el = card.select_one(price_selector) if price_selector else None
            avail_el = card.select_one(availability_selector) if availability_selector else None
            link_el = card.select_one(link_selector) if link_selector else None

            precio = self._parse_price(price_el.get_text(strip=True) if price_el else None)
            if precio is None:
                continue

            disponible = True
            if avail_el:
                disponible = self._parse_availability(avail_el.get_text(strip=True))

            url_producto = None
            if link_el and link_el.get("href"):
                href = link_el["href"]
                if href.startswith("/"):
                    url_producto = f"{self.url_base}{href}"
                elif not href.startswith("http"):
                    url_producto = f"{self.url_base}/{href}"
                else:
                    url_producto = href

            result = {
                "precio": precio,
                "disponible": disponible,
                "url": url_producto,
            }
            break

        return result
