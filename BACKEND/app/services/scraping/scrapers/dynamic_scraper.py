"""Scraper dinámico usando Playwright para sitios que requieren JavaScript.

Soporta dos modos:
1. Precio en resultados de búsqueda (un solo render)
2. Precio en página de producto (dos renders: búsqueda -> producto)
"""

import logging

from app.services.scraping.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

MAX_PRODUCT_PAGES = 3


class DynamicScraper(BaseScraper):
    """Scraper para sitios que requieren renderizado JavaScript (Playwright)."""

    async def scrape(self, query: str) -> list[dict]:
        url_busqueda = self._build_search_url(query)
        results: list[dict] = []

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("Playwright no está instalado. Ejecutar: pip install playwright && playwright install chromium")
            return results

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url_busqueda, wait_until="domcontentloaded", timeout=10000)

                card_selector = self.selectores.get("product_card", "")
                price_selector = self.selectores.get("price", "")
                link_selector = self.selectores.get("product_url", "")
                availability_selector = self.selectores.get("availability", "")
                stock_in_classes = self.selectores.get("stock_in_classes", False)

                if card_selector:
                    try:
                        await page.wait_for_selector(card_selector, timeout=5000)
                    except Exception:
                        logger.info("No se encontraron productos dinámicos en %s", self.nombre_tienda)
                        await browser.close()
                        return results

                cards = await page.query_selector_all(card_selector) if card_selector else []

                page_visit_count = 0

                for card in cards:
                    # URL del producto
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

                    # Nombre del producto
                    nombre_producto = None
                    if link_selector:
                        link_el = await card.query_selector(link_selector)
                        if link_el:
                            nombre_producto = await link_el.inner_text()

                    # Disponibilidad
                    disponible = True
                    if stock_in_classes:
                        class_attr = await card.get_attribute("class")
                        if class_attr:
                            classes = class_attr.split()
                            disponible = "instock" in classes and "outofstock" not in classes
                    elif availability_selector:
                        avail_el = await card.query_selector(availability_selector)
                        if avail_el:
                            avail_text = await avail_el.inner_text()
                            disponible = self._parse_availability(avail_text)

                    # Precio en búsqueda
                    if price_selector:
                        price_el = await card.query_selector(price_selector)
                        if price_el:
                            price_text = await price_el.inner_text()
                            precio = self._parse_price(price_text)
                            if precio is not None:
                                results.append({
                                    "precio": precio,
                                    "disponible": disponible,
                                    "url": url_producto,
                                    "nombre_producto": nombre_producto,
                                })
                                continue

                    # Si no hay precio en búsqueda, visitar página de producto
                    if url_producto and page_visit_count < MAX_PRODUCT_PAGES:
                        page_visit_count += 1
                        page_price_sel = self.selectores.get("product_page_price", "p.price")
                        page_avail_sel = self.selectores.get("product_page_availability", ".stock")
                        precio, page_disp = await self._scrape_product_page_playwright(
                            browser, url_producto, page_price_sel, page_avail_sel
                        )
                        if precio is not None:
                            results.append({
                                "precio": precio,
                                "disponible": page_disp if page_disp is not None else disponible,
                                "url": url_producto,
                                "nombre_producto": nombre_producto,
                            })

                await browser.close()
        except Exception as exc:
            logger.error("Error en scraping dinámico de %s: %s", self.nombre_tienda, exc)

        return results

    async def _scrape_product_page_playwright(
        self, browser, url: str, price_selector: str, avail_selector: str
    ) -> tuple[float | None, bool | None]:
        """Visita la página de un producto con Playwright y extrae precio/disponibilidad."""
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=10000)

            precio = None
            try:
                price_el = await page.query_selector(price_selector)
                if price_el:
                    price_text = await price_el.inner_text()
                    precio = self._parse_price(price_text)
            except Exception:
                pass

            disponible = None
            try:
                avail_el = await page.query_selector(avail_selector)
                if avail_el:
                    avail_text = await avail_el.inner_text()
                    disponible = self._parse_availability(avail_text)
            except Exception:
                pass

            return precio, disponible
        finally:
            await page.close()
