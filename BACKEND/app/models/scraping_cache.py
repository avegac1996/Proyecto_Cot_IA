from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ScrapingCache(Base):
    __tablename__ = "scraping_cache"
    __table_args__ = (
        Index("idx_scraping_cache_producto_tienda", "producto_id", "tienda"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    producto_id: Mapped[int | None] = mapped_column(ForeignKey("productos.id"), nullable=True)
    tienda: Mapped[str] = mapped_column(String(100), nullable=False)
    termino_normalizado: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nombre_producto: Mapped[str | None] = mapped_column(String(255), nullable=True)
    variantes: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    precio: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    disponible: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    url_producto: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha_consulta: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    ttl_horas: Mapped[int | None] = mapped_column(Integer, nullable=True)
