import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Cotizacion(Base):
    __tablename__ = "cotizaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    cliente_nombre: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    fecha_actualizacion: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    estado: Mapped[str] = mapped_column(String(20), default="pendiente", nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)

    items: Mapped[list["CotizacionItem"]] = relationship(
        back_populates="cotizacion", cascade="all, delete-orphan", lazy="selectin"
    )


class CotizacionItem(Base):
    __tablename__ = "cotizacion_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cotizacion_id: Mapped[int] = mapped_column(ForeignKey("cotizaciones.id"), nullable=False)
    producto_id: Mapped[int | None] = mapped_column(ForeignKey("productos.id"), nullable=True)
    producto_nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    proveedor: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    margen_aplicado: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    disponible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    es_propio: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    seleccionado: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    opciones_proveedores: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)

    cotizacion: Mapped["Cotizacion"] = relationship(back_populates="items")
