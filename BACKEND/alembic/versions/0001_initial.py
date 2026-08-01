"""Initial schema - all tables.

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # usuarios
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("rol", sa.String(20), nullable=False, server_default="user"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("fecha_actualizacion", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )

    # sesiones
    op.create_table(
        "sesiones",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("componentes_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("ambiguedades_resueltas", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("estado", sa.String(20), nullable=False, server_default="activa"),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("fecha_actualizacion", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # productos
    op.create_table(
        "productos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column("tipo", sa.String(50), nullable=False),
        sa.Column("valor", sa.String(100), nullable=True),
        sa.Column("unidad", sa.String(20), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # tiendas
    op.create_table(
        "tiendas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("url_base", sa.String(500), nullable=False),
        sa.Column("selectores", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("usa_javascript", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("ttl_horas", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nombre"),
    )

    # cotizaciones
    op.create_table(
        "cotizaciones",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("cliente_nombre", sa.String(255), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("fecha_actualizacion", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("estado", sa.String(20), nullable=False, server_default="pendiente"),
        sa.Column("total", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
    )
    op.create_index("ix_cotizaciones_usuario_id", "cotizaciones", ["usuario_id"])

    # cotizacion_items
    op.create_table(
        "cotizacion_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cotizacion_id", sa.Integer(), nullable=False),
        sa.Column("producto_id", sa.Integer(), nullable=True),
        sa.Column("producto_nombre", sa.String(255), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("precio_unitario", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("proveedor", sa.String(100), nullable=False, server_default=""),
        sa.Column("margen_aplicado", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("disponible", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["cotizacion_id"], ["cotizaciones.id"]),
        sa.ForeignKeyConstraint(["producto_id"], ["productos.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # preguntas
    op.create_table(
        "preguntas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("categoria", sa.String(50), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("campo_relacionado", sa.String(50), nullable=True),
        sa.Column("prioridad", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id"),
    )

    # scraping_cache
    op.create_table(
        "scraping_cache",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("producto_id", sa.Integer(), nullable=False),
        sa.Column("tienda_id", sa.Integer(), nullable=False),
        sa.Column("precio", sa.Numeric(10, 2), nullable=True),
        sa.Column("disponible", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("url_producto", sa.String(500), nullable=True),
        sa.Column("fecha_consulta", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ttl_horas", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["producto_id"], ["productos.id"]),
        sa.ForeignKeyConstraint(["tienda_id"], ["tiendas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scraping_cache_producto_tienda", "scraping_cache", ["producto_id", "tienda_id"])


def downgrade() -> None:
    op.drop_table("scraping_cache")
    op.drop_table("preguntas")
    op.drop_table("cotizacion_items")
    op.drop_index("ix_cotizaciones_usuario_id", table_name="cotizaciones")
    op.drop_table("cotizaciones")
    op.drop_table("tiendas")
    op.drop_table("productos")
    op.drop_table("sesiones")
    op.drop_table("usuarios")
