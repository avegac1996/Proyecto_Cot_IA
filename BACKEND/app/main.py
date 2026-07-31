from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.database import Base, async_session, engine
from app.core.security import hash_password
from app.models.usuario import Usuario


async def seed_default_users():
    """Crea los usuarios por defecto (admin y user) si no existen."""
    async with async_session() as db:
        # Admin
        result = await db.execute(select(Usuario).where(Usuario.username == "admin"))
        if result.scalar_one_or_none() is None:
            admin = Usuario(
                username="admin",
                email="admin@cotia.com",
                password_hash=hash_password("Admin123!"),
                rol="admin",
                activo=True,
            )
            db.add(admin)

        # User
        result = await db.execute(select(Usuario).where(Usuario.username == "user"))
        if result.scalar_one_or_none() is None:
            user = Usuario(
                username="user",
                email="user@cotia.com",
                password_hash=hash_password("User123!"),
                rol="user",
                activo=True,
            )
            db.add(user)

        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Seed de usuarios por defecto
    await seed_default_users()
    yield
    await engine.dispose()


app = FastAPI(
    title="CotIA API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api/v1")
