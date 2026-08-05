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
    DESCRIPCIONES_EXTRA,
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
    # Eliminar puntuación (¿?¡!.,;:()[]{}'"-...)
    texto = re.sub(r"[¿?¡!.,;:()\[\]{}'\"\\\/\-]", " ", texto)
    # Múltiples espacios → uno solo
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def _construir_diccionario_busqueda() -> dict[str, str]:
    """Construye un diccionario término → tipo desde TIPOS_PALABRAS y listas auxiliares.

    Agrega variantes con espacio para términos letra+numero pegados:
    "esp32" -> tambien reconoce "esp 32", "hc05" -> "hc 05", etc.
    """
    dic = {}
    for tipo, palabras in TIPOS_PALABRAS.items():
        for palabra in palabras:
            dic[palabra] = tipo
            # Variante con espacio: "esp32" -> "esp 32", "hc05" -> "hc 05"
            match = re.match(r"^([a-z]+)(\d+)$", palabra)
            if match:
                dic[f"{match.group(1)} {match.group(2)}"] = tipo
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
    # Agregar descripciones extra como tipo 'descriptor'
    for desc in DESCRIPCIONES_EXTRA:
        dic[desc] = "descriptor"
    return dic


_DICCIONARIO = _construir_diccionario_busqueda()

# Conjunto de todas las palabras que son componentes (no descriptores)
_PALABRAS_COMPONENTE = {
    p for p, tipo in _DICCIONARIO.items()
    if tipo not in ("color", "tamano", "descriptor")
}

# Tipos que son compatibles entre si (se consumen como descriptores)
_TIPOS_COMPATIBLES: dict[str, set[str]] = {
    "wifi": {"bluetooth"},
    "bluetooth": {"wifi"},
}

# Palabras que se ignoran silenciosamente durante el scan de descriptores
_STOP_WORDS = {"de", "del", "la", "el", "los", "las", "con", "para", "en", "y", "un", "una", "datos", "poder", "agua"}


def _es_modelo_o_spec(palabra: str) -> bool:
    """Detecta si una palabra es un modelo o especificacion (contiene letras y numeros).

    Ejemplos: bme680, vl53l1x, kf301, 5v, 16v, 2a, 470uf, i2c, hc06
    """
    return any(c.isalpha() for c in palabra) and any(c.isdigit() for c in palabra)


def _extraer_cantidad(texto: str, posicion: int) -> int:
    """Busca un número antes de la posición dada en el texto."""
    antes = texto[:posicion].rstrip()
    match = re.search(r"(\d+)\s*(?:x|×)?\s*$", antes)
    if match:
        return int(match.group(1))
    return 1


def _singularizar_color(palabra: str) -> str:
    """Convierte plurales de colores a singular: rojos -> rojo, verdes -> verde."""
    mapa = {
        "rojos": "rojo", "verdes": "verde", "azules": "azul",
        "amarillos": "amarillo", "amarrillos": "amarrillo",
        "blancos": "blanco", "negros": "negro", "naranjas": "naranja",
        "morados": "morado", "violetas": "violeta",
    }
    return mapa.get(palabra, palabra)


def _singularizar_componente(palabra: str) -> str:
    """Convierte plurales de componentes a singular: leds -> led, jumpers -> jumper."""
    mapa = {
        "leds": "led", "jumpers": "jumper", "resistencias": "resistencia",
        "resistores": "resistor", "capacitores": "capacitor",
        "transistores": "transistor", "diodos": "diodo",
        "cables": "cable", "pulsadores": "pulsador",
        "botones": "boton", "sensores": "sensor",
        "conectores": "conector", "baterias": "bateria",
        "pilas": "pila", "focos": "foco",
    }
    return mapa.get(palabra, palabra)


def _buscar_descriptores(
    palabras: list[str],
    consumido: list[bool],
    inicio: int,
    fin: int,
    tipo_componente: str,
) -> list[str]:
    """Busca palabras descriptoras y sinónimos del mismo tipo alrededor del componente [inicio, fin).

    También consume palabras que son sinónimos del mismo tipo de componente
    (ej: 'boton' cuando se encontro 'pulsador') para evitar duplicados.
    """
    descriptores: list[str] = []

    # Buscar hacia adelante (después del componente)
    j = fin
    while j < len(palabras) and not consumido[j]:
        palabra = palabras[j]
        # Ignorar stop words (de, del, la, el, etc.)
        if palabra in _STOP_WORDS:
            consumido[j] = True
            j += 1
            continue
        # Capturar modelos y especificaciones alfanumericas (bme680, vl53l1x, 5v, etc.)
        if _es_modelo_o_spec(palabra) and palabra not in _DICCIONARIO:
            descriptores.append(palabra)
            consumido[j] = True
            j += 1
            continue
        # Si es un número, verificar si es cantidad de otro componente o especificación
        if palabra.isdigit():
            # Si la siguiente palabra es un componente conocido, parar (nueva línea)
            if j + 1 < len(palabras) and palabras[j + 1] in _PALABRAS_COMPONENTE:
                break
            # Si no, es una especificación (ej: 330 ohms, 2 pines)
            # Probar n-grams que incluyen el número (ej: "2 pines", "4 pin")
            for v in (3, 2):
                if j + v <= len(palabras) and not any(consumido[j : j + v]):
                    ngram = " ".join(palabras[j : j + v])
                    if ngram in _DICCIONARIO and _DICCIONARIO[ngram] in ("color", "tamano", "descriptor"):
                        descriptores.append(ngram)
                        for k in range(j, j + v):
                            consumido[k] = True
                        j += v
                        break
            else:
                # Si no se encontró n-gram con número, buscar sin número
                num = palabra
                j += 1
                if j < len(palabras) and not consumido[j]:
                    for v in (2, 1):
                        if j + v <= len(palabras) and not any(consumido[j : j + v]):
                            ngram = " ".join(palabras[j : j + v])
                            if ngram in _DICCIONARIO and _DICCIONARIO[ngram] in ("color", "tamano", "descriptor"):
                                descriptores.append(f"{num} {ngram}")
                                for k in range(j, j + v):
                                    consumido[k] = True
                                j += v
                                break
            continue
        # Probar n-grams de 2 y 1 hacia adelante
        encontrado = False
        for v in (2, 1):
            if j + v <= len(palabras) and not any(consumido[j : j + v]):
                ngram = " ".join(palabras[j : j + v])
                if ngram in _DICCIONARIO:
                    tipo_ngram = _DICCIONARIO[ngram]
                    if tipo_ngram == tipo_componente:
                        # Sinónimo del mismo componente, consumir sin agregar
                        for k in range(j, j + v):
                            consumido[k] = True
                        j += v
                        encontrado = True
                        break
                    elif tipo_ngram in _TIPOS_COMPATIBLES.get(tipo_componente, set()):
                        # Tipo compatible (ej: bluetooth junto a wifi), consumir como descriptor
                        descriptores.append(ngram)
                        for k in range(j, j + v):
                            consumido[k] = True
                        j += v
                        encontrado = True
                        break
                    elif tipo_ngram in ("color", "tamano", "descriptor"):
                        if tipo_ngram == "color":
                            descriptores.append(_singularizar_color(ngram))
                        else:
                            descriptores.append(ngram)
                        for k in range(j, j + v):
                            consumido[k] = True
                        j += v
                        encontrado = True
                        break
        if not encontrado:
            # Si la palabra no es descriptor ni sinónimo, parar
            break

    # Buscar hacia atras (antes del componente, después del número)
    j = inicio - 1
    while j >= 0 and not consumido[j]:
        palabra = palabras[j]
        # Si es un número, no consumir (lo maneja _extraer_cantidad)
        if palabra.isdigit():
            break
        # Ignorar stop words hacia atras
        if palabra in _STOP_WORDS:
            consumido[j] = True
            j -= 1
            continue
        if palabra in _DICCIONARIO:
            tipo_palabra = _DICCIONARIO[palabra]
            if tipo_palabra == tipo_componente:
                # Sinónimo del mismo componente, consumir sin agregar
                consumido[j] = True
                j -= 1
                continue
            elif tipo_palabra in _TIPOS_COMPATIBLES.get(tipo_componente, set()):
                descriptores.insert(0, palabra)
                consumido[j] = True
                j -= 1
                continue
            elif tipo_palabra in ("color", "tamano", "descriptor"):
                if tipo_palabra == "color":
                    descriptores.insert(0, _singularizar_color(palabra))
                else:
                    descriptores.insert(0, palabra)
                consumido[j] = True
                j -= 1
                continue
        # Capturar modelos/especificaciones hacia atras
        if _es_modelo_o_spec(palabra):
            descriptores.insert(0, palabra)
            consumido[j] = True
            j -= 1
            continue
        break

    return descriptores


def _extraer_de_linea(texto: str) -> list[dict]:
    """Extrae componentes de una sola linea de texto normalizado."""
    palabras = texto.split()
    n = len(palabras)
    consumido = [False] * n
    resultados: list[dict] = []

    # Si la linea empieza con numero, es la cantidad por defecto
    cantidad_default = 1
    if palabras and palabras[0].isdigit():
        cantidad_default = int(palabras[0])

    # Ventana de 3 → 2 → 1 palabras
    for ventana in (3, 2, 1):
        for i in range(n - ventana + 1):
            # Saltar si alguna palabra ya fue consumida
            if any(consumido[i : i + ventana]):
                continue

            ngram = " ".join(palabras[i : i + ventana])
            if ngram in _DICCIONARIO:
                tipo = _DICCIONARIO[ngram]
                if tipo in ("color", "tamano", "descriptor"):
                    # No es un componente por sí solo.
                    # NO marcar como consumido: se capturará como descriptor
                    # del componente más cercano en _buscar_descriptores.
                    continue

                # Calcular posición en texto original para extraer cantidad
                pos_aprox = len(" ".join(palabras[:i])) + (1 if i > 0 else 0)
                cantidad = _extraer_cantidad(texto, pos_aprox)
                # Si no se encontro numero adyacente, usar el de la linea
                if cantidad == 1 and cantidad_default > 1:
                    cantidad = cantidad_default

                # Marcar palabras del componente como consumidas
                for j in range(i, i + ventana):
                    consumido[j] = True

                # Buscar descriptores adyacentes (colores, tamaños, especificaciones)
                descriptores = _buscar_descriptores(palabras, consumido, i, i + ventana, tipo)

                # Construir término de búsqueda enriquecido
                termino_base = _singularizar_componente(ngram)
                termino_busqueda = termino_base
                if descriptores:
                    termino_busqueda = f"{termino_base} {' '.join(descriptores)}"

                resultados.append({
                    "termino": termino_busqueda,
                    "termino_base": termino_base,
                    "descriptores": descriptores,
                    "cantidad": cantidad,
                    "tipo": tipo,
                })

    return resultados


def extraer_componentes(mensaje: str) -> list[dict]:
    """Extrae componentes electrónicos de un mensaje conversacional.

    Procesa linea por linea para no mezclar componentes de diferentes lineas.
    Usa n-grams (3→2→1) contra el diccionario TIPOS_PALABRAS.
    Captura descriptores adyacentes (colores, tamaños, especificaciones)
    para enriquecer el término de búsqueda.

    Returns:
        list[dict] con keys: termino (str), cantidad (int), tipo (str)
    """
    resultados: list[dict] = []

    for linea in mensaje.split("\n"):
        texto = _normalizar(linea)
        if not texto:
            continue
        resultados.extend(_extraer_de_linea(texto))

    return resultados
