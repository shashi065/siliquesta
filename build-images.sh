VERSION=2.0.0
REGISTRY=siliquesta
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Build backend
docker build \
  --build-arg BUILD_DATE=${BUILD_DATE} \
  --build-arg VCS_REF=${GIT_COMMIT} \
  --build-arg VERSION=${VERSION} \
  -t ${REGISTRY}/backend:${VERSION} \
  -t ${REGISTRY}/backend:latest \
  -f infra/docker/Dockerfile.backend \
  services/api/

# Build frontend
docker build \
  --build-arg BUILD_DATE=${BUILD_DATE} \
  --build-arg VCS_REF=${GIT_COMMIT} \
  --build-arg VERSION=${VERSION} \
  -t ${REGISTRY}/frontend:${VERSION} \
  -t ${REGISTRY}/frontend:latest \
  -f infra/docker/Dockerfile.frontend \
  apps/web/

echo "✅ Docker images built successfully"
docker images | grep siliquesta
