# SILIQUESTA Pricing System Implementation Guide

**Status**: ✅ COMPLETE & INTEGRATED  
**Last Updated**: April 14, 2026  
**Version**: 1.0.0

## Table of Contents

1. [Overview](#overview)
2. [Plans & Features](#plans--features)
3. [Architecture](#architecture)
4. [Setup Instructions](#setup-instructions)
5. [API Reference](#api-reference)
6. [Feature Gating](#feature-gating)
7. [Stripe Integration](#stripe-integration)
8. [Usage Examples](#usage-examples)
9. [Troubleshooting](#troubleshooting)

---

## Overview

### What's Included

The pricing system provides:

- **Three Subscription Plans**: Free, Pro, Ultra
- **Stripe Payment Processing**: Complete payment integration
- **Feature Gating**: Permission-based feature access
- **Usage Tracking**: Monthly run limits and usage reporting
- **Subscription Management**: Upgrade, downgrade, cancel
- **Webhook Handling**: Real-time subscription status updates
- **Customer Portal**: Self-service management interface

### Key Components

```
src/
├── models/pricing.js              # Plan definitions & utilities
├── services/stripeService.js      # Stripe API integration
├── controllers/subscriptionController.js  # Endpoint handlers
├── routes/subscriptionRoutes.js   # API routes
├── utils/featureGating.js        # Feature access control
├── middleware/featureGate.js     # Express middleware
├── middleware/rawBody.js         # Webhook signature verification
└── prisma/schema.prisma          # Database schema (updated)
```

---

## Plans & Features

### Free Plan

- **Price**: $0/month
- **Monthly Runs**: 10
- **Max Projects**: 1
- **Max Constraints**: 5
- **Max Objectives**: 2
- **GPU Acceleration**: ❌ No
- **AI Insights**: ❌ No
- **Export Formats**: JSON
- **Support**: Community
- **Concurrent Optimizations**: 1

**Features:**
- Basic optimization
- Single project
- Community support

---

### Pro Plan

- **Price**: $29/month
- **Monthly Runs**: Unlimited
- **Max Projects**: 50
- **Max Constraints**: 50
- **Max Objectives**: 10
- **GPU Acceleration**: ❌ No
- **AI Insights**: ✅ Yes
- **Export Formats**: JSON, CSV, XML
- **Support**: Priority email
- **Concurrent Optimizations**: 5

**Features:**
- Unlimited optimization runs
- Multiple projects
- Advanced optimization algorithms
- AI-powered insights
- Priority support
- Multiple export formats
- API access
- Webhook support

---

### Ultra Plan

- **Price**: $99/month
- **Monthly Runs**: Unlimited
- **Max Projects**: Unlimited
- **Max Constraints**: Unlimited
- **Max Objectives**: Unlimited
- **GPU Acceleration**: ✅ Yes
- **AI Insights**: ✅ Yes
- **Export Formats**: JSON, CSV, XML, SQL, Parquet
- **Support**: Dedicated
- **Concurrent Optimizations**: 50

**Features:**
- Unlimited everything
- GPU acceleration for faster optimization
- Advanced AI insights
- ML model training capabilities
- Custom algorithms
- Dedicated support
- All export formats
- Full API access
- Advanced webhooks

---

## Architecture

### Database Schema

The `Subscription` model tracks:

```prisma
model Subscription {
  // Identity
  id                    String   @id @default(cuid())
  userId                String   @unique
  user                  User     @relation(...)
  
  // Plan & Pricing
  plan                  String   @default("free")
  status                String   @default("active")
  
  // Usage Tracking
  usageCount            Int      @default(0)
  usageLimit            Int      @default(10)
  
  // Stripe Integration
  stripeCustomerId      String?
  stripeSubscriptionId  String?
  
  // Billing Period
  currentPeriodStart    DateTime?
  currentPeriodEnd      DateTime?
  
  // Lifecycle
  canceledAt            DateTime?
  lastPaymentDate       DateTime?
  paymentStatus         String?
  failureReason         String?
  
  // Metadata
  features              Json?
  createdAt             DateTime @default(now())
  updatedAt             DateTime @updatedAt
}
```

### Feature Matrix

| Feature | Free | Pro | Ultra |
|---------|:----:|:---:|:-----:|
| Basic Optimization | ✅ | ✅ | ✅ |
| Advanced Optimization | ❌ | ✅ | ✅ |
| GPU Acceleration | ❌ | ❌ | ✅ |
| AI Insights | ❌ | ✅ | ✅ |
| ML Training | ❌ | ❌ | ✅ |
| Priority Support | ❌ | ✅ | ✅ |
| Dedicated Support | ❌ | ❌ | ✅ |
| API Access | ❌ | ✅ | ✅ |
| Webhook Support | ❌ | ✅ | ✅ |
| Multiple Projects | ❌ | ✅ | ✅ |

---

## Setup Instructions

### 1. Environment Configuration

Create `.env` file in `services/api/`:

```env
# Stripe Configuration
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Stripe Product IDs
STRIPE_PRO_PRODUCT_ID=prod_...
STRIPE_PRO_PRICE_ID=price_...
STRIPE_ULTRA_PRODUCT_ID=prod_...
STRIPE_ULTRA_PRICE_ID=price_...

# Database (existing)
DATABASE_URL=postgresql://user:password@localhost:5432/siliquesta

# Optional: Sentry DSN for error tracking
SENTRY_DSN=https://...
```

### 2. Migrate Database

```bash
cd services/api

# Generate Prisma client
npx prisma generate

# Apply migrations
npx prisma db push

# (Optional) Seed test data
npx prisma db seed
```

### 3. Install Dependencies

```bash
npm install
```

This installs the new `stripe` package (v13.5.0).

### 4. Stripe Setup

#### Create Stripe Account

1. Go to [stripe.com](https://stripe.com)
2. Create account
3. Go to Developers > API Keys
4. Copy Secret Key and Publishable Key

#### Create Products & Prices

1. In Stripe Dashboard, go to Products
2. Create product "Pro Plan"
   - Name: "Pro"
   - Price: $29/month
   - Recurring: Monthly
   - Get Price ID

3. Create product "Ultra Plan"
   - Name: "Ultra"
   - Price: $99/month
   - Recurring: Monthly
   - Get Price ID

#### Configure Webhooks

1. Go to Developers > Webhooks
2. Add endpoint: `https://your-domain/api/v1/subscriptions/webhook`
3. Select events:
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `charge.failed`
4. Copy Webhook Secret

#### Add to .env

```env
STRIPE_PRO_PRICE_ID=price_...  (from Pro plan)
STRIPE_ULTRA_PRICE_ID=price_...  (from Ultra plan)
STRIPE_WEBHOOK_SECRET=whsec_...  (from Webhook)
```

### 5. Start Server

```bash
npm start
```

Verify endpoints:

```bash
# Check API is running
curl http://localhost:10000/api/v1/health

# List plans
curl http://localhost:10000/api/v1/subscriptions/plans
```

---

## API Reference

### Authentication

All endpoints except `/plans` require:

```
Authorization: Bearer {jwt_token}
```

### Endpoints

#### GET `/subscriptions/plans`

List all available plans.

**Response:**
```json
{
  "plans": [
    {
      "name": "Free",
      "price": 0,
      "billingCycle": null,
      "features": [...],
      "limits": {...}
    },
    {
      "name": "Pro",
      "price": 29,
      "billingCycle": "month",
      "features": [...],
      "limits": {...}
    },
    {
      "name": "Ultra",
      "price": 99,
      "billingCycle": "month",
      "features": [...],
      "limits": {...}
    }
  ]
}
```

---

#### GET `/subscriptions/current`

Get current user's subscription and usage.

**Authorization**: ✅ Required  
**Response:**
```json
{
  "plan": "pro",
  "status": "active",
  "features": ["unlimited_runs", "ai_insights", ...],
  "limits": {
    "monthly_runs": 999999999,
    "max_projects": 50,
    "max_constraints": 50,
    "concurrent_optimizations": 5
  },
  "usageCount": 25,
  "usageLimit": 999999999,
  "usageRemaining": 999999974,
  "currentPeriodStart": "2026-04-01T00:00:00Z",
  "currentPeriodEnd": "2026-05-01T00:00:00Z",
  "planDetails": {...}
}
```

---

#### POST `/subscriptions/checkout-session`

Create a Stripe checkout session for upgrading a plan.

**Authorization**: ✅ Required  
**Body:**
```json
{
  "planId": "pro",
  "successUrl": "https://app.siliquesta.com/billing/success",
  "cancelUrl": "https://app.siliquesta.com/billing/cancel"
}
```

**Response:**
```json
{
  "sessionId": "cs_live_...",
  "url": "https://checkout.stripe.com/..."
}
```

**Redirect user to `url` for checkout.**

---

#### GET `/subscriptions/portal`

Get Stripe Customer Portal session URL for users to manage their subscription.

**Authorization**: ✅ Required  
**Query Parameters:**
- `returnUrl` (required): Where to return after managing subscription

**Response:**
```json
{
  "url": "https://billing.stripe.com/session/..."
}
```

---

#### POST `/subscriptions/cancel`

Cancel user's active subscription.

**Authorization**: ✅ Required  
**Response:**
```json
{
  "message": "Subscription canceled. Downgrade to free plan scheduled.",
  "plan": "free"
}
```

---

#### GET `/subscriptions/features/:featureName`

Check if user has access to a specific feature.

**Note**: This endpoint does NOT require authentication  
**Response:**
```json
{
  "feature": "gpu_acceleration",
  "available": false,
  "plan": "free",
  "requiredPlan": "ultra",
  "message": "Feature requires an upgrade. Current plan: free"
}
```

---

#### GET `/subscriptions/usage-report`

Get detailed usage report for the current month.

**Authorization**: ✅ Required  
**Response:**
```json
{
  "plan": "pro",
  "currentMonth": "2026-04",
  "usageReports": {
    "monthlyRuns": {
      "used": 25,
      "limit": 999999999,
      "remaining": 999999974,
      "percentage": 0.0025,
      "unlimited": true
    }
  },
  "totalRuns": 25,
  "availableFeatures": [...],
  "limits": {...},
  "nextReset": "2026-05-01T00:00:00Z"
}
```

---

#### POST `/subscriptions/webhook`

Stripe webhook receiver for subscription events.

**Headers:**
- `stripe-signature`: Stripe signature for verification

**Note**: This endpoint expects raw body, not JSON

---

### Error Responses

**Feature Not Available** (403):
```json
{
  "statusCode": 403,
  "error": "Feature not available",
  "message": "Feature \"gpu_acceleration\" is not available on your free plan. Upgrade to Pro or Ultra.",
  "feature": "gpu_acceleration",
  "plan": "free",
  "requiredPlan": "ultra"
}
```

**Usage Limit Exceeded** (429):
```json
{
  "statusCode": 429,
  "error": "Limit exceeded",
  "message": "monthly_runs limit reached for free plan.",
  "limit": "monthly_runs",
  "plan": "free"
}
```

**Stripe Not Configured** (503):
```json
{
  "statusCode": 503,
  "error": "Service unavailable",
  "message": "Stripe payment is not configured on this server"
}
```

---

## Feature Gating

### Checking Feature Access in Code

```javascript
import { FeatureGate, Features } from './utils/featureGating.js';

// Check if user has access
if (FeatureGate.hasAccess(userPlan, Features.GPU_ACCELERATION)) {
  // Use GPU acceleration
}

// Get required plan
const required = FeatureGate.getRequiredPlan(Features.GPU_ACCELERATION);
console.log(`Upgrade to ${required} to use GPU acceleration`);

// Get all available features
const features = FeatureGate.getAvailableFeatures(userPlan);

// Check usage limit
const isLimitReached = FeatureGate.isLimitReached(
  userPlan,
  'monthly_runs',
  currentUsageCount
);
```

### Using Feature Gate Middleware

```javascript
import { featureGate, requirePlan } from './middleware/featureGate.js';

// Protect route with feature
router.post('/optimize', featureGate('gpu_acceleration'), controller);

// Require minimum plan
router.post('/train-model', requirePlan('ultra'), controller);

// Check payment status
router.get('/data', checkPaymentStatus, controller);
```

### In Controllers

```javascript
export async function expensiveOperation(req, res, next) {
  try {
    // Feature gating middleware already checked access
    const userPlan = req.userPlan;
    
    // Use features based on plan
    if (FeatureGate.hasAccess(userPlan, 'gpu_acceleration')) {
      // Use GPU
    }
    
    // Increment usage
    if (req.limitName) {
      await incrementUsage(req.user.userId, req.limitName, req.incrementUsage);
    }
    
    res.json({ result: 'success' });
  } catch (error) {
    next(error);
  }
}
```

---

## Stripe Integration

### Webhook Events Handled

| Event | Action |
|-------|--------|
| `customer.subscription.updated` | Update plan, status, billing period |
| `customer.subscription.deleted` | Downgrade to free |
| `invoice.payment_succeeded` | Record payment |
| `charge.failed` | Mark as failed |

### Payment Flow

```
User clicks "Upgrade" → Create Checkout Session
        ↓
Stripe Checkout Page
        ↓
User completes payment approval
        ↓
Stripe redirects to successUrl
        ↓
Stripe sends webhook to /subscriptions/webhook
        ↓
Backend updates subscription
        ↓
User now has new plan
```

### Webhook Verification

The webhook receiver verifies Stripe's signature:

```javascript
const event = stripeService.verifyWebhookSignature(req.body, signature);
```

If verification fails, request is rejected (400).

---

## Usage Examples

### JavaScript/React Frontend

```javascript
// Fetch available plans
const response = await fetch('/api/v1/subscriptions/plans');
const { plans } = await response.json();

// Get current subscription
const current = await fetch('/api/v1/subscriptions/current', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const subscription = await current.json();

// Create checkout session
const checkout = await fetch('/api/v1/subscriptions/checkout-session', {
  method: 'POST',
  headers: { 
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    planId: 'pro',
    successUrl: 'https://app.siliquesta.com/success',
    cancelUrl: 'https://app.siliquesta.com/cancel'
  })
});
const { url } = await checkout.json();

// Redirect to Stripe Checkout
window.location.href = url;

// Check feature access
const feature = await fetch('/api/v1/subscriptions/features/gpu_acceleration', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const { available } = await feature.json();

if (!available) {
  console.log('Upgrade to use this feature');
}
```

### cURL Examples

```bash
# List plans
curl https://api.siliquesta.com/api/v1/subscriptions/plans

# Get current subscription
curl https://api.siliquesta.com/api/v1/subscriptions/current \
  -H "Authorization: Bearer $TOKEN"

# Create checkout
curl -X POST https://api.siliquesta.com/api/v1/subscriptions/checkout-session \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "planId": "pro",
    "successUrl": "https://app.siliquesta.com/success",
    "cancelUrl": "https://app.siliquesta.com/cancel"
  }'

# Get usage report
curl https://api.siliquesta.com/api/v1/subscriptions/usage-report \
  -H "Authorization: Bearer $TOKEN"

# Check feature access
curl https://api.siliquesta.com/api/v1/subscriptions/features/gpu_acceleration \
  -H "Authorization: Bearer $TOKEN"
```

---

## Troubleshooting

### Stripe API Connection Failed

**Problem**: "Stripe is not configured"

**Solution**:
1. Verify `STRIPE_SECRET_KEY` is set in `.env`
2. Check Stripe API keys are valid
3. Ensure keys are from live mode (not test mode)

---

### Webhook Signature Verification Failed

**Problem**: "Webhook signature verification failed"

**Solution**:
1. Verify `STRIPE_WEBHOOK_SECRET` from Stripe Dashboard
2. Ensure webhook endpoint is correct in Stripe Dashboard
3. Check req.rawBody is properly captured
4. Verify Stripe is using correct secret

---

### Payment Succeeded but Plan Not Updated

**Problem**: User upgraded but subscription not updated

**Solution**:
1. Check webhook event received (check Stripe Dashboard > Webhooks)
2. Verify webhook secret matches
3. Check database for errors in subscription update
4. Manually trigger: `POST /subscriptions/webhook` with test event

---

### User Still Has Free Plan Limits After Upgrade

**Problem**: User upgraded but still hitting free plan limits

**Solution**:
1. Refresh `/subscriptions/current` endpoint to see live status
2. Check webhook updates subscription immediately
3. Clear browser cache/cookies if frontend caching
4. Verify `plan` field changed in database: 
   ```sql
   SELECT plan, status FROM subscriptions WHERE user_id = 'user-id';
   ```

---

### Feature Gating Middleware Returns 403

**Problem**: Authenticated user getting "Feature not available"

**Solution**:
1. Check user's actual plan: `GET /subscriptions/current`
2. Verify feature name matches exactly
3. Check pricing.js for feature definitions
4. Validate database subscription record

---

## Testing

### Local Stripe Testing

Use Stripe's test keys in development:

```env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
```

Test card numbers:
- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`
- Requires authentication: `4000 0025 0000 3155`

---

### Local Webhook Testing

Use Stripe CLI for local webhook testing:

```bash
# Install Stripe CLI
# https://stripe.com/docs/stripe-cli

# Forward webhooks to local server
stripe listen --forward-to localhost:10000/api/v1/subscriptions/webhook

# Get webhook signing secret
stripe listen

# Trigger test event
stripe trigger customer.subscription.created
```

---

## Deployment Checklist

- [ ] Set Stripe Secret Key in production environment
- [ ] Set Stripe Publishable Key for frontend
- [ ] Configure all Stripe Price IDs
- [ ] Set Stripe Webhook Secret
- [ ] Add webhook endpoint in Stripe Dashboard
- [ ] Run database migrations: `npx prisma db push`
- [ ] Test checkout flow end-to-end
- [ ] Verify webhook delivery in Stripe Dashboard
- [ ] Set up Stripe alerts for failed payments
- [ ] Document Stripe credentials backup
- [ ] Plan for PCI compliance review

---

## Security Considerations

### Payment Security

- Never store raw card data - Stripe handles it
- Always verify webhook signatures
- Use HTTPS only (enforced by Stripe)
- Rotate webhook secrets regularly

### Feature Access

- Feature checks happen server-side, not client-side
- Middleware enforcement ensures features cannot be bypassed
- Usage limits enforced before operations start

### Data Privacy

- Stripe data synced with permission
- Personal data minimal in database
- webhook events logged without PII

---

## Support

For issues or questions:

1. Check [Troubleshooting](#troubleshooting) section
2. Review Stripe docs: https://stripe.com/docs/api
3. Check implementation in source code
4. Enable debug logging: `DEBUG=* npm start`

---

**Generated**: April 14, 2026  
**For**: SILIQUESTA SaaS Platform  
**Status**: Production Ready
