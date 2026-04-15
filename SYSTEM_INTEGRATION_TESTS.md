# SILIQUESTA - System Integration Tests

Complete test suite to verify all components are working together correctly.

## Prerequisites

- All three services running (Backend, AI Service, Frontend)
- Test user account credentials
- curl or Postman for API testing
- Browser DevTools console for frontend testing

## 1. Service Connectivity Tests

### 1.1 Backend Health Check
```bash
# Verify backend is running
curl http://localhost:5000/health

# Expected: { "status": "ok", "db": "ok", ... }
```

### 1.2 AI Service Health Check
```bash
# Verify AI service is running
curl http://localhost:8000/health

# Expected: { "status": "ok", "version": "..." }
```

### 1.3 Frontend Accessibility
```bash
# Access frontend
curl http://localhost:3000/

# Should return HTML of login page
```

---

## 2. Authentication Flow Tests

### 2.1 User Registration
```bash
# Test signup
curl -X POST http://localhost:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "name": "Test User",
    "password": "TestPassword123!"
  }'

# Expected:
# {
#   "accessToken": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "user": {
#     "id": 1,
#     "email": "testuser@example.com",
#     "name": "Test User"
#   }
# }

# Save TOKEN for next tests
export TOKEN="<your_access_token>"
```

### 2.2 User Login
```bash
# Test login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "TestPassword123!"
  }'

# Expected: { "accessToken": "...", "user": {...} }
```

### 2.3 Get Current User
```bash
# Verify JWT authentication works
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/auth/me

# Expected: { "id": 1, "email": "testuser@example.com", "name": "Test User" }
```

### 2.4 Invalid Token Handling
```bash
# Test invalid token
curl -H "Authorization: Bearer invalid_token_123" \
  http://localhost:5000/api/auth/me

# Expected: 401 Unauthorized error
```

---

## 3. Project Management Tests

### 3.1 Create Project
```bash
# Create a new project
curl -X POST http://localhost:5000/api/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Circuit Design",
    "description": "Testing circuit optimization system"
  }'

# Expected:
# {
#   "id": 1,
#   "name": "Test Circuit Design",
#   "user_id": 1,
#   "created_at": "2026-04-12T10:30:00Z"
# }

# Save PROJECT_ID
export PROJECT_ID=1
```

### 3.2 List Own Projects
```bash
# Get all projects owned by user
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/projects

# Expected: [{ "id": 1, "name": "Test Circuit Design", ... }]
```

### 3.3 Get Single Project
```bash
# Get specific project
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/projects/$PROJECT_ID

# Expected: { "id": 1, "name": "Test Circuit Design", ... }
```

### 3.4 Update Project
```bash
# Update project details
curl -X PATCH http://localhost:5000/api/projects/$PROJECT_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated description for testing"
  }'

# Expected: { "id": 1, "description": "Updated description..." }
```

---

## 4. Project Sharing Tests

### 4.1 Create Second Test User (for sharing)
```bash
# Signup as second user
curl -X POST http://localhost:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "colleague@example.com",
    "name": "Colleague User",
    "password": "TestPassword123!"
  }'

# Save COLLEAGUE_TOKEN
export COLLEAGUE_TOKEN="<colleague_access_token>"
```

### 4.2 Share Project with Colleague
```bash
# Share project with colleague (as owner)
curl -X POST http://localhost:5000/api/projects/$PROJECT_ID/share \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "collaborator_email": "colleague@example.com",
    "role": "editor"
  }'

# Expected:
# {
#   "id": 1,
#   "project_id": 1,
#   "collaborator": { "id": 2, "email": "colleague@example.com", ... },
#   "role": "editor",
#   "permissions": { "can_edit": true, "can_run_simulations": true }
# }
```

### 4.3 List Project Collaborators
```bash
# See all users with access to project
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/projects/$PROJECT_ID/shares

# Expected: [{ "collaborator": {...}, "role": "editor", ... }]
```

### 4.4 Colleague Views Shared Project
```bash
# Colleague lists projects shared with them
curl -H "Authorization: Bearer $COLLEAGUE_TOKEN" \
  http://localhost:5000/api/projects/shared

# Expected: [{ "id": 1, "name": "Test Circuit Design", "owner": {...} }]
```

### 4.5 Update Collaborator Role
```bash
# Upgrade colleague to admin
curl -X PUT http://localhost:5000/api/projects/$PROJECT_ID/shares/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "role": "admin" }'

# Expected: { "role": "admin", "permissions": { "can_share": true, ... } }
```

### 4.6 Revoke Access
```bash
# Remove colleague's access
curl -X DELETE http://localhost:5000/api/projects/$PROJECT_ID/shares/1 \
  -H "Authorization: Bearer $TOKEN"

# Expected: { "status": "ok", "message": "Access revoked" }

# Verify colleague can no longer see it
curl -H "Authorization: Bearer $COLLEAGUE_TOKEN" \
  http://localhost:5000/api/projects/shared

# Expected: [] (empty list)
```

---

## 5. Simulation & Optimization Tests

### 5.1 Run Simulation
```bash
# Submit optimization job
curl -X POST http://localhost:5000/api/simulations/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "parameters": {
      "wn": 0.5,
      "wp": 1.0,
      "vdd": 1.2,
      "temp": 27,
      "years": 10
    }
  }'

# Expected:
# {
#   "job_id": "job_abc123",
#   "status": "queued",
#   "project_id": 1
# }

# Save JOB_ID
export JOB_ID="job_abc123"
```

### 5.2 Get Simulation Status
```bash
# Poll job status
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/simulations/$JOB_ID

# Expected (while running): { "status": "running", "progress": 45 }
# Expected (completed): { "status": "completed", "results": {...} }
```

### 5.3 Direct AI Service Optimization
```bash
# Call AI service directly (circumventing backend)
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "wn": 0.5,
    "wp": 1.0,
    "vdd": 1.2,
    "temp": 27,
    "objective": "power_efficiency"
  }'

# Expected:
# {
#   "optimized_params": {
#     "wn": 0.6,
#     "wp": 1.1,
#     "vdd": 1.1
#   },
#   "performance": {
#     "freq": 2400,
#     "power": 35,
#     "health": 92,
#     "cost": "moderate"
#   },
#   "pareto_front": [...]
# }
```

### 5.4 AI Predictions
```bash
# Get ML predictions
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "wn": 0.5,
    "wp": 1.0,
    "vdd": 1.2,
    "temp": 27,
    "years": 10
  }'

# Expected:
# {
#   "health_score": 92.5,
#   "confidence": 0.87,
#   "aging_effects": {
#     "nbti": 3.2,
#     "hci": 1.5,
#     "em": 0.8
#   }
# }
```

---

## 6. Error Handling Tests

### 6.1 Unauthenticated Request
```bash
# Try to access protected endpoint without token
curl http://localhost:5000/api/projects

# Expected: 401 Unauthorized
```

### 6.2 Invalid Project ID
```bash
# Request non-existent project
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/projects/99999

# Expected: 404 Not Found
```

### 6.3 Permission Denied
```bash
# Try to access another user's project
# (using COLLEAGUE_TOKEN on original user's project)
curl -H "Authorization: Bearer $COLLEAGUE_TOKEN" \
  http://localhost:5000/api/projects/1

# Expected: 403 Forbidden (if project not shared)
```

### 6.4 Invalid Request Data
```bash
# Submit with invalid parameters
curl -X POST http://localhost:5000/api/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "name": "" }'  # Empty name

# Expected: 400 Bad Request with validation errors
```

---

## 7. Frontend Integration Tests

### 7.1 Open App in Browser
1. Go to http://localhost:3000
2. You should see the login/signup page
3. Open browser console (F12) for any errors

### 7.2 Frontend Authentication
1. Click "Sign Up"
2. Enter: email, name, password
3. Click "Create Account"
4. Should be redirected to app dashboard
5. Check localStorage: `localStorage.getItem('accessToken')` should exist

### 7.3 Create Project from Frontend
1. In dashboard, click "New Project"
2. Enter project name and description
3. Click "Create"
4. New project should appear in project list
5. Check Network tab: POST /api/projects request should succeed

### 7.4 Run Simulation from Frontend
1. Select a project
2. Click "Run Simulation"
3. Enter circuit parameters
4. Click "Optimize"
5. Wait for results
6. Check Network tab: Requests to AI service and backend should succeed

### 7.5 Share Project from Frontend
1. On project page, look for "Share" button
2. Enter colleague's email
3. Select role (editor/viewer/admin)
4. Click "Share"
5. Verify success message

### 7.6 View Shared Projects
1. Log out and log in as colleague
2. Dashboard should show both owned and shared projects
3. Shared projects should show owner name

---

## 8. Performance & Load Tests

### 8.1 Rapid Sequential Requests
```bash
# Fire multiple requests quickly
for i in {1..10}; do
  curl -H "Authorization: Bearer $TOKEN" \
    http://localhost:5000/api/projects &
done
wait

# All requests should succeed
```

### 8.2 Large Dataset Handling
```bash
# Get paginated results
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:5000/api/projects?page=1&limit=50"

# Should handle pagination correctly
```

### 8.3 AI Service Load
```bash
# Send multiple optimization requests
for i in {1..5}; do
  curl -X POST http://localhost:8000/optimize \
    -H "Content-Type: application/json" \
    -d '{"wn":0.5,"wp":1.0,"vdd":1.2,"temp":27}' &
done
wait

# All should complete successfully
```

---

## 9. Data Consistency Tests

### 9.1 Verify Database Updates
```bash
# Create project via API
curl -X POST http://localhost:5000/api/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Consistency Test"}'

# Verify it appears in list immediately
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/projects | grep "Consistency Test"

# Expected: Project should be findable
```

### 9.2 JWT Token Validation
```bash
# Get token
TOKEN=$(curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"testuser@example.com","password":"TestPassword123!"}' \
  | jq -r '.accessToken')

# Use it immediately
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/auth/me

# Should succeed

# Try with modified token (should fail)
MODIFIED_TOKEN="${TOKEN:0:10}XXXX${TOKEN:14}"
curl -H "Authorization: Bearer $MODIFIED_TOKEN" \
  http://localhost:5000/api/auth/me

# Should return 401
```

---

## 10. Integration Test Checklist

### Backend Status
- [ ] /health endpoint returns ok
- [ ] Database is accessible
- [ ] All API routes respond
- [ ] JWT authentication works
- [ ] CORS is configured correctly

### AI Service Status
- [ ] /health endpoint returns ok
- [ ] ML models are loaded
- [ ] Optimization algorithms work
- [ ] Predictions are accurate
- [ ] No GPU/CUDA errors

### Frontend Status
- [ ] Page loads without console errors
- [ ] API calls work with correct URLs
- [ ] LocalStorage works for tokens
- [ ] UI renders correctly
- [ ] Form submissions work

### Data Flow Status
- [ ] User → Backend → Database works
- [ ] User → Backend → AI Service works
- [ ] Frontend ← Backend ← Database works
- [ ] Frontend ← AI Service works
- [ ] Project sharing works end-to-end

### Security Status
- [ ] Unauthorized requests rejected
- [ ] Permission checks work
- [ ] Tokens are properly validated
- [ ] Sensitive data is not exposed
- [ ] CORS prevents unauthorized domains

---

## Continuous Integration

These tests should be automated in CI/CD:

```yaml
# Example GitHub Actions workflow
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: siliquesta_test
    
    steps:
      - uses: actions/checkout@v2
      - name: Start Backend
        run: cd backend && python -m uvicorn app.main:app &
      - name: Start AI Service
        run: cd ai-engine && python main.py &
      - name: Wait for services
        run: sleep 5
      - name: Run integration tests
        run: bash tests/integration.sh
```

## Troubleshooting Failed Tests

If a test fails:

1. **Backend error**: Check backend logs for detailed error messages
2. **AI service error**: Verify NumPy/SciPy are installed correctly
3. **Frontend error**: Check browser console for client-side errors
4. **Database error**: Verify PostgreSQL is running and accessible
5. **Network error**: Check firewall/port configuration

## Next Steps

After integration tests pass:

1. Deploy to staging environment
2. Run full end-to-end user workflows
3. Performance test under realistic load
4. Security penetration testing
5. Deploy to production
