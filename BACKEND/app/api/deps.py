from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.usuario import Usuario

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_INVALID", "message": "Token inválido o expirado"},
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_INVALID", "message": "Token malformado"},
        )
    result = await db.execute(select(Usuario).where(Usuario.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "USER_NOT_FOUND", "message": "Usuario no encontrado"},
        )
    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "USER_INACTIVE", "message": "Usuario desactivado"},
        )
    return user


async def require_admin(user: Usuario = Depends(get_current_user)) -> Usuario:
    if user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Se requiere rol de administrador"},
        )
    return user
