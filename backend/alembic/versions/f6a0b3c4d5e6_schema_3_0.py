"""Schema 3.0: User, ConditioningProtocol/Progress/Benchmark, PatternHistory, WorkoutSet flexible, etc.

Revision ID: f6a0b3c4d5e6
Revises: e5f9b2c3d4e5
Create Date: 2026-02-12

- User table, ConditioningProtocol, ConditioningProgress, ConditioningBenchmark
- Exercise: add tracking_unit, is_unilateral, is_bodyweight
- Rename patterninventory -> patternhistory
- WorkoutSession: add computed_state, rename notes -> session_notes
- WorkoutSet: exercise_id FK, flexible nullable columns; data migration from exercise_name (auto-create unknown exercises)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
# revision identifiers, used by Alembic.
revision: str = "f6a0b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "e5f9b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ----- Create new tables -----
    op.create_table(
        "user",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("first_name", sa.String(length=255), nullable=False),
        sa.Column("last_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("dob", sa.Date(), nullable=True),
        sa.Column("gender", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)

    op.create_table(
        "conditioningprotocol",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tier", sa.String(length=20), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("work_duration", sa.Integer(), nullable=True),
        sa.Column("rest_duration", sa.Integer(), nullable=True),
        sa.Column("rounds", sa.Integer(), nullable=False),
        sa.Column("target_modifier", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "conditioningprogress",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("sit_level", sa.Integer(), nullable=False),
        sa.Column("hiit_level", sa.Integer(), nullable=False),
        sa.Column("last_tier_performed", sa.String(length=20), nullable=False),
        sa.Column("last_performed", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.create_table(
        "conditioningbenchmark",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("benchmark_type", sa.String(length=50), nullable=False),
        sa.Column("equipment", sa.String(length=100), nullable=False),
        sa.Column("result_metric", sa.Float(), nullable=False),
        sa.Column("peak_watts", sa.Integer(), nullable=True),
        sa.Column("avg_hr", sa.Integer(), nullable=True),
        sa.Column("peak_hr", sa.Integer(), nullable=True),
        sa.Column("hr_recovery", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_conditioningbenchmark_user_id"), "conditioningbenchmark", ["user_id"], unique=False)

    # ----- Alter exercise -----
    op.add_column("exercise", sa.Column("tracking_unit", sa.String(length=20), nullable=False, server_default="REPS"))
    op.add_column("exercise", sa.Column("is_unilateral", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("exercise", sa.Column("is_bodyweight", sa.Boolean(), nullable=False, server_default="false"))

    # ----- Rename patterninventory -> patternhistory -----
    op.rename_table("patterninventory", "patternhistory")
    op.drop_constraint("uq_pattern_inventory_user_pattern", "patternhistory", type_="unique")
    op.create_unique_constraint("uq_pattern_history_user_pattern", "patternhistory", ["user_id", "pattern"])
    # Widen pattern column for CONDITIONING:SIT etc.
    op.alter_column(
        "patternhistory",
        "pattern",
        existing_type=sa.String(length=100),
        type_=sa.String(length=150),
        existing_nullable=False,
    )

    # ----- Alter workoutsession -----
    op.add_column(
        "workoutsession",
        sa.Column("computed_state", sa.String(length=50), nullable=False, server_default="GREEN"),
    )
    op.alter_column(
        "workoutsession",
        "computed_state",
        server_default=None,
    )
    op.rename_column("workoutsession", "notes", "session_notes")

    # ----- Alter workoutset: add new columns and nullable exercise_id -----
    op.add_column("workoutset", sa.Column("exercise_id", sa.Integer(), nullable=True))
    op.add_column("workoutset", sa.Column("distance_meters", sa.Float(), nullable=True))
    op.add_column("workoutset", sa.Column("work_seconds", sa.Integer(), nullable=True))
    op.add_column("workoutset", sa.Column("rest_seconds", sa.Integer(), nullable=True))
    op.add_column("workoutset", sa.Column("watts_avg", sa.Integer(), nullable=True))
    op.add_column("workoutset", sa.Column("watts_peak", sa.Integer(), nullable=True))
    op.add_column("workoutset", sa.Column("hr_avg", sa.Integer(), nullable=True))
    op.add_column("workoutset", sa.Column("hr_peak", sa.Integer(), nullable=True))
    op.add_column("workoutset", sa.Column("is_benchmark", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("workoutset", sa.Column("exercise_notes", sa.Text(), nullable=True))
    op.alter_column(
        "workoutset",
        "weight_kg",
        existing_type=sa.Float(),
        nullable=True,
    )
    op.alter_column(
        "workoutset",
        "reps",
        existing_type=sa.Integer(),
        nullable=True,
    )

    # ----- Data migration: exercise_name -> exercise_id (auto-create unknown exercises) -----
    connection = op.get_bind()
    # Get distinct exercise_name from workoutset that are not in exercise; insert them
    result = connection.execute(
        sa.text("""
            SELECT DISTINCT ws.exercise_name
            FROM workoutset ws
            LEFT JOIN exercise e ON e.name = ws.exercise_name
            WHERE e.id IS NULL
        """)
    )
    for row in result:
        name = row[0]
        connection.execute(
            sa.text("""
                INSERT INTO exercise (name, category, modality, tracking_unit, is_unilateral, is_bodyweight)
                VALUES (:name, 'UNKNOWN', 'Unknown', 'REPS', false, false)
            """),
            {"name": name},
        )
    # Set exercise_id from exercise name
    connection.execute(
        sa.text("""
            UPDATE workoutset ws
            SET exercise_id = e.id
            FROM exercise e
            WHERE e.name = ws.exercise_name
        """)
    )
    # Drop exercise_name, make exercise_id non-nullable, add FK
    op.drop_column("workoutset", "exercise_name")
    op.alter_column(
        "workoutset",
        "exercise_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.create_foreign_key("fk_workoutset_exercise_id", "workoutset", "exercise", ["exercise_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_workoutset_exercise_id", "workoutset", type_="foreignkey")
    op.add_column("workoutset", sa.Column("exercise_name", sa.String(length=255), nullable=True))
    # Backfill exercise_name from exercise
    connection = op.get_bind()
    connection.execute(
        sa.text("""
            UPDATE workoutset ws
            SET exercise_name = e.name
            FROM exercise e
            WHERE e.id = ws.exercise_id
        """)
    )
    op.alter_column("workoutset", "exercise_name", nullable=False)
    op.drop_column("workoutset", "exercise_id")
    op.alter_column("workoutset", "weight_kg", nullable=False)
    op.alter_column("workoutset", "reps", nullable=False)
    op.drop_column("workoutset", "exercise_notes")
    op.drop_column("workoutset", "is_benchmark")
    op.drop_column("workoutset", "hr_peak")
    op.drop_column("workoutset", "hr_avg")
    op.drop_column("workoutset", "watts_peak")
    op.drop_column("workoutset", "watts_avg")
    op.drop_column("workoutset", "rest_seconds")
    op.drop_column("workoutset", "work_seconds")
    op.drop_column("workoutset", "distance_meters")

    op.rename_column("workoutsession", "session_notes", "notes")
    op.drop_column("workoutsession", "computed_state")

    op.drop_constraint("uq_pattern_history_user_pattern", "patternhistory", type_="unique")
    op.alter_column(
        "patternhistory",
        "pattern",
        existing_type=sa.String(length=150),
        type_=sa.String(length=100),
        existing_nullable=False,
    )
    op.rename_table("patternhistory", "patterninventory")
    op.create_unique_constraint("uq_pattern_inventory_user_pattern", "patterninventory", ["user_id", "pattern"])

    op.drop_column("exercise", "is_bodyweight")
    op.drop_column("exercise", "is_unilateral")
    op.drop_column("exercise", "tracking_unit")

    op.drop_index(op.f("ix_conditioningbenchmark_user_id"), table_name="conditioningbenchmark")
    op.drop_table("conditioningbenchmark")
    op.drop_table("conditioningprogress")
    op.drop_table("conditioningprotocol")
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_table("user")
