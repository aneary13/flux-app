"""Complete Workout schema: PatternInventory, WorkoutSession/WorkoutSet UUID schema

Revision ID: d4e8a1b2c3d4
Revises: c3b95ff3bdbf
Create Date: 2026-02-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4e8a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "c3b95ff3bdbf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: drop old workout tables, add PatternInventory and new session/set tables."""
    op.drop_table("workoutset")
    op.drop_index(op.f("ix_workoutsession_user_id"), table_name="workoutsession")
    op.drop_table("workoutsession")

    op.create_table(
        "patterninventory",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("pattern", sa.String(length=100), nullable=False),
        sa.Column("last_performed", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "pattern", name="uq_pattern_inventory_user_pattern"),
    )
    op.create_index(op.f("ix_patterninventory_user_id"), "patterninventory", ["user_id"], unique=False)
    op.create_index(op.f("ix_patterninventory_pattern"), "patterninventory", ["pattern"], unique=False)

    op.create_table(
        "workoutsession",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=False),
        sa.Column("readiness_score", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workoutsession_user_id"), "workoutsession", ["user_id"], unique=False)

    op.create_table(
        "workoutset",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("exercise_name", sa.String(length=255), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("reps", sa.Integer(), nullable=False),
        sa.Column("rpe", sa.Float(), nullable=True),
        sa.Column("set_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["workoutsession.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Restore previous workout tables; drop PatternInventory and new session/set tables."""
    op.drop_table("workoutset")
    op.drop_index(op.f("ix_workoutsession_user_id"), table_name="workoutsession")
    op.drop_table("workoutsession")
    op.drop_index(op.f("ix_patterninventory_pattern"), table_name="patterninventory")
    op.drop_index(op.f("ix_patterninventory_user_id"), table_name="patterninventory")
    op.drop_table("patterninventory")

    op.create_table(
        "workoutsession",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("session_type", sa.String(length=50), nullable=True),
        sa.Column("impacted_patterns", sa.JSON(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workoutsession_user_id"), "workoutsession", ["user_id"], unique=False)
    op.create_table(
        "workoutset",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workout_id", sa.Integer(), nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("set_order", sa.Integer(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("reps", sa.Integer(), nullable=True),
        sa.Column("rpe", sa.Integer(), nullable=True),
        sa.Column("superset_group_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercise.id"]),
        sa.ForeignKeyConstraint(["workout_id"], ["workoutsession.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
