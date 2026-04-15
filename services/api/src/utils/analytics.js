/**
 * Analytics Integration - PostHog
 * Tracks: optimization runs, errors, user behavior, performance metrics
 */

let PostHog = null;
let analyticsEnabled = false;

try {
  PostHog = require('posthog-node').PostHog;
  if (process.env.POSTHOG_API_KEY) {
    analyticsEnabled = true;
    console.log('✓ PostHog analytics initialized');
  }
} catch (err) {
  console.warn('⚠ PostHog SDK not available (optional)');
}

class AnalyticsClient {
  constructor() {
    this.client = null;
    this.sessionMetrics = new Map();
    this.eventBuffer = [];
    this.bufferFlushInterval = null;
    this.initPostHog();
  }

  initPostHog() {
    if (!analyticsEnabled || !PostHog) return;

    try {
      this.client = new PostHog(process.env.POSTHOG_API_KEY, {
        host: process.env.POSTHOG_HOST || 'https://app.posthog.com',
        flushInterval: 5000, // Flush every 5 seconds
        disableGeoip: true,
      });

      // Periodic buffer flush for batching
      this.bufferFlushInterval = setInterval(() => this.flushEventBuffer(), 10000);
      console.log('✓ PostHog client ready');
    } catch (err) {
      console.warn('⚠ PostHog initialization error:', err.message);
      this.client = null;
      analyticsEnabled = false;
    }
  }

  /**
   * Capture event with automatic batching
   */
  captureEvent(userId, eventName, properties = {}) {
    if (!this.client || !analyticsEnabled) return;

    const enrichedEvent = {
      userId,
      eventName,
      timestamp: Date.now(),
      properties: {
        ...properties,
        env: process.env.NODE_ENV || 'development',
        appVersion: process.env.APP_VERSION || '1.0.0',
      },
    };

    this.eventBuffer.push(enrichedEvent);

    // Flush if buffer reaches 50 events
    if (this.eventBuffer.length >= 50) {
      this.flushEventBuffer();
    }
  }

  /**
   * Flush buffered events to PostHog
   */
  flushEventBuffer() {
    if (this.eventBuffer.length === 0) return;

    const batch = this.eventBuffer.splice(0, 50);
    batch.forEach((event) => {
      try {
        this.client.capture({
          distinctId: event.userId,
          event: event.eventName,
          properties: event.properties,
          timestamp: new Date(event.timestamp),
        });
      } catch (err) {
        console.error('Failed to capture event:', err.message);
      }
    });
  }

  /**
   * Track optimization start
   */
  trackOptimizationStart(userId, requestId, payload) {
    this.captureEvent(userId, 'optimization_started', {
      requestId,
      iterations: payload?.iterations || 25,
      constraints: payload?.constraints ? Object.keys(payload.constraints).length : 0,
      objectives: payload?.objectives ? Object.keys(payload.objectives).length : 0,
    });

    // Store session metrics
    this.sessionMetrics.set(requestId, {
      userId,
      startTime: Date.now(),
      startMemory: process.memoryUsage().heapUsed,
    });
  }

  /**
   * Track optimization completion
   */
  trackOptimizationComplete(requestId, duration, updateCount, result) {
    const sessionMetrics = this.sessionMetrics.get(requestId);
    if (!sessionMetrics) return;

    const endMemory = process.memoryUsage().heapUsed;
    const memoryDelta = endMemory - sessionMetrics.startMemory;

    this.captureEvent(sessionMetrics.userId, 'optimization_completed', {
      requestId,
      duration,
      updateCount,
      success: !result.error,
      hasPartialResults: result.partial || false,
      bestScore: result.best?.score,
      improvementPercent: result.best?.improvementPercent,
      paretoSize: result.paretoFront?.length || 0,
      memoryUsedMB: (memoryDelta / 1024 / 1024).toFixed(2),
    });

    this.sessionMetrics.delete(requestId);
  }

  /**
   * Track errors
   */
  trackError(userId, requestId, operation, error, context = {}) {
    this.captureEvent(userId, 'error_occurred', {
      requestId,
      operation,
      errorMessage: error.message,
      errorCode: error.code,
      errorType: error.constructor.name,
      ...context,
    });

    // Also log if error was retryable
    if (context.isRetryable) {
      this.captureEvent(userId, 'error_retryable', {
        requestId,
        operation,
        attemptNumber: context.attempts || 1,
      });
    }
  }

  /**
   * Track user behavior
   */
  trackUserAction(userId, action, data = {}) {
    this.captureEvent(userId, `user_${action}`, data);
  }

  /**
   * Track subscription events
   */
  trackSubscriptionEvent(userId, eventType, plan, metadata = {}) {
    this.captureEvent(userId, `subscription_${eventType}`, {
      plan,
      timestamp: Date.now(),
      ...metadata,
    });
  }

  /**
   * Track performance metrics
   */
  trackPerformance(userId, requestId, metric, value, unit = 'ms') {
    this.captureEvent(userId, 'performance_metric', {
      requestId,
      metric,
      value,
      unit,
      timestamp: Date.now(),
    });
  }

  /**
   * Get session metrics
   */
  getSessionMetric(requestId) {
    return this.sessionMetrics.get(requestId);
  }

  /**
   * Shutdown gracefully
   */
  async shutdown() {
    try {
      this.flushEventBuffer();
      clearInterval(this.bufferFlushInterval);
      if (this.client) {
        await this.client.shutdown();
        console.log('✓ Analytics client shutdown complete');
      }
    } catch (err) {
      console.error('Error shutting down analytics:', err.message);
    }
  }

  /**
   * Get client stats
   */
  getStats() {
    return {
      enabled: analyticsEnabled && !!this.client,
      bufferedEvents: this.eventBuffer.length,
      activeSessions: this.sessionMetrics.size,
    };
  }
}

export const analytics = new AnalyticsClient();
export { AnalyticsClient };
