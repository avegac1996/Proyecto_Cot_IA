"""Ingesta de audio: transcribe audio a texto usando Whisper y luego parsea componentes."""

import logging
import os
import tempfile

from app.services.ingesta.texto import parsear_texto

logger = logging.getLogger(__name__)


def transcribir_audio(contenido_bytes: bytes, extension: str = ".wav") -> list[dict]:
    """Transcribe audio a texto usando Whisper y extrae componentes.

    Args:
        contenido_bytes: bytes del archivo de audio.
        extension: extensión del archivo (ej: .mp3, .wav).

    Returns:
        Lista de componentes extraídos del texto transcrito.
    """
    try:
        import whisper
    except ImportError:
        logger.error("Whisper no está instalado. Ejecutar: pip install openai-whisper")
        raise RuntimeError("Whisper no está disponible. Instale openai-whisper y ffmpeg.")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as tmp:
            tmp.write(contenido_bytes)
            tmp_path = tmp.name

        logger.info("Transcribiendo audio con Whisper (modelo 'base')...")
        model = whisper.load_model("base")
        result = model.transcribe(tmp_path, language="es")
        texto = result.get("text", "").strip()
        logger.info("Transcripción completada: %d caracteres", len(texto))

        if not texto:
            return []

        return parsear_texto(texto)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
