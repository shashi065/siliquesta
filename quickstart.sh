#!/bin/bash
# Quick start SILIQUESTA v2

set -e

echo "🚀 SILIQUESTA v2 - Quick Start"
echo "=============================="

# Create .env if doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo "✓ .env created. Edit it with your settings."
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Install from https://docker.com"
    exit 1
fi

# Start services
echo ""
echo "🐳 Starting Docker services..."
cd infra/docker
docker-compose up -d

echo ""
echo "⏳ Waiting for services..."
sleep 5

# Check health
echo ""
echo "🏥 Health check..."
curl -s http://localhost:8000/health | python -m json.tool || echo "⚠️  Backend starting..."

echo ""
echo "✅ SILIQUESTA is starting!"
echo ""
echo "📍 Frontend:  http://localhost:3000"
echo "📍 Backend:   http://localhost:8000"
echo "📍 API Docs:  http://localhost:8000/docs"
echo "📍 Database:  postgres://localhost:5432"
echo ""
echo "🧠 Ollama:     http://localhost:11434"
echo ""
echo "💾 View logs:  docker-compose -f infra/docker/docker-compose.yml logs -f"
echo "🛑 Stop:       docker-compose -f infra/docker/docker-compose.yml down"
echo ""
