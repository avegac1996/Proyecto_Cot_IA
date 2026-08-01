from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.banco_preguntas import BancoPregunta
from app.models.sesion import Sesion
from app.models.usuario import Usuario
from app.schemas.preguntas import (
    PreguntasResponse,
    RespuestasRequest,
    RespuestasResponse,
)
from app.services.matching.normalizer import aplicar_respuestas
from app.services.preguntas.selector import seleccionar_preguntas

router = APIRouter(prefix="/preguntas", tags=["preguntas"])


async def _get_sesion(session_id: UUID, user: Usuario, db: AsyncSession) -> Sesion:
    result = await db.execute(select(Sesion).where(Sesion.id == session_id))
    sesion = result.scalar_one_or_none()
    if sesion is None or (sesion.usuario_id != user.id and user.rol != "admin"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SESSION_NOT_FOUND", "message": "Sesión no existe o expiró"},
        )
    return sesion


@router.get("/{session_id}", response_model=PreguntasResponse)
async def obtener_preguntas(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    sesion = await _get_sesion(session_id, user, db)
    preguntas = await seleccionar_preguntas(db, sesion.componentes_json)
    return PreguntasResponse(
        session_id=sesion.id,
        preguntas=preguntas,
        total_preguntas=len(preguntas),
    )


@router.post("/{session_id}/respuestas", response_model=RespuestasResponse)
async def enviar_respuestas(
    session_id: UUID,
    request: RespuestasRequest,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    sesion = await _get_sesion(session_id, user, db)

    # Reconstruir las preguntas para mapear pregunta_id → campo/componentes
    preguntas = await seleccionar_preguntas(db, sesion.componentes_json)
    preguntas_map = {p["id"]: p for p in preguntas}

    # Validar que las preguntas respondidas existen en el banco
    ids_validos = {p.id for p in (await db.execute(select(BancoPregunta))).scalars().all()}
    for resp in request.respuestas:
        if resp.pregunta_id not in ids_validos:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "VALIDATION_ERROR", "message": f"Pregunta {resp.pregunta_id} no existe"},
            )

    componentes = aplicar_respuestas(
        [dict(c) for c in sesion.componentes_json],
        [r.model_dump() for r in request.respuestas],
        preguntas_map,
    )

    sesion.componentes_json = componentes
    restantes = sum(len(c["ambiguedades"]) for c in componentes)
    sesion.ambiguedades_resueltas = restantes == 0
    await db.commit()

    return RespuestasResponse(
        session_id=sesion.id,
        componentes_actualizados=True,
        ambiguedades_restantes=restantes,
    )
