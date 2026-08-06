"""Búsqueda priorizada: AV Electronics primero, luego tiendas externas con margen."""

import logging
import re
import unicodedata

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.configuracion import obtener_margen, obtener_tienda_propia
from app.services.scraping.engine import buscar_por_termino

logger = logging.getLogger(__name__)


def _normalizar_texto(texto: str) -> str:
    """Lowercase, sin tildes, con unidades normalizadas."""
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    # Normalizar unidades de resistencia: ω/ohm/ohms → ohm
    texto = texto.replace("ω", "ohm")
    texto = re.sub(r'\bohms\b', 'ohm', texto)
    # Normalizar errores ortográficos comunes
    texto = re.sub(r'\bamarrillo\b', 'amarillo', texto)
    return texto


def _palabra_en_texto(palabra: str, texto: str) -> bool:
    """Verifica si palabra aparece como palabra completa en texto (no substring)."""
    patron = r'(?<![a-z])' + re.escape(palabra) + r'(?![a-z])'
    return bool(re.search(patron, texto))


def _score_relevancia(nombre_producto: str, descriptores: list[str]) -> int:
    """Puntúa qué tan relevante es un producto según los descriptores.

    Mayor score = más relevante. 0 = no contiene ningún descriptor.
    Usa matching de palabra completa para evitar falsos positivos (ej: 'rojo' en 'infrarrojo').
    Si el descriptor contiene un número, el producto debe contener ese número para puntuar.
    """
    nombre_norm = _normalizar_texto(nombre_producto)
    score = 0
    for desc in descriptores:
        desc_norm = _normalizar_texto(desc)
        # Coincidencia exacta del descriptor completo
        if _palabra_en_texto(desc_norm, nombre_norm):
            score += 10
            continue
        # Coincidencia por partes: separar números de palabras
        partes = desc_norm.split()
        partes_numericas = [p for p in partes if p.replace(".", "").replace(",", "").isdigit()]
        partes_texto = [p for p in partes if p not in partes_numericas]
        # Si hay parte numérica, debe coincidir para puntuar
        numero_match = all(_palabra_en_texto(p, nombre_norm) for p in partes_numericas) if partes_numericas else True
        if not numero_match:
            continue
        # Bonus por palabras de texto que coinciden
        for parte in partes_texto:
            if len(parte) >= 3 and _palabra_en_texto(parte, nombre_norm):
                score += 3
        # Bonus por números que coinciden
        for parte in partes_numericas:
            if _palabra_en_texto(parte, nombre_norm):
                score += 5
    return score


def _filtrar_y_ordenar_por_relevancia(
    opciones: list[dict], descriptores: list[str], termino_base: str | None = None
) -> list[dict]:
    """Filtra opciones por relevancia con los descriptores y término base.

    1. Si hay productos que coinciden con los descriptores, muestra SOLO esos.
    2. Si ninguno coincide con descriptores, filtra por término base en el nombre.
    3. Si tampoco hay coincidencias con término base, devuelve todos.
    """
    if not descriptores and not termino_base:
        return opciones

    base_norm = _normalizar_texto(termino_base) if termino_base else ""
    # También verificar plural del término base (ej: "led" → "leds")
    base_plural = base_norm + "s" if base_norm and not base_norm.endswith("s") else ""
    # Sin espacios (ej: "porta pila" → "portapila")
    base_sin_espacios = base_norm.replace(" ", "") if base_norm else ""

    con_descriptor = []
    con_base = []
    sin_match = []
    for op in opciones:
        nombre = op.get("nombre_producto", "")
        nombre_norm = _normalizar_texto(nombre)
        score = _score_relevancia(nombre, descriptores) if descriptores else 0
        if score > 0:
            op["_relevancia"] = score
            con_descriptor.append(op)
        elif base_norm and (
            _palabra_en_texto(base_norm, nombre_norm)
            or (base_plural and _palabra_en_texto(base_plural, nombre_norm))
            or (base_sin_espacios and base_sin_espacios in nombre_norm.replace(" ", ""))
        ):
            op["_relevancia"] = 1
            con_base.append(op)
        else:
            op["_relevancia"] = 0
            sin_match.append(op)

    if con_descriptor:
        # Ordenar por relevancia desc, luego disponibles primero, luego precio asc
        con_descriptor.sort(key=lambda o: (-o["_relevancia"], not o.get("disponible", False), o.get("precio_base", 9999)))
        resultado = con_descriptor
    elif con_base:
        # Sin descriptor match, pero hay productos con el término base
        con_base.sort(key=lambda o: (not o.get("disponible", False), o.get("precio_base", 9999)))
        resultado = con_base
    else:
        # Ningún producto coincide con descriptores ni término base
        # Devolver vacío para forzar fallback o sugerencia
        resultado = []

    for op in resultado:
        op.pop("_relevancia", None)
    return resultado


async def buscar_por_termino_priorizado(
    db: AsyncSession,
    termino: str,
    cantidad: int = 1,
    termino_base: str | None = None,
    descriptores: list[str] | None = None,
) -> dict:
    """Busca un término en tiendas activas, priorizando AV Electronics.

    1. Busca con el término completo (ej: "led rojo").
    2. Si hay resultados, los filtra por relevancia con los descriptores.
    3. Si no hay resultados, busca con el término base (ej: "led").
    4. Si aún no hay, genera sugerencia.
    """
    margen_pct = await obtener_margen(db)
    tienda_propia = await obtener_tienda_propia(db)
    margen_factor = 1 + margen_pct / 100

    # Búsqueda principal con término completo
    resultado_raw = await buscar_por_termino(db, termino)
    opciones_raw = resultado_raw.get("opciones", [])

    # Filtrar por relevancia: término base y descriptores
    base_para_filtrar = termino_base or termino
    opciones_filtradas = _filtrar_y_ordenar_por_relevancia(opciones_raw, descriptores or [], base_para_filtrar)

    # Fallback: si el filtrado dejó todo vacío Y hay término base diferente, buscar con base
    if not opciones_filtradas and termino_base and termino_base != termino:
        logger.info("Fallback: buscando '%s' en vez de '%s'", termino_base, termino)
        resultado_raw = await buscar_por_termino(db, termino_base)
        opciones_raw = resultado_raw.get("opciones", [])
        opciones_filtradas = _filtrar_y_ordenar_por_relevancia(opciones_raw, descriptores or [], base_para_filtrar)

    # Probar aliases que conservan el mismo artículo antes de declarar que no
    # hay resultados. Ej.: "broche porta pila" -> "portapilas", nunca
    # "batería", porque sería un producto diferente.
    opciones_raw = opciones_filtradas

    opciones_propias = []
    opciones_externas = []

    for op in opciones_raw:
        if op["precio_base"] is None:
            continue
        variantes = op.get("variantes", [])
        if op["tienda"] == tienda_propia:
            opciones_propias.append({
                "tienda": op["tienda"],
                "nombre_producto": op["nombre_producto"],
                "precio_base": op["precio_base"],
                "precio_con_margen": round(op["precio_base"], 2),
                "margen_aplicado": 0.0,
                "disponible": op["disponible"],
                "url": op["url"],
                "es_propio": True,
                "es_favorita": op.get("es_favorita", False),
                "variantes": variantes,
            })
        else:
            precio_con_margen = round(op["precio_base"] * margen_factor, 2)
            opciones_externas.append({
                "tienda": op["tienda"],
                "nombre_producto": op["nombre_producto"],
                "precio_base": op["precio_base"],
                "precio_con_margen": precio_con_margen,
                "margen_aplicado": margen_pct,
                "disponible": op["disponible"],
                "url": op["url"],
                "es_propio": False,
                "es_favorita": op.get("es_favorita", False),
                "variantes": variantes,
            })

    # Ordenar: si hay descriptores, mantener orden por relevancia; si no, por precio
    if not descriptores:
        opciones_propias.sort(key=lambda o: o["precio_con_margen"])
        opciones_externas.sort(key=lambda o: o["precio_con_margen"])
    else:
        # Con descriptores, mantener orden de relevancia (no reordenar)
        pass

    todas_opciones = opciones_propias + opciones_externas
    # La favorita siempre encabeza las opciones, incluso si hay otra más barata.
    todas_opciones.sort(key=lambda opcion: not opcion["es_favorita"])

    return {
        "termino": termino,
        "cantidad": cantidad,
        "encontrado_propia": len(opciones_propias) > 0,
        "opciones": todas_opciones,
        "sugerencia": None,
    }
