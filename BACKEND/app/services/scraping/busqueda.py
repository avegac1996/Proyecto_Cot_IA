"""Búsqueda priorizada: AV Electronics primero, luego tiendas externas con margen."""

import logging
import re
import unicodedata

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.configuracion import obtener_margen, obtener_tienda_propia
from app.services.matching.normalizer import TIPOS_PALABRAS
from app.services.scraping.engine import buscar_por_termino
from app.services.scraping.sugerencias import sugerir_termino

logger = logging.getLogger(__name__)


def _normalizar_texto(texto: str) -> str:
    """Lowercase, sin tildes, con unidades normalizadas."""
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    # Normalizar unidades de resistencia: ω/ohm/ohms → ohm
    texto = texto.replace("ω", "ohm")
    texto = re.sub(r'\bohms\b', 'ohm', texto)
    # Normalizar micro: µ/μ → u (470µF → 470uf)
    texto = texto.replace("µ", "u").replace("μ", "u")
    # Normalizar errores ortográficos comunes
    texto = re.sub(r'\bamarrillo\b', 'amarillo', texto)
    return texto


_PATRON_VALOR = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(k|m)?\s*(ohm|uf|nf|pf|v|ma|a|w)\b"
)

_CLASES_UNIDAD = {
    "ohm": "R",
    "uf": "C", "nf": "C", "pf": "C",
    "v": "V",
    "a": "I", "ma": "I",
    "w": "W",
}


def _extraer_valores(texto: str) -> set[tuple[str, float]]:
    """Extrae pares (clase, valor_base) de un texto normalizado.

    Normaliza a unidades base para comparación numérica:
    - Resistencia → ohms (4.7kohm → 4700)
    - Capacitancia → uF (470nf → 0.47)
    - Corriente → A (500ma → 0.5)
    """
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


def _palabra_en_texto(palabra: str, texto: str) -> bool:
    """Verifica si palabra aparece como palabra completa en texto (no substring)."""
    patron = r'(?<![a-z])' + re.escape(palabra) + r'(?![a-z])'
    return bool(re.search(patron, texto))


def _score_relevancia(nombre_producto: str, descriptores: list[str]) -> int:
    """Puntúa qué tan relevante es un producto según los descriptores.

    Mayor score = más relevante. 0 = no contiene ningún descriptor.
    Usa matching de palabra completa para evitar falsos positivos (ej: 'rojo' en 'infrarrojo').
    Si el descriptor contiene un número, el producto debe contener ese número para puntuar.
    Los valores con unidad (470uf, 4.7kohm, 5v) se comparan numéricamente.
    """
    nombre_norm = _normalizar_texto(nombre_producto)
    valores_producto = _extraer_valores(nombre_norm)
    score = 0
    for desc in descriptores:
        desc_norm = _normalizar_texto(desc)
        # Coincidencia numérica de valores con unidad (470µF == 470 uF, 4.7kΩ == 4.7 KΩ)
        valores_desc = _extraer_valores(desc_norm)
        if valores_desc:
            if valores_desc & valores_producto:
                score += 15
            continue
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


def _match_tipo(nombre_norm: str, tipo: str | None, termino_base: str | None) -> bool:
    """Verifica si el producto pertenece al tipo de componente buscado.

    Usa las palabras de TIPOS_PALABRAS[tipo] (ej: regleta → regleta, tira de pines, header).
    Si no hay tipo, cae al matching por término base (comportamiento anterior).
    """
    if tipo and tipo in TIPOS_PALABRAS:
        for palabra in TIPOS_PALABRAS[tipo]:
            palabra_norm = _normalizar_texto(palabra)
            if " " in palabra_norm:
                if palabra_norm in nombre_norm:
                    return True
            elif _palabra_en_texto(palabra_norm, nombre_norm) or _palabra_en_texto(palabra_norm + "s", nombre_norm):
                return True
        return False
    # Fallback: matching por término base
    if not termino_base:
        return False
    base_norm = _normalizar_texto(termino_base)
    base_plural = base_norm + "s" if not base_norm.endswith("s") else ""
    base_sin_espacios = base_norm.replace(" ", "")
    return (
        _palabra_en_texto(base_norm, nombre_norm)
        or (base_plural and _palabra_en_texto(base_plural, nombre_norm))
        or (base_sin_espacios and base_sin_espacios in nombre_norm.replace(" ", ""))
    )


def _filtrar_y_ordenar_por_relevancia(
    opciones: list[dict],
    descriptores: list[str],
    termino_base: str | None = None,
    tipo: str | None = None,
) -> list[dict]:
    """Filtra y ordena opciones por relevancia en 3 niveles:

    Nivel 1: producto ES del tipo buscado Y coincide con descriptores (lo que pidió el cliente).
    Nivel 2: producto ES del tipo buscado pero sin match de descriptores (alternativas del mismo tipo).
    Nivel 3: producto NO es del tipo pero coincide con algún descriptor (ej: 'hembra' en adaptador USB).
    """
    if not descriptores and not termino_base and not tipo:
        return opciones

    nivel1, nivel2, nivel3 = [], [], []
    for op in opciones:
        nombre = op.get("nombre_producto", "")
        nombre_norm = _normalizar_texto(nombre)
        score = _score_relevancia(nombre, descriptores) if descriptores else 0
        es_tipo = _match_tipo(nombre_norm, tipo, termino_base)
        op["_relevancia"] = score
        if score > 0 and es_tipo:
            nivel1.append(op)
        elif es_tipo:
            nivel2.append(op)
        elif score > 0:
            nivel3.append(op)

    nivel1.sort(key=lambda o: (-o["_relevancia"], not o.get("disponible", False), o.get("precio_base", 9999)))
    nivel2.sort(key=lambda o: (not o.get("disponible", False), o.get("precio_base", 9999)))
    nivel3.sort(key=lambda o: (-o["_relevancia"], not o.get("disponible", False), o.get("precio_base", 9999)))

    MAX_NIVEL1 = 10
    MAX_NIVEL2 = 5
    MAX_NIVEL3 = 3
    MIN_NIVEL1_PARA_OMITIR = 5

    nivel1 = nivel1[:MAX_NIVEL1]
    if len(nivel1) >= MIN_NIVEL1_PARA_OMITIR:
        nivel2 = []
        nivel3 = []
    else:
        nivel2 = nivel2[:MAX_NIVEL2]
        nivel3 = nivel3[:MAX_NIVEL3]

    resultado = nivel1 + nivel2 + nivel3
    for op in resultado:
        op.pop("_relevancia", None)
    return resultado


async def buscar_por_termino_priorizado(
    db: AsyncSession,
    termino: str,
    cantidad: int = 1,
    termino_base: str | None = None,
    descriptores: list[str] | None = None,
    tipo: str | None = None,
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

    # Filtrar por relevancia: tipo, término base y descriptores
    base_para_filtrar = termino_base or termino
    opciones_filtradas = _filtrar_y_ordenar_por_relevancia(opciones_raw, descriptores or [], base_para_filtrar, tipo)

    # Fallback: si el filtrado dejó todo vacío Y hay término base diferente, buscar con base
    if not opciones_filtradas and termino_base and termino_base != termino:
        logger.info("Fallback: buscando '%s' en vez de '%s'", termino_base, termino)
        resultado_raw = await buscar_por_termino(db, termino_base)
        opciones_raw = resultado_raw.get("opciones", [])
        opciones_filtradas = _filtrar_y_ordenar_por_relevancia(opciones_raw, descriptores or [], base_para_filtrar, tipo)

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

    # Si no hay resultados, generar sugerencia
    sugerencia = None
    if not todas_opciones:
        sugerencia = sugerir_termino(termino)

    return {
        "termino": termino,
        "cantidad": cantidad,
        "encontrado_propia": len(opciones_propias) > 0,
        "opciones": todas_opciones,
        "sugerencia": sugerencia,
    }
