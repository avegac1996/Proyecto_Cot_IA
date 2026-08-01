from app.services.scraping.scrapers.base import BaseScraper
from app.services.scraping.scrapers.static_scraper import StaticScraper
from app.services.scraping.scrapers.dynamic_scraper import DynamicScraper

__all__ = ["BaseScraper", "StaticScraper", "DynamicScraper", "get_scraper"]


async def get_scraper(
    nombre_tienda: str,
    url_base: str,
    selectores: dict,
    usa_javascript: bool,
) -> BaseScraper:
    """Fábrica que devuelve el scraper adecuado según si la tienda usa JS o no."""
    if usa_javascript:
        return DynamicScraper(nombre_tienda, url_base, selectores)
    return StaticScraper(nombre_tienda, url_base, selectores)
