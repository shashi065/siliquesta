export const PLAN_LIMITS = {
  free: 10,
  pro: 100,
  enterprise: Number.MAX_SAFE_INTEGER,
};

export function normalizePlan(plan = 'free') {
  const normalized = String(plan || 'free').toLowerCase();
  return Object.hasOwn(PLAN_LIMITS, normalized) ? normalized : 'free';
}

export function usageLimitForPlan(plan = 'free') {
  return PLAN_LIMITS[normalizePlan(plan)];
}

export function toPlanPayload(subscription) {
  const plan = normalizePlan(subscription?.plan);
  const limit = Number(subscription?.usageLimit ?? subscription?.usage_limit ?? usageLimitForPlan(plan));
  const used = Number(subscription?.usageCount ?? subscription?.usage_count ?? 0);

  return {
    plan,
    usage_limit: limit,
    usage_used: used,
    usage_remaining: Math.max(limit - used, 0),
    limit_reached: used >= limit,
  };
}
