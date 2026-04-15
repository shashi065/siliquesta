#!/bin/bash

# SILIQUESTA Kubernetes Deployment Script
# Automatically deploys to EKS, GKE, or AKS

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== SILIQUESTA Kubernetes Deployment ===${NC}"

# Step 1: Check prerequisites
echo -e "\n${YELLOW}Step 1: Checking prerequisites...${NC}"

if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}kubectl not found. Install using: https://kubernetes.io/docs/tasks/tools/${NC}"
    exit 1
fi

if ! command -v helm &> /dev/null; then
    echo -e "${YELLOW}Helm not found. Installing Helm...${NC}"
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

echo -e "${GREEN}✓ kubectl and helm found${NC}"

# Step 2: Create namespace
echo -e "\n${YELLOW}Step 2: Creating namespace...${NC}"
kubectl create namespace siliquesta --dry-run=client -o yaml | kubectl apply -f -
echo -e "${GREEN}✓ Namespace created${NC}"

# Step 3: Create secrets
echo -e "\n${YELLOW}Step 3: Setting up secrets...${NC}"

# Generate database password if not exists
DB_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -base64 32)

kubectl create secret generic siliquesta-secrets \
  --from-literal=DATABASE_URL="postgresql://postgres:${DB_PASSWORD}@postgres.siliquesta.svc.cluster.local:5432/siliquesta" \
  --from-literal=POSTGRES_PASSWORD="${DB_PASSWORD}" \
  --from-literal=JWT_SECRET="${JWT_SECRET}" \
  --from-literal=REDIS_URL="redis://redis.siliquesta.svc.cluster.local:6379" \
  --from-literal=OLLAMA_URL="http://ollama.siliquesta.svc.cluster.local:11434" \
  -n siliquesta --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✓ Secrets configured${NC}"

# Step 4: Create storage classes (if using persistence)
echo -e "\n${YELLOW}Step 4: Creating storage classes...${NC}"

cat <<EOF | kubectl apply -f -
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: siliquesta-storage
  namespace: siliquesta
provisioner: kubernetes.io/host-path
allowVolumeExpansion: true
reclaimPolicy: Retain
parameters:
  type: pd-standard
EOF

echo -e "${GREEN}✓ Storage classes created${NC}"

# Step 5: Deploy PostgreSQL
echo -e "\n${YELLOW}Step 5: Deploying PostgreSQL...${NC}"

cat <<EOF | kubectl apply -f -
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: siliquesta
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: siliquesta-storage
  resources:
    requests:
      storage: 20Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: siliquesta
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:16
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: siliquesta
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: siliquesta-secrets
              key: POSTGRES_PASSWORD
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        livenessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U postgres
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U postgres
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: siliquesta
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
EOF

echo -e "${GREEN}✓ PostgreSQL deployed${NC}"

# Step 6: Deploy Redis
echo -e "\n${YELLOW}Step 6: Deploying Redis...${NC}"

cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: siliquesta
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        livenessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: siliquesta
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
  type: ClusterIP
EOF

echo -e "${GREEN}✓ Redis deployed${NC}"

# Step 7: Deploy Ollama
echo -e "\n${YELLOW}Step 7: Deploying Ollama...${NC}"

cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama
  namespace: siliquesta
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ollama
  template:
    metadata:
      labels:
        app: ollama
    spec:
      containers:
      - name: ollama
        image: ollama/ollama:latest
        ports:
        - containerPort: 11434
        env:
        - name: OLLAMA_HOST
          value: "0.0.0.0:11434"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /api/tags
            port: 11434
          initialDelaySeconds: 60
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/tags
            port: 11434
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: ollama
  namespace: siliquesta
spec:
  selector:
    app: ollama
  ports:
  - port: 11434
    targetPort: 11434
  type: ClusterIP
EOF

echo -e "${GREEN}✓ Ollama deployed${NC}"

# Step 8: Deploy Backend
echo -e "\n${YELLOW}Step 8: Deploying FastAPI Backend...${NC}"

kubectl apply -f infra/kubernetes/backend.yaml -n siliquesta

echo -e "${GREEN}✓ Backend deployed${NC}"

# Step 9: Deploy Frontend
echo -e "\n${YELLOW}Step 9: Deploying Next.js Frontend...${NC}"

kubectl apply -f infra/kubernetes/frontend.yaml -n siliquesta

echo -e "${GREEN}✓ Frontend deployed${NC}"

# Step 10: Wait for deployments
echo -e "\n${YELLOW}Step 10: Waiting for deployments to be ready...${NC}"

kubectl wait --for=condition=available --timeout=300s \
  deployment/postgres deployment/redis deployment/ollama \
  deployment/backend deployment/frontend \
  -n siliquesta

echo -e "${GREEN}✓ All deployments ready${NC}"

# Step 11: Get access information
echo -e "\n${YELLOW}Step 11: Cluster Information${NC}"

FRONTEND_IP=$(kubectl get service frontend -n siliquesta -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
BACKEND_IP=$(kubectl get service backend -n siliquesta -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "internal")

echo -e "${GREEN}✓ Deployment complete!${NC}"
echo -e "\n${YELLOW}Access URLs:${NC}"
echo -e "Frontend:  http://${FRONTEND_IP}:3000"
echo -e "Backend:   http://${BACKEND_IP}:8000"
echo -e "API Docs:  http://${BACKEND_IP}:8000/docs"

echo -e "\n${YELLOW}Useful Commands:${NC}"
echo -e "kubectl get all -n siliquesta"
echo -e "kubectl logs -f deployment/backend -n siliquesta"
echo -e "kubectl exec -it deployment/backend -n siliquesta -- /bin/bash"

echo -e "\n${GREEN}SILIQUESTA is now running in your Kubernetes cluster!${NC}"
