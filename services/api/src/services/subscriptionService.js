import { prisma } from '../config/database.js';
import { normalizePlan, toPlanPayload, usageLimitForPlan } from '../models/subscription.js';

export async function getOrCreateSubscription(userId) {
  if (!userId) {
    return {
      plan: 'free',
      usageCount: 0,
      usageLimit: usageLimitForPlan('free'),
    };
  }

  const existing = await prisma.subscription.findUnique({ where: { userId } });
  if (existing) return existing;

  return prisma.subscription.create({
    data: {
      userId,
      plan: 'free',
      usageCount: 0,
      usageLimit: usageLimitForPlan('free'),
    },
  });
}

export async function getPlanPayload(userId) {
  return toPlanPayload(await getOrCreateSubscription(userId));
}

export async function assertUsageAvailable(userId) {
  if (!userId) {
    return getPlanPayload(null);
  }

  const subscription = await getOrCreateSubscription(userId);
  const payload = toPlanPayload(subscription);

  if (payload.limit_reached) {
    const error = new Error('Usage limit exceeded');
    error.statusCode = 403;
    error.payload = payload;
    throw error;
  }

  return payload;
}

export async function incrementUsage(userId) {
  if (!userId) {
    return getPlanPayload(null);
  }

  const subscription = await getOrCreateSubscription(userId);
  const plan = normalizePlan(subscription.plan);
  const updated = await prisma.subscription.update({
    where: { userId },
    data: {
      usageCount: { increment: 1 },
      usageLimit: usageLimitForPlan(plan),
    },
  });

  return toPlanPayload(updated);
}
