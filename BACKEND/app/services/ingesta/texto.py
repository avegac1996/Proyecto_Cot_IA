import re

from app.services.matching.normalizer import (
    detectar_ambiguedades,
    detectar_tipo,
    normalizar_unidad,
    normalizar_valor,
)

# Cantidad al inicio: "5 resistencias", "5x led", "5 x led"
RE_CANTIDAD_INICIO = re.compile(r"^(\d+)\s*(?:x|×)?\s+", re.IGNORECASE)
# Cantidad al final: "led x5", "resistencias x 5"
RE_CANTIDAD_FIN = re.compile(r"(?:x|×)\s*(\d+)\s*$", re.IGNORECASE)
# Valor con unidad: "220 ohm", "220Ω", "10k", "100uf", "0.1uF", "5v"
RE_VALOR_UNIDAD = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(k|m)?\s*(ohm|ohms|Ω|uf|µf|nf|pf|f|v|voltios|ma|a|w|watts|h|mh)\b",
    re.IGNORECASE,
)


def parsear_linea(linea: str) -> dict:
    """Convierte una línea de texto libre en un componente estructurado."""
    texto_original = linea.strip()
    texto = texto_original.lower()

    cantidad = 1
    match = RE_CANTIDAD_INICIO.match(texto)
    if match:
        cantidad = int(match.group(1))
        texto = texto[match.end():]
    else:
        match = RE_CANTIDAD_FIN.search(texto)
        if match:
            cantidad = int(match.group(1))
            texto = texto[: match.start()].strip()

    valor = None
    unidad = None
    match = RE_VALOR_UNIDAD.search(texto)
    if match:
        valor = normalizar_valor(match.group(1), match.group(2))
        unidad = normalizar_unidad(match.group(3))

    tipo = detectar_tipo(texto)
    ambiguedades = detectar_ambiguedades(tipo, texto, valor)

    return {
        "texto_original": texto_original,
        "tipo": tipo,
        "valor": valor,
        "unidad": unidad,
        "cantidad": cantidad,
        "ambiguo": len(ambiguedades) > 0,
        "ambiguedades": ambiguedades,
    }


def parsear_texto(contenido: str) -> list[dict]:
    """Procesa un archivo de texto completo y devuelve la lista de componentes."""
    componentes = []
    for linea in re.split(r"[\r\n;]+", contenido):
        linea = linea.strip().strip(",")
        if len(linea) < 2:
            continue
        componentes.append(parsear_linea(linea))
    return componentes
