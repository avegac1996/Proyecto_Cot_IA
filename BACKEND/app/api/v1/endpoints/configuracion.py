from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.core.database import get_db
from app.models.usuario import Usuario
from app.services.configuracion import actualizar_margen, obtener_margen, obtener_tienda_propia

router = APIRouter(prefix="/configuracion", tags=["configuracion"])


class ConfiguracionResponse(BaseModel):
    margen_competencia: float
    tienda_propia: str


class ActualizarMargenRequest(BaseModel):
    margen: float


@router.get("", response_model=ConfiguracionResponse)
async def obtener_configuracion(
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    margen = await obtener_margen(db)
    tienda = await obtener_tienda_propia(db)
    return ConfiguracionResponse(
        margen_competencia=margen,
        tienda_propia=tienda,
    )


@router.put("/margen", response_model=ConfiguracionResponse)
async def cambiar_margen(
    body: ActualizarMargenRequest,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_admin),
):
    if body.margen < 0 or body.margen > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_MARGIN",
                "message": "El margen debe estar entre 0 y 100",
            },
        )
    await actualizar_margen(db, body.margen)
    margen = await obtener_margen(db)
    tienda = await obtener_tienda_propia(db)
    return ConfiguracionResponse(
        margen_competencia=margen,
        tienda_propia=tienda,
    )
