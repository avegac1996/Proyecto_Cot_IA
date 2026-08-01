"""Tests del filtro de n-grams para extracción de componentes."""

import pytest

from app.services.ingesta.filtro import extraer_componentes


class TestExtraerComponentes:
    def test_un_componente_simple(self):
        resultado = extraer_componentes("arduino")
        assert len(resultado) == 1
        assert resultado[0]["termino"] == "arduino"
        assert resultado[0]["cantidad"] == 1

    def test_componente_con_cantidad(self):
        resultado = extraer_componentes("5 resistencias")
        assert len(resultado) == 1
        assert resultado[0]["termino"] == "resistencia"
        assert resultado[0]["cantidad"] == 5

    def test_multiples_componentes(self):
        resultado = extraer_componentes("1 arduino y 10 leds")
        assert len(resultado) == 2
        terminos = [r["termino"] for r in resultado]
        assert "arduino" in terminos
        assert "led" in terminos

    def test_ngram_sensor_temperatura(self):
        resultado = extraer_componentes("sensor de temperatura")
        assert len(resultado) == 1
        assert resultado[0]["termino"] == "sensor de temperatura"

    def test_ngram_motor_paso_paso(self):
        resultado = extraer_componentes("motor paso a paso")
        assert len(resultado) == 1
        assert resultado[0]["termino"] == "motor paso a paso"

    def test_texto_conversacional(self):
        resultado = extraer_componentes(
            "buenas, necesito cotizar un arduino y un sensor de temperatura"
        )
        assert len(resultado) == 2
        terminos = [r["termino"] for r in resultado]
        assert "arduino" in terminos
        assert "sensor de temperatura" in terminos

    def test_texto_vacio(self):
        assert extraer_componentes("") == []

    def test_texto_sin_componentes(self):
        assert extraer_componentes("hola, como estas?") == []

    def test_cantidad_con_x(self):
        resultado = extraer_componentes("3x resistencias")
        assert len(resultado) == 1
        assert resultado[0]["cantidad"] == 3

    def test_no_filtra_stopwords_a_ciegas(self):
        """El filtro no debe eliminar 'de' en 'sensor de temperatura'."""
        resultado = extraer_componentes("sensor de temperatura")
        assert len(resultado) == 1
        assert "temperatura" in resultado[0]["termino"]

    def test_preserva_orden(self):
        resultado = extraer_componentes("motor y arduino")
        assert resultado[0]["termino"] == "motor"
        assert resultado[1]["termino"] == "arduino"

    def test_sin_tildes(self):
        resultado = extraer_componentes("5 resistencias")
        assert len(resultado) == 1
        assert resultado[0]["termino"] == "resistencia"
