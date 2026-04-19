"""
Генерирует SQL INSERT для таблиц exercise_builder_pool и exercise_builder_equipment.
"""
import csv
import math

# ─── пути ───────────────────────────────────────────────────────────────────
POOL_CSV  = r"C:\Users\magla\Downloads\exercise_builder_pool_new (1).csv"
EQUIP_CSV = r"C:\Users\magla\Downloads\exercise_builder_equipment_new (1).csv"
SQL_PATH  = r"C:\Users\magla\Downloads\insert_exercise_builder_new_1.sql"

# ─── типы колонок ────────────────────────────────────────────────────────────
# exercise_builder_pool
POOL_INT_COLS = {
    "id","exercise_id",
    "default_min_reps","default_max_reps","default_min_sets","default_max_sets",
    "default_rest_seconds","estimated_time_per_set_seconds","base_priority",
    "max_usage_per_28d","anchor_order_push","anchor_order_pull","anchor_order_legs",
    "default_duration_seconds_min","default_duration_seconds_max",
    "fatigue_cost","role_rank_in_slot",
}
POOL_FLOAT_COLS = {
    "goal_fat_loss_weight","goal_mass_gain_weight","goal_maintenance_weight",
    "week1_weight","week2_weight","week3_weight","week4_weight",
}
POOL_BOOL_COLS = {
    "actual","is_anchor_candidate","uses_external_load","is_time_based","is_unilateral","is_active",
    "can_use_in_heavy_push","can_use_in_heavy_pull","can_use_in_heavy_legs",
    "can_use_in_light_recovery","can_use_in_light_pump","can_use_in_light_core",
    "can_be_secondary_in_heavy_push","can_be_secondary_in_heavy_pull","can_be_secondary_in_heavy_legs",
    "anchor_cycle_lock_recommended_push","anchor_cycle_lock_recommended_pull","anchor_cycle_lock_recommended_legs",
}
POOL_SKIP = {"created_at","updated_at"}

# exercise_builder_equipment
EQUIP_INT_COLS  = {"id","exercise_builder_id"}
EQUIP_BOOL_COLS = {"actual"}
EQUIP_SKIP      = {"created_at","updated_at"}


def sql_val(col, raw, int_cols, float_cols, bool_cols):
    raw = raw.strip()
    if raw == "" or raw.lower() in ("nan", "none"):
        return "NULL"
    if col in bool_cols:
        return "TRUE" if raw.lower() in ("true", "1", "yes") else "FALSE"
    if col in int_cols:
        try:
            return str(int(float(raw)))
        except Exception:
            return "NULL"
    if col in float_cols:
        try:
            v = float(raw)
            return "NULL" if math.isnan(v) else repr(v)
        except Exception:
            return "NULL"
    # string / uuid / timestamp — просто экранируем
    escaped = raw.replace("'", "''")
    return f"'{escaped}'"


def build_inserts(csv_path, table, int_cols, float_cols, bool_cols, skip_cols):
    statements = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = [c for c in reader.fieldnames if c not in skip_cols]
        for row in reader:
            values = []
            for col in cols:
                values.append(sql_val(col, row.get(col, ""), int_cols, float_cols, bool_cols))
            col_list  = ", ".join(cols)
            val_list  = ", ".join(values)
            statements.append(f"INSERT INTO {table} ({col_list})\nVALUES ({val_list});")
    return statements, len(statements)


lines = ["BEGIN;", ""]

print("Обрабатываю exercise_builder_pool ...")
pool_stmts, pool_cnt = build_inserts(
    POOL_CSV, "exercise_builder_pool",
    POOL_INT_COLS, POOL_FLOAT_COLS, POOL_BOOL_COLS, POOL_SKIP,
)
lines.append(f"-- ── exercise_builder_pool ({pool_cnt} rows) ───────────────────────────────────")
lines.extend(pool_stmts)
lines.append("")

print("Обрабатываю exercise_builder_equipment ...")
equip_stmts, equip_cnt = build_inserts(
    EQUIP_CSV, "exercise_builder_equipment",
    EQUIP_INT_COLS, set(), EQUIP_BOOL_COLS, EQUIP_SKIP,
)
lines.append(f"-- ── exercise_builder_equipment ({equip_cnt} rows) ──────────────────────────────")
lines.extend(equip_stmts)
lines.append("")

lines.append("COMMIT;")

with open(SQL_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Done: {pool_cnt} pool + {equip_cnt} equipment -> {SQL_PATH}")
