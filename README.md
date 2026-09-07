# Toy E-Commerce App

A microservices-based `e-commerce` application built with `Python`, `FastAPI`, and `Docker`. Designed as a learning project to explore service-oriented architecture patterns including API gateways, message queues, and inter-service communication.

## Features

- Browse and query a product catalog
- Place orders with product validation
- Asynchronous order notifications via RabbitMQ
- Centralized API gateway with Nginx
- Fully containerized with Docker Compose
- Structured logging with correlation IDs for request tracing
- Kubernetes deployment manifests (minikube-ready)

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
- **Structured Logging**: python-json-logger (JSON in production, pretty-printed locally)
- **API Gateway**: Nginx
- **Containerization**: Docker + Docker Compose
- **Orchestration**: Kubernetes (minikube-ready manifests)
- **Package Manager**: uv

## Structured Logging

Each service implements a unified structured logging system with three components:

| File | Purpose |
|---|---|
| `logging_config.py` | Core setup — formatters, filters, `setup_logging()` entry point |
| `log_context.py` | Correlation ID management via Python `contextvars` |
| `middleware/logging_middleware.py` | FastAPI middleware — logs every request with timing and correlation ID |

**How it works:**

- A unique `X-Correlation-Id` is extracted from incoming requests (or generated if absent) and propagated across all services via HTTP headers and RabbitMQ message payloads.
- `ServiceContextFilter` injects `service_name`, `environment`, and `version` into every log record automatically.
- `CorrelationIdFilter` attaches the current correlation ID to every log record.

**Output formats** (controlled by `LOG_FORMAT` env var):

| Format | When | Example |
|---|---|---|
| `pretty` | Local development (Docker Compose) | `2025-01-01 12:00:00 \| INFO \| product-service \| abc-123 \| Products retrieved count=10` |
| `json` | Production (Kubernetes) | `{"timestamp":"2025-01-01T12:00:00Z","level":"info","service_name":"product-service","correlation_id":"abc-123","message":"Products retrieved","count":10}` |

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

### Run with Kubernetes (minikube)

Deploy the entire stack to a local cluster using the manifests in `kubernetes/`.

#### Prerequisites

- [minikube](https://minikube.sigs.k8s.io/docs/start/) with a `kubectl` CLI
- A local Docker daemon

#### Steps

```bash
# 1. Start the minikube cluster
minikube start

# 2. Point your shell at minikube's Docker daemon so images are built into the cluster
eval $(minikube docker-env)

# 3. Build the service images (must run against minikube's Docker daemon)
docker build -t toy-ecommerce-app-product-service:latest ./services/product-service
docker build -t toy-ecommerce-app-order-service:latest ./services/order-service
docker build -t toy-ecommerce-app-notification-service:latest ./services/notification-service

# 4. Apply manifests in dependency order (start dependencies first)
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/rabbitmq/            # RabbitMQ (AMQP broker)
kubectl apply -f kubernetes/product-service/
kubectl apply -f kubernetes/order-service/
kubectl apply -f kubernetes/notification-service/
kubectl apply -f kubernetes/api-gateway/          # Nginx gateway (last)

# 5. Verify all pods are running (all should be Ready)
kubectl -n ecommerce get pods

# 6. Get the API gateway URL and open it in your browser
minikube service nginx-service -n ecommerce --url
```

> **Note:** The service manifests use `imagePullPolicy: Never` and reference local images, so the images **must** be built inside minikube's Docker daemon (step 2–3) before deploying.

All resources are deployed into the `ecommerce` namespace. Useful commands:

```bash
# Inspect deployments and services
kubectl -n ecommerce get deployments
kubectl -n ecommerce get services

# Stream logs from a specific pod (e.g. product-service)
kubectl -n ecommerce logs -f deployment/product-service

# Tear down the application
kubectl delete namespace ecommerce
minikube stop
```

## Project Structure

```
toy-ecommerce-app/
├── docker-compose.yaml          # Multi-service orchestration
├── nginx.conf                   # API gateway configuration (Docker Compose)
├── pyproject.toml               # Python dependencies
├── uv.lock                      # Dependency lockfile
├── kubernetes/                  # K8s manifests (minikube deployment)
│   ├── namespace.yaml           # ecommerce namespace
│   ├── api-gateway/
│   │   ├── nginx-configmap.yaml # Nginx route config
│   │   ├── nginx-deployment.yaml
│   │   └── nginx-service.yaml   # NodePort 30080
│   ├── product-service/
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── order-service/
│   │   ├── configmap.yaml       # Product/RabbitMQ connection config
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── notification-service/
│   │   ├── configmap.yaml       # RabbitMQ connection config
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   └── rabbitmq/
│       ├── rabbitmq-deployment.yaml
│       └── rabbitmq-service.yaml
└── services/
    ├── product-service/
    │   ├── Dockerfile
    │   └── app/
    │       ├── main.py          # FastAPI routes
    │       ├── models.py        # Pydantic schemas
    │       ├── database.py      # In-memory data store
    │       ├── logging_config.py    # Structured logging setup
    │       ├── log_context.py       # Correlation ID context
    │       └── middleware/
    │           └── logging_middleware.py  # Request/correlation logging
    ├── order-service/
    │   ├── Dockerfile
    │   └── app/
    │       ├── main.py          # FastAPI routes
    │       ├── models.py        # Pydantic schemas
    │       ├── database.py      # In-memory data store
    │       ├── queue_client.py  # RabbitMQ publisher
    │       ├── logging_config.py    # Structured logging setup
    │       ├── log_context.py       # Correlation ID context
    │       └── middleware/
    │           └── logging_middleware.py  # Request/correlation logging
    └── notification-service/
        ├── Dockerfile
        └── app/
            ├── main.py          # FastAPI routes
            ├── queue_consumer.py # RabbitMQ consumer
            ├── logging_config.py    # Structured logging setup
            ├── log_context.py       # Correlation ID context
            └── middleware/
                └── logging_middleware.py  # Request/correlation logging
```

## Environment Variables

| Variable | Service | Default (Docker) |
|---|---|---|
| `PRODUCT_SERVICE_URL` | Order Service | `http://product-service:8000` |
| `RABBITMQ_HOST` | Order, Notification | `rabbitmq` |
| `RABBITMQ_PORT` | Order, Notification | `5672` |
| `RABBITMQ_USER` | Order, Notification | `guest` |
| `RABBITMQ_PASSWORD` | Order, Notification | `guest` |

### Logging Variables

| Variable | Service | Default (Docker) | Default (K8s) |
|---|---|---|---|
| `SERVICE_NAME` | All | `unknown` | `<service-name>` |
| `SERVICE_VERSION` | All | `1.0.0` | `1.0.0` |
| `ENVIRONMENT` | All | `development` | `production` |
| `LOG_LEVEL` | All | `INFO` | `INFO` |
| `LOG_FORMAT` | All | `pretty` | `json` |

## Notes

- All data is stored in-memory (Python dicts) and is lost on container restart
- The product catalog is pre-seeded with 10 sample electronics items on each startup
- No authentication or authorization is implemented
- Kubernetes custom service images use `imagePullPolicy: Never` and must be built inside minikube's Docker daemon before deploying
