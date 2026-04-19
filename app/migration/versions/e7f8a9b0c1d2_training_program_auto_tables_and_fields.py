"""training program auto: new tables and fields

Revision ID: e7f8a9b0c1d2
Revises: bed84e8e1044
Create Date: 2026-03-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "e7f8a9b0c1d2"
down_revision: Union[str, Sequence[str], None] = "bed84e8e1044"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) training_composition_rules
    op.create_table(
        "training_composition_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("actual", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("training_type", sa.String(), nullable=True),
        sa.Column("program_goal", sa.String(), nullable=True),
        sa.Column("program_week_index", sa.Integer(), nullable=True),
        sa.Column("duration_target_minutes", sa.Integer(), nullable=True),
        sa.Column("location_scope", sa.String(), nullable=True),
        sa.Column("anchor_slots_count", sa.Integer(), nullable=True),
        sa.Column("main_slots_count", sa.Integer(), nullable=True),
        sa.Column("accessory_slots_count", sa.Integer(), nullable=True),
        sa.Column("core_slots_count", sa.Integer(), nullable=True),
        sa.Column("mobility_slots_count", sa.Integer(), nullable=True),
        sa.Column("allow_second_anchor", sa.Boolean(), nullable=True),
        sa.Column("anchor_sets", sa.Integer(), nullable=True),
        sa.Column("anchor_reps_min", sa.Integer(), nullable=True),
        sa.Column("anchor_reps_max", sa.Integer(), nullable=True),
        sa.Column("anchor_rest_seconds", sa.Integer(), nullable=True),
        sa.Column("main_sets", sa.Integer(), nullable=True),
        sa.Column("main_reps_min", sa.Integer(), nullable=True),
        sa.Column("main_reps_max", sa.Integer(), nullable=True),
        sa.Column("main_rest_seconds", sa.Integer(), nullable=True),
        sa.Column("accessory_sets", sa.Integer(), nullable=True),
        sa.Column("accessory_reps_min", sa.Integer(), nullable=True),
        sa.Column("accessory_reps_max", sa.Integer(), nullable=True),
        sa.Column("accessory_rest_seconds", sa.Integer(), nullable=True),
        sa.Column("core_sets", sa.Integer(), nullable=True),
        sa.Column("core_reps_min", sa.Integer(), nullable=True),
        sa.Column("core_reps_max", sa.Integer(), nullable=True),
        sa.Column("core_rest_seconds", sa.Integer(), nullable=True),
        sa.Column("mobility_sets", sa.Integer(), nullable=True),
        sa.Column("mobility_reps_min", sa.Integer(), nullable=True),
        sa.Column("mobility_reps_max", sa.Integer(), nullable=True),
        sa.Column("mobility_rest_seconds", sa.Integer(), nullable=True),
        sa.Column("notes_ru", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_training_composition_rules_uuid"), "training_composition_rules", ["uuid"], unique=True)

    # 2) exercise_builder_pool
    op.create_table(
        "exercise_builder_pool",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("actual", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("exercise_id", sa.Integer(), nullable=True),
        sa.Column("exercise_caption", sa.String(), nullable=True),
        sa.Column("difficulty_level", sa.String(), nullable=True),
        sa.Column("primary_muscle_group", sa.String(), nullable=True),
        sa.Column("auxiliary_muscle_groups", sa.Text(), nullable=True),
        sa.Column("preferred_role", sa.String(), nullable=True),
        sa.Column("is_anchor_candidate", sa.Boolean(), nullable=True),
        sa.Column("anchor_priority_tier", sa.String(), nullable=True),
        sa.Column("uses_external_load", sa.Boolean(), nullable=True),
        sa.Column("default_min_reps", sa.Integer(), nullable=True),
        sa.Column("default_max_reps", sa.Integer(), nullable=True),
        sa.Column("default_min_sets", sa.Integer(), nullable=True),
        sa.Column("default_max_sets", sa.Integer(), nullable=True),
        sa.Column("default_rest_seconds", sa.Integer(), nullable=True),
        sa.Column("is_time_based", sa.Boolean(), nullable=True),
        sa.Column("default_duration_seconds_min", sa.Integer(), nullable=True),
        sa.Column("default_duration_seconds_max", sa.Integer(), nullable=True),
        sa.Column("estimated_time_per_set_seconds", sa.Integer(), nullable=True),
        sa.Column("variation_group_code", sa.String(), nullable=True),
        sa.Column("base_priority", sa.Integer(), nullable=True),
        sa.Column("goal_fat_loss_weight", sa.Integer(), nullable=True),
        sa.Column("goal_mass_gain_weight", sa.Integer(), nullable=True),
        sa.Column("goal_maintenance_weight", sa.Integer(), nullable=True),
        sa.Column("week1_weight", sa.Integer(), nullable=True),
        sa.Column("week2_weight", sa.Integer(), nullable=True),
        sa.Column("week3_weight", sa.Integer(), nullable=True),
        sa.Column("week4_weight", sa.Integer(), nullable=True),
        sa.Column("cooldown_sessions", sa.String(), nullable=True),
        sa.Column("max_usage_per_28d", sa.Integer(), nullable=True),
        sa.Column("can_use_in_heavy_push", sa.Boolean(), nullable=True),
        sa.Column("can_use_in_heavy_pull", sa.Boolean(), nullable=True),
        sa.Column("can_use_in_heavy_legs", sa.Boolean(), nullable=True),
        sa.Column("can_use_in_light_recovery", sa.Boolean(), nullable=True),
        sa.Column("can_use_in_light_pump", sa.Boolean(), nullable=True),
        sa.Column("can_use_in_light_core", sa.Boolean(), nullable=True),
        sa.Column("can_be_secondary_in_heavy_push", sa.Boolean(), nullable=True),
        sa.Column("can_be_secondary_in_heavy_pull", sa.Boolean(), nullable=True),
        sa.Column("can_be_secondary_in_heavy_legs", sa.Boolean(), nullable=True),
        sa.Column("anchor_order_push", sa.Integer(), nullable=True),
        sa.Column("anchor_order_pull", sa.Integer(), nullable=True),
        sa.Column("anchor_order_legs", sa.Integer(), nullable=True),
        sa.Column("is_unilateral", sa.Boolean(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("source_analysis_note", sa.Text(), nullable=True),
        sa.Column("anchor_priority_tier_push", sa.String(), nullable=True),
        sa.Column("anchor_cycle_lock_recommended_push", sa.Boolean(), nullable=True),
        sa.Column("anchor_priority_tier_pull", sa.String(), nullable=True),
        sa.Column("anchor_cycle_lock_recommended_pull", sa.Boolean(), nullable=True),
        sa.Column("anchor_priority_tier_legs", sa.String(), nullable=True),
        sa.Column("anchor_cycle_lock_recommended_legs", sa.Boolean(), nullable=True),
        sa.Column("slot_family", sa.String(), nullable=True),
        sa.Column("fatigue_cost", sa.Integer(), nullable=True),
        sa.Column("role_rank_in_slot", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercise_reference.id"], name="exercise_builder_pool_exercise_id_fkey"),
    )
    op.create_index(op.f("ix_exercise_builder_pool_uuid"), "exercise_builder_pool", ["uuid"], unique=True)
    op.create_index("ix_exercise_builder_pool_actual", "exercise_builder_pool", ["actual"], postgresql_where=sa.text("actual = true"))

    # 3) exercise_builder_equipment
    op.create_table(
        "exercise_builder_equipment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("actual", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("exercise_builder_id", sa.Integer(), nullable=True),
        sa.Column("equipment_code", sa.String(), nullable=True),
        sa.Column("exercise_caption", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["exercise_builder_id"], ["exercise_builder_pool.id"], name="exercise_builder_equipment_exercise_builder_id_fkey"),
    )
    op.create_index(op.f("ix_exercise_builder_equipment_uuid"), "exercise_builder_equipment", ["uuid"], unique=True)

    # 4) user_program_plan
    op.create_table(
        "user_program_plan",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("actual", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("train_at_gym", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("train_at_home", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("train_at_home_no_equipment", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("has_dumbbells", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("has_pullup_bar", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("has_bands", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("duration_target_minutes", sa.Integer(), nullable=False),
        sa.Column("difficulty_level", sa.String(), nullable=False),
        sa.Column("program_goal", sa.String(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("training_days_per_week", sa.Integer(), nullable=False),
        sa.Column("current_week_index", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("completed_heavy_training_count", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("recommended_next_training_date", sa.Date(), nullable=True),
        sa.Column("anchor1_for_pull_id", sa.Integer(), nullable=True),
        sa.Column("anchor2_for_pull_id", sa.Integer(), nullable=True),
        sa.Column("anchor1_for_push_id", sa.Integer(), nullable=True),
        sa.Column("anchor2_for_push_id", sa.Integer(), nullable=True),
        sa.Column("anchor1_for_legs_id", sa.Integer(), nullable=True),
        sa.Column("anchor2_for_legs_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name="user_program_plan_user_id_fkey"),
        sa.ForeignKeyConstraint(["anchor1_for_pull_id"], ["exercise_builder_pool.id"]),
        sa.ForeignKeyConstraint(["anchor2_for_pull_id"], ["exercise_builder_pool.id"]),
        sa.ForeignKeyConstraint(["anchor1_for_push_id"], ["exercise_builder_pool.id"]),
        sa.ForeignKeyConstraint(["anchor2_for_push_id"], ["exercise_builder_pool.id"]),
        sa.ForeignKeyConstraint(["anchor1_for_legs_id"], ["exercise_builder_pool.id"]),
        sa.ForeignKeyConstraint(["anchor2_for_legs_id"], ["exercise_builder_pool.id"]),
    )
    op.create_index(op.f("ix_user_program_plan_uuid"), "user_program_plan", ["uuid"], unique=True)
    op.create_index("ix_user_program_plan_user_actual", "user_program_plan", ["user_id", "actual"], postgresql_where=sa.text("actual = true"))

    # 5) user_exercise_stats
    op.create_table(
        "user_exercise_stats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("actual", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("exercise_reference_id", sa.Integer(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("total_usage_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_workout_uuid", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("last_training_type", sa.String(), nullable=True),
        sa.Column("last_role", sa.String(), nullable=True),
        sa.Column("last_sets_summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("best_weight_value", sa.Numeric(), nullable=True),
        sa.Column("best_reps_value", sa.Integer(), nullable=True),
        sa.Column("best_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("best_volume_value", sa.Numeric(), nullable=True),
        sa.Column("usage_ring_last_shift_date", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
        sa.Column("usage_day_0", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_1", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_2", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_3", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_4", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_5", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_6", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_7", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_8", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_9", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_10", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_11", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_12", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_13", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_14", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_15", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_16", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_17", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_18", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_19", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_20", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_21", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_22", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_23", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_24", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_25", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_26", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("usage_day_27", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "exercise_reference_id", name="uq_user_exercise_stats_user_exercise"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["exercise_reference_id"], ["exercise_reference.id"]),
    )
    op.create_index(op.f("ix_user_exercise_stats_uuid"), "user_exercise_stats", ["uuid"], unique=True)
    op.create_index("ix_user_exercise_stats_user_exercise", "user_exercise_stats", ["user_id", "exercise_reference_id"], unique=True)
    op.create_index("ix_user_exercise_stats_user_last_used", "user_exercise_stats", ["user_id", "last_used_at"])

    # 6) exercise: add training_id
    op.add_column("exercise", sa.Column("training_id", sa.Integer(), nullable=True))
    op.create_foreign_key("exercise_training_id_fkey", "exercise", "training", ["training_id"], ["id"])

    # 7) training: add user_program_plan_id
    op.add_column("training", sa.Column("user_program_plan_id", sa.Integer(), nullable=True))
    op.create_foreign_key("training_user_program_plan_id_fkey", "training", "user_program_plan", ["user_program_plan_id"], ["id"])

    # 8) user_training: add training_type, user_program_plan_id
    op.add_column("user_training", sa.Column("training_type", sa.String(), nullable=True))
    op.add_column("user_training", sa.Column("user_program_plan_id", sa.Integer(), nullable=True))
    op.create_foreign_key("user_training_user_program_plan_id_fkey", "user_training", "user_program_plan", ["user_program_plan_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("user_training_user_program_plan_id_fkey", "user_training", type_="foreignkey")
    op.drop_column("user_training", "user_program_plan_id")
    op.drop_column("user_training", "training_type")

    op.drop_constraint("training_user_program_plan_id_fkey", "training", type_="foreignkey")
    op.drop_column("training", "user_program_plan_id")

    op.drop_constraint("exercise_training_id_fkey", "exercise", type_="foreignkey")
    op.drop_column("exercise", "training_id")

    op.drop_index("ix_user_exercise_stats_user_last_used", table_name="user_exercise_stats")
    op.drop_index("ix_user_exercise_stats_user_exercise", table_name="user_exercise_stats")
    op.drop_index(op.f("ix_user_exercise_stats_uuid"), table_name="user_exercise_stats")
    op.drop_table("user_exercise_stats")

    op.drop_index(op.f("ix_user_program_plan_uuid"), table_name="user_program_plan")
    op.drop_index("ix_user_program_plan_user_actual", table_name="user_program_plan")
    op.drop_table("user_program_plan")

    op.drop_index(op.f("ix_exercise_builder_equipment_uuid"), table_name="exercise_builder_equipment")
    op.drop_table("exercise_builder_equipment")

    op.drop_index("ix_exercise_builder_pool_actual", table_name="exercise_builder_pool")
    op.drop_index(op.f("ix_exercise_builder_pool_uuid"), table_name="exercise_builder_pool")
    op.drop_table("exercise_builder_pool")

    op.drop_index(op.f("ix_training_composition_rules_uuid"), table_name="training_composition_rules")
    op.drop_table("training_composition_rules")
