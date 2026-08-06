"""Servicio para identificar componentes electrónicos con Google Gemini Vision."""

import base64
import logging

import httpx

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-flash-lite-latest"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

PROMPT = (
    "Eres un experto en electrónica. Analiza esta imagen e identifica TODOS los "
    "componentes electrónicos que veas. Responde SOLO con una lista, un producto "
    "por línea, en este formato: 'cantidad nombre_del_producto'. "
    "Ejemplo:\n"
    "3 Arduino Uno R3\n"
    "2 Sensor HC-SR04\n"
    "1 Motor DC 6V\n"
    "Si no reconoces algo, inclúyelo con '1' como cantidad. "
    "No agregues explicaciones, solo la lista."
)


async def identificar_componentes_imagen(image_bytes: bytes, mime_type: str, api_key: str) -> str:
    """Envía una imagen a Gemini Vision y devuelve el texto identificado.

    Args:
        image_bytes: bytes de la imagen
        mime_type: tipo MIME de la imagen (image/jpeg, image/png, etc.)

    Returns:
        Texto con los componentes identificados, una línea por producto.
    """
    if not api_key:
        raise ValueError("GEMINI_API_KEY no configurada")

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": PROMPT},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_b64,
                        }
                    },
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 1024,
        },
    }

    headers = {"Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            GEMINI_URL,
            json=payload,
            headers=headers,
            params={"key": api_key},
        )

    if response.status_code != 200:
        logger.error("Gemini API error %d: %s", response.status_code, response.text[:500])
        raise ValueError(f"Gemini API error: {response.status_code}")

    data = response.json()

    candidates = data.get("candidates", [])
    if not candidates:
        logger.warning("Gemini: no candidates in response")
        return ""

    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        return ""

    text = parts[0].get("text", "").strip()
    logger.info("Gemini response: %s", text[:200])
    return text
