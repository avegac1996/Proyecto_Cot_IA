"""Tests del servicio de configuración de negocio."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.configuracion import obtener_margen, actualizar_margen, obtener_tienda_propia


class TestConfiguracion:
    @pytest.mark.asyncio
    async def test_obtener_margen_desde_bd(self):
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.valor = "15.0"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config
        mock_db.execute.return_value = mock_result

        margen = await obtener_margen(mock_db)
        assert margen == 15.0

    @pytest.mark.asyncio
    async def test_obtener_margen_fallback_settings(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        margen = await obtener_margen(mock_db)
        assert margen == 5.0  # settings.MARGEN_COMPETENCIA default

    @pytest.mark.asyncio
    async def test_obtener_margen_valor_invalido_fallback(self):
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.valor = "invalid"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config
        mock_db.execute.return_value = mock_result

        margen = await obtener_margen(mock_db)
        assert margen == 5.0  # fallback

    @pytest.mark.asyncio
    async def test_actualizar_margen_crear_nuevo(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        resultado = await actualizar_margen(mock_db, 10.0)
        assert resultado == 10.0
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_actualizar_margen_existente(self):
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.valor = "5.0"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config
        mock_db.execute.return_value = mock_result

        resultado = await actualizar_margen(mock_db, 20.0)
        assert resultado == 20.0
        assert mock_config.valor == "20.0"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_obtener_tienda_propia_desde_bd(self):
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.valor = "Mi Tienda"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config
        mock_db.execute.return_value = mock_result

        tienda = await obtener_tienda_propia(mock_db)
        assert tienda == "Mi Tienda"

    @pytest.mark.asyncio
    async def test_obtener_tienda_propia_fallback(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        tienda = await obtener_tienda_propia(mock_db)
        assert tienda == "AV Electronics"
