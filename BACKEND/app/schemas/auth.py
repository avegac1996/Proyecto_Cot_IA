from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: str
    username: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    rol: str
    activo: bool

    model_config = {"from_attributes": True}
