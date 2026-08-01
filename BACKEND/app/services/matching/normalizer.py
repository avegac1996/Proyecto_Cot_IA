import re

# Diccionario de términos coloquiales/sinónimos → tipo estandarizado.
# Se enriquece con la tabla `equivalencias` en BD; este mapa es el fallback base.
TIPOS_PALABRAS: dict[str, list[str]] = {
    "resistencia": ["resistencia", "resistor", "resistores"],
    "capacitor": ["capacitor", "condensador", "capacitores"],
    "led": ["led", "leds", "foquito", "foquitos", "bombillo", "bombilla", "foco"],
    "transistor": ["transistor", "transistores"],
    "diodo": ["diodo", "diodos"],
    "integrado": ["integrado", "circuito integrado", "chip"],
    "protoboard": ["protoboard", "tablita", "breadboard", "tabla de pruebas"],
    "arduino": ["arduino"],
    "sensor": ["sensor", "sensores"],
    "fuente": ["fuente", "eliminador", "cargador", "transformador"],
    "conector": ["conector", "conectores", "jack", "plug", "borne"],
    "cable": ["cable", "cables", "jumper", "jumpers", "alambre"],
    "pulsador": ["pulsador", "boton", "botón", "switch", "interruptor", "push"],
    "buzzer": ["buzzer", "zumbador", "bocina", "speaker", "altavoz"],
    "motor": ["motor", "servo", "servomotor", "motor dc"],
    "rele": ["rele", "relé", "relay"],
    "potenciometro": ["potenciometro", "potenciómetro", "pot"],
    "display": ["display", "pantalla", "lcd", "oled", "7 segmentos"],
}

COLORES = ["rojo", "verde", "azul", "amarillo", "blanco", "rgb", "naranja", "violeta"]
TAMANOS_LED = ["3mm", "5mm", "8mm", "10mm", "smd"]
TIPOS_TRANSISTOR = ["npn", "pnp", "mosfet", "jfet"]
TIPOS_DIODOS = ["rectificador", "zener", "schottky", "led", "puente"]

# Campos que deben estar presentes por tipo para no ser ambiguo
CAMPOS_REQUERIDOS: dict[str, list[str]] = {
    "resistencia": ["valor"],
    "capacitor": ["valor"],
    "led": ["color", "tamano"],
    "transistor": ["tipo_o_modelo"],
    "diodo": ["tipo_o_modelo"],
}


def detectar_tipo(texto: str) -> str:
    for tipo, palabras in TIPOS_PALABRAS.items():
        for palabra in palabras:
            if re.search(rf"\b{re.escape(palabra)}", texto):
                return tipo
    return "desconocido"


def normalizar_valor(valor_str: str, multiplicador: str | None) -> str:
    """Normaliza '10k' → '10000', '0.1' → '0.1'. Devuelve el valor como string."""
    valor = float(valor_str.replace(",", "."))
    if multiplicador:
        mult = multiplicador.lower()
        if mult == "k":
            valor *= 1_000
        elif mult == "m":
            valor *= 0.001
    if valor == int(valor):
        return str(int(valor))
    return str(valor)


def normalizar_unidad(unidad: str) -> str:
    u = unidad.lower()
    mapa = {
        "ohm": "ohm", "ohms": "ohm", "Ω": "ohm",
        "uf": "uF", "µf": "uF", "nf": "nF", "pf": "pF", "f": "F",
        "v": "V", "voltios": "V",
        "ma": "mA", "a": "A",
        "w": "W", "watts": "W",
        "h": "H", "mh": "mH",
    }
    return mapa.get(u, u)


def detectar_ambiguedades(tipo: str, texto: str, valor: str | None) -> list[str]:
    """Detecta qué campos requeridos faltan según el tipo de componente."""
    ambiguedades: list[str] = []

    if tipo == "desconocido":
        return ["tipo"]

    requeridos = CAMPOS_REQUERIDOS.get(tipo, [])
    for campo in requeridos:
        if campo == "valor":
            if valor is None:
                ambiguedades.append("valor")
        elif campo == "color":
            if not any(c in texto for c in COLORES):
                ambiguedades.append("color")
        elif campo == "tamano":
            if not any(t in texto for t in TAMANOS_LED):
                ambiguedades.append("tamano")
        elif campo == "tipo_o_modelo":
            opciones = TIPOS_TRANSISTOR if tipo == "transistor" else TIPOS_DIODOS
            tiene_tipo = any(o in texto for o in opciones)
            tiene_modelo = re.search(r"\b[a-z]{1,3}\d{3,5}[a-z]?\b", texto) is not None
            if not tiene_tipo and not tiene_modelo:
                ambiguedades.append("tipo_o_modelo")

    return ambiguedades


def aplicar_respuestas(componentes: list[dict], respuestas: list[dict], preguntas_map: dict[int, dict]) -> list[dict]:
    """Aplica las respuestas del usuario a los componentes afectados por cada pregunta."""
    for resp in respuestas:
        pregunta = preguntas_map.get(resp["pregunta_id"])
        if pregunta is None:
            continue
        campo = pregunta["campo_a_desambiguar"]
        valor_respuesta = resp["respuesta"].strip().lower()
        for idx in pregunta["componentes_afectados"]:
            if idx >= len(componentes):
                continue
            comp = componentes[idx]
            if campo == "color":
                comp["color"] = valor_respuesta
            elif campo == "tamano":
                comp["tamano"] = valor_respuesta
            elif campo == "valor":
                comp["valor"] = valor_respuesta
            elif campo == "tipo_o_modelo":
                comp["tipo_o_modelo"] = valor_respuesta
            else:
                comp[campo] = valor_respuesta
            if campo in comp["ambiguedades"]:
                comp["ambiguedades"].remove(campo)
            comp["ambiguo"] = len(comp["ambiguedades"]) > 0
    return componentes
