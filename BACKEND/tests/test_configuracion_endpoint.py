"""Tests del endpoint de configuración."""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


class TestConfiguracionEndpoint:
    @pytest.mark.asyncio
    async def test_get_configuracion_sin_token(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/configuracion")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_put_margen_sin_token(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                "/api/v1/configuracion/margen",
                json={"margen": 10.0},
            )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_put_margen_usuario_no_admin(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Login como user normal
            login_resp = await client.post(
                "/api/v1/auth/login",
                data={"username": "user", "password": "User123!"},
            )
            assert login_resp.status_code == 200
            token = login_resp.json()["access_token"]

            response = await client.put(
                "/api/v1/configuracion/margen",
                json={"margen": 10.0},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_put_margen_admin_valido(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Login como admin
            login_resp = await client.post(
                "/api/v1/auth/login",
                data={"username": "admin", "password": "Admin123!"},
            )
            assert login_resp.status_code == 200
            token = login_resp.json()["access_token"]

            response = await client.put(
                "/api/v1/configuracion/margen",
                json={"margen": 12.5},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["margen_competencia"] == 12.5

    @pytest.mark.asyncio
    async def test_put_margen_invalido_negativo(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            login_resp = await client.post(
                "/api/v1/auth/login",
                data={"username": "admin", "password": "Admin123!"},
            )
            token = login_resp.json()["access_token"]

            response = await client.put(
                "/api/v1/configuracion/margen",
                json={"margen": -5.0},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_put_margen_invalido_mayor_100(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            login_resp = await client.post(
                "/api/v1/auth/login",
                data={"username": "admin", "password": "Admin123!"},
            )
            token = login_resp.json()["access_token"]

            response = await client.put(
                "/api/v1/configuracion/margen",
                json={"margen": 150.0},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 400
