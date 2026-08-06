"""Align the initial schema with the SQLAlchemy models in use.

This migration preserves columns from the original prototype schema.  They are
not mapped anymore, but retaining them avoids data loss while deployments move
to the current model names and tables.

Revision ID: 0002_align_current_models
Revises: 0001_initial
Create Date: 2026-08-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0002_align_current_models"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Los modelos actuales usan created_at/updated_at; se conservan las fechas
    # previas y se copian sus valores históricos a las columnas nuevas.
    op.add_column("usuarios", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("usuarios", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.execute("UPDATE usuarios SET created_at = fecha_creacion, updated_at = fecha_actualizacion")
    op.create_index("ix_usuarios_username", "usuarios", ["username"])
    op.create_index("ix_usuarios_email", "usuarios", ["email"])

    op.add_column("sesiones", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("sesiones", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.execute("UPDATE sesiones SET created_at = fecha_creacion, updated_at = fecha_actualizacion")
    op.create_index("ix_sesiones_usuario_id", "sesiones", ["usuario_id"])

    # productos pasó de tipo/valor/unidad al catálogo por categoría y JSONB.
    op.alter_column("productos", "tipo", existing_type=sa.String(length=50), nullable=True)
    op.add_column(
        "productos",
        sa.Column("categoria", sa.String(length=100), nullable=False, server_default="general"),
    )
    op.add_column(
        "productos",
        sa.Column(
            "especificaciones",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        "productos",
        sa.Column("terminos_coloquiales", postgresql.ARRAY(sa.String()), nullable=True),
    )
    op.add_column(
        "productos",
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column("productos", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("productos", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.execute("UPDATE productos SET categoria = COALESCE(tipo, 'general'), created_at = fecha_creacion")
    op.create_index("ix_productos_nombre", "productos", ["nombre"])
    op.create_index("ix_productos_categoria", "productos", ["categoria"])

    # Datos adicionales de cotización usados por carrito, envío y exportación.
    op.add_column("cotizaciones", sa.Column("cliente_correo", sa.String(length=255), nullable=True))
    op.add_column("cotizaciones", sa.Column("cliente_celular", sa.String(length=50), nullable=True))
    op.add_column("cotizaciones", sa.Column("envio_nombre", sa.String(length=255), nullable=True))
    op.add_column("cotizaciones", sa.Column("envio_precio", sa.Numeric(10, 2), nullable=True))

    op.create_table(
        "banco_preguntas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("categoria", sa.String(length=100), nullable=False),
        sa.Column("pregunta", sa.Text(), nullable=False),
        sa.Column("campo_a_desambiguar", sa.String(length=100), nullable=True),
        sa.Column("prioridad", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_banco_preguntas_categoria", "banco_preguntas", ["categoria"])

    op.create_table(
        "equivalencias",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("producto_id", sa.Integer(), nullable=False),
        sa.Column("termino_equivalente", sa.String(length=255), nullable=False),
        sa.Column("tipo_match", sa.String(length=50), nullable=False),
        sa.Column("confianza", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["producto_id"], ["productos.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_equivalencias_termino_equivalente", "equivalencias", ["termino_equivalente"])

    op.create_table(
        "configuracion_negocio",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("clave", sa.String(length=50), nullable=False),
        sa.Column("valor", sa.String(length=255), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("fecha_actualizacion", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clave"),
    )
    op.create_index("ix_configuracion_negocio_clave", "configuracion_negocio", ["clave"])

    # La caché ahora identifica la tienda por nombre. Se completa desde la FK
    # previa antes de exigir el nuevo campo.
    op.add_column("scraping_cache", sa.Column("tienda", sa.String(length=100), nullable=True))
    op.execute(
        "UPDATE scraping_cache AS cache "
        "SET tienda = tiendas.nombre "
        "FROM tiendas WHERE cache.tienda_id = tiendas.id"
    )
    op.alter_column("scraping_cache", "tienda", existing_type=sa.String(length=100), nullable=False)
    op.create_index("idx_scraping_cache_producto_tienda", "scraping_cache", ["producto_id", "tienda"])


def downgrade() -> None:
    op.drop_index("idx_scraping_cache_producto_tienda", table_name="scraping_cache")
    op.drop_column("scraping_cache", "tienda")

    op.drop_index("ix_configuracion_negocio_clave", table_name="configuracion_negocio")
    op.drop_table("configuracion_negocio")
    op.drop_index("ix_equivalencias_termino_equivalente", table_name="equivalencias")
    op.drop_table("equivalencias")
    op.drop_index("ix_banco_preguntas_categoria", table_name="banco_preguntas")
    op.drop_table("banco_preguntas")

    op.drop_column("cotizaciones", "envio_precio")
    op.drop_column("cotizaciones", "envio_nombre")
    op.drop_column("cotizaciones", "cliente_celular")
    op.drop_column("cotizaciones", "cliente_correo")

    op.drop_index("ix_productos_categoria", table_name="productos")
    op.drop_index("ix_productos_nombre", table_name="productos")
    op.drop_column("productos", "updated_at")
    op.drop_column("productos", "created_at")
    op.drop_column("productos", "activo")
    op.drop_column("productos", "terminos_coloquiales")
    op.drop_column("productos", "especificaciones")
    op.drop_column("productos", "categoria")
    op.alter_column("productos", "tipo", existing_type=sa.String(length=50), nullable=False)

    op.drop_index("ix_sesiones_usuario_id", table_name="sesiones")
    op.drop_column("sesiones", "updated_at")
    op.drop_column("sesiones", "created_at")
    op.drop_index("ix_usuarios_email", table_name="usuarios")
    op.drop_index("ix_usuarios_username", table_name="usuarios")
    op.drop_column("usuarios", "updated_at")
    op.drop_column("usuarios", "created_at")
