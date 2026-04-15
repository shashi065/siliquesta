# Pricing System - Integration Examples

Shows how to integrate pricing/feature gating with existing optimization endpoints.

## Example 1: Protect GPU Acceleration Feature

```javascript
// routes/optimizationRoutes.js
import { featureGate } from '../middleware/featureGate.js';
import { incrementUsage } from '../middleware/featureGate.js';
import optimizationController from '../controllers/optimizationController.js';

router.post(
  '/optimize-with-gpu',
  authenticate,
  featureGate('gpu_acceleration'),  // ← Blocks free/pro users
  optimizationController.optimizeWithGPU
);

// controllers/optimizationController.js
export async function optimizeWithGPU(req, res, next) {
  try {
    const userId = req.user.userId;
    
    // Feature access already verified by middleware
    // Run GPU optimization
    const result = await gpuOptimizer.optimize(req.body);
    
    // Track usage
    await incrementUsage(userId, 'monthly_runs', 1);
    
    res.json(result);
  } catch (error) {
    next(error);
  }
}
```

## Example 2: Check Usage Limits

```javascript
// controllers/simulationController.js
import { FeatureGate, Limits } from '../utils/featureGating.js';
import { prisma } from '../config/database.js';

export async function createSimulation(req, res, next) {
  try {
    const userId = req.user.userId;
    
    // Get user subscription
    const subscription = await prisma.subscription.findUnique({
      where: { userId }
    });
    
    const userPlan = subscription?.plan || 'free';
    const currentUsage = subscription?.usageCount || 0;
    
    // Check if user is at limit
    if (FeatureGate.isLimitReached(userPlan, Limits.MONTHLY_RUNS, currentUsage)) {
      return res.status(429).json({
        message: 'Monthly run limit reached',
        plan: userPlan,
        used: currentUsage,
        limit: FeatureGate.getLimit(userPlan, Limits.MONTHLY_RUNS),
        upgradeUrl: '/subscriptions/plans'
      });
    }
    
    // Create simulation (allowed)
    const simulation = await createSimulation(req.body);
    
    // Increment usage
    await prisma.subscription.update({
      where: { userId },
      data: { usageCount: { increment: 1 } }
    });
    
    res.status(201).json(simulation);
  } catch (error) {
    next(error);
  }
}
```

## Example 3: Feature Availability in Response

```javascript
// controllers/projectController.js
import { FeatureGate, Features } from '../utils/featureGating.js';

export async function getProjectDetails(req, res, next) {
  try {
    const userId = req.user.userId;
    const projectId = req.params.id;
    
    // Get project
    const project = await prisma.project.findUnique({
      where: { id: projectId }
    });
    
    // Get user plan
    const subscription = await prisma.subscription.findUnique({
      where: { userId }
    });
    const userPlan = subscription?.plan || 'free';
    
    // Include feature availability in response
    res.json({
      ...project,
      features: {
        advanced_optimization: FeatureGate.hasAccess(userPlan, Features.ADVANCED_OPTIMIZATION),
        gpu_acceleration: FeatureGate.hasAccess(userPlan, Features.GPU_ACCELERATION),
        ai_insights: FeatureGate.hasAccess(userPlan, Features.AI_INSIGHTS),
        api_access: FeatureGate.hasAccess(userPlan, Features.API_ACCESS),
      },
      subscription: {
        plan: userPlan,
        limits: FeatureGate.getAvailableLimits(userPlan),
      }
    });
  } catch (error) {
    next(error);
  }
}
```

## Example 4: Require Specific Plan

```javascript
// routes/mlRoutes.js
import { requirePlan } from '../middleware/featureGate.js';

// Only Ultra users can train models
router.post(
  '/train-model',
  authenticate,
  requirePlan('ultra'),  // ← Requires Ultra plan
  mlController.trainModel
);

// Pro+ can use API
router.post(
  '/api/webhook',
  authenticate,
  requirePlan('pro'),  // ← Requires Pro or Ultra
  apiController.configureWebhook
);
```

## Example 5: WebSocket Optimization with Feature Gating

```javascript
// wsServer.js
import { FeatureGate, Limits } from './utils/featureGating.js';
import { prisma } from './config/database.js';

server.on('connection', async (ws, req) => {
  // Get user subscription
  const subscription = await prisma.subscription.findUnique({
    where: { userId: req.user.userId }
  });
  
  const userPlan = subscription?.plan || 'free';
  
  // Check usage limit
  if (FeatureGate.isLimitReached(
    userPlan,
    Limits.MONTHLY_RUNS,
    subscription.usageCount
  )) {
    ws.send(JSON.stringify({
      type: 'error',
      message: 'Monthly run limit reached. Upgrade to continue.',
      plan: userPlan,
      usage: {
        used: subscription.usageCount,
        limit: FeatureGate.getLimit(userPlan, Limits.MONTHLY_RUNS)
      }
    }));
    ws.close(1008, 'Usage limit exceeded');
    return;
  }
  
  // Check concurrent optimization limit
  const concurrentCount = activeOptimizations.get(req.user.userId)?.length || 0;
  const maxConcurrent = FeatureGate.getLimit(
    userPlan,
    Limits.CONCURRENT_OPTIMIZATIONS
  );
  
  if (concurrentCount >= maxConcurrent) {
    ws.send(JSON.stringify({
      type: 'error',
      message: `Cannot start more than ${maxConcurrent} concurrent optimizations`
    }));
    ws.close(1008, 'Concurrent limit exceeded');
    return;
  }
  
  // Proceed with optimization
  // Track it
  activeOptimizations.add(req.user.userId, optimizationId);
  
  ws.on('message', async (msg) => {
    const message = JSON.parse(msg);
    
    // Check feature access for GPU
    if (message.useGPU && !FeatureGate.hasAccess(userPlan, 'gpu_acceleration')) {
      ws.send(JSON.stringify({
        type: 'feature_required',
        feature: 'gpu_acceleration',
        message: 'GPU acceleration requires Ultra plan',
        requiredPlan: 'ultra'
      }));
      return;
    }
    
    // Run optimization
    const result = await runOptimization(message);
    
    // Increment usage on success
    if (result.success) {
      await prisma.subscription.update({
        where: { userId: req.user.userId },
        data: { usageCount: { increment: 1 } }
      });
    }
    
    ws.send(JSON.stringify(result));
  });
});
```

## Example 6: Return Upgrade Suggestions

```javascript
// middleware/suggestUpgrade.js
import { FeatureGate } from '../utils/featureGating.js';
import { prisma } from '../config/database.js';

export async function suggestUpgrade(req, res, next) {
  // Add suggested features if user is on limited plan
  if (req.user?.userId) {
    const subscription = await prisma.subscription.findUnique({
      where: { userId: req.user.userId }
    });
    
    const plan = subscription?.plan || 'free';
    
    // Send upgrade suggestion header
    if (plan === 'free') {
      res.setHeader('X-Upgrade-Suggestion', 'pro');
      res.setHeader('X-Upgrade-Message', 'Upgrade to Pro for unlimited runs and AI insights');
    }
    
    if (plan === 'pro') {
      res.setHeader('X-Upgrade-Suggestion', 'ultra');
      res.setHeader('X-Upgrade-Message', 'Upgrade to Ultra for GPU acceleration and ML training');
    }
  }
  
  next();
}

// Use in routes:
router.get('/expensive', suggestUpgrade, controller);
```

## Example 7: Show Usage in Status Endpoint

```javascript
// GET /api/v1/status
app.get('/api/v1/status', authenticate, async (req, res) => {
  const subscription = await prisma.subscription.findUnique({
    where: { userId: req.user.userId }
  });
  
  const plan = subscription?.plan || 'free';
  const limits = FeatureGate.getAvailableLimits(plan);
  const used = subscription?.usageCount || 0;
  
  res.json({
    user: req.user.email,
    subscription: {
      plan,
      features: FeatureGate.getAvailableFeatures(plan)
    },
    usage: {
      monthly_runs: {
        used,
        limit: limits.monthly_runs,
        remaining: Math.max(0, limits.monthly_runs - used),
        percentage: limits.monthly_runs === Number.MAX_SAFE_INTEGER 
          ? 0 
          : (used / limits.monthly_runs) * 100,
        unlimited: limits.monthly_runs === Number.MAX_SAFE_INTEGER
      },
      concurrent_optimizations: {
        limit: limits.concurrent_optimizations,
        active: activeOptimizations.count(req.user.userId)
      }
    },
    upgradeUrl: plan === 'free' ? '/subscriptions/checkout-session' : null
  });
});
```

## Example 8: Middleware Stack Example

```javascript
// Complete route with nested feature gates
router.post(
  '/optimize',
  authenticate,                    // 1. User must be logged in
  checkPaymentStatus,              // 2. Payment must be current
  featureGate('advanced_optimization'),  // 3. Feature must be available
  async (req, res, next) => {
    try {
      const userId = req.user.userId;
      const userPlan = req.userPlan;      // Set by featureGate middleware
      
      // Feature is verified, now execute
      const result = await optimize(req.body, { useAdvanced: true });
      
      // Track usage
      await incrementUsage(userId, 'monthly_runs', 1);
      
      // Include subscription info in response
      const subscription = await prisma.subscription.findUnique({
        where: { userId }
      });
      
      res.json({
        result,
        usage: {
          used: subscription.usageCount + 1,
          remaining: FeatureGate.getRemaining(
            userPlan,
            'monthly_runs',
            subscription.usageCount + 1
          )
        }
      });
    } catch (error) {
      next(error);
    }
  }
);
```

## Example 9: Error Handling for Feature Denials

```javascript
// In existing error handler, add special handling
app.use((err, req, res, next) => {
  if (err.statusCode === 403 && err.feature) {
    // Feature not available
    return res.status(403).json({
      error: 'Feature Unavailable',
      message: err.message,
      feature: err.feature,
      requiredPlan: err.requiredPlan,
      yourPlan: req.userPlan,
      action: 'UPGRADE_REQUIRED',
      upgradeUrl: `/api/v1/subscriptions/checkout-session`
    });
  }
  
  if (err.statusCode === 429) {
    // Usage limit hit
    return res.status(429).json({
      error: 'Usage Limit Exceeded',
      message: err.message,
      limit: err.limit,
      plan: err.plan,
      action: 'UPGRADE_REQUIRED',
      upgradeUrl: `/api/v1/subscriptions/checkout-session`
    });
  }
  
  // Default error handling...
  next(err);
});
```

## Example 10: Frontend Integration

```javascript
// Frontend code showing how to use the API

// 1. Get current subscription
async function getCurrentPlan() {
  const response = await fetch('/api/v1/subscriptions/current', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
}

// 2. Check feature availability
async function canUseGPU() {
  const response = await fetch('/api/v1/subscriptions/features/gpu_acceleration', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const { available } = await response.json();
  return available;
}

// 3. Show upgrade prompt
async function showUpgradePrompt() {
  const { requiredPlan } = await fetch('/api/v1/subscriptions/features/gpu_acceleration')
    .then(r => r.json());
  
  alert(`This feature requires ${requiredPlan} plan. Upgrade now?`);
}

// 4. Start checkout
async function startCheckout(planId) {
  const response = await fetch('/api/v1/subscriptions/checkout-session', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      planId,
      successUrl: `${window.location.origin}/billing/success`,
      cancelUrl: `${window.location.origin}/billing/cancel`
    })
  });
  const { url } = await response.json();
  window.location.href = url;  // Redirect to Stripe Checkout
}

// 5. Show usage in UI
async function showUsageStats() {
  const response = await fetch('/api/v1/subscriptions/usage-report', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const { usageReports } = await response.json();
  
  const { used, limit, remaining } = usageReports.monthlyRuns;
  document.getElementById('usage-bar').style.width = `${(used / limit) * 100}%`;
  document.getElementById('usage-text').textContent = `${remaining} runs remaining`;
}
```

---

## Integration Testing Checklist

- [ ] Free tier limited to 10 runs
- [ ] Pro tier allows unlimited runs
- [ ] Pro tier blocks GPU features
- [ ] Ultra tier has all features
- [ ] Usage increments correctly
- [ ] Reaching limit blocks operation
- [ ] Stripe checkout creates session
- [ ] Webhook updates subscription
- [ ] Plan downgrade on cancellation
- [ ] Payment failure marked in DB
- [ ] Feature gates work in middleware
- [ ] Feature gates work in routes
- [ ] Error responses have upgrade URL

---

These examples show how to integrate the pricing system with existing optimization, simulation, and ML endpoints throughout SILIQUESTA.
