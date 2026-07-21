from fastapi import FastAPI
from threading import Thread
import time

from app.queue_consumer import start_consuming

app = FastAPI(title="Notification Service", version="1.0.0")

# Background comnsumer thread
consumer_thread = None

def run_consumer():
    """Run the queue consumer in background"""
    time.sleep(2) # Give FastAPI time to start before connecting to RabbitMQ
    start_consuming()


@app.on_event("startup")
async def startup_event():
    """Start background consumer on startup"""
    global consumer_thread
    
    consumer_thread = Thread(target=run_consumer, daemon=True)
    consumer_thread.start()

    print("Notification Service started and background consumer thread initiated.")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "notification-service",
        "version": "1.0.0",
        "consumer_active": consumer_thread is not None and consumer_thread.is_alive()
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "notification-service",
        "description": "Consumes order notifications from RabbitMQ and simulates sending email notifications.",
        "endpoints": {
            "/health": "Health check endpoint",
            "/": "Root endpoint with service description"
        }   
    }