"""Servicio para responder preguntas sobre componentes electrónicos usando Gemini."""

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-flash-lite-latest"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

SYSTEM_PROMPT = (
    "Eres un asistente experto en electrónica que ayuda a los usuarios a entender "
    "los resultados de búsqueda de componentes electrónicos. "
    "El usuario ha buscado componentes y ha obtenido resultados de varias tiendas. "
    "SOLO puedes responder preguntas relacionadas con los componentes que aparecen "
    "en los resultados de búsqueda proporcionados, o con el término de búsqueda "
    "que el usuario ingresó si no se encontraron resultados. "
    "Puedes ayudar con: diferencias entre productos encontrados, recomendaciones "
    "basadas en los resultados, compatibilidad entre los componentes listados, "
    "explicaciones técnicas de los productos encontrados, comparaciones de precios "
    "entre las opciones disponibles, y cualquier duda sobre los componentes de la búsqueda. "
    "Si no se encontraron resultados, puedes ayudar al usuario a reformular su búsqueda, "
    "sugerir términos alternativos, o explicar qué tipo de componente podría estar buscando. "
    "Si la pregunta no está relacionada con los componentes de los resultados o el término "
    "de búsqueda, responde amablemente que solo puedes ayudar con preguntas sobre los "
    "componentes que el usuario buscó."
)


def _build_context(resultados: list[dict]) -> str:
    """Construye un texto con el contexto de los resultados de búsqueda."""
    if not resultados:
        return "No se realizó ninguna búsqueda aún."

    lines = ["Resultados de búsqueda actuales:"]
    sin_resultados = []
    for r in resultados:
        termino = r.get("termino", "")
        cantidad = r.get("cantidad", 1)
        opciones = r.get("opciones", [])
        lines.append(f"\n- Componente: {termino} (cantidad: {cantidad})")
        if not opciones:
            lines.append("  Sin opciones encontradas.")
            sin_resultados.append(termino)
        for op in opciones:
            tienda = op.get("tienda", "")
            nombre = op.get("nombre_producto", "")
            precio = op.get("precio_con_margen")
            disponible = op.get("disponible", True)
            precio_str = f"${precio:.2f}" if precio is not None else "Precio no disponible"
            disp_str = "Disponible" if disponible else "Agotado"
            propio = " (AV Electronics)" if op.get("es_propio") else ""
            lines.append(f"  · {nombre} - {tienda}{propio} - {precio_str} - {disp_str}")

    if sin_resultados:
        lines.append(f"\nComponentes sin resultados encontrados: {', '.join(sin_resultados)}")
        lines.append("El usuario puede tener dudas sobre estos componentes que no se encontraron.")

    return "\n".join(lines)


async def preguntar_agente(
    pregunta: str,
    resultados: list[dict],
    historial: list[dict] | None = None,
) -> str:
    """Envía una pregunta a Gemini con el contexto de los resultados.

    Args:
        pregunta: pregunta del usuario
        resultados: resultados de búsqueda actuales
        historial: historial de mensajes previos (opcional)

    Returns:
        Respuesta del agente.
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY no configurada")

    contexto = _build_context(resultados)

    contents = []

    # Mensaje del sistema como primer mensaje
    contents.append({
        "role": "user",
        "parts": [{"text": f"{SYSTEM_PROMPT}\n\n{contexto}"}],
    })
    contents.append({
        "role": "model",
        "parts": [{"text": "Entendido. Estoy listo para responder tus preguntas sobre los componentes encontrados."}],
    })

    # Historial previo
    if historial:
        for msg in historial[-6:]:
            role = "user" if msg.get("role") == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.get("content", "")}],
            })

    # Pregunta actual
    contents.append({
        "role": "user",
        "parts": [{"text": pregunta}],
    })

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 1024,
        },
    }

    headers = {"Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            GEMINI_URL,
            json=payload,
            headers=headers,
            params={"key": settings.GEMINI_API_KEY},
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
    logger.info("Gemini chat response: %s", text[:200])
    return text
