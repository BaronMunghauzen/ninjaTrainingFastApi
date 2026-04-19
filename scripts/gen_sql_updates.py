import csv
import math

CSV_PATH = r"C:\Users\magla\Downloads\improved_training_composition_rules_final.csv"
SQL_PATH = r"C:\Users\magla\Downloads\update_training_composition_rules.sql"

FLOAT_COLS = {
    "anchor_sets","anchor_reps_min","anchor_reps_max","anchor_rest_seconds",
    "main_sets","main_reps_min","main_reps_max","main_rest_seconds",
    "accessory_sets","accessory_reps_min","accessory_reps_max","accessory_rest_seconds",
    "core_sets","core_reps_min","core_reps_max","core_rest_seconds",
    "mobility_sets","mobility_reps_min","mobility_reps_max","mobility_rest_seconds",
}
INT_COLS = {
    "program_week_index","duration_target_minutes",
    "anchor_slots_count","main_slots_count","accessory_slots_count",
    "core_slots_count","mobility_slots_count",
}
BOOL_COLS = {"actual","allow_second_anchor"}
SKIP_COLS = {"id","created_at","updated_at","uuid"}


def sql_val(col, raw):
    raw = raw.strip()
    if col in SKIP_COLS:
        return None
    if raw == "" or raw.lower() == "nan":
        return "NULL"
    if col in BOOL_COLS:
        return "TRUE" if raw.lower() in ("true", "1", "yes") else "FALSE"
    if col in INT_COLS:
        try:
            return str(int(float(raw)))
        except Exception:
            return "NULL"
    if col in FLOAT_COLS:
        try:
            v = float(raw)
            return "NULL" if math.isnan(v) else str(v)
        except Exception:
            return "NULL"
    escaped = raw.replace("'", "''")
    return f"'{escaped}'"


lines = ["BEGIN;", ""]

with open(CSV_PATH, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    count = 0
    for row in reader:
        uuid = row["uuid"].strip()
        sets = []
        for col in reader.fieldnames:
            if col in SKIP_COLS:
                continue
            v = sql_val(col, row.get(col, ""))
            if v is not None:
                sets.append(f"    {col} = {v}")
        if not sets:
            continue
        stmt = (
            f"UPDATE training_composition_rules\nSET\n"
            + ",\n".join(sets)
            + f"\nWHERE uuid = '{uuid}';\n"
        )
        lines.append(stmt)
        count += 1

lines.append("COMMIT;")

with open(SQL_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Done: {count} UPDATE statements -> {SQL_PATH}")
