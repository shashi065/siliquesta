/**
 * Error Logging & Monitoring Utility
 * Integrates Sentry for production error tracking
 * Integrates PostHog for analytics tracking
 * Provides structured logging with retry context
 */

// Import analytics and performance monitoring
let analytics = null;
let performanceMonitor = null;

try {
  const { analytics: analyticsModule } = await import('./analytics.js');
  analytics = analyticsModule;
} catch (err) {
  console.warn('⚠ Analytics not available');
}

try {
  const { performanceMonitor: pmModule } = await import('./performanceMonitor.js');
  performanceMonitor = pmModule;
} catch (err) {
  console.warn('⚠ Performance monitor not available');
}

// Sentry initialization (optional - works without it)
let sentryInitialized = false;
let Sentry = null;

try {
  Sentry = require('@sentry/node');
  if (process.env.SENTRY_DSN) {
    Sentry.init({
      dsn: process.env.SENTRY_DSN,
      environment: process.env.NODE_ENV || 'development',
      tracesSampleRate: 1.0,
      integrations: [
        new Sentry.Integrations.Http({ tracing: true }),
      ],
    });
    sentryInitialized = true;
    console.log('✓ Sentry initialized for error tracking');
  }
} catch (err) {
  console.warn('⚠ Sentry not available (optional dependency)');
}

/**
 * Error Context for logging
 */
class ErrorContext {
  constructor(operation, context = {}) {
    this.operation = operation;
    this.context = context;
    this.timestamp = new Date().toISOString();
    this.attempts = context.attempts || 1;
    this.maxAttempts = context.maxAttempts || 3;
    this.requestId = context.requestId || generateRequestId();
  }

  isRetryable() {
    return this.attempts < this.maxAttempts;
  }

  canRetry() {
    return this.attempts < this.maxAttempts;
  }

  nextAttempt() {
    this.attempts++;
    return this.attempts <= this.maxAttempts;
  }

  toJSON() {
    return {
      operation: this.operation,
      timestamp: this.timestamp,
      requestId: this.requestId,
      attempts: this.attempts,
      maxAttempts: this.maxAttempts,
      context: this.context,
    };
  }
}

/**
 * Main Error Logger
 */
class ErrorLogger {
  constructor(serviceName = 'SILIQUESTA') {
    this.serviceName = serviceName;
    this.errorHistory = [];
    this.maxHistorySize = 1000;
  }

  /**
   * Log error with full context
   */
  error(error, errorContext, metadata = {}) {
    const errorEntry = {
      timestamp: new Date().toISOString(),
      service: this.serviceName,
      operation: errorContext.operation,
      requestId: errorContext.requestId,
      attempts: errorContext.attempts,
      maxAttempts: errorContext.maxAttempts,
      isRetryable: errorContext.isRetryable(),
      message: error.message || String(error),
      stack: error.stack,
      code: error.code,
      metadata: metadata,
    };

    // Add to history
    this.errorHistory.push(errorEntry);
    if (this.errorHistory.length > this.maxHistorySize) {
      this.errorHistory.shift();
    }

    // Log to console
    console.error(`❌ [${errorEntry.operation}] ${error.message}`);
    if (error.stack && process.env.NODE_ENV === 'development') {
      console.error(error.stack);
    }

    // Track error in analytics
    if (analytics) {
      const userId = metadata.userId || errorContext.context?.userId || 'anonymous';
      analytics.trackError(userId, errorContext.requestId, errorContext.operation, error, {
        isRetryable: errorContext.isRetryable(),
        attempts: errorContext.attempts,
        maxAttempts: errorContext.maxAttempts,
        ...metadata,
      });
    }

    // Send to Sentry if available
    if (sentryInitialized && Sentry) {
      try {
        Sentry.captureException(error, {
          contexts: {
            error_context: {
              operation: errorContext.operation,
              requestId: errorContext.requestId,
              attempts: errorContext.attempts,
              isRetryable: errorContext.isRetryable(),
            },
          },
          tags: {
            service: this.serviceName,
            operation: errorEntry.operation,
            retryable: errorContext.isRetryable(),
          },
          level: errorContext.isRetryable() ? 'warning' : 'error',
        });
      } catch (sentryErr) {
        console.warn('Failed to send to Sentry:', sentryErr.message);
      }
    }

    return errorEntry;
  }

  /**
   * Log warning
   */
  warn(message, errorContext, metadata = {}) {
    const entry = {
      timestamp: new Date().toISOString(),
      level: 'warning',
      service: this.serviceName,
      operation: errorContext.operation,
      requestId: errorContext.requestId,
      message: message,
      metadata: metadata,
    };

    this.errorHistory.push(entry);
    if (this.errorHistory.length > this.maxHistorySize) {
      this.errorHistory.shift();
    }

    console.warn(`⚠ [${errorContext.operation}] ${message}`);

    if (sentryInitialized && Sentry) {
      try {
        Sentry.captureMessage(message, 'warning');
      } catch (err) {
        // Silently ignore Sentry errors
      }
    }

    return entry;
  }

  /**
   * Log info
   */
  info(message, errorContext, metadata = {}) {
    const entry = {
      timestamp: new Date().toISOString(),
      level: 'info',
      service: this.serviceName,
      operation: errorContext.operation,
      requestId: errorContext.requestId,
      message: message,
      metadata: metadata,
    };

    if (process.env.NODE_ENV === 'development' || process.env.DEBUG) {
      console.log(`ℹ [${errorContext.operation}] ${message}`);
    }

    return entry;
  }

  /**
   * Get recent errors
   */
  getRecentErrors(limit = 20) {
    return this.errorHistory.slice(-limit);
  }

  /**
   * Get error statistics
   */
  getStats() {
    const stats = {
      total: this.errorHistory.length,
      errors: 0,
      warnings: 0,
      info: 0,
      byOperation: {},
      recent24h: 0,
    };

    const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();

    this.errorHistory.forEach(entry => {
      if (entry.level === 'error' || entry.code) stats.errors++;
      else if (entry.level === 'warning') stats.warnings++;
      else stats.info++;

      stats.byOperation[entry.operation] = (stats.byOperation[entry.operation] || 0) + 1;

      if (entry.timestamp > oneDayAgo) stats.recent24h++;
    });

    return stats;
  }

  /**
   * Clear history
   */
  clearHistory() {
    this.errorHistory = [];
  }
}

/**
 * Retry executor with exponential backoff
 */
async function executeWithRetry(operation, fn, options = {}) {
  const {
    maxAttempts = 3,
    baseDelay = 100,
    maxDelay = 10000,
    logger = null,
    metadata = {},
  } = options;

  const errorContext = new ErrorContext(operation, {
    maxAttempts,
    metadata,
  });

  let lastError = null;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    errorContext.attempts = attempt;

    try {
      if (attempt > 1 && logger) {
        const delay = Math.min(baseDelay * Math.pow(2, attempt - 2), maxDelay);
        logger.info(`Retry attempt ${attempt}/${maxAttempts} after ${delay}ms`, errorContext);
        await new Promise(r => setTimeout(r, delay));
      }

      const result = await fn();
      return { success: true, data: result, attempts: attempt };

    } catch (error) {
      lastError = error;

      if (logger) {
        logger.error(error, errorContext, {
          attempt: attempt,
          maxAttempts,
          willRetry: attempt < maxAttempts,
        });
      }

      if (attempt === maxAttempts) {
        throw {
          operation,
          originalError: error,
          attempts: attempt,
          message: `Failed after ${attempt} attempts: ${error.message}`,
        };
      }
    }
  }

  throw lastError;
}

/**
 * Timeout wrapper
 */
async function executeWithTimeout(fn, timeoutMs, operation = 'operation') {
  return Promise.race([
    fn(),
    new Promise((_, reject) =>
      setTimeout(() => {
        reject(new Error(`${operation} timed out after ${timeoutMs}ms`));
      }, timeoutMs)
    ),
  ]);
}

/**
 * Graceful fallback executor
 */
async function executeWithFallback(primary, fallback, operation = 'operation', logger = null) {
  const errorContext = new ErrorContext(operation);

  try {
    return await primary();
  } catch (primaryError) {
    if (logger) {
      logger.warn(`Primary failed, using fallback: ${primaryError.message}`, errorContext);
    }

    try {
      const result = await fallback();
      if (logger) {
        logger.info('Fallback succeeded', errorContext);
      }
      return result;
    } catch (fallbackError) {
      if (logger) {
        logger.error(fallbackError, errorContext, { fallbackFailed: true });
      }
      throw new Error(`Both primary and fallback failed: ${fallbackError.message}`);
    }
  }
}

/**
 * Generate unique request ID
 */
function generateRequestId() {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Circuit breaker pattern
 */
class CircuitBreaker {
  constructor(options = {}) {
    this.failureThreshold = options.failureThreshold || 5;
    this.resetTimeout = options.resetTimeout || 60000;
    this.state = 'CLOSED'; // CLOSED, OPEN, HALF_OPEN
    this.failures = 0;
    this.successes = 0;
    this.lastFailureTime = null;
    this.nextAttemptTime = null;
  }

  async execute(fn) {
    if (this.state === 'OPEN') {
      if (Date.now() > this.nextAttemptTime) {
        this.state = 'HALF_OPEN';
        console.log('🔄 Circuit breaker: HALF_OPEN - attempting recovery');
      } else {
        throw new Error('Circuit breaker is OPEN');
      }
    }

    try {
      const result = await fn();

      if (this.state === 'HALF_OPEN') {
        this.reset();
        console.log('✓ Circuit breaker: CLOSED - recovered');
      }

      return result;
    } catch (error) {
      this.failures++;
      this.lastFailureTime = Date.now();

      if (this.failures >= this.failureThreshold) {
        this.state = 'OPEN';
        this.nextAttemptTime = Date.now() + this.resetTimeout;
        console.error(`❌ Circuit breaker: OPEN - threshold exceeded (${this.failures}/${this.failureThreshold})`);
      }

      throw error;
    }
  }

  reset() {
    this.state = 'CLOSED';
    this.failures = 0;
    this.successes = 0;
    this.lastFailureTime = null;
    this.nextAttemptTime = null;
  }

  getStatus() {
    return {
      state: this.state,
      failures: this.failures,
      successes: this.successes,
      lastFailureTime: this.lastFailureTime,
      nextAttemptTime: this.nextAttemptTime,
    };
  }
}

/**
 * Health check manager
 */
class HealthCheck {
  constructor() {
    this.checks = new Map();
    this.lastCheck = null;
  }

  register(name, checkFn, interval = 30000) {
    this.checks.set(name, {
      fn: checkFn,
      interval,
      lastRun: null,
      status: 'unknown',
      lastError: null,
    });
  }

  async runAll() {
    const results = {};
    const startTime = Date.now();

    for (const [name, check] of this.checks) {
      try {
        const checkStart = Date.now();
        await check.fn();
        const duration = Date.now() - checkStart;

        check.status = 'healthy';
        check.lastRun = new Date().toISOString();
        check.lastError = null;

        results[name] = { status: 'healthy', duration };
      } catch (error) {
        check.status = 'unhealthy';
        check.lastRun = new Date().toISOString();
        check.lastError = error.message;

        results[name] = { status: 'unhealthy', error: error.message };
      }
    }

    this.lastCheck = {
      timestamp: new Date().toISOString(),
      totalDuration: Date.now() - startTime,
      results,
    };

    return results;
  }

  getStatus() {
    return {
      lastCheck: this.lastCheck,
      checks: Array.from(this.checks.entries()).map(([name, check]) => ({
        name,
        status: check.status,
        lastRun: check.lastRun,
        lastError: check.lastError,
      })),
    };
  }
}

module.exports = {
  ErrorContext,
  ErrorLogger,
  executeWithRetry,
  executeWithTimeout,
  executeWithFallback,
  generateRequestId,
  CircuitBreaker,
  HealthCheck,
  sentryInitialized,
  analytics,
  performanceMonitor,
};
