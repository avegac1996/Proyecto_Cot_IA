"""Add favorite-store priority and persistent cache by search term.

Revision ID: 0003_store_favorite_and_search_cache
Revises: 0002_align_current_models
Create Date: 2026-08-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0003_store_cache"
down_revision: Union[str, None] = "0002_align_current_models"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tiendas",
        sa.Column("es_favorita", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.alter_column("scraping_cache", "producto_id", existing_type=sa.Integer(), nullable=True)
    op.add_column("scraping_cache", sa.Column("termino_normalizado", sa.String(length=255), nullable=True))
    op.add_column("scraping_cache", sa.Column("nombre_producto", sa.String(length=255), nullable=True))
    op.add_column("scraping_cache", sa.Column("variantes", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.create_index(
        "ix_scraping_cache_termino_tienda",
        "scraping_cache",
        ["termino_normalizado", "tienda"],
    )


def downgrade() -> None:
    op.drop_index("ix_scraping_cache_termino_tienda", table_name="scraping_cache")
    op.drop_column("scraping_cache", "variantes")
    op.drop_column("scraping_cache", "nombre_producto")
    op.drop_column("scraping_cache", "termino_normalizado")
    op.alter_column("scraping_cache", "producto_id", existing_type=sa.Integer(), nullable=False)
    op.drop_column("tiendas", "es_favorita")
