# Kubernetes Operations Guide

## 📋 Prerequisites

### Required Tools
- `kubectl` (v1.24+)
- `helm` (v3.0+)
- Kubernetes cluster (EKS, GKE, AKS, or local minikube)
- `docker` (for building images if needed)

### Cluster Requirements
- **Minimum**: 2 nodes, 4GB RAM each
- **Recommended**: 3+ nodes, 8GB RAM each (production)
- **Storage**: 30GB persistent volume for databases

### Install Tools

```bash
# macOS/Linux
curl -fsSL https://get.helm.sh/helm-v3.12.0-linux-amd64.tar.gz | tar xz
sudo mv linux-amd64/helm /usr/local/bin/

# Windows
choco install kubernetes-cli helm
```

---

## 🚀 Deployment Methods

### Method 1: Automated Script (Recommended)

```bash
# Make script executable
chmod +x k8s-deploy.sh

# Run deployment
./k8s-deploy.sh

# Watch progress
kubectl get pods -n siliquesta -w
```

### Method 2: Manual kubectl

```bash
# Create namespace
kubectl create namespace siliquesta

# Apply all manifests
kubectl apply -f infra/kubernetes/backend.yaml
kubectl apply -f infra/kubernetes/frontend.yaml

# Verify
kubectl get all -n siliquesta
```

### Method 3: Helm Chart

```bash
# Create Helm chart structure (scaffold provided)
helm create siliquesta

# Deploy
helm install siliquesta ./siliquesta -n siliquesta --create-namespace

# Upgrade
helm upgrade siliquesta ./siliquesta -n siliquesta
```

---

## 🔧 Configuration

### Environment Variables

Default values in `infra/kubernetes/backend.yaml`:

```yaml
env:
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: siliquesta-secrets
        key: DATABASE_URL
  - name: OLLAMA_URL
    value: http://ollama.siliquesta.svc.cluster.local:11434
  - name: REDIS_URL
    value: redis://redis.siliquesta.svc.cluster.local:6379
  - name: LOG_LEVEL
    value: INFO
```

### Secrets Management

```bash
# Create secrets from CLI
kubectl create secret generic siliquesta-secrets \
  --from-literal=DATABASE_URL="..." \
  --from-literal=JWT_SECRET="..." \
  -n siliquesta

# Or use sealed-secrets for security
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm install sealed-secrets sealed-secrets/sealed-secrets -n kube-system
```

---

## 📊 Monitoring & Observability

### Deploy Monitoring Stack

```bash
# Make script executable
chmod +x setup-monitoring.sh

# Deploy Prometheus, Grafana, AlertManager
./setup-monitoring.sh

# Access Grafana
kubectl port-forward -n monitoring svc/grafana 3000:3000
# Then open http://localhost:3000 (admin/admin)
```

### View Logs

```bash
# Single pod
kubectl logs -n siliquesta deployment/backend

# Stream logs
kubectl logs -f -n siliquesta deployment/backend

# Previous pod logs
kubectl logs -n siliquesta deployment/backend --previous

# Multiple pods
kubectl logs -n siliquesta -l app=backend --tail=100
```

### Access Metrics

```bash
# Port forward Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# Query examples
# In Prometheus: http://localhost:9090
# - Backend uptime: up{job="siliquesta-backend"}
# - Request rate: rate(http_requests_total[5m])
# - Error rate: rate(http_requests_total{status=~"5.."}[5m])
```

---

## 🔍 Debugging & Troubleshooting

### Check Pod Status

```bash
# Describe pod (shows events, volumes, etc.)
kubectl describe pod <POD_NAME> -n siliquesta

# Get pod YAML
kubectl get pod <POD_NAME> -n siliquesta -o yaml

# Check container logs
kubectl logs <POD_NAME> -n siliquesta -c <CONTAINER_NAME>
```

### Common Issues

#### Pod stuck in `Pending`
```bash
# Check node resources
kubectl top nodes

# Check PVC status
kubectl get pvc -n siliquesta

# ResourceQuota issue?
kubectl describe resourcequota -n siliquesta
```

#### Pod crashes (CrashLoopBackOff)
```bash
# Check log for errors
kubectl logs <POD_NAME> -n siliquesta --tail=50

# Check events
kubectl get events -n siliquesta --sort-by=.metadata.creationTimestamp
```

#### Service not reachable
```bash
# Check service endpoints
kubectl get endpoints <SERVICE_NAME> -n siliquesta

# Try exec into pod and curl
kubectl exec -it <POD_NAME> -n siliquesta -- curl http://backend:8000/health

# Check DNS
kubectl exec -it <POD_NAME> -n siliquesta -- nslookup backend.siliquesta.svc.cluster.local
```

### Interactive Debug

```bash
# Get shell in running pod
kubectl exec -it <POD_NAME> -n siliquesta -- /bin/bash

# Or create debug container
kubectl debug <POD_NAME> -it -n siliquesta --image=busybox

# Port-forward for local access
kubectl port-forward <POD_NAME> 8000:8000 -n siliquesta
```

---

## 📈 Scaling

### Manual Scaling

```bash
# Scale backend to 5 replicas
kubectl scale deployment backend -n siliquesta --replicas=5

# Verify
kubectl get deployment backend -n siliquesta
```

### Auto-Scaling (HPA)

Already configured in `backend.yaml` and `frontend.yaml`:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

Monitor HPA:
```bash
kubectl get hpa -n siliquesta -w
```

---

## 🔄 Updates & Rollouts

### Rolling Update

```bash
# Update image
kubectl set image deployment/backend backend=siliquesta/backend:v2.1.0 -n siliquesta

# Monitor rollout
kubectl rollout status deployment/backend -n siliquesta

# Check history
kubectl rollout history deployment/backend -n siliquesta
```

### Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/backend -n siliquesta

# Rollback to specific revision
kubectl rollout undo deployment/backend --to-revision=2 -n siliquesta
```

---

## 💾 Backup & Recovery

### Backup ETCD (Cluster State)

```bash
# For managed K8s (EKS, GKE, AKS): Use cloud provider snapshots

# For self-managed:
ETCDCTL_API=3 etcdctl --endpoints=<ENDPOINT> \
  --cacert=<CA_CERT> --cert=<CERT> --key=<KEY> \
  snapshot save /tmp/etcd-backup.db
```

### Backup PV Data

```bash
# Use velero for full cluster backup
velero install --provider aws --bucket siliquesta-backups --secret-file ./credentials

# Create backup
velero backup create siliquesta-backup

# List backups
velero backup get
```

### Database Backup

```bash
# Exec into postgres pod
kubectl exec -it postgres-xxx -n siliquesta -- /bin/bash

# Create dump
pg_dump -U postgres siliquesta > /tmp/backup.sql

# Copy to local
kubectl cp siliquesta/postgres-xxx:/tmp/backup.sql ./backup.sql -c postgres
```

---

## 🔐 Security

### RBAC Configuration

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: siliquesta-user
  namespace: siliquesta
rules:
- apiGroups: [""]
  resources: ["pods", "pods/logs"]
  verbs: ["get", "list"]
- apiGroups: [""]
  resources: ["services"]
  verbs: ["get", "list"]
```

### Network Policies

```yaml
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
    - namespaceSelector:
        matchLabels:
          name: siliquesta
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: siliquesta
```

### TLS/SSL Configuration

```bash
# Using cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create certificate
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: siliquesta-tls
  namespace: siliquesta
spec:
  secretName: siliquesta-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - siliquesta.example.com
EOF
```

---

## 🚫 Drain & Maintenance

### Drain Node (for maintenance)

```bash
# Cordon node (prevent new pods)
kubectl cordon <NODE_NAME>

# Drain existing pods
kubectl drain <NODE_NAME> --ignore-daemonsets --delete-emptydir-data

# Do maintenance...

# Uncordon node
kubectl uncordon <NODE_NAME>
```

---

## 📋 Useful Commands Reference

```bash
# Cluster information
kubectl cluster-info
kubectl get nodes
kubectl describe node <NODE_NAME>

# Namespaces
kubectl get namespaces
kubectl get all -n siliquesta

# Deployments
kubectl get deployments -n siliquesta
kubectl describe deployment backend -n siliquesta
kubectl edit deployment backend -n siliquesta

# Pods
kubectl get pods -n siliquesta -o wide
kubectl describe pod <POD_NAME> -n siliquesta
kubectl logs <POD_NAME> -n siliquesta

# Services
kubectl get services -n siliquesta
kubectl port-forward svc/backend 8000:8000 -n siliquesta

# Storage
kubectl get pvc -n siliquesta
kubectl get pv

# Events
kubectl get events -n siliquesta --sort-by='.lastTimestamp'

# Resource usage
kubectl top nodes
kubectl top pods -n siliquesta
```

---

## 🆘 Getting Help

### Check Kubernetes Docs
- https://kubernetes.io/docs/
- https://kubernetes.io/docs/tasks/

### Debug Resources
- `kubectl explain deployment`
- `kubectl api-resources`
- `kubectl api-versions`

### Community
- Kubernetes Slack: https://kubernetes.slack.com
- Stack Overflow: tag `kubernetes`
- CNCF Forums: https://discuss.kubernetes.io

---

**Last Updated**: April 7, 2026
**SILIQUESTA Version**: 2.0.0
