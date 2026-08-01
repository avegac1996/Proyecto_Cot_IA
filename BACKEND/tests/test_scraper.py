"""Tests for the price parser utility."""

from app.services.scraping.scrapers.base import BaseScraper


class TestParsePrice:
    def test_dolar_simple(self):
        assert BaseScraper._parse_price("$12.40") == 12.40

    def test_dolar_con_iva(self):
        assert BaseScraper._parse_price("$0.30IVA incluido") == 0.30

    def test_dolar_cero(self):
        assert BaseScraper._parse_price("$0.00") == 0.0

    def test_euro_formato(self):
        assert BaseScraper._parse_price("1,234.56") == 1234.56

    def test_europeo_decimal(self):
        assert BaseScraper._parse_price("12,50") == 12.50

    def test_europeo_miles(self):
        assert BaseScraper._parse_price("1,200") == 1200.0

    def test_none(self):
        assert BaseScraper._parse_price(None) is None

    def test_vacio(self):
        assert BaseScraper._parse_price("") is None

    def test_sin_numeros(self):
        assert BaseScraper._parse_price("Sin precio") is None


class TestParseAvailability:
    def test_disponible(self):
        assert BaseScraper._parse_availability("En stock") is True

    def test_agotado(self):
        assert BaseScraper._parse_availability("Agotado") is False

    def test_sin_stock(self):
        assert BaseScraper._parse_availability("Sin stock") is False

    def test_sin_existencias(self):
        assert BaseScraper._parse_availability("Sin existencias") is False

    def test_none(self):
        assert BaseScraper._parse_availability(None) is False
