# SILIQUESTA 2.0 - Production Features Quick Reference

## ⚡ 30-Second Start

```powershell
# Windows
.\launcher.ps1

# Linux/Mac
python3 launcher.py
```

Then: **http://localhost:8000/docs**

---

## 🎯 System Overview (v2.0)

SILIQUESTA is now a **production-grade deep-tech SaaS platform**:

```
┌─────────────────────────────────────┐
│      FastAPI Backend (Port 8000)    │
├─────────────────────────────────────┤
│ • Realistic MOSFET simulation       │
│ • 2-stage AI optimization           │
│ • Project versioning & sharing      │
│ • Health checks (Kubernetes-ready)  │
│ • 30+ REST APIs                     │
├─────────────────────────────────────┤
│     Database (PostgreSQL/SQLite)    │
│     Cache (Redis/In-Memory)         │
└─────────────────────────────────────┘

NO DOCKER REQUIRED - Pure Python/FastAPI
```

## 📋 Prerequisites

- Python 3.10+
- PostgreSQL 12+ (optional)
- Redis 6+ (optional)
DATABASE_URL=postgresql://siliquesta_user:siliquesta_password_secure@localhost:5432/siliquesta
JWT_SECRET=your_jwt_secret_key
JWT_EXPIRY=7d
CORS_ORIGIN=http://localhost:3000,http://localhost:8080,file://
AI_SERVICE_URL=http://localhost:8000

# Install dependencies
npm install
```

**3. Configure AI Service (2 min)**
```bash
cd ai-service
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file with:
PYTHON_ENV=development
PORT=8000
HOST=0.0.0.0
```

### Daily Startup (30 seconds)

**Terminal 1 - Backend**
```bash
cd backend
npm run dev
# Expect: 🚀 Server running on http://localhost:5000
```

**Terminal 2 - AI Service**
```bash
cd ai-service
source venv/bin/activate  # Windows: venv\Scripts\activate
python main.py
# Expect: INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Terminal 3 - Frontend**
```bash
cd frontend
python -m http.server 3000
# Expect: Serving HTTP on 0.0.0.0 port 3000
```

**Browser**
```
Open: http://localhost:3000/login.html
Create account or login
Start using SILIQUESTA!
```

## Service Status Checks

### Backend Health
```bash
curl http://localhost:5000/api/health
```
**Success**: 
```json
{"status":"healthy","timestamp":"2024-01-15T10:30:00Z"}
```

### AI Service Health
```bash
curl http://localhost:8000/health
```
**Success**:
```json
{"status":"healthy","service":"SILIQUESTA AI Optimization Engine"}
```

### Database Connection
```bash
psql -U siliquesta_user -d siliquesta -h localhost -c "SELECT 1"
```
**Success**: Output = `1`

## Common User Workflows

### Workflow 1: Create and Test a Project

1. **Login** → Sign up or use existing account
2. **Dashboard** → Click "New Project"
3. **Enter Details** → Title + Description
4. **Save** → Project created and listed
5. **Run Simulation** → Select project → Run
6. **View Results** → Check metrics (power, delay, area)

### Workflow 2: Optimize Circuit Parameters

1. **Dashboard** → Click "AI Optimizer"
2. **Enter Parameters**:
   - Circuit Type: e.g., "Inverter"
   - Width: 100 nm
   - Length: 50 nm
   - Supply Voltage: 3.3 V
   - Frequency: 1 GHz
3. **Click "Run Optimization"**
4. **View Results**:
   - See original vs. optimized parameters
   - View improvement percentages
   - Understand which parameters changed and by how much

### Workflow 3: Compare Multiple Optimizations

1. **Optimizer** → Run optimization with parameters (100, 50)
2. **Note Results** → Save/screenshot improvements
3. **Modify Parameters** → Change to (150, 75)
4. **Run Again** → Get new optimization
5. **Compare** → See which configuration is better

## API Quick Reference

### Authentication
```bash
# Signup
POST http://localhost:5000/api/auth/signup
Content-Type: application/json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "password123"
}
Response: { token, refreshToken, user }

# Login
POST http://localhost:5000/api/auth/login
{ "email": "john@example.com", "password": "password123" }
Response: { token, refreshToken }
```

### Projects
```bash
# Create
POST /api/projects
{ "title": "My Project", "description": "..." }

# List
GET /api/projects?page=1&limit=10

# Get One
GET /api/projects/123

# Update
PATCH /api/projects/123
{ "title": "Updated" }

# Delete
DELETE /api/projects/123
```

### Simulations
```bash
# Run
POST /api/simulations
{ "projectId": 123, "name": "Test Run" }

# List
GET /api/simulations

# Get Results
GET /api/simulations/456/results

# Formats:
{
  "gain": 42.5,
  "power": 1.2e-6,
  "delay": 3.5e-9,
  "area": 2.1e-12,
  "convergence": 0.95
}
```

### AI Optimization
```bash
# Optimize
POST http://localhost:8000/optimize
{
  "circuit_type": "Inverter",
  "width": 100,
  "length": 50,
  "vdd": 3.3,
  "frequency": 1
}

Response:
{
  "original_parameters": { ... },
  "optimized_parameters": { ... },
  "improvements": {
    "width": -5,
    "power": -0.18
  }
}
```

## Frontend Features

### Authentication Page (login.html)
- **Signup Form**: Create new account
- **Login Form**: Access existing account
- Auto-redirect to app if already logged in
- Error messages for invalid credentials

### Main Application (app.html)
- **Dashboard**: Quick overview, recent activity
- **Projects**: Create, view, edit, delete projects
- **Simulations**: Run simulations, view results
- **AI Optimizer**: Optimize circuit parameters
- **User Profile**: View logged-in user info
- **Logout**: Sign out and return to login

### UI Components
- Loading spinners during operations
- Success/error notifications
- Form validation feedback
- Empty states with helpful messages
- Responsive design for all screen sizes

## Database Schema (Simple Reference)

```sql
-- Users
CREATE TABLE "User" (
  id SERIAL PRIMARY KEY,
  email VARCHAR UNIQUE,
  name VARCHAR,
  passwordHash VARCHAR
);

-- Projects
CREATE TABLE "Project" (
  id SERIAL PRIMARY KEY,
  userId INTEGER REFERENCES "User"(id),
  title VARCHAR,
  description TEXT,
  parameters JSON
);

-- Simulations
CREATE TABLE "Simulation" (
  id SERIAL PRIMARY KEY,
  projectId INTEGER REFERENCES "Project"(id),
  name VARCHAR,
  status VARCHAR,
  results JSON
);
```

## Environment Variables Reference

### Backend (.env)
| Variable | Value | Notes |
|----------|-------|-------|
| NODE_ENV | development | Use "production" for deployment |
| PORT | 5000 | Backend server port |
| DATABASE_URL | postgresql://... | PostgreSQL connection string |
| JWT_SECRET | your_secret_key | Used for token signing |
| JWT_EXPIRY | 7d | Token expiration time |
| AI_SERVICE_URL | http://localhost:8000 | AI service address |
| CORS_ORIGIN | http://localhost:3000,... | Allowed frontend origins |

### AI Service (.env)
| Variable | Value | Notes |
|----------|-------|-------|
| PYTHON_ENV | development | Use "production" for deployment |
| PORT | 8000 | AI service port |
| HOST | 0.0.0.0 | Listen on all interfaces |
| OPTIMIZATION_TIMEOUT | 30 | Timeout in seconds |
| OPTIMIZATION_WORKERS | 4 | Parallel workers |

## Frontend Service API

### Available Global Objects

```javascript
// Authentication
window.authService.login(email, password)
window.authService.signup(userData)
window.authService.logout()
window.authService.isAuthenticated()
window.authService.getCurrentUser()

// Projects
window.projectService.createProject(title, desc)
window.projectService.getProjects()
window.projectService.getProject(id)
window.projectService.deleteProject(id)

// Simulations
window.simulationService.runSimulation(projectId, name)
window.simulationService.getSimulations()
window.simulationService.getResults(id)

// AI Optimization
window.aiService.optimize(parameters)
window.aiService.checkHealth()

// UI Helpers
UIHelpers.showLoader(message)
UIHelpers.hideLoader()
UIHelpers.showNotification(message, type)
UIHelpers.formatNumber(num)
UIHelpers.formatScientific(num)
```

## Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| Port already in use | `lsof -i :5000` then `kill -9 <PID>` |
| Can't connect to DB | Check PostgreSQL is running |
| 401 Unauthorized | Token expired, need to login again |
| CORS errors | Check CORS_ORIGIN in backend .env |
| AI service not found | Start AI service in separate terminal |
| Frontend can't load | Check http server is running |
| Network errors | Verify all services are running on correct ports |

## Default Ports

| Service | Port | URL |
|---------|------|-----|
| Frontend | 3000 | http://localhost:3000 |
| Backend | 5000 | http://localhost:5000 |
| AI Service | 8000 | http://localhost:8000 |
| PostgreSQL | 5432 | localhost:5432 |

## File Locations

| Component | Location | Purpose |
|-----------|----------|---------|
| Backend Server | backend/src/server.js | Express app entry point |
| Database Schema | backend/prisma/schema.prisma | Data models |
| AI Optimizer | ai-service/optimizer.py | Optimization algorithm |
| Login Page | frontend/login.html | Authentication UI |
| App Page | frontend/app.html | Main application UI |
| API Client | frontend/js/api-client.js | HTTP communication |
| Auth Service | frontend/js/auth-service.js | Authentication logic |

## Performance Targets

| Metric | Target | Typical |
|--------|--------|---------|
| Login | < 500ms | 200-300ms |
| Create Project | < 1s | 300-500ms |
| Run Simulation | < 5s | 2-3s |
| AI Optimization | < 10s | 5-7s |
| Page Load | < 2s | 500ms-1s |

## Example Session

```
1. Open http://localhost:3000/login.html
   → Login page loads

2. Click "Sign Up"
   → Fill form: name, email, password
   → Submit
   → Account created, redirected to app.html

3. Dashboard loads
   → Welcome message shows
   → Empty state because no projects yet

4. Click "New Project"
   → Modal opens
   → Enter: Title="Inverter", Description="Low power"
   → Click Create
   → Project appears in list

5. Click AI Optimizer
   → Enter parameters (default provided)
   → Click "Run Optimization"
   → Loading spinner appears
   → Results table shows improvements

6. Logout
   → Confirm logout
   → Redirect to login page
```

## Security Notes

1. **Never commit secrets**: .env files contain sensitive data
2. **JWT tokens**: Stored in browser localStorage (vulnerable to XSS)
3. **Password hashing**: Passwords hashed with bcryptjs (10 rounds)
4. **CORS controlled**: Only specified origins can access API
5. **Rate limiting**: Backend has request rate limiting

## Performance Optimization Tips

1. **Backend**: Set NODE_ENV=production for deployment
2. **Database**: Add indexes for frequently searched fields
3. **Frontend**: Enable HTTP caching headers
4. **AI Service**: Increase worker count for parallel optimization
5. **Network**: Use CDN for static assets in production

## Useful Commands

```bash
# View backend logs
tail -f backend/logs/app.log

# View database contents
psql -U siliquesta_user -d siliquesta -c "SELECT * FROM \"Project\";"

# Reset database
npm run db:reset

# Kill process on port
# Windows: netstat -ano | findstr :5000 then taskkill /PID <PID> /F
# Unix: lsof -i :5000 | grep -v PID | awk '{print $2}' | xargs kill -9

# Install new package
npm install package-name
pip install package-name

# Update all packages
npm update
pip install --upgrade -r requirements.txt
```

## Next Steps

1. ✅ Complete 5-minute quick start
2. ✅ Verify all services are healthy
3. ✅ Create a test project
4. ✅ Run a simulation
5. ✅ Try AI optimization
6. ✅ Explore the API using curl
7. 📖 Read full documentation in respective README files
8. 🚀 Deploy to production (see COMPLETE_SYSTEM_SETUP.md)

## Support Resources

- **Backend**: `backend/README.md`
- **AI Service**: `ai-service/README.md` + `INTEGRATION.md`
- **Frontend**: `frontend/FRONTEND_INTEGRATION_GUIDE.md`
- **System**: `COMPLETE_SYSTEM_SETUP.md`
- **Architecture**: `ARCHITECTURE.md`

---

**Last Updated**: January 2024  
**Version**: 1.0  
**Status**: Production Ready
