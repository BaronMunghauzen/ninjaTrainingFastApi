"""
Скрипт наполнения БД из CSV для автоподбора тренировок.
Запуск (из корня проекта):
  python -m scripts.import_training_program_data

По умолчанию CSV ищутся в корне репозитория (рядом с каталогом app/).
Свои пути:
  python -m scripts.import_training_program_data --rules path/to/rules.csv --pool ... --equipment ...

Только training_composition_rules:
  python -m scripts.import_training_program_data --skip-pool --skip-equipment
"""
import asyncio
import argparse
import sys
from pathlib import Path

# Корень проекта — родитель каталога scripts
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Пути по умолчанию — корень проекта (положите CSV туда же, где app/ и scripts/)
DEFAULT_RULES = PROJECT_ROOT / "training_composition_rules_import.csv"
DEFAULT_POOL = PROJECT_ROOT / "exercise_builder_pool_import_v8.csv"
DEFAULT_EQUIPMENT = PROJECT_ROOT / "exercise_builder_equipment_import_v8.csv"


async def main():
    parser = argparse.ArgumentParser(description="Импорт CSV для training_composition_rules, exercise_builder_pool, exercise_builder_equipment")
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES, help="Путь к training_composition_rules_import.csv")
    parser.add_argument("--pool", type=Path, default=DEFAULT_POOL, help="Путь к exercise_builder_pool_import_v8.csv")
    parser.add_argument("--equipment", type=Path, default=DEFAULT_EQUIPMENT, help="Путь к exercise_builder_equipment_import_v8.csv")
    parser.add_argument("--skip-rules", action="store_true", help="Не импортировать правила")
    parser.add_argument("--skip-pool", action="store_true", help="Не импортировать пул упражнений")
    parser.add_argument("--skip-equipment", action="store_true", help="Не импортировать оборудование")
    args = parser.parse_args()

    from app.training_composition_rules.import_csv import import_from_csv as import_rules
    from app.exercise_builder_pool.import_csv import import_from_csv as import_pool
    from app.exercise_builder_equipment.import_csv import import_from_csv as import_equipment

    if not args.skip_rules:
        if not args.rules.exists():
            print(f"Файл не найден: {args.rules}")
            return 1
        n = await import_rules(args.rules)
        print(f"training_composition_rules: импортировано {n} записей")
    else:
        print("Пропуск training_composition_rules")

    if not args.skip_pool:
        if not args.pool.exists():
            print(f"Файл не найден: {args.pool}")
            return 1
        n = await import_pool(args.pool)
        print(f"exercise_builder_pool: импортировано {n} записей")
    else:
        print("Пропуск exercise_builder_pool")

    if not args.skip_equipment:
        if not args.equipment.exists():
            print(f"Файл не найден: {args.equipment}")
            return 1
        n = await import_equipment(args.equipment)
        print(f"exercise_builder_equipment: импортировано {n} записей")
    else:
        print("Пропуск exercise_builder_equipment")

    print("Импорт завершён.")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
