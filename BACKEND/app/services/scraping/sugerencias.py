"""Sugerencias para términos no encontrados en la búsqueda.

Si un término no se encuentra en ninguna tienda, se intenta:
1. Buscar sinónimos en TIPOS_PALABRAS.
2. Buscar por tipo genérico (ej: "sensor de temperatura" → "dht11", "lm35").
3. Retornar una sugerencia para preguntar al usuario.
"""

import re
import unicodedata

from app.services.matching.normalizer import TIPOS_PALABRAS, TIPOS_SENSOR


def _normalizar(texto: str) -> str:
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto


# Sinónimos inversos: término coloquial → término de búsqueda sugerido
SINONIMOS: dict[str, list[str]] = {
    "broche porta pila": ["portapilas 9v"],
    "porta bateria": ["portapilas 9v"],
    "porta pila": ["portapilas"],
    "porta pilas": ["portapilas"],
    "clip bateria": ["portapilas 9v"],
    "foquito": ["led 5mm"],
    "foquitos": ["led 5mm"],
    "bombillo": ["led 5mm"],
    "bombilla": ["led 5mm"],
    "foco": ["led 5mm"],
    "tablita": ["protoboard 830"],
    "breadboard": ["protoboard 830"],
    "tabla de pruebas": ["protoboard 830"],
    "condensador": ["capacitor 100uf"],
    "eliminador": ["fuente 9v"],
    "cargador": ["fuente 9v"],
    "transformador": ["fuente 9v"],
    "adaptador": ["fuente 9v"],
    "jumper": ["jumper"],
    "jumpers": ["jumper"],
    "alambre": ["cable"],
    "boton": ["pulsador"],
    "botón": ["pulsador"],
    "switch": ["pulsador"],
    "interruptor": ["pulsador"],
    "zumbador": ["buzzer activo"],
    "bocina": ["buzzer activo"],
    "speaker": ["buzzer activo"],
    "altavoz": ["buzzer activo"],
    "servo": ["servomotor sg90"],
    "servomotor": ["servomotor sg90"],
    "stepper": ["motor paso a paso 28byj48"],
    "paso a paso": ["motor paso a paso 28byj48"],
    "rele": ["modulo rele 5v"],
    "relé": ["modulo rele 5v"],
    "relay": ["modulo rele 5v"],
    "pot": ["potenciometro 10k"],
    "potenciometro": ["potenciometro 10k"],
    "potenciómetro": ["potenciometro 10k"],
    "pantalla": ["display lcd 16x2"],
    "lcd": ["display lcd 16x2"],
    "oled": ["display oled 0.96"],
    "7 segmentos": ["display 7 segmentos"],
    "wifi": ["esp8266"],
    "wi-fi": ["esp8266"],
    "internet": ["esp8266"],
    "bluetooth": ["hc-05"],
    "puente h": ["l298n"],
    "rpi": ["raspberry pi 4"],
}


def consultas_equivalentes_seguras(termino: str) -> list[str]:
    """Devuelve consultas equivalentes sin cambiar el tipo de producto.

    Estas equivalencias se pueden probar automáticamente: ``broche porta
    pila`` y ``portapilas`` nombran el mismo artículo. No incluye sugerencias
    genéricas como ``pila`` o ``batería``, que cambiarían el producto pedido.
    """
    termino_norm = _normalizar(termino)
    consultas: list[str] = []
    for clave, sugerencias in SINONIMOS.items():
        if clave in termino_norm:
            for sugerencia in sugerencias:
                if sugerencia not in consultas:
                    consultas.append(sugerencia)
    return consultas


def consultas_parciales_para_confirmar(termino: str) -> list[str]:
    """Busca por encapsulado cuando falta confirmar un valor eléctrico.

    No es una sustitución automática: permite encontrar una resistencia SMD
    del encapsulado pedido y la capa API la marca para confirmación del usuario.
    """
    termino_norm = _normalizar(termino).replace("ω", "ohm")
    match = re.search(r"\b(?:resistor|resistencia)\b.*?\b(0201|0402|0603|0805|1206|1210)\b", termino_norm)
    if not match:
        return []
    return [f"resistencia smd {match.group(1)}"]

# Mapeo de sensores específicos
SENSOR_SUGERENCIAS: dict[str, str] = {
    "temperatura": "dht11",
    "humedad": "dht11",
    "distancia": "hc-sr04",
    "luz": "ldr",
    "movimiento": "pir",
    "proximidad": "pir",
    "ultrasonico": "hc-sr04",
    "ultrasonido": "hc-sr04",
}


def sugerir_termino(termino: str) -> dict | None:
    """Intenta sugerir un término alternativo para una búsqueda sin resultados.

    Returns:
        dict con keys: sugerencia (str), razon (str) o None si no hay sugerencia.
    """
    termino_norm = _normalizar(termino)

    # 1. Buscar en sinónimos directos
    for clave, sugerencias in SINONIMOS.items():
        if clave in termino_norm:
            return {
                "sugerencia": sugerencias[0],
                "razon": f"'{termino}' es un sinónimo de '{sugerencias[0]}'",
            }

    # 2. Buscar por tipo en TIPOS_PALABRAS
    for tipo, palabras in TIPOS_PALABRAS.items():
        for palabra in palabras:
            if palabra in termino_norm:
                # Si es sensor, buscar subtipo
                if tipo == "sensor":
                    for subtipo, sugerencia in SENSOR_SUGERENCIAS.items():
                        if subtipo in termino_norm:
                            return {
                                "sugerencia": sugerencia,
                                "razon": f"Sensor de {subtipo} → modelo sugerido: {sugerencia}",
                            }
                # Sugerencia genérica del tipo
                return {
                    "sugerencia": palabras[0],
                    "razon": f"Tipo detectado: {tipo}",
                }

    return None
