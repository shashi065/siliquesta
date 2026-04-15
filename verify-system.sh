#!/bin/bash

# SILIQUESTA - System Verification Script
# Quick health check for integrated system

COLOR_GREEN='\033[0;32m'
COLOR_RED='\033[0;31m'
COLOR_YELLOW='\033[1;33m'
COLOR_BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${COLOR_BLUE}"
echo "╔════════════════════════════════════════╗"
echo "║  SILIQUESTA - System Verification      ║"
echo "║  Complete Integration Health Check     ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}"

# Counters
PASSED=0
FAILED=0

# Helper function
check_service() {
    local name=$1
    local url=$2
    local method=${3:-GET}
    
    echo -n "  Checking $name... "
    
    if [ "$method" = "POST" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$url" \
            -H "Content-Type: application/json" \
            -d '{}' 2>/dev/null)
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    fi
    
    if [ "$response" = "200" ] || [ "$response" = "201" ] || [ "$response" = "400" ]; then
        echo -e "${COLOR_GREEN}✓${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${COLOR_RED}✗ (HTTP $response)${NC}"
        ((FAILED++))
        return 1
    fi
}

# Test 1: Backend Connection
echo -e "\n${COLOR_BLUE}1. Backend Service${NC}"
check_service "Backend Health" "http://localhost:5000/health" "GET"

# Test 2: Database
echo -e "\n${COLOR_BLUE}2. Database${NC}"
echo -n "  Checking PostgreSQL... "
if docker ps | grep -q postgres; then
    echo -e "${COLOR_GREEN}✓${NC}"
    ((PASSED++))
else
    echo -e "${COLOR_RED}✗${NC}"
    ((FAILED++))
fi

# Test 3: AI Service
echo -e "\n${COLOR_BLUE}3. AI Service${NC}"
check_service "AI Health" "http://localhost:8000/health" "GET"

# Test 4: Frontend
echo -e "\n${COLOR_BLUE}4. Frontend${NC}"
echo -n "  Checking Frontend Server... "
response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000/" 2>/dev/null)
if [ "$response" = "200" ]; then
    echo -e "${COLOR_GREEN}✓${NC}"
    ((PASSED++))
else
    echo -e "${COLOR_RED}✗${NC}"
    ((FAILED++))
fi

# Test 5: API Endpoints
echo -e "\n${COLOR_BLUE}5. API Endpoints${NC}"
check_service "Auth Endpoint" "http://localhost:5000/api/v1/auth" "GET"
check_service "Projects Endpoint" "http://localhost:5000/api/v1/projects" "GET"
check_service "Project Sharing" "http://localhost:5000/api/v1/projects/1/shares" "GET"

# Test 6: Docker Compose Services
echo -e "\n${COLOR_BLUE}6. Docker Services${NC}"
echo -n "  Checking Docker Compose... "
if command -v docker-compose &> /dev/null; then
    services=$(docker-compose ps -a 2>/dev/null | grep -c "siliquesta")
    if [ "$services" -gt 0 ]; then
        echo -e "${COLOR_GREEN}✓ ($services running)${NC}"
        ((PASSED++))
    else
        echo -e "${COLOR_RED}✗ (no containers running)${NC}"
        ((FAILED++))
    fi
else
    echo -e "${COLOR_YELLOW}⚠ (Docker Compose not installed)${NC}"
fi

# Test 7: Required Files
echo -e "\n${COLOR_BLUE}7. Required Files${NC}"
files=(
    "services/api/app/main.py"
    "apps/web/package.json"
    "ai-engine/main.py"
    "services/api/app/api/project_sharing.py"
    "apps/web/js/api-client.js"
    "apps/web/js/project-service.js"
)

for file in "${files[@]}"; do
    echo -n "  Checking $file... "
    if [ -f "$file" ]; then
        echo -e "${COLOR_GREEN}✓${NC}"
        ((PASSED++))
    else
        echo -e "${COLOR_RED}✗${NC}"
        ((FAILED++))
    fi
done

# Summary
echo -e "\n${COLOR_BLUE}════════════════════════════════════════${NC}"
echo -e "Results: ${COLOR_GREEN}$PASSED passed${NC}, ${COLOR_RED}$FAILED failed${NC}"
echo -e "${COLOR_BLUE}════════════════════════════════════════${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${COLOR_GREEN}✓ All systems operational!${NC}"
    echo -e "\nYou can now:"
    echo "  1. Open http://localhost:3000 in your browser"
    echo "  2. Run integration tests in browser console"
    echo "  3. Deploy to staging/production"
    exit 0
else
    echo -e "\n${COLOR_RED}✗ Some systems need attention${NC}"
    echo -e "\nTo fix:"
    if ! docker ps | grep -q postgres; then
        echo "  1. Start services: docker-compose up -d"
    fi
    if [ -f "DEVOPS_DEPLOYMENT_GUIDE.md" ]; then
        echo "  2. Check DEVOPS_DEPLOYMENT_GUIDE.md for troubleshooting"
    fi
    exit 1
fi
