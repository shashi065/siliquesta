# SILIQUESTA - Production Integration & Deployment Guide

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (Web/Mobile/Desktop)                         │
│  ├─ landing.html          (Public landing page)        │
│  ├─ login.html            (Authentication)             │
│  ├─ app.html              (Main application)           │
│  └─ js/ (Service Layer)                                │
│     ├─ api-client.js      (HTTP + JWT)                │
│     ├─ auth-service.js    (Login/Signup/Logout)       │
│     ├─ project-service.js (Project CRUD)              │
│     ├─ simulation-service.js (Simulations)            │
│     └─ ai-service.js      (AI Optimization)           │
└─────────────────────────────────────────────────────────┘
                           ↓↑
                    (JWT Authentication)
┌─────────────────────────────────────────────────────────┐
│  Backend API (Node.js Express)                        │
│  Port: 5000                                            │
│  Database: PostgreSQL (5432)                           │
│  ├─ /api/auth              (Login/Signup)              │
│  ├─ /api/projects          (Project CRUD)              │
│  ├─ /api/projects/:id/shares (Collaboration)          │
│  ├─ /api/simulations       (Simulation jobs)           │
│  └─ /api/health            (Health checks)            │
└─────────────────────────────────────────────────────────┘
                           ↓↑
                  (HTTP requests to optimize)
┌─────────────────────────────────────────────────────────┐
│  AI Service (Python FastAPI)                          │
│  Port: 8000                                            │
│  ├─ /optimize              (Circuit optimization)      │
│  ├─ /predict               (ML predictions)            │
│  ├─ /health                (Health status)             │
│  └─ /docs                  (Swagger documentation)     │
└─────────────────────────────────────────────────────────┘
                           ↓↑
                  (Binary computations)
┌─────────────────────────────────────────────────────────┐
│  Database & Storage                                   │
│  ├─ PostgreSQL              (Schemas, Users, Projects) │
│  ├─ Redis                   (Caching, Sessions)         │
│  └─ Local Storage            (Frontend cache)           │
└─────────────────────────────────────────────────────────┘
```

## Quick Start (Development)

### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with local settings

# Initialize database
python -m app.database

# Run backend
python -m uvicorn app.main:app --reload --port 5000
```

### AI Service Setup
```bash
cd ai-engine

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run service
python -m app.main --port 8000
```

### Frontend Setup
```bash
cd frontend

# Update API configuration in js/api-client.js
# Test locally via http://localhost:3000
```

## API Integration Points

### 1. Authentication Flow
```javascript
// Login
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "password123"
}
→ { "accessToken": "...", "user": {...} }

// Signup
POST /api/auth/signup
{
  "email": "user@example.com",
  "name": "User Name", 
  "password": "password123"
}
→ { "accessToken": "...", "user": {...} }

// Verify token (auto-called on page load)
GET /api/auth/me
Header: Authorization: Bearer <token>
→ { "id": 1, "email": "...", "name": "..." }
```

### 2. Project Management
```javascript
// List projects (owned + shared)
GET /api/projects
Header: Authorization: Bearer <token>
→ [{ "id": 1, "name": "Project 1", "owner": {...}, ... }]

// Create project
POST /api/projects
{
  "name": "New Project",
  "description": "Project description"
}
→ { "id": 1, "name": "New Project", ... }

// Share project
POST /api/projects/{id}/share
{
  "collaborator_email": "colleague@example.com",
  "role": "editor"  // "viewer", "editor", "admin"
}
→ { "id": 1, "collaborator": {...}, "role": "editor", ... }

// List collaborators
GET /api/projects/{id}/shares
→ [{ "collaborator": {...}, "role": "editor", ... }]

// Get shared projects
GET /api/projects/shared
→ [{ "id": 2, "name": "Shared Project", "owner": {...}, ... }]
```

### 3. Simulation & Optimization
```javascript
// Run simulation
POST /api/simulations/run
{
  "project_id": 1,
  "parameters": {
    "wn": 0.5,
    "wp": 1.0,
    "vdd": 1.2,
    "temp": 27
  }
}
→ { "job_id": "job_123", "status": "queued" }

// Call AI optimization (via AI Service at port 8000)
POST http://localhost:8000/optimize
{
  "wn": 0.5,
  "wp": 1.0,
  "vdd": 1.2,
  "temp": 27,
  "objective": "power_efficiency"
}
→ {
    "optimized_params": {...},
    "performance": {
      "freq": 2400,
      "power": 35,
      "health": 92
    }
  }

// Get simulation results
GET /api/simulations/{job_id}
→ {
    "id": 1,
    "status": "completed",
    "results": { "freq": 2400, "power": 35, ... },
    "created_at": "2026-04-12T10:30:00Z"
  }
```

## Production Deployment

### Environment Configuration

**Backend (.env)**
```
# Database
DATABASE_URL=postgresql://user:password@db_host:5432/siliquesta

# Redis (optional)
REDIS_URL=redis://redis_host:6379

# API Keys
JWT_SECRET=your-production-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION=604800

# CORS
ALLOWED_ORIGINS=https://app.siliquesta.com,https://www.siliquesta.com

# Logging
LOG_LEVEL=INFO

# AI Service
AI_SERVICE_URL=http://ai_service:8000
```

**Frontend (update js/api-client.js)**
```javascript
const API_CONFIG = {
  BACKEND_URL: "https://api.siliquesta.com/api",
  AI_SERVICE_URL: "https://ai.siliquesta.com",
  TIMEOUT: 30000
};
```

### Docker Deployment

**Backend Container**
```bash
docker build -f infra/docker/Dockerfile.backend -t siliquesta-backend:latest .
docker run -d \
  -p 5000:5000 \
  -e DATABASE_URL=postgresql://... \
  -e JWT_SECRET=... \
  siliquesta-backend:latest
```

**AI Service Container**
```bash
docker build -f infra/docker/Dockerfile.ai -t siliquesta-ai:latest .
docker run -d \
  -p 8000:8000 \
  siliquesta-ai:latest
```

**Frontend Container**
```bash
docker build -f infra/docker/Dockerfile.frontend -t siliquesta-frontend:latest .
docker run -d -p 3000:3000 siliquesta-frontend:latest
```

**Docker Compose**
```bash
docker-compose -f infra/docker/docker-compose.yml up -d
```

### Kubernetes Deployment

```bash
# Apply manifests
kubectl apply -f infra/kubernetes/backend.yaml
kubectl apply -f infra/kubernetes/ai.yaml
kubectl apply -f infra/kubernetes/frontend.yaml
kubectl apply -f infra/kubernetes/monitoring.yaml

# Check status
kubectl get pods
kubectl logs -f deployment/siliquesta-backend

# Port forward for testing
kubectl port-forward svc/siliquesta-backend 5000:5000
```

## Integration Testing

### Test Authentication Flow
```bash
# 1. Signup
curl -X POST http://localhost:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test User","password":"test123"}'

# 2. Login
TOKEN=$(curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' | jq -r '.accessToken')

# 3. Get current user
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/auth/me
```

### Test Project Management
```bash
# Create project
curl -X POST http://localhost:5000/api/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Project","description":"Test"}'

# List projects
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/projects

# Share project
curl -X POST http://localhost:5000/api/projects/1/share \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"collaborator_email":"colleague@example.com","role":"editor"}'
```

### Test AI Optimization
```bash
# Call AI service directly
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "wn": 0.5,
    "wp": 1.0,
    "vdd": 1.2,
    "temp": 27,
    "objective": "power_efficiency"
  }'

# Response should include:
# - optimized_params
# - performance metrics (freq, power, health)
# - recommendations
```

## Health Checks

### Backend Health
```bash
curl http://localhost:5000/health
# Returns: { "status": "ok", "db": "ok", "redis": "ok", ... }
```

### AI Service Health
```bash
curl http://localhost:8000/health
# Returns: { "status": "ok", "version": "1.0", ... }
```

### Frontend Health (built-in)
```javascript
// Checks in app.html on page load:
// 1. Backend API connectivity
// 2. AI service availability
// 3. Database status
```

## Production Checklist

- [ ] Database migrations applied
- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] JWT secrets strong and unique
- [ ] CORS origins whitelist configured
- [ ] Logging configured to files/centralized service
- [ ] Backups scheduled (hourly/daily)
- [ ] Monitoring and alerting set up
- [ ] Rate limiting enabled
- [ ] API keys managed securely
- [ ] Frontend built and optimized
- [ ] CDN configured for static assets
- [ ] Load balancer configured
- [ ] Health checks verified
- [ ] Performance tested under load
- [ ] Security audit completed

## Troubleshooting

### Backend won't start
```bash
# Check database connection
psql postgresql://user:password@localhost:5432/siliquesta

# Check environment variables
env | grep DATABASE_URL

# Check logs
docker logs siliquesta-backend  # if containerized
```

### AI service errors
```bash
# Verify AI service is running
curl http://localhost:8000/health

# Check AI logs
docker logs siliquesta-ai  # if containerized

# Test optimization endpoint
curl -X POST http://localhost:8000/optimize -d '{...}'
```

### Frontend API errors
1. Open browser console (F12)
2. Check Network tab for failed requests
3. Verify backend URL in js/api-client.js
4. Check CORS error messages
5. Verify JWT token is present in localStorage

### Database issues
```bash
# Check connection
psql -U user -h localhost -d siliquesta -c "SELECT version();"

# Run migrations
python -m alembic upgrade head

# Reset database (dev only)
python -m app.database --reset
```

## Performance Optimization

### Frontend Optimization
- Minify JavaScript and CSS
- Enable gzip compression
- Use CDN for static assets
- Implement lazy loading for images
- Cache API responses in localStorage

### Backend Optimization
- Use database connection pooling
- Enable query caching with Redis
- Implement pagination for large result sets
- Use async/await properly
- Monitor slow queries

### AI Service Optimization
- Cache model predictions
- Batch optimization requests
- Use vectorized NumPy operations
- Profile for bottlenecks
- Consider GPU acceleration

## Support & Documentation

- **API Docs**: http://localhost:5000/docs (Swagger UI)
- **AI Docs**: http://localhost:8000/docs (Swagger UI)
- **GitHub Issues**: https://github.com/siliquesta/app/issues
- **Email Support**: support@siliquesta.com

## Version History

- **v1.0 (July 2026)**: Production release with collaboration features
- **v0.9 (April 2026)**: Beta release with core functionality
