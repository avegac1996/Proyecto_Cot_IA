"""Extracción de componentes desde texto conversacional usando n-grams.

Estrategia:
1. Normalizar texto (lowercase, sin tildes, sin puntuación excesiva).
2. Generar ventanas deslizantes de 3 → 2 → 1 palabras.
3. Comparar cada ventana contra TIPOS_PALABRAS y listas de especificaciones.
4. Marcar posiciones consumidas para no duplicar.
5. Extraer cantidad si hay un número antes del término.
6. Retornar lista de términos de búsqueda.
"""

import re
import unicodedata

from app.services.matching.normalizer import (
    COLORES,
    TAMANOS_LED,
    TIPOS_MOTOR,
    TIPOS_SENSOR,
    TIPOS_PALABRAS,
)


def _normalizar(texto: str) -> str:
    """Lowercase, sin tildes, sin puntuación excesiva."""
    texto = texto.lower().strip()
    # Sin tildes
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    # Eliminar puntuación (¿?¡!.,;:()[]{}'"...)
    texto = re.sub(r"[¿?¡!.,;:()\[\]{}'\"\\\/]", " ", texto)
    # Múltiples espacios → uno solo
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def _construir_diccionario_busqueda() -> dict[str, str]:
    """Construye un diccionario término → tipo desde TIPOS_PALABRAS y listas auxiliares."""
    dic = {}
    for tipo, palabras in TIPOS_PALABRAS.items():
        for palabra in palabras:
            dic[palabra] = tipo
    # Agregar tipos específicos de sensor
    for sensor_tipo in TIPOS_SENSOR:
        dic[sensor_tipo] = "sensor"
    # Agregar tipos de motor
    for motor_tipo in TIPOS_MOTOR:
        dic[motor_tipo] = "motor"
    # Agregar colores
    for color in COLORES:
        dic[color] = "color"
    # Agregar tamaños LED
    for tam in TAMANOS_LED:
        dic[tam] = "tamano"
    return dic


_DICCIONARIO = _construir_diccionario_busqueda()


def _extraer_cantidad(texto: str, posicion: int) -> int:
    """Busca un número antes de la posición dada en el texto."""
    antes = texto[:posicion].rstrip()
    match = re.search(r"(\d+)\s*(?:x|×)?\s*$", antes)
    if match:
        return int(match.group(1))
    return 1


def extraer_componentes(mensaje: str) -> list[dict]:
    """Extrae componentes electrónicos de un mensaje conversacional.

    Usa n-grams (3→2→1) contra el diccionario TIPOS_PALABRAS.
    No filtra stopwords a ciegas — busca matches contra tipos conocidos.

    Returns:
        list[dict] con keys: termino (str), cantidad (int), tipo (str)
    """
    texto = _normalizar(mensaje)
    if not texto:
        return []

    palabras = texto.split()
    n = len(palabras)
    consumido = [False] * n
    resultados: list[dict] = []

    # Ventana de 3 → 2 → 1 palabras
    for ventana in (3, 2, 1):
        for i in range(n - ventana + 1):
            # Saltar si alguna palabra ya fue consumida
            if any(consumido[i : i + ventana]):
                continue

            ngram = " ".join(palabras[i : i + ventana])
            if ngram in _DICCIONARIO:
                tipo = _DICCIONARIO[ngram]
                if tipo in ("color", "tamano"):
                    # No es un componente por sí solo, pero marcamos como consumido
                    for j in range(i, i + ventana):
                        consumido[j] = True
                    continue

                # Calcular posición en texto original para extraer cantidad
                pos_aprox = len(" ".join(palabras[:i])) + (1 if i > 0 else 0)
                cantidad = _extraer_cantidad(texto, pos_aprox)

                resultados.append({
                    "termino": ngram,
                    "cantidad": cantidad,
                    "tipo": tipo,
                })
                for j in range(i, i + ventana):
                    consumido[j] = True

    return resultados
