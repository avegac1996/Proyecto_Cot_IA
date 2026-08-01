from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BancoPregunta(Base):
    __tablename__ = "banco_preguntas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    categoria: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    pregunta: Mapped[str] = mapped_column(Text, nullable=False)
    campo_a_desambiguar: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prioridad: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
