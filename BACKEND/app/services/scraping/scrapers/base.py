"""Clase base para todos los scrapers de tiendas."""

import re
from abc import ABC, abstractmethod
from urllib.parse import quote_plus


class BaseScraper(ABC):
    """Define la interfaz común para scrapers estáticos y dinámicos."""

    def __init__(self, nombre_tienda: str, url_base: str, selectores: dict):
        self.nombre_tienda = nombre_tienda
        self.url_base = url_base.rstrip("/")
        self.selectores = selectores or {}

    def _build_search_url(self, query: str) -> str:
        """Construye la URL de búsqueda a partir del template en selectores."""
        template = self.selectores.get("search_url", "")
        if template and "{query}" in template:
            return template.replace("{query}", quote_plus(query))
        # Fallback: buscar en la raíz del sitio
        return f"{self.url_base}/?s={quote_plus(query)}"

    @staticmethod
    def _parse_price(text: str | None) -> float | None:
        """Extrae el valor numérico de un texto de precio."""
        if not text:
            return None
        # Remover todo excepto dígitos, punto y coma
        cleaned = re.sub(r"[^\d.,]", "", text.strip())
        if not cleaned:
            return None
        # Si hay coma y punto, asumir formato europeo (1.234,56)
        if "," in cleaned and "." in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "," in cleaned and "." not in cleaned:
            # Podría ser separador decimal europeo o miles
            parts = cleaned.split(",")
            if len(parts) == 2 and len(parts[1]) <= 2:
                cleaned = cleaned.replace(",", ".")
            else:
                cleaned = cleaned.replace(",", "")
        try:
            return float(cleaned)
        except ValueError:
            return None

    @staticmethod
    def _parse_availability(text: str | None) -> bool:
        """Determina si un producto está disponible según el texto."""
        if not text:
            return False
        text_lower = text.strip().lower()
        # Palabras que indican sin stock
        unavailable_keywords = [
            "agotado", "sin stock", "out of stock", "no disponible",
            "sold out", "sin existencias", "no hay stock",
        ]
        return not any(kw in text_lower for kw in unavailable_keywords)

    @abstractmethod
    async def scrape(self, query: str) -> list[dict]:
        """Ejecuta el scraping y devuelve una LISTA de resultados.

        Returns:
            list[dict] donde cada dict tiene keys:
                precio (float|None), disponible (bool), url (str|None),
                nombre_producto (str|None)
        """
        ...
