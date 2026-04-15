# Pricing System Quick Start

**Ready to integrate**: Follow this quick 5-minute setup

## Step 1: Install Dependencies

```bash
cd services/api
npm install
```

This adds `stripe@^13.5.0` to your project.

## Step 2: Update Environment

Create or update `.env` in `services/api/`:

```env
# Get these from Stripe Dashboard → Developers → API Keys
STRIPE_SECRET_KEY=sk_live_52JfC2...
STRIPE_PUBLISHABLE_KEY=pk_live_52JfC2...

# Get these from Stripe Dashboard → Products
STRIPE_PRO_PRICE_ID=price_1Nt5j...
STRIPE_ULTRA_PRICE_ID=price_1Nt5k...

# Get this from Dashboard → Developers → Webhooks
STRIPE_WEBHOOK_SECRET=whsec_test_52JfC2...
```

**No Stripe account?** Create free at [stripe.com](https://stripe.com)

## Step 3: Database Setup

```bash
# Apply schema changes (adds subscription fields to DB)
npx prisma db push

# Generate Prisma client
npx prisma generate
```

## Step 4: Test It

```bash
# Start server
npm start

# Check API is running
curl http://localhost:10000/api/v1/health

# List available plans
curl http://localhost:10000/api/v1/subscriptions/plans

# Response shows Free, Pro, Ultra plans with features
```

## Step 5: Get API Token & Test

```bash
# 1. Sign up / login to get token
TOKEN=$(curl -X POST http://localhost:10000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com", "password":"Test123!"}' \
  | jq -r '.token')

# 2. Check current subscription
curl http://localhost:10000/api/v1/subscriptions/current \
  -H "Authorization: Bearer $TOKEN"

# Response: Currently on "free" plan

# 3. Create checkout session to upgrade
curl -X POST http://localhost:10000/api/v1/subscriptions/checkout-session \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "planId": "pro",
    "successUrl": "https://app.siliquesta.com/success",
    "cancelUrl": "https://app.siliquesta.com/cancel"
  }'

# Response includes Stripe Checkout URL
```

## Available Plans

### Free (Always)
- 10 monthly runs
- 1 project
- Basic optimization

### Pro ($29/month)
- Unlimited runs
- 50 projects
- Advanced optimization + AI insights
- Priority support

### Ultra ($99/month)
- Everything unlimited
- GPU acceleration
- ML training
- Dedicated support

## Key Features

✅ **Feature Gating** - Protect endpoints by plan
```javascript
// In routes
router.post('/optimize', featureGate('gpu_acceleration'), controller);

// In code
FeatureGate.assertAccess(userPlan, 'gpu_acceleration');
```

✅ **Usage Limits** - Track monthly runs
```javascript
FeatureGate.isLimitReached(plan, 'monthly_runs', currentCount);
```

✅ **Check Access** - Before expensive operations
```javascript
const info = FeatureGate.getFeatureInfo(plan, 'feature_name');
// Returns: { available: true/false, requiredPlan, message }
```

## API Endpoints

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| GET | `/subscriptions/plans` | ❌ | List available plans |
| GET | `/subscriptions/current` | ✅ | Get user's current plan |
| POST | `/subscriptions/checkout-session` | ✅ | Create Stripe checkout |
| GET | `/subscriptions/portal` | ✅ | Manage subscription |
| POST | `/subscriptions/cancel` | ✅ | Downgrade to free |
| GET | `/subscriptions/features/:name` | ❌ | Check feature access |
| GET | `/subscriptions/usage-report` | ✅ | Monthly usage stats |
| POST | `/subscriptions/webhook` | ❌ | Stripe webhook |

## Feature Gate Usage

### Check Feature Access

```javascript
import { FeatureGate } from './utils/featureGating.js';

// Option 1: Soft check (returns boolean)
if (FeatureGate.hasAccess(userPlan, 'gpu_acceleration')) {
  // Use GPU
}

// Option 2: Hard check (throws on denied)
FeatureGate.assertAccess(userPlan, 'gpu_acceleration');
// ✓ User has access
// ✗ Throws error if denied
```

### Check Usage Limits

```javascript
// Is user at limit?
const atLimit = FeatureGate.isLimitReached(
  userPlan,
  'monthly_runs',
  userCurrentCount
);

if (atLimit) {
  return res.status(429).json({ message: 'Monthly limit reached' });
}

// How much remaining?
const remaining = FeatureGate.getRemaining(
  userPlan,
  'monthly_runs',
  userCurrentCount
);
console.log(`${remaining} runs remaining this month`);
```

### Get Feature Info

```javascript
const info = FeatureGate.getFeatureInfo(userPlan, 'gpu_acceleration');
// Returns:
// {
//   feature: 'gpu_acceleration',
//   available: false,
//   plan: 'free',
//   requiredPlan: 'ultra',
//   message: 'Feature requires upgrade'
// }
```

## Middleware Usage

```javascript
import { featureGate, requirePlan } from './middleware/featureGate.js';

// Protect by feature
router.post(
  '/optimize-with-gpu',
  featureGate('gpu_acceleration'),
  controller
);
// ✓ Pro and Ultra users get through
// ✗ Free users get 403 "Feature not available"

// Require specific plan
router.post(
  '/train-model',
  requirePlan('ultra'),
  controller
);
// ✓ Only Ultra users pass
// ✗ Others get 403 "Requires Ultra plan"

// Check payment status
router.get(
  '/data',
  checkPaymentStatus,
  controller
);
// ✗ If payment past due or failed: 402 error
// ✓ Otherwise: continues
```

## Testing Stripe Locally

Use Stripe test keys and CLI:

```bash
# 1. Get test keys from Stripe Dashboard
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# 2. Install Stripe CLI
# macOS: brew install stripe/stripe-cli/stripe
# Linux/Windows: See https://stripe.com/docs/stripe-cli

# 3. Forward webhooks locally
stripe listen --forward-to localhost:10000/api/v1/subscriptions/webhook

# 4. Trigger test events
stripe trigger customer.subscription.created
stripe trigger customer.subscription.updated

# 5. In another terminal, test checkout
TOKEN=$(curl ... | jq -r '.token')
curl -X POST http://localhost:10000/api/v1/subscriptions/checkout-session \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"planId":"pro", "successUrl":"...", "cancelUrl":"..."}'
```

Test card numbers:
- **Success**: 4242 4242 4242 4242
- **Decline**: 4000 0000 0000 0002
- **3D Secure**: 4000 0025 0000 3155

## Common Patterns

### Protect Expensive Endpoint

```javascript
router.post(
  '/expensive-operation',
  authenticate,
  featureGate('gpu_acceleration'),
  async (req, res, next) => {
    try {
      // Feature access already verified by middleware
      await expensiveOperation();
      res.json({ success: true });
    } catch (error) {
      next(error);
    }
  }
);
```

### Check Limits Before Operation

```javascript
router.post('/optimize', authenticate, async (req, res, next) => {
  try {
    const { userPlan, userId } = req.user;
    const subscription = await getSubscription(userId);

    // Check monthly limit
    FeatureGate.assertAccess(userPlan, 'unlimited_runs');

    // Or check usage count
    if (FeatureGate.isLimitReached(userPlan, 'monthly_runs', subscription.usageCount)) {
      throw new Error('Monthly limit reached. Upgrade to continue.');
    }

    // Perform optimization
    const result = await optimize(req.body);

    // Increment usage
    await incrementUsage(userId);

    res.json(result);
  } catch (error) {
    next(error);
  }
});
```

### Return Plan Info With Response

```javascript
router.get('/user-info', authenticate, async (req, res, next) => {
  try {
    const subscription = await getSubscription(req.user.userId);
    const planDetails = getPlanDetails(subscription.plan);

    res.json({
      user: { ...userInfo },
      subscription: {
        plan: subscription.plan,
        features: FeatureGate.getAvailableFeatures(subscription.plan),
        limits: FeatureGate.getAvailableLimits(subscription.plan),
        usage: {
          runs: subscription.usageCount,
          remaining: FeatureGate.getRemaining(
            subscription.plan,
            'monthly_runs',
            subscription.usageCount
          ),
        },
      },
      upgradePath: planDetails.price > 0 ? planDetails : null,
    });
  } catch (error) {
    next(error);
  }
});
```

## Deployment Notes

- Stripe requires HTTPS in production
- Set webhook URL in Stripe Dashboard to your production endpoint
- Use production Stripe keys (`sk_live_...`, not `sk_test_...`)
- Test webhook delivery works after deployment
- Monitor webhook failures in Stripe Dashboard

## What's Next?

1. **Test checkout flow** - Create session, complete payment
2. **Set up webhooks** - Stripe Dashboard → Webhooks
3. **Build UI** - Front-end checkout/pricing pages
4. **Add analytics** - Track feature adoption
5. **Monitor payments** - Stripe Dashboard alerts

## You're Ready! 🚀

Your pricing system is now live and ready to accept payments.

```bash
npm start
```

Check the full guide: [PRICING_SYSTEM_GUIDE.md](./PRICING_SYSTEM_GUIDE.md)
