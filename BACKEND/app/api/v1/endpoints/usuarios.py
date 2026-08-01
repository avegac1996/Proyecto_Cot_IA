from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_db
from app.core.security import hash_password
from app.models.usuario import Usuario
from app.schemas.usuario import (
    PasswordChange,
    ToggleActiveResponse,
    UsuarioCreate,
    UsuarioListResponse,
    UsuarioResponse,
)

router = APIRouter(
    prefix="/usuarios",
    tags=["usuarios"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=UsuarioListResponse)
async def list_usuarios(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    total_result = await db.execute(select(func.count(Usuario.id)))
    total = total_result.scalar_one()

    result = await db.execute(
        select(Usuario)
        .order_by(Usuario.id)
        .offset((page - 1) * limit)
        .limit(limit)
    )
    usuarios = result.scalars().all()

    return UsuarioListResponse(total=total, page=page, limit=limit, usuarios=usuarios)


@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def create_usuario(request: UsuarioCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Usuario).where(Usuario.username == request.username))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "USERNAME_EXISTS", "message": "El nombre de usuario ya existe"},
        )

    result = await db.execute(select(Usuario).where(Usuario.email == request.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "EMAIL_EXISTS", "message": "El email ya está registrado"},
        )

    usuario = Usuario(
        username=request.username,
        email=request.email,
        password_hash=hash_password(request.password),
        rol=request.rol,
        activo=True,
    )
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)
    return usuario


async def _get_usuario_or_404(usuario_id: int, db: AsyncSession) -> Usuario:
    result = await db.execute(select(Usuario).where(Usuario.id == usuario_id))
    usuario = result.scalar_one_or_none()
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "Usuario no encontrado"},
        )
    return usuario


@router.patch("/{usuario_id}/toggle-active", response_model=ToggleActiveResponse)
async def toggle_active(
    usuario_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    usuario = await _get_usuario_or_404(usuario_id, db)

    if usuario.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CANNOT_TOGGLE_SELF", "message": "No puedes desactivar tu propio usuario"},
        )

    usuario.activo = not usuario.activo
    await db.commit()

    message = "Usuario activado" if usuario.activo else "Usuario desactivado"
    return ToggleActiveResponse(
        id=usuario.id,
        username=usuario.username,
        activo=usuario.activo,
        message=message,
    )


@router.patch("/{usuario_id}/password", response_model=UsuarioResponse)
async def change_password(
    usuario_id: int,
    request: PasswordChange,
    db: AsyncSession = Depends(get_db),
):
    usuario = await _get_usuario_or_404(usuario_id, db)
    usuario.password_hash = hash_password(request.password)
    await db.commit()
    await db.refresh(usuario)
    return usuario
