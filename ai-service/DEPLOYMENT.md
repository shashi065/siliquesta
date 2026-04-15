# Deployment Guide - Full Stack Setup

Complete guide to deploy and run the entire SILIQUESTA stack locally.

## 🏗️ Full Architecture

```
Your Machine
├── Port 3000  ← Frontend (React/Next)
├── Port 5000  ← Backend API (Node.js)
├── Port 5432  ← PostgreSQL Database
└── Port 8000  ← AI Service (Python FastAPI)
```

---

## 📋 Prerequisites

### System Requirements
- Windows 10/11, macOS, or Linux
- 4GB RAM minimum (8GB recommended)
- 5GB free disk space

### Software to Install

1. **Node.js 18+**
   - Download: https://nodejs.org
   - Verify: `node --version` && `npm --version`

2. **Python 3.9+**
   - Download: https://python.org
   - Verify: `python --version`

3. **PostgreSQL 12+**
   - Download: https://postgresql.org
   - Verify: `psql --version`

4. **Git** (optional)
   - Download: https://git-scm.com

---

## 🚀 Quick Start (All Services)

### Option A: Terminal Tabs (Recommended for Development)

Open 4 terminals in the root directory:

**Terminal 1 - PostgreSQL** (Windows):
```bash
psql -U postgres
```

Or if installed as service, ensure it's running. Check services or:
```bash
# Windows (if using PostgreSQL service)
# It usually auto-starts

# macOS (if using Homebrew)
brew services start postgresql

# Linux
sudo systemctl start postgresql
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm install  # First time only
npm run dev
# Runs on http://localhost:3000
```

**Terminal 3 - Backend**:
```bash
cd backend
npm install  # First time only
cp .env.example .env
# Edit .env and set DATABASE_URL
npm run db:push  # First time only
npm run dev
# Runs on http://localhost:5000
```

**Terminal 4 - AI Service**:
```bash
cd ai-service
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
python -m uvicorn main:app --reload
# Runs on http://localhost:8000
```

---

### Option B: Single Command (Advanced)

Create `start-all.sh` (macOS/Linux):
```bash
#!/bin/bash
cd "$(dirname "$0")"

# Kill any existing processes
trap "pkill -f 'npm run dev'; pkill -f 'uvicorn'" EXIT

# Start services in background
echo "Starting Frontend..."
cd frontend && npm run dev &
sleep 2

echo "Starting Backend..."
cd ../backend && npm run dev &
sleep 2

echo "Starting AI Service..."
cd ../ai-service
source venv/bin/activate
python -m uvicorn main:app --reload &

wait
```

Make executable and run:
```bash
chmod +x start-all.sh
./start-all.sh
```

---

## 🛠️ Step-by-Step Setup

### Step 1: Database Setup

**Create PostgreSQL Database:**

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE siliquesta_db;
CREATE USER siliquesta WITH PASSWORD 'siliquesta_dev_pass';
ALTER ROLE siliquesta WITH CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE siliquesta_db TO siliquesta;

# Verify
\dt
\du
```

Or use a GUI tool like pgAdmin:
```bash
# Visit http://localhost:5050
# Email: admin@example.com
# Password: admin
```

### Step 2: Backend Setup

```bash
cd backend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
```

Edit `backend/.env`:
```env
NODE_ENV=development
PORT=5000
DATABASE_URL=postgresql://siliquesta:siliquesta_dev_pass@localhost:5432/siliquesta_db
JWT_SECRET=dev_secret_key_change_in_production
CORS_ORIGIN=http://localhost:3000,http://localhost:8000
AI_SERVICE_URL=http://localhost:8000
```

Initialize database:
```bash
npm run db:push
npm run db:seed  # Optional: seed test data
```

Start development server:
```bash
npm run dev
# http://localhost:5000
```

### Step 3: Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
# http://localhost:3000
```

### Step 4: AI Service Setup

```bash
cd ai-service

# Create virtual environment
python -m venv venv

# Activate
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Start service
python -m uvicorn main:app --reload --port 8000
# http://localhost:8000
```

---

## ✅ Verification

Check all services are running:

**Backend Health:**
```bash
curl http://localhost:5000/health
# Should respond with 200 OK
```

**AI Service Health:**
```bash
curl http://localhost:8000/health
# Should respond with 200 OK
```

**Database Connection:**
```bash
psql -U siliquesta -d siliquesta_db -c "SELECT 1;"
# Should output 1
```

**Frontend:**
- Open browser: http://localhost:3000
- Should see login page

---

## 🧪 End-to-End Test

### 1. Register User
```bash
curl -X POST http://localhost:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "password": "Test123!@#",
    "confirmPassword": "Test123!@#"
  }'
```

Save the `accessToken`.

### 2. Create Project
```bash
curl -X POST http://localhost:5000/api/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "My Project",
    "description": "Testing the stack"
  }'
```

### 3. Test Optimization
```bash
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "W_L_ratio": 10,
      "supply_voltage": 1.8,
      "operating_frequency": 1e9,
      "load_capacitance": 1e-12
    },
    "objectives": {
      "minimize_power": true,
      "maximize_speed": true
    }
  }'
```

---

## 📊 Useful Commands

### Backend
```bash
cd backend

npm run dev              # Development with auto-reload
npm start              # Production
npm test               # Run tests
npm run db:push        # Sync database schema
npm run db:studio      # Open Prisma Studio
npm run db:seed        # Seed test data
npm run lint           # Run ESLint
npm run format         # Format code
```

### AI Service
```bash
cd ai-service

# Development
python -m uvicorn main:app --reload

# Production
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# Testing
pytest
```

### Frontend
```bash
cd frontend

npm run dev            # Development
npm run build          # Production build
npm test              # Run tests
npm run lint          # Run ESLint
```

### PostgreSQL
```bash
# Connect
psql -U siliquesta -d siliquesta_db

# Backup
pg_dump -U siliquesta siliquesta_db > backup.sql

# Restore
psql -U siliquesta siliquesta_db < backup.sql

# Reset database
psql -U siliquesta -d postgres -c "DROP DATABASE siliquesta_db;"
psql -U siliquesta -d postgres -c "CREATE DATABASE siliquesta_db;"
```

---

## 🔧 Configuration

### Development .env Files

**backend/.env:**
```env
NODE_ENV=development
PORT=5000
DATABASE_URL=postgresql://siliquesta:siliquesta_dev_pass@localhost:5432/siliquesta_db
JWT_SECRET=dev_secret_please_change_in_production
JWT_EXPIRES_IN=7d
CORS_ORIGIN=http://localhost:3000,http://localhost:8000
RATE_LIMIT_MAX_REQUESTS=1000
AI_SERVICE_URL=http://localhost:8000
```

**ai-service/.env:**
```env
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=info
PORT=8000
CORS_ORIGINS=http://localhost:5000,http://localhost:3000
OPTIMIZATION_MAX_ITERATIONS=500
OPTIMIZATION_TIMEOUT=30000
```

### Production .env Files

**backend/.env.prod:**
```env
NODE_ENV=production
PORT=5000
DATABASE_URL=postgresql://prod_user:prod_pass@prod_host/siliquesta_prod
JWT_SECRET=<generate_long_random_key>
CORS_ORIGIN=https://yourdomain.com
RATE_LIMIT_MAX_REQUESTS=100
AI_SERVICE_URL=https://ai-service.yourdomain.com:8000
```

**ai-service/.env.prod:**
```env
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=warning
PORT=8000
CORS_ORIGINS=https://api.yourdomain.com
OPTIMIZATION_MAX_ITERATIONS=1000
OPTIMIZATION_TIMEOUT=60000
```

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find process using port
# Windows
netstat -ano | findstr :5000

# macOS/Linux
lsof -i :5000

# Kill process
# Windows
taskkill /PID <PID> /F

# macOS/Linux
kill -9 <PID>
```

### Database Connection Failed
```bash
# Check PostgreSQL is running
# Windows: Check Services panel
# macOS: brew services list
# Linux: sudo systemctl status postgresql

# Test connection
psql -U siliquesta -d siliquesta_db -c "SELECT 1;"

# If connection fails, verify .env DATABASE_URL
```

### Backend won't start
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check for port conflicts
# Check .env file is correct
# Check database connection
npm run db:push
```

### AI Service won't start
```bash
# Verify Python 3.9+
python --version

# Recreate virtual environment
rm -rf venv
python -m venv venv
# Activate venv
pip install -r requirements.txt

# Check port 8000 is free
lsof -i :8000
```

### CORS Errors
```bash
# Make sure CORS_ORIGINS includes all your URLs
# Backend .env:
CORS_ORIGIN=http://localhost:3000,http://localhost:8000

# AI Service .env:
CORS_ORIGINS=http://localhost:5000
```

### Database Locked
```bash
# Reset database
psql -U postgres
DROP DATABASE siliquesta_db;
CREATE DATABASE siliquesta_db;
GRANT ALL PRIVILEGES ON DATABASE siliquesta_db TO siliquesta;

# In backend
npm run db:push
npm run db:seed
```

---

## 📈 Performance Optimization

### Backend
```env
# Connection pooling
DATABASE_URL_MAX_CONNECTIONS=20

# Rate limiting (adjust based on traffic)
RATE_LIMIT_MAX_REQUESTS=1000
RATE_LIMIT_WINDOW_MS=900000

# Caching
CACHE_TTL=3600
```

### AI Service
```env
# Optimization performance
OPTIMIZATION_MAX_ITERATIONS=1000
MAX_WORKERS=4

# Timeout
OPTIMIZATION_TIMEOUT=60000

# For high volume
OPTIMIZATION_METHOD=ml  # Faster ML-based method
```

---

## 🚀 Deployment Options

### Local Production-like Setup

```bash
# Backend
cd backend
NODE_ENV=production npm start

# AI Service
cd ai-service
source venv/bin/activate
gunicorn main:app --workers 4 --bind 0.0.0.0:8000

# Frontend (build first)
cd frontend
npm run build
npm run start
```

### Using PM2 (Process Manager)

```bash
# Install globally
npm install -g pm2

# Start all services
pm2 start backend/src/server.js --name "siliquesta-backend"
pm2 start ai-service/main.py --name "siliquesta-ai" --interpreter python
pm2 start frontend/server.js --name "siliquesta-frontend"

# View processes
pm2 list

# Save configuration
pm2 save
pm2 startup  # Auto-start on reboot
```

### Docker Deployment

See `docker-compose.yml` in each service directory.

### Cloud Deployment

- **Backend**: Deploy to Heroku, Railway, Render, or AWS Lambda
- **AI Service**: Deploy to AWS EC2, DigitalOcean, or Google Cloud
- **Database**: Use AWS RDS, DigitalOcean, or Managed PostgreSQL
- **Frontend**: Deploy to Vercel, Netlify, or AWS S3 + CloudFront

---

## 📚 Monitoring

### Logs

**Backend Logs:**
```bash
cd backend
npm run dev 2>&1 | tee backend.log
```

**AI Service Logs:**
```bash
cd ai-service
python -m uvicorn main:app --reload 2>&1 | tee ai-service.log
```

### Health Monitoring

```bash
# Create health check script
cat > health-check.sh << 'EOF'
#!/bin/bash
echo "Checking services..."
curl -s http://localhost:5000/health && echo "✓ Backend" || echo "✗ Backend"
curl -s http://localhost:8000/health && echo "✓ AI Service" || echo "✗ AI Service"
curl -s http://localhost:3000 && echo "✓ Frontend" || echo "✗ Frontend"
EOF

chmod +x health-check.sh
./health-check.sh
```

---

## 🔐 Security Checklist

- [ ] Change JWT_SECRET for production
- [ ] Use HTTPS/SSL in production
- [ ] Set up CORS correctly
- [ ] Use strong database password
- [ ] Enable rate limiting
- [ ] Set up firewall rules
- [ ] Use environment-specific configs
- [ ] Enable HTTPS redirect
- [ ] Set secure headers
- [ ] Rotate secrets regularly

---

## 📞 Getting Help

1. Check logs for errors
2. Verify all services are running
3. Check port conflicts
4. Verify .env configurations
5. Test individual services separately
6. Check documentation files:
   - Backend: `backend/README.md`
   - AI Service: `ai-service/README.md`
   - Integration: `ai-service/INTEGRATION.md`

---

## 🎉 You're Ready!

All services operational:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **Backend Docs**: http://localhost:5000/api
- **AI Service**: http://localhost:8000
- **AI Docs**: http://localhost:8000/docs

Happy building! 🚀
