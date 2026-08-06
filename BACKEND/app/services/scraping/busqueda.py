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
    """Verifica si palabra aparece como palabra completa en texto (no substring).

    Usa word boundaries que incluyen dígitos: '1' no debe matchear '12'.
    """
    patron = r'(?<![a-z0-9])' + re.escape(palabra) + r'(?![a-z0-9])'
    return bool(re.search(patron, texto))


def _palabra_o_plural_en_texto(palabra: str, texto: str) -> bool:
    """Verifica si palabra o su plural/singular español aparece en texto.

    Maneja plurales reales: canal→canales, pin→pines, terminal→terminales.
    También busca singular si la palabra ya es plural: pines→pin, canales→canal.
    """
    if _palabra_en_texto(palabra, texto):
        return True
    # Buscar singular si la palabra es plural (pines→pin, canales→canal)
    if len(palabra) > 4 and palabra.endswith("es"):
        singular = palabra[:-2]  # pines→pin, canales→canal
        if _palabra_en_texto(singular, texto):
            return True
    elif len(palabra) > 3 and palabra.endswith("s") and not palabra.endswith("es"):
        singular = palabra[:-1]  # cables→cable
        if _palabra_en_texto(singular, texto):
            return True
    # Plural español: si termina en vocal +s, conson +es
    if palabra[-1:] in "aeiou":
        plural = palabra + "s"
    elif palabra[-1:] in "rzns":
        plural = palabra + "es"
    else:
        plural = palabra + "es"
    if _palabra_en_texto(plural, texto):
        return True
    # Casos irregulares comunes: pin→pines (n→nes)
    if palabra.endswith("n") and not palabra.endswith("en"):
        plural_irreg = palabra[:-1] + "nes"
        if _palabra_en_texto(plural_irreg, texto):
            return True
    return False


def _score_relevancia(nombre_producto: str, descriptores: list[str]) -> int:
    """Puntúa qué tan relevante es un producto según los descriptores.

    Mayor score = más relevante. 0 = no contiene ningún descriptor.
    Penaliza productos que tienen un valor de la misma clase pero diferente
    (ej: descriptor pide 470uf, producto tiene 10uf → penalización -20).
    """
    nombre_norm = _normalizar_texto(nombre_producto)
    valores_producto = _extraer_valores(nombre_norm)
    score = 0
    for desc in descriptores:
        desc_norm = _normalizar_texto(desc)
        # 1. Valores con unidad (470uf, 5v, 4.7kohm) — comparación numérica
        valores_desc = _extraer_valores(desc_norm)
        if valores_desc:
            matched = False
            mismatched = False
            for clase, valor in valores_desc:
                if (clase, valor) in valores_producto:
                    matched = True
                elif any(c == clase for c, _ in valores_producto):
                    mismatched = True
            if matched:
                score += 15
            if mismatched:
                score -= 20
            continue
        # 2. Coincidencia exacta del descriptor completo
        if _palabra_en_texto(desc_norm, nombre_norm):
            score += 10
            continue
        # 3. Descriptor compuesto (ej: '1 canal', '2 pines', '40 surtido')
        partes = desc_norm.split()
        partes_numericas = [p for p in partes if p.replace(".", "").replace(",", "").isdigit()]
        partes_texto = [p for p in partes if p not in partes_numericas]
        if partes_numericas:
            numero_match = all(_palabra_en_texto(p, nombre_norm) for p in partes_numericas)
            texto_coincide = any(
                _palabra_o_plural_en_texto(p, nombre_norm)
                for p in partes_texto if len(p) >= 3
            )
            if not numero_match:
                # Si el texto coincide pero el número no, penalizar fuerte
                # ej: descriptor '1 canal', producto '2 canales' → -15
                if texto_coincide:
                    score -= 15
                # Si ni número ni texto coinciden, no dar ni quitar puntos
                continue
            # Número coincide: solo dar bonus si el texto también coincide
            if texto_coincide:
                score += 8  # número + texto = match fuerte
            # Si solo el número coincide pero no el texto, no dar bonus
            # (ej: '2' en '2.8mm' no debe puntuar para descriptor '2 pines')
            continue
        # 4. Bonus por palabras de texto que coinciden (con plurales reales)
        for parte in partes_texto:
            if len(parte) >= 3 and _palabra_o_plural_en_texto(parte, nombre_norm):
                score += 3
    # 6. Bonus por 'pack': si hay descriptor 'pack' y el producto tiene '40' o 'pack'
    if any(_normalizar_texto(d) == "pack" for d in descriptores):
        if "pack" in nombre_norm or "surtido" in nombre_norm or " 40 " in f" {nombre_norm} ":
            score += 10
        else:
            score -= 5
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
    """Filtra y ordena opciones por relevancia.

    Criterio: producto ES del tipo buscado Y tiene score > 0 (coincide con
    al menos un descriptor o el término base).
    Si no hay resultados, retorna [] (el caller generará sugerencia).
    """
    if not descriptores and not termino_base and not tipo:
        return opciones

    relevantes = []
    for op in opciones:
        nombre = op.get("nombre_producto", "")
        nombre_norm = _normalizar_texto(nombre)
        score = _score_relevancia(nombre, descriptores) if descriptores else 0
        # Si el score es negativo (penalización por valor incorrecto), excluir
        if score < 0:
            continue
        # Bonus por coincidencia del termino_base (ej: "esp 32" en "ESP32 ESP-WROOM-32")
        # Solo si el termino_base es específico (no solo la palabra del tipo genérico)
        base_bonus = 0
        if termino_base and not (termino_base == tipo and " " not in termino_base):
            base_norm = _normalizar_texto(termino_base)
            base_sin_espacios = base_norm.replace(" ", "")
            nombre_sin_espacios = nombre_norm.replace(" ", "")
            if _palabra_en_texto(base_norm, nombre_norm) or base_sin_espacios in nombre_sin_espacios:
                base_bonus = 10
            elif " " in base_norm:
                # Matching parcial: +3 por cada palabra del termino_base que aparece
                for palabra in base_norm.split():
                    if len(palabra) >= 4 and _palabra_en_texto(palabra, nombre_norm):
                        base_bonus += 3
        total = score + base_bonus
        es_tipo = _match_tipo(nombre_norm, tipo, termino_base)
        op["_relevancia"] = total
        # Incluir si: es del tipo correcto Y (score > 0 O base_bonus > 0)
        if es_tipo and total > 0:
            relevantes.append(op)

    relevantes.sort(key=lambda o: (-o["_relevancia"], not o.get("disponible", False), o.get("precio_base", 9999)))

    MAX_RESULTADOS = 5
    resultado = relevantes[:MAX_RESULTADOS]
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

    # Si no hay resultados, generar sugerencia y opción agotado
    sugerencia = None
    if not todas_opciones:
        sugerencia = sugerir_termino(termino)
        # Retornar opción agotado para que el frontend pueda mostrar alternativas
        todas_opciones = [{
            "tienda": None,
            "nombre_producto": termino,
            "precio_base": None,
            "precio_con_margen": None,
            "margen_aplicado": 0.0,
            "disponible": False,
            "url": None,
            "es_propio": False,
            "variantes": [],
            "agotado": True,
        }]

    return {
        "termino": termino,
        "cantidad": cantidad,
        "encontrado_propia": len(opciones_propias) > 0,
        "opciones": todas_opciones,
        "sugerencia": sugerencia,
    }
