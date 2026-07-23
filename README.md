# Toy E-Commerce App

A microservices-based `e-commerce` application built with `Python`, `FastAPI`, and `Docker`. Designed as a learning project to explore service-oriented architecture patterns including API gateways, message queues, and inter-service communication.

## Features

- Browse and query a product catalog
- Place orders with product validation
- Asynchronous order notifications via RabbitMQ
- Centralized API gateway with Nginx
- Fully containerized with Docker Compose

## Architecture

The application follows a **microservices architecture** with three independent services communicating through `HTTP` and an `asynchronous message queue`.

```
                            ┌──────────────────────┐
                            │       Client         │
                            └──────────┬───────────┘
                                       │
                            ┌──────────▼───────────┐
                            │   Nginx (port 80)    │
                            │    API Gateway       │
                            └──┬───────────────┬───┘
                               │               │
               /api/products   │               │  /api/orders
                               │               │
              ┌────────────────▼──┐   ┌────────▼─────────────┐
              │ Product Service   │   │   Order Service       │
              │ (port 8000)       │   │   (port 8001)         │
              │                   │   │                       │
              │ - Product catalog │   │ - Order management    │
              │ - CRUD operations │   │ - Product validation  │
              └───────────────────┘   │   (HTTP → Product)    │
                                      │ - Publishes events    │
                                      │   (AMQP → RabbitMQ)  │
                                      └──────────┬────────────┘
                                                  │
                                        ┌─────────▼──────────┐
                                        │     RabbitMQ       │
                                        │   (port 5672)      │
                                        └─────────┬──────────┘
                                                  │
                                      ┌───────────▼───────────────┐
                                      │  Notification Service     │
                                      │  (port 8002)              │
                                      │                           │
                                      │ - Consumes order events   │
                                      │ - Simulates email sending │
                                      └───────────────────────────┘
```

### Communication Patterns

| Pattern | Producer | Consumer | Protocol |
|---|---|---|---|
| API Gateway routing | Nginx | Product/Order Service | HTTP |
| Product validation | Order Service | Product Service | HTTP |
| Order events | Order Service | Notification Service | AMQP (RabbitMQ) |

### Services

| Service | Port | Description |
|---|---|---|
| **Nginx** | 80 | API gateway that routes requests to backend services |
| **Product Service** | 8000 | Manages the product catalog with CRUD operations |
| **Order Service** | 8001 | Handles order creation and lifecycle management |
| **Notification Service** | 8002 | Listens for order events and simulates email notifications |
| **RabbitMQ** | 5672 (AMQP), 15672 (UI) | Message broker for asynchronous communication |

## Tech Stack

- **Language**: Python 3.13
- **Web Framework**: FastAPI + Uvicorn
- **Validation**: Pydantic v2
- **HTTP Client**: httpx (async, for inter-service calls)
- **Message Queue**: RabbitMQ 3 (via `pika`)
- **API Gateway**: Nginx
- **Containerization**: Docker + Docker Compose
- **Package Manager**: uv

## Getting Started

### Prerequisites

- Docker and Docker Compose

### Run with Docker Compose

```bash
docker-compose up --build
```

This starts all services. Access them at:

- **API Gateway**: http://localhost:80
- **RabbitMQ Management UI**: http://localhost:15672 (guest/guest)
- **Product Service docs**: http://localhost:8000/docs
- **Order Service docs**: http://localhost:8001/docs
- **Notification Service docs**: http://localhost:8002/docs

### Example API Usage

```bash
# List all products
curl http://localhost:80/api/products

# Get a specific product
curl http://localhost:80/api/products/1

# Create an order
curl -X POST http://localhost:80/api/orders \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 2, "customer_email": "user@example.com"}'

# List all orders
curl http://localhost:80/api/orders
```

## Project Structure

```
toy-ecommerce-app/
├── docker-compose.yaml          # Multi-service orchestration
├── nginx.conf                   # API gateway configuration
├── pyproject.toml               # Python dependencies
├── uv.lock                      # Dependency lockfile
├── kubernetes/                  # (planned) K8s manifests
└── services/
    ├── product-service/
    │   ├── Dockerfile
    │   └── app/
    │       ├── main.py          # FastAPI routes
    │       ├── models.py        # Pydantic schemas
    │       └── database.py      # In-memory data store
    ├── order-service/
    │   ├── Dockerfile
    │   └── app/
    │       ├── main.py          # FastAPI routes
    │       ├── models.py        # Pydantic schemas
    │       ├── database.py      # In-memory data store
    │       └── queue_client.py  # RabbitMQ publisher
    └── notification-service/
        ├── Dockerfile
        └── app/
            ├── main.py          # FastAPI routes
            └── queue_consumer.py # RabbitMQ consumer
```

## Environment Variables

| Variable | Service | Default (Docker) |
|---|---|---|
| `PRODUCT_SERVICE_URL` | Order Service | `http://product-service:8000` |
| `RABBITMQ_HOST` | Order, Notification | `rabbitmq` |
| `RABBITMQ_PORT` | Order, Notification | `5672` |
| `RABBITMQ_USER` | Order, Notification | `guest` |
| `RABBITMQ_PASSWORD` | Order, Notification | `guest` |

## Notes

- All data is stored in-memory (Python dicts) and is lost on container restart
- The product catalog is pre-seeded with 10 sample electronics items on each startup
- No authentication or authorization is implemented
- The `kubernetes/` directory exists for future K8s deployment but is not yet implemented
