from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Usuario).where(Usuario.email == request.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Email o contraseña incorrectos"},
        )

    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "USER_INACTIVE", "message": "Usuario desactivado. Contacte al administrador"},
        )

    token = create_access_token({"sub": str(user.id), "rol": user.rol})
    return TokenResponse(access_token=token, rol=user.rol, username=user.username)


@router.get("/me", response_model=UserResponse)
async def me(user: Usuario = Depends(get_current_user)):
    return user


@router.post("/refresh", response_model=TokenResponse)
async def refresh(user: Usuario = Depends(get_current_user)):
    token = create_access_token({"sub": str(user.id), "rol": user.rol})
    return TokenResponse(access_token=token, rol=user.rol, username=user.username)
