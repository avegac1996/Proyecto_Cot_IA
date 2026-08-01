from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.producto import Producto
from app.models.usuario import Usuario
from app.schemas.producto import ProductoResponse, ProductoSearchResponse

router = APIRouter(prefix="/productos", tags=["productos"])


@router.get("", response_model=ProductoSearchResponse)
async def buscar_productos(
    query: str = Query(default=""),
    categoria: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    stmt = select(Producto).where(Producto.activo.is_(True))

    if categoria:
        stmt = stmt.where(Producto.categoria == categoria)
    if query:
        patron = f"%{query}%"
        stmt = stmt.where(
            or_(
                Producto.nombre.ilike(patron),
                Producto.categoria.ilike(patron),
            )
        )

    result = await db.execute(stmt.order_by(Producto.nombre).limit(50))
    productos = result.scalars().all()
    return ProductoSearchResponse(resultados=productos, total=len(productos))


@router.get("/{producto_id}", response_model=ProductoResponse)
async def detalle_producto(
    producto_id: int,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    result = await db.execute(select(Producto).where(Producto.id == producto_id))
    producto = result.scalar_one_or_none()
    if producto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PRODUCT_NOT_FOUND", "message": "Producto no encontrado"},
        )
    return producto
