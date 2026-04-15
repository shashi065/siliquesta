# ⚡ SILIQUESTA v2 - QUICK START (5 Minutes)

## Step 1: Start Everything (Docker)
```bash
cd infra/docker
docker-compose up -d
```

Wait 30 seconds for services to start...

## Step 2: Open Browser

```
Frontend:    http://localhost:3000
Backend API: http://localhost:8000
API Docs:    http://localhost:8000/docs (Swagger)
Ollama:      http://localhost:11434
PG Admin:    http://localhost:5050 (optional)
```

## Step 3: Test Backend

```bash
# Run a single simulation
curl -X POST http://localhost:8000/api/v1/simulate/run \
  -H "Content-Type: application/json" \
  -d '{
    "wn": 1.0,
    "wp": 2.0,
    "vdd": 1.8,
    "temp": 27,
    "cl_ff": 1.0,
    "corner": "TT",
    "tech_node": 28
  }'

# Expected response: {
#   "freq": 3.456,
#   "power": 2.145,
#   "delay": 58.23,
#   "fom": 1.610,
#   ...
# }
```

## Step 4: Run PVT Analysis

```bash
curl -X POST http://localhost:8000/api/v1/pvt/full-sweep \
  -H "Content-Type: application/json" \
  -d '{
    "wn": 1.0,
    "wp": 2.0,
    "vdd_nominal": 1.8,
    "temp_min": 0,
    "temp_max": 85,
    "step_temp": 21,
    "tech_node": 28
  }'
```

## Step 5: Chat with AI (Ollama)

```bash
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How do I reduce power in a CMOS circuit?"
  }'

# Response from local Ollama LLM (no API key needed!)
```

## Step 6: Run Optimizer

```bash
curl -X POST http://localhost:8000/api/v1/optimizer/run \
  -H "Content-Type: application/json" \
  -d '{
    "wn_min": 0.1,
    "wn_max": 5.0,
    "freq_target": 3.0,
    "power_max": 5.0,
    "tech_node": 28
  }'

# Returns top 8 Pareto-optimal designs
```

## Step 7: Check Logs (Optional)

```bash
# Backend logs
docker logs siliquesta-backend-1

# Frontend logs
docker logs siliquesta-frontend-1

# Database logs
docker logs siliquesta-postgres-1

# Ollama logs
docker logs siliquesta-ollama-1
```

## Step 8: Stop Everything

```bash
docker-compose down

# Or to keep data:
docker-compose stop
```

---

## 🔥 Common Commands

### Restart Backend
```bash
docker-compose restart backend
```

### View Database
```bash
# Using psql (if installed)
psql -h localhost -U postgres -d siliquesta

# Or use PG Admin at http://localhost:5050
```

### Rebuild Containers
```bash
docker-compose build --no-cache
```

### View Container Logs
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Check Health
```bash
curl http://localhost:8000/health
```

---

## 📊 API Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/simulate/run` | POST | Single simulation |
| `/api/v1/pvt/corner-summary` | POST | All 5 corners |
| `/api/v1/pvt/full-sweep` | POST | Complete matrix |
| `/api/v1/optimizer/run` | POST | ADA optimizer |
| `/api/v1/twin/compute-aging` | POST | Reliability |
| `/api/v1/ai/chat` | POST | AI chat |
| `/api/v1/auth/signup` | POST | Register |
| `/api/v1/auth/login` | POST | Login |
| `/docs` | GET | Swagger UI |
| `/health` | GET | Health check |

---

## 🎯 Frontend Features (Ready for UI)

The frontend scaffolding is ready with:
```
store/designStore.ts      → State management
utils/api.ts              → All API calls
tailwind.config.js        → Design system
next.config.js            → Performance
```

Components to create:
- SimulationPanel (controls + results)
- PVTChart (visualization)
- ADAResults (top 8 designs)
- AIChat (message interface)
- DesignDNA (saved designs)

---

## 🚀 Next Steps

1. **Explore API docs**: http://localhost:8000/docs
2. **Build UI components**: Create React components in `frontend/components/`
3. **Connect to backend**: Use `useDesignStore` and `api.ts` functions
4. **Add authentication**: Login UI using JWT endpoints
5. **Deploy to Kubernetes**: Follow `DEPLOYMENT.md`

---

## 💡 Pro Tips

✅ **Use Swagger UI** for interactive API testing
✅ **Check `requirements.txt`** for Python dependencies
✅ **Use `.env.example`** as template for configuration
✅ **Review `ARCHITECTURE.md`** for technical details
✅ **Read `DEPLOYMENT.md`** for production setup

---

## ❌ Troubleshooting

**Containers won't start:**
```bash
docker system prune -a --volumes
docker-compose up -d
```

**Port conflicts:**
```bash
# List processes using ports
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # Database
```

**Database connection error:**
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Restart it
docker-compose restart postgres
```

**Ollama not responding:**
```bash
# Check if model is downloaded
docker exec siliquesta-ollama-1 ollama list

# Pull a model if needed
docker exec siliquesta-ollama-1 ollama pull mistral
```

---

## 📞 Get Help

- **Read**: BUILD_SUMMARY.md, ARCHITECTURE.md, DEPLOYMENT.md
- **Check**: API docs at http://localhost:8000/docs
- **View logs**: `docker-compose logs -f [service]`
- **Test**: Use curl or Postman for manual API testing

---

**Ready? Start with:** `docker-compose up -d` 🚀
