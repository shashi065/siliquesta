# 🚀 SILIQUESTA Integration - Quick Start Guide

Get the system running and verified in 15 minutes.

---

## Step 1: Verify Integration (2 minutes)

```bash
# Navigate to project root
cd siliquesta

# Run verification script
python verify_integration.py
```

**Expected Output:**
```
✓ PASS - Backend app file (main.py)
✓ PASS - Projects API endpoint (projects.py)
✓ PASS - Projects import in main.py
✓ PASS - Projects router included
... (40+ checks)

Results: 40 passed, 0 failed
✓ All checks passed! System is properly integrated.
```

If any checks fail, review `INTEGRATION_GUIDE.md` section "Troubleshooting".

---

## Step 2: Start Backend (3 minutes)

```bash
# Navigate to backend
cd backend

# Create/activate virtual environment (if not done)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies (if not done)
pip install -r requirements.txt

# Start backend server
python -m uvicorn app.main:app --reload --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete
```

**Verify in browser:** http://localhost:8000/health
Should return: `{"status": "ok"}`

---

## Step 3: Start Frontend (3 minutes)

In a new terminal:

```bash
# Navigate to frontend
cd frontend

# Install dependencies (if not done)
npm install

# Start frontend dev server
npm run dev
```

**Expected Output:**
```
> next dev

  ▲ Next.js 14.0.0
  - Local:        http://localhost:3000
  - Environments: .env.local

✓ Ready in 2s
```

**Verify in browser:** http://localhost:3000

---

## Step 4: Test Core Workflows (7 minutes)

### 4.1 Test Authentication

1. Go to http://localhost:3000/auth/login
2. Click "Sign Up" to create account OR use existing credentials
3. Enter email and password
4. Click "Sign Up" / "Login"
5. Should be redirected to dashboard
6. ✅ **Authentication Working**

### 4.2 Test Project Creation

1. On dashboard, click "New Project"
2. Enter:
   - Name: "Test Circuit"
   - Description: "My first test circuit"
   - Tags: "test, verification"
3. Click "Create"
4. Should show success message
5. ✅ **Project Creation Working**

### 4.3 Test Design Saving

1. In project, design your circuit (drag components, etc.)
2. Click "Save Design"
3. Should show "Design saved successfully"
4. Close project and reopen
5. Design should be restored
6. ✅ **Design Persistence Working**

### 4.4 Test Simulation

1. In project, enter circuit parameters:
   - Width N: 5
   - Width P: 10
   - VDD: 1.2
   - Temperature: 25
2. Click "Run Simulation"
3. Should show "Running simulation..."
4. Wait for results (5-30 seconds)
5. Should display metrics (Frequency, Power, Delay)
6. ✅ **Simulation Working**

### 4.5 Test ML Optimization

1. In project, click "Optimize with AI"
2. Should show optimization parameters
3. Click "Run ML Optimization"
4. Should show "Optimizing with machine learning..."
5. Wait for results (10-60 seconds)
6. Should display:
   - Optimized parameters
   - Confidence score (0-1)
   - Predicted improvement
7. ✅ **ML Optimization Working**

---

## Step 5: Run Integration Tests (Optional but recommended)

In a third terminal:

```bash
# Navigate to backend
cd backend

# Run all integration tests
pytest tests/test_e2e_integration.py -v
```

**Expected Output:**
```
tests/test_e2e_integration.py::TestProjectsAPI::test_create_project PASSED
tests/test_e2e_integration.py::TestProjectsAPI::test_list_projects PASSED
tests/test_e2e_integration.py::TestProjectsAPI::test_get_project PASSED
tests/test_e2e_integration.py::TestProjectsAPI::test_update_project PASSED
tests/test_e2e_integration.py::TestProjectsAPI::test_delete_project PASSED
tests/test_e2e_integration.py::TestSimulationIntegration::test_submit_simulation PASSED
tests/test_e2e_integration.py::TestOptimizationIntegration::test_ml_optimization PASSED
... (9 more tests)

======================== 16 passed in 45.23s ========================
```

**All tests pass?** ✅ **System fully integrated and tested!**

---

## System Status

When all steps are complete:

| Component | Status | Endpoint |
|-----------|--------|----------|
| Backend API | ✅ Running | http://localhost:8000 |
| Frontend UI | ✅ Running | http://localhost:3000 |
| Database | ✅ Connected | SQLite (dev) or PostgreSQL |
| Job Queue | ✅ Ready | Celery + Redis |
| ML Services | ✅ Ready | Models loaded |
| Authentication | ✅ Working | JWT tokens issued |
| Projects | ✅ Working | CRUD operations functional |
| Simulation | ✅ Working | Jobs executing |
| Optimization | ✅ Working | ML predictions running |

---

## Troubleshooting

### Backend won't start
```bash
# Check Python version (need 3.8+)
python --version

# Check all dependencies installed
pip install -r requirements.txt

# Check port 8000 is available
lsof -i :8000  # Or check in Windows Task Manager
```

### Frontend won't start
```bash
# Check Node version (need 16+)
node --version

# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Database connection error
```bash
# If using PostgreSQL, ensure it's running
# On Windows: Check Services → PostgreSQL
# On macOS: brew services list | grep postgres
# On Linux: sudo systemctl status postgresql

# If using SQLite (default), clear old db:
# rm backend/app/database.db
```

### Tests are failing
- Check backend is running: http://localhost:8000/health
- Check database is initialized
- Run `pytest tests/test_e2e_integration.py -v` for details
- Review `INTEGRATION_GUIDE.md` "Troubleshooting" section

### Redis not found
```bash
# Install Redis (development only)
# macOS: brew install redis
# Ubuntu: sudo apt-get install redis-server
# Windows: https://github.com/microsoftarchive/redis/releases

# Start Redis
redis-server
```

---

## Key Files Reference

| File | Purpose | When to Use |
|------|---------|------------|
| `INTEGRATION_GUIDE.md` | Complete technical guide | Deep dive, troubleshooting |
| `INTEGRATION_STATUS.md` | Current system status | Overview, progress |
| `INTEGRATION_SUMMARY.md` | High-level summary | Quick understanding |
| `verify_integration.py` | Automated verification | Check system health |
| `backend/tests/test_e2e_integration.py` | Integration tests | Validate functionality |

---

## What's Next?

### After Verification (Next Steps)
1. ✅ Complete all 5 steps above
2. 📋 Review `INTEGRATION_GUIDE.md` for details
3. 🧪 Run manual tests for your specific use case
4. 🔧 Customize as needed for your requirements
5. 📊 Load test with multiple concurrent users
6. 🚀 Deploy to production

### Common Next Tasks
- **Performance Tuning**: See `INTEGRATION_GUIDE.md` "Performance Considerations"
- **Security Setup**: See `INTEGRATION_STATUS.md` "Security Checklist"
- **Team Collaboration**: See repository for team features roadmap
- **Custom Models**: See `ai-engine/` for ML model training

---

## Quick Commands Reference

```bash
# Backend
cd backend && python -m uvicorn app.main:app --reload  # Start
curl http://localhost:8000/health                     # Health check
pytest tests/test_e2e_integration.py -v               # Run tests

# Frontend
cd frontend && npm run dev                             # Start
npm run build                                          # Production build
npm test                                               # Run tests

# Verification
python verify_integration.py                           # Full system check

# Database
sqlite3 backend/app/database.db ".tables"             # List tables (SQLite)
```

---

## Success Criteria

You'll know everything is working when:

✅ `verify_integration.py` shows all 40+ checks passing  
✅ You can log in and create a project  
✅ You can save and load designs  
✅ Simulations complete and show results  
✅ ML optimization runs and shows predictions  
✅ Integration tests pass (16/16)  
✅ No errors in browser console  
✅ No errors in terminal logs  

---

## Getting Help

1. **First**: Run `verify_integration.py` to check what's failing
2. **Then**: Check `INTEGRATION_GUIDE.md` "Troubleshooting" section
3. **Then**: Review relevant test in `test_e2e_integration.py`
4. **Then**: Check component-specific documentation

---

## Estimated Time Breakdown

| Step | Estimated Time | Actual Time |
|------|----------------|------------|
| Verify Integration | 2 min | ___ |
| Start Backend | 3 min | ___ |
| Start Frontend | 3 min | ___ |
| Test Workflows | 7 min | ___ |
| Run Tests | 1 min | ___ |
| **Total** | **~15 min** | ___ |

---

## One-liner Verification

If everything is set up, run this:

```bash
python verify_integration.py && echo "✅ Integration verified!" || echo "❌ Integration issues found"
```

---

## You're All Set! 🎉

The SILIQUESTA system is now fully integrated and ready. Start with Step 1 above and you'll be up and running in minutes.

Good luck! 🚀
