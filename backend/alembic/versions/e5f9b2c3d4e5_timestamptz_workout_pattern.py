"""TIMESTAMPTZ for workout and pattern timestamps

Revision ID: e5f9b2c3d4e5
Revises: d4e8a1b2c3d4
Create Date: 2026-02-10

Alters started_at, completed_at, last_performed to TIMESTAMP WITH TIME ZONE
so timezone-aware datetimes from the API can be stored without asyncpg errors.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e5f9b2c3d4e5"
down_revision: Union[str, Sequence[str], None] = "d4e8a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Alter timestamp columns to TIMESTAMP WITH TIME ZONE (TIMESTAMPTZ)."""
    op.alter_column(
        "workoutsession",
        "started_at",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
    )
    op.alter_column(
        "workoutsession",
        "completed_at",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
    )
    op.alter_column(
        "patterninventory",
        "last_performed",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Revert timestamp columns to TIMESTAMP WITHOUT TIME ZONE."""
    op.alter_column(
        "workoutsession",
        "started_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=False,
    )
    op.alter_column(
        "workoutsession",
        "completed_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=False,
    )
    op.alter_column(
        "patterninventory",
        "last_performed",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=False,
    )
