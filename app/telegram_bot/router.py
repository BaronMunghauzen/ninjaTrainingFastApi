import re
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, Request
from sqlalchemy import func, select

from app.anonymous_session.models import AnonymousSession
from app.database import async_session_maker
from app.logger import logger
from app.subscriptions.models import Payment, PaymentStatusEnum
from app.telegram_service import telegram_service
from app.user_training.models import TrainingStatus, UserTraining
from app.users.models import User
from app.config import settings


router = APIRouter(prefix="/telegram", tags=["telegram-bot"])


def _month_start(dt: date) -> date:
    return date(dt.year, dt.month, 1)


def _next_month_start(dt: date) -> date:
    if dt.month == 12:
        return date(dt.year + 1, 1, 1)
    return date(dt.year, dt.month + 1, 1)


def _parse_period_from_text(text: str) -> Tuple[date, date, str]:
    """
    Returns inclusive date range [start_date, end_date] and human-readable label.
    Supported:
      - "stat YYYY-MM"
      - "stat YYYY-MM..YYYY-MM"
      - "stat YYYY-MM-DD YYYY-MM-DD"
      - "stat from YYYY-MM-DD to YYYY-MM-DD"
      - "stat month" (current month)
    """
    text_l = (text or "").strip().lower()
    today = datetime.now(timezone.utc).date()

    # Explicit day range: YYYY-MM-DD YYYY-MM-DD
    m = re.search(r"(\d{4}-\d{2}-\d{2})\s+(\d{4}-\d{2}-\d{2})", text_l)
    if m:
        d1 = date.fromisoformat(m.group(1))
        d2 = date.fromisoformat(m.group(2))
        if d2 < d1:
            d1, d2 = d2, d1
        return d1, d2, f"{d1.isoformat()}..{d2.isoformat()}"

    # Explicit day range with "from ... to ..."
    m = re.search(r"(?:from|с)\s+(\d{4}-\d{2}-\d{2})\s+(?:to|по)\s+(\d{4}-\d{2}-\d{2})", text_l)
    if m:
        d1 = date.fromisoformat(m.group(1))
        d2 = date.fromisoformat(m.group(2))
        if d2 < d1:
            d1, d2 = d2, d1
        return d1, d2, f"{d1.isoformat()}..{d2.isoformat()}"

    # Month range: YYYY-MM..YYYY-MM
    m = re.search(r"(\d{4}-\d{2})\s*\.\.\s*(\d{4}-\d{2})", text_l)
    if m:
        m1 = date.fromisoformat(f"{m.group(1)}-01")
        m2 = date.fromisoformat(f"{m.group(2)}-01")
        if m2 < m1:
            m1, m2 = m2, m1
        start = _month_start(m1)
        end = _next_month_start(m2) - timedelta(days=1)
        return start, end, f"{m1.strftime('%Y-%m')}..{m2.strftime('%Y-%m')}"

    # Single month: YYYY-MM
    m = re.search(r"\b(\d{4}-\d{2})\b", text_l)
    if m:
        m1 = date.fromisoformat(f"{m.group(1)}-01")
        start = _month_start(m1)
        end = _next_month_start(m1) - timedelta(days=1)
        return start, end, m1.strftime("%Y-%m")

    # Current month fallback for plain "stats"
    start = _month_start(today)
    end = today
    return start, end, f"{start.strftime('%Y-%m')} (to today)"


async def _count_total(model, dt_col, start_dt: datetime, end_dt_exclusive: datetime, *, extra_filters=None) -> int:
    filters = [dt_col >= start_dt, dt_col < end_dt_exclusive]
    if extra_filters:
        filters.extend(extra_filters)
    async with async_session_maker() as session:
        result = await session.execute(select(func.count(model.id)).where(*filters))
    return int(result.scalar() or 0)


async def _count_by_month(model, dt_col, start_dt: datetime, end_dt_exclusive: datetime, *, extra_filters=None) -> Dict[str, int]:
    filters = [dt_col >= start_dt, dt_col < end_dt_exclusive]
    if extra_filters:
        filters.extend(extra_filters)
    async with async_session_maker() as session:
        result = await session.execute(
            select(func.date_trunc("month", dt_col).label("m"), func.count(model.id))
            .where(*filters)
            .group_by("m")
            .order_by("m")
        )
        rows = result.all()
    out: Dict[str, int] = {}
    for month_dt, cnt in rows:
        if month_dt is None:
            continue
        out[month_dt.strftime("%Y-%m")] = int(cnt or 0)
    return out


def _merge_month_keys(*series: Dict[str, int]) -> List[str]:
    keys = set()
    for s in series:
        keys.update(s.keys())
    return sorted(keys)


def _format_stats_message(period_label: str, totals: Dict[str, int], monthly: Dict[str, Dict[str, int]]) -> str:
    lines = [
        "📊 <b>Статистика</b>",
        f"🗓 Период: <b>{period_label}</b>",
        "",
        "<b>Итого за период</b>",
        f"• Новые anonymous sessions: <b>{totals['anonymous_sessions']}</b>",
        f"• Новые регистрации: <b>{totals['users']}</b>",
        f"• Успешные оплаты: <b>{totals['payments_succeeded']}</b>",
        f"• Завершенные тренировки (PASSED): <b>{totals['user_training_passed']}</b>",
        "",
        "<b>По месяцам</b>",
    ]
    months = _merge_month_keys(
        monthly["anonymous_sessions"],
        monthly["users"],
        monthly["payments_succeeded"],
        monthly["user_training_passed"],
    )
    if not months:
        lines.append("Нет данных за период.")
        return "\n".join(lines)

    for ym in months:
        lines.append(
            f"\n<b>{ym}</b>\n"
            f"• anon: {monthly['anonymous_sessions'].get(ym, 0)}\n"
            f"• users: {monthly['users'].get(ym, 0)}\n"
            f"• payments: {monthly['payments_succeeded'].get(ym, 0)}\n"
            f"• passed trainings: {monthly['user_training_passed'].get(ym, 0)}"
        )
    return "\n".join(lines)


def _extract_message_meta(update: dict) -> Tuple[Optional[int], Optional[str], Optional[int]]:
    msg = update.get("message") or update.get("edited_message") or {}
    chat = msg.get("chat") or {}
    from_user = msg.get("from") or {}
    chat_id = chat.get("id")
    text = msg.get("text")
    user_id = from_user.get("id")
    return chat_id, text, user_id


def _is_authorized_chat(chat_id: Optional[int]) -> bool:
    allowed_chat_id = getattr(settings, "TELEGRAM_CHAT_ID", None)
    if not allowed_chat_id:
        return False
    return str(chat_id) == str(allowed_chat_id)


@router.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Telegram bot webhook for chat commands.
    Supported command examples:
      - "статистика"
      - "статистика 2026-04"
      - "статистика 2026-01..2026-04"
      - "статистика 2026-04-01 2026-04-27"
      - "статистика с 2026-04-01 по 2026-04-27"
    """
    update = await request.json()
    chat_id, text, user_id = _extract_message_meta(update)
    if chat_id is None or not text:
        return {"ok": True}

    if not _is_authorized_chat(chat_id):
        logger.warning(f"Unauthorized telegram chat_id={chat_id}, user_id={user_id}")
        return {"ok": True}

    text_l = text.strip().lower()
    if "статист" not in text_l and "stats" not in text_l and "stat" not in text_l:
        return {"ok": True}

    try:
        start_date, end_date, period_label = _parse_period_from_text(text)
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt_exclusive = datetime.combine(end_date + timedelta(days=1), datetime.min.time())

        totals = {
            "anonymous_sessions": await _count_total(
                AnonymousSession, AnonymousSession.created_at, start_dt, end_dt_exclusive
            ),
            "users": await _count_total(
                User, User.created_at, start_dt, end_dt_exclusive
            ),
            "payments_succeeded": await _count_total(
                Payment,
                Payment.created_at,
                start_dt,
                end_dt_exclusive,
                extra_filters=[Payment.status == PaymentStatusEnum.succeeded],
            ),
            "user_training_passed": await _count_total(
                UserTraining,
                UserTraining.created_at,
                start_dt,
                end_dt_exclusive,
                extra_filters=[UserTraining.status == TrainingStatus.PASSED],
            ),
        }

        monthly = {
            "anonymous_sessions": await _count_by_month(
                AnonymousSession, AnonymousSession.created_at, start_dt, end_dt_exclusive
            ),
            "users": await _count_by_month(
                User, User.created_at, start_dt, end_dt_exclusive
            ),
            "payments_succeeded": await _count_by_month(
                Payment,
                Payment.created_at,
                start_dt,
                end_dt_exclusive,
                extra_filters=[Payment.status == PaymentStatusEnum.succeeded],
            ),
            "user_training_passed": await _count_by_month(
                UserTraining,
                UserTraining.created_at,
                start_dt,
                end_dt_exclusive,
                extra_filters=[UserTraining.status == TrainingStatus.PASSED],
            ),
        }

        message = _format_stats_message(period_label, totals, monthly)
        await telegram_service.send_message(message)
    except Exception as exc:
        logger.error(f"Telegram stats command failed: {exc}", exc_info=True)
        await telegram_service.send_message(
            "❌ Не удалось собрать статистику. Проверьте формат запроса.\n"
            "Примеры:\n"
            "• статистика\n"
            "• статистика 2026-04\n"
            "• статистика 2026-01..2026-04\n"
            "• статистика 2026-04-01 2026-04-27"
        )

    return {"ok": True}
