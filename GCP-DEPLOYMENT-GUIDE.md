# GCP Kubernetes Deployment Guide - Retail Microservices
# Step-by-step guide to deploy the retail application on Google Cloud Platform

## Overview

This guide walks through deploying a microservices-based retail application on Google Cloud Kubernetes Engine (GKE).

### Microservices:
- **Account Service**: User management (signup, login, profiles)
- **Payment Service**: Payment processing and transactions
- **Loyalty Service**: Points and rewards management
- **Checkout Service**: Shopping cart and order management

---

## Prerequisites

1. **GCP Account** with billing enabled
2. **gcloud CLI** installed: https://cloud.google.com/sdk/docs/install
3. **kubectl** installed: https://kubernetes.io/docs/tasks/tools/
4. **Docker** installed (for building images locally)
5. **GCP Project** created

---

## PART 1: Setup GCP Environment

### Step 1: Set Project Variables
```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export CLUSTER_NAME="retail-cluster"
export ZONE="us-central1-a"

# Authenticate with GCP
gcloud auth login
gcloud config set project $PROJECT_ID
```

### Step 2: Create GKE Cluster
```bash
# Create a standard GKE cluster (production-ready)
gcloud container clusters create $CLUSTER_NAME \
  --region $REGION \
  --num-nodes 3 \
  --machine-type n1-standard-2 \
  --enable-stackdriver-kubernetes \
  --enable-autoscaling \
  --min-nodes 3 \
  --max-nodes 10 \
  --enable-autorepair \
  --enable-autoupgrade \
  --addons HttpLoadBalancing,HttpsLoadBalancing \
  --workload-pool=$PROJECT_ID.svc.id.goog

# This creates a production cluster with:
# - 3 initial nodes
# - Auto-scaling enabled (3-10 nodes)
# - Stackdriver monitoring
# - Workload Identity for secure pod authentication
```

### Step 3: Get Cluster Credentials
```bash
# Configure kubectl to connect to your cluster
gcloud container clusters get-credentials $CLUSTER_NAME --region $REGION

# Verify connection
kubectl cluster-info
kubectl get nodes
```

### Step 4: Enable Required GCP APIs
```bash
gcloud services enable container.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudsql.googleapis.com
gcloud services enable cloudkms.googleapis.com
```

---

## PART 2: Build and Push Docker Images to Google Container Registry (GCR)

### Step 5: Build Docker Images
```bash
# Set Docker registry
export REGISTRY="gcr.io/$PROJECT_ID"

# Build Account Service
docker build -t $REGISTRY/account-service:v1.0.0 \
  -f Dockerfile.account .

# Build Payment Service
docker build -t $REGISTRY/payment-service:v1.0.0 \
  -f Dockerfile.payment .

# Build Loyalty Service
docker build -t $REGISTRY/loyalty-service:v1.0.0 \
  -f Dockerfile.loyalty .

# Build Checkout Service
docker build -t $REGISTRY/checkout-service:v1.0.0 \
  -f Dockerfile.checkout .
```

### Step 6: Configure Docker Authentication
```bash
# Configure Docker to authenticate with GCR
gcloud auth configure-docker

# Verify authentication
cat ~/.docker/config.json | grep gcr.io
```

### Step 7: Push Images to GCR
```bash
# Push all images
docker push $REGISTRY/account-service:v1.0.0
docker push $REGISTRY/payment-service:v1.0.0
docker push $REGISTRY/loyalty-service:v1.0.0
docker push $REGISTRY/checkout-service:v1.0.0

# Verify images are pushed
gcloud container images list --repository-url=$REGISTRY
gcloud container images list-tags $REGISTRY/account-service
```

---

## PART 3: Setup Google Cloud SQL Database

### Step 8: Create Cloud SQL Instance
```bash
# Create PostgreSQL instance
gcloud sql instances create retail-db \
  --database-version=POSTGRES_13 \
  --tier=db-f1-micro \
  --region=$REGION \
  --availability-type=REGIONAL \
  --backup-start-time=03:00 \
  --retained-backups-count=7 \
  --retained-transaction-log-days=7

# Get the connection name (you'll need this)
gcloud sql instances describe retail-db --format='value(connectionName)'
# Output: PROJECT_ID:REGION:retail-db
```

### Step 9: Create Database and User
```bash
# Create database
gcloud sql databases create retail_db --instance=retail-db

# Create database user
gcloud sql users create postgres --instance=retail-db --password

# Set password (save this securely)
gcloud sql users set-password postgres --instance=retail-db --password='your-secure-password'
```

### Step 10: Setup Cloud SQL Proxy
```bash
# Create service account for Cloud SQL
gcloud iam service-accounts create cloudsql-sa \
  --display-name="Cloud SQL Service Account"

# Grant Cloud SQL Client role
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:cloudsql-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/cloudsql.client

# Create Cloud SQL Proxy deployment
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cloud-sql-proxy
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cloud-sql-proxy
  template:
    metadata:
      labels:
        app: cloud-sql-proxy
    spec:
      containers:
      - name: cloud-sql-proxy
        image: gcr.io/cloudsql-docker/cloud-sql-proxy:1.33.2
        args:
          - "PROJECT_ID:REGION:retail-db"
          - "-instances=PROJECT_ID:REGION:retail-db=tcp:5432"
        ports:
        - containerPort: 5432
          name: postgres
EOF

# Verify Cloud SQL Proxy is running
kubectl get pods -l app=cloud-sql-proxy
```

---

## PART 4: Deploy Microservices

### Step 11: Update YAML with Your Project ID
```bash
# Replace PROJECT_ID in the manifest
sed -i "s/PROJECT_ID/$PROJECT_ID/g" gcp-retail-app.yaml

# Verify the replacement
grep "gcr.io" gcp-retail-app.yaml
```

### Step 12: Create Static IP Address for Ingress
```bash
# Reserve a global static IP for the ingress
gcloud compute addresses create retail-ip --global

# Get the IP address
gcloud compute addresses describe retail-ip --global --format='value(address)'
# Save this IP for DNS records
```

### Step 13: Update Ingress Configuration
```bash
# Update the Ingress with your domain
# Replace "api.retail.example.com" with your actual domain

# If using a GCP domain or Cloud DNS:
gcloud dns records update api.retail.example.com. \
  --rrdatas=STATIC_IP \
  --ttl=300 \
  --type=A \
  --zone=your-dns-zone
```

### Step 14: Deploy the Application
```bash
# Apply the main microservices deployment
kubectl apply -f gcp-retail-app.yaml

# Verify deployments
kubectl get deployments -n retail
kubectl get pods -n retail

# Watch pods starting up
kubectl get pods -n retail --watch
```

### Step 15: Deploy Ingress
```bash
# Apply ingress configuration
kubectl apply -f gcp-retail-ingress.yaml

# Verify ingress is created
kubectl get ingress -n retail

# Get ingress details (wait 2-5 minutes for IP to be assigned)
kubectl describe ingress retail-ingress -n retail
```

### Step 16: Update Secrets with Real Values
```bash
# Update database credentials
kubectl create secret generic db-credentials \
  --from-literal=DB_USER=postgres \
  --from-literal=DB_PASSWORD='your-actual-password' \
  -n retail --dry-run=client -o yaml | kubectl apply -f -

# Update payment gateway keys
kubectl create secret generic payment-secrets \
  --from-literal=STRIPE_API_KEY='sk_live_xxxxx' \
  --from-literal=STRIPE_WEBHOOK_SECRET='whsec_xxxxx' \
  -n retail --dry-run=client -o yaml | kubectl apply -f -
```

---

## PART 5: Verify Deployment

### Step 17: Check Service Status
```bash
# List all services
kubectl get services -n retail

# Check pod logs
kubectl logs -n retail -l app=account-service
kubectl logs -n retail -l app=payment-service

# Verify health checks
kubectl get pods -n retail -o custom-columns=NAME:.metadata.name,READY:.status.ready,STATUS:.status.phase

# Port forward to test locally
kubectl port-forward -n retail svc/account-service 5000:80
# In another terminal: curl localhost:5000/health
```

### Step 18: Test API Endpoints
```bash
# Get the external IP
kubectl get ingress -n retail

# Test account service
curl https://api.retail.example.com/account/users

# Test payment service
curl https://api.retail.example.com/payments

# Test checkout service
curl https://api.retail.example.com/checkout/cart/user123

# Test loyalty service
curl https://api.retail.example.com/loyalty/user123
```

---

## PART 6: Monitoring and Logging

### Step 19: Setup Cloud Monitoring
```bash
# View metrics in Cloud Console
gcloud monitoring dashboards create --config-from-file=- <<EOF
{
  "displayName": "Retail Microservices",
  "mosaicLayout": {
    "columns": 12,
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "CPU Usage",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"k8s_pod\" AND resource.labels.namespace_name=\"retail\""
                }
              }
            }]
          }
        }
      }
    ]
  }
}
EOF
```

### Step 20: View Logs
```bash
# Stream logs from all services
kubectl logs -n retail -l app=account-service --tail=100 -f

# Search logs in Cloud Logging
gcloud logging read "resource.type=k8s_container AND resource.labels.namespace_name=retail" \
  --limit=50 \
  --format=json
```

---

## PART 7: Auto-Scaling Configuration

### Step 21: Verify HPA is Working
```bash
# Check HPA status
kubectl get hpa -n retail

# Detailed HPA info
kubectl describe hpa account-service-hpa -n retail

# Watch HPA metrics
kubectl get hpa -n retail --watch
```

### Step 22: Load Testing (Optional)
```bash
# Create a load generator pod
kubectl run -it load-generator \
  -n retail \
  --image=busybox \
  --restart=Never \
  -- /bin/sh

# Inside the pod, generate load
while sleep 0.01; do wget -q -O- http://account-service/health; done

# In another terminal, watch pods scale up
kubectl get pods -n retail --watch
```

---

## PART 8: Cleanup

### To Delete Everything
```bash
# Delete the application
kubectl delete -f gcp-retail-ingress.yaml
kubectl delete -f gcp-retail-app.yaml

# Delete the namespace (optional)
kubectl delete namespace retail

# Delete Cloud SQL instance
gcloud sql instances delete retail-db

# Delete the GKE cluster
gcloud container clusters delete $CLUSTER_NAME --region $REGION

# Delete static IP
gcloud compute addresses delete retail-ip --global

# Delete service account
gcloud iam service-accounts delete cloudsql-sa@$PROJECT_ID.iam.gserviceaccount.com
```

---

## Useful kubectl Commands

```bash
# View resources
kubectl get pods -n retail
kubectl get services -n retail
kubectl get deployments -n retail
kubectl get ingress -n retail

# Get detailed info
kubectl describe pod <pod-name> -n retail
kubectl describe service <service-name> -n retail
kubectl describe ingress retail-ingress -n retail

# View logs
kubectl logs <pod-name> -n retail
kubectl logs -f <pod-name> -n retail  # Follow logs

# Execute commands
kubectl exec -it <pod-name> -n retail -- /bin/bash
kubectl exec <pod-name> -n retail -- env  # View environment variables

# Scale manually
kubectl scale deployment account-service --replicas=5 -n retail

# Update image
kubectl set image deployment/account-service \
  app=gcr.io/$PROJECT_ID/account-service:v2.0.0 \
  -n retail

# Port forward
kubectl port-forward svc/account-service 5000:80 -n retail

# Watch changes
kubectl get pods -n retail --watch
```

---

## Troubleshooting

### Pods not starting?
```bash
# Check pod events
kubectl describe pod <pod-name> -n retail

# Check logs for errors
kubectl logs <pod-name> -n retail

# Check resource limits
kubectl top pods -n retail
```

### Ingress not working?
```bash
# Verify ingress is created
kubectl get ingress -n retail

# Check ingress events
kubectl describe ingress retail-ingress -n retail

# Verify backend services
kubectl get endpoints -n retail
```

### Can't connect to database?
```bash
# Verify Cloud SQL Proxy is running
kubectl get pods -n default | grep cloud-sql-proxy

# Check Cloud SQL instance status
gcloud sql instances describe retail-db

# Verify connection string
gcloud sql instances describe retail-db --format='value(connectionName)'
```

---

## Security Best Practices Implemented

✅ **Network Policy** - Restricts traffic between pods
✅ **RBAC** - Role-based access control for service accounts
✅ **Secrets** - Database passwords stored as Kubernetes secrets
✅ **PodDisruptionBudget** - Ensures service availability
✅ **Security Context** - Pods run as non-root users
✅ **Resource Limits** - Prevents resource exhaustion
✅ **Health Checks** - Liveness and readiness probes
✅ **Managed TLS** - SSL certificates auto-provisioned
✅ **Session Affinity** - Sticky sessions for stateful operations

---

## Next Steps

1. **Add CI/CD**: Setup Cloud Build for automatic deployments
2. **Add Database**: Initialize CloudSQL with schema
3. **Add API Gateway**: Use Apigee or similar for API management
4. **Add Caching**: Implement Redis for cache layer
5. **Add Message Queue**: Use Pub/Sub for asynchronous operations
6. **Add Monitoring**: Setup alerts for errors and performance
7. **Add Backup Strategy**: Configure database backups
8. **Add Disaster Recovery**: Setup cluster backup and restore

Good luck! 🚀
