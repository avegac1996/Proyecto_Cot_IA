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
    "foquito": ["led 5mm"],
    "foquitos": ["led 5mm"],
    "bombillo": ["led 5mm"],
    "bombilla": ["led 5mm"],
    "foco": ["led 5mm"],
    "tablita": ["protoboard 830"],
    "breadboard": ["protoboard 830"],
    "tabla de pruebas": ["protoboard 830"],
    "resistor": ["resistencia 220 ohm"],
    "resistores": ["resistencia 220 ohm"],
    "condensador": ["capacitor 100uf"],
    "eliminador": ["fuente 9v"],
    "cargador": ["fuente 9v"],
    "transformador": ["fuente 9v"],
    "adaptador": ["fuente 9v"],
    "jumper": ["cable macho-macho"],
    "jumpers": ["cable macho-macho"],
    "alambre": ["cable"],
    "boton": ["pulsador push"],
    "botón": ["pulsador push"],
    "switch": ["pulsador push"],
    "interruptor": ["pulsador push"],
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
