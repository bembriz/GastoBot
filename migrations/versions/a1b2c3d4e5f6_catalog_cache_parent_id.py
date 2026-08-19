"""catalog_cache_parent_id

Revision ID: a1b2c3d4e5f6
Revises: 3cdc35b3c310
Create Date: 2026-08-19 00:10:00.000000

La columna parent_id (jerarquia de catalogos) se agrego a los modelos y a la
base de produccion de forma manual, sin migracion. Esta revision alinea el
esquema: usa IF NOT EXISTS para ser no-op en produccion (donde ya existe) y
crear la columna en bases nuevas (p. ej. gastos_ia_test).

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "3cdc35b3c310"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "ALTER TABLE catalog_cache "
        "ADD COLUMN IF NOT EXISTS parent_id UUID "
        "REFERENCES catalog_cache(id) ON DELETE SET NULL"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE catalog_cache DROP COLUMN IF EXISTS parent_id")
