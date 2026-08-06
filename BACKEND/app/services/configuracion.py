"""Servicio para leer y actualizar la configuración de negocio desde BD."""

from decimal import Decimal

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.configuracion import ConfiguracionNegocio


async def obtener_margen(db: AsyncSession) -> float:
    """Lee el margen de competencia desde BD.

    Fallback a settings.MARGEN_COMPETENCIA si no existe el registro.
    """
    result = await db.execute(
        select(ConfiguracionNegocio).where(
            ConfiguracionNegocio.clave == "margen_competencia"
        )
    )
    config = result.scalar_one_or_none()
    if config:
        try:
            return float(config.valor)
        except ValueError:
            pass
    return settings.MARGEN_COMPETENCIA


async def actualizar_margen(db: AsyncSession, valor: float) -> float:
    """Actualiza o crea el margen en BD. Retorna el valor guardado."""
    result = await db.execute(
        select(ConfiguracionNegocio).where(
            ConfiguracionNegocio.clave == "margen_competencia"
        )
    )
    config = result.scalar_one_or_none()
    if config:
        config.valor = str(valor)
    else:
        config = ConfiguracionNegocio(
            clave="margen_competencia",
            valor=str(valor),
            descripcion="Margen % aplicado a productos de tiendas externas",
        )
        db.add(config)
    await db.commit()
    return valor


async def obtener_tienda_propia(db: AsyncSession) -> str:
    """Lee el nombre de la tienda propia desde BD.

    Fallback a settings.TIENDA_PROPIA si no existe.
    """
    result = await db.execute(
        select(ConfiguracionNegocio).where(
            ConfiguracionNegocio.clave == "tienda_propia"
        )
    )
    config = result.scalar_one_or_none()
    if config:
        return config.valor
    return settings.TIENDA_PROPIA


async def obtener_iva(db: AsyncSession) -> float:
    """Lee el porcentaje de IVA desde BD. Fallback a 15% si no existe."""
    result = await db.execute(
        select(ConfiguracionNegocio).where(
            ConfiguracionNegocio.clave == "iva"
        )
    )
    config = result.scalar_one_or_none()
    if config:
        try:
            return float(config.valor)
        except ValueError:
            pass
    return 15.0


async def actualizar_iva(db: AsyncSession, valor: float) -> float:
    """Actualiza o crea el IVA en BD. Retorna el valor guardado."""
    result = await db.execute(
        select(ConfiguracionNegocio).where(
            ConfiguracionNegocio.clave == "iva"
        )
    )
    config = result.scalar_one_or_none()
    if config:
        config.valor = str(valor)
    else:
        config = ConfiguracionNegocio(
            clave="iva",
            valor=str(valor),
            descripcion="Porcentaje de IVA aplicado a las cotizaciones",
        )
        db.add(config)
    await db.commit()
    return valor


# --- Opciones de envío ---

OPCIONES_ENVIO_DEFAULT = [
    {"id": "recogida", "nombre": "Recogida local", "precio": 0.0},
    {"id": "servientrega_dmq", "nombre": "Servientrega - Quito DMQ y Valles", "precio": 3.0},
    {"id": "servientrega_rurales", "nombre": "Servientrega - Quito Parroquias Rurales", "precio": 5.4},
    {"id": "servientrega_provincias", "nombre": "Servientrega - Provincias", "precio": 6.0},
    {"id": "servientrega_lejanas", "nombre": "Servientrega - Samborondón, Oriente y Ciudades Lejanas", "precio": 7.1},
]


async def obtener_opciones_envio(db: AsyncSession) -> list[dict]:
    """Lee las opciones de envío desde BD. Fallback a defaults si no existe."""
    result = await db.execute(
        select(ConfiguracionNegocio).where(
            ConfiguracionNegocio.clave == "opciones_envio"
        )
    )
    config = result.scalar_one_or_none()
    if config:
        try:
            import json
            return json.loads(config.valor)
        except (json.JSONDecodeError, ValueError):
            pass
    return OPCIONES_ENVIO_DEFAULT


async def actualizar_opciones_envio(db: AsyncSession, opciones: list[dict]) -> list[dict]:
    """Actualiza o crea las opciones de envío en BD."""
    import json
    result = await db.execute(
        select(ConfiguracionNegocio).where(
            ConfiguracionNegocio.clave == "opciones_envio"
        )
    )
    config = result.scalar_one_or_none()
    valor = json.dumps(opciones)
    if config:
        config.valor = valor
    else:
        config = ConfiguracionNegocio(
            clave="opciones_envio",
            valor=valor,
            descripcion="Opciones de envío con precios configurables",
        )
        db.add(config)
    await db.commit()
    return opciones


# --- API Key de Gemini ---

GEMINI_KEY_PREFIX = "enc:v1:"


class GeminiKeyStorageError(RuntimeError):
    """La clave de Gemini almacenada no se puede usar de forma segura."""


def _get_gemini_fernet() -> Fernet:
    """Obtiene el cifrador con una clave maestra que nunca se guarda en la BD."""
    if not settings.GEMINI_KEY_ENCRYPTION_KEY:
        raise GeminiKeyStorageError(
            "Falta GEMINI_KEY_ENCRYPTION_KEY para usar una clave Gemini almacenada en la base de datos"
        )
    try:
        return Fernet(settings.GEMINI_KEY_ENCRYPTION_KEY.encode())
    except (ValueError, TypeError) as exc:
        raise GeminiKeyStorageError("GEMINI_KEY_ENCRYPTION_KEY no tiene formato Fernet válido") from exc


def _encrypt_gemini_key(value: str) -> str:
    return GEMINI_KEY_PREFIX + _get_gemini_fernet().encrypt(value.encode()).decode()


def _decrypt_gemini_key(value: str) -> str:
    if not value.startswith(GEMINI_KEY_PREFIX):
        raise GeminiKeyStorageError(
            "La clave Gemini existente no está cifrada. Configure GEMINI_KEY_ENCRYPTION_KEY y guárdela nuevamente"
        )
    try:
        return _get_gemini_fernet().decrypt(value[len(GEMINI_KEY_PREFIX):].encode()).decode()
    except InvalidToken as exc:
        raise GeminiKeyStorageError("No se pudo descifrar la clave Gemini almacenada") from exc

async def obtener_gemini_api_key(db: AsyncSession) -> str:
    """Obtiene la clave efectiva: BD cifrada primero y entorno como respaldo."""
    result = await db.execute(
        select(ConfiguracionNegocio).where(
            ConfiguracionNegocio.clave == "gemini_api_key"
        )
    )
    config = result.scalar_one_or_none()
    if config and config.valor:
        return _decrypt_gemini_key(config.valor)
    return settings.GEMINI_API_KEY


async def actualizar_gemini_api_key(db: AsyncSession, valor: str) -> str:
    """Cifra y almacena la API key de Gemini en la BD."""
    result = await db.execute(
        select(ConfiguracionNegocio).where(
            ConfiguracionNegocio.clave == "gemini_api_key"
        )
    )
    config = result.scalar_one_or_none()
    valor_cifrado = _encrypt_gemini_key(valor)
    if config:
        config.valor = valor_cifrado
    else:
        config = ConfiguracionNegocio(
            clave="gemini_api_key",
            valor=valor_cifrado,
            descripcion="API key cifrada para Google Gemini (Vision y Chat)",
        )
        db.add(config)
    await db.commit()
    return valor
