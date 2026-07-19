import pika
import json
import os
from typing import Dict, Any


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

        # Publish the message
        message = json.dumps(order_data, default=str)
        channel.basic_publish(
            exchange='',
            routing_key='orders',
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
                content_type='application/json'
            )
        )

        print(f"[x] Sent order notification: {order_data['id']}")

        connection.close()
        return True
    except Exception as e:
        print(f"Error occurred while publishing order notification: {e}")
        return False