# SILIQUESTA Backend API Documentation

Complete API reference with request/response examples.

## Base URL
```
http://localhost:5000/api
```

## Authentication

All protected endpoints require the `Authorization` header:
```
Authorization: Bearer <accessToken>
```

---

## 🔐 Authentication Endpoints

### 1. Sign Up
Create a new user account.

**Request:**
```http
POST /auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "SecurePassword123!",
  "confirmPassword": "SecurePassword123!"
}
```

**Response (201 Created):**
```json
{
  "message": "User created successfully",
  "user": {
    "id": "clh1a2b3c4d5e6f7g8h9i0j",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user",
    "createdAt": "2024-04-11T10:30:00Z"
  },
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### 2. Login
Authenticate user and get tokens.

**Request:**
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "message": "Login successful",
  "user": {
    "id": "clh1a2b3c4d5e6f7g8h9i0j",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user",
    "isActive": true,
    "createdAt": "2024-04-11T10:30:00Z",
    "lastLogin": "2024-04-11T14:22:15Z"
  },
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### 3. Get Current User
Get authenticated user's profile information.

**Request:**
```http
GET /auth/me
Authorization: Bearer <accessToken>
```

**Response (200 OK):**
```json
{
  "user": {
    "id": "clh1a2b3c4d5e6f7g8h9i0j",
    "email": "user@example.com",
    "name": "John Doe",
    "avatar": "https://example.com/avatar.jpg",
    "bio": "Software engineer",
    "role": "user",
    "isActive": true,
    "createdAt": "2024-04-11T10:30:00Z",
    "updatedAt": "2024-04-11T12:00:00Z",
    "lastLogin": "2024-04-11T14:22:15Z"
  }
}
```

---

### 4. Update Profile
Update user profile information.

**Request:**
```http
PATCH /auth/profile
Authorization: Bearer <accessToken>
Content-Type: application/json

{
  "name": "John Smith",
  "bio": "Lead Software Engineer",
  "avatar": "https://example.com/new-avatar.jpg"
}
```

**Response (200 OK):**
```json
{
  "message": "Profile updated successfully",
  "user": {
    "id": "clh1a2b3c4d5e6f7g8h9i0j",
    "email": "user@example.com",
    "name": "John Smith",
    "avatar": "https://example.com/new-avatar.jpg",
    "bio": "Lead Software Engineer",
    "role": "user",
    "createdAt": "2024-04-11T10:30:00Z",
    "updatedAt": "2024-04-11T14:25:00Z"
  }
}
```

---

### 5. Change Password
Change user password.

**Request:**
```http
POST /auth/change-password
Authorization: Bearer <accessToken>
Content-Type: application/json

{
  "oldPassword": "SecurePassword123!",
  "newPassword": "NewSecurePassword456!"
}
```

**Response (200 OK):**
```json
{
  "message": "Password changed successfully"
}
```

---

### 6. Refresh Token
Get new access token using refresh token.

**Request:**
```http
POST /auth/refresh
Content-Type: application/json

{
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "message": "Token refreshed successfully",
  "user": { ... },
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### 7. Logout
Logout user (client-side token invalidation).

**Request:**
```http
POST /auth/logout
Authorization: Bearer <accessToken>
```

**Response (200 OK):**
```json
{
  "message": "Logged out successfully"
}
```

---

## 📋 Project Endpoints

### 1. Create Project
Create a new project.

**Request:**
```http
POST /projects
Authorization: Bearer <accessToken>
Content-Type: application/json

{
  "title": "Thermal Analysis 2024",
  "description": "Advanced heat transfer simulation for aerospace components",
  "parameters": {
    "material": "titanium",
    "temperature": 500,
    "pressure": 10
  },
  "metadata": {
    "industry": "aerospace",
    "priority": "high",
    "deadline": "2024-06-30"
  }
}
```

**Response (201 Created):**
```json
{
  "message": "Project created successfully",
  "project": {
    "id": "proj_1a2b3c4d5e6f7g8h9i0j",
    "title": "Thermal Analysis 2024",
    "description": "Advanced heat transfer simulation for aerospace components",
    "slug": "thermal-analysis-2024",
    "status": "active",
    "parameters": {
      "material": "titanium",
      "temperature": 500,
      "pressure": 10
    },
    "metadata": {
      "industry": "aerospace",
      "priority": "high",
      "deadline": "2024-06-30"
    },
    "userId": "clh1a2b3c4d5e6f7g8h9i0j",
    "simulationCount": 0,
    "createdAt": "2024-04-11T15:00:00Z",
    "updatedAt": "2024-04-11T15:00:00Z"
  }
}
```

---

### 2. Get All Projects
Get paginated list of user's projects.

**Request:**
```http
GET /projects?page=1&limit=10&status=active&search=thermal
Authorization: Bearer <accessToken>
```

**Response (200 OK):**
```json
{
  "message": "Projects retrieved successfully",
  "data": [
    {
      "id": "proj_1a2b3c4d5e6f7g8h9i0j",
      "title": "Thermal Analysis 2024",
      "description": "Advanced heat transfer simulation...",
      "slug": "thermal-analysis-2024",
      "status": "active",
      "userId": "clh1a2b3c4d5e6f7g8h9i0j",
      "simulationCount": 5,
      "createdAt": "2024-04-11T15:00:00Z",
      "updatedAt": "2024-04-11T15:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 1,
    "pages": 1
  }
}
```

---

### 3. Get Project by ID
Get single project with recent simulations.

**Request:**
```http
GET /projects/proj_1a2b3c4d5e6f7g8h9i0j
Authorization: Bearer <accessToken>
```

**Response (200 OK):**
```json
{
  "message": "Project retrieved successfully",
  "project": {
    "id": "proj_1a2b3c4d5e6f7g8h9i0j",
    "title": "Thermal Analysis 2024",
    "description": "Advanced heat transfer simulation for aerospace components",
    "slug": "thermal-analysis-2024",
    "status": "active",
    "parameters": { ... },
    "metadata": { ... },
    "userId": "clh1a2b3c4d5e6f7g8h9i0j",
    "simulationCount": 5,
    "createdAt": "2024-04-11T15:00:00Z",
    "updatedAt": "2024-04-11T15:00:00Z",
    "simulations": [
      {
        "id": "sim_1a2b3c4d",
        "title": "Initial CFD Run",
        "status": "completed",
        "createdAt": "2024-04-11T15:30:00Z"
      }
    ]
  }
}
```

---

### 4. Update Project
Update project details.

**Request:**
```http
PATCH /projects/proj_1a2b3c4d5e6f7g8h9i0j
Authorization: Bearer <accessToken>
Content-Type: application/json

{
  "title": "Thermal Analysis 2024 - Updated",
  "description": "Enhanced heat transfer analysis",
  "status": "active",
  "parameters": {
    "material": "steel",
    "temperature": 600
  }
}
```

**Response (200 OK):**
```json
{
  "message": "Project updated successfully",
  "project": { ... }
}
```

---

### 5. Delete Project
Delete a project (cascades to simulations).

**Request:**
```http
DELETE /projects/proj_1a2b3c4d5e6f7g8h9i0j
Authorization: Bearer <accessToken>
```

**Response (200 OK):**
```json
{
  "message": "Project deleted successfully"
}
```

---

### 6. Get Project Statistics
Get project simulation statistics.

**Request:**
```http
GET /projects/proj_1a2b3c4d5e6f7g8h9i0j/stats
Authorization: Bearer <accessToken>
```

**Response (200 OK):**
```json
{
  "message": "Project statistics retrieved successfully",
  "stats": {
    "total": 5,
    "completed": 3,
    "running": 1,
    "failed": 0,
    "pending": 1
  }
}
```

---

## 🧪 Simulation Endpoints

### 1. Create Simulation
Create a new simulation within a project.

**Request:**
```http
POST /simulations
Authorization: Bearer <accessToken>
Content-Type: application/json

{
  "title": "Initial FEA Run",
  "description": "First iteration with coarse mesh",
  "input": {
    "meshDensity": 0.5,
    "flowRate": 100,
    "iterations": 1000
  },
  "parameters": {
    "material": "steel",
    "temperature": 500
  },
  "config": {
    "solver": "iterative",
    "tolerance": 1e-6
  },
  "projectId": "proj_1a2b3c4d5e6f7g8h9i0j"
}
```

**Response (201 Created):**
```json
{
  "message": "Simulation created successfully",
  "simulation": {
    "id": "sim_1a2b3c4d5e6f7g8h9i0j",
    "title": "Initial FEA Run",
    "description": "First iteration with coarse mesh",
    "status": "pending",
    "input": { ... },
    "output": null,
    "parameters": { ... },
    "config": { ... },
    "results": null,
    "error": null,
    "projectId": "proj_1a2b3c4d5e6f7g8h9i0j",
    "userId": "clh1a2b3c4d5e6f7g8h9i0j",
    "createdAt": "2024-04-11T16:00:00Z",
    "updatedAt": "2024-04-11T16:00:00Z",
    "startedAt": null,
    "completedAt": null
  }
}
```

---

### 2. Get Simulations
Get paginated simulations for a project.

**Request:**
```http
GET /simulations?projectId=proj_1a2b3c4d5e6f7g8h9i0j&page=1&limit=10&status=completed
Authorization: Bearer <accessToken>
```

**Response (200 OK):**
```json
{
  "message": "Simulations retrieved successfully",
  "data": [
    {
      "id": "sim_1a2b3c4d",
      "title": "Initial FEA Run",
      "description": "First iteration with coarse mesh",
      "status": "completed",
      "duration": 15000,
      "createdAt": "2024-04-11T16:00:00Z",
      "completedAt": "2024-04-11T16:15:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 1,
    "pages": 1
  }
}
```

---

### 3. Get Simulation by ID
Get single simulation details.

**Request:**
```http
GET /simulations/sim_1a2b3c4d5e6f7g8h9i0j
Authorization: Bearer <accessToken>
```

**Response (200 OK):**
```json
{
  "message": "Simulation retrieved successfully",
  "simulation": {
    "id": "sim_1a2b3c4d5e6f7g8h9i0j",
    "title": "Initial FEA Run",
    "description": "First iteration with coarse mesh",
    "status": "completed",
    "input": { ... },
    "output": { ... },
    "parameters": { ... },
    "config": { ... },
    "results": { ... },
    "duration": 15000,
    "projectId": "proj_1a2b3c4d5e6f7g8h9i0j",
    "userId": "clh1a2b3c4d5e6f7g8h9i0j",
    "createdAt": "2024-04-11T16:00:00Z",
    "completedAt": "2024-04-11T16:15:00Z",
    "project": {
      "id": "proj_1a2b3c4d5e6f7g8h9i0j",
      "title": "Thermal Analysis 2024",
      "slug": "thermal-analysis-2024"
    }
  }
}
```

---

### 4. Run Simulation
Execute/start a simulation.

**Request:**
```http
POST /simulations/sim_1a2b3c4d5e6f7g8h9i0j/run
Authorization: Bearer <accessToken>
```

**Response (200 OK):**
```json
{
  "message": "Simulation completed successfully",
  "simulation": {
    "id": "sim_1a2b3c4d5e6f7g8h9i0j",
    "title": "Initial FEA Run",
    "status": "completed",
    "output": {
      "processedAt": "2024-04-11T16:15:30Z",
      "iterationsCompleted": 1000,
      "input": { ... }
    },
    "results": {
      "convergence": 0.999,
      "error": 0.001,
      "accuracy": 0.98,
      "iterationsRun": 1000,
      "timestamp": "2024-04-11T16:15:30Z"
    },
    "duration": 15000,
    "completedAt": "2024-04-11T16:15:30Z"
  }
}
```

---

### 5. Get Simulation Results
Get final results of a completed simulation.

**Request:**
```http
GET /simulations/sim_1a2b3c4d5e6f7g8h9i0j/results
Authorization: Bearer <accessToken>
```

**Response (200 OK):**
```json
{
  "message": "Simulation results retrieved successfully",
  "simulation": {
    "id": "sim_1a2b3c4d5e6f7g8h9i0j",
    "title": "Initial FEA Run",
    "status": "completed",
    "input": { ... },
    "output": { ... },
    "results": { ... },
    "duration": 15000,
    "error": null,
    "createdAt": "2024-04-11T16:00:00Z",
    "completedAt": "2024-04-11T16:15:00Z"
  }
}
```

---

### 6. Update Simulation
Update simulation status or data.

**Request:**
```http
PATCH /simulations/sim_1a2b3c4d5e6f7g8h9i0j
Authorization: Bearer <accessToken>
Content-Type: application/json

{
  "status": "completed",
  "results": {
    "convergence": 0.999,
    "error": 0.001
  }
}
```

**Response (200 OK):**
```json
{
  "message": "Simulation updated successfully",
  "simulation": { ... }
}
```

---

### 7. Delete Simulation
Delete a simulation.

**Request:**
```http
DELETE /simulations/sim_1a2b3c4d5e6f7g8h9i0j
Authorization: Bearer <accessToken>
```

**Response (200 OK):**
```json
{
  "message": "Simulation deleted successfully"
}
```

---

## 🔴 Error Responses

### Validation Error (400)
```json
{
  "error": "Validation Error",
  "message": "Invalid input",
  "details": {
    "email": "email must be a valid email",
    "password": "password must be at least 8 characters"
  }
}
```

### Unauthorized (401)
```json
{
  "error": "Unauthorized",
  "message": "Invalid token"
}
```

### Forbidden (403)
```json
{
  "error": "Forbidden",
  "message": "Insufficient permissions"
}
```

### Not Found (404)
```json
{
  "error": "Not Found",
  "message": "Project not found or unauthorized"
}
```

### Conflict (409)
```json
{
  "error": "Conflict",
  "message": "Email already registered"
}
```

### Server Error (500)
```json
{
  "error": "Error",
  "message": "Internal Server Error"
}
```

---

## 📝 Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PATCH, POST (query) |
| 201 | Created | Successful POST (creation) |
| 400 | Bad Request | Validation error |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate/conflict |
| 500 | Server Error | Internal error |

---

## 🧪 Quick Test

```bash
# 1. Register
curl -X POST http://localhost:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "password": "Test123!@#",
    "confirmPassword": "Test123!@#"
  }'

# 2. Login and save token
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!@#"
  }'

# 3. Create project (replace TOKEN)
curl -X POST http://localhost:5000/api/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "title": "My Project",
    "description": "Test"
  }'
```

---

For more information, see [README.md](./README.md)
