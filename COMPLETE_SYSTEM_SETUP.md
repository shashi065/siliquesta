# SILIQUESTA Complete System Setup

This guide provides complete instructions for running the entire SILIQUESTA platform with backend API, AI optimization service, and frontend application.

## System Architecture

```
SILIQUESTA Platform
├── Frontend (Static HTML/JS)
│   ├── login.html          - Authentication
│   └── app.html            - Main application
│
├── Backend API (Node.js/Express)
│   └── http://localhost:5000
│       ├── POST /api/auth/*          - Authentication endpoints
│       ├── GET|POST|PATCH /api/projects/*  - Project management
│       └── GET|POST|PATCH /api/simulations/* - Simulation execution
│
└── AI Service (Python/FastAPI)
    └── http://localhost:8000
        └── POST /optimize           - Circuit optimization
```

## Prerequisites

### Global Requirements
- **Node.js** 16+ ([download](https://nodejs.org/))
- **Python** 3.9+ ([download](https://www.python.org/))
- **PostgreSQL** 12+ ([download](https://www.postgresql.org/))
- **npm** (comes with Node.js)
- **pip** (comes with Python)
- **git** (optional, for version control)

### Verify Installation

```bash
# Check Node.js
node --version
# Should be v16.0.0 or higher

# Check Python
python --version
# or
python3 --version
# Should be Python 3.9 or higher

# Check PostgreSQL
psql --version
# Should be psql (PostgreSQL) 12 or higher

# Check npm
npm --version
# Should be 7.0.0 or higher
```

## Database Setup

### Step 1: Start PostgreSQL

**On Windows:**
```bash
# PostgreSQL should start automatically
# Verify it's running:
psql -U postgres -h localhost -w

# If it doesn't start, use Services:
# 1. Press Win+R
# 2. Type "services.msc"
# 3. Find "PostgreSQL" service
# 4. Click Start
```

**On macOS:**
```bash
# If installed via Homebrew
brew services start postgresql

# Or manually
pg_ctl -D /usr/local/var/postgres start
```

**On Linux:**
```bash
sudo systemctl start postgresql
# or
sudo service postgresql start
```

### Step 2: Create Database and User

```bash
# Connect to PostgreSQL
psql -U postgres

# In psql shell, run:
CREATE DATABASE siliquesta;
CREATE USER siliquesta_user WITH PASSWORD 'siliquesta_password_secure';
GRANT ALL PRIVILEGES ON DATABASE siliquesta TO siliquesta_user;
\q

# Verify connection
psql -U siliquesta_user -d siliquesta -h localhost
\q
```

### Step 3: Initialize Database Schema

```bash
# Navigate to project root
cd /path/to/siliquesta

# Run migrations (via backend setup, see below)
```

## Backend API Setup

### Step 1: Navigate to Backend Directory

```bash
cd backend
```

### Step 2: Create Environment Configuration

Create a `.env` file in the `backend/` directory:

```bash
# Backend Configuration
NODE_ENV=development
PORT=5000

# Database
DATABASE_URL=postgresql://siliquesta_user:siliquesta_password_secure@localhost:5432/siliquesta

# JWT Configuration
JWT_SECRET=your_jwt_secret_key_change_this_in_production
JWT_EXPIRY=7d
REFRESH_TOKEN_SECRET=your_refresh_token_secret_change_this_in_production

# CORS
CORS_ORIGIN=http://localhost:3000,http://localhost:8080,file://

# AI Service
AI_SERVICE_URL=http://localhost:8000

# Logging
LOG_LEVEL=debug
```

### Step 3: Install Dependencies

```bash
# Install Node packages
npm install
```

**Expected output:**
```
added 45 packages in 8s
```

### Step 4: Initialize Database

```bash
# Run Prisma migrations
npx prisma migrate dev --name init

# Seed database (optional)
npm run seed
```

### Step 5: Start Backend Server

```bash
# Development mode (with auto-reload)
npm run dev

# Or production mode
npm start
```

**Expected output:**
```
🚀 Server running on http://localhost:5000
📦 Database connected: siliquesta
✅ Ready for requests
```

### Step 6: Verify Backend is Running

In a new terminal:
```bash
curl http://localhost:5000/api/health

# Expected response:
# {"status":"healthy","timestamp":"2024-01-15T10:30:00Z"}
```

## AI Service Setup

### Step 1: Navigate to AI Service Directory

```bash
cd ai-service
```

### Step 2: Create Python Virtual Environment

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Expected output:**
```
(venv) PS C:\path\to\ai-service>
# or
(venv) $ 
```

### Step 3: Create Environment Configuration

Create a `.env` file in the `ai-service/` directory:

```bash
# AI Service Configuration
PYTHON_ENV=development
PORT=8000
HOST=0.0.0.0

# Optimization Parameters
OPTIMIZATION_TIMEOUT=30
OPTIMIZATION_WORKERS=4

# Logging
LOG_LEVEL=INFO
```

### Step 4: Install Python Dependencies

```bash
# Install packages
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed numpy-1.24.0 scipy-1.10.0 ... (and more packages)
```

### Step 5: Start AI Service

```bash
# Run FastAPI server
python main.py

# Or using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Step 6: Verify AI Service is Running

In a new terminal:
```bash
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","service":"SILIQUESTA AI Optimization Engine",...}
```

## Frontend Setup

### Option 1: Using Python's Built-in Server

```bash
# Navigate to project root
cd /path/to/siliquesta/frontend

# Start simple HTTP server
python -m http.server 3000

# On Windows, if that doesn't work:
python -m http.server 3000

# Or Python 3.x explicitly:
python3 -m http.server 3000
```

**Expected output:**
```
Serving HTTP on 0.0.0.0 port 3000 (http://0.0.0.0:3000/) ...
```

### Option 2: Using Node's HTTP Server

```bash
# Install globally (if not already installed)
npm install -g http-server

# Navigate to frontend directory
cd frontend

# Start server
http-server -p 3000 -c-1

# Open browser to http://localhost:3000
```

**Expected output:**
```
Starting up http-server, serving ./
http-server version 14.1.1
http-server is running at:
http://localhost:3000
```

### Option 3: Using Live Server VS Code Extension

1. Install "Live Server" extension in VS Code
2. Right-click on `login.html`
3. Select "Open with Live Server"
4. Browser opens at `http://localhost:5500/login.html`

## Complete System Startup Guide

### Quick Start (All Services)

**Terminal 1 - Backend:**
```bash
cd backend
npm install  # First time only
npm run dev
# Expected: 🚀 Server running on http://localhost:5000
```

**Terminal 2 - AI Service:**
```bash
cd ai-service
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt  # First time only
python main.py
# Expected: INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Terminal 3 - Frontend:**
```bash
cd frontend
python -m http.server 3000
# Expected: Serving HTTP on 0.0.0.0 port 3000
```

### Access the Application

1. Open browser to `http://localhost:3000/login.html`
2. Create an account or login
3. Create a project
4. Run simulations
5. Use AI Optimizer to optimize parameters

## Verification Checklist

- [ ] PostgreSQL running and accessible
- [ ] Backend server running on http://localhost:5000
- [ ] AI service running on http://localhost:8000
- [ ] Frontend accessible at http://localhost:3000 or http://localhost:5500
- [ ] Backend health check works: `curl http://localhost:5000/api/health`
- [ ] AI health check works: `curl http://localhost:8000/health`
- [ ] Can access login page
- [ ] Can create account or login
- [ ] Can create project
- [ ] Can run simulation
- [ ] Can run AI optimization

## Testing API Endpoints

### Test Backend API

```bash
# Health check
curl http://localhost:5000/api/health

# Signup
curl -X POST http://localhost:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "password123"
  }'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'

# Save the token from response and use in subsequent requests:
# curl -H "Authorization: Bearer YOUR_TOKEN_HERE" http://localhost:5000/api/projects

# Get projects (with valid token)
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  http://localhost:5000/api/projects
```

### Test AI Service

```bash
# Health check
curl http://localhost:8000/health

# Optimization request
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "circuit_type": "Inverter",
    "width": 100,
    "length": 50,
    "vdd": 3.3,
    "frequency": 1
  }'
```

## Common Issues and Solutions

### Issue: PostgreSQL Connection Failed

```
Error: connect ECONNREFUSED 127.0.0.1:5432
```

**Solution:**
```bash
# Check if PostgreSQL is running
psql -U postgres

# If not, start PostgreSQL
# Windows: Open Services and start PostgreSQL service
# macOS: brew services start postgresql
# Linux: sudo systemctl start postgresql

# Verify connection string in .env
DATABASE_URL=postgresql://siliquesta_user:siliquesta_password_secure@localhost:5432/siliquesta
```

### Issue: Backend Port Already in Use

```
Error: listen EADDRINUSE: address already in use :::5000
```

**Solution:**
```bash
# Find process using port 5000
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -i :5000
kill -9 <PID>

# Or change port in .env
PORT=5001
```

### Issue: Python Virtual Environment Not Activating

**Solution:**
```bash
# Ensure you're using the correct activation command:
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# If shell integration hasn't been set up:
# Install Python again with "Add Python to PATH" option
```

### Issue: AI Service Not Found from Frontend

```
Error: Failed to fetch http://localhost:8000/health
```

**Solution:**
1. Verify AI service is running: `curl http://localhost:8000/health`
2. Check firewall is not blocking port 8000
3. Verify AI_SERVICE_URL in api-config.js is correct
4. Check browser console for actual error message

### Issue: 401 Unauthorized Errors

**Solution:**
```javascript
// Frontend will automatically redirect to login
// Or manually trigger token refresh:
await window.authService.refreshToken();
```

### Issue: CORS Errors

**Solution:**
1. Verify backend has CORS enabled (check package.json has cors installed)
2. Check CORS_ORIGIN in backend .env includes `http://localhost:3000`
3. Ensure correct Content-Type header: `application/json`

```bash
# Test CORS
curl -i -X OPTIONS http://localhost:5000/api/projects \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET"
```

## Environment Recap

| Service | Port | URL | Environment File |
|---------|------|-----|-------------------|
| Frontend | 3000 | http://localhost:3000 | N/A (static) |
| Backend | 5000 | http://localhost:5000/api | backend/.env |
| AI Service | 8000 | http://localhost:8000 | ai-service/.env |
| PostgreSQL | 5432 | localhost:5432 | N/A (system service) |

## File Locations

```
siliquesta/
├── backend/
│   ├── .env              ← Create this
│   └── package.json
│
├── ai-service/
│   ├── .env              ← Create this
│   └── requirements.txt
│
└── frontend/
    ├── login.html
    ├── app.html
    └── js/
        ├── api-client.js
        ├── auth-service.js
        └── ...
```

## Performance Tips

1. **Backend**: Use production build mode for better performance
   ```bash
   NODE_ENV=production npm start
   ```

2. **AI Service**: Increase worker count for parallel optimization
   ```bash
   OPTIMIZATION_WORKERS=8 python main.py
   ```

3. **Frontend**: Enable browser caching headers in HTTP server
   ```bash
   http-server -c-1  # Disable caching
   # or
   http-server       # Enable caching
   ```

4. **Database**: Create indexes for frequently queried fields
   ```bash
   npm run db:index
   ```

## Monitoring and Debugging

### Monitor Backend Logs

```bash
# From backend directory
npm run dev

# Look for:
# - Connection status
# - API request logging
# - Error messages
```

### Monitor AI Service Logs

```bash
# From ai-service directory
python main.py

# Look for:
# - Optimization start/completion
# - Performance metrics
# - Error traces
```

### Monitor Network Traffic

**In Browser DevTools:**
1. Press F12 to open Developer Tools
2. Go to Network tab
3. Perform an action (login, create project, run simulation)
4. See all HTTP requests and responses

### Check Frontend Console

**In Browser DevTools:**
1. Press F12
2. Go to Console tab
3. Look for JavaScript errors
4. Check logged messages

## Next Steps

After successful system startup:

1. **Create test data**: Create projects, run simulations
2. **Monitor performance**: Check response times
3. **Test edge cases**: Try error scenarios
4. **Load testing**: Simulate multiple users
5. **Deploy**: Move to production environment

## Production Deployment

For production deployment:

1. **Backend**:
   ```bash
   NODE_ENV=production npm start
   # Use PM2 or similar for process management
   ```

2. **AI Service**:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 main:app
   # Or use Uvicorn with supervisor
   ```

3. **Frontend**:
   ```bash
   # Use Nginx or Apache to serve static files
   # Set appropriate caching headers
   ```

4. **Database**:
   - Use managed PostgreSQL services (AWS RDS, Azure Database, etc.)
   - Set up automated backups
   - Configure replication for high availability

5. **SSL/TLS**:
   - Use Let's Encrypt certificates
   - Enforce HTTPS
   - Update API URLs to use HTTPS

## Support and Documentation

- **Backend README**: See `backend/README.md`
- **AI Service README**: See `ai-service/README.md`
- **Frontend Guide**: See `frontend/FRONTEND_INTEGRATION_GUIDE.md`
- **Architecture**: See `ARCHITECTURE.md`
- **Database Schema**: See `database/schemas/init.sql`

## Quick Reference Commands

```bash
# Start all services (from project root)
# Terminal 1
cd backend && npm run dev

# Terminal 2
cd ai-service && source venv/bin/activate && python main.py

# Terminal 3
cd frontend && python -m http.server 3000

# Access
# http://localhost:3000/login.html

# Stop services
# Press Ctrl+C in each terminal

# Cleanup
rm backend/.env ai-service/.env  # Remove config files
rm -rf backend/node_modules      # Remove dependencies
rm -rf ai-service/venv           # Remove Python venv
```

## Support

For issues or questions, please refer to:
1. Individual service documentation
2. Check issue tracker on GitHub
3. Review logs in each service terminal
4. Check browser console for frontend errors
