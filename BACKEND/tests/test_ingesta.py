"""Tests for the text parser (ingesta)."""

from app.services.ingesta.texto import parsear_linea, parsear_texto
from app.services.matching.normalizer import detectar_tipo


class TestParsearLinea:
    def test_resistencia_con_cantidad(self):
        result = parsear_linea("5 resistencias de 220 ohm")
        assert result["cantidad"] == 5
        assert result["tipo"] == "resistencia"
        assert result["valor"] is not None

    def test_led_simple(self):
        result = parsear_linea("10 leds rojos 5mm")
        assert result["cantidad"] == 10
        assert result["tipo"] == "led"

    def test_arduino_uno(self):
        result = parsear_linea("1 arduino uno")
        assert result["cantidad"] == 1
        assert result["tipo"] == "arduino"

    def test_cantidad_al_final(self):
        result = parsear_linea("led x5")
        assert result["cantidad"] == 5

    def test_linea_vacia(self):
        result = parsear_linea("")
        assert result["texto_original"] == ""

    def test_linea_corta_se_ignora(self):
        componentes = parsear_texto("a")
        assert len(componentes) == 0


class TestParsearTexto:
    def test_multiples_lineas(self):
        texto = "5 resistencias de 220 ohm\n10 leds rojos 5mm\n1 arduino uno"
        result = parsear_texto(texto)
        assert len(result) == 3
        assert result[0]["cantidad"] == 5
        assert result[1]["cantidad"] == 10
        assert result[2]["cantidad"] == 1

    def test_separador_punto_coma(self):
        texto = "5 resistencias;10 leds;1 arduino"
        result = parsear_texto(texto)
        assert len(result) == 3

    def test_lineas_vacias_se_ignoran(self):
        texto = "5 resistencias\n\n\n10 leds"
        result = parsear_texto(texto)
        assert len(result) == 2


class TestDetectarTipo:
    def test_resistencia(self):
        assert detectar_tipo("resistencia 220 ohm") == "resistencia"

    def test_led(self):
        assert detectar_tipo("led rojo 5mm") == "led"

    def test_capacitor(self):
        assert detectar_tipo("capacitor 100uf") == "capacitor"

    def test_arduino(self):
        assert detectar_tipo("arduino uno") == "arduino"

    def test_desconocido(self):
        assert detectar_tipo("widget raro") == "desconocido"
