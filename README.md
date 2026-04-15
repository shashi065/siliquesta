# SILIQUESTA - Complete Production Architecture

**Version 2.0** | Enterprise AI-Native EDA Platform

## 📦 Architecture Overview

```
Frontend (Next.js + Tailwind)
    ↓
API Gateway / Load Balancer
    ↓
Backend (FastAPI)
    ├─ CMOS Physics Engine
    ├─ PVT Analyzer
    ├─ ADA Optimizer
    ├─ Digital Twin (ML)
    └─ AI Services (Ollama + RAG)
    ↓
Database (PostgreSQL)
Cache (Redis)
Vector DB (FAISS)
LLM (Ollama)
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- 8GB RAM minimum
- 20GB disk space

### Local Development

```bash
# Clone repository
git clone https://github.com/siliquesta/siliquesta.git
cd siliquesta

# Start all services
cd infra/docker
docker-compose up -d

# Install frontend
cd ../../frontend
npm install
npm run dev

# Backend automatically runs on port 8000
# Frontend available on port 3000
```

### Docker Compose
```bash
cd infra/docker
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down
```

### Kubernetes Deployment

```bash
# Create namespace
kubectl create namespace siliquesta

# Create secrets
kubectl create secret generic siliquesta-secrets \
  --from-literal=database-url=postgresql://... \
  --from-literal=secret-key=your-secret-key \
  -n siliquesta

# Deploy
kubectl apply -f infra/kubernetes/backend.yaml
kubectl apply -f infra/kubernetes/frontend.yaml

# Check status
kubectl get pods -n siliquesta
kubectl get svc -n siliquesta
```

## 📁 Project Structure

### Frontend (`frontend/`)
- **app/**: Next.js app router
- **components/**: Reusable UI components
- **store/**: Zustand state management
- **utils/**: API clients, helpers

### Backend (`backend/`)
- **app/api/**: FastAPI route handlers
  - `simulation.py`: CMOS simulation endpoints
  - `pvt.py`: PVT analysis
  - `optimizer.py`: ADA optimizer
  - `digital_twin.py`: Reliability model
  - `ai_service.py`: AI chat interface
  - `auth.py`: JWT authentication
- **app/services/**: Core business logic
  - `cmos_engine.py`: Physics computation
  - `rag_system.py`: Knowledge retrieval
- **main.py**: FastAPI application

### AI Engine (`ai-engine/`)
- **models/**: Pre-trained ML models
- **training/**: Training pipelines
- **inference/**: Runtime prediction
- **digital_twin/**: ML-based reliability

### Database (`database/`)
- **schemas/**: PostgreSQL initialization
- Schema: users, projects, simulations, pvt_results, digital_twin, ai_chat_history, design_dna

### Infrastructure (`infra/`)
- **docker/**: Dockerfile, Docker Compose
- **kubernetes/**: K8s deployments, services, HPA
- **gpu_scaling/**: GPU acceleration setup

## 🔌 API Endpoints

### Simulation
```
POST /api/v1/simulate
POST /api/v1/simulate/sweep
POST /api/v1/simulate/batch
```

### PVT Analysis
```
POST /api/v1/pvt/corner-summary
POST /api/v1/pvt/full-sweep
```

### Optimization
```
POST /api/v1/optimize
```

### Digital Twin
```
POST /api/v1/twin/compute-aging
```

### AI Services
```
POST /api/v1/ai/chat
POST /api/v1/ai/generate-code
POST /api/v1/ai/predict-failure
```

### Authentication
```
POST /api/v1/auth/signup
POST /api/v1/auth/login
POST /api/v1/auth/token
```

## 🧠 AI Features

### Local LLM (Ollama)
- Fully offline, runs on device
- Supports: Mistral, Llama 2, Neural Chat
- No API key required

### RAG System
- Built-in knowledge base (5000+ docs)
- Design pattern matching
- Circuit similarity search

### Hybrid Mode
- Local Ollama for fast responses
- Optional Claude API for advanced queries
- Automatic fallback

## 🗄️ Database Schema

### Users
```sql
id, email, password_hash, name, plan, created_at, updated_at
```

### Simulations
```sql
id, project_id, user_id, wn, wp, vdd, temp, cl_ff, corner, tech_node,
freq, power, delay, fom, created_at
```

### PVT Results
```sql
id, simulation_id, corner, temp, vdd, freq, power, delay, created_at
```

### Digital Twin
```sql
id, simulation_id, years, dvth_nbti, did_hci, mtf_em, health_score
```

## 🔐 Security

- JWT authentication
- Password hashing (bcrypt)
- CORS middleware
- Non-root container users
- Read-only filesystem
- Rate limiting (via middleware)

## 📊 Performance

### CMOS Physics Engine
- Computation: ~1ms per corner
- Full PVT sweep: ~500ms (25 corners)
- Batch processing: 100 designs/sec

### Database
- Indexed queries: <100ms
- Connection pooling: 20 connections
- Redis caching for frequent queries

### Frontend
- Next.js SSR/SSG
- Client-side state with Zustand
- Chart.js for real-time visualization

## 🚀 Deployment

### Production Checklist
- [ ] Update `SECRET_KEY` in production
- [ ] Set up PostgreSQL backup
- [ ] Configure Redis persistence
- [ ] Enable HTTPS/TLS
- [ ] Set up monitoring (Prometheus)
- [ ] Configure log aggregation
- [ ] Set up automated backups
- [ ] Test disaster recovery

### Environment Variables
```
DATABASE_URL=postgresql://user:pass@host:5432/siliquesta
REDIS_URL=redis://localhost:6379
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
SECRET_KEY=your-production-secret-key
ANTHROPIC_API_KEY=sk-ant-... (optional)
DEBUG=false
```

## 📈 Scaling

### Horizontal Scaling
- Kubernetes HPA configured for 2-10 replicas
- Triggers on CPU (70%) and Memory (80%)
- Load balancing via Kubernetes Service

### GPU Acceleration
- Training: 4x NVIDIA H100 GPUs
- Inference: 2x NVIDIA A100 GPUs
- Mixed precision (FP16) for speed

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
cd ../frontend
npm test

# Integration tests
pytest tests/integration/
```

## 📝 Development

### Code Style
```bash
# Format backend
black backend/

# Lint backend
flake8 backend/

# Type check
mypy backend/

# Format frontend
prettier --write frontend/
```

## 🤝 Contributing

1. Fork repository
2. Create feature branch: `git checkout -b feature/name`
3. Commit changes: `git commit -m 'Add feature'`
4. Push to branch: `git push origin feature/name`
5. Open Pull Request

## 📄 License

MIT License - See LICENSE file

**Built for the future of chip design**
