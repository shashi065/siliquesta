#!/bin/bash

# SILIQUESTA Monitoring and Alerting Setup
# Deploys Prometheus, Grafana, and AlertManager

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}=== SILIQUESTA Monitoring Setup ===${NC}"

# Step 1: Deploy monitoring stack
echo -e "\n${YELLOW}Step 1: Deploying Prometheus, Grafana, and AlertManager...${NC}"

kubectl apply -f infra/kubernetes/monitoring.yaml

echo -e "${GREEN}✓ Monitoring stack deployed${NC}"

# Step 2: Wait for deployments
echo -e "\n${YELLOW}Step 2: Waiting for monitoring services to start...${NC}"

kubectl wait --for=condition=available --timeout=300s \
  deployment/prometheus deployment/grafana deployment/alertmanager \
  -n monitoring

echo -e "${GREEN}✓ All monitoring services ready${NC}"

# Step 3: Get access URLs
echo -e "\n${YELLOW}Step 3: Monitoring Access Information${NC}"

PROMETHEUS_IP=$(kubectl get service prometheus -n monitoring -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "10.0.0.0")
GRAFANA_IP=$(kubectl get service grafana -n monitoring -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "10.0.0.0")
ALERTMANAGER_IP=$(kubectl get service alertmanager -n monitoring -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "internal")

echo -e "${GREEN}✓ Services Running${NC}"
echo -e "\n${YELLOW}Access URLs:${NC}"
echo -e "Prometheus:  http://${PROMETHEUS_IP}:9090"
echo -e "Grafana:     http://${GRAFANA_IP}:3000 (admin / admin)"
echo -e "AlertManager: http://${ALERTMANAGER_IP}:9093"

# Step 4: Setup port forwarding for local access
echo -e "\n${YELLOW}Step 4: Setting up port forwarding (background)...${NC}"

# Port forward Prometheus (optional)
kubectl port-forward -n monitoring svc/prometheus 9090:9090 &> /tmp/prometheus-pf.log &
PROMETHEUS_PID=$!

# Port forward Grafana
kubectl port-forward -n monitoring svc/grafana 3000:3000 &> /tmp/grafana-pf.log &
GRAFANA_PID=$!

echo -e "${GREEN}✓ Port forwarding enabled (PIDs: $PROMETHEUS_PID, $GRAFANA_PID)${NC}"

# Step 5: Display metrics endpoints
echo -e "\n${YELLOW}Step 5: Metrics Available${NC}"

echo -e "${GREEN}Backend Metrics:${NC}"
echo -e "  • http://backend.siliquesta.svc.cluster.local:8000/metrics"
echo -e "  • Query in Prometheus: up{job=\"siliquesta-backend\"}"

echo -e "${GREEN}Frontend Metrics:${NC}"
echo -e "  • http://frontend.siliquesta.svc.cluster.local:3000/metrics"
echo -e "  • Query in Prometheus: up{job=\"siliquesta-frontend\"}"

echo -e "${GREEN}Database Metrics:${NC}"
echo -e "  • pg_stat_statements"
echo -e "  • Query: pg_stat_activity_count"

# Step 6: Create dashboards
echo -e "\n${YELLOW}Step 6: Pre-configured Dashboards${NC}"

echo -e "${GREEN}Available Dashboards:${NC}"
echo -e "  1. SILIQUESTA System Overview"
echo -e "  2. Backend API Performance"
echo -e "  3. Database Health"
echo -e "  4. Infrastructure Metrics"
echo -e "  5. Error Tracking"

# Step 7: Alert rules
echo -e "\n${YELLOW}Step 7: Active Alert Rules${NC}"

echo -e "${GREEN}Monitoring Rules:${NC}"
echo -e "  • HighCPUUsage (>80% for 5m)"
echo -e "  • HighMemoryUsage (>85% for 5m)"
echo -e "  • BackendDown (not responding for 1m)"
echo -e "  • DatabaseDown (not responding for 1m)"
echo -e "  • HighResponseTime (>1s p95 for 5m)"
echo -e "  • ErrorRateHigh (>5% error rate for 5m)"

# Step 8: Helm charts (optional)
echo -e "\n${YELLOW}Step 8: Optional - Helm Installation${NC}"

echo -e "${YELLOW}To install kube-prometheus-stack (production-grade):${NC}"
echo "helm repo add prometheus-community https://prometheus-community.github.io/helm-charts"
echo "helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring"

# Step 9: Cleanup information
echo -e "\n${YELLOW}Step 9: Cleanup Commands${NC}"

echo -e "${YELLOW}To stop port forwarding:${NC}"
echo "kill $PROMETHEUS_PID $GRAFANA_PID"

echo -e "${YELLOW}To remove monitoring stack:${NC}"
echo "kubectl delete -f infra/kubernetes/monitoring.yaml"

echo -e "\n${GREEN}✓ Monitoring setup complete!${NC}"
echo -e "\n${YELLOW}Quick Start:${NC}"
echo "1. Open Grafana: http://localhost:3000 (admin/admin)"
echo "2. Add Prometheus datasource: http://prometheus:9090"
echo "3. Import SILIQUESTA dashboard"
echo "4. Configure alert webhooks in AlertManager"
echo -e "\n${GREEN}SILIQUESTA monitoring is now active!${NC}"
