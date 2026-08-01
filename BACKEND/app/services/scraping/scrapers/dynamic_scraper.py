"""Scraper dinámico usando Playwright para sitios que requieren JavaScript."""

import logging

from app.services.scraping.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class DynamicScraper(BaseScraper):
    """Scraper para sitios que requieren renderizado JavaScript (Playwright)."""

    async def scrape(self, query: str) -> dict:
        url_busqueda = self._build_search_url(query)
        result = {"precio": None, "disponible": False, "url": None}

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("Playwright no está instalado. Ejecutar: pip install playwright && playwright install chromium")
            return result

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url_busqueda, wait_until="networkidle", timeout=30000)

                # Esperar a que carguen las tarjetas de producto
                card_selector = self.selectores.get("product_card", "")
                if card_selector:
                    try:
                        await page.wait_for_selector(card_selector, timeout=10000)
                    except Exception:
                        logger.info("No se encontraron productos dinámicos en %s", self.nombre_tienda)
                        await browser.close()
                        return result

                price_selector = self.selectores.get("price", "")
                availability_selector = self.selectores.get("availability", "")
                link_selector = self.selectores.get("product_url", "")

                # Extraer datos del primer producto con precio
                cards = await page.query_selector_all(card_selector) if card_selector else []
                for card in cards:
                    price_el = await card.query_selector(price_selector) if price_selector else None
                    if price_el is None:
                        continue
                    price_text = await price_el.inner_text()
                    precio = self._parse_price(price_text)
                    if precio is None:
                        continue

                    disponible = True
                    if availability_selector:
                        avail_el = await card.query_selector(availability_selector)
                        if avail_el:
                            avail_text = await avail_el.inner_text()
                            disponible = self._parse_availability(avail_text)

                    url_producto = None
                    if link_selector:
                        link_el = await card.query_selector(link_selector)
                        if link_el:
                            href = await link_el.get_attribute("href")
                            if href:
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

                await browser.close()
        except Exception as exc:
            logger.error("Error en scraping dinámico de %s: %s", self.nombre_tienda, exc)

        return result
