import asyncio

from app.config import settings
from app.logger import logger
from app.telegram_bot.router import process_telegram_stats_update
from app.telegram_service import telegram_service


async def run_telegram_poller(stop: asyncio.Event) -> None:
    """
    Long polling: исходящие запросы getUpdates к Telegram.
    Удобно, когда входящий webhook с интернета до сервера нестабилен.
    Перед стартом снимает webhook через deleteWebhook.
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("Telegram polling: пропуск — нет TELEGRAM_BOT_TOKEN")
        return

    res = await telegram_service.call_raw_api("deleteWebhook", timeout=30.0)
    if res and res.get("ok"):
        logger.info("Telegram: webhook снят (deleteWebhook), используется getUpdates")
    else:
        logger.warning("Telegram: deleteWebhook не подтвердился: %s", res)

    offset = 0
    while not stop.is_set():
        try:
            data = await telegram_service.call_raw_api(
                "getUpdates",
                get_params={"offset": offset, "timeout": 25},
                timeout=35.0,
            )
            if not data:
                await asyncio.sleep(2)
                continue
            if not data.get("ok"):
                logger.warning("Telegram getUpdates ok=false: %s", data)
                await asyncio.sleep(2)
                continue
            for u in data.get("result", []):
                offset = max(offset, u["update_id"] + 1)
                asyncio.create_task(process_telegram_stats_update(u))
        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception("Telegram poller: ошибка цикла")
            await asyncio.sleep(2)
