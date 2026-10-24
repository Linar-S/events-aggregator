import logging

from src.db.models import Outbox

logger = logging.getLogger(__name__)


async def handle_outbox_event(entry: Outbox) -> None:
    """Обработать одну запись outbox по типу события.

    Пока — заглушка: логирует, что «отправили бы». В Шаге 6
    добавим вызов Capashino для ticket_purchased.
    """
    if entry.event_type == "ticket_purchased":
        logger.info(
            "Would send notification: ticket_id=%s reference_id=%s",
            entry.payload.get("ticket_id"),
            entry.payload.get("ticket_id"),
        )
        logger.info("Message: %r", entry.payload.get("message"))
        return

    logger.warning("Unknown outbox event_type: %s", entry.event_type)
