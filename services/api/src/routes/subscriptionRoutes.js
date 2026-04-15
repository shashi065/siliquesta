/**
 * Subscription Routes
 * Routes for managing billing and subscriptions
 */

import express from 'express';
import { authenticate } from '../middleware/auth.js';
import { handleRawBody } from '../middleware/rawBody.js';
import subscriptionController from '../controllers/subscriptionController.js';

const router = express.Router();

/**
 * Public Routes (no authentication required)
 */

/**
 * GET /subscriptions/plans
 * List all available plans
 */
router.get('/plans', subscriptionController.listPlans);

/**
 * Protected Routes (authentication required)
 */

/**
 * GET /subscriptions/current
 * Get current user's subscription
 */
router.get('/current', authenticate, subscriptionController.getCurrentSubscription);

/**
 * POST /subscriptions/checkout-session
 * Create a Stripe checkout session
 * Body: { planId, successUrl, cancelUrl }
 */
router.post('/checkout-session', authenticate, subscriptionController.createCheckoutSession);

/**
 * GET /subscriptions/portal
 * Get Stripe customer portal sesion URL
 * Query: returnUrl
 */
router.get('/portal', authenticate, subscriptionController.getPortalSession);

/**
 * POST /subscriptions/cancel
 * Cancel active subscription
 */
router.post('/cancel', authenticate, subscriptionController.cancelSubscription);

/**
 * GET /subscriptions/features/:featureName
 * Check if user has access to a feature
 */
router.get('/features/:featureName', subscriptionController.checkFeatureAccess);

/**
 * GET /subscriptions/usage-report
 * Get detailed usage report
 */
router.get('/usage-report', authenticate, subscriptionController.getUsageReport);

/**
 * POST /subscriptions/webhook
 * Stripe webhook endpoint (must use raw body)
 * This is required for Stripe to send events to the server
 */
router.post(
  '/webhook',
  handleRawBody(),
  subscriptionController.handleWebhook
);

export default router;
