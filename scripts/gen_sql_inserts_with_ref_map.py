"""
Generate INSERT SQL for exercise_builder_pool/equipment with remap:
pool.exercise_id (prod id) -> exercise_reference.uuid -> local exercise_reference.id;
если по id не найдено — поиск по caption (первое совпадение в справочнике).
"""
import csv
import math

# Input files
POOL_CSV = r"C:\Users\magla\Downloads\exercise_builder_pool_final_v8.csv"
EQUIP_CSV = r"C:\Users\magla\Downloads\exercise_builder_equipment_final_v7.csv"
PROD_REF_CSV = (
    r"C:\Users\magla\Downloads\exercise_reference_202604072246.csv"
)

# Output files
SQL_PATH = r"C:\Users\magla\Downloads\insert_exercise_builder_new_2_mapped.sql"
REPORT_PATH = r"C:\Users\magla\Downloads\insert_exercise_builder_new_2_mapped_report.txt"

# exercise_builder_pool typing
POOL_INT_COLS = {
    "id",
    "default_min_reps",
    "default_max_reps",
    "default_min_sets",
    "default_max_sets",
    "default_rest_seconds",
    "estimated_time_per_set_seconds",
    "base_priority",
    "max_usage_per_28d",
    "anchor_order_push",
    "anchor_order_pull",
    "anchor_order_legs",
    "default_duration_seconds_min",
    "default_duration_seconds_max",
    "fatigue_cost",
    "role_rank_in_slot",
}
POOL_FLOAT_COLS = {
    "goal_fat_loss_weight",
    "goal_mass_gain_weight",
    "goal_maintenance_weight",
    "week1_weight",
    "week2_weight",
    "week3_weight",
    "week4_weight",
}
POOL_BOOL_COLS = {
    "actual",
    "is_anchor_candidate",
    "uses_external_load",
    "is_time_based",
    "is_unilateral",
    "is_active",
    "can_use_in_heavy_push",
    "can_use_in_heavy_pull",
    "can_use_in_heavy_legs",
    "can_use_in_light_recovery",
    "can_use_in_light_pump",
    "can_use_in_light_core",
    "can_be_secondary_in_heavy_push",
    "can_be_secondary_in_heavy_pull",
    "can_be_secondary_in_heavy_legs",
    "anchor_cycle_lock_recommended_push",
    "anchor_cycle_lock_recommended_pull",
    "anchor_cycle_lock_recommended_legs",
}
POOL_SKIP = {"created_at", "updated_at"}

# exercise_builder_equipment typing
EQUIP_INT_COLS = {"id", "exercise_builder_id"}
EQUIP_BOOL_COLS = {"actual"}
EQUIP_SKIP = {"created_at", "updated_at"}


def parse_int(raw: str):
    raw = raw.strip()
    if raw == "" or raw.lower() in ("nan", "none"):
        return None
    try:
        return int(float(raw))
    except Exception:
        return None


def sql_literal(col: str, raw: str, int_cols: set, float_cols: set, bool_cols: set) -> str:
    raw = (raw or "").strip()
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
    escaped = raw.replace("'", "''")
    return f"'{escaped}'"


def load_prod_id_to_uuid(path: str):
    mapping = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_id = (row.get("id") or "").strip().strip('"')
            raw_uuid = (row.get("uuid") or "").strip().strip('"')
            if not raw_id or not raw_uuid:
                continue
            prod_id = parse_int(raw_id)
            if prod_id is None:
                continue
            mapping[prod_id] = raw_uuid
    return mapping


def _normalize_caption(s: str) -> str:
    """Одна строка для сопоставления: trim, lower, пробелы схлопнуты."""
    return " ".join((s or "").strip().lower().split())


def load_caption_to_first_uuid(path: str) -> dict:
    """Первое вхождение caption в файле (порядок строк) сохраняет uuid."""
    mapping = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cap = _normalize_caption(row.get("caption") or "")
            raw_uuid = (row.get("uuid") or "").strip().strip('"')
            if not cap or not raw_uuid:
                continue
            if cap not in mapping:
                mapping[cap] = raw_uuid
    return mapping


def build_pool_inserts(pool_csv: str, prod_id_to_uuid: dict, caption_to_uuid: dict):
    statements = []
    missing = []
    resolved_by_caption = 0
    with open(pool_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = [c for c in reader.fieldnames if c not in POOL_SKIP]
        for row in reader:
            values = []
            for col in cols:
                if col == "exercise_id":
                    prod_id = parse_int(row.get("exercise_id", ""))
                    ex_uuid = prod_id_to_uuid.get(prod_id) if prod_id is not None else None
                    caption_raw = (
                        row.get("exercise_caption")
                        or row.get("caption")
                        or ""
                    )
                    cap_norm = _normalize_caption(caption_raw)
                    if not ex_uuid and caption_to_uuid and cap_norm:
                        ex_uuid = caption_to_uuid.get(cap_norm)
                        if ex_uuid:
                            resolved_by_caption += 1
                    if ex_uuid:
                        ex_uuid_sql = ex_uuid.replace("'", "''")
                        values.append(
                            f"(SELECT id FROM exercise_reference WHERE uuid = '{ex_uuid_sql}')"
                        )
                    else:
                        values.append("NULL")
                        row_id = parse_int(row.get("id", "")) or 0
                        missing.append((row_id, prod_id, cap_norm or caption_raw))
                else:
                    values.append(
                        sql_literal(
                            col,
                            row.get(col, ""),
                            POOL_INT_COLS,
                            POOL_FLOAT_COLS,
                            POOL_BOOL_COLS,
                        )
                    )
            col_list = ", ".join(cols)
            val_list = ", ".join(values)
            statements.append(
                f"INSERT INTO exercise_builder_pool ({col_list})\nVALUES ({val_list});"
            )
    return statements, missing, resolved_by_caption


def build_equipment_inserts(equip_csv: str):
    statements = []
    with open(equip_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = [c for c in reader.fieldnames if c not in EQUIP_SKIP]
        for row in reader:
            values = [
                sql_literal(c, row.get(c, ""), EQUIP_INT_COLS, set(), EQUIP_BOOL_COLS)
                for c in cols
            ]
            col_list = ", ".join(cols)
            val_list = ", ".join(values)
            statements.append(
                f"INSERT INTO exercise_builder_equipment ({col_list})\nVALUES ({val_list});"
            )
    return statements


def main():
    prod_map = load_prod_id_to_uuid(PROD_REF_CSV)
    caption_map = load_caption_to_first_uuid(PROD_REF_CSV)
    pool_stmts, missing_pool_refs, caption_resolved = build_pool_inserts(
        POOL_CSV, prod_map, caption_map
    )
    equip_stmts = build_equipment_inserts(EQUIP_CSV)

    lines = ["BEGIN;", ""]
    lines.append(f"-- exercise_builder_pool ({len(pool_stmts)} rows)")
    lines.extend(pool_stmts)
    lines.append("")
    lines.append(f"-- exercise_builder_equipment ({len(equip_stmts)} rows)")
    lines.extend(equip_stmts)
    lines.append("")
    lines.append("COMMIT;")

    with open(SQL_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    report = []
    report.append(f"pool_rows={len(pool_stmts)}")
    report.append(f"equipment_rows={len(equip_stmts)}")
    report.append(f"prod_reference_rows={len(prod_map)}")
    report.append(f"caption_index_entries={len(caption_map)}")
    report.append(f"pool_exercise_id_resolved_by_caption={caption_resolved}")
    report.append(f"missing_pool_reference_rows={len(missing_pool_refs)}")
    if missing_pool_refs:
        report.append("missing_details(pool_row_id, prod_exercise_id, caption_norm):")
        for row_id, prod_id, cap in missing_pool_refs[:200]:
            report.append(f"{row_id} -> prod_id={prod_id} caption={cap!r}")
        if len(missing_pool_refs) > 200:
            report.append(f"... and {len(missing_pool_refs) - 200} more")
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report))

    print(f"Done: {len(pool_stmts)} pool + {len(equip_stmts)} equipment -> {SQL_PATH}")
    print(f"Report: {REPORT_PATH}")
    print(f"Resolved by caption: {caption_resolved}; still missing: {len(missing_pool_refs)}")


if __name__ == "__main__":
    main()
