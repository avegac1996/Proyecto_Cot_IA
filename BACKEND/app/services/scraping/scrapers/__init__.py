from app.services.scraping.scrapers.base import BaseScraper
from app.services.scraping.scrapers.static_scraper import StaticScraper
from app.services.scraping.scrapers.dynamic_scraper import DynamicScraper
from app.services.scraping.scrapers.wayback_scraper import WaybackScraper

__all__ = ["BaseScraper", "StaticScraper", "DynamicScraper", "WaybackScraper", "get_scraper"]


async def get_scraper(
    nombre_tienda: str,
    url_base: str,
    selectores: dict,
    usa_javascript: bool,
) -> BaseScraper:
    """Fábrica que devuelve el scraper adecuado según la configuración."""
    # Si la tienda tiene use_wayback=True, usar Wayback Machine
    if selectores and selectores.get("use_wayback", False):
        return WaybackScraper(nombre_tienda, url_base, selectores)
    if usa_javascript:
        return DynamicScraper(nombre_tienda, url_base, selectores)
    return StaticScraper(nombre_tienda, url_base, selectores)
