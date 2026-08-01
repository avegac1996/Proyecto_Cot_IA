from fastapi import APIRouter

from app.api.v1.endpoints import auth, cotizacion, health, preguntas, productos, upload, usuarios

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(auth.router, tags=["auth"])
router.include_router(usuarios.router)
router.include_router(upload.router)
router.include_router(preguntas.router)
router.include_router(cotizacion.router)
router.include_router(productos.router)
