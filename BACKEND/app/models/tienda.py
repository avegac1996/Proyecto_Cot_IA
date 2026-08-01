from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Tienda(Base):
    __tablename__ = "tiendas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    url_base: Mapped[str] = mapped_column(Text, nullable=False)
    selector_precio: Mapped[str | None] = mapped_column(Text, nullable=True)
    selector_disponibilidad: Mapped[str | None] = mapped_column(Text, nullable=True)
    selector_nombre: Mapped[str | None] = mapped_column(Text, nullable=True)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    usa_javascript: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
