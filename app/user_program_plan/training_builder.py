"""
Сборка тренировки по программе: отбор по оборудованию, якоря (с сохранением в план),
скоринг для main/accessory/core/mobility, fallback, контроль длительности.
"""
from datetime import date, datetime
from typing import Optional, List, Tuple, Dict, Any, Set
from collections import defaultdict

from app.database import async_session_maker
from sqlalchemy import select
from app.exercise_builder_pool.models import ExerciseBuilderPool
from app.exercise_builder_equipment.models import ExerciseBuilderEquipment
from app.user_exercise_stats.service import bulk_get_by_user_and_exercise_ids, times_used_from_stats


# Коды оборудования в exercise_builder_equipment (CSV): none, dumbbells, pullup_bar, bands,
# barbell, smith_machine, cable, ...
def _is_gym_plan(plan) -> bool:
    """Зал: флаги has_* часто не заполняются — фильтрацию по equipment не применяем."""
    return bool(getattr(plan, "train_at_gym", False))


def _user_allowed_equipment(plan) -> set:
    """
    Множество разрешённых equipment_code для дома / не-зала.
    В режиме зала не используется (см. _is_gym_plan + _pool_item_equipment_ok).
    """
    allowed = set()
    allowed.add("none")
    if getattr(plan, "has_dumbbells", False):
        allowed.add("dumbbells")
    if getattr(plan, "has_pullup_bar", False):
        allowed.add("pullup_bar")
    if getattr(plan, "has_bands", False):
        allowed.add("bands")
    # Только вес тела: явный флаг без доп. снаряжения
    if getattr(plan, "train_at_home_no_equipment", False) and not any(
        (
            getattr(plan, "has_dumbbells", False),
            getattr(plan, "has_pullup_bar", False),
            getattr(plan, "has_bands", False),
        )
    ):
        return {"none"}
    return allowed


async def _load_pool_equipment_map() -> Dict[int, List[str]]:
    """Мапа pool_id -> список equipment_code (для проверки доступности)."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(ExerciseBuilderEquipment.exercise_builder_id, ExerciseBuilderEquipment.equipment_code).where(
                ExerciseBuilderEquipment.actual == True
            )
        )
        rows = result.all()
    out = defaultdict(list)
    for pool_id, code in rows:
        if pool_id and code:
            out[pool_id].append((code or "").strip().lower())
    return {k: list(set(v)) for k, v in out.items()}


def _normalize_equipment_code(code: str) -> str:
    c = (code or "").strip().lower()
    aliases = {
        "bar_bell": "barbell",
        "olympic_bar": "barbell",
        "olympic_barbell": "barbell",
    }
    return aliases.get(c, c)


def _pool_item_equipment_ok(
    pool_id: int,
    equipment_map: Dict[int, List[str]],
    allowed: set,
    *,
    gym_mode: bool,
) -> bool:
    """
    Зал: не режем по таблице equipment (доступно всё, что в зале).
    Дом: хотя бы один вариант из строк exercise_builder_equipment должен входить в allowed.
    Нет строк equipment у pool_id: считаем упражнение «без снаряжения» — только если в плане есть none.
    """
    if gym_mode:
        return True
    codes = [_normalize_equipment_code(x) for x in equipment_map.get(pool_id, [])]
    allowed_norm = {_normalize_equipment_code(x) for x in allowed}
    if not codes:
        return "none" in allowed_norm
    return any(c in allowed_norm for c in codes)


def _gym_equipment_sort_rank(pool_id: int, equipment_map: Dict[int, List[str]]) -> int:
    """
    Для train_at_gym: порядок предпочтения при равном скоринге (меньше — лучше).
    0 — обычное снаряжение (есть вариант не только вес тела, без резинок).
    1 — только вес тела (нет строк equipment или все варианты none).
    2 — в списке вариантов есть резинки (самый низкий приоритет в зале).
    """
    codes = [_normalize_equipment_code(x) for x in equipment_map.get(pool_id, [])]
    if any(c == "bands" for c in codes):
        return 2
    if not codes or all(c == "none" for c in codes):
        return 1
    return 0


def _get_goal_weight(pool_item, program_goal: str) -> float:
    g = (program_goal or "").strip().lower()
    if g == "fat_loss":
        w = getattr(pool_item, "goal_fat_loss_weight", None)
    elif g == "mass_gain":
        w = getattr(pool_item, "goal_mass_gain_weight", None)
    else:
        w = getattr(pool_item, "goal_maintenance_weight", None)
    return float(w) if w is not None else 1.0


def _get_week_weight(pool_item, week_index: int) -> float:
    attr = f"week{min(max(week_index, 1), 4)}_weight"
    w = getattr(pool_item, attr, None)
    return float(w) if w is not None else 1.0


_DIFF_LEVEL_ORDER = {"beginner": 0, "intermediate": 1, "advanced": 2}
_DIFF_ANY = "any"
_DIFF_ALIASES = {
    "beginner": "beginner", "easy": "beginner", "начинающий": "beginner", "1": "beginner",
    "intermediate": "intermediate", "medium": "intermediate", "средний": "intermediate", "2": "intermediate",
    "advanced": "advanced", "hard": "advanced", "продвинутый": "advanced", "3": "advanced",
    "any": "any", "all": "any", "any_level": "any", "любой": "any",
}


def _normalize_difficulty(value: str) -> str:
    raw = (value or "").strip().lower()
    return _DIFF_ALIASES.get(raw, raw)


def _difficulty_fallback_order(plan_diff: str) -> List[str]:
    """
    Приоритет fallback:
    1) текущий уровень
    2) на 1 уровень легче
    3) еще на 1 уровень легче
    4) на 1 уровень сложнее
    5) еще на 1 уровень сложнее
    """
    if not plan_diff:
        return []
    base = _DIFF_LEVEL_ORDER.get(plan_diff)
    if base is None:
        return [plan_diff]
    order = [base, base - 1, base - 2, base + 1, base + 2]
    reverse = {v: k for k, v in _DIFF_LEVEL_ORDER.items()}
    return [reverse[i] for i in order if i in reverse]


def _difficulty_matches(
    item_diff_raw: Optional[str],
    target_diff: Optional[str],
    *,
    include_any: bool = False,
) -> bool:
    """
    Совпадение уровня сложности для отбора:
    - если target_diff пустой -> пропускаем любой уровень;
    - обычный режим: item == target;
    - режим include_any: item == target ИЛИ item == any.
    """
    if not target_diff:
        return True
    item_diff = _normalize_difficulty(item_diff_raw or "")
    if item_diff == target_diff:
        return True
    return include_any and item_diff == _DIFF_ANY


def pool_item_can_use_training_type(p, type_lower: str) -> bool:
    if "heavy_push" in type_lower:
        return bool(getattr(p, "can_use_in_heavy_push", False))
    if "heavy_pull" in type_lower:
        return bool(getattr(p, "can_use_in_heavy_pull", False))
    if "heavy_legs" in type_lower:
        return bool(getattr(p, "can_use_in_heavy_legs", False))
    if "light_recovery" in type_lower:
        return bool(getattr(p, "can_use_in_light_recovery", False))
    if "light_pump" in type_lower:
        return bool(getattr(p, "can_use_in_light_pump", False))
    if "light_core" in type_lower:
        return bool(getattr(p, "can_use_in_light_core", False))
    return False


def role_ok_pool_item(p, role: str, type_lower: str) -> bool:
    pr = (getattr(p, "preferred_role", "") or "").strip().lower()
    if pr == role:
        return True
    if role == "accessory":
        return False
    if role == "main" and "heavy" in type_lower and pr not in ("core", "mobility"):
        if "heavy_push" in type_lower:
            return bool(getattr(p, "can_be_secondary_in_heavy_push", False))
        if "heavy_pull" in type_lower:
            return bool(getattr(p, "can_be_secondary_in_heavy_pull", False))
        if "heavy_legs" in type_lower:
            return bool(getattr(p, "can_be_secondary_in_heavy_legs", False))
    return False


def normalize_replacement_action(action: str) -> str:
    a = (action or "").strip().lower()
    aliases = {
        "упростить": "simplify",
        "заменить": "replace",
        "усложнить": "complicate",
    }
    return aliases.get(a, a)


def clamp_int_with_pool_bounds(value: int, vmin: Optional[int], vmax: Optional[int]) -> int:
    if vmin is not None and value < vmin:
        value = vmin
    if vmax is not None and value > vmax:
        value = vmax
    return value


def rule_reps_max_for_slot(rule, slot: Optional[str]) -> Optional[int]:
    """Макс. повторения из правила состава для слота (как источник для reps_count при сборке)."""
    if rule is None:
        return None
    key = (slot or "main").strip().lower()
    attr = {
        "anchor": "anchor_reps_max",
        "main": "main_reps_max",
        "accessory": "accessory_reps_max",
        "core": "core_reps_max",
        "mobility": "mobility_reps_max",
    }.get(key, "main_reps_max")
    return getattr(rule, attr, None)


def duration_seconds_for_time_based_pool_item(pool_item, reps_max_after_clamp: int) -> Optional[int]:
    """
    Длительность одного «рабочего» отрезка в секундах для time-based упражнений:
    база — то же число, что уже ушло в reps после clamp по пулу,
    затем clamp по default_duration_seconds_min/max пула.
    """
    if not getattr(pool_item, "is_time_based", None):
        return None
    dur = reps_max_after_clamp
    dmin = getattr(pool_item, "default_duration_seconds_min", None)
    dmax = getattr(pool_item, "default_duration_seconds_max", None)
    return clamp_int_with_pool_bounds(dur, dmin, dmax)


def replacement_duration_seconds(pool_item, rule, slot: Optional[str], fallback_reps: Optional[int]) -> Optional[int]:
    """Для replace-from-pool: reps_max из правила по слоту → clamp по min/max reps пула → duration clamp по пулу."""
    if not getattr(pool_item, "is_time_based", None):
        return None
    seed = rule_reps_max_for_slot(rule, slot)
    if seed is None:
        seed = fallback_reps if fallback_reps is not None else 12
    seed = clamp_int_with_pool_bounds(
        seed,
        getattr(pool_item, "default_min_reps", None),
        getattr(pool_item, "default_max_reps", None),
    )
    return duration_seconds_for_time_based_pool_item(pool_item, seed)


def replacement_difficulty_order(plan, anchor_diff_raw: Optional[str], action: str) -> List[str]:
    """
    Уровни сложности для подбора замены (только относительно текущего упражнения).

    Заменить — ровно тот же уровень, что у текущего.
    Упростить — на 1–2 ступени легче (от более лёгкого к ближе к текущему); у минимального уровня — [].
    Усложнить — на 1–2 ступени сложнее (от ближе к текущему к более сложному); у максимального уровня — [].

    Неизвестный уровень у якоря: заменить — один элемент как есть; упростить/усложнить — [].
    """
    act = normalize_replacement_action(action)
    plan_diff = _normalize_difficulty(getattr(plan, "difficulty_level", "") or "")
    anchor = _normalize_difficulty(anchor_diff_raw or "") or plan_diff
    reverse = {v: k for k, v in _DIFF_LEVEL_ORDER.items()}
    max_idx = max(_DIFF_LEVEL_ORDER.values())
    base = _DIFF_LEVEL_ORDER.get(anchor)

    if act == "replace":
        if base is not None:
            return [reverse[base]]
        return [anchor] if anchor else []

    if base is None:
        return []

    if act == "simplify":
        if base <= 0:
            return []
        lo = max(0, base - 2)
        indices = list(range(lo, base))
        return [reverse[i] for i in indices if i in reverse]

    if act == "complicate":
        if base >= max_idx:
            return []
        hi = min(max_idx, base + 2)
        indices = list(range(base + 1, hi + 1))
        return [reverse[i] for i in indices if i in reverse]

    return []


def pool_difficulty_for_reference(base_pool_items: List[Any], ref_id: Optional[int]) -> Optional[str]:
    if not ref_id:
        return None
    for p in base_pool_items:
        if getattr(p, "exercise_id", None) == ref_id:
            raw = getattr(p, "difficulty_level", None)
            if raw is None:
                return None
            s = str(raw).strip()
            return s or None
    return None


def variation_codes_for_reference_ids(base_pool_items: List[Any], ref_ids: set) -> set:
    out = set()
    for p in base_pool_items:
        rid = getattr(p, "exercise_id", None)
        if rid and rid in ref_ids:
            vc = (getattr(p, "variation_group_code", None) or "").strip()
            if vc:
                out.add(vc)
    return out


def _score_candidate(
    pool_item,
    role: str,
    plan,
    rule,
    stats_map: Dict[int, Any],
    last_workout_ref_ids: set,
    two_ago_ref_ids: set,
    in_last_7d_ref_ids: set,
    selected_variation_codes: set,
    training_type: str,
) -> float:
    """
    computed_selection_score = base_priority + (goal_weight-1)*20 + (week_weight-1)*20
    + role_fit_bonus + freshness_bonus + low_usage_bonus + difficulty_match_bonus
    - recent_use_penalty - variation_conflict_penalty - fatigue_penalty - role_mismatch_penalty
    """
    ref_id = getattr(pool_item, "exercise_id", None) or getattr(pool_item, "exercise_reference_id", None)
    if ref_id is None:
        ref_id = pool_item.exercise_id if hasattr(pool_item, "exercise_id") else None
    stats = stats_map.get(ref_id) if ref_id else None
    times_7, times_14, times_28 = times_used_from_stats(stats)

    goal_w = _get_goal_weight(pool_item, getattr(plan, "program_goal", ""))
    week_idx = getattr(plan, "current_week_index", 1) or 1
    week_w = _get_week_weight(pool_item, week_idx)

    base = float(getattr(pool_item, "base_priority", 0) or 0)
    score = base + (goal_w - 1) * 20 + (week_w - 1) * 20

    pr = (getattr(pool_item, "preferred_role", "") or "").strip().lower()
    tt = (training_type or "").strip().lower()
    if pr == role:
        score += 12
    elif role == "main" and pr not in ("core", "mobility"):
        if "heavy_push" in tt and getattr(pool_item, "can_be_secondary_in_heavy_push", None):
            score += 5
        elif "heavy_pull" in tt and getattr(pool_item, "can_be_secondary_in_heavy_pull", None):
            score += 5
        elif "heavy_legs" in tt and getattr(pool_item, "can_be_secondary_in_heavy_legs", None):
            score += 5

    if times_14 == 0:
        score += 5
    if times_28 == 0:
        score += 3

    if ref_id and ref_id in last_workout_ref_ids:
        score -= 25
    elif ref_id and ref_id in two_ago_ref_ids:
        score -= 12
    elif ref_id and ref_id in in_last_7d_ref_ids:
        score -= 6

    var_code = (getattr(pool_item, "variation_group_code", "") or "").strip()
    if var_code and var_code in selected_variation_codes:
        score -= 20 if role in ("main", "accessory") else 10

    fatigue = int(getattr(pool_item, "fatigue_cost", 0) or 0)
    score -= fatigue

    if pr and pr != role and role != "anchor":
        score -= 8

    # Difficulty bonus/penalty: +15 if exact match, -20 if wrong level
    plan_diff = _normalize_difficulty(getattr(plan, "difficulty_level", "") or "")
    item_diff = _normalize_difficulty(getattr(pool_item, "difficulty_level", "") or "")
    if plan_diff and item_diff:
        if item_diff == plan_diff:
            score += 15
        else:
            plan_order = _DIFF_LEVEL_ORDER.get(plan_diff, 1)
            item_order = _DIFF_LEVEL_ORDER.get(item_diff, 1)
            score -= abs(plan_order - item_order) * 20

    return score


async def _get_recent_workout_ref_ids(user_id: int, training_type: str, plan_id: int, limit: int = 3) -> Tuple[set, set, set]:
    """Возвращает (last_workout_ref_ids, two_ago_ref_ids, in_last_7d_ref_ids) по exercise_reference_id."""
    from app.user_training.models import UserTraining
    from app.exercises.models import Exercise
    from datetime import timedelta

    last_workout_ref_ids = set()
    two_ago_ref_ids = set()
    in_last_7d_ref_ids = set()
    seven_days_ago = (datetime.now() - timedelta(days=7)).date()

    async with async_session_maker() as session:
        r = await session.execute(
            select(UserTraining)
            .where(
                UserTraining.user_id == user_id,
                UserTraining.user_program_plan_id == plan_id,
                UserTraining.status == "PASSED",
                UserTraining.training_type == training_type,
                UserTraining.completed_at.isnot(None),
            )
            .order_by(UserTraining.completed_at.desc())
            .limit(limit)
        )
        ut_list = r.scalars().all()

        for ti, ut in enumerate(ut_list):
            if not ut.training_id:
                continue
            ex_refs = await session.execute(
                select(Exercise.exercise_reference_id).where(
                    Exercise.training_id == ut.training_id,
                    Exercise.exercise_reference_id.isnot(None),
                )
            )
            ref_ids_this = {row[0] for row in ex_refs.all() if row[0]}
            if ti == 0:
                last_workout_ref_ids = ref_ids_this
            elif ti == 1:
                two_ago_ref_ids = ref_ids_this
            if ut.completed_at:
                cd = ut.completed_at.date() if hasattr(ut.completed_at, "date") else None
                if cd and cd >= seven_days_ago:
                    in_last_7d_ref_ids |= ref_ids_this

    return last_workout_ref_ids, two_ago_ref_ids, in_last_7d_ref_ids


async def build_training_builder_context(
    plan,
    training_type: str,
    user_id: Optional[int],
    plan_id: int,
) -> Dict[str, Any]:
    """
    Общий контекст подбора (пул, оборудование, статы, недавние тренировки, порядок сложности по плану).
    Используется build_training_exercises и подбор замен.
    """
    from app.exercise_builder_pool.dao import ExerciseBuilderPoolDAO

    type_lower = (training_type or "").strip().lower()
    gym_mode = _is_gym_plan(plan)
    allowed = _user_allowed_equipment(plan)
    equipment_map = await _load_pool_equipment_map()
    diff_plan = _normalize_difficulty(getattr(plan, "difficulty_level", "") or "")
    diff_order = _difficulty_fallback_order(diff_plan)

    all_pool = await ExerciseBuilderPoolDAO.find_all(actual=True, is_active=True)
    base_pool_items = [
        p
        for p in all_pool
        if pool_item_can_use_training_type(p, type_lower)
        and _pool_item_equipment_ok(p.id, equipment_map, allowed, gym_mode=gym_mode)
    ]

    ref_ids = [getattr(p, "exercise_id", None) for p in base_pool_items if getattr(p, "exercise_id", None)]
    ref_ids = [r for r in ref_ids if r is not None]
    if user_id is None:
        stats_list = []
        last_ref, two_ago_ref, in_7d_ref = set(), set(), set()
    else:
        stats_list = await bulk_get_by_user_and_exercise_ids(user_id, ref_ids)
        last_ref, two_ago_ref, in_7d_ref = await _get_recent_workout_ref_ids(user_id, type_lower, plan_id)
    stats_map = {s.exercise_reference_id: s for s in stats_list}

    return {
        "type_lower": type_lower,
        "gym_mode": gym_mode,
        "allowed": allowed,
        "equipment_map": equipment_map,
        "base_pool_items": base_pool_items,
        "stats_map": stats_map,
        "last_ref": last_ref,
        "two_ago_ref": two_ago_ref,
        "in_7d_ref": in_7d_ref,
        "diff_order_default": diff_order,
        "plan_diff_normalized": diff_plan,
    }


async def suggest_pool_replacements_for_slot(
    *,
    plan,
    rule,
    training_type: str,
    user_id: Optional[int],
    plan_id: int,
    slot_role: str,
    action: str,
    exclude_exercise_reference_ids: Set[int],
    anchor_diff_for_order: Optional[str],
    top_n: int = 24,
    ctx: Optional[Dict[str, Any]] = None,
) -> List[Any]:
    """
    Кандидаты из пула для замены одного слота с учётом action (simplify/replace/complicate).
    Исключаются записи с exercise_id из exclude_exercise_reference_ids (уже в тренировке).
    """
    if ctx is None:
        ctx = await build_training_builder_context(plan, training_type, user_id, plan_id)
    type_lower = ctx["type_lower"]
    gym_mode = ctx["gym_mode"]
    equipment_map = ctx["equipment_map"]
    allowed = ctx["allowed"]
    base_pool_items = ctx["base_pool_items"]
    stats_map = ctx["stats_map"]
    last_ref = ctx["last_ref"]
    two_ago_ref = ctx["two_ago_ref"]
    in_7d_ref = ctx["in_7d_ref"]

    role = (slot_role or "main").strip().lower()
    diff_steps = replacement_difficulty_order(plan, anchor_diff_for_order, action)
    if not diff_steps:
        return []

    sel_var = variation_codes_for_reference_ids(base_pool_items, exclude_exercise_reference_ids)

    scored: List[Tuple] = []
    seen_pool_ids = set()

    include_any = normalize_replacement_action(action) == "replace"
    for step_i, diff in enumerate(diff_steps):
        tier = [
            p
            for p in base_pool_items
            if p.id not in seen_pool_ids
            and getattr(p, "exercise_id", None)
            and getattr(p, "exercise_id") not in exclude_exercise_reference_ids
            and role_ok_pool_item(p, role, type_lower)
            and _difficulty_matches(getattr(p, "difficulty_level", ""), diff, include_any=include_any)
        ]
        for p in tier:
            sc = _score_candidate(
                p,
                role,
                plan,
                rule,
                stats_map,
                last_ref,
                two_ago_ref,
                in_7d_ref,
                sel_var,
                type_lower,
            )
            g_rank = _gym_equipment_sort_rank(p.id, equipment_map) if gym_mode else 0
            scored.append(
                (
                    step_i,
                    sc,
                    getattr(p, "role_rank_in_slot", 999) or 999,
                    g_rank,
                    stats_map.get(getattr(p, "exercise_id")),
                    p,
                )
            )
            seen_pool_ids.add(p.id)

    def _sort_repl(x):
        s = x[4]
        last_used = (s.last_used_at if s else None) or datetime.min
        t14 = times_used_from_stats(s)[1] if s else 0
        return (x[0], -x[1], x[2], x[3], last_used, t14)

    scored.sort(key=_sort_repl)
    ordered_pools = [x[5] for x in scored]
    return ordered_pools[:top_n]


async def suggest_anchor_replacements(
    *,
    plan,
    training_type: str,
    user_id: Optional[int],
    plan_id: int,
    limb: str,
    exclude_exercise_reference_ids: Set[int],
    anchor_diff_for_order: Optional[str],
    action: str,
    top_n: int = 24,
    ctx: Optional[Dict[str, Any]] = None,
) -> List[Any]:
    """Замена якоря: та же сортировка якорей, другой порядок сложности по action."""
    if ctx is None:
        ctx = await build_training_builder_context(plan, training_type, user_id, plan_id)
    gym_mode = ctx["gym_mode"]
    equipment_map = ctx["equipment_map"]
    allowed = ctx["allowed"]
    base_pool_items = ctx["base_pool_items"]

    tier_attr = f"anchor_priority_tier_{limb}"
    order_attr = f"anchor_order_{limb}"
    tier_order = {"primary": 0, "secondary": 1, "backup": 2}
    diff_steps = replacement_difficulty_order(plan, anchor_diff_for_order, action)
    if not diff_steps:
        return []

    include_any = normalize_replacement_action(action) == "replace"
    out: List[Any] = []
    seen = set()
    for diff in diff_steps:
        candidates = [p for p in base_pool_items if getattr(p, "is_anchor_candidate", False)]
        candidates.sort(
            key=lambda p: (
                tier_order.get((getattr(p, tier_attr) or "").strip().lower(), 99),
                getattr(p, order_attr) or 999,
                _gym_equipment_sort_rank(p.id, equipment_map) if gym_mode else 0,
            )
        )
        for c in candidates:
            if c.id in seen:
                continue
            if getattr(c, "exercise_id", None) in exclude_exercise_reference_ids:
                continue
            if not _difficulty_matches(getattr(c, "difficulty_level", ""), diff, include_any=include_any):
                continue
            if not _pool_item_equipment_ok(c.id, equipment_map, allowed, gym_mode=gym_mode):
                continue
            out.append(c)
            seen.add(c.id)
            if len(out) >= top_n:
                return out
    return out


async def build_training_exercises(
    plan,
    rule,
    training_type: str,
    user_id: Optional[int],
    plan_id: int,
) -> Tuple[List[Dict[str, Any]], Optional[str], List[str]]:
    """
    Строит список упражнений для тренировки: якоря (с сохранением в план), main, accessory, core, mobility.
    Возвращает (list of {pool_item, role, sets, reps_min, reps_max, rest, caption, exercise_reference_id}, limb или None, список uuid якорей для сохранения в план).
    """
    ctx = await build_training_builder_context(plan, training_type, user_id, plan_id)
    type_lower = ctx["type_lower"]
    gym_mode = ctx["gym_mode"]
    allowed = ctx["allowed"]
    equipment_map = ctx["equipment_map"]
    base_pool_items = ctx["base_pool_items"]
    stats_map = ctx["stats_map"]
    last_ref = ctx["last_ref"]
    two_ago_ref = ctx["two_ago_ref"]
    in_7d_ref = ctx["in_7d_ref"]
    diff_order = ctx["diff_order_default"]

    result = []
    used_pool_ids = set()
    selected_variation_codes = set()
    anchor_uuids_to_save = []

    # --- Якоря (только heavy) ---
    limb = None
    if "heavy_push" in type_lower:
        limb = "push"
    elif "heavy_pull" in type_lower:
        limb = "pull"
    elif "heavy_legs" in type_lower:
        limb = "legs"

    anchor_count = min(rule.anchor_slots_count or 0, 2)
    if limb and anchor_count > 0:
        a1_id = getattr(plan, f"anchor1_for_{limb}_id", None)
        a2_id = getattr(plan, f"anchor2_for_{limb}_id", None)
        pool_by_id = {p.id: p for p in base_pool_items}
        saved_anchors = []
        if a1_id and a1_id in pool_by_id and _pool_item_equipment_ok(
            a1_id, equipment_map, allowed, gym_mode=gym_mode
        ):
            saved_anchors.append(pool_by_id[a1_id])
        if a2_id and a2_id != a1_id and a2_id in pool_by_id and _pool_item_equipment_ok(
            a2_id, equipment_map, allowed, gym_mode=gym_mode
        ):
            saved_anchors.append(pool_by_id[a2_id])

        tier_attr = f"anchor_priority_tier_{limb}"
        order_attr = f"anchor_order_{limb}"
        tier_order = {"primary": 0, "secondary": 1, "backup": 2}
        candidates = [p for p in base_pool_items if getattr(p, "is_anchor_candidate", False)]
        candidates.sort(key=lambda p: (
            tier_order.get((getattr(p, tier_attr) or "").strip().lower(), 99),
            getattr(p, order_attr) or 999,
            _gym_equipment_sort_rank(p.id, equipment_map) if gym_mode else 0,
        ))

        anchors_to_use = []
        if len(saved_anchors) >= anchor_count:
            anchors_to_use = saved_anchors[:anchor_count]
        else:
            for idx in range(anchor_count):
                if idx < len(saved_anchors):
                    anchors_to_use.append(saved_anchors[idx])
                    used_pool_ids.add(saved_anchors[idx].id)
                    continue
                used_ids = {a.id for a in anchors_to_use}
                first_vg = (getattr(anchors_to_use[0], "variation_group_code") or "").strip() if anchors_to_use else None
                found_anchor = False
                for diff in (diff_order or [""]):
                    for c in candidates:
                        if c.id in used_pool_ids or c.id in used_ids:
                            continue
                        if not _difficulty_matches(getattr(c, "difficulty_level", ""), diff, include_any=True):
                            continue
                        if not _pool_item_equipment_ok(c.id, equipment_map, allowed, gym_mode=gym_mode):
                            continue
                        if anchors_to_use and (getattr(c, "variation_group_code") or "").strip() == first_vg:
                            continue
                        anchors_to_use.append(c)
                        used_pool_ids.add(c.id)
                        found_anchor = True
                        break
                    if found_anchor:
                        break

        for p in anchors_to_use[:anchor_count]:
            used_pool_ids.add(p.id)
            vc = (getattr(p, "variation_group_code") or "").strip()
            if vc:
                selected_variation_codes.add(vc)
            anchor_uuids_to_save.append(str(p.uuid))
            result.append({
                "pool_item": p,
                "role": "anchor",
                "sets": rule.anchor_sets or 3,
                "reps_min": rule.anchor_reps_min,
                "reps_max": rule.anchor_reps_max,
                "rest": rule.anchor_rest_seconds or 120,
                "caption": getattr(p, "exercise_caption", "") or "Exercise",
                "exercise_reference_id": getattr(p, "exercise_id", None),
            })

    # --- Main / Accessory / Core / Mobility со скорингом ---
    slot_specs = [
        ("main", rule.main_slots_count or 0, rule.main_sets, rule.main_reps_min, rule.main_reps_max, rule.main_rest_seconds, 3),
        ("accessory", rule.accessory_slots_count or 0, rule.accessory_sets, rule.accessory_reps_min, rule.accessory_reps_max, rule.accessory_rest_seconds, 5),
        ("core", rule.core_slots_count or 0, rule.core_sets, rule.core_reps_min, rule.core_reps_max, rule.core_rest_seconds, 4),
        ("mobility", rule.mobility_slots_count or 0, rule.mobility_sets, rule.mobility_reps_min, rule.mobility_reps_max, rule.mobility_rest_seconds, 4),
    ]
    for role, count, sets, reps_min, reps_max, rest, top_n in slot_specs:
        rest = rest or 45
        sets = sets or 2
        reps_max = reps_max or 15
        for _ in range(count):
            candidates = []
            diff_steps = diff_order or [""]
            for diff in diff_steps:
                tier = [
                    p for p in base_pool_items
                    if p.id not in used_pool_ids
                    and role_ok_pool_item(p, role, type_lower)
                    and _difficulty_matches(getattr(p, "difficulty_level", ""), diff, include_any=True)
                ]
                if tier:
                    candidates = tier
                    break
            if not candidates:
                continue
            scored = []
            for p in candidates:
                sc = _score_candidate(
                    p, role, plan, rule, stats_map,
                    last_ref, two_ago_ref, in_7d_ref,
                    selected_variation_codes, type_lower,
                )
                g_rank = _gym_equipment_sort_rank(p.id, equipment_map) if gym_mode else 0
                scored.append((
                    sc,
                    getattr(p, "role_rank_in_slot", 999) or 999,
                    g_rank,
                    stats_map.get(getattr(p, "exercise_id")),
                    p,
                ))
            def _sort_key(x):
                s = x[3]
                last_used = (s.last_used_at if s else None) or datetime.min
                t14 = times_used_from_stats(s)[1] if s else 0
                return (-x[0], x[1], x[2], last_used, t14)
            scored.sort(key=_sort_key)
            top = scored[:top_n]
            if not top:
                break
            _, _, _, _, chosen = top[0]
            used_pool_ids.add(chosen.id)
            vc = (getattr(chosen, "variation_group_code") or "").strip()
            if vc:
                selected_variation_codes.add(vc)
            result.append({
                "pool_item": chosen,
                "role": role,
                "sets": sets,
                "reps_min": reps_min,
                "reps_max": reps_max,
                "rest": rest,
                "caption": getattr(chosen, "exercise_caption", "") or "Exercise",
                "exercise_reference_id": getattr(chosen, "exercise_id", None),
            })

    # Контроль длительности
    target_seconds = (rule.duration_target_minutes or 45) * 60
    total_seconds = 0
    for item in result:
        p = item["pool_item"]
        sets = item["sets"]
        rest = item["rest"]
        est = getattr(p, "estimated_time_per_set_seconds", None) or 90
        total_seconds += sets * est + (sets - 1) * rest
    if total_seconds > target_seconds * 1.15 and result:
        for item in reversed(result):
            if item["role"] == "accessory" and item["sets"] > 1:
                item["sets"] = item["sets"] - 1
                break
    elif total_seconds < target_seconds * 0.85 and result:
        for item in result:
            if item["role"] == "accessory":
                item["sets"] = item["sets"] + 1
                break

    return result, limb, anchor_uuids_to_save
