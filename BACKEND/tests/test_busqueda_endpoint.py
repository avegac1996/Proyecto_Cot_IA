"""Tests del endpoint de búsqueda conversacional."""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


class TestBusquedaEndpoint:
    @pytest.mark.asyncio
    async def test_buscar_sin_token(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/buscar",
                json={"texto": "arduino"},
            )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_buscar_con_token(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            login_resp = await client.post(
                "/api/v1/auth/login",
                data={"username": "user", "password": "User123!"},
            )
            token = login_resp.json()["access_token"]

            response = await client.post(
                "/api/v1/buscar",
                json={"texto": "1 arduino"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 200
        data = response.json()
        assert "resultados" in data
        assert isinstance(data["resultados"], list)

    @pytest.mark.asyncio
    async def test_buscar_texto_vacio(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            login_resp = await client.post(
                "/api/v1/auth/login",
                data={"username": "user", "password": "User123!"},
            )
            token = login_resp.json()["access_token"]

            response = await client.post(
                "/api/v1/buscar",
                json={"texto": ""},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["resultados"] == []

    @pytest.mark.asyncio
    async def test_buscar_multiples_componentes(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            login_resp = await client.post(
                "/api/v1/auth/login",
                data={"username": "user", "password": "User123!"},
            )
            token = login_resp.json()["access_token"]

            response = await client.post(
                "/api/v1/buscar",
                json={"texto": "1 arduino y 5 resistencias"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 200
        data = response.json()
        assert len(data["resultados"]) == 2
        terminos = [r["termino"] for r in data["resultados"]]
        assert "arduino" in terminos
        assert "resistencia" in terminos
