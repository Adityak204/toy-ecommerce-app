# Kubernetes Deployment FAQ

## How is load balancing managed with replicas in this project?

Load balancing happens at two levels:

### 1. Kubernetes Services (L4 round-robin)
Each `kind: Service` selects pods by label (e.g., `app: product-service`) and kube-proxy distributes traffic across all matching replicas.

- `product-service` → 3 pods
- `order-service` → 2 pods
- `nginx-gateway` → 2 pods
- `notification-service` → 1 pod
- `rabbitmq` → 1 pod

### 2. Nginx (L7 routing/proxy)
Nginx acts as the API gateway. Each `upstream` block points to a **Service name**, not individual pods:

```nginx
upstream product_backend {
    server product-service:8000;
}
```

Nginx sends traffic to the Service's ClusterIP, and kube-proxy then balances across the replica pods.

### End-to-end flow:
1. Client hits NodePort `30080` → kube-proxy balances across 2 Nginx replicas
2. Each Nginx pod routes `/api/products` → `product-service:8000`
3. `product-service` Service balances across 3 product pods

### Key detail:
There's no Ingress controller — the `NodePort` Service on Nginx is the sole cluster entry point. Each Python service runs a single uvicorn worker, so scaling relies entirely on replica count, not multi-worker processes.

---

## How are replicas created on a single worker node in minikube?

Replicas are **pods**, not nodes. In minikube (single node), all 3 `product-service` replicas run as **3 separate pods on the same node**. Each pod is an independent container with its own IP. The Kubernetes Service load balances across all 3 pod IPs, even though they're on the same machine.

In production (multi-node), the scheduler *may* spread replicas across different worker nodes for availability, but that's a scheduling decision, not a requirement.

- **Replicas** = number of pod instances
- **Nodes** = number of machines
- The Service load balances across **pods**, regardless of which node they're on

To verify in minikube:
```bash
kubectl get pods -n ecommerce -o wide
```

---

## How does load balancing across nodes happen automatically in production?

`kube-proxy` runs on every node and watches the Kubernetes API for Service endpoints. When a Service has multiple pods (replicas), kube-proxy creates routing rules (iptables/IPVS) on **each node** so that any pod can reach any other pod's IP. The network layer handles cross-node traffic — no manual configuration needed.

---

## When to use ClusterIP, NodePort, and LoadBalancer Service types?

| Type | Purpose | When to Use |
|------|---------|-------------|
| **ClusterIP** | Internal-only, accessible within cluster | Backend services (product/order services) |
| **NodePort** | Exposes on a static port on every node | Development/minikube, simple access |
| **LoadBalancer** | Provisions a cloud load balancer (ALB/NLB) | Production external access (AWS ALB, GCP LB, etc.) |

### For this project in production:
- `nginx-service` would change from `NodePort` to `LoadBalancer` — this provisions an actual cloud load balancer
- All backend services (`product-service`, `order-service`) stay as `ClusterIP`
- If using an Ingress controller (recommended), use `LoadBalancer` on the Ingress controller instead

### Why LoadBalancer is limited:
It creates one load balancer per Service, which gets expensive with many services. Ingress controllers are preferred — one `LoadBalancer` + Ingress rules route to multiple backend services.

---

## How would an Ingress setup look with nginx-service?

### Architecture
```
Internet/Client
      ↓
Cloud Load Balancer (LoadBalancer type)
      ↓
Ingress Controller Pod (nginx-ingress-controller)
      ↓ (routes based on host/path rules)
product-service:8000
order-service:8001
notification-service:8002
```

### What changes:
- **Current setup:** `nginx-gateway` Deployment (2 replicas) + `nginx-service` NodePort — you maintain custom nginx config
- **Ingress setup:** Install nginx-ingress-controller (pre-built nginx that watches Ingress resources). One `LoadBalancer` Service provisions the cloud LB and sends traffic to the Ingress controller

### Example Ingress Resource:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ecommerce-ingress
  namespace: ecommerce
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$2
spec:
  ingressClassName: nginx
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /api/products
            pathType: Prefix
            backend:
              service:
                name: product-service
                port:
                  number: 8000
          - path: /api/orders
            pathType: Prefix
            backend:
              service:
                name: order-service
                port:
                  number: 8001
          - path: /api/notifications
            pathType: Prefix
            backend:
              service:
                name: notification-service
                port:
                  number: 8002
```

### How Load Balancer links to Ingress:
1. The `LoadBalancer` Service sends all external traffic to the Ingress controller pods
2. The Ingress controller reads Ingress resources from the API server
3. It generates nginx config internally and reloads
4. Traffic flows: Client → Load Balancer → Ingress Controller → Backend Service → Pods

### Comparison:
| Component | Current | With Ingress |
|-----------|---------|--------------|
| Routing config | Manual nginx.conf | Ingress resource (declarative) |
| External access | NodePort :30080 | Cloud Load Balancer (real IP) |
| TLS/SSL | Manual | Automatic via cert-manager annotation |
| Who maintains nginx | You | Ingress controller (managed) |

### Testing in minikube:
```bash
minikube addons enable ingress
```
This installs the nginx-ingress controller without provisioning a cloud LB.
