from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class CotizacionItemResponse(BaseModel):
    id: int
    producto_nombre: str
    cantidad: int
    precio_unitario: Decimal
    proveedor: str
    margen_aplicado: Decimal
    subtotal: Decimal
    disponible: bool

    model_config = {"from_attributes": True}


class CotizacionResponse(BaseModel):
    session_id: UUID
    cotizacion_id: int
    items: list[CotizacionItemResponse]
    total: Decimal
    estado: str
    fecha_creacion: datetime

    model_config = {"from_attributes": True}


class CotizacionListItem(BaseModel):
    cotizacion_id: int
    session_id: UUID
    estado: str
    total: Decimal
    total_items: int
    fecha_creacion: datetime


class CotizacionListResponse(BaseModel):
    total: int
    page: int
    limit: int
    cotizaciones: list[CotizacionListItem]
