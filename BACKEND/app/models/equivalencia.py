from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Equivalencia(Base):
    __tablename__ = "equivalencias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"), nullable=False)
    termino_equivalente: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    tipo_match: Mapped[str] = mapped_column(String(50), nullable=False)
    confianza: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
