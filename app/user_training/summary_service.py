"""Итоги и сравнение прохождений user_training по данным user_exercise."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from app.exercises.dao import ExerciseDAO
from app.exercises.models import Exercise
from app.trainings.dao import TrainingDAO
from app.user_exercises.dao import UserExerciseDAO
from app.user_exercises.models import UserExercise
from app.user_training.dao import UserTrainingDAO
from app.user_training.models import UserTraining


def _pct_vs_previous(current: float, previous: float) -> Optional[float]:
    if previous == 0:
        if current == 0:
            return 0.0
        return None
    return round(100.0 * (current - previous) / previous, 2)


def _ratio_clamped(cur: float, prev: float, lo: float = 0.5, hi: float = 2.0) -> float:
    if prev <= 0:
        return hi if cur > 0 else 1.0
    r = cur / prev
    return max(lo, min(hi, r))


def _triple(
    current: Any,
    previous: Any,
    has_previous: bool,
) -> dict[str, Any]:
    """Сравнительный блок: current / previous / index (% к прошлому разу)."""
    prev_out = previous if has_previous else None
    index: Optional[float] = None
    if has_previous and previous is not None:
        index = _pct_vs_previous(float(current or 0), float(previous))
    return {"current": current, "previous": prev_out, "index": index}


SESSION_LOAD_INDEX_FORMULA = (
    "Берутся отношения текущее/прошлое по четырём величинам всей тренировки: общий тоннаж, "
    "повторы, подходы, число завершённых упражнений. Каждое отношение ограничивается "
    "в диапазоне [0,5 … 2,0] (чтобы выбросы не ломали оценку). "
    "Индекс = 100 × (r₁·r₂·r₃·r₄)^0,25 — геометрическое среднее этих четырёх отношений в процентах. "
    "В ответе previous зафиксирован как 100 (условная база); index = current − 100 (отклонение в пунктах)."
)


def _user_exercise_counts_as_logged_set(ue: UserExercise) -> bool:
    """Подход входит в статистику, если не оба нуля: вес и повторы (None веса считаем 0)."""
    w = float(ue.weight) if ue.weight is not None else 0.0
    r = int(ue.reps or 0)
    return not (w == 0.0 and r == 0)


def _user_exercise_filters_for_training_session(ut: UserTraining) -> Optional[dict[str, Any]]:
    """
    Поля для выборки user_exercise в рамках одной сессии user_training:
    один и тот же шаблон тренировки (training_id) могут проходить разные пользователи и в разные даты.
    """
    if ut.training_id is None:
        return None
    filters: dict[str, Any] = {
        "training_id": ut.training_id,
        "training_date": ut.training_date,
    }
    if ut.user_id is not None:
        filters["user_id"] = ut.user_id
    else:
        filters["user_id"] = None
        filters["anonymous_session_id"] = ut.anonymous_session_id
    return filters


def _last_session_aggregate_for_progress(ues: list[UserExercise]) -> Optional[dict[str, Any]]:
    """Самая поздняя сессия (по max created_at подходов) среди переданных подходов."""
    if not ues:
        return None
    groups: dict[tuple, list[UserExercise]] = defaultdict(list)
    for ue in ues:
        groups[(ue.training_date, ue.training_id)].append(ue)
    best_key: Optional[tuple] = None
    best_end: Optional[datetime] = None
    for key, group in groups.items():
        ends = [u.created_at for u in group if u.created_at]
        if not ends:
            continue
        mx = max(ends)
        if best_end is None or mx > best_end:
            best_end = mx
            best_key = key
    if best_key is None:
        return None
    g = groups[best_key]
    sets_count = 0
    total_reps = 0
    tonnage = 0.0
    for ue in g:
        if not _user_exercise_counts_as_logged_set(ue):
            continue
        sets_count += 1
        r = int(ue.reps or 0)
        total_reps += r
        if ue.weight is not None:
            tonnage += float(ue.weight) * r
    return {
        "training_date": best_key[0].isoformat(),
        "training_id": best_key[1],
        "sets_count": sets_count,
        "total_reps": total_reps,
        "tonnage": round(tonnage, 2),
    }


async def _filter_user_exercises_for_current_session(ut: UserTraining) -> list[UserExercise]:
    filters = _user_exercise_filters_for_training_session(ut)
    if filters is None:
        return []
    return await UserExerciseDAO.find_all(**filters)


async def _build_exercise_progress_vs_history(
    *,
    exercises_list: list[dict],
    by_ex_cur: dict[int, dict],
    id_to_ex_cur: dict[int, Exercise],
    current_ut: UserTraining,
) -> list[dict[str, Any]]:
    """
    Прогресс по каждому упражнению текущей сессии относительно последнего раза, когда выполнялось
    то же движение: по exercise_reference_id (предпочтительно) или по exercise_id, если ссылки нет.
    Не привязано к «прошлой тренировке» из meta — ищется последняя историческая сессия в прошлом.
    """
    current_ues = await _filter_user_exercises_for_current_session(current_ut)
    exclude_ids = [ue.id for ue in current_ues]
    ends = [ue.created_at for ue in current_ues if ue.created_at]
    created_before = min(ends) if ends else None

    ref_ids = sorted(
        {ex.exercise_reference_id for ex in id_to_ex_cur.values() if ex.exercise_reference_id}
    )
    fallback_eids = [
        eid
        for eid, ex in id_to_ex_cur.items()
        if ex.exercise_reference_id is None
    ]

    rows: list[tuple[UserExercise, Optional[int], int]] = []
    if current_ut.user_id is not None or current_ut.anonymous_session_id is not None:
        rows = await UserExerciseDAO.find_historical_sets_for_exercise_progress(
            user_id=current_ut.user_id,
            anonymous_session_id=current_ut.anonymous_session_id,
            exercise_reference_ids=ref_ids,
            exercise_ids_fallback=fallback_eids,
            exclude_user_exercise_ids=exclude_ids,
            created_before=created_before,
        )

    hist_by_ref: dict[int, list[UserExercise]] = defaultdict(list)
    hist_by_eid: dict[int, list[UserExercise]] = defaultdict(list)
    for ue, ref_id, _ex_pk in rows:
        if ref_id is not None:
            hist_by_ref[ref_id].append(ue)
        hist_by_eid[ue.exercise_id].append(ue)

    last_by_ref: dict[int, Optional[dict[str, Any]]] = {
        rid: _last_session_aggregate_for_progress(ues)
        for rid, ues in hist_by_ref.items()
    }
    last_by_eid: dict[int, Optional[dict[str, Any]]] = {
        eid: _last_session_aggregate_for_progress(ues)
        for eid, ues in hist_by_eid.items()
    }

    tid_set: set[int] = set()
    for h in list(last_by_ref.values()) + list(last_by_eid.values()):
        if h:
            tid_set.add(h["training_id"])
    tid_to_uuid: dict[int, str] = {}
    if tid_set:
        trs = await TrainingDAO.find_in("id", list(tid_set))
        tid_to_uuid = {t.id: str(t.uuid) for t in trs}

    uuid_to_eid = {str(ex.uuid): eid for eid, ex in id_to_ex_cur.items()}
    progress_rows: list[dict[str, Any]] = []

    for row in exercises_list:
        eid = uuid_to_eid.get(str(row.get("exercise_uuid") or ""))
        if eid is None:
            continue
        ex = id_to_ex_cur.get(eid)
        if ex is None:
            continue
        cur = by_ex_cur[eid]
        c_sets = int(cur["sets_count"])
        c_reps = int(cur["total_reps"])
        c_ton = float(cur["tonnage"])

        hist: Optional[dict[str, Any]] = None
        basis: str
        if ex.exercise_reference_id is not None:
            hist = last_by_ref.get(ex.exercise_reference_id)
            basis = "exercise_reference_id"
        else:
            hist = last_by_eid.get(eid)
            basis = "exercise_id"

        has_hist = hist is not None
        p_sets = int(hist["sets_count"]) if hist else None
        p_reps = int(hist["total_reps"]) if hist else None
        p_ton = float(hist["tonnage"]) if hist else None

        entry: dict[str, Any] = {
            "exercise_uuid": str(ex.uuid),
            "exercise_id": eid,
            "exercise_reference_id": ex.exercise_reference_id,
            "caption": ex.caption,
            "match_basis": basis,
            "note": (
                "Сравнение с последней завершённой сессией того же движения в архиве подходов "
                "(по exercise_reference_id, если есть; иначе по тому же exercise_id — обычно только "
                "повтор того же шаблона тренировки)."
            ),
            "history_training_date": hist["training_date"] if hist else None,
            "history_training_uuid": tid_to_uuid.get(hist["training_id"]) if hist else None,
            "sets_count": _triple(c_sets, p_sets, has_hist),
            "total_reps": _triple(c_reps, p_reps, has_hist),
            "tonnage": _triple(round(c_ton, 2), round(p_ton, 2) if p_ton is not None else None, has_hist),
        }
        progress_rows.append(entry)

    return progress_rows


async def _aggregate_user_training_by_exercises(
    user_training: UserTraining,
) -> tuple[
    Optional[int],
    Optional[float],
    list[dict],
    int,
    int,
    int,
    float,
    dict[int, dict],
]:
    """
    Считает длительность и агрегаты по user_exercise для сессии user_training.
    Подходы с весом 0 и повторениями 0 в суммарную статистику не входят.
    Возвращает также by_exercise_id для сопоставления по exercise_reference_id.
    """
    duration_seconds: Optional[int] = None
    duration_minutes: Optional[float] = None
    if user_training.created_at and user_training.completed_at:
        delta = user_training.completed_at - user_training.created_at
        duration_seconds = max(0, int(delta.total_seconds()))
        duration_minutes = round(duration_seconds / 60.0, 2)

    ue_filters = _user_exercise_filters_for_training_session(user_training)
    user_exercises = (
        await UserExerciseDAO.find_all(**ue_filters)
        if ue_filters
        else []
    )

    by_exercise: dict[int, dict] = {}
    for row in user_exercises:
        if not _user_exercise_counts_as_logged_set(row):
            continue
        exercise_id = row.exercise_id
        if exercise_id is None:
            continue

        item = by_exercise.setdefault(
            exercise_id,
            {
                "sets_count": 0,
                "total_reps": 0,
                "tonnage": 0.0,
            },
        )
        item["sets_count"] += 1
        reps = int(row.reps or 0)
        item["total_reps"] += reps
        if row.weight is not None:
            item["tonnage"] += float(row.weight) * reps

    exercise_ids = list(by_exercise.keys())
    id_to_exercise: dict = {}
    if exercise_ids:
        exercises = await ExerciseDAO.find_in("id", exercise_ids)
        id_to_exercise = {e.id: e for e in exercises}

    exercises_summary: list[dict] = []
    total_tonnage = 0.0
    total_sets = 0
    total_reps = 0
    for exercise_id, agg in by_exercise.items():
        ex = id_to_exercise.get(exercise_id)
        ex_tonnage = round(float(agg["tonnage"]), 2)
        total_tonnage += ex_tonnage
        total_sets += int(agg["sets_count"])
        total_reps += int(agg["total_reps"])
        exercises_summary.append(
            {
                "exercise_uuid": str(ex.uuid) if ex else "",
                "caption": ex.caption if ex else None,
                "sets_count": int(agg["sets_count"]),
                "total_reps": int(agg["total_reps"]),
                "tonnage": ex_tonnage,
            }
        )

    return (
        duration_seconds,
        duration_minutes,
        exercises_summary,
        len(by_exercise),
        total_sets,
        total_reps,
        total_tonnage,
        by_exercise,
    )


def _by_exercise_metrics(
    by_exercise: dict[int, dict], id_to_exercise: dict[int, Optional[Exercise]]
) -> tuple[dict[int, dict], dict[int, dict]]:
    """Группировка по exercise_id и по exercise_reference_id (если есть)."""
    by_ref: dict[int, dict] = {}
    merged_by_id: dict[int, dict] = {}
    for eid, agg in by_exercise.items():
        ex = id_to_exercise.get(eid)
        merged_by_id[eid] = {
            "sets_count": int(agg["sets_count"]),
            "total_reps": int(agg["total_reps"]),
            "tonnage": float(agg["tonnage"]),
            "exercise_reference_id": ex.exercise_reference_id if ex else None,
        }
        ref_id = ex.exercise_reference_id if ex else None
        if ref_id is None:
            continue
        b = by_ref.setdefault(
            ref_id,
            {"sets_count": 0, "total_reps": 0, "tonnage": 0.0},
        )
        b["sets_count"] += int(agg["sets_count"])
        b["total_reps"] += int(agg["total_reps"])
        b["tonnage"] += float(agg["tonnage"])
    return merged_by_id, by_ref


def _tonnage_and_sets_for_weighted_exercises(
    by_exercise: dict[int, dict], id_to_exercise: dict[int, Optional[Exercise]]
) -> tuple[float, int]:
    """
    Тоннаж и число подходов только у упражнений с флагом with_weight=True (с внешней нагрузкой).
    Тоннаж — как в агрегате: сумма weight*reps по подходам (без веса в строке — 0 к тоннажу).
    """
    tonnage = 0.0
    sets = 0
    for eid, agg in by_exercise.items():
        ex = id_to_exercise.get(eid)
        if ex is None or ex.with_weight is not True:
            continue
        sets += int(agg["sets_count"])
        tonnage += float(agg["tonnage"])
    return tonnage, sets


def _avg_tonnage_per_set_prefer_weighted(
    w_ton: float,
    w_sets: int,
    total_ton: float,
    total_sets: int,
) -> Optional[float]:
    """
    Средний тоннаж на подход: сначала только по with_weight=true; если таких подходов нет —
    по всей тренировке (total_ton / total_sets), чтобы прошлые сессии без флага не давали previous=null.
    """
    if w_sets > 0:
        return round(w_ton / w_sets, 3)
    if total_sets > 0:
        return round(total_ton / total_sets, 3)
    return None


async def compute_user_training_summary_for_row(user_training: UserTraining) -> dict:
    """
    Итоги тренировки по уже загруженной строке user_training.
    """
    if not user_training.training_id:
        return {"error": "training_id_not_found"}

    (
        duration_seconds,
        duration_minutes,
        exercises_summary,
        completed_exercises_count,
        total_sets,
        total_reps,
        total_tonnage,
        by_exercise,
    ) = await _aggregate_user_training_by_exercises(user_training)

    training_uuid: Optional[str] = None
    training_obj = await TrainingDAO.find_one_or_none(id=user_training.training_id)
    if training_obj:
        training_uuid = str(training_obj.uuid)

    return {
        "user_training_uuid": str(user_training.uuid),
        "training_uuid": training_uuid,
        "training_duration_seconds": duration_seconds,
        "training_duration_minutes": duration_minutes,
        "completed_exercises_count": completed_exercises_count,
        "total_sets": total_sets,
        "total_reps": total_reps,
        "total_tonnage": round(total_tonnage, 2),
        "exercises": exercises_summary,
        "_by_exercise_id": by_exercise,
    }


async def build_user_training_summary(*, user_training_uuid: UUID) -> dict:
    """
    Подвести итоги тренировки по user_training_uuid.
    Расчеты делаются по user_exercise c совпадающим training_id.
    """
    user_training = await UserTrainingDAO.find_one_or_none(uuid=user_training_uuid)
    if not user_training:
        return {"error": "user_training_not_found"}
    data = await compute_user_training_summary_for_row(user_training)
    if data.get("error"):
        return data
    data.pop("_by_exercise_id", None)
    return data


LOAD_INDEX_NOTE = (
    "Индекс сессии ~100 соответствует прошлой тренировке из пары сравнения; >100 — суммарно больше "
    "объёма по ключевым метрикам; <100 — меньше. Поле index — отклонение от базы 100 в пунктах. "
    "Подробная формула — в поле formula."
)


async def build_user_training_summary_vs_previous(*, user_training_uuid: UUID) -> dict:
    """
    Итоги текущей тренировки + сравнение с предыдущей по правилам:
    - при user_program_plan_id: предыдущая с тем же training_type (если тип пуст — по тому же training_id);
    - при отсутствии плана: предыдущая с тем же training_id.
    Предыдущая ищется среди PASSED, строго раньше по (training_date, created_at, id).

    Каждый числовой показатель — объект { current, previous, index }, где index — % к прошлой тренировке.
    Доп. метрики — в extra.
    """
    current = await UserTrainingDAO.find_one_or_none(uuid=user_training_uuid)
    if not current:
        return {"error": "user_training_not_found"}

    current_data = await compute_user_training_summary_for_row(current)
    if current_data.get("error"):
        return current_data

    exercises_list = list(current_data.get("exercises") or [])
    by_ex_cur = current_data.pop("_by_exercise_id", None) or {}
    exercise_ids_cur = list(by_ex_cur.keys())
    id_to_ex_cur: dict = {}
    if exercise_ids_cur:
        rows = await ExerciseDAO.find_in("id", exercise_ids_cur)
        id_to_ex_cur = {e.id: e for e in rows}
    _, by_ref_cur = _by_exercise_metrics(by_ex_cur, id_to_ex_cur)

    match_mode = (
        "training_type"
        if current.user_program_plan_id and (current.training_type or "").strip()
        else "training_id"
    )

    w_ton_cur, w_sets_cur = _tonnage_and_sets_for_weighted_exercises(by_ex_cur, id_to_ex_cur)

    previous = await UserTrainingDAO.find_previous_for_progress_comparison(current)
    prev_data: Optional[dict] = None
    by_ex_prev: dict[int, dict] = {}
    id_to_ex_prev: dict = {}
    by_ref_prev: dict[int, dict] = {}

    meta: dict[str, Any] = {
        "has_previous": False,
        "previous_user_training_uuid": None,
        "previous_training_date": None,
        "match_mode": match_mode,
    }

    has_prev = False
    if previous:
        prev_data = await compute_user_training_summary_for_row(previous)
        if not prev_data.get("error"):
            has_prev = True
            meta["has_previous"] = True
            meta["previous_user_training_uuid"] = str(previous.uuid)
            meta["previous_training_date"] = previous.training_date.isoformat()
            by_ex_prev = prev_data.pop("_by_exercise_id", None) or {}
            exercise_ids_prev = list(by_ex_prev.keys())
            if exercise_ids_prev:
                rows_p = await ExerciseDAO.find_in("id", exercise_ids_prev)
                id_to_ex_prev = {e.id: e for e in rows_p}
            _, by_ref_prev = _by_exercise_metrics(by_ex_prev, id_to_ex_prev)

    def cd(key: str) -> Any:
        return current_data.get(key)

    def pd(key: str) -> Any:
        return prev_data.get(key) if prev_data else None

    c_sec = cd("training_duration_seconds")
    p_sec = pd("training_duration_seconds") if has_prev else None
    c_min = cd("training_duration_minutes")
    p_min = pd("training_duration_minutes") if has_prev else None
    c_sets = int(current_data.get("total_sets") or 0)
    p_sets = int(prev_data.get("total_sets") or 0) if has_prev else None
    c_reps = int(current_data.get("total_reps") or 0)
    p_reps = int(prev_data.get("total_reps") or 0) if has_prev else None
    c_ton = float(current_data.get("total_tonnage") or 0)
    p_ton = float(prev_data.get("total_tonnage") or 0) if has_prev else None
    c_ex = int(current_data.get("completed_exercises_count") or 0)
    p_ex = int(prev_data.get("completed_exercises_count") or 0) if has_prev else None

    w_ton_prev, w_sets_prev = (0, 0)
    if has_prev:
        w_ton_prev, w_sets_prev = _tonnage_and_sets_for_weighted_exercises(by_ex_prev, id_to_ex_prev)

    avg_load_cur = _avg_tonnage_per_set_prefer_weighted(
        w_ton_cur, w_sets_cur, c_ton, c_sets
    )
    avg_load_prev = (
        _avg_tonnage_per_set_prefer_weighted(
            w_ton_prev, w_sets_prev, p_ton or 0, p_sets or 0
        )
        if has_prev
        else None
    )

    rpm_cur = round(c_reps / c_min, 2) if c_min else None
    rpm_prev = round(p_reps / p_min, 2) if has_prev and p_min else None

    session_load: dict[str, Any] = {
        "current": None,
        "previous": None,
        "index": None,
        "note": LOAD_INDEX_NOTE,
        "formula": SESSION_LOAD_INDEX_FORMULA,
    }
    if has_prev and prev_data:
        r_ton = _ratio_clamped(c_ton, p_ton or 0)
        r_rep = _ratio_clamped(c_reps, p_reps or 0)
        r_set = _ratio_clamped(c_sets, p_sets or 0)
        r_ex = _ratio_clamped(c_ex, p_ex or 0)
        composite = round(100.0 * (r_ton * r_rep * r_set * r_ex) ** 0.25, 2)
        session_load["current"] = composite
        session_load["previous"] = 100.0
        session_load["index"] = round(composite - 100.0, 2)

    shared_refs = set(by_ref_cur.keys()) & set(by_ref_prev.keys()) if has_prev else set()
    improved = regressed = same = 0
    top_moves: list[dict] = []
    if has_prev:
        for ref_id in sorted(shared_refs):
            t_cur = float(by_ref_cur[ref_id]["tonnage"])
            t_prev_v = float(by_ref_prev[ref_id]["tonnage"])
            top_moves.append(
                {
                    "exercise_reference_id": ref_id,
                    "tonnage": _triple(round(t_cur, 2), round(t_prev_v, 2), True),
                }
            )
            if t_cur > t_prev_v + 1e-6:
                improved += 1
            elif t_cur < t_prev_v - 1e-6:
                regressed += 1
            else:
                same += 1
        if len(top_moves) > 8:
            top_moves.sort(
                key=lambda x: abs((x["tonnage"].get("index") or 0.0)),
                reverse=True,
            )
            top_moves = top_moves[:8]

    reps_per_set_cur = round(c_reps / c_sets, 2) if c_sets else None
    reps_per_set_prev = (
        round(p_reps / p_sets, 2) if has_prev and p_sets else None
    )
    tpe_cur = round(c_ton / c_ex, 2) if c_ex else None
    tpe_prev = round(p_ton / p_ex, 2) if has_prev and p_ex else None
    tpm_cur = round(c_ton / c_min, 2) if c_min else None
    tpm_prev = round(p_ton / p_min, 2) if has_prev and p_min else None
    w_share_cur = (
        round(100.0 * w_sets_cur / c_sets, 2) if c_sets else None
    )
    w_share_prev = (
        round(100.0 * w_sets_prev / p_sets, 2) if has_prev and p_sets else None
    )

    extra: dict[str, Any] = {
        "reps_per_set": _triple(reps_per_set_cur, reps_per_set_prev, has_prev),
        "tonnage_per_completed_exercise": _triple(tpe_cur, tpe_prev, has_prev),
        "tonnage_per_minute": _triple(tpm_cur, tpm_prev, has_prev),
        "weighted_sets_share_pct": _triple(w_share_cur, w_share_prev, has_prev),
        "weighted_tonnage_share_pct": _triple(
            round(100.0 * w_ton_cur / c_ton, 2) if c_ton else None,
            round(100.0 * w_ton_prev / p_ton, 2) if has_prev and (p_ton or 0) > 0 else None,
            has_prev,
        ),
    }
    if has_prev:
        extra["exercise_tonnage_outcomes"] = {
            "shared_exercise_references_count": len(shared_refs),
            "improved": improved,
            "regressed": regressed,
            "unchanged": same,
            "net_balance": improved - regressed,
        }
        extra["top_exercise_tonnage_moves"] = top_moves

    exercise_progress = await _build_exercise_progress_vs_history(
        exercises_list=exercises_list,
        by_ex_cur=by_ex_cur,
        id_to_ex_cur=id_to_ex_cur,
        current_ut=current,
    )

    return {
        "user_training_uuid": str(current_data["user_training_uuid"]),
        "training_uuid": current_data.get("training_uuid"),
        "meta": meta,
        "training_duration_seconds": _triple(c_sec, p_sec, has_prev),
        "training_duration_minutes": _triple(c_min, p_min, has_prev),
        "completed_exercises_count": _triple(c_ex, p_ex, has_prev),
        "total_sets": _triple(c_sets, p_sets, has_prev),
        "total_reps": _triple(c_reps, p_reps, has_prev),
        "total_tonnage": _triple(round(c_ton, 2), round(p_ton, 2) if p_ton is not None else None, has_prev),
        "avg_tonnage_per_weighted_set": _triple(avg_load_cur, avg_load_prev, has_prev),
        "reps_per_minute": _triple(rpm_cur, rpm_prev, has_prev),
        "session_load_index": session_load,
        "exercises": exercises_list,
        "exercise_progress": exercise_progress,
        "extra": extra,
    }
