#!/bin/bash
# Deployment script for SILIQUESTA

set -e

echo "🚀 SILIQUESTA Deployment Script"
echo "================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check dependencies
echo -e "${YELLOW}Checking dependencies...${NC}"
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker not found${NC}"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo -e "${RED}Docker Compose not found${NC}"; exit 1; }

# Build images
echo -e "${YELLOW}Building Docker images...${NC}"
cd infra/docker
docker-compose build --no-cache
cd ../..

# Start services
echo -e "${YELLOW}Starting services...${NC}"
cd infra/docker
docker-compose up -d
cd ../..

# Wait for services
echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
sleep 10

# Initialize database
echo -e "${YELLOW}Initializing database...${NC}"
docker-compose -f infra/docker/docker-compose.yml exec -T postgres psql -U siliquesta -d siliquesta -f /docker-entrypoint-initdb.d/init.sql || true

# Pull Ollama model
echo -e "${YELLOW}Pulling Ollama model (mistral)...${NC}"
docker exec siliquesta-ollama ollama pull mistral || true

# Install frontend dependencies
echo -e "${YELLOW}Installing frontend dependencies...${NC}"
cd apps/web
npm install
npm run build
cd ../..

echo -e "${GREEN}✓ SILIQUESTA deployment complete!${NC}"
echo -e "${GREEN}✓ Backend: http://localhost:8000${NC}"
echo -e "${GREEN}✓ Frontend: http://localhost:3000${NC}"
echo -e "${GREEN}✓ API Docs: http://localhost:8000/docs${NC}"
