import pika
import json
import os
import time
from datetime import datetime


def get_rabbitmq_connection():
    """Establish a connection to RabbitMQ."""
    rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
    rabbitmq_port = int(os.getenv("RABBITMQ_PORT", 5672))
    rabbitmq_user = os.getenv("RABBITMQ_USER", "guest")
    rabbitmq_password = os.getenv("RABBITMQ_PASSWORD", "guest")

    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
    parameters = pika.ConnectionParameters(
        host=rabbitmq_host, 
        port=rabbitmq_port, 
        credentials=credentials,
        heartbeat=600,  # Set heartbeat to 10 minutes
        blocked_connection_timeout=300  # Set blocked connection timeout to 5 minutes
    )

    max_retries = 10
    retry_delay = 5  # seconds

    for attempt in range(max_retries):
        try:
            connection = pika.BlockingConnection(parameters)
            print(f"Successfully connected to RabbitMQ on attempt {attempt + 1}.")
            return connection
        except Exception as e:
            print(f"Attempt {attempt + 1} of {max_retries}: Failed to connect to RabbitMQ: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Could not connect to RabbitMQ.")
                raise


def process_order_notification(ch, method, properties, body):
    """Process the order notification message."""
    try:
        order_data = json.loads(body)
        order_id = order_data.get("id")
        customer_email = order_data.get("customer_email")
        product_id = order_data.get("product_id")
        quantity = order_data.get("quantity")
        status = order_data.get("status")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Simulate sending an email notification
        print(f"\n{'='*60}")
        print(f"[{timestamp}] Processing order notification:")
        print(f"Order ID       : {order_id}")
        print(f"Customer Email : {customer_email}")
        print(f"Product ID     : {product_id}")
        print(f"Quantity       : {quantity}")
        print(f"Status         : {status}")
        print(f"\n{'='*60}")
        print(f"✉️ Notification sent to {customer_email} for Order ID: {order_id}.\n")
        print(f"{'='*60}\n")

        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error processing message: {e}")
        # Optionally, you can reject the message and requeue it
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def start_consuming():
    """Start consuming messages from the RabbitMQ queue."""
    connection = get_rabbitmq_connection()
    channel = connection.channel()

    # Declare the queue (make sure it exists)
    channel.queue_declare(queue='orders', durable=True)

    # Set up consumer
    channel.basic_qos(prefetch_count=1)  # Fair dispatch (Set QoS to process one message at a time)
    channel.basic_consume(queue='orders', on_message_callback=process_order_notification)

    print("[*] Notification service is listening for order notifications.")
    print("[*] Waiting for messages in queue 'orders'. To exit press CTRL+C")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Stopping consumer...")
        channel.stop_consuming()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        connection.close()
        print("Connection to RabbitMQ closed.")