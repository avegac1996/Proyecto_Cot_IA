import re

# Diccionario de términos coloquiales/sinónimos → tipo estandarizado.
# Se enriquece con la tabla `equivalencias` en BD; este mapa es el fallback base.
TIPOS_PALABRAS: dict[str, list[str]] = {
    "resistencia": ["resistencia", "resistencias", "resistor", "resistores"],
    "capacitor": ["capacitor", "condensador", "capacitores"],
    "led": ["led", "leds", "foquito", "foquitos", "bombillo", "bombilla", "foco", "focos"],
    "transistor": ["transistor", "transistores"],
    "diodo": ["diodo", "diodos"],
    "integrado": ["integrado", "circuito integrado", "chip"],
    "protoboard": ["protoboard", "tablita", "breadboard", "tabla de pruebas"],
    "arduino": ["arduino"],
    "sensor": ["sensor", "sensores"],
    "fuente": ["fuente", "eliminador", "cargador", "transformador", "adaptador"],
    "conector": ["conector", "conectores", "jack", "plug", "borne"],
    "cable": ["cable", "cables", "jumper", "jumpers", "alambre"],
    "pulsador": ["pulsador", "pulsadores", "boton", "botones", "botón", "switch", "interruptor", "push"],
    "buzzer": ["buzzer", "zumbador", "bocina", "speaker", "altavoz"],
    "motor": ["motor dc", "motor", "servo", "servomotor", "paso a paso", "stepper"],
    "rele": ["rele", "relé", "relay"],
    "potenciometro": ["potenciometro", "potenciómetro", "pot"],
    "display": ["display", "pantalla", "lcd", "oled", "7 segmentos"],
    "wifi": ["esp8266", "esp32", "wifi", "wi-fi", "internet"],
    "bluetooth": ["bluetooth", "hc-05", "hc05", "hc-06", "hc06", "ble"],
    "driver": ["driver", "l298n", "uln2003", "puente h"],
    "raspberry": ["raspberry", "raspberry pi", "rpi"],
    "bateria": ["bateria", "baterias", "pila", "pilas"],
    "porta_pila": ["porta pila", "porta pilas", "broche", "porta bateria", "clip bateria"],
    "bomba": ["bomba", "bombas", "bomba de agua", "bomba agua"],
    "regleta": ["regleta", "regletas", "tira de pines", "tira pines", "header"],
    "terminal": ["terminal", "terminales", "terminal block", "bloque terminal", "kf301"],
    "placa": ["placa", "placas", "placa perforada", "baquelita perforada", "placa universal"],
    "caja": ["caja", "cajas", "caja de paso", "caja paso", "caja pvc"],
}

COLORES = ["rojo", "rojos", "verde", "verdes", "azul", "azules", "amarillo", "amarillos", "amarrillo", "amarrillos", "blanco", "blancos", "rgb", "naranja", "naranjas", "violeta", "morado", "morados", "negro", "negros"]
TAMANOS_LED = ["3mm", "5mm", "8mm", "10mm", "smd", "0805", "1206"]
TIPOS_TRANSISTOR = ["npn", "pnp", "mosfet", "jfet"]
TIPOS_DIODOS = ["rectificador", "zener", "schottky", "led", "puente"]
TIPOS_MOTOR = ["dc", "servo", "paso a paso", "stepper"]
TIPOS_SENSOR = ["temperatura", "humedad", "distancia", "luz", "movimiento", "proximidad", "ultrasonico", "pir", "dht11", "dht22", "lm35", "ds18b20"]

# Descriptores adicionales que enriquecen la busqueda
DESCRIPCIONES_EXTRA = {
    "modulo", "módulo", "pack", "kit", "set",
    "electrolitico", "electrolítico", "ceramico", "cerámico", "poliester", "poliéster",
    "tantalio", "smd", "dip", "tht", "through-hole",
    "universal", "perforada", "baquelita",
    "sumergible", "periferica", "periférica", "brushless",
    "optoacoplado", "estado solido", "estado sólido",
    "rango", "laser", "láser", "tof", "infrarrojo", "ultrasonico", "ultrasónico",
    "nivel", "liquido", "líquido", "boya", "flotador",
    "micro", "mini", "usb", "datos",
    "dupont", "jumper",
    "pines", "pin", "puntos", "canales", "canal",
    "macho", "hembra", "tira", "regleta",
    "bloque", "block", "terminal",
    "caja", "paso", "pvc",
    "surtido", "surtida",
    "ac", "dc",
    "macho-hembra", "macho-macho", "hembra-hembra", "macho hembra", "macho macho",
    "pequeno", "pequena", "grande", "mediano",
    "5v", "12v", "3v", "3.3v", "24v", "9v", "220v",
    "330", "220", "470", "1k", "10k", "100k", "1m",
    "ohm", "ohms", "kohm", "kohms", "mohm",
    "activo", "pasivo",
    "2 pines", "4 pines", "2 pin", "4 pin",
    "cristal", "oscilador",
}

# Defaults automáticos basados en las preguntas frecuentes de la tienda.
# Se aplican ANTES de marcar como ambigüedad. Si el campo tiene default,
# no genera pregunta.
DEFAULTS_POR_TIPO: dict[str, dict] = {
    "resistencia": {"valor": "220", "unidad": "ohm", "potencia": "1/4W"},
    "capacitor": {"valor": "100", "unidad": "uF"},
    "led": {"color": "rojo", "tamano": "5mm"},
    "arduino": {"modelo": "UNO R3"},
    "protoboard": {"puntos": "830"},
    "cable": {"tipo": "macho-macho"},
    "fuente": {"voltaje": "9V", "tipo": "DC jack+"},
    "pulsador": {"tipo": "push"},
    "buzzer": {"tipo": "activo"},
    "rele": {"voltaje": "5V"},
    "potenciometro": {"valor": "10k", "unidad": "ohm"},
    "display": {"tipo": "LCD 16x2"},
    "wifi": {"modelo": "ESP8266"},
    "bluetooth": {"modelo": "HC-05"},
    "raspberry": {"modelo": "Raspberry Pi 4"},
    "driver": {"modelo": "L298N"},
}

# Campos que requieren pregunta del usuario (NO tienen default automático)
CAMPOS_PREGUNTA: dict[str, list[str]] = {
    "sensor": ["tipo_o_modelo"],
    "motor": ["tipo_o_modelo"],
    "transistor": ["tipo_o_modelo"],
    "diodo": ["tipo_o_modelo"],
    "integrado": ["tipo_o_modelo"],
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


def aplicar_defaults(tipo: str, texto: str, comp: dict) -> dict:
    """Aplica defaults automáticos al componente según su tipo.

    Basado en las preguntas frecuentes de AV Electronics:
    - Resistencias sin valor → 220Ω 1/4W (más común para LEDs)
    - LEDs sin color/tamaño → 5mm rojo (estándar más vendido)
    - Arduino sin modelo → UNO R3 (recomendado para principiantes)
    - Fuente sin voltaje → 9V DC jack+ (más común)
    - Protoboard sin tamaño → 830 puntos (estándar)
    - Cables sin tipo → Macho-Macho pack 40
    """
    defaults = DEFAULTS_POR_TIPO.get(tipo, {})
    for campo, val in defaults.items():
        if campo == "valor" and comp.get("valor") is None:
            comp["valor"] = val
            if "unidad" in defaults and comp.get("unidad") is None:
                comp["unidad"] = defaults["unidad"]
        elif campo == "color" and not any(c in texto for c in COLORES):
            comp["color"] = val
        elif campo == "tamano" and not any(t in texto for t in TAMANOS_LED):
            comp["tamano"] = val
        elif campo == "modelo" and comp.get("tipo_o_modelo") is None:
            comp["tipo_o_modelo"] = val
        elif campo == "tipo" and comp.get("tipo_o_modelo") is None:
            comp["tipo_o_modelo"] = val
        elif campo == "voltaje" and comp.get("valor") is None:
            comp["valor"] = val
        elif campo == "puntos" and comp.get("valor") is None:
            comp["valor"] = val
        elif comp.get(campo) is None:
            comp[campo] = val
    comp["auto_completado"] = bool(defaults)
    return comp


def detectar_ambiguedades(tipo: str, texto: str, valor: str | None) -> list[str]:
    """Detecta qué campos requieren pregunta del usuario.

    Solo se marcan como ambigüedad los campos que NO tienen default automático
    y que el cliente debe responder obligatoriamente (sensor, motor, transistor, etc.).
    """
    ambiguedades: list[str] = []

    if tipo == "desconocido":
        return ["tipo"]

    # Campos que requieren pregunta explícita (sin default)
    campos_pregunta = CAMPOS_PREGUNTA.get(tipo, [])
    for campo in campos_pregunta:
        if campo == "tipo_o_modelo":
            if tipo == "motor":
                tiene_tipo = any(o in texto for o in TIPOS_MOTOR)
                tiene_modelo = re.search(r"\b[a-z]{1,3}\d{3,5}[a-z]?\b", texto) is not None
                if not tiene_tipo and not tiene_modelo:
                    ambiguedades.append("tipo_o_modelo")
            elif tipo == "sensor":
                tiene_tipo = any(o in texto for o in TIPOS_SENSOR)
                tiene_modelo = re.search(r"\b[a-z]{1,3}\d{3,5}[a-z]?\b", texto) is not None
                if not tiene_tipo and not tiene_modelo:
                    ambiguedades.append("tipo_o_modelo")
            else:
                opciones = TIPOS_TRANSISTOR if tipo == "transistor" else TIPOS_DIODOS
                tiene_tipo = any(o in texto for o in opciones)
                tiene_modelo = re.search(r"\b[a-z]{1,3}\d{3,5}[a-z]?\b", texto) is not None
                if not tiene_tipo and not tiene_modelo:
                    ambiguedades.append("tipo_o_modelo")
        elif campo == "valor":
            if valor is None:
                ambiguedades.append("valor")

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
