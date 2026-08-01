"""Tests for the exporter (PDF/Excel generation)."""

import io
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

from app.services.cotizacion.exporter import generate_excel, generate_pdf


def _mock_cotizacion():
    items = [
        MagicMock(
            producto_nombre="Resistencia 220Ω 1/4W",
            cantidad=10,
            proveedor="AV Electronics",
            precio_unitario=Decimal("0.30"),
            margen_aplicado=Decimal("5.00"),
            subtotal=Decimal("3.15"),
            disponible=True,
        ),
        MagicMock(
            producto_nombre="LED Rojo 5mm",
            cantidad=5,
            proveedor="",
            precio_unitario=Decimal("0.00"),
            margen_aplicado=Decimal("0.00"),
            subtotal=Decimal("0.00"),
            disponible=False,
        ),
    ]
    cotizacion = MagicMock(
        id=1,
        items=items,
        total=Decimal("3.15"),
        estado="pendiente",
        fecha_creacion=datetime(2026, 8, 1, 12, 0, 0),
    )
    return cotizacion


class TestGeneratePDF:
    def test_pdf_es_bytes(self):
        pdf = generate_pdf(_mock_cotizacion())
        assert isinstance(pdf, bytes)
        assert len(pdf) > 0
        assert pdf[:4] == b"%PDF"

    def test_pdf_no_vacio(self):
        pdf = generate_pdf(_mock_cotizacion())
        assert len(pdf) > 100


class TestGenerateExcel:
    def test_excel_es_bytes(self):
        excel = generate_excel(_mock_cotizacion())
        assert isinstance(excel, bytes)
        assert len(excel) > 0

    def test_excel_es_zip(self):
        excel = generate_excel(_mock_cotizacion())
        # xlsx files are ZIP archives, start with PK
        assert excel[:2] == b"PK"
