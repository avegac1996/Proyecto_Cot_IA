"""Ingesta de imagen: extrae texto de imágenes usando Tesseract OCR y parsea componentes."""

import logging

from app.services.ingesta.texto import parsear_texto

logger = logging.getLogger(__name__)


def extraer_texto_imagen(contenido_bytes: bytes) -> list[dict]:
    """Extrae texto de una imagen usando Tesseract OCR y parsea componentes.

    Args:
        contenido_bytes: bytes del archivo de imagen.

    Returns:
        Lista de componentes extraídos del texto OCR.
    """
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        logger.error("pytesseract o Pillow no están instalados.")
        raise RuntimeError("OCR no disponible. Instale pytesseract y Pillow.")

    try:
        import io

        image = Image.open(io.BytesIO(contenido_bytes))
        texto = pytesseract.image_to_string(image, lang="spa+eng")
        logger.info("OCR completado: %d caracteres", len(texto.strip()))

        if not texto.strip():
            return []

        return parsear_texto(texto)
    except Exception as exc:
        logger.error("Error en OCR: %s", exc)
        raise
