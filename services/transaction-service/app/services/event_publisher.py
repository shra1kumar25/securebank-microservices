import json
import logging

import pika

from app.core.config import settings

logger = logging.getLogger(__name__)


def publish_transaction_event(event: dict) -> bool:
    try:
        connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))

        channel = connection.channel()

        channel.queue_declare(
            queue="transaction_events",
            durable=True,
        )

        channel.basic_publish(
            exchange="",
            routing_key="transaction_events",
            body=json.dumps(event),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
            ),
        )

        connection.close()

        logger.info(
            "Transaction event published: %s",
            event.get("event_type"),
        )

        return True

    except Exception:
        logger.exception("Failed to publish transaction event")
        return False
