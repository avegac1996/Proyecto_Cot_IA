"""Caché de catálogo completo de tiendas WooCommerce.

En vez de scrapear la página de búsqueda por cada término (lento),
descarga el catálogo completo vía /wp-json/wc/store/v1/products y lo
mantiene en memoria por 1 hora. Las búsquedas se hacen localmente
sobre el catálogo cacheado (instantáneas).

Si la tienda no soporta la API de WooCommerce, se cae al scraping HTML.
"""

import asyncio
import logging
import re
import time
import unicodedata

import httpx

from app.services.ingesta.filtro import _STOP_WORDS

logger = logging.getLogger(__name__)

TTL_SEGUNDOS = 3600  # 1 hora

# url_base -> {"productos": [...], "timestamp": float}
_cache_catalogo: dict[str, dict] = {}

# url_base -> bool (True si la tienda soporta la API de WooCommerce)
_cache_soporta_api: dict[str, bool] = {}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _normalizar(texto: str) -> str:
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = texto.replace("ω", "ohm").replace("µ", "u").replace("μ", "u")
    texto = re.sub(r"\bohms\b", "ohm", texto)
    return texto


def _palabra_en_texto(palabra: str, texto: str) -> bool:
    patron = r"(?<![a-z])" + re.escape(palabra) + r"(?![a-z])"
    return bool(re.search(patron, texto))


_PATRON_VALOR = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(k|m)?\s*(ohm|uf|nf|pf|v|ma|a|w)\b"
)

_CLASES_UNIDAD = {
    "ohm": "R", "uf": "C", "nf": "C", "pf": "C",
    "v": "V", "a": "I", "ma": "I", "w": "W",
}


def _extraer_valores(texto: str) -> set[tuple[str, float]]:
    valores: set[tuple[str, float]] = set()
    for m in _PATRON_VALOR.finditer(texto):
        num = float(m.group(1).replace(",", "."))
        mult = m.group(2)
        unidad = m.group(3)
        clase = _CLASES_UNIDAD.get(unidad)
        if clase is None:
            continue
        if clase == "R":
            if mult == "k":
                num *= 1_000
            elif mult == "m":
                num *= 1_000_000
        elif clase == "C":
            if unidad == "nf":
                num /= 1_000
            elif unidad == "pf":
                num /= 1_000_000
        elif clase == "I":
            if unidad == "ma":
                num /= 1_000
        valores.add((clase, round(num, 6)))
    return valores


async def _descargar_catalogo(url_base: str) -> list[dict]:
    """Descarga todas las páginas del catálogo vía WooCommerce Store API.

    Los productos variables se expanden: cada variación es una entrada
    propia con su nombre ("Padre - Valor"), precio y stock individual.
    """
    productos: list[dict] = []
    variaciones_pendientes: list[tuple[str, int, str]] = []  # (nombre_padre, var_id, sufijo)
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
                if p.get("type") == "variable":
                    # Expandir variaciones: nombre desde atributos del padre,
                    # precio/stock se obtienen por fetch individual
                    for var in p.get("variations") or []:
                        var_id = var.get("id")
                        valores = [a.get("value", "") for a in var.get("attributes") or []]
                        sufijo = ", ".join(v for v in valores if v)
                        if var_id:
                            variaciones_pendientes.append((nombre, var_id, sufijo))
                    continue
                precios = p.get("prices") or {}
                precio_raw = precios.get("price")
                precio_base = None
                if precio_raw:
                    try:
                        # Store API devuelve precios en unidades menores (centavos)
                        precio_base = round(float(precio_raw) / 100, 2)
                    except (TypeError, ValueError):
                        precio_base = None
                productos.append({
                    "nombre_producto": nombre,
                    "precio_base": precio_base,
                    "disponible": bool(p.get("is_in_stock")),
                    "url": p.get("permalink"),
                })
            total_paginas = int(resp.headers.get("x-wp-totalpages", "1"))
            if pagina >= total_paginas:
                break
            pagina += 1

        # Resolver variaciones en paralelo (precio y stock individuales)
        sem = asyncio.Semaphore(10)

        async def _resolver_variacion(nombre_padre: str, var_id: int, sufijo: str) -> dict | None:
            async with sem:
                try:
                    rv = await client.get(f"{url_base}/wp-json/wc/store/v1/products/{var_id}")
                    if rv.status_code != 200:
                        return None
                    v = rv.json()
                    precio_raw = (v.get("prices") or {}).get("price")
                    precio_base = round(float(precio_raw) / 100, 2) if precio_raw else None
                    nombre = f"{nombre_padre} - {sufijo}" if sufijo else nombre_padre
                    return {
                        "nombre_producto": nombre,
                        "precio_base": precio_base,
                        "disponible": bool(v.get("is_in_stock")),
                        "url": v.get("permalink"),
                    }
                except Exception:
                    return None

        if variaciones_pendientes:
            resueltas = await asyncio.gather(
                *[_resolver_variacion(n, vid, s) for n, vid, s in variaciones_pendientes]
            )
            productos.extend(r for r in resueltas if r is not None)

    return productos


async def soporta_api_wc(url_base: str) -> bool:
    """Detecta (y cachea) si la tienda expone la Store API de WooCommerce."""
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


async def refrescar_catalogo(url_base: str) -> None:
    """Descarga el catálogo y actualiza el caché."""
    productos = await _descargar_catalogo(url_base)
    if productos:
        _cache_catalogo[url_base] = {"productos": productos, "timestamp": time.time()}
        logger.info("Catálogo cacheado: %s (%d productos)", url_base, len(productos))
        # Invalidar caché de términos para que búsquedas usen el catálogo actualizado
        from app.services.scraping.engine import limpiar_cache_termino
        limpiar_cache_termino()


async def obtener_catalogo(url_base: str, forzar: bool = False) -> list[dict]:
    """Devuelve el catálogo cacheado SIN bloquear.

    Si no hay caché todavía, devuelve [] para que el scraper caiga al
    scraping HTML. El refresh lo hace la tarea en background cada hora.
    """
    entrada = _cache_catalogo.get(url_base)
    if entrada:
        return entrada["productos"]
    if forzar:
        await refrescar_catalogo(url_base)
        entrada = _cache_catalogo.get(url_base)
        return entrada["productos"] if entrada else []
    return []


def iniciar_refresh_background(url_base: str) -> asyncio.Task:
    """Tarea en background que refresca el catálogo cada hora.

    Así las búsquedas nunca pagan el costo de descarga: siempre leen
    el caché, y el scraping HTML sirve de fallback hasta el primer build.
    """
    async def _loop() -> None:
        while True:
            try:
                if await soporta_api_wc(url_base):
                    await refrescar_catalogo(url_base)
            except Exception as exc:
                logger.warning("Refresh de catálogo falló para %s: %s", url_base, exc)
            await asyncio.sleep(TTL_SEGUNDOS)

    return asyncio.create_task(_loop())


def buscar_en_catalogo(productos: list[dict], termino: str) -> list[dict]:
    """Busca productos del catálogo que coincidan con el término.

    Criterio generoso (similar a la búsqueda fuzzy de WooCommerce):
    - Producto coincide si al menos un token significativo del término
      aparece como palabra completa en el nombre, o si coincide un valor
      con unidad (470uF, 4.7kohm, 5v).
    - Orden: más tokens coincidentes primero, luego precio ascendente.
    El ranking fino lo hace _filtrar_y_ordenar_por_relevancia aguas abajo.
    """
    termino_norm = _normalizar(termino)
    valores_termino = _extraer_valores(termino_norm)

    tokens_texto: list[str] = []
    for token in termino_norm.split():
        if token in _STOP_WORDS or len(token) < 2:
            continue
        if _PATRON_VALOR.fullmatch(token):
            continue  # los valores se comparan numéricamente
        if token.replace(".", "").isdigit():
            continue  # números sueltos (cantidades) no filtran
        tokens_texto.append(token)

    resultados: list[dict] = []
    for p in productos:
        nombre = p["nombre_producto"]
        if not nombre:
            continue
        nombre_norm = _normalizar(nombre)
        coincidencias = 0
        for token in tokens_texto:
            candidatos = [token]
            if not token.endswith("s"):
                candidatos.append(token + "s")
            elif len(token) > 3:
                candidatos.append(token[:-1])
            if any(_palabra_en_texto(c, nombre_norm) for c in candidatos):
                coincidencias += 1
        if valores_termino and valores_termino & _extraer_valores(nombre_norm):
            coincidencias += 2
        if coincidencias == 0:
            continue
        resultados.append({
            "nombre_producto": nombre,
            "precio": p["precio_base"],
            "disponible": p["disponible"],
            "url": p["url"],
            "variantes": [],
            "_coincidencias": coincidencias,
        })

    resultados.sort(key=lambda r: (
        -r["_coincidencias"],
        not r["disponible"],
        r["precio"] if r["precio"] is not None else 9999,
    ))
    for r in resultados:
        r.pop("_coincidencias", None)
    return resultados[:50]


def invalidar_cache() -> None:
    """Limpia el caché de catálogos (para tests o refresh manual)."""
    _cache_catalogo.clear()
    _cache_soporta_api.clear()
