/**
 * Feature Gating System
 * Controls feature access based on subscription plan
 */

import { getPlanDetails, hasFeature as planHasFeature, getPlanLimits } from '../models/pricing.js';

/**
 * Main FeatureGate class for checking user access to features
 */
export class FeatureGate {
  /**
   * Check if user has access to a feature
   * @param {string} userPlan - User's subscription plan
   * @param {string} featureName - Feature to check
   * @throws {Error} Feature access denied
   * @returns {boolean} True if user has access
   */
  static hasAccess(userPlan, featureName) {
    return planHasFeature(userPlan, featureName);
  }

  /**
   * Check if user can perform an action
   * Throws error if not allowed
   * @param {string} userPlan - User's subscription plan
   * @param {string} featureName - Feature to check
   * @throws {Error} Feature not available for plan
   */
  static assertAccess(userPlan, featureName) {
    if (!this.hasAccess(userPlan, featureName)) {
      const error = new Error(
        `Feature "${featureName}" is not available on your plan. Upgrade to Pro or Ultra.`
      );
      error.statusCode = 403;
      error.feature = featureName;
      error.requiredPlan = this.getRequiredPlan(featureName);
      throw error;
    }
  }

  /**
   * Get the minimum plan required for a feature
   * @param {string} featureName - Feature name
   * @returns {string} Required plan ID
   */
  static getRequiredPlan(featureName) {
    for (const planId of ['free', 'pro', 'ultra']) {
      if (planHasFeature(planId, featureName)) {
        return planId;
      }
    }
    return 'ultra'; // Default to highest tier
  }

  /**
   * Check if user has reached a limit
   * @param {string} userPlan - User's subscription plan
   * @param {string} limitName - Limit to check
   * @param {number} currentUsage - Current usage value
   * @returns {boolean} True if limit reached
   */
  static isLimitReached(userPlan, limitName, currentUsage = 0) {
    const limits = getPlanLimits(userPlan);
    const limit = limits[limitName];
    if (limit === Number.MAX_SAFE_INTEGER) return false;
    return currentUsage >= limit;
  }

  /**
   * Get remaining usage for a limit
   * @param {string} userPlan - User's subscription plan
   * @param {string} limitName - Limit to check
   * @param {number} currentUsage - Current usage value
   * @returns {number} Remaining usage count
   */
  static getRemaining(userPlan, limitName, currentUsage = 0) {
    const limits = getPlanLimits(userPlan);
    const limit = limits[limitName];
    if (limit === Number.MAX_SAFE_INTEGER) return Number.MAX_SAFE_INTEGER;
    return Math.max(0, limit - currentUsage);
  }

  /**
   * Get limit value for a plan
   * @param {string} userPlan - User's subscription plan
   * @param {string} limitName - Limit name
   * @returns {number} Limit value
   */
  static getLimit(userPlan, limitName) {
    return getPlanLimits(userPlan)[limitName] ?? 0;
  }

  /**
   * Create a feature access response
   * @param {string} userPlan - User's subscription plan
   * @param {string} featureName - Feature name
   * @returns {object} Feature access info
   */
  static getFeatureInfo(userPlan, featureName) {
    const hasAccess = this.hasAccess(userPlan, featureName);
    return {
      feature: featureName,
      available: hasAccess,
      plan: userPlan,
      requiredPlan: hasAccess ? null : this.getRequiredPlan(featureName),
      message: hasAccess 
        ? `Feature "${featureName}" is available on your ${userPlan} plan`
        : `Feature "${featureName}" requires an upgrade. Current plan: ${userPlan}`,
    };
  }

  /**
   * Get all available features for a plan
   * @param {string} userPlan - User's subscription plan
   * @returns {array} Array of available features
   */
  static getAvailableFeatures(userPlan) {
    const plan = getPlanDetails(userPlan);
    return plan.features;
  }

  /**
   * Get all available limits for a plan
   * @param {string} userPlan - User's subscription plan
   * @returns {object} Plan limits
   */
  static getAvailableLimits(userPlan) {
    return getPlanLimits(userPlan);
  }

  /**
   * Create usage report for a feature
   * @param {string} userPlan - User's subscription plan
   * @param {string} limitName - Limit name
   * @param {number} currentUsage - Current usage
   * @returns {object} Usage report
   */
  static getUsageReport(userPlan, limitName, currentUsage = 0) {
    const limit = this.getLimit(userPlan, limitName);
    const remaining = this.getRemaining(userPlan, limitName, currentUsage);
    const percentage = limit === Number.MAX_SAFE_INTEGER ? 100 : (currentUsage / limit) * 100;

    return {
      limit: limitName,
      plan: userPlan,
      used: currentUsage,
      limit: limit,
      remaining: remaining,
      percentage: Math.min(100, percentage),
      limitReached: this.isLimitReached(userPlan, limitName, currentUsage),
      unlimited: limit === Number.MAX_SAFE_INTEGER,
    };
  }
}

/**
 * Quick access functions for common feature checks
 */

export const Features = {
  // Optimization features
  BASIC_OPTIMIZATION: 'basic_optimization',
  ADVANCED_OPTIMIZATION: 'advanced_optimization',
  GPU_ACCELERATION: 'gpu_acceleration',
  ML_TRAINING: 'ml_training',
  CUSTOM_ALGORITHMS: 'custom_algorithms',

  // AI features
  AI_INSIGHTS: 'ai_insights',

  // Project features
  MULTIPLE_PROJECTS: 'multiple_projects',
  SINGLE_PROJECT: 'single_project',

  // Support features
  PRIORITY_SUPPORT: 'priority_support',
  COMMUNITY_SUPPORT: 'community_support',
  DEDICATED_SUPPORT: 'dedicated_support',

  // API features
  API_ACCESS: 'api_access',
  WEBHOOK_SUPPORT: 'webhook_support',

  // Export features
  EXPORT_FORMATS: 'export_formats',

  // Run limits
  UNLIMITED_RUNS: 'unlimited_runs',
};

/**
 * Common limit keys
 */
export const Limits = {
  MONTHLY_RUNS: 'monthly_runs',
  MAX_PROJECTS: 'max_projects',
  MAX_CONSTRAINTS: 'max_constraints',
  MAX_OBJECTIVES: 'max_objectives',
  CONCURRENT_OPTIMIZATIONS: 'concurrent_optimizations',
};

export default { FeatureGate, Features, Limits };
