"""Servicio para leer y actualizar la configuración de negocio desde BD."""

from decimal import Decimal

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
