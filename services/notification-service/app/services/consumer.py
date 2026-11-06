import json
import logging
import time
from threading import Thread

import pika
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db.database import SessionLocal
from app.models.notification import Notification

logger = logging.getLogger(__name__)

QUEUE_NAME = "transaction_events"


def process_message(channel, method, properties, body):
    db = SessionLocal()

    try:
        event = json.loads(body.decode("utf-8"))

        event_type = event["event_type"]
        amount = event["amount"]
        reference = event["reference"]

        message = (
            f"Your SecureBank {event_type.lower()} transaction "
            f"of INR {amount} was successful. Reference: {reference}"
        )

        notification = Notification(
            customer_id=int(event["customer_id"]),
            reference=reference,
            event_type=event_type,
            message=message,
            status="SENT",
        )

        db.add(notification)
        db.commit()

        print(f"EMAIL SIMULATION: {message}", flush=True)
        channel.basic_ack(delivery_tag=method.delivery_tag)

    except (ValueError, KeyError, SQLAlchemyError):
        db.rollback()
        logger.exception("Failed to process transaction notification")
        channel.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=False,
        )

    except Exception:
        db.rollback()
        logger.exception("Unexpected notification processing error")
        channel.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=True,
        )

    finally:
        db.close()


def consume_notifications():
    while True:
        connection = None

        try:
            parameters = pika.URLParameters(settings.RABBITMQ_URL)
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()

            channel.queue_declare(
                queue=QUEUE_NAME,
                durable=True,
            )

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue=QUEUE_NAME,
                on_message_callback=process_message,
            )

            logger.info("Listening for transaction events")
            channel.start_consuming()

        except Exception:
            logger.exception("RabbitMQ connection failed; retrying in 5 seconds")
            time.sleep(5)

        finally:
            if connection and connection.is_open:
                connection.close()


def start_consumer():
    thread = Thread(
        target=consume_notifications,
        daemon=True,
        name="notification-consumer",
    )
    thread.start()
