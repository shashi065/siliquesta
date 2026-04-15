/**
 * Feature Gating Middleware
 * Checks if user has access to a feature
 */

import { prisma } from '../config/database.js';
import { FeatureGate, Limits } from '../utils/featureGating.js';

/**
 * Create a feature gate middleware
 * Usage: router.post('/expensive-endpoint', featureGate('gpu_acceleration'), controller)
 *
 * @param {string} featureName - Name of the feature to gate
 * @param {object} options - Additional options
 * @param {string} options.limitName - Check usage limit instead of feature
 * @param {number} options.usageIncrement - Amount to increment usage by
 */
export function featureGate(featureName, options = {}) {
  return async (req, res, next) => {
    try {
      const userId = req.user?.userId;

      // Allow unauthenticated requests with free tier limits
      let plan = 'free';

      if (userId) {
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

        plan = subscription.plan;

        // Check usage limits if specified
        if (options.limitName) {
          const isLimitReached = FeatureGate.isLimitReached(
            plan,
            options.limitName,
            subscription.usageCount
          );

          if (isLimitReached) {
            const error = new Error(
              `${options.limitName} limit reached for ${plan} plan. Upgrade to continue.`
            );
            error.statusCode = 429; // Too Many Requests
            error.limit = options.limitName;
            error.plan = plan;
            return next(error);
          }

          // Store for later usage increment
          req.limitName = options.limitName;
          req.incrementUsage = options.usageIncrement || 1;
        }
      }

      // Check feature access
      if (!FeatureGate.hasAccess(plan, featureName)) {
        const error = new Error(
          `Feature "${featureName}" is not available on your ${plan} plan. Upgrade to Pro or Ultra.`
        );
        error.statusCode = 403; // Forbidden
        error.feature = featureName;
        error.plan = plan;
        error.requiredPlan = FeatureGate.getRequiredPlan(featureName);
        return next(error);
      }

      // Store plan in request for later use
      req.userPlan = plan;

      next();
    } catch (error) {
      next(error);
    }
  };
}

/**
 * Middleware to increment usage after successful operation
 * Should be used in response handling
 */
export async function incrementUsage(userId, limitName, amount = 1) {
  if (!userId || !limitName) return;

  try {
    const subscription = await prisma.subscription.findUnique({
      where: { userId },
    });

    if (subscription) {
      await prisma.subscription.update({
        where: { userId },
        data: {
          usageCount: { increment: amount },
        },
      });
    }
  } catch (error) {
    console.error('Failed to increment usage:', error);
    // Don't throw - this is auxiliary tracking
  }
}

/**
 * Middleware to require specific plan or higher
 * Usage: router.post('/ultra-feature', requirePlan('ultra'), controller)
 *
 * @param {string} minimumPlan - Minimum plan required (free, pro, ultra)
 */
export function requirePlan(minimumPlan) {
  return async (req, res, next) => {
    try {
      const userId = req.user?.userId;
      let plan = 'free';

      if (userId) {
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

        plan = subscription.plan;
      }

      const planOrder = { free: 0, pro: 1, ultra: 2 };
      const userLevel = planOrder[plan] ?? 0;
      const requiredLevel = planOrder[minimumPlan] ?? 0;

      if (userLevel < requiredLevel) {
        const error = new Error(
          `This feature requires ${minimumPlan.charAt(0).toUpperCase() + minimumPlan.slice(1)} plan or higher. Current plan: ${plan}`
        );
        error.statusCode = 403;
        error.plan = plan;
        error.requiredPlan = minimumPlan;
        return next(error);
      }

      req.userPlan = plan;
      next();
    } catch (error) {
      next(error);
    }
  };
}

/**
 * Check subscription status and payment health
 * Usage: router.get('/data', checkPaymentStatus, controller)
 */
export async function checkPaymentStatus(req, res, next) {
  try {
    const userId = req.user?.userId;

    if (!userId) {
      return next();
    }

    const subscription = await prisma.subscription.findUnique({
      where: { userId },
    });

    if (subscription) {
      // Warn if past due
      if (subscription.status === 'past_due') {
        req.paymentWarning = 'Payment is overdue. Please update your payment method.';
      }

      // Block if payment failed
      if (subscription.status === 'suspended' || subscription.status === 'unpaid') {
        const error = new Error(
          'Your subscription is suspended due to payment issues. Please update your payment method.'
        );
        error.statusCode = 402; // Payment Required
        error.subscription = subscription;
        return next(error);
      }
    }

    next();
  } catch (error) {
    next(error);
  }
}

export default {
  featureGate,
  requirePlan,
  checkPaymentStatus,
  incrementUsage,
};
