# KUBERNETES QUICKSTART

Handy reference for deploying and troubleshooting this app on a local **minikube** cluster. Written for both beginners and experienced Kubernetes users — commands first, expected output below.

All resources live in the **`ecommerce`** namespace, so **every** `kubectl` command passes `-n ecommerce`.

> **TL;DR** — the five services are: `nginx-service` (API Gateway), `product-service`, `order-service`, `notification-service`, and `rabbitmq-service`. The only service exposed to your machine is the gateway via **NodePort `30080`**.

---

## 1. Prerequisites

- [minikube](https://minikube.sigs.k8s.io/docs/start/) installed
- `kubectl` CLI installed
- A local Docker daemon (used to build images into minikube)

---

## 2. Build & Deploy

### 2.1 Start minikube

```bash
minikube start --cpus=4 --memory=4096
```

**Expected output** (highlights):

```
😄  minikube v1.x.x on Darwin
✅  Done! kubectl is now configured to use "minikube" cluster and "default" namespace by default
```

### 2.2 Point your shell at minikube's Docker daemon (optional)

```bash
eval $(minikube docker-env)
```

> This is **required** when you don't have pre-built image and want to build them inside minikube's Docker daemon. The manifests use `imagePullPolicy: Never` and reference local `:latest` images, so they must be built *inside* minikube's Docker daemon or the pods will never pull them.

### 2.3 Build the three service images

```bash
docker build -t toy-ecommerce-app-product-service:latest ./services/product-service
docker build -t toy-ecommerce-app-order-service:latest ./services/order-service
docker build -t toy-ecommerce-app-notification-service:latest ./services/notification-service
```

**Expected output** (each build ends with):

```
Successfully built 9f1c2a3b4d5e
Successfully tagged toy-ecommerce-app-product-service:latest
```

#### 2.3.1 (if images are pre-built)

```bash
minikube image load toy-ecommerce-app-product-service:latest
minikube image load toy-ecommerce-app-order-service:latest
minikube image load toy-ecommerce-app-notification-service:latest
```

Using above commands you can manually upload pre-built docker images on minikube.

### 2.4 Apply manifests in dependency order

Dependencies first (RabbitMQ → services → gateway last):

```bash
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/rabbitmq/
kubectl apply -f kubernetes/product-service/
kubectl apply -f kubernetes/order-service/
kubectl apply -f kubernetes/notification-service/
kubectl apply -f kubernetes/api-gateway/
```

**Expected output** (each resource is created):

```
namespace/ecommerce created
deployment.apps/rabbitmq created
service/rabbitmq-service created
deployment.apps/product-service created
service/product-service created
...
deployment.apps/nginx-gateway created
service/nginx-service created
```

### 2.5 Wait for pods to be Ready

```bash
kubectl -n ecommerce wait --for=condition=available deployment --all --timeout=180s
```

---

## 3. Checking Deployment / Pod Status

### All pods

```bash
kubectl -n ecommerce get pods
```

**Expected output** (healthy cluster):

```
NAME                                  READY   STATUS    RESTARTS      AGE
nginx-gateway-7d94b9d5c6-bf2kl        1/1     Running   0             2m
nginx-gateway-7d94b9d5c6-r4mvx        1/1     Running   0             2m
notification-service-5f6dccd4-x2mno   1/1     Running   0             2m
order-service-6b8f4c7d8f-jk3pq        1/1     Running   0             2m
order-service-6b8f4c7d8f-zs7ty        1/1     Running   0             2m
product-service-5c9d7e8f2b-9hq4r      1/1     Running   0             2m
product-service-5c9d7e8f2b-mnb6w      1/1     Running   0             2m
product-service-5c9d7e8f2b-vrt9c      1/1     Running   0             2m
rabbitmq-74d8c9f5b6-8wd5x             1/1     Running   0             2m
```

- **`READY`** = `1/1` means the container is up and passing both liveness and readiness probes.
- **`STATUS`** = `Running` is the healthy state. Anything else (see §8 Debugging) needs attention.

### With more detail (which node, IP, labels)

```bash
kubectl -n ecommerce get pods -o wide
```

**Expected output** adds `NODE`, `IP`, and `NOMINATED NODE` columns:

```
NAME                                  READY   STATUS    RESTARTS      AGE   IP           NODE       NOMINATED NODE
product-service-5c9d7e8f2b-9hq4r      1/1     Running   0             2m    10.244.0.7   minikube   <none>
```

### Deployments

```bash
kubectl -n ecommerce get deployments
```

**Expected output**:

```
NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
nginx-gateway         2/2     2            2           2m
notification-service  1/1     1            1           2m
order-service         2/2     2            2           2m
product-service       3/3     3            3           2m
rabbitmq              1/1     1            1           2m
```

- `READY` column = `available / desired` replicas. If `READY` is less than `DESIRED`, run `kubectl describe` (§8).

### Services

```bash
kubectl -n ecommerce get svc
```

**Expected output**:

```
NAME                  TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)                          AGE
nginx-service         NodePort    10.108.12.34    <none>        80:30080/TCP                     2m
notification-service  ClusterIP   10.107.8.15     <none>        8002/TCP                         2m
order-service         ClusterIP   10.106.7.22     <none>        8001/TCP                         2m
product-service       ClusterIP   10.105.6.11     <none>        8000/TCP                         2m
rabbitmq-service      ClusterIP   10.109.5.99     <none>        5672/TCP,15672/TCP              2m
```

- `nginx-service` is **NodePort** → the only one reachable from your machine (`80:30080`).
- Everything else is **ClusterIP** → reachable only inside the cluster, unless you port-forward (§7).

### Everything at once (pod, svc, deployment, replicaset)

```bash
kubectl -n ecommerce get all
```

**Expected output** — a combined table of every resource kind.

### Check a specific rollout finished

```bash
kubectl -n ecommerce rollout status deployment/product-service
```

**Expected output**:

```
deployment "product-service" successfully rolled out
```

---

## 4. Accessing the API Gateway (External URL)

The gateway is exposed as a NodePort on port **30080** but since we are using minikube which is also hosted as a container on docker so most likely you will get another port number. Run this to get the ready-to-use URL from minikube:

```bash
minikube service nginx-service -n ecommerce --url
```

**Expected output** (this is the URL you open in your browser / use in curl):

```
http://192.168.64.2:50652
```

> The `192.168.64.x` IP is minikube's node IP and varies per machine.

### Quick curl sanity checks (in case of minikube replace 30080 with the correct exposed port)

```bash
# Root / gateway health
curl http://192.168.64.2:30080/

# List products (10 pre-seeded)
curl http://192.168.64.2:30080/api/products

# List orders (empty or seeded)
curl http://192.168.64.2:30080/api/orders
```

**Expected outputs**:

```bash
$ curl http://192.168.64.2:30080/
{"message": "Ecommerce API Gateway", "endpoints": ["/api/products", "/api/orders"]}

$ curl http://192.168.64.2:30080/api/products
[{"id":1,"name":"Building Blocks","description":"...","price":29.99}, ...]
```

### Create an order end-to-end (verifies HTTP + RabbitMQ path)

```bash
curl -X POST http://192.168.64.2:30080/api/orders \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 2, "customer_email": "buyer@example.com"}'
```

**Expected output**:

```bash
{"id":1,"product_id":1,"quantity":2,"customer_email":"buyer@example.com","status":"created","created_at":"..."}
```

---

## 5. Accessing the RabbitMQ Management UI

RabbitMQ serves its web UI on port **15672** (management) inside the cluster. It's a ClusterIP service, so `minikube service` won't give you a URL — you must **port-forward**:

```bash
kubectl -n ecommerce port-forward svc/rabbitmq-service 15672:15672
```

Then open **http://localhost:15672** in your browser.

- **Username / password:** `guest` / `guest`
- **Expected:** the RabbitMQ Management login page. After logging in you should see the `orders` queue (once an order has been placed) in the *Queues and Streams* tab.

> Keep the port-forward terminal running in the foreground while you browse. See §7 for more on port-forwarding.

---

## 6. Logs

### Logs from a specific pod

```bash
kubectl -n ecommerce logs product-service-5c9d7e8f2b-9hq4r
```

**Expected output** — structured JSON or pretty logs (depending on the `LOG_FORMAT` env var), e.g.:

```json
{"asctime": "...", "event": "products_listed", "level": "INFO", "correlation_id": "..."}
```

### Stream logs live (follow)

```bash
kubectl -n ecommerce logs -f product-service-5c9d7e8f2b-9hq4r
```

Press `Ctrl+C` to stop.

### Logs from all pods in a deployment

```bash
kubectl -n ecommerce logs -f deployment/product-service
```

### Logs from the *previous* (crashed) container

Use this when a pod is in `CrashLoopBackOff` — it shows the logs from the last run before it died:

```bash
kubectl -n ecommerce logs <pod-name> --previous
```

### A single real-time peek at the notification consumer

```bash
kubectl -n ecommerce logs -f deployment/notification-service
```

Place an order (§4) and watch the notification service consume it:

```
{"level": "INFO", "event": "notification_email_sent", "order_id": 1, "email": "buyer@example.com"}
```

---

## 7. Port Forwarding

Port-forward lets you reach a ClusterIP service from your machine — great for the RabbitMQ UI and for hitting individual services directly (bypassing the gateway).

| Service                  | Port          | Forward command (run in a terminal)                                   |
|--------------------------|---------------|-----------------------------------------------------------------------|
| RabbitMQ management UI   | `15672`       | `kubectl -n ecommerce port-forward svc/rabbitmq-service 15672:15672`  |
| RabbitMQ AMQP            | `5672`        | `kubectl -n ecommerce port-forward svc/rabbitmq-service 5672:5672`    |
| Product service          | `8000`        | `kubectl -n ecommerce port-forward svc/product-service 8000:8000`     |
| Order service            | `8001`        | `kubectl -n ecommerce port-forward svc/order-service 8001:8001`       |
| Notification service     | `8002`        | `kubectl -n ecommerce port-forward svc/notification-service 8002:8002`|

**Expected output** (once it binds):

```
Forwarding from 127.0.0.1:8000 -> 8000
Forwarding from [::1]:8000 -> 8000
```

Then hit it locally:

```bash
curl http://localhost:8000/products
```

> You can also port-forward a single pod: `kubectl -n ecommerce port-forward pod/<pod-name> 8000:8000`.

---

## 8. Debugging Errors

### 8.1 Get detailed pod info (events, why it's not running)

```bash
kubectl -n ecommerce describe pod <pod-name>
```

**Expected output** sections: `Containers`, `Conditions`, `Events`. The **`Events:`** section at the bottom is the goldmine for errors:

```
Events:
  Type     Reason   Age   From               Message
  ----     ------   ----  ----               -------
  Normal   Scheduled 2m   default-scheduler  Successfully assigned ...
  Normal   Pulled    2m   kubelet            Container image already present on machine
  Normal   Created   2m   kubelet            Created container product-service
  Normal   Started   2m   kubelet            Started container product-service
```

### 8.2 Get cluster events

```bash
kubectl -n ecommerce get events --sort-by='.lastTimestamp'
```

### 8.3 Open a shell inside a running container

```bash
kubectl -n ecommerce exec -it product-service-5c9d7e8f2b-9hq4r -- /bin/sh
```

**Expected output:** you're dropped into a shell inside the container. Test connectivity between services:

```sh
# From inside a pod, can we reach RabbitMQ on the service DNS name?
nslookup rabbitmq-service

# Does the product service resolve?
wget -qO- http://product-service:8000/health
```

Type `exit` to leave.

### 8.4 Common pod states → causes → fixes

| Pod `STATUS`                          | Meaning & likely cause                                                                                                                 | Quick fix                                                                                          |
|---------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| `ImagePullBackOff`                    | Kubelet can't pull the image. Almost always: you forgot `eval $(minikube docker-env)` before building, or images were built on your *host* docker, not minikube's. Doesn't apply to `nginx:alpine`/`rabbitmq:3-management`. | Rebuild images into minikube's daemon (§2.2–2.3), then `kubectl -n ecommerce rollout restart deployment/product-service` (repeat for others). |
| `ErrImagePull`                        | Same as above — transient version.                                                                                                     | Same fix as `ImagePullBackOff`.                                                                    |
| `CrashLoopBackOff`                    | A container starts then keeps dying. Check logs: `kubectl -n ecommerce logs <pod> --previous`.                                         | Inspect the log output and fix the app / env config. Often a bad `RABBITMQ_HOST` or missing ConfigMap. |
| `Pending`                             | Pod can't be scheduled — often no resources or node selector mismatch.                                                                 | `kubectl -n ecommerce describe pod <pod>` → read Events; free resources or check limits.            |
| `Running` but `0/1 Ready`             | Container running but failing readiness probe (`/health`).                                                                             | Logs + `kubectl -n ecommerce describe pod <pod>`; find why `/health` is failing.                    |

### 8.5 Quick loop: logs → describe → exec

The standard 3-step debugging flow:

```bash
# 1. What's broken?
kubectl -n ecommerce get pods

# 2. Why? (events)
kubectl -n ecommerce describe pod <pod-name>

# 3. What is it printing?
kubectl -n ecommerce logs <pod-name> --previous
```

---

## 9. Scaling & Rolling Updates

### Scale a deployment

```bash
kubectl -n ecommerce scale deployment/product-service --replicas=5
```

**Expected output:**

```
deployment.apps/product-service scaled
```

Then confirm the new pods come up:

```bash
kubectl -n ecommerce get pods
```

### Restart all pods of a deployment (e.g. after a config change)

```bash
kubectl -n ecommerce rollout restart deployment/product-service
```

**Expected output:**

```
deployment.apps/product-service restarted
```

### Watch a rollout / rollback

```bash
kubectl -n ecommerce rollout status deployment/product-service
kubectl -n ecommerce rollout undo deployment/product-service   # if a rollout is broken
```

---

## 10. Config & Secrets

### View a ConfigMap

```bash
kubectl -n ecommerce get configmap order-service-config -o yaml
```

**Expected output** shows the keys `PRODUCT_SERVICE_URL`, `RABBITMQ_HOST`, `RABBITMQ_PORT`, etc.

### List all configmaps

```bash
kubectl -n ecommerce get configmaps
```

---

## 11. Cleanup

### Tear down just the app (keeps minikube running)

```bash
kubectl delete namespace ecommerce
```

> Deleting the namespace removes **everything** in it (deployments, services, configmaps). Re-deploy with §2.4.

### Full shutdown (also stops the VM)

```bash
minikube stop
```

### Delete the cluster entirely

```bash
minikube delete
```
