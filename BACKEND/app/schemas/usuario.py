from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UsuarioCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)
    rol: str = Field(default="user", pattern="^(admin|user)$")


class UsuarioResponse(BaseModel):
    id: int
    username: str
    email: str
    rol: str
    activo: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UsuarioListResponse(BaseModel):
    total: int
    page: int
    limit: int
    usuarios: list[UsuarioResponse]


class PasswordChange(BaseModel):
    password: str = Field(min_length=6, max_length=100)


class ToggleActiveResponse(BaseModel):
    id: int
    username: str
    activo: bool
    message: str
