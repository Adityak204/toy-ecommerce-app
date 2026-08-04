import pika
import json
import os
import logging
from typing import Dict, Any
from app.log_context import get_correlation_id

# Get logger for this module
logger = logging.getLogger(__name__)


def get_rabbitmq_connection() -> pika.BlockingConnection:
    rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
    rabbitmq_port = int(os.getenv("RABBITMQ_PORT", 5672))
    rabbitmq_user = os.getenv("RABBITMQ_USER", "guest")
    rabbitmq_password = os.getenv("RABBITMQ_PASSWORD", "guest")

    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
    parameters = pika.ConnectionParameters(
        host=rabbitmq_host,
        port=rabbitmq_port,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300
    )
    return pika.BlockingConnection(parameters)


def publish_order_notification(order_data: Dict[Any, Any]) -> bool:
    """Publishes an order notification to the RabbitMQ queue."""
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()

        # Declare queue (idempotent operation, will only create if it doesn't exist)
        channel.queue_declare(queue='orders', durable=True)

        # Add correlation id to the message
        correlation_id = get_correlation_id()
        message_payload = {
            "correlation_id": correlation_id,
            "order_data": order_data
        }

        # Publish the message
        message = json.dumps(message_payload, default=str)
        channel.basic_publish(
            exchange='',
            routing_key='orders',
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
                content_type='application/json'
            )
        )

        logger.info(
            "Order notification published",
            extra={
                "event": "order_notification_published",
                "correlation_id": correlation_id,
                "order_id": order_data["id"],
                "queue": "orders",
            }
        )

        connection.close()
        return True
    except Exception as e:
        print(f"Error occurred while publishing order notification: {e}")
        return False