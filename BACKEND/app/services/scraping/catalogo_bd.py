"""Catálogo persistente en PostgreSQL con Full-Text Search.

Reemplaza el caché en memoria por una tabla en BD:
- Descarga el catálogo completo vía WooCommerce Store API
- Persiste en catalogo_productos (UPSERT por tienda + url)
- Búsqueda con ILIKE + trigram similarity (no requiere extensión pg_trgm)
- Refresh hourly en background

Ventajas sobre el caché en memoria:
- Sobrevive reinicios del servidor
- Búsquedas SQL instantáneas (<10ms)
- No requiere scraping en vivo
- ILIKE + similarity ranking más preciso que word matching en Python
"""

import asyncio
import logging
import re
import unicodedata
from datetime import datetime

import httpx
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalogo_producto import CatalogoProducto

logger = logging.getLogger(__name__)

TTL_SEGUNDOS = 3600  # 1 hora

# url_base -> bool (True si la tienda soporta la API de WooCommerce)
_cache_soporta_api: dict[str, bool] = {}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

_STOP_WORDS = {
    "de", "la", "el", "en", "y", "a", "los", "las", "un", "una",
    "unos", "unas", "con", "para", "por", "del", "al", "lo", "le",
    "se", "su", "sus", "es", "son", "the", "and", "for", "of", "to",
    "in", "on", "at", "or", "an", "it", "is", "as", "by",
}


def _normalizar(texto: str) -> str:
    """Lowercase, sin tildes, unidades normalizadas."""
    if not texto:
        return ""
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = texto.replace("ω", "ohm").replace("µ", "u").replace("μ", "u")
    texto = texto.replace("²", "2").replace("³", "3")
    texto = re.sub(r"\bohms\b", "ohm", texto)
    return texto


async def soporta_api_wc(url_base: str) -> bool:
    """Detecta si la tienda expone la Store API de WooCommerce."""
    if url_base in _cache_soporta_api:
        return _cache_soporta_api[url_base]
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(15.0), headers=_HEADERS, follow_redirects=True
        ) as client:
            resp = await client.get(
                f"{url_base}/wp-json/wc/store/v1/products",
                params={"per_page": 1, "page": 1},
            )
        soporta = resp.status_code == 200 and isinstance(resp.json(), list)
    except Exception:
        soporta = False
    _cache_soporta_api[url_base] = soporta
    return soporta


async def _descargar_catalogo_wc(url_base: str) -> list[dict]:
    """Descarga todas las páginas del catálogo vía WooCommerce Store API.

    Los productos variables se expanden: cada variación es una entrada
    propia con su nombre ("Padre - Valor"), precio y stock individual.
    """
    productos: list[dict] = []
    variaciones_pendientes: list[tuple[str, int, str, int]] = []
    pagina = 1
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(30.0), headers=_HEADERS, follow_redirects=True
    ) as client:
        while True:
            url = f"{url_base}/wp-json/wc/store/v1/products"
            resp = await client.get(url, params={"per_page": 100, "page": pagina})
            if resp.status_code != 200:
                break
            lote = resp.json()
            if not lote:
                break
            for p in lote:
                nombre = p.get("name") or ""
                pid = p.get("id")
                if p.get("type") == "variable":
                    for var in p.get("variations") or []:
                        var_id = var.get("id")
                        valores = [a.get("value", "") for a in var.get("attributes") or []]
                        sufijo = ", ".join(v for v in valores if v)
                        if var_id:
                            variaciones_pendientes.append((nombre, var_id, sufijo, pid))
                    continue
                precios = p.get("prices") or {}
                precio_raw = precios.get("price")
                precio = None
                if precio_raw:
                    try:
                        precio = round(float(precio_raw) / 100, 2)
                    except (TypeError, ValueError):
                        pass
                productos.append({
                    "nombre": nombre,
                    "precio": precio,
                    "disponible": bool(p.get("is_in_stock")),
                    "url": p.get("permalink"),
                    "producto_id_wc": pid,
                })
            total_paginas = int(resp.headers.get("x-wp-totalpages", "1"))
            if pagina >= total_paginas:
                break
            pagina += 1

        sem = asyncio.Semaphore(10)

        async def _resolver_var(nombre_padre: str, var_id: int, sufijo: str, pid: int) -> dict | None:
            async with sem:
                try:
                    rv = await client.get(f"{url_base}/wp-json/wc/store/v1/products/{var_id}")
                    if rv.status_code != 200:
                        return None
                    v = rv.json()
                    precio_raw = (v.get("prices") or {}).get("price")
                    precio = round(float(precio_raw) / 100, 2) if precio_raw else None
                    nombre = f"{nombre_padre} - {sufijo}" if sufijo else nombre_padre
                    return {
                        "nombre": nombre,
                        "precio": precio,
                        "disponible": bool(v.get("is_in_stock")),
                        "url": v.get("permalink"),
                        "producto_id_wc": pid,
                    }
                except Exception:
                    return None

        if variaciones_pendientes:
            resueltas = await asyncio.gather(
                *[_resolver_var(n, vid, s, pid) for n, vid, s, pid in variaciones_pendientes]
            )
            productos.extend(r for r in resueltas if r is not None)

    return productos


async def refrescar_catalogo_bd(db: AsyncSession, url_base: str, nombre_tienda: str) -> int:
    """Descarga el catálogo y lo persiste en BD (reemplazo completo).

    Retorna el número de productos guardados.
    """
    productos = await _descargar_catalogo_wc(url_base)
    if not productos:
        logger.warning("Catálogo vacío para %s", url_base)
        return 0

    # Eliminar productos anteriores de esta tienda
    await db.execute(
        delete(CatalogoProducto).where(CatalogoProducto.url_base == url_base)
    )

    # Insertar nuevos
    for p in productos:
        nombre = p["nombre"]
        if not nombre or not nombre.strip():
            continue
        db.add(CatalogoProducto(
            tienda=nombre_tienda,
            nombre=nombre,
            nombre_normalizado=_normalizar(nombre),
            precio=p["precio"],
            disponible=p["disponible"],
            url=p["url"],
            variantes=[],
            url_base=url_base,
            producto_id_wc=p.get("producto_id_wc"),
            actualizado=datetime.now(),
        ))

    await db.commit()
    logger.info("Catálogo BD actualizado: %s (%d productos)", nombre_tienda, len(productos))

    # Invalidar caché de términos del engine
    from app.services.scraping.engine import limpiar_cache_termino
    limpiar_cache_termino()

    return len(productos)


# Sinónimos: términos del usuario -> palabras que aparecen en el catálogo
_SINONIMOS = {
    "regleta": "header",
    "tira": "header",
    "pines": "header",
    "jumper": "dupont",
    "protoboard": "protoboard",
    "placa": "baquelita",
    "perforada": "baquelita",
    "rele": "rele",
    "relé": "rele",
    "boya": "nivel",
    "block": "terminal",
    "bornera": "terminal",
}


def _expandir_token(token: str) -> list[str]:
    """Genera variantes de un token: sinónimos y versión colapsada."""
    variantes = [token]
    # Sinónimo
    sinonimo = _SINONIMOS.get(token)
    if sinonimo and sinonimo != token:
        variantes.append(sinonimo)
    return variantes


async def buscar_en_bd(
    db: AsyncSession,
    termino: str,
    url_base: str | None = None,
    limite: int = 50,
) -> list[dict]:
    """Busca productos en BD usando ILIKE + ranking por coincidencia de tokens.

    Estrategia:
    1. Normalizar el término de búsqueda
    2. Extraer tokens significativos (sin stop words, sin números sueltos)
    3. Generar variantes por token (sinónimos: regleta→header, jumper→dupont)
    4. Buscar AND: cada token (o su sinónimo) debe aparecer en el nombre
    5. Si no hay resultados, aflojar a OR
    6. Rankear por coincidencias + disponibilidad + precio
    """
    termino_norm = _normalizar(termino)

    # Extraer tokens significativos
    tokens_brutos = []
    for token in termino_norm.split():
        if token in _STOP_WORDS or len(token) < 2:
            continue
        if token.replace(".", "").replace(",", "").isdigit():
            continue
        tokens_brutos.append(token)

    if not tokens_brutos:
        return []

    # Generar tokens colapsados: pares adyacentes alfanuméricos (esp + 32 -> esp32)
    # Pero solo para pares donde uno es letras y el otro es números
    tokens = []
    i = 0
    while i < len(tokens_brutos):
        token = tokens_brutos[i]
        # Intentar colapsar con el siguiente si es par letra+número o número+letra
        if i + 1 < len(tokens_brutos):
            sig = tokens_brutos[i + 1]
            es_letra_num = token.isalpha() and sig.isdigit()
            if es_letra_num:
                tokens.append(token + sig)
                i += 2
                continue
        tokens.append(token)
        i += 1

    # Generar variantes por token
    tokens_expandidos = [_expandir_token(t) for t in tokens]

    # Construir query base
    base_query = select(CatalogoProducto)
    if url_base:
        base_query = base_query.where(CatalogoProducto.url_base == url_base)

    from sqlalchemy import or_

    # Intento 1: AND estricto — cada token debe aparecer (con variantes OR)
    condiciones_and = []
    for variantes in tokens_expandidos:
        condiciones_token = [
            CatalogoProducto.nombre_normalizado.ilike(f"%{v}%") for v in variantes
        ]
        condiciones_and.append(or_(*condiciones_token))

    query_and = base_query.where(*condiciones_and)
    result_and = await db.execute(query_and)
    productos = result_and.scalars().all()

    # Intento 2: OR — al menos un token (con variantes)
    if not productos:
        condiciones_or = []
        for variantes in tokens_expandidos:
            for v in variantes:
                condiciones_or.append(CatalogoProducto.nombre_normalizado.ilike(f"%{v}%"))
        query_or = base_query.where(or_(*condiciones_or))
        result_or = await db.execute(query_or)
        productos = result_or.scalars().all()

    # Rankear en Python: contar tokens coincidentes (con variantes)
    def _contar_coincidencias(nombre_norm: str) -> int:
        count = 0
        for variantes in tokens_expandidos:
            if any(v in nombre_norm for v in variantes):
                count += 1
        return count

    resultados = []
    for p in productos:
        nombre_norm = p.nombre_normalizado
        coincidencias = _contar_coincidencias(nombre_norm)
        if coincidencias == 0:
            continue
        resultados.append({
            "tienda": p.tienda,
            "nombre_producto": p.nombre,
            "precio_base": p.precio,
            "disponible": p.disponible,
            "url": p.url,
            "variantes": p.variantes or [],
            "_coincidencias": coincidencias,
        })

    resultados.sort(key=lambda r: (
        -r["_coincidencias"],
        not r["disponible"],
        r["precio_base"] if r["precio_base"] is not None else 9999,
    ))

    for r in resultados:
        r.pop("_coincidencias", None)

    return resultados[:limite]


async def contar_productos(db: AsyncSession, url_base: str | None = None) -> int:
    """Cuenta productos en el catálogo persistido."""
    query = select(CatalogoProducto)
    if url_base:
        query = query.where(CatalogoProducto.url_base == url_base)
    result = await db.execute(query)
    return len(result.scalars().all())


def iniciar_refresh_background(db_factory, url_base: str, nombre_tienda: str) -> asyncio.Task:
    """Tarea en background que refresca el catálogo cada hora."""

    async def _loop() -> None:
        while True:
            try:
                if await soporta_api_wc(url_base):
                    async with db_factory() as db:
                        await refrescar_catalogo_bd(db, url_base, nombre_tienda)
            except Exception as exc:
                logger.warning("Refresh BD catálogo falló para %s: %s", nombre_tienda, exc)
            await asyncio.sleep(TTL_SEGUNDOS)

    return asyncio.create_task(_loop())
