# Retail Microservices Application

Complete microservices-based retail application with checkout, payment, loyalty, and account services. Deploy locally with Docker Compose or to Google Cloud Platform (GCP) Kubernetes.

## 📋 Overview

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (Nginx)                       │
│              Routes requests to microservices                │
└────────────────────────────┬────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────────┐    ┌──────────────┐    ┌─────────────┐
   │  Account    │    │   Payment    │    │   Loyalty   │
   │  Service    │    │   Service    │    │   Service   │
   │ (Port 5000) │    │ (Port 5001)  │    │ (Port 5002) │
   └─────────────┘    └──────────────┘    └─────────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Checkout       │
                    │  Service        │
                    │  (Port 5003)    │
                    └─────────────────┘
                             │
                    ┌────────▼────────┐
                    │  PostgreSQL DB  │
                    │  Redis Cache    │
                    └─────────────────┘
```

### Microservices

| Service | Port | Responsibility | Key Endpoints |
|---------|------|-----------------|----------------|
| **Account** | 5000 | User management, auth | `/users`, `/auth`, `/login` |
| **Payment** | 5001 | Payment processing | `/payments`, `/payments/{id}`, `/payments/process` |
| **Loyalty** | 5002 | Points & rewards | `/loyalty/{user_id}`, `/rewards`, `/loyalty/{user_id}/add-points` |
| **Checkout** | 5003 | Cart & orders | `/cart/{user_id}`, `/orders`, `/checkout` |

---

## 🚀 Quick Start - Local Development

### Prerequisites

- Docker and Docker Compose installed
- Python 3.9+ (for local testing without Docker)
- 8GB RAM minimum

### Option 1: Run with Docker Compose (Recommended)

```bash
# Clone/download all files into a directory
cd retail-microservices

# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option 2: Run Services Individually

```bash
# Terminal 1: Start Account Service
python account-service.py
# Service running at http://localhost:5000

# Terminal 2: Start Payment Service
python payment-service.py
# Service running at http://localhost:5001

# Terminal 3: Start Loyalty Service
python loyalty-service.py
# Service running at http://localhost:5002

# Terminal 4: Start Checkout Service
python checkout-service.py
# Service running at http://localhost:5003
```

### Test the APIs

```bash
# Health check
curl http://localhost:5000/health
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:5003/health

# Account Service - Create user
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890"
  }'

# Account Service - List users
curl http://localhost:5000/users

# Loyalty Service - Get loyalty info
curl http://localhost:5002/loyalty/user123

# Loyalty Service - Add points
curl -X POST http://localhost:5002/loyalty/user123/add-points \
  -H "Content-Type: application/json" \
  -d '{"points": 100}'

# Checkout Service - Get cart
curl http://localhost:5003/cart/user123

# Checkout Service - Add to cart
curl -X POST http://localhost:5003/cart/user123/add-item \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "prod_001",
    "name": "Laptop",
    "price": 999.99,
    "quantity": 1
  }'

# Payment Service - Process payment
curl -X POST http://localhost:5001/payments/process \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "amount": 999.99,
    "currency": "USD",
    "payment_method": "credit_card"
  }'
```

---

## 🐳 Docker Build & Push (For GCP)

### Build Docker Images

```bash
# Set variables
export PROJECT_ID="your-gcp-project-id"
export REGISTRY="gcr.io/$PROJECT_ID"

# Build all images
docker build -t $REGISTRY/account-service:v1.0.0 -f Dockerfile.account .
docker build -t $REGISTRY/payment-service:v1.0.0 -f Dockerfile.payment .
docker build -t $REGISTRY/loyalty-service:v1.0.0 -f Dockerfile.loyalty .
docker build -t $REGISTRY/checkout-service:v1.0.0 -f Dockerfile.checkout .

# Configure Docker auth
gcloud auth configure-docker

# Push to GCR
docker push $REGISTRY/account-service:v1.0.0
docker push $REGISTRY/payment-service:v1.0.0
docker push $REGISTRY/loyalty-service:v1.0.0
docker push $REGISTRY/checkout-service:v1.0.0
```

---

## ☁️ Deploy to GCP (Google Kubernetes Engine)

### Complete Deployment Guide

Follow the **GCP-DEPLOYMENT-GUIDE.md** file for step-by-step instructions:

1. **Setup GCP Environment**
   - Create GKE cluster
   - Configure gcloud CLI
   - Enable APIs

2. **Build & Push Images**
   - Build Docker images
   - Push to Google Container Registry

3. **Setup Database**
   - Create Cloud SQL instance
   - Setup database and users
   - Configure Cloud SQL Proxy

4. **Deploy Application**
   - Update YAML files with your project ID
   - Deploy microservices
   - Configure ingress and load balancer

5. **Setup Monitoring**
   - View metrics and logs
   - Configure alerts

### Quick Deploy Commands

```bash
# 1. Update YAML with your project ID
sed -i "s/PROJECT_ID/$PROJECT_ID/g" gcp-retail-app.yaml

# 2. Deploy to GCP
gcloud container clusters get-credentials $CLUSTER_NAME --region $REGION
kubectl apply -f gcp-retail-app.yaml
kubectl apply -f gcp-retail-ingress.yaml

# 3. Verify deployment
kubectl get pods -n retail
kubectl get services -n retail
kubectl get ingress -n retail

# 4. Check ingress IP (takes 2-5 minutes to get IP)
kubectl describe ingress retail-ingress -n retail
```

---

## 📁 File Structure

```
retail-microservices/
├── account-service.py          # Account service source code
├── payment-service.py          # Payment service source code
├── loyalty-service.py          # Loyalty service source code
├── checkout-service.py         # Checkout service source code
│
├── Dockerfile.account          # Docker image for account service
├── Dockerfile.payment          # Docker image for payment service
├── Dockerfile.loyalty          # Docker image for loyalty service
├── Dockerfile.checkout         # Docker image for checkout service
│
├── docker-compose.yml          # Local Docker Compose setup
├── nginx.conf                  # API Gateway configuration
│
├── gcp-retail-app.yaml         # GCP Kubernetes manifests (deployments, services)
├── gcp-retail-ingress.yaml     # GCP Ingress & networking configuration
│
├── GCP-DEPLOYMENT-GUIDE.md     # Step-by-step GCP deployment guide
├── README.md                   # This file
```

---

## API Endpoints Reference

### Account Service (`localhost:5000`)

```
GET  /health                    # Health check
GET  /ready                     # Readiness check
GET  /users                     # List all users
GET  /users/{user_id}           # Get user details
POST /users                     # Create new user
PUT  /users/{user_id}           # Update user
POST /auth/login                # User login
POST /auth/logout               # User logout
GET  /metrics                   # Service metrics
```

### Payment Service (`localhost:5001`)

```
GET  /health                    # Health check
GET  /ready                     # Readiness check
GET  /payments                  # List transactions
GET  /payments/{transaction_id} # Get transaction details
POST /payments/process          # Process payment
POST /payments/{id}/refund      # Refund payment
POST /validate-payment-method   # Validate payment method
GET  /metrics                   # Service metrics
```

### Loyalty Service (`localhost:5002`)

```
GET  /health                    # Health check
GET  /ready                     # Readiness check
GET  /loyalty/{user_id}         # Get loyalty info
POST /loyalty/{user_id}/add-points      # Add points
POST /loyalty/{user_id}/redeem          # Redeem points
POST /loyalty/{user_id}/purchase        # Record purchase
GET  /loyalty/rewards           # Get rewards catalog
GET  /metrics                   # Service metrics
```

### Checkout Service (`localhost:5003`)

```
GET  /health                    # Health check
GET  /ready                     # Readiness check
GET  /cart/{user_id}            # Get cart
POST /cart/{user_id}/add-item   # Add to cart
POST /cart/{user_id}/remove-item # Remove from cart
POST /cart/{user_id}/clear      # Clear cart
POST /checkout/{user_id}        # Process checkout
GET  /orders/{order_id}         # Get order details
POST /orders/{order_id}/cancel  # Cancel order
GET  /metrics                   # Service metrics
```

---

## Environment Variables

### Account Service
```
SERVICE_NAME=account-service
SERVICE_VERSION=1.0.0
ENVIRONMENT=production
LOG_LEVEL=INFO
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=retail_db
PORT=5000
```

### Payment Service
```
SERVICE_NAME=payment-service
SERVICE_VERSION=1.0.0
ENVIRONMENT=production
LOG_LEVEL=INFO
PAYMENT_GATEWAY=stripe
DATABASE_HOST=localhost
PORT=5001
```

### Loyalty Service
```
SERVICE_NAME=loyalty-service
SERVICE_VERSION=1.0.0
ENVIRONMENT=production
LOG_LEVEL=INFO
POINTS_MULTIPLIER=1.0
DATABASE_HOST=localhost
PORT=5002
```

### Checkout Service
```
SERVICE_NAME=checkout-service
SERVICE_VERSION=1.0.0
ENVIRONMENT=production
LOG_LEVEL=INFO
TAX_RATE=0.08
DATABASE_HOST=localhost
PORT=5003
```

---

## 🧪 Testing & Workflow Example

### Complete User Flow

```bash
# 1. Create account
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Smith",
    "email": "alice@example.com",
    "phone": "+1555123456"
  }'

# 2. Login
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com"}'

# 3. Add items to cart
curl -X POST http://localhost:5003/cart/alice_example_com/add-item \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "prod_001",
    "name": "Wireless Mouse",
    "price": 29.99,
    "quantity": 2
  }'

curl -X POST http://localhost:5003/cart/alice_example_com/add-item \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "prod_002",
    "name": "USB-C Cable",
    "price": 9.99,
    "quantity": 3
  }'

# 4. View cart
curl http://localhost:5003/cart/alice_example_com

# 5. Get loyalty status
curl http://localhost:5002/loyalty/alice_example_com

# 6. Checkout
curl -X POST http://localhost:5003/checkout/alice_example_com \
  -H "Content-Type: application/json" \
  -d '{
    "shipping_address": {
      "street": "123 Main St",
      "city": "San Francisco",
      "state": "CA",
      "zip": "94102"
    }
  }'

# 7. Process payment
curl -X POST http://localhost:5001/payments/process \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice_example_com",
    "amount": 89.97,
    "currency": "USD",
    "payment_method": "credit_card"
  }'

# 8. Add loyalty points
curl -X POST http://localhost:5002/loyalty/alice_example_com/purchase \
  -H "Content-Type: application/json" \
  -d '{"amount": 89.97}'

# 9. View updated loyalty
curl http://localhost:5002/loyalty/alice_example_com
```

---

## 🔐 Security Features

✅ **Service Authentication**: JWT token support
✅ **Database Encryption**: Passwords stored securely
✅ **API Rate Limiting**: Nginx rate limiting configured
✅ **Health Checks**: Liveness and readiness probes
✅ **Input Validation**: Endpoint validation
✅ **HTTPS/TLS**: SSL support in GCP
✅ **RBAC**: Kubernetes role-based access
✅ **Network Policies**: Service-to-service communication control

---

## 📊 Monitoring & Logging

### Local Monitoring
```bash
# View service logs
docker-compose logs account-service
docker-compose logs payment-service
docker-compose logs loyalty-service
docker-compose logs checkout-service

# Monitor containers
docker stats

# View metrics
curl http://localhost:5000/metrics
curl http://localhost:5001/metrics
curl http://localhost:5002/metrics
curl http://localhost:5003/metrics
```

### GCP Monitoring
```bash
# View pod logs
kubectl logs -n retail -l app=account-service

# View metrics
kubectl top pods -n retail
kubectl top nodes

# View events
kubectl get events -n retail

# Port forward for local testing
kubectl port-forward -n retail svc/account-service 5000:80
```

---

## 🚀 Scaling

### Local Scaling with Docker Compose
```bash
# Scale services (requires modifying docker-compose.yml)
docker-compose up -d --scale account-service=3 --scale payment-service=2
```

### GCP Auto-Scaling
Configured through HPA (Horizontal Pod Autoscaler) in `gcp-retail-app.yaml`:
- Scales based on CPU usage (70% threshold)
- Scales based on memory usage (80% threshold)
- Min replicas: 2, Max replicas: 10-15 (varies by service)

---

## 🔧 Troubleshooting

### Service won't start?
```bash
# Check logs
docker-compose logs <service_name>

# Or for Kubernetes
kubectl describe pod <pod_name> -n retail
kubectl logs <pod_name> -n retail
```

### Can't connect to database?
```bash
# Verify database is running
docker-compose ps postgres

# Or check Cloud SQL
gcloud sql instances describe retail-db
```

### Port conflicts?
```bash
# Change ports in docker-compose.yml or service files
# Default ports: 5000, 5001, 5002, 5003
```

---

## 📚 Learning Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [GCP GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [Microservices Patterns](https://microservices.io/)
- [Cloud Native Development](https://www.cncf.io/)

---

## 🤝 Contributing

To extend this application:

1. **Add new service**: Copy a service template and modify
2. **Add database integration**: Integrate with PostgreSQL/Cloud SQL
3. **Add message queue**: Implement Pub/Sub for async operations
4. **Add caching**: Integrate Redis for performance
5. **Add API gateway features**: Enhance nginx.conf

---

## 📝 License

MIT License - Feel free to use for learning and development

---

## 🎯 Next Steps

1. ✅ Run locally with Docker Compose
2. ✅ Test all API endpoints
3. ✅ Deploy to GCP following the guide
4. ✅ Setup monitoring and logging
5. ✅ Add CI/CD pipeline
6. ✅ Implement real database schema
7. ✅ Add authentication/authorization
8. ✅ Scale and optimize

Happy microservicing! 🚀
