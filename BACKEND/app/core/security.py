from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    # Temporal: sin hash ni encriptacion. Se agregara bcrypt al final del proyecto.
    return password


def verify_password(plain_password: str, stored_password: str) -> bool:
    # Temporal: comparacion directa. Se agregara bcrypt al final del proyecto.
    return plain_password == stored_password


def create_access_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
