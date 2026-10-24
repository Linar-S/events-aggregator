import logging

from src.db.models import Outbox
from src.services.capashino import CapashinoClient, CapashinoConflictError

logger = logging.getLogger(__name__)


async def handle_outbox_event(
    entry: Outbox,
    capashino_client: CapashinoClient,
) -> None:
    """Обработать одну запись outbox по типу события."""
    if entry.event_type == "ticket_purchased":
        ticket_id = entry.payload.get("ticket_id")
        message = entry.payload.get("message")

        if not ticket_id or not message:
            raise ValueError(f"Invalid payload for ticket_purchased: {entry.payload}")

        try:
            response = await capashino_client.send_notification(
                message=message,
                reference_id=ticket_id,
                idempotency_key=entry.id,
            )
            logger.info(
                "Notification sent: outbox_id=%s ticket_id=%s response_id=%s",
                entry.id,
                ticket_id,
                response.get("id"),
            )
        except CapashinoConflictError:
            logger.info(
                "Notification already exists (409), marking as sent: outbox_id=%s",
                entry.id,
            )
        return

    logger.warning("Unknown outbox event_type: %s", entry.event_type)
