/**
 * Pricing Model - SILIQUESTA Plan Definitions
 * Defines all available subscription plans, features, and limits
 */

export const PLANS = {
  FREE: 'free',
  PRO: 'pro',
  ULTRA: 'ultra',
};

export const PLAN_DETAILS = {
  free: {
    name: 'Free',
    description: 'Get started with limited optimization runs',
    price: 0,
    currency: 'USD',
    billingCycle: null,
    stripePriceId: null,
    stripeProductId: null,
    features: ['basic_optimization', 'single_project', 'community_support'],
    limits: {
      monthly_runs: 10,
      max_constraints: 5,
      max_objectives: 2,
      max_projects: 1,
      export_formats: ['json'],
      gpu_acceleration: false,
      ai_insights: false,
      priority_support: false,
      concurrent_optimizations: 1,
    },
  },

  pro: {
    name: 'Pro',
    description: 'Unlimited optimization runs with advanced features',
    price: 29,
    currency: 'USD',
    billingCycle: 'month',
    stripePriceId: process.env.STRIPE_PRO_PRICE_ID || null,
    stripeProductId: process.env.STRIPE_PRO_PRODUCT_ID || null,
    features: [
      'unlimited_runs',
      'multiple_projects',
      'advanced_optimization',
      'ai_insights',
      'priority_support',
      'export_formats',
      'api_access',
      'webhook_support',
    ],
    limits: {
      monthly_runs: Number.MAX_SAFE_INTEGER,
      max_constraints: 50,
      max_objectives: 10,
      max_projects: 50,
      export_formats: ['json', 'csv', 'xml'],
      gpu_acceleration: false,
      ai_insights: true,
      priority_support: true,
      concurrent_optimizations: 5,
    },
  },

  ultra: {
    name: 'Ultra',
    description: 'Maximum performance with GPU acceleration and full AI capabilities',
    price: 99,
    currency: 'USD',
    billingCycle: 'month',
    stripePriceId: process.env.STRIPE_ULTRA_PRICE_ID || null,
    stripeProductId: process.env.STRIPE_ULTRA_PRODUCT_ID || null,
    features: [
      'unlimited_runs',
      'unlimited_projects',
      'advanced_optimization',
      'gpu_acceleration',
      'ai_insights',
      'ml_model_training',
      'priority_support',
      'export_formats',
      'api_access',
      'webhook_support',
      'custom_algorithms',
      'dedicated_support',
    ],
    limits: {
      monthly_runs: Number.MAX_SAFE_INTEGER,
      max_constraints: Number.MAX_SAFE_INTEGER,
      max_objectives: Number.MAX_SAFE_INTEGER,
      max_projects: Number.MAX_SAFE_INTEGER,
      export_formats: ['json', 'csv', 'xml', 'sql', 'parquet'],
      gpu_acceleration: true,
      ai_insights: true,
      ml_training: true,
      priority_support: true,
      custom_algorithms: true,
      concurrent_optimizations: 50,
    },
  },
};

/**
 * Get plan details by plan ID
 * @param {string} planId - Plan identifier (free, pro, ultra)
 * @returns {object} Plan details
 */
export function getPlanDetails(planId = PLANS.FREE) {
  const normalized = String(planId || PLANS.FREE).toLowerCase();
  return PLAN_DETAILS[normalized] || PLAN_DETAILS[PLANS.FREE];
}

/**
 * Get all available plans with details
 * @returns {array} Array of plan details
 */
export function getAllPlans() {
  return [
    PLAN_DETAILS[PLANS.FREE],
    PLAN_DETAILS[PLANS.PRO],
    PLAN_DETAILS[PLANS.ULTRA],
  ];
}

/**
 * Validate if a plan exists
 * @param {string} planId - Plan identifier
 * @returns {boolean} True if plan exists
 */
export function isPlanValid(planId) {
  return Object.values(PLANS).includes(String(planId || '').toLowerCase());
}

/**
 * Get plan limits for a specific plan
 * @param {string} planId - Plan identifier
 * @returns {object} Plan limits
 */
export function getPlanLimits(planId = PLANS.FREE) {
  const plan = getPlanDetails(planId);
  return plan.limits;
}

/**
 * Get monthly run limit for a plan
 * @param {string} planId - Plan identifier
 * @returns {number} Monthly run limit
 */
export function getMonthlyRunLimit(planId = PLANS.FREE) {
  return getPlanLimits(planId).monthly_runs;
}

/**
 * Check if plan has a specific feature
 * @param {string} planId - Plan identifier
 * @param {string} feature - Feature name
 * @returns {boolean} True if plan includes feature
 */
export function hasFeature(planId = PLANS.FREE, feature) {
  const plan = getPlanDetails(planId);
  return plan.features.includes(feature);
}

/**
 * Get stripe price ID for a plan
 * @param {string} planId - Plan identifier
 * @returns {string|null} Stripe price ID
 */
export function getStripePriceId(planId = PLANS.FREE) {
  const plan = getPlanDetails(planId);
  return plan.stripePriceId;
}

/**
 * Compare two plans - returns whether plan1 >= plan2 in features
 * @param {string} plan1 - First plan
 * @param {string} plan2 - Second plan
 * @returns {boolean} True if plan1 has equal or more features
 */
export function planComesAfter(plan1, plan2) {
  const planOrder = [PLANS.FREE, PLANS.PRO, PLANS.ULTRA];
  const index1 = planOrder.indexOf(String(plan1 || '').toLowerCase());
  const index2 = planOrder.indexOf(String(plan2 || '').toLowerCase());
  return index1 >= index2;
}

/**
 * Format plan price for display
 * @param {string} planId - Plan identifier
 * @returns {string} Formatted price
 */
export function formatPlanPrice(planId = PLANS.FREE) {
  const plan = getPlanDetails(planId);
  if (plan.price === 0) return 'Free';
  return `$${plan.price}/${plan.billingCycle}`;
}

export default {
  PLANS,
  PLAN_DETAILS,
  getPlanDetails,
  getAllPlans,
  isPlanValid,
  getPlanLimits,
  getMonthlyRunLimit,
  hasFeature,
  getStripePriceId,
  planComesAfter,
  formatPlanPrice,
};
