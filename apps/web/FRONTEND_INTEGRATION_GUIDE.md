# Frontend Integration Guide

## Overview

The frontend is now fully integrated with the backend API and AI service. All components communicate through a modular service layer that handles HTTP requests, JWT authentication, and data formatting.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│            HTML Pages (UI Layer)                   │
├─────────────────────────────────────────────────────┤
│  login.html          │         app.html            │
│  (Auth)              │    (Main Application)       │
└────────────┬──────────────────────────┬────────────┘
             │                          │
┌────────────▼──────────────┬───────────▼────────────┐
│  Service Layer (Business Logic)                   │
├──────────────────────────────────────────────────┤
│  authService   │  projectService  │  simService  │
│  aiService                                        │
└──────────────┬─────────────────────┬─────────────┘
               │                     │
┌──────────────▼─────────────────────▼─────────────┐
│        APIClient (HTTP Abstraction)              │
├──────────────────────────────────────────────────┤
│  - JWT Token Management                          │
│  - Automatic Header Injection                    │
│  - Error Handling (401 redirect)                │
│  - JSON Serialization                            │
└──────────────┬─────────────────────┬─────────────┘
               │                     │
        ┌──────▼──────────────────┬──▼──────┐
        │                         │         │
   ┌────▼──────┐      ┌──────────▼─┐   ┌──▼────────┐
   │Backend API│      │ AI Service │   │localStorage│
   │(Node:5000)│      │(Python:8000)  │ (JWT)     │
   └───────────┘      └────────────┘   └───────────┘
```

## File Structure

```
frontend/
├── index.html              # Entry point (redirects to login/app)
├── login.html              # Authentication page
├── app.html                # Main application
├── landing.html            # (existing) Landing page
│
├── js/
│   ├── api-client.js       # HTTP client with JWT management
│   ├── auth-service.js     # Authentication workflow
│   ├── project-service.js  # Project CRUD operations
│   ├── simulation-service.js # Simulation execution
│   ├── ai-service.js       # AI optimization integration
│   └── ui-state.js         # State management and UI helpers
│
├── shared/
│   ├── api-config.js       # API configuration (baseURL)
│   └── runtime-config.js   # (existing)
│
├── assets/                 # Static assets
├── components/             # (existing) React components
└── downloads/              # (existing) Pre-built downloads
```

## Service Layer Details

### 1. APIClient (`api-client.js`)

**Purpose**: Centralized HTTP client for all API communication

**Key Methods**:
- `getHeaders()` - Returns headers with JWT token
- `request(method, endpoint, data)` - Generic HTTP request
- `get(endpoint)` - GET request helper
- `post(endpoint, data)` - POST request helper
- `patch(endpoint, data)` - PATCH request helper
- `delete(endpoint)` - DELETE request helper

**Usage**:
```javascript
const response = await window.apiClient.get('/users/me');
const project = await window.apiClient.post('/projects', {
  title: 'My Project',
  description: 'Project description'
});
```

**Features**:
- Automatically adds JWT token from localStorage
- Handles 401 unauthorized (redirects to login)
- Parses JSON responses
- Centralized error handling

### 2. AuthService (`auth-service.js`)

**Purpose**: Authentication workflow management

**Key Methods**:
- `signup(userData)` - Create new account
- `login(email, password)` - Authenticate user
- `logout()` - Clear auth tokens
- `getCurrentUser()` - Get currently logged-in user
- `getProfile()` - Fetch user profile
- `updateProfile(updates)` - Update user information
- `isAuthenticated()` - Check if user is logged in
- `refreshToken()` - Refresh JWT token

**Usage**:
```javascript
// Signup
const response = await window.authService.signup({
  name: 'John Doe',
  email: 'john@example.com',
  password: 'password123'
});

// Login
const response = await window.authService.login('john@example.com', 'password123');

// Check authentication
if (window.authService.isAuthenticated()) {
  const user = window.authService.getCurrentUser();
  console.log('Logged in as:', user.name);
}

// Logout
window.authService.logout();
```

**Token Management**:
- Stores JWT token in `localStorage['auth_token']`
- Stores refresh token in `localStorage['refresh_token']`
- Automatically redirects to login on 401 error
- Handles token expiration (7 days)

### 3. ProjectService (`project-service.js`)

**Purpose**: Project CRUD operations

**Key Methods**:
- `createProject(title, description)` - Create new project
- `getProjects(options)` - Fetch user projects with pagination
- `getProject(projectId)` - Get single project details
- `updateProject(projectId, updates)` - Update project
- `deleteProject(projectId)` - Delete project
- `getProjectStats()` - Get project statistics

**Usage**:
```javascript
// Create project
const project = await window.projectService.createProject(
  'Inverter Circuit',
  'Low power inverter design'
);

// Get all projects with pagination
const projects = await window.projectService.getProjects({
  page: 1,
  limit: 10,
  status: 'active', // optional
  search: 'Inverter' // optional search
});

// Get single project
const project = await window.projectService.getProject(projectId);

// Update project
const updated = await window.projectService.updateProject(projectId, {
  title: 'Updated Title',
  description: 'Updated description'
});

// Delete project
await window.projectService.deleteProject(projectId);

// Get statistics
const stats = await window.projectService.getProjectStats();
console.log(`Total projects: ${stats.total}`);
```

**API Endpoints Used**:
- `POST /api/projects` - Create
- `GET /api/projects` - List
- `GET /api/projects/:id` - Get single
- `PATCH /api/projects/:id` - Update
- `DELETE /api/projects/:id` - Delete
- `GET /api/projects/stats` - Statistics

### 4. SimulationService (`simulation-service.js`)

**Purpose**: Simulation execution and management

**Key Methods**:
- `createSimulation(projectId, name, parameters)` - Create new simulation
- `getSimulations(options)` - Fetch simulations with pagination
- `getSimulation(simulationId)` - Get single simulation
- `updateSimulation(simulationId, updates)` - Update simulation
- `deleteSimulation(simulationId)` - Delete simulation
- `runSimulation(projectId, name)` - Execute simulation
- `getResults(simulationId)` - Get simulation results
- `formatResults(results)` - Format results for UI display

**Usage**:
```javascript
// Run simulation
const result = await window.simulationService.runSimulation(
  projectId,
  'Test Run 1'
);
console.log('Simulation status:', result.status);

// Get all simulations
const sims = await window.simulationService.getSimulations({
  page: 1,
  limit: 10,
  status: 'completed' // optional
});

// Get single simulation results
const sim = await window.simulationService.getSimulation(simulationId);
const formatted = window.simulationService.formatResults(sim.results);
console.log('Power:', formatted.power);
console.log('Delay:', formatted.delay);

// API Response Format
{
  id: 123,
  project_id: 456,
  name: 'Test Run 1',
  status: 'completed', // pending, running, completed, failed
  results: {
    gain: 42.5,
    power: 1.2e-6,
    delay: 3.5e-9,
    area: 2.1e-12,
    convergence: 0.95
  },
  created_at: '2024-01-15T10:30:00Z'
}
```

### 5. AIOptimizationService (`ai-service.js`)

**Purpose**: Circuit parameter optimization using AI

**Key Methods**:
- `checkHealth()` - Verify AI service is running
- `optimize(parameters)` - Run optimization algorithm
- `formatResults(results)` - Format results for display

**Usage**:
```javascript
// Check AI service health
const health = await window.aiService.checkHealth();
console.log('AI Service:', health.status);

// Run optimization
const params = {
  circuit_type: 'Inverter',
  width: 100,          // nm
  length: 50,          // nm
  vdd: 3.3,            // V
  frequency: 1         // GHz
};

const result = await window.aiService.optimize(params);

// Response format
{
  original_parameters: {
    width: 100,
    length: 50,
    vdd: 3.3,
    frequency: 1
  },
  optimized_parameters: {
    width: 95,
    length: 48,
    vdd: 3.2,
    frequency: 1.05
  },
  metrics: {
    power_reduction: 0.18,
    speed_improvement: 0.12,
    area_reduction: 0.05
  },
  improvements: {
    width: -5,
    length: -4,
    vdd: -0.1,
    frequency: 5
  },
  optimization_time: 2.34 // seconds
}
```

### 6. UIHelpers & UIState (`ui-state.js`)

**Purpose**: UI state management and helper functions

**UIState Methods**:
- `setState(updates)` - Update application state
- `getState()` - Get current state
- `setLoading(isLoading, message)` - Set loading state
- `setError(error)` - Set error state
- `clearError()` - Clear error

**UIHelpers Methods**:
- `showLoader(message)` - Show loading overlay
- `hideLoader()` - Hide loading overlay
- `showNotification(message, type)` - Show notification toast
- `formatNumber(num, decimals)` - Format number
- `formatScientific(num, decimals)` - Format scientific notation
- `formatPercentage(num, decimals)` - Format percentage
- `createParameterTable(params, title)` - Create HTML table
- `enableForm(form, enabled)` - Enable/disable form
- `getFormData(form)` - Extract form data as object
- `populateForm(form, data)` - Populate form from object

**Usage**:
```javascript
// Show loader
UIHelpers.showLoader('Running optimization...');

// Hide loader
UIHelpers.hideLoader();

// Show notification
UIHelpers.showNotification('Project created!', 'success');
UIHelpers.showNotification('Error occurred', 'error');

// Format numbers
UIHelpers.formatNumber(3.14159, 2)      // "3.14"
UIHelpers.formatScientific(0.000001)    // "1.00e-6"
UIHelpers.formatPercentage(0.456)       // "45.6%"

// Form handling
const data = UIHelpers.getFormData(formElement);
UIHelpers.populateForm(formElement, data);
```

## Authentication Flow

### Login/Signup Flow

```
┌─────────────────┐
│  login.html     │  ← User enters credentials
└────────┬────────┘
         │
         ▼
┌────────────────────────────────────┐
│ authService.login/signup()         │
└────────┬───────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│ POST /api/auth/login               │
│ POST /api/auth/signup              │  → Backend validates
└────────┬───────────────────────────┘
         │
         ▼ ✓ Success
┌────────────────────────────────────┐
│ Store JWT in localStorage          │
│ Store refresh token in localStorage│
└────────┬───────────────────────────┘
         │
         ▼
┌─────────────────┐
│ Redirect to     │  → app.html
│ app.html        │
└─────────────────┘
```

### Protected Route Check

```
User navigates to app.html
         │
         ▼
authService.isAuthenticated()
         │
    ┌────┴────┐
    │          │
    ▼ No      ▼ Yes
Redirect    Load
to login    app
```

## API Integration Points

### Backend API (http://localhost:5000/api)

**Authentication**:
```
POST /auth/signup
{
  name: string,
  email: string (unique),
  password: string (min 6 chars)
}

POST /auth/login
{
  email: string,
  password: string
}

Response:
{
  success: boolean,
  token: string (JWT),
  refreshToken: string,
  user: {
    id: number,
    name: string,
    email: string
  }
}
```

**Projects**:
```
POST /projects
{ title: string, description?: string }

GET /projects?page=1&limit=10&status=active&search=term

GET /projects/:id

PATCH /projects/:id
{ title?: string, description?: string }

DELETE /projects/:id

GET /projects/stats
```

**Simulations**:
```
POST /simulations
{ projectId: number, name: string }

GET /simulations?page=1&limit=10&status=completed

GET /simulations/:id

PATCH /simulations/:id
{ status?: string }

DELETE /simulations/:id

GET /simulations/:id/results
```

### AI Service API (http://localhost:8000)

**Health Check**:
```
GET /health
Response: { status: "healthy" }
```

**Optimization**:
```
POST /optimize
{
  circuit_type: string,
  width: number,
  length: number,
  vdd: number,
  frequency: number
}

Response:
{
  original_parameters: { ... },
  optimized_parameters: { ... },
  metrics: { ... },
  improvements: { ... },
  optimization_time: number
}
```

## Running the Frontend

### Development Mode

```bash
# 1. Install dependencies (if using Node-based dev server)
npm install -g http-server

# 2. Start HTTP server
http-server frontend/ -p 3000 -c-1

# 3. Open browser
# http://localhost:3000/login.html
```

### Viewing Files Directly

```bash
# Option 1: Open in browser
file:///full/path/to/frontend/login.html

# Option 2: Use VS Code Live Server
# Install extension: Live Server
# Right-click index.html → "Open with Live Server"
```

## Common Workflows

### 1. Create and Simulate a Project

```javascript
// Step 1: Create project
const project = await window.projectService.createProject(
  'My Inverter',
  'A low-power inverter design'
);

// Step 2: Run simulation
const sim = await window.simulationService.runSimulation(
  project.id,
  'Initial Run'
);

// Step 3: Get results
const results = await window.simulationService.getResults(sim.id);
console.log('Simulation Results:', results);
```

### 2. Optimize Circuit Parameters

```javascript
const params = {
  circuit_type: 'Inverter',
  width: 100,
  length: 50,
  vdd: 3.3,
  frequency: 1
};

const result = await window.aiService.optimize(params);

// Display improvements
Object.entries(result.improvements).forEach(([key, value]) => {
  console.log(`${key}: ${UIHelpers.formatPercentage(Math.abs(value))} improvement`);
});
```

### 3. Handle Errors Gracefully

```javascript
try {
  UIHelpers.showLoader('Processing...');
  const result = await someLongOperation();
  UIHelpers.showNotification('Success!', 'success');
} catch (error) {
  console.error('Error:', error);
  UIHelpers.showNotification(error.message || 'An error occurred', 'error');
} finally {
  UIHelpers.hideLoader();
}
```

## Troubleshooting

### Issue: 401 Unauthorized

**Cause**: JWT token expired or missing

**Solution**:
```javascript
// Automatic: APIClient will redirect to login
// Manual: Check authentication
if (!window.authService.isAuthenticated()) {
  window.location.href = '/login.html';
}
```

### Issue: CORS Error

**Cause**: Backend not allowing frontend domain

**Solution**:
1. Verify backend CORS configuration
2. Check API_CONFIG in shared/api-config.js
3. Ensure backend is running on correct port (5000)

### Issue: AI Service Not Responding

**Cause**: Python service offline

**Solution**:
```javascript
// Check service health
try {
  const health = await window.aiService.checkHealth();
  console.log('AI Service Status:', health.status);
} catch (error) {
  console.log('AI Service is offline');
}
```

### Issue: Form Data Not Submitting

**Debugging**:
```javascript
const form = document.getElementById('my-form');
const data = UIHelpers.getFormData(form);
console.log('Form Data:', data); // Check data structure
```

## Best Practices

1. **Always use services, not direct fetch calls**
   - Keep API logic centralized in service layer
   - Makes debugging and maintenance easier

2. **Handle loading states**
   - Show loader during async operations
   - Disable buttons during submission
   - Provide user feedback

3. **Validate input before sending to API**
   - Check required fields
   - Validate email format
   - Check password length

4. **Show meaningful error messages**
   - Use UIHelpers.showNotification()
   - Log errors to console for debugging
   - Display user-friendly error text

5. **Manage tokens securely**
   - Never log tokens to console in production
   - Use httpOnly cookies for sensitive data (future enhancement)
   - Implement token refresh before expiration

## Next Steps

### Frontend Enhancement Ideas

1. **Add Analytics**
   - Track user actions
   - Monitor API performance
   - Page load metrics

2. **Implement Caching**
   - Cache projects/simulations list
   - Reduce API calls
   - Better offline support

3. **Add Data Persistence**
   - Save drafts locally
   - Resume incomplete simulations
   - Version control for projects

4. **Enhanced UI Components**
   - Real-time simulation progress
   - Circuit visualization
   - Parameter optimization charts

5. **Mobile Responsiveness**
   - Touch-friendly UI
   - Mobile-optimized layouts
   - Works on tablets/phones

## Support

For issues or questions:
1. Check browser console for errors
2. Verify backend is running (`http://localhost:5000/health`)
3. Verify AI service is running (`http://localhost:8000/health`)
4. Check network requests in DevTools
5. Refer to backend and AI service documentation
