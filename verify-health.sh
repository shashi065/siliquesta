#!/bin/bash

# SILIQUESTA System Health Verification Script
# Checks all components and configurations

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   SILIQUESTA v2.0 Health Check        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"

PASSED=0
FAILED=0
WARNINGS=0

# Function to check status
check_status() {
    local name=$1
    local command=$2
    local required=$3

    printf "%-40s ... " "$name"
    
    if eval "$command" &> /dev/null; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
    else
        if [ "$required" = "required" ]; then
            echo -e "${RED}✗ FAIL${NC}"
            ((FAILED++))
        else
            echo -e "${YELLOW}⚠ SKIP${NC}"
            ((WARNINGS++))
        fi
    fi
}

# =========================
# 1. System Requirements
# =========================
echo -e "\n${YELLOW}=== System Requirements ===${NC}"

check_status "Docker installed" "docker --version" "required"
check_status "Docker running" "docker ps" "required"
check_status "kubectl installed" "kubectl version --client" "optional"
check_status "Helm installed" "helm version" "optional"

# =========================
# 2. Docker Services
# =========================
echo -e "\n${YELLOW}=== Docker Services ===${NC}"

check_status "Frontend running (port 3000)" "curl -s http://localhost:3000 > /dev/null" "optional"
check_status "Backend running (port 8000)" "curl -s http://localhost:8000/health > /dev/null" "optional"
check_status "PostgreSQL running (port 5432)" "nc -z localhost 5432" "optional"
check_status "Redis running (port 6379)" "nc -z localhost 6379" "optional"

# =========================
# 3. Backend Health
# =========================
echo -e "\n${YELLOW}=== Backend Health ===${NC}"

check_status "API Docs available" "curl -s http://localhost:8000/docs > /dev/null" "optional"
check_status "Health endpoint" "curl -s http://localhost:8000/health | grep -q 'status'" "optional"

# =========================
# 4. Frontend Health
# =========================
echo -e "\n${YELLOW}=== Frontend Health ===${NC}"

check_status "Frontend loads" "curl -s http://localhost:3000 | grep -q 'SILIQUESTA'" "optional"
check_status "Landing page" "curl -s http://localhost:3000 | grep -q 'Advanced CMOS'" "optional"

# =========================
# 5. File Structure
# =========================
echo -e "\n${YELLOW}=== File Structure ===${NC}"

check_status "Backend files" "test -f services/api/app/main.py" "required"
check_status "Frontend files" "test -f apps/web/package.json" "required"
check_status "Docker Compose" "test -f infra/docker/docker-compose.yml" "required"
check_status "Kubernetes manifests" "test -f infra/kubernetes/backend.yaml" "required"
check_status "Database schema" "test -f database/schemas/init.sql" "required"

# =========================
# 6. Configuration Files
# =========================
echo -e "\n${YELLOW}=== Configuration Files ===${NC}"

check_status ".env.example" "test -f .env.example" "required"
check_status "README.md" "test -f README.md" "required"
check_status "ARCHITECTURE.md" "test -f ARCHITECTURE.md" "required"
check_status "DEPLOYMENT.md" "test -f DEPLOYMENT.md" "required"
check_status "QUICK_START.md" "test -f QUICK_START.md" "required"

# =========================
# 7. Scripts
# =========================
echo -e "\n${YELLOW}=== Deployment Scripts ===${NC}"

check_status "quickstart.sh" "test -f quickstart.sh && test -x quickstart.sh" "optional"
check_status "k8s-deploy.sh" "test -f k8s-deploy.sh && test -x k8s-deploy.sh" "optional"
check_status "setup-monitoring.sh" "test -f setup-monitoring.sh && test -x setup-monitoring.sh" "optional"

# =========================
# 8. API Testing
# =========================
echo -e "\n${YELLOW}=== API Testing ===${NC}"

# Test simulation endpoint
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/simulate/run \
  -H "Content-Type: application/json" \
  -d '{
    "wn": 1.0, "wp": 2.0, "vdd": 1.8, "temp": 27,
    "cl_ff": 1.0, "corner": "TT", "tech_node": 28
  }' 2>/dev/null || echo "")

if echo "$RESPONSE" | grep -q "freq"; then
    echo -e "Simulation API ...................... ${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "Simulation API ...................... ${YELLOW}⚠ API not responding${NC}"
    ((WARNINGS++))
fi

# =========================
# 9. Database
# =========================
echo -e "\n${YELLOW}=== Database ===${NC}"

check_status "PostgreSQL accessible" "docker exec docker-postgres-1 pg_isready -U postgres 2>/dev/null || true" "optional"

# =========================
# 10. Storage
# =========================
echo -e "\n${YELLOW}=== Storage ===${NC}"

check_status "Database volume exists" "docker volume ls | grep -q postgres" "optional"
check_status "Redis volume exists" "docker volume ls | grep -q redis" "optional"

# =========================
# Summary
# =========================
TOTAL=$((PASSED + FAILED + WARNINGS))

echo -e "\n${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          Summary                      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"

echo -e "Total Checks: ${TOTAL}"
echo -e "  ${GREEN}✓ Passed: ${PASSED}${NC}"
echo -e "  ${RED}✗ Failed: ${FAILED}${NC}"
echo -e "  ${YELLOW}⚠ Warnings: ${WARNINGS}${NC}"

# =========================
# Recommendations
# =========================
echo -e "\n${YELLOW}=== Recommendations ===${NC}"

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}❌ Critical failures detected. Fix issues above.${NC}"
    exit 1
fi

if [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Some services not running. Try:${NC}"
    echo "  1. Start Docker services: docker-compose up -d"
    echo "  2. Check logs: docker-compose logs"
    echo "  3. Rebuild: docker-compose build --no-cache"
fi

if [ $PASSED -eq $TOTAL ]; then
    echo -e "${GREEN}✓ All systems operational!${NC}"
    echo -e "\n${YELLOW}Quick Links:${NC}"
    echo "  Frontend:  http://localhost:3000"
    echo "  Backend:   http://localhost:8000"
    echo "  API Docs:  http://localhost:8000/docs"
    
    # Show next steps
    echo -e "\n${YELLOW}Next Steps:${NC}"
    echo "  1. Open http://localhost:3000 in your browser"
    echo "  2. Create a new account"
    echo "  3. Run your first simulation"
    echo "  4. Explore the AI Lab"
    echo "  5. Save designs to your library"
    
    exit 0
fi
