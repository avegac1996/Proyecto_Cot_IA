"""Búsqueda priorizada: AV Electronics primero, luego tiendas externas con margen."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.configuracion import obtener_margen, obtener_tienda_propia
from app.services.scraping.engine import buscar_por_termino
from app.services.scraping.sugerencias import sugerir_termino

logger = logging.getLogger(__name__)


async def buscar_por_termino_priorizado(
    db: AsyncSession, termino: str, cantidad: int = 1
) -> dict:
    """Busca un término en tiendas activas, priorizando AV Electronics.

    1. Busca en todas las tiendas activas.
    2. Si AV Electronics tiene resultados → opciones propias (sin margen).
    3. Otras tiendas → opciones con margen aplicado.
    4. Si no hay resultados, genera una sugerencia de término alternativo.
    """
    margen_pct = await obtener_margen(db)
    tienda_propia = await obtener_tienda_propia(db)
    margen_factor = 1 + margen_pct / 100

    resultado_raw = await buscar_por_termino(db, termino)
    opciones_raw = resultado_raw.get("opciones", [])

    opciones_propias = []
    opciones_externas = []

    for op in opciones_raw:
        if op["precio_base"] is None:
            continue
        if op["tienda"] == tienda_propia:
            opciones_propias.append({
                "tienda": op["tienda"],
                "nombre_producto": op["nombre_producto"],
                "precio_base": op["precio_base"],
                "precio_con_margen": round(op["precio_base"], 2),
                "margen_aplicado": 0.0,
                "disponible": op["disponible"],
                "url": op["url"],
                "es_propio": True,
            })
        else:
            precio_con_margen = round(op["precio_base"] * margen_factor, 2)
            opciones_externas.append({
                "tienda": op["tienda"],
                "nombre_producto": op["nombre_producto"],
                "precio_base": op["precio_base"],
                "precio_con_margen": precio_con_margen,
                "margen_aplicado": margen_pct,
                "disponible": op["disponible"],
                "url": op["url"],
                "es_propio": False,
            })

    # Ordenar: propias primero (por precio), luego externas (por precio con margen)
    opciones_propias.sort(key=lambda o: o["precio_con_margen"])
    opciones_externas.sort(key=lambda o: o["precio_con_margen"])

    todas_opciones = opciones_propias + opciones_externas

    # Si no hay resultados, generar sugerencia
    sugerencia = None
    if not todas_opciones:
        sugerencia = sugerir_termino(termino)

    return {
        "termino": termino,
        "cantidad": cantidad,
        "encontrado_propia": len(opciones_propias) > 0,
        "opciones": todas_opciones,
        "sugerencia": sugerencia,
    }
