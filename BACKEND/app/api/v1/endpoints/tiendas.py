"""CRUD de tiendas + test de scraping con detección de captcha."""

import asyncio
import logging

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.tienda import Tienda
from app.models.usuario import Usuario

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tiendas", tags=["tiendas"])

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}

CAPTCHA_INDICATORS = [
    "robot challenge", "sgcaptcha", "captcha", "cloudflare",
    "are you human", "verify you are human", "checking your browser",
    "ddos protection", "access denied", "blocked",
]


class SelectorSchema(BaseModel):
    search_url: str | None = None
    product_card: str | None = None
    product_url: str | None = None
    price: str | None = None
    stock_in_classes: bool = False
    product_page_price: str | None = None
    product_page_availability: str | None = None
    store_path: str | None = None
    use_wayback: bool = False


class TiendaCreate(BaseModel):
    nombre: str
    url_base: str
    usa_javascript: bool = False
    activa: bool = True
    ttl_horas: int = 24
    selectores: SelectorSchema = SelectorSchema()


class TiendaUpdate(BaseModel):
    nombre: str | None = None
    url_base: str | None = None
    usa_javascript: bool | None = None
    activa: bool | None = None
    ttl_horas: int | None = None
    selectores: SelectorSchema | None = None


class TiendaResponse(BaseModel):
    id: int
    nombre: str
    url_base: str
    usa_javascript: bool
    activa: bool
    ttl_horas: int
    selectores: dict


class TestScrapingRequest(BaseModel):
    url_base: str
    usa_javascript: bool = False
    selectores: SelectorSchema = SelectorSchema()
    query: str = "arduino"


class TestScrapingResponse(BaseModel):
    status: str  # "ok", "captcha", "error"
    captcha: bool
    captcha_type: str | None = None
    message: str
    products_found: int = 0
    sample_products: list[dict] = []
    http_status: int | None = None
    response_length: int | None = None
    recommended_scraper: str | None = None


@router.get("", response_model=list[TiendaResponse])
async def listar_tiendas(
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_admin),
):
    result = await db.execute(select(Tienda).order_by(Tienda.id))
    return result.scalars().all()


@router.post("", response_model=TiendaResponse, status_code=status.HTTP_201_CREATED)
async def crear_tienda(
    body: TiendaCreate,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_admin),
):
    existing = await db.execute(select(Tienda).where(Tienda.nombre == body.nombre))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail={"code": "DUPLICATE", "message": "Ya existe una tienda con ese nombre"})

    tienda = Tienda(
        nombre=body.nombre,
        url_base=body.url_base,
        usa_javascript=body.usa_javascript,
        activa=body.activa,
        ttl_horas=body.ttl_horas,
        selectores=body.selectores.model_dump(),
    )
    db.add(tienda)
    await db.commit()
    await db.refresh(tienda)
    return tienda


@router.put("/{tienda_id}", response_model=TiendaResponse)
async def actualizar_tienda(
    tienda_id: int,
    body: TiendaUpdate,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_admin),
):
    result = await db.execute(select(Tienda).where(Tienda.id == tienda_id))
    tienda = result.scalar_one_or_none()
    if not tienda:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Tienda no encontrada"})

    if body.nombre is not None:
        tienda.nombre = body.nombre
    if body.url_base is not None:
        tienda.url_base = body.url_base
    if body.usa_javascript is not None:
        tienda.usa_javascript = body.usa_javascript
    if body.activa is not None:
        tienda.activa = body.activa
    if body.ttl_horas is not None:
        tienda.ttl_horas = body.ttl_horas
    if body.selectores is not None:
        tienda.selectores = body.selectores.model_dump()

    await db.commit()
    await db.refresh(tienda)
    return tienda


@router.delete("/{tienda_id}")
async def eliminar_tienda(
    tienda_id: int,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_admin),
):
    result = await db.execute(select(Tienda).where(Tienda.id == tienda_id))
    tienda = result.scalar_one_or_none()
    if not tienda:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Tienda no encontrada"})

    await db.delete(tienda)
    await db.commit()
    return {"message": "Tienda eliminada"}


@router.post("/test-scraping", response_model=TestScrapingResponse)
async def test_scraping(
    body: TestScrapingRequest,
    user: Usuario = Depends(require_admin),
):
    """Prueba el scraping de una tienda y detecta captcha o errores.

    Retorna:
    - status="ok" (verde): scraping funciona, encontró productos
    - status="captcha" (verde): detectó captcha, recomienda usar Wayback
    - status="captcha_error" (rojo): no detectó captcha pero la página es diferente/error
    - status="error" (rojo): error genérico
    """
    selectores = body.selectores.model_dump()
    search_url = selectores.get("search_url", "")
    if search_url and "{query}" in search_url:
        test_url = search_url.replace("{query}", body.query)
    else:
        test_url = f"{body.url_base.rstrip('/')}/?s={body.query}"

    # Si use_wayback está activo, probar Wayback
    if selectores.get("use_wayback", False):
        return await _test_wayback(body.url_base, selectores, body.query)

    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True) as client:
            r = await client.get(test_url)

            # Detectar captcha por status 202 o contenido
            content = r.text.lower()
            is_captcha = (
                r.status_code == 202
                or any(ind in content for ind in CAPTCHA_INDICATORS)
                or len(r.text) < 500
            )

            if is_captcha:
                captcha_type = _detect_captcha_type(content, r.status_code)
                return TestScrapingResponse(
                    status="captcha",
                    captcha=True,
                    captcha_type=captcha_type,
                    message=f"⚠️ CAPTCHA detectado ({captcha_type}). Se recomienda activar Wayback Machine.",
                    http_status=r.status_code,
                    response_length=len(r.text),
                    recommended_scraper="wayback",
                )

            # No es captcha, pero verificar si encontró productos
            soup = BeautifulSoup(r.text, "html.parser")
            card_sel = selectores.get("product_card", "li.product")
            cards = soup.select(card_sel)

            if not cards:
                # No encontró productos pero no es captcha — la página es diferente
                return TestScrapingResponse(
                    status="captcha_error",
                    captcha=True,
                    captcha_type="página_diferente",
                    message="🔴 No se detectó captcha pero la página no contiene productos con los selectores configurados. Posible bloqueo silencioso o selectores incorrectos.",
                    http_status=r.status_code,
                    response_length=len(r.text),
                    recommended_scraper="wayback",
                )

            # Encontró productos — extraer muestra
            link_sel = selectores.get("product_url", "h2 a, h2")
            price_sel = selectores.get("price", ".woocommerce-Price-amount, .price")
            sample = []
            for card in cards[:5]:
                name_el = None
                for sel in link_sel.split(","):
                    sel = sel.strip()
                    if sel:
                        name_el = card.select_one(sel)
                        if name_el:
                            break
                if not name_el:
                    name_el = card.select_one("h2")
                nombre = name_el.get_text(strip=True) if name_el else "sin nombre"

                precio = None
                for sel in price_sel.split(","):
                    sel = sel.strip()
                    if sel:
                        price_el = card.select_one(sel)
                        if price_el:
                            import re
                            raw = price_el.get_text(strip=True)
                            cleaned = re.sub(r"[^\d.,]", "", raw)
                            if cleaned:
                                try:
                                    precio = float(cleaned.replace(",", "."))
                                except ValueError:
                                    pass
                            if precio is not None:
                                break

                sample.append({"nombre": nombre, "precio": precio})

            scraper_type = "dynamic" if body.usa_javascript else "static"
            return TestScrapingResponse(
                status="ok",
                captcha=False,
                message=f"✅ Scraping exitoso. Se encontraron {len(cards)} productos.",
                products_found=len(cards),
                sample_products=sample,
                http_status=r.status_code,
                response_length=len(r.text),
                recommended_scraper=scraper_type,
            )

    except httpx.TimeoutException:
        return TestScrapingResponse(
            status="error",
            captcha=False,
            message="🔴 Timeout: la tienda no respondió en 20 segundos. Puede estar bloqueando la conexión.",
            recommended_scraper="wayback",
        )
    except Exception as exc:
        return TestScrapingResponse(
            status="error",
            captcha=False,
            message=f"🔴 Error: {str(exc)}",
        )


def _detect_captcha_type(content: str, status_code: int) -> str:
    """Identifica el tipo de captcha/protección."""
    if "sgcaptcha" in content or "siteguard" in content:
        return "SiteGuard"
    if "cloudflare" in content:
        return "Cloudflare"
    if "are you human" in content or "verify you are human" in content:
        return "Captcha genérico"
    if "checking your browser" in content:
        return "JavaScript Challenge"
    if status_code == 202:
        return "Bloqueo silencioso (202)"
    if len(content) < 500:
        return "Página vacía/bloqueada"
    return "Desconocido"


async def _test_wayback(url_base: str, selectores: dict, query: str) -> TestScrapingResponse:
    """Prueba si Wayback Machine tiene snapshots de la tienda."""
    store_path = selectores.get("store_path", "/store/")
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=30, follow_redirects=True) as client:
            r = await client.get(
                f"https://archive.org/wayback/available?url={url_base}{store_path}"
            )
            data = r.json()
            closest = data.get("archived_snapshots", {}).get("closest", {})
            if closest.get("available"):
                timestamp = closest.get("timestamp", "")
                snapshot_url = closest.get("url", "")
                # Verificar que el snapshot tenga productos
                r2 = await client.get(snapshot_url)
                if r2.status_code == 200:
                    soup = BeautifulSoup(r2.text, "html.parser")
                    card_sel = selectores.get("product_card", "li.product")
                    cards = soup.select(card_sel)
                    return TestScrapingResponse(
                        status="ok",
                        captcha=False,
                        message=f"✅ Wayback Machine: snapshot de {timestamp[:8]} con {len(cards)} productos.",
                        products_found=len(cards),
                        http_status=r2.status_code,
                        response_length=len(r2.text),
                        recommended_scraper="wayback",
                    )
            return TestScrapingResponse(
                status="error",
                captcha=False,
                message="🔴 Wayback Machine no tiene snapshots de esta tienda.",
            )
    except Exception as exc:
        return TestScrapingResponse(
            status="error",
            captcha=False,
            message=f"🔴 Error con Wayback: {str(exc)}",
        )
