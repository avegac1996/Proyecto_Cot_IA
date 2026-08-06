"""Regresiones de autorización para recursos de cotización."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.cotizacion import _get_cotizacion_by_id


def _db_returning(cotizacion):
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = cotizacion
    db.execute.return_value = result
    return db


@pytest.mark.asyncio
async def test_usuario_no_puede_obtener_cotizacion_ajena():
    cotizacion = SimpleNamespace(usuario_id=2)
    user = SimpleNamespace(id=1, rol="user")

    with pytest.raises(HTTPException) as exc_info:
        await _get_cotizacion_by_id(10, user, _db_returning(cotizacion))

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_admin_puede_obtener_cotizacion_de_otro_usuario():
    cotizacion = SimpleNamespace(usuario_id=2)
    admin = SimpleNamespace(id=1, rol="admin")

    result = await _get_cotizacion_by_id(10, admin, _db_returning(cotizacion))

    assert result is cotizacion
