from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CatalogoProducto(Base):
    __tablename__ = "catalogo_productos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tienda: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    nombre_normalizado: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    precio: Mapped[float | None] = mapped_column(Float, nullable=True)
    disponible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    variantes: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    url_base: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    producto_id_wc: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actualizado: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
