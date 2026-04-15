# SILIQUESTA - Production Deployment & DevOps Guide

Complete guide for deploying SILIQUESTA across all environments (development, staging, production).

## Table of Contents

1. [Environment Setup](#environment-setup)
2. [Docker Containerization](#docker-containerization)
3. [Docker Compose Orchestration](#docker-compose-orchestration)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [CI/CD Pipeline](#cicd-pipeline)
6. [Monitoring & Observability](#monitoring--observability)
7. [Backup & Disaster Recovery](#backup--disaster-recovery)
8. [Security Hardening](#security-hardening)
9. [Troubleshooting](#troubleshooting)
10. [Post-Deployment Validation](#post-deployment-validation)

---

## Environment Setup

### Development Environment (.env.development)
```bash
# Application
APP_ENV=development
APP_NAME=SILIQUESTA
APP_VERSION=2.0.0
DEBUG=true

# Backend
BACKEND_HOST=localhost
BACKEND_PORT=5000
NODE_ENV=development

# Database
DATABASE_URL="postgresql://user:password@localhost:5432/siliquesta_dev"
POSTGRES_USER=siliquesta
POSTGRES_PASSWORD=dev_password_123
POSTGRES_DB=siliquesta_dev

# AI Service
AI_SERVICE_URL=http://localhost:8000

# Frontend
FRONTEND_PORT=3000
FRONTEND_URL=http://localhost:3000

# Authentication
JWT_SECRET=dev-jwt-secret-key-change-in-production
JWT_EXPIRY=7d
BCRYPT_ROUNDS=10

# Redis (for caching/jobs)
REDIS_URL=redis://localhost:6379

# Celery (for background jobs)
CELERY_BROKER_URL=redis://localhost:6379
CELERY_RESULT_BACKEND=redis://localhost:6379

# Logging
LOG_LEVEL=DEBUG
METRICS_ENABLED=true

# CORS
CORS_ORIGIN=http://localhost:3000

# Feature flags
FEATURE_COLLABORATION=true
FEATURE_AI_OPTIMIZATION=true
FEATURE_ADVANCED_ANALYTICS=false
```

### Staging Environment (.env.staging)
```bash
# Application
APP_ENV=staging
APP_NAME=SILIQUESTA
APP_VERSION=2.0.0
DEBUG=false

# Backend
BACKEND_HOST=staging-api.siliquesta.com
BACKEND_PORT=5000
NODE_ENV=production

# Database
DATABASE_URL="postgresql://user:${DB_PASSWORD}@postgres.staging.internal:5432/siliquesta"
POSTGRES_DB=siliquesta

# AI Service
AI_SERVICE_URL=http://ai-service.staging.internal:8000

# Frontend
FRONTEND_PORT=3000
FRONTEND_URL=https://staging.siliquesta.com

# Authentication
JWT_SECRET=${STAGING_JWT_SECRET}
JWT_EXPIRY=7d

# Redis
REDIS_URL=redis://redis.staging.internal:6379

# Logging
LOG_LEVEL=INFO
METRICS_ENABLED=true

# CORS
CORS_ORIGIN=https://staging.siliquesta.com

# Feature flags
FEATURE_COLLABORATION=true
FEATURE_AI_OPTIMIZATION=true
FEATURE_ADVANCED_ANALYTICS=true
```

### Production Environment (.env.production)
```bash
# Application
APP_ENV=production
APP_NAME=SILIQUESTA
APP_VERSION=2.0.0
DEBUG=false

# Backend
BACKEND_HOST=api.siliquesta.com
BACKEND_PORT=5000
NODE_ENV=production

# Database
DATABASE_URL="postgresql://user:${DB_PASSWORD}@${DB_HOST}:5432/siliquesta"
POSTGRES_DB=siliquesta

# AI Service
AI_SERVICE_URL=https://ai.siliquesta.com

# Frontend
FRONTEND_PORT=3000
FRONTEND_URL=https://app.siliquesta.com

# Authentication
JWT_SECRET=${PRODUCTION_JWT_SECRET}
JWT_EXPIRY=7d

# Redis
REDIS_URL=${REDIS_ENDPOINT}

# Logging
LOG_LEVEL=WARN
METRICS_ENABLED=true
LOG_AGGREGATION_ENDPOINT=https://logs.siliquesta.com

# CORS
CORS_ORIGIN=https://app.siliquesta.com

# Feature flags
FEATURE_COLLABORATION=true
FEATURE_AI_OPTIMIZATION=true
FEATURE_ADVANCED_ANALYTICS=true

# SSL
SSL_CERT_PATH=/etc/ssl/certs/api.siliquesta.com.crt
SSL_KEY_PATH=/etc/ssl/private/api.siliquesta.com.key
```

---

## Docker Containerization

### Backend Dockerfile (infra/docker/Dockerfile.backend)
```dockerfile
# Build stage
FROM node:18-alpine AS builder

WORKDIR /build

# Copy package files
COPY backend/package.json backend/package-lock.json ./

# Install dependencies
RUN npm ci --only=production

# Production stage
FROM node:18-alpine

LABEL maintainer="SILIQUESTA <info@siliquesta.com>"
LABEL version="2.0.0"

WORKDIR /app

# Install curl for health checks
RUN apk add --no-cache curl tzdata

# Copy from builder
COPY --from=builder /build/node_modules ./node_modules

# Copy application code
COPY backend/app ./app
COPY backend/.env* ./

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

USER nodejs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000

CMD ["node", "-e", "require('./app/main.js')"]
```

### AI Service Dockerfile (infra/docker/Dockerfile.ai)
```dockerfile
FROM python:3.11-slim

LABEL maintainer="SILIQUESTA <info@siliquesta.com>"
LABEL version="2.0.0"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY ai-engine/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ai-engine/ .

# Create non-root user
RUN useradd -m -u 1001 aiservice && chown -R aiservice:aiservice /app
USER aiservice

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile (infra/docker/Dockerfile.frontend)
```dockerfile
FROM node:18-alpine AS builder

WORKDIR /build

COPY frontend/package.json frontend/package-lock.json ./

RUN npm ci

COPY frontend/ .

RUN npm run build

# Production stage
FROM nginx:alpine

LABEL maintainer="SILIQUESTA <info@siliquesta.com>"
LABEL version="2.0.0"

# Copy nginx config
COPY infra/nginx.conf /etc/nginx/nginx.conf

# Copy built app
COPY --from=builder /build/dist /usr/share/nginx/html

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:80/health || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

---

## Docker Compose Orchestration

### docker-compose.yml
```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: siliquesta-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-siliquesta}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-dev_password}
      POSTGRES_DB: ${POSTGRES_DB:-siliquesta_dev}
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./database/schemas/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-siliquesta}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: siliquesta-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Backend API
  backend:
    build:
      context: .
      dockerfile: infra/docker/Dockerfile.backend
    container_name: siliquesta-backend
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER:-siliquesta}:${POSTGRES_PASSWORD:-dev_password}@postgres:5432/${POSTGRES_DB:-siliquesta_dev}
      REDIS_URL: redis://redis:6379
      AI_SERVICE_URL: http://ai-service:8000
      CELERY_BROKER_URL: redis://redis:6379
      CELERY_RESULT_BACKEND: redis://redis:6379
      JWT_SECRET: ${JWT_SECRET:-dev-secret-key}
      APP_ENV: ${APP_ENV:-development}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    ports:
      - "5000:5000"
    volumes:
      - ./backend/app:/app/app
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  # AI Service
  ai-service:
    build:
      context: .
      dockerfile: infra/docker/Dockerfile.ai
    container_name: siliquesta-ai
    restart: unless-stopped
    environment:
      PYTHONUNBUFFERED: 1
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
    ports:
      - "8000:8000"
    volumes:
      - ./ai-engine/models:/app/models
      - ./ai-engine/datasets:/app/datasets
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Frontend
  frontend:
    build:
      context: .
      dockerfile: infra/docker/Dockerfile.frontend
    container_name: siliquesta-frontend
    restart: unless-stopped
    ports:
      - "3000:80"
    environment:
      BACKEND_URL: http://backend:5000/api/v1
      AI_SERVICE_URL: http://ai-service:8000
    depends_on:
      - backend
      - ai-service
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:80/"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres-data:
  redis-data:

networks:
  default:
    name: siliquesta-network
```

### Building and Running

```bash
# Build all images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Remove volumes
docker-compose down -v

# Rebuild specific service
docker-compose build backend

# Restart service
docker-compose restart backend
```

---

## Kubernetes Deployment

### Kubernetes Manifests Structure
```
infra/kubernetes/
├── namespace.yaml
├── postgres/
│   ├── pvc.yaml
│   ├── deployment.yaml
│   └── service.yaml
├── redis/
│   ├── deployment.yaml
│   └── service.yaml
├── backend/
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── hpa.yaml
├── ai-service/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── hpa.yaml
├── frontend/
│   ├── configmap.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
└── monitoring/
    ├── prometheus.yaml
    ├── grafana.yaml
    └── alertmanager.yaml
```

### Frontend Ingress (infra/kubernetes/frontend/ingress.yaml)
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: siliquesta-ingress
  namespace: siliquesta
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - app.siliquesta.com
        - api.siliquesta.com
      secretName: siliquesta-tls
  rules:
    - host: app.siliquesta.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend
                port:
                  number: 80
    - host: api.siliquesta.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: backend
                port:
                  number: 5000
    - host: ai.siliquesta.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: ai-service
                port:
                  number: 8000
```

### Backend Deployment (infra/kubernetes/backend/deployment.yaml)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: siliquesta
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      serviceAccountName: backend-sa
      containers:
        - name: backend
          image: siliquesta/backend:latest
          imagePullPolicy: Always
          ports:
            - containerPort: 5000
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: backend-secret
                  key: database-url
            - name: JWT_SECRET
              valueFrom:
                secretKeyRef:
                  name: backend-secret
                  key: jwt-secret
            - name: REDIS_URL
              value: redis://redis-service:6379
            - name: AI_SERVICE_URL
              value: http://ai-service:8000
            - name: APP_ENV
              value: production
          livenessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 5
            periodSeconds: 5
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
```

### Apply Kubernetes Manifests

```bash
# Create namespace
kubectl create namespace siliquesta

# Create secrets
kubectl create secret generic backend-secret \
  --from-literal=database-url="postgresql://..." \
  --from-literal=jwt-secret="..." \
  -n siliquesta

# Apply manifests
kubectl apply -f infra/kubernetes/

# Check deployment status
kubectl get all -n siliquesta

# View logs
kubectl logs -f deployment/backend -n siliquesta

# Port forward for testing
kubectl port-forward svc/backend 5000:5000 -n siliquesta
```

---

## CI/CD Pipeline

### GitHub Actions Workflow (.github/workflows/deploy.yml)
```yaml
name: Deploy SILIQUESTA

on:
  push:
    branches: [main, staging]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install Node dependencies
        run: npm ci
      
      - name: Install Python dependencies
        run: pip install -r ai-engine/requirements.txt
      
      - name: Run tests
        run: npm test
      
      - name: Run integration tests
        run: bash tests/integration.sh

  build:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/staging'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Log in to registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=sha
      
      - name: Build and push images
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          files: |
            infra/docker/Dockerfile.backend
            infra/docker/Dockerfile.ai
            infra/docker/Dockerfile.frontend

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/backend backend=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} -n siliquesta
          kubectl rollout status deployment/backend -n siliquesta
      
      - name: Run smoke tests
        run: bash tests/smoke.sh
```

---

## Monitoring & Observability

### Prometheus Configuration
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:5000']
    metrics_path: '/metrics'
  
  - job_name: 'ai-service'
    static_configs:
      - targets: ['ai-service:8000']
    metrics_path: '/metrics'
  
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - 'alerts.yml'
```

### Alert Rules (monitoring/alerts.yml)
```yaml
groups:
  - name: siliquesta
    rules:
      - alert: BackendDown
        expr: up{job="backend"} == 0
        for: 5m
        annotations:
          summary: "Backend service is down"
      
      - alert: HighCPU
        expr: process_cpu_seconds_total > 80
        for: 5m
        annotations:
          summary: "High CPU usage detected"
      
      - alert: DatabaseConnectionPoolExhausted
        expr: pg_stat_activity_count > 90
        for: 5m
        annotations:
          summary: "DB connection pool exhausted"
      
      - alert: APILatencyHigh
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 1
        for: 5m
        annotations:
          summary: "API P95 latency above 1s"
```

---

## Backup & Disaster Recovery

### Database Backup Strategy
```bash
#!/bin/bash
# backup-db.sh

BACKUP_DIR="/backups/siliquesta"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="siliquesta"

# Create backup directory
mkdir -p $BACKUP_DIR

# PostgreSQL backup
pg_dump -h $DB_HOST -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/postgres_$TIMESTAMP.sql.gz

# Upload to S3
aws s3 cp $BACKUP_DIR/postgres_$TIMESTAMP.sql.gz s3://siliquesta-backups/postgres/

# Keep only last 30 days
find $BACKUP_DIR -name "postgres_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/postgres_$TIMESTAMP.sql.gz"
```

### Kubernetes Backup (Velero)
```bash
# Install Velero
velero install --provider aws --bucket siliquesta-backups

# Create daily backup schedule
velero schedule create daily --schedule="0 2 * * *"

# Restore from backup
velero restore create --from-backup <backup-name>
```

---

## Security Hardening

### Network Security
```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-network-policy
  namespace: siliquesta
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: frontend
        - podSelector:
            matchLabels:
              app: nginx-ingress
      ports:
        - protocol: TCP
          port: 5000
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: postgres
      ports:
        - protocol: TCP
          port: 5432
```

### TLS/SSL Configuration
```bash
# Generate certificates for production
certbot certonly \
  --standalone \
  -d api.siliquesta.com \
  -d app.siliquesta.com \
  -d ai.siliquesta.com

# Store in Kubernetes secret
kubectl create secret tls siliquesta-tls \
  --cert=/etc/letsencrypt/live/api.siliquesta.com/fullchain.pem \
  --key=/etc/letsencrypt/live/api.siliquesta.com/privkey.pem \
  -n siliquesta
```

---

## Post-Deployment Validation

### Health Check Script
```bash
#!/bin/bash
# verify-deployment.sh

echo "🔍 Verifying SILIQUESTA Deployment..."

# Check backend
echo -n "Backend: "
curl -s http://api.siliquesta.com/health | jq -r '.status'

# Check AI service
echo -n "AI Service: "
curl -s http://ai.siliquesta.com/health | jq -r '.status'

# Check frontend
echo -n "Frontend: "
curl -s http://app.siliquesta.com | head -n 1

# Check database
echo -n "Database: "
kubectl exec -it postgres-0 -n siliquesta -- pg_isready

# Check Redis
echo -n "Redis: "
kubectl exec -it redis-0 -n siliquesta -- redis-cli ping

echo "✅ Deployment verification complete"
```

---

## Troubleshooting

### Common Issues

#### Pod CrashLoopBackOff
```bash
# Check logs
kubectl logs <pod-name> -n siliquesta

# Check events
kubectl describe pod <pod-name> -n siliquesta
```

#### Database Connection Issues
```bash
# Test connection
kubectl exec -it backend-0 -n siliquesta -- \
  psql -h postgres -U siliquesta -d siliquesta -c "SELECT 1"
```

#### Memory Pressure
```bash
# Check resource usage
kubectl top node
kubectl top pod -n siliquesta

# Increase resource limits
kubectl set resources deployment backend \
  --limits=memory=1Gi \
  --requests=memory=512Mi \
  -n siliquesta
```

---

This guide provides a complete, production-ready deployment strategy for SILIQUESTA across all environments using Docker, Kubernetes, and CI/CD automation.
