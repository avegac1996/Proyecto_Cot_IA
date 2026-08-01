from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.banco_preguntas import BancoPregunta


async def seleccionar_preguntas(
    db: AsyncSession, componentes: list[dict]
) -> list[dict]:
    """Selecciona preguntas del banco para las ambigüedades detectadas.

    Agrupa componentes que comparten el mismo campo faltante en una sola
    pregunta y limita el total a MAX_PREGUNTAS_SESION, priorizando las
    preguntas que desambigüen más componentes.
    """
    # Agrupar índices de componentes por campo faltante
    faltantes: dict[str, list[int]] = {}
    for idx, comp in enumerate(componentes):
        for campo in comp.get("ambiguedades", []):
            faltantes.setdefault(campo, []).append(idx)

    if not faltantes:
        return []

    result = await db.execute(
        select(BancoPregunta).where(BancoPregunta.activa.is_(True))
    )
    banco = result.scalars().all()

    preguntas: list[dict] = []
    campos_usados: set[str] = set()

    # Campos con más componentes afectados primero
    for campo, indices in sorted(faltantes.items(), key=lambda kv: -len(kv[1])):
        if len(preguntas) >= settings.MAX_PREGUNTAS_SESION:
            break
        candidatas = [p for p in banco if p.campo_a_desambiguar == campo]
        if not candidatas:
            continue
        candidatas.sort(key=lambda p: p.prioridad)
        pregunta = candidatas[0]
        preguntas.append({
            "id": pregunta.id,
            "categoria": pregunta.categoria,
            "pregunta": pregunta.pregunta,
            "campo_a_desambiguar": campo,
            "componentes_afectados": indices,
        })
        campos_usados.add(campo)

    return preguntas
