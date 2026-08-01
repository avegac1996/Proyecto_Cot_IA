import io
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.cotizacion import Cotizacion, CotizacionItem
from app.models.sesion import Sesion
from app.models.usuario import Usuario
from app.schemas.cotizacion import (
    CotizacionListItem,
    CotizacionListResponse,
    CotizacionResponse,
)
from app.services.cotizacion.exporter import generate_excel, generate_pdf
from app.services.cotizacion.generator import agregar_item_cotizacion, generar_cotizacion, recalcular_total
from app.services.preguntas.selector import seleccionar_preguntas

router = APIRouter(tags=["cotizacion"])


def _to_response(c: Cotizacion) -> CotizacionResponse:
    return CotizacionResponse(
        session_id=c.session_id,
        cotizacion_id=c.id,
        items=c.items,
        total=c.total,
        estado=c.estado,
        fecha_creacion=c.fecha_creacion,
    )


async def _get_sesion(session_id: UUID, user: Usuario, db: AsyncSession) -> Sesion:
    result = await db.execute(select(Sesion).where(Sesion.id == session_id))
    sesion = result.scalar_one_or_none()
    if sesion is None or (sesion.usuario_id != user.id and user.rol != "admin"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SESSION_NOT_FOUND", "message": "Sesión no existe o expiró"},
        )
    return sesion


@router.post("/cotizacion/{session_id}", response_model=CotizacionResponse, status_code=status.HTTP_201_CREATED)
async def crear_cotizacion(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    sesion = await _get_sesion(session_id, user, db)

    result = await db.execute(select(Cotizacion).where(Cotizacion.session_id == session_id))
    existente = result.scalar_one_or_none()
    if existente is not None:
        return _to_response(existente)

    preguntas_pendientes = await seleccionar_preguntas(db, sesion.componentes_json)
    if preguntas_pendientes:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "AMBIGUITIES_PENDING",
                "message": "Hay ambigüedades sin resolver. Responda las preguntas pendientes primero",
            },
        )

    cotizacion = await generar_cotizacion(db, sesion, user.id)
    return _to_response(cotizacion)


@router.get("/cotizacion/{session_id}", response_model=CotizacionResponse)
async def obtener_cotizacion(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    await _get_sesion(session_id, user, db)
    result = await db.execute(select(Cotizacion).where(Cotizacion.session_id == session_id))
    cotizacion = result.scalar_one_or_none()
    if cotizacion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SESSION_NOT_FOUND", "message": "No existe cotización para esta sesión"},
        )
    return _to_response(cotizacion)


@router.get("/cotizaciones", response_model=CotizacionListResponse)
async def listar_cotizaciones(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    base = select(Cotizacion)
    if user.rol != "admin":
        base = base.where(Cotizacion.usuario_id == user.id)

    total_result = await db.execute(
        select(func.count()).select_from(base.subquery())
    )
    total = total_result.scalar_one()

    result = await db.execute(
        base.order_by(Cotizacion.fecha_creacion.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    cotizaciones = result.scalars().all()

    return CotizacionListResponse(
        total=total,
        page=page,
        limit=limit,
        cotizaciones=[
            CotizacionListItem(
                cotizacion_id=c.id,
                session_id=c.session_id,
                estado=c.estado,
                total=c.total,
                total_items=len(c.items),
                fecha_creacion=c.fecha_creacion,
            )
            for c in cotizaciones
        ],
    )


async def _get_cotizacion_by_id(cotizacion_id: int, user: Usuario, db: AsyncSession) -> Cotizacion:
    result = await db.execute(select(Cotizacion).where(Cotizacion.id == cotizacion_id))
    cotizacion = result.scalar_one_or_none()
    if cotizacion is None or (cotizacion.usuario_id != user.id and user.rol != "admin"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COTIZACION_NOT_FOUND", "message": "Cotización no encontrada"},
        )
    return cotizacion


@router.get("/cotizacion/{cotizacion_id}/pdf")
async def descargar_pdf(
    cotizacion_id: int,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    cotizacion = await _get_cotizacion_by_id(cotizacion_id, user, db)
    pdf_bytes = generate_pdf(cotizacion)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="cotizacion_{cotizacion_id}.pdf"'
        },
    )


@router.get("/cotizacion/{cotizacion_id}/excel")
async def descargar_excel(
    cotizacion_id: int,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    cotizacion = await _get_cotizacion_by_id(cotizacion_id, user, db)
    excel_bytes = generate_excel(cotizacion)
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="cotizacion_{cotizacion_id}.xlsx"'
        },
    )


class SeleccionarProveedorRequest(BaseModel):
    tienda: str


@router.put("/cotizacion/item/{item_id}/seleccionar", response_model=CotizacionResponse)
async def seleccionar_proveedor(
    item_id: int,
    body: SeleccionarProveedorRequest,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    """Permite al usuario seleccionar el proveedor de un item con múltiples opciones."""
    result = await db.execute(select(CotizacionItem).where(CotizacionItem.id == item_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ITEM_NOT_FOUND", "message": "Ítem no encontrado"},
        )

    result = await db.execute(select(Cotizacion).where(Cotizacion.id == item.cotizacion_id))
    cotizacion = result.scalar_one_or_none()
    if cotizacion is None or (cotizacion.usuario_id != user.id and user.rol != "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "No tiene permiso sobre esta cotización"},
        )

    if cotizacion.estado == "finalizada":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "COTIZACION_LOCKED", "message": "La cotización ya está finalizada"},
        )

    opciones = item.opciones_proveedores or []
    seleccionada = None
    for op in opciones:
        if op["tienda"] == body.tienda:
            seleccionada = op
            break

    if seleccionada is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "PROVEEDOR_NOT_AVAILABLE", "message": f"Proveedor '{body.tienda}' no disponible para este ítem"},
        )

    from decimal import Decimal

    item.proveedor = seleccionada["tienda"]
    item.precio_unitario = Decimal(str(seleccionada["precio_con_margen"])).quantize(Decimal("0.01"))
    item.margen_aplicado = Decimal(str(seleccionada["margen_aplicado"]))
    item.subtotal = (item.precio_unitario * item.cantidad).quantize(Decimal("0.01"))
    item.seleccionado = True

    recalcular_total(cotizacion)
    await db.commit()
    await db.refresh(cotizacion)
    return _to_response(cotizacion)


class AgregarItemRequest(BaseModel):
    texto: str


@router.post("/cotizacion/{cotizacion_id}/agregar", response_model=CotizacionResponse)
async def agregar_item_carrito(
    cotizacion_id: int,
    body: AgregarItemRequest,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    """Agrega un componente a una cotización existente (funcionalidad de carrito)."""
    cotizacion = await _get_cotizacion_by_id(cotizacion_id, user, db)

    if cotizacion.estado == "finalizada":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "COTIZACION_LOCKED", "message": "La cotización ya está finalizada"},
        )

    from app.services.ingesta.texto import parsear_linea

    comp = parsear_linea(body.texto)
    if not comp.get("tipo") or comp["tipo"] == "desconocido":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": "No se pudo identificar el componente"},
        )

    item = await agregar_item_cotizacion(db, cotizacion, comp)
    recalcular_total(cotizacion)
    await db.commit()
    await db.refresh(cotizacion)
    return _to_response(cotizacion)


@router.post("/cotizacion/{cotizacion_id}/finalizar", response_model=CotizacionResponse)
async def finalizar_cotizacion(
    cotizacion_id: int,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    """Finaliza la cotización, bloqueando ediciones posteriores."""
    cotizacion = await _get_cotizacion_by_id(cotizacion_id, user, db)

    if cotizacion.estado == "finalizada":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "COTIZACION_LOCKED", "message": "La cotización ya está finalizada"},
        )

    pendientes = [i for i in cotizacion.items if not i.seleccionado and i.disponible]
    if pendientes:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "PENDING_SELECTIONS",
                "message": f"Hay {len(pendientes)} ítem(s) sin proveedor seleccionado",
            },
        )

    cotizacion.estado = "finalizada"
    await db.commit()
    await db.refresh(cotizacion)
    return _to_response(cotizacion)
