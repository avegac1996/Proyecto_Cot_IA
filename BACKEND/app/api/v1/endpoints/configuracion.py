from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.core.database import get_db
from app.core.security import verify_password
from app.models.usuario import Usuario
from app.services.configuracion import actualizar_margen, actualizar_iva, obtener_margen, obtener_iva, obtener_tienda_propia, obtener_opciones_envio, actualizar_opciones_envio, obtener_gemini_api_key, actualizar_gemini_api_key

router = APIRouter(prefix="/configuracion", tags=["configuracion"])


class ConfiguracionResponse(BaseModel):
    margen_competencia: float
    tienda_propia: str
    iva: float


class ActualizarMargenRequest(BaseModel):
    margen: float


class ActualizarIvaRequest(BaseModel):
    iva: float


class OpcionEnvio(BaseModel):
    id: str
    nombre: str
    precio: float


class ActualizarOpcionesEnvioRequest(BaseModel):
    opciones: list[OpcionEnvio]


class ActualizarGeminiKeyRequest(BaseModel):
    api_key: str


class VerificarPasswordRequest(BaseModel):
    password: str


def _mask_key(key: str) -> str:
    if not key or len(key) <= 10:
        return "*" * len(key) if key else ""
    return key[:6] + "*" * (len(key) - 10) + key[-4:]


@router.get("", response_model=ConfiguracionResponse)
async def obtener_configuracion(
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    margen = await obtener_margen(db)
    tienda = await obtener_tienda_propia(db)
    iva = await obtener_iva(db)
    return ConfiguracionResponse(
        margen_competencia=margen,
        tienda_propia=tienda,
        iva=iva,
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
    iva = await obtener_iva(db)
    return ConfiguracionResponse(
        margen_competencia=margen,
        tienda_propia=tienda,
        iva=iva,
    )


@router.put("/iva", response_model=ConfiguracionResponse)
async def cambiar_iva(
    body: ActualizarIvaRequest,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_admin),
):
    if body.iva < 0 or body.iva > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_IVA",
                "message": "El IVA debe estar entre 0 y 100",
            },
        )
    await actualizar_iva(db, body.iva)
    margen = await obtener_margen(db)
    tienda = await obtener_tienda_propia(db)
    iva = await obtener_iva(db)
    return ConfiguracionResponse(
        margen_competencia=margen,
        tienda_propia=tienda,
        iva=iva,
    )


@router.get("/envio", response_model=list[OpcionEnvio])
async def obtener_envio(
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    opciones = await obtener_opciones_envio(db)
    return opciones


@router.put("/envio", response_model=list[OpcionEnvio])
async def actualizar_envio(
    body: ActualizarOpcionesEnvioRequest,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_admin),
):
    opciones = [{"id": o.id, "nombre": o.nombre, "precio": o.precio} for o in body.opciones]
    return await actualizar_opciones_envio(db, opciones)


@router.get("/gemini-key")
async def obtener_gemini_key(
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_admin),
):
    key = await obtener_gemini_api_key(db)
    return {"api_key": _mask_key(key), "has_key": bool(key)}


@router.post("/gemini-key/revelar")
async def revelar_gemini_key(
    body: VerificarPasswordRequest,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_admin),
):
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "INVALID_PASSWORD", "message": "Contraseña incorrecta"},
        )
    key = await obtener_gemini_api_key(db)
    return {"api_key": key}


@router.put("/gemini-key")
async def actualizar_gemini_key(
    body: ActualizarGeminiKeyRequest,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_admin),
):
    if not body.api_key.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMPTY_KEY", "message": "La API key no puede estar vacía"},
        )
    key = await actualizar_gemini_api_key(db, body.api_key.strip())
    return {"api_key": key}
