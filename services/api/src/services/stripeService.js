/**
 * Stripe Payment Service
 * Handles all Stripe integration: checkout, subscriptions, webhooks
 */

import Stripe from 'stripe';
import { prisma } from '../config/database.js';
import { getStripePriceId, getPlanDetails } from '../models/pricing.js';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY || '');

/**
 * Create a checkout session for a plan upgrade
 * @param {string} userId - User ID
 * @param {string} userEmail - User email
 * @param {string} planId - Plan ID (pro or ultra)
 * @param {string} successUrl - URL to redirect on success
 * @param {string} cancelUrl - URL to redirect on cancel
 * @returns {object} Checkout session
 */
export async function createCheckoutSession(userId, userEmail, planId, successUrl, cancelUrl) {
  if (!process.env.STRIPE_SECRET_KEY) {
    throw new Error('Stripe is not configured. Set STRIPE_SECRET_KEY.');
  }

  const priceId = getStripePriceId(planId);
  if (!priceId) {
    throw new Error(`No Stripe price configured for plan: ${planId}`);
  }

  try {
    let customer = null;

    // Find or create Stripe customer
    const subscription = await prisma.subscription.findUnique({
      where: { userId },
    });

    if (subscription?.stripeCustomerId) {
      customer = { id: subscription.stripeCustomerId };
    } else {
      const stripeCustomer = await stripe.customers.create({
        email: userEmail,
        metadata: {
          userId,
          createdAt: new Date().toISOString(),
        },
      });
      customer = stripeCustomer;

      // Update subscription with Stripe customer ID
      await prisma.subscription.update({
        where: { userId },
        data: { stripeCustomerId: stripeCustomer.id },
      });
    }

    // Create checkout session
    const session = await stripe.checkout.sessions.create({
      customer: customer.id,
      payment_method_types: ['card'],
      line_items: [
        {
          price: priceId,
          quantity: 1,
        },
      ],
      mode: 'subscription',
      success_url: successUrl,
      cancel_url: cancelUrl,
      metadata: {
        userId,
        planId,
      },
    });

    return {
      sessionId: session.id,
      url: session.url,
      customerId: customer.id,
    };
  } catch (error) {
    console.error('Stripe checkout error:', error);
    throw error;
  }
}

/**
 * Handle subscription.updated webhook
 * @param {object} subscription - Stripe subscription object
 */
export async function handleSubscriptionUpdated(subscription) {
  const userId = subscription.metadata?.userId;
  const planId = subscription.metadata?.planId;

  if (!userId) {
    console.warn('Webhook received for subscription with no userId');
    return;
  }

  // Map Stripe status to our status
  const statusMap = {
    active: 'active',
    past_due: 'past_due',
    unpaid: 'unpaid',
    canceled: 'canceled',
    incomplete: 'incomplete',
    incomplete_expired: 'inactive',
  };

  const status = statusMap[subscription.status] || 'unknown';

  // Determine plan from items
  let newPlanId = planId || 'free';
  if (subscription.items?.data?.[0]?.price?.lookup_key) {
    newPlanId = subscription.items.data[0].price.lookup_key;
  }

  // Update subscription in database
  await prisma.subscription.update({
    where: { userId },
    data: {
      stripeSubscriptionId: subscription.id,
      stripeCustomerId: subscription.customer,
      plan: newPlanId,
      status,
      currentPeriodStart: new Date(subscription.current_period_start * 1000),
      currentPeriodEnd: new Date(subscription.current_period_end * 1000),
      canceledAt: subscription.canceled_at ? new Date(subscription.canceled_at * 1000) : null,
    },
  });

  console.log(`Updated subscription for user ${userId}: ${newPlanId} (${status})`);
}

/**
 * Handle invoice.payment_succeeded webhook
 * @param {object} invoice - Stripe invoice object
 */
export async function handleInvoicePaymentSucceeded(invoice) {
  const customerId = invoice.customer;
  if (!customerId) return;

  // Find subscription by customer ID
  const subscription = await prisma.subscription.findFirst({
    where: { stripeCustomerId: customerId },
  });

  if (subscription) {
    // Update last payment info
    await prisma.subscription.update({
      where: { userId: subscription.userId },
      data: {
        lastPaymentDate: new Date(invoice.paid_at * 1000),
        paymentStatus: 'succeeded',
      },
    });
  }
}

/**
 * Handle charge.failed webhook
 * @param {object} charge - Stripe charge object
 */
export async function handleChargeFailed(charge) {
  const customerId = charge.customer;
  if (!customerId) return;

  // Find subscription by customer ID
  const subscription = await prisma.subscription.findFirst({
    where: { stripeCustomerId: customerId },
  });

  if (subscription) {
    await prisma.subscription.update({
      where: { userId: subscription.userId },
      data: {
        paymentStatus: 'failed',
        failureReason: charge.failure_message,
      },
    });
  }
}

/**
 * Handle customer.subscription.deleted webhook
 * @param {object} subscription - Stripe subscription object
 */
export async function handleSubscriptionDeleted(subscription) {
  const userId = subscription.metadata?.userId;
  if (!userId) return;

  // Downgrade user to free plan
  await prisma.subscription.update({
    where: { userId },
    data: {
      plan: 'free',
      status: 'canceled',
      stripeSubscriptionId: null,
      canceledAt: new Date(),
    },
  });

  console.log(`Subscription deleted for user ${userId}, downgraded to free`);
}

/**
 * Verify webhook signature
 * @param {string} body - Raw request body
 * @param {string} signature - Signature from header
 * @returns {object} Parsed event
 */
export function verifyWebhookSignature(body, signature) {
  if (!process.env.STRIPE_WEBHOOK_SECRET) {
    throw new Error('STRIPE_WEBHOOK_SECRET not configured');
  }

  return stripe.webhooks.constructEvent(body, signature, process.env.STRIPE_WEBHOOK_SECRET);
}

/**
 * Get customer portal session for managing subscriptions
 * @param {string} userId - User ID
 * @param {string} returnUrl - URL to return to
 * @returns {object} Portal session
 */
export async function getPortalSession(userId, returnUrl) {
  const subscription = await prisma.subscription.findUnique({
    where: { userId },
  });

  if (!subscription?.stripeCustomerId) {
    throw new Error('User does not have a Stripe customer ID');
  }

  const session = await stripe.billingPortal.sessions.create({
    customer: subscription.stripeCustomerId,
    return_url: returnUrl,
  });

  return session;
}

/**
 * Cancel subscription
 * @param {string} userId - User ID
 */
export async function cancelSubscription(userId) {
  const subscription = await prisma.subscription.findUnique({
    where: { userId },
  });

  if (!subscription?.stripeSubscriptionId) {
    throw new Error('User does not have an active Stripe subscription');
  }

  const canceled = await stripe.subscriptions.del(subscription.stripeSubscriptionId);
  return canceled;
}

/**
 * Get subscription details from Stripe
 * @param {string} stripeSubscriptionId - Stripe subscription ID
 * @returns {object} Subscription details
 */
export async function getSubscriptionDetails(stripeSubscriptionId) {
  return stripe.subscriptions.retrieve(stripeSubscriptionId);
}

/**
 * Check if Stripe is configured
 * @returns {boolean} True if Stripe is configured
 */
export function isStripeConfigured() {
  return !!process.env.STRIPE_SECRET_KEY;
}

export default {
  createCheckoutSession,
  handleSubscriptionUpdated,
  handleInvoicePaymentSucceeded,
  handleChargeFailed,
  handleSubscriptionDeleted,
  verifyWebhookSignature,
  getPortalSession,
  cancelSubscription,
  getSubscriptionDetails,
  isStripeConfigured,
};
