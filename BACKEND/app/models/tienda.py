from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Tienda(Base):
    __tablename__ = "tiendas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    url_base: Mapped[str] = mapped_column(Text, nullable=False)
    selectores: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    usa_javascript: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ttl_horas: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
