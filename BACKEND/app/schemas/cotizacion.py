from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class OpcionProveedor(BaseModel):
    tienda: str
    precio_base: float
    precio_con_margen: float
    margen_aplicado: float
    disponible: bool
    url: str | None = None
    es_propio: bool = False


class CotizacionItemResponse(BaseModel):
    id: int
    producto_nombre: str
    cantidad: int
    precio_unitario: Decimal
    proveedor: str
    margen_aplicado: Decimal
    subtotal: Decimal
    disponible: bool
    es_propio: bool = False
    seleccionado: bool = True
    opciones_proveedores: list[OpcionProveedor] = []

    model_config = {"from_attributes": True}


class CotizacionResponse(BaseModel):
    session_id: UUID
    cotizacion_id: int
    items: list[CotizacionItemResponse]
    total: Decimal
    estado: str
    fecha_creacion: datetime
    cliente_nombre: str | None = None
    cliente_correo: str | None = None
    cliente_celular: str | None = None
    envio_nombre: str | None = None
    envio_precio: Decimal | None = None

    model_config = {"from_attributes": True}


class CotizacionListItem(BaseModel):
    cotizacion_id: int
    session_id: UUID
    estado: str
    total: Decimal
    total_items: int
    fecha_creacion: datetime
    cliente_nombre: str | None = None
    usuario_nombre: str | None = None


class CotizacionListResponse(BaseModel):
    total: int
    page: int
    limit: int
    cotizaciones: list[CotizacionListItem]
