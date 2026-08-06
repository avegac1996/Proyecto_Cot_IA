"""Scraper estático usando httpx + BeautifulSoup4.

Soporta dos modos:
1. Precio en resultados de búsqueda (un solo request)
2. Precio en página de producto (dos requests: búsqueda -> producto)
El modo se determina por la presencia de 'price' en selectores.
Si no hay 'price' en search, usa 'product_page_price' en la página del producto.

Distingue entre productos simples y variables (WooCommerce):
- Producto simple: un solo precio, sin variantes seleccionables.
- Producto variable: múltiples variantes con precio propio (data-product_variations JSON).
"""

import asyncio
import json
import logging

import httpx
from bs4 import BeautifulSoup

from app.services.scraping import catalogo
from app.services.scraping.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

MAX_PRODUCT_PAGES = 10

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
        # Vía rápida: catálogo cacheado vía WooCommerce Store API (TTL 1 hora)
        try:
            if await catalogo.soporta_api_wc(self.url_base):
                productos = await catalogo.obtener_catalogo(self.url_base)
                if productos:
                    return catalogo.buscar_en_catalogo(productos, query)
        except Exception as exc:
            logger.warning("Catálogo WC falló en %s, usando scraping HTML: %s", self.nombre_tienda, exc)

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

        # Primera pasada: extraer info básica de cada card y precio si está en la búsqueda
        cards_info = []  # Info extraída sin visitar página
        cards_to_visit = []  # Cards que necesitan visita a página de producto

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

            # Detectar tipo de producto (simple vs variable) desde clases del card
            card_classes = card.get("class", []) or [] if hasattr(card, "get") else []
            is_variable = "product-type-variable" in card_classes

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
            precio_en_busqueda = None
            if price_selector:
                price_el = card.select_one(price_selector)
                if price_el:
                    precio_en_busqueda = self._parse_price(price_el.get_text(strip=True))

            if precio_en_busqueda is not None:
                results.append({
                    "precio": precio_en_busqueda,
                    "disponible": disponible,
                    "url": url_producto,
                    "nombre_producto": nombre_producto,
                    "variantes": [],
                })
            elif url_producto:
                cards_to_visit.append({
                    "url": url_producto,
                    "nombre": nombre_producto,
                    "disponible": disponible,
                    "is_variable": is_variable,
                })

        # Visitar páginas de producto en paralelo (hasta MAX_PRODUCT_PAGES)
        if cards_to_visit:
            page_price_selector = self.selectores.get("product_page_price", "p.price")
            page_avail_selector = self.selectores.get("product_page_availability", ".stock")
            cards_to_visit = cards_to_visit[:MAX_PRODUCT_PAGES]

            async def _visit_product(info: dict) -> list[dict]:
                url = info["url"]
                nombre = info["nombre"]
                disponible = info["disponible"]
                is_var = info["is_variable"]

                if is_var:
                    variantes_data = await self._scrape_variable_product(
                        url, page_price_selector, page_avail_selector
                    )
                    if variantes_data:
                        return [{
                            "precio": v["precio"],
                            "disponible": v["disponible"],
                            "url": url,
                            "nombre_producto": f"{nombre} - {v['nombre_variante']}" if v.get("nombre_variante") else nombre,
                            "variantes": [],
                        } for v in variantes_data]
                    # Fallback: precio base
                    precio, page_disponible, _ = await self._scrape_product_page(
                        url, page_price_selector, page_avail_selector
                    )
                    if precio is not None:
                        return [{
                            "precio": precio,
                            "disponible": page_disponible if page_disponible is not None else disponible,
                            "url": url,
                            "nombre_producto": nombre,
                            "variantes": [],
                        }]
                else:
                    precio, page_disponible, _ = await self._scrape_product_page(
                        url, page_price_selector, page_avail_selector
                    )
                    if precio is not None:
                        return [{
                            "precio": precio,
                            "disponible": page_disponible if page_disponible is not None else disponible,
                            "url": url,
                            "nombre_producto": nombre,
                            "variantes": [],
                        }]
                return []

            visit_results = await asyncio.gather(*[_visit_product(info) for info in cards_to_visit])
            for batch in visit_results:
                results.extend(batch)

        return results

    async def _scrape_product_page(
        self, url: str, price_selector: str, avail_selector: str
    ) -> tuple[float | None, bool | None, list[str]]:
        """Visita la página de un producto simple y extrae precio y disponibilidad."""
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
            return None, None, []

        soup = BeautifulSoup(response.text, "html.parser")

        precio = None
        price_el = soup.select_one(price_selector)
        if price_el:
            precio = self._parse_price(price_el.get_text(strip=True))

        disponible = None
        avail_el = soup.select_one(avail_selector)
        if avail_el:
            disponible = self._parse_availability(avail_el.get_text(strip=True))

        return precio, disponible, []

    async def _scrape_variable_product(
        self, url: str, price_selector: str, avail_selector: str
    ) -> list[dict]:
        """Extrae cada variación de un producto variable desde el JSON embebido de WooCommerce.

        Returns:
            list[dict] con keys: precio (float), disponible (bool), nombre_variante (str|None)
        """
        try:
            async with httpx.AsyncClient(
                headers=HEADERS,
                timeout=8.0,
                follow_redirects=True,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Error HTTP en producto variable %s: %s", url, exc)
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        # Buscar form.variations_form con data-product_variations JSON
        form = soup.select_one("form.variations_form")
        if not form:
            return []

        data_var = form.get("data-product_variations")
        if not data_var:
            return []

        try:
            variaciones = json.loads(data_var)
            if not isinstance(variaciones, list):
                # data-product_variations puede ser "false" (string)
                return []
        except (json.JSONDecodeError, TypeError):
            logger.warning("No se pudo parsear data-product_variations en %s", url)
            return []

        resultados = []
        for v in variaciones:
            precio = v.get("display_price") or v.get("display_regular_price")
            if precio is None:
                continue
            disponible = v.get("is_in_stock", True)
            # Extraer nombre de la variante desde attributes
            attrs = v.get("attributes", {})
            nombre_parts = []
            for key, val in attrs.items():
                if val:
                    nombre_parts.append(val)
            nombre_variante = " / ".join(nombre_parts) if nombre_parts else None

            resultados.append({
                "precio": float(precio),
                "disponible": disponible,
                "nombre_variante": nombre_variante,
            })

        return resultados
