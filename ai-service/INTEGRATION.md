# Integration Guide - AI Service with Node Backend

Complete guide to integrate the FastAPI AI optimization microservice with your Express.js Node backend.

## 🔗 Architecture Overview

```
┌─────────────────┐
│   Frontend      │
│  (React/Next)   │
└────────┬────────┘
         │
         ↓
┌─────────────────────────────────────────┐
│   Node.js Express Backend (Port 5000)   │
│  - Auth, Projects, Simulations, Routing │
│  - Calls AI Service for optimization    │
└────────┬────────────────────────────────┘
         │
         ↓
┌──────────────────────────────────────────┐
│  FastAPI AI Service (Port 8000)          │
│  - SciPy Optimization                    │
│  - Circuit Parameter Tuning              │
│  - ML Models                             │
└──────────────────────────────────────────┘
```

## 🚀 Setup Steps

### Step 1: Update Backend .env

Add AI service configuration to `backend/.env`:

```env
# Existing configuration...
NODE_ENV=development
PORT=5000
DATABASE_URL=postgresql://...
JWT_SECRET=...

# NEW: AI Service Configuration
AI_SERVICE_URL=http://localhost:8000
AI_SERVICE_TIMEOUT=60000
AI_SERVICE_ENABLED=true
```

### Step 2: Create AI Integration Service

Create `backend/src/services/aiService.js`:

```javascript
import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:8000';
const TIMEOUT = parseInt(process.env.AI_SERVICE_TIMEOUT) || 60000;

class AIService {
  /**
   * Create axios client for AI service
   */
  static getClient() {
    return axios.create({
      baseURL: AI_SERVICE_URL,
      timeout: TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Check AI service health
   */
  static async healthCheck() {
    try {
      const client = this.getClient();
      const response = await client.get('/health');
      return response.data;
    } catch (error) {
      console.error('AI Service health check failed:', error.message);
      throw new Error('AI Service unavailable');
    }
  }

  /**
   * Optimize circuit parameters
   * @param {Object} parameters - Circuit parameters
   * @param {Object} objectives - Optimization objectives
   * @param {Object} options - Additional options
   * @returns {Promise<Object>} - Optimization results
   */
  static async optimizeCircuit(parameters, objectives, options = {}) {
    try {
      const client = this.getClient();

      const payload = {
        parameters: {
          W_L_ratio: parameters.WLRatio || 10,
          finger_ratio: parameters.fingerRatio || 1,
          supply_voltage: parameters.supplyVoltage || 1.8,
          operating_frequency: parameters.frequency || 1e9,
          load_capacitance: parameters.loadCapacitance || 1e-12,
          technology_node: parameters.techNode || 28e-9,
          temperature: parameters.temperature || 27,
          bias_current: parameters.biasCurrent || 1e-6,
          ...(parameters.powerBudget && { power_budget: parameters.powerBudget }),
          ...(parameters.areaBudget && { area_budget: parameters.areaBudget }),
        },
        objectives: {
          minimize_power: objectives.minimizePower ?? true,
          minimize_area: objectives.minimizeArea ?? false,
          maximize_speed: objectives.maximizeSpeed ?? true,
          maximize_gain: objectives.maximizeGain ?? false,
        },
        method: options.method || 'scipy',
        max_iterations: options.maxIterations || 500,
        tolerance: options.tolerance || 1e-6,
      };

      console.log('Calling AI Service with payload:', JSON.stringify(payload, null, 2));

      const response = await client.post('/optimize', payload);

      return response.data;
    } catch (error) {
      console.error('AI optimization failed:', error.message);
      throw new Error(`Optimization failed: ${error.message}`);
    }
  }

  /**
   * Get service info
   */
  static async getInfo() {
    try {
      const client = this.getClient();
      const response = await client.get('/info');
      return response.data;
    } catch (error) {
      console.error('Failed to get AI service info:', error.message);
      throw error;
    }
  }
}

export default AIService;
```

### Step 3: Create Optimization Controller

Create `backend/src/controllers/optimizationController.js`:

```javascript
import AIService from '../services/aiService.js';
import { prisma } from '../config/database.js';

export class OptimizationController {
  /**
   * Optimize simulation parameters
   * POST /api/optimizations/simulate
   */
  static optimize = async (req, res, next) => {
    try {
      const userId = req.user.userId;
      const { simulationId, parameters, objectives, projectId } = req.validatedData;

      // Verify project ownership
      const project = await prisma.project.findFirst({
        where: { id: projectId, userId },
      });

      if (!project) {
        return res.status(404).json({
          error: 'Not Found',
          message: 'Project not found or unauthorized',
        });
      }

      // Call AI service
      const optimizationResult = await AIService.optimizeCircuit(
        parameters,
        objectives || {}
      );

      // Save optimization result to database
      const optimization = await prisma.simulation.create({
        data: {
          title: `Optimization - ${new Date().toISOString()}`,
          description: `AI-optimized parameters from simulation ${simulationId}`,
          status: 'completed',
          input: parameters,
          output: optimizationResult.optimized_parameters,
          results: {
            ...optimizationResult.metrics_comparison,
            overall_improvement: optimizationResult.overall_improvement,
          },
          projectId,
          userId,
          duration: optimizationResult.execution_time * 1000,
          completedAt: new Date(),
        },
      });

      res.status(200).json({
        message: 'Optimization completed successfully',
        optimization,
        details: optimizationResult,
      });
    } catch (error) {
      next(error);
    }
  };

  /**
   * Check AI service health
   * GET /api/optimizations/health
   */
  static checkHealth = async (req, res, next) => {
    try {
      const health = await AIService.healthCheck();
      res.status(200).json({ health });
    } catch (error) {
      res.status(503).json({
        error: 'Service Unavailable',
        message: 'AI optimization service is not available',
      });
    }
  };

  /**
   * Get optimization suggestions
   * POST /api/optimizations/suggest
   */
  static getSuggestions = async (req, res, next) => {
    try {
      const { projectId, simulationStats } = req.validatedData;
      const userId = req.user.userId;

      // Auto-detect optimization objectives based on stats
      const objectives = {
        minimizePower: simulationStats.avgPower > 1e-3,
        maximizeSpeed: simulationStats.avgDelay > 1e-9,
        minimizeArea: simulationStats.avgArea > 1e-9,
        maximizeGain: simulationStats.avgGain < 20,
      };

      res.status(200).json({
        message: 'Optimization suggestions',
        objectives,
        recommendations: [
          objectives.minimizePower && 'Consider reducing supply voltage',
          objectives.maximizeSpeed && 'Increase transistor sizing',
          objectives.minimizeArea && 'Optimize layout efficiency',
          objectives.maximizeGain && 'Improve gain stage design',
        ].filter(Boolean),
      });
    } catch (error) {
      next(error);
    }
  };
}

export default OptimizationController;
```

### Step 4: Create Optimization Routes

Create `backend/src/routes/optimizationRoutes.js`:

```javascript
import express from 'express';
import { authenticate } from '../middleware/auth.js';
import { validateBody } from '../middleware/validation.js';
import Joi from 'joi';
import OptimizationController from '../controllers/optimizationController.js';

const router = express.Router();

// Validation schemas
const optimizeSchema = Joi.object({
  simulationId: Joi.string(),
  projectId: Joi.string().required(),
  parameters: Joi.object({
    WLRatio: Joi.number().positive(),
    fingerRatio: Joi.number().positive(),
    supplyVoltage: Joi.number().positive(),
    frequency: Joi.number().positive(),
    loadCapacitance: Joi.number().positive(),
    biasCurrent: Joi.number().positive(),
    powerBudget: Joi.number().positive(),
    areaBudget: Joi.number().positive(),
  }).required(),
  objectives: Joi.object({
    minimizePower: Joi.boolean(),
    minimizeArea: Joi.boolean(),
    maximizeSpeed: Joi.boolean(),
    maximizeGain: Joi.boolean(),
  }),
});

const suggestionsSchema = Joi.object({
  projectId: Joi.string().required(),
  simulationStats: Joi.object({
    avgPower: Joi.number().positive(),
    avgDelay: Joi.number().positive(),
    avgArea: Joi.number().positive(),
    avgGain: Joi.number(),
  }).required(),
});

// All routes require authentication
router.use(authenticate);

/**
 * Optimization Routes
 * POST /api/optimizations/optimize - Optimize circuit parameters
 * GET /api/optimizations/health - Check AI service health
 * POST /api/optimizations/suggest - Get optimization suggestions
 */

router.post(
  '/optimize',
  validateBody(optimizeSchema),
  OptimizationController.optimize
);

router.get('/health', OptimizationController.checkHealth);

router.post(
  '/suggest',
  validateBody(suggestionsSchema),
  OptimizationController.getSuggestions
);

export default router;
```

### Step 5: Register Optimization Routes

Update `backend/src/server.js`:

```javascript
import optimizationRoutes from './routes/optimizationRoutes.js';

// ... existing imports and setup ...

// Add optimization routes
app.use('/api/optimizations', optimizationRoutes);

// ... rest of server.js ...
```

## 📝 Usage Example

### From Frontend

```javascript
// frontend/components/OptimizePanel.tsx
const optimizeCircuit = async () => {
  try {
    const response = await fetch('/api/optimizations/optimize', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        projectId: project.id,
        parameters: {
          WLRatio: 10,
          supplyVoltage: 1.8,
          frequency: 1e9,
        },
        objectives: {
          minimizePower: true,
          maximizeSpeed: true,
        },
      }),
    });

    const result = await response.json();
    console.log('Optimization result:', result);
    // Update UI with result.details
  } catch (error) {
    console.error('Optimization failed:', error);
  }
};
```

### CURL Test

```bash
# Test that both services are running
curl http://localhost:5000/api
curl http://localhost:8000/info

# Call optimization through backend
curl -X POST http://localhost:5000/api/optimizations/optimize \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "projectId": "proj_123",
    "parameters": {
      "WLRatio": 10,
      "supplyVoltage": 1.8
    },
    "objectives": {
      "minimizePower": true,
      "maximizeSpeed": true
    }
  }'
```

## 🔄 Workflow

1. **User creates project** → Backend saves to database
2. **User uploads simulation data** → Simulations table populated
3. **User clicks "Optimize"** → Frontend calls `/api/optimizations/optimize`
4. **Backend receives request** → Calls AI Service at `http://localhost:8000/optimize`
5. **AI Service optimizes** → Returns optimized parameters (≈2-3s)
6. **Backend saves results** → Stores optimization in simulations table
7. **Frontend displays** → Shows improvement metrics and optimized params

## 📊 Example Data Flow

```
Frontend Input:
{
  "projectId": "proj_123abc",
  "parameters": {
    "WLRatio": 10,
    "supplyVoltage": 1.8,
    "frequency": 1e9
  },
  "objectives": {
    "minimizePower": true,
    "maximizeSpeed": true
  }
}
            ↓
Backend Transforms & Sends to AI Service
            ↓
AI Service Optimizes (2-3 seconds)
            ↓
Backend Receives:
{
  "optimized_parameters": {...},
  "overall_improvement": 20.67,
  "iterations_used": 127
}
            ↓
Backend Saves to Database as Simulation
            ↓
Frontend Displays Results
```

## ⚙️ Configuration

### Environment Variables

```env
# backend/.env
AI_SERVICE_URL=http://localhost:8000
AI_SERVICE_TIMEOUT=60000

# For production
# AI_SERVICE_URL=https://ai-service.example.com
```

### At Scale

```env
# Load balancing between multiple AI services
AI_SERVICE_URLS=http://ai-1:8000,http://ai-2:8000,http://ai-3:8000
AI_SERVICE_STRATEGY=round-robin
```

## 🧪 Testing

```bash
# 1. Start AI service
cd ai-service
python -m uvicorn main:app --reload

# 2. In another terminal, start backend
cd backend
npm run dev

# 3. Test health
curl http://localhost:5000/api
curl http://localhost:8000/health

# 4. Run optimization
curl -X POST http://localhost:5000/api/optimizations/optimize \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{...}'
```

## 📈 Monitoring

Monitor both services' performance:

```javascript
// backend/middleware/monitoringMiddleware.js
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    if (req.path.includes('/optimizations')) {
      console.log(`${req.method} ${req.path} - ${duration}ms`);
    }
  });
  next();
});
```

## 🔒 Security

1. **Validate input** - Constraints on circuit parameters
2. **Rate limit** - Limit optimization requests per user
3. **Timeout** - Prevent long-running optimizations
4. **CORS** - Only allow requests from backend

```javascript
// backend/middleware/rateLimit.js
const optimizationLimiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  max: 10, // 10 requests per minute
  keyGenerator: (req) => req.user.userId,
  message: 'Too many optimization requests, please try again later',
});

router.post('/optimize', optimizationLimiter, ...);
```

## 🚀 Production

### Docker Compose

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      AI_SERVICE_URL: http://ai-service:8000
    depends_on:
      - ai-service

  ai-service:
    build: ./ai-service
    ports:
      - "8000:8000"
    environment:
      ENVIRONMENT: production
```

### Kubernetes

```yaml
apiVersion: v1
kind: Service
metadata:
  name: ai-service
spec:
  selector:
    app: ai-service
  ports:
    - port: 8000
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-service
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: ai-service
        image: siliquesta-ai:latest
        ports:
        - containerPort: 8000
```

## 📞 Support

- AI Service not responding? Check it's running on port 8000
- Timeout errors? Increase `AI_SERVICE_TIMEOUT`
- CORS errors? Ensure backend URL is in AI service CORS_ORIGINS

That's it! Your full stack is now integrated. 🎉
