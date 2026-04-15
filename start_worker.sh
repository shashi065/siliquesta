#!/bin/bash
# Start Celery Worker for Background Tasks
# 
# Prerequisites:
# - Redis running: redis-server
# - Python environment: .venv/bin/activate
# - Dependencies: celery, redis
#
# Usage:
#   bash start_worker.sh [options]
#
# Options:
#   --concurrency N    Number of worker processes (default: 4)
#   --queues NAMES     Comma-separated queue names (default: celery)
#   --loglevel LEVEL   Logging level: debug|info|warning (default: info)
#   --monitor          Also start Celery Flower monitoring (optional)

set -e

# Configuration
CONCURRENCY=${CONCURRENCY:-4}
QUEUES=${QUEUES:-celery}
LOGLEVEL=${LOGLEVEL:-info}
START_MONITOR=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --concurrency)
            CONCURRENCY="$2"
            shift 2
            ;;
        --queues)
            QUEUES="$2"
            shift 2
            ;;
        --loglevel)
            LOGLEVEL="$2"
            shift 2
            ;;
        --monitor)
            START_MONITOR=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Color outputs
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Celery Worker Startup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Configuration:"
echo "  Concurrency: ${CONCURRENCY} processes"
echo "  Queues: ${QUEUES}"
echo "  Log Level: ${LOGLEVEL}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check Redis
if ! command -v redis-cli &> /dev/null; then
    echo -e "${RED}✗ redis-cli not found${NC}"
    echo "  Install Redis: https://redis.io/download"
    exit 1
fi

if ! redis-cli ping &> /dev/null; then
    echo -e "${RED}✗ Redis server not running${NC}"
    echo "  Start Redis: redis-server"
    exit 1
fi
echo -e "${GREEN}✓ Redis is running${NC}"

# Check Python environment
if [ ! -f ".venv/bin/activate" ] && [ ! -f "venv/bin/activate" ]; then
    echo -e "${RED}✗ Virtual environment not found${NC}"
    echo "  Create environment: python -m venv .venv"
    exit 1
fi

# Activate venv
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Check Celery
if ! python -c "import celery" 2>/dev/null; then
    echo -e "${RED}✗ Celery not installed${NC}"
    echo "  Install: pip install celery[redis]"
    exit 1
fi
echo -e "${GREEN}✓ Celery is installed${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Starting Celery Worker${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Export environment variables
export CELERY_BROKER_URL=${CELERY_BROKER_URL:-redis://localhost:6379/0}
export CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND:-redis://localhost:6379/0}

# Start Celery worker
cd services/api
celery -A app.celery_app worker \
    --concurrency=${CONCURRENCY} \
    --queues=${QUEUES} \
    --loglevel=${LOGLEVEL} \
    --time-limit=300 \
    --soft-time-limit=240 \
    --prefetch-multiplier=1 \
    --task-events \
    --without-gossip \
    --without-mingle \
    --without-heartbeat

# Optional: Start Flower monitoring
if [ "$START_MONITOR" = true ]; then
    echo ""
    echo -e "${YELLOW}Starting Flower monitoring at http://localhost:5555${NC}"
    celery -A app.celery_app flower --port=5555
fi
