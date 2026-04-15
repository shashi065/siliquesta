/**
 * Subscription Controller
 * Handles subscription management endpoints
 */

import { prisma } from '../config/database.js';
import { getAllPlans, getPlanDetails } from '../models/pricing.js';
import * as stripeService from '../services/stripeService.js';
import { FeatureGate } from '../utils/featureGating.js';

/**
 * GET /subscriptions/plans
 * Get all available plans
 */
export async function listPlans(req, res, next) {
  try {
    const plans = getAllPlans();
    return res.status(200).json({ plans });
  } catch (error) {
    next(error);
  }
}

/**
 * GET /subscriptions/current
 * Get current subscription for logged-in user
 */
export async function getCurrentSubscription(req, res, next) {
  try {
    const userId = req.user?.userId;
    if (!userId) {
      return res.status(401).json({ message: 'Authentication required' });
    }

    let subscription = await prisma.subscription.findUnique({
      where: { userId },
    });

    // Create default free subscription if doesn't exist
    if (!subscription) {
      subscription = await prisma.subscription.create({
        data: {
          userId,
          plan: 'free',
          usageCount: 0,
          usageLimit: 10,
        },
      });
    }

    const planDetails = getPlanDetails(subscription.plan);
    const features = FeatureGate.getAvailableFeatures(subscription.plan);
    const limits = FeatureGate.getAvailableLimits(subscription.plan);

    return res.status(200).json({
      plan: subscription.plan,
      status: subscription.status || 'active',
      features,
      limits,
      usageCount: subscription.usageCount,
      usageLimit: subscription.usageLimit,
      usageRemaining: Math.max(0, subscription.usageLimit - subscription.usageCount),
      currentPeriodStart: subscription.currentPeriodStart,
      currentPeriodEnd: subscription.currentPeriodEnd,
      canceledAt: subscription.canceledAt,
      planDetails,
    });
  } catch (error) {
    next(error);
  }
}

/**
 * POST /subscriptions/checkout-session
 * Create a checkout session for plan upgrade
 */
export async function createCheckoutSession(req, res, next) {
  try {
    const userId = req.user?.userId;
    const userEmail = req.user?.email;
    const { planId, successUrl, cancelUrl } = req.body;

    if (!userId || !userEmail) {
      return res.status(401).json({ message: 'Authentication required' });
    }

    if (!planId || !['pro', 'ultra'].includes(planId)) {
      return res.status(400).json({ message: 'Valid planId required (pro or ultra)' });
    }

    if (!stripeService.isStripeConfigured()) {
      return res.status(503).json({
        message: 'Stripe payment is not configured on this server',
      });
    }

    if (!successUrl || !cancelUrl) {
      return res.status(400).json({
        message: 'successUrl and cancelUrl required in request body',
      });
    }

    const checkoutSession = await stripeService.createCheckoutSession(
      userId,
      userEmail,
      planId,
      successUrl,
      cancelUrl
    );

    return res.status(200).json({
      sessionId: checkoutSession.sessionId,
      url: checkoutSession.url,
    });
  } catch (error) {
    next(error);
  }
}

/**
 * GET /subscriptions/portal
 * Get customer portal session for managing subscription
 */
export async function getPortalSession(req, res, next) {
  try {
    const userId = req.user?.userId;
    const { returnUrl } = req.query;

    if (!userId) {
      return res.status(401).json({ message: 'Authentication required' });
    }

    if (!returnUrl) {
      return res.status(400).json({ message: 'returnUrl query parameter required' });
    }

    if (!stripeService.isStripeConfigured()) {
      return res.status(503).json({
        message: 'Stripe is not configured on this server',
      });
    }

    const portalSession = await stripeService.getPortalSession(userId, returnUrl);

    return res.status(200).json({
      url: portalSession.url,
    });
  } catch (error) {
    next(error);
  }
}

/**
 * POST /subscriptions/cancel
 * Cancel user's subscription (downgrade to free)
 */
export async function cancelSubscription(req, res, next) {
  try {
    const userId = req.user?.userId;

    if (!userId) {
      return res.status(401).json({ message: 'Authentication required' });
    }

    const subscription = await prisma.subscription.findUnique({
      where: { userId },
    });

    if (!subscription) {
      return res.status(404).json({ message: 'Subscription not found' });
    }

    if (subscription.plan === 'free') {
      return res.status(400).json({
        message: 'Cannot cancel free plan subscription',
      });
    }

    // If has Stripe subscription, cancel it through Stripe
    if (subscription.stripeSubscriptionId) {
      await stripeService.cancelSubscription(userId);
      // handleSubscriptionDeleted will be triggered by webhook
      return res.status(200).json({
        message: 'Subscription canceled. Downgrade to free plan scheduled.',
        plan: subscription.plan,
      });
    } else {
      // Manual downgrade if no Stripe subscription
      await prisma.subscription.update({
        where: { userId },
        data: {
          plan: 'free',
          status: 'canceled',
          canceledAt: new Date(),
        },
      });

      return res.status(200).json({
        message: 'Subscription canceled and downgraded to free plan',
        plan: 'free',
      });
    }
  } catch (error) {
    next(error);
  }
}

/**
 * POST /subscriptions/webhook
 * Handle Stripe webhook events
 */
export async function handleWebhook(req, res, next) {
  try {
    const signature = req.headers['stripe-signature'];

    let event;
    try {
      event = stripeService.verifyWebhookSignature(req.body, signature);
    } catch (err) {
      console.error('Webhook signature verification failed:', err.message);
      return res.status(400).json({ message: 'Webhook signature verification failed' });
    }

    // Handle events
    switch (event.type) {
      case 'customer.subscription.updated':
        await stripeService.handleSubscriptionUpdated(event.data.object);
        break;

      case 'customer.subscription.deleted':
        await stripeService.handleSubscriptionDeleted(event.data.object);
        break;

      case 'invoice.payment_succeeded':
        await stripeService.handleInvoicePaymentSucceeded(event.data.object);
        break;

      case 'charge.failed':
        await stripeService.handleChargeFailed(event.data.object);
        break;

      default:
        console.log(`Unhandled webhook event type: ${event.type}`);
    }

    return res.status(200).json({ received: true });
  } catch (error) {
    next(error);
  }
}

/**
 * GET /subscriptions/features/:featureName
 * Check if user has access to a feature
 */
export async function checkFeatureAccess(req, res, next) {
  try {
    const userId = req.user?.userId;
    const { featureName } = req.params;

    if (!featureName) {
      return res.status(400).json({ message: 'featureName required' });
    }

    let subscription = await prisma.subscription.findUnique({
      where: { userId },
    });

    // Use free plan if user not authenticated or no subscription
    const plan = subscription?.plan || 'free';

    const info = FeatureGate.getFeatureInfo(plan, featureName);

    return res.status(200).json(info);
  } catch (error) {
    next(error);
  }
}

/**
 * GET /subscriptions/usage-report
 * Get detailed usage report for user
 */
export async function getUsageReport(req, res, next) {
  try {
    const userId = req.user?.userId;

    if (!userId) {
      return res.status(401).json({ message: 'Authentication required' });
    }

    let subscription = await prisma.subscription.findUnique({
      where: { userId },
    });

    if (!subscription) {
      subscription = await prisma.subscription.create({
        data: {
          userId,
          plan: 'free',
          usageCount: 0,
          usageLimit: 10,
        },
      });
    }

    const plan = subscription.plan;
    const monthlyRunsReport = FeatureGate.getUsageReport(
      plan,
      'monthly_runs',
      subscription.usageCount
    );

    const features = FeatureGate.getAvailableFeatures(plan);
    const limits = FeatureGate.getAvailableLimits(plan);

    return res.status(200).json({
      plan,
      currentMonth: new Date().toISOString().slice(0, 7),
      usageReports: {
        monthlyRuns: monthlyRunsReport,
      },
      totalRuns: subscription.usageCount,
      availableFeatures: features,
      limits,
      lastReset: subscription.currentPeriodStart,
      nextReset: subscription.currentPeriodEnd,
    });
  } catch (error) {
    next(error);
  }
}

export default {
  listPlans,
  getCurrentSubscription,
  createCheckoutSession,
  getPortalSession,
  cancelSubscription,
  handleWebhook,
  checkFeatureAccess,
  getUsageReport,
};
