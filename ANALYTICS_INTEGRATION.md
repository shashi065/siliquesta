/**
 * ANALYTICS & PERFORMANCE MONITORING INTEGRATION GUIDE
 * 
 * This guide explains the analytics and performance monitoring system
 * integrated into the SILIQUESTA backend.
 */

# Analytics & Performance Monitoring System

## Overview

The system tracks three key areas:
1. **User Behavior** - Connection, disconnection, optimization runs
2. **Error Events** - All errors with retry context and metadata
3. **Performance Metrics** - Latency, memory, throughput, error rates

## Setup

### Environment Variables

Add to `.env`:

```env
# PostHog Analytics
POSTHOG_API_KEY=your_posthog_api_key
POSTHOG_HOST=https://app.posthog.com

# Sentry Error Tracking (optional)
SENTRY_DSN=your_sentry_dsn

# Node Environment
NODE_ENV=production
```

### Installation

```bash
npm install posthog-node @sentry/node
```

## Components

### 1. Analytics Client (`src/utils/analytics.js`)

Handles all event tracking through PostHog.

**Key Methods:**
- `captureEvent(userId, eventName, properties)` - Track any event
- `trackOptimizationStart(userId, requestId, payload)` - Track optimization start
- `trackOptimizationComplete(requestId, duration, updateCount, result)` - Track completion
- `trackError(userId, requestId, operation, error, context)` - Track errors
- `trackUserAction(userId, action, data)` - Track user actions
- `trackSubscriptionEvent(userId, eventType, plan, metadata)` - Track subscription events
- `trackPerformance(userId, requestId, metric, value, unit)` - Track custom metrics

**Event Batching:**
- Events are buffered and sent in batches of 50 or every 10 seconds
- Automatic enrichment with environment info and version

### 2. Performance Monitor (`src/utils/performanceMonitor.js`)

Real-time performance tracking and metrics.

**Features:**
- Operation timing with percentile analysis (p50, p95, p99)
- Memory monitoring (heap usage, RSS, external)
- Counter-based event tracking
- Gauge-based instantaneous values
- Prometheus-compatible metrics export

**Key Methods:**
- `startTimer(operationId)` - Start timing an operation
- `endTimer(operationId, operation)` - End timer and record metric
- `incrementCounter(name, value)` - Increment counter
- `recordGauge(name, value)` - Record instantaneous value
- `getMemoryMetrics()` - Get current memory usage
- `getPercentiles(operation)` - Get latency percentiles
- `getReport()` - Get full performance report
- `exportMetrics()` - Export in Prometheus format

### 3. Error Logger Integration (`src/utils/errorLogger.js`)

Enhanced error logging with automatic analytics and Sentry integration.

**Features:**
- Automatic error tracking to PostHog
- Retryable error distinction
- Operation context tracking
- Attempt count in analytics

## Tracked Events

### Optimization Events

**optimization_started**
```json
{
  "userId": "user-id",
  "eventName": "optimization_started",
  "properties": {
    "requestId": "req-id",
    "iterations": 25,
    "constraints": 3,
    "objectives": 2
  }
}
```

**optimization_completed**
```json
{
  "userId": "user-id",
  "eventName": "optimization_completed",
  "properties": {
    "requestId": "req-id",
    "duration": 5000,
    "updateCount": 42,
    "success": true,
    "hasPartialResults": false,
    "bestScore": 0.95,
    "improvementPercent": 15.5,
    "paretoSize": 12,
    "memoryUsedMB": "5.23"
  }
}
```

### Error Events

**error_occurred**
```json
{
  "userId": "user-id",
  "eventName": "error_occurred",
  "properties": {
    "requestId": "req-id",
    "operation": "optimization-start",
    "errorMessage": "Subscription check failed",
    "errorCode": "INSUFFICIENT_QUOTA",
    "errorType": "QuotaExceededError",
    "isRetryable": true
  }
}
```

**error_retryable**
```json
{
  "userId": "user-id",
  "eventName": "error_retryable",
  "properties": {
    "requestId": "req-id",
    "operation": "run-optimization",
    "attemptNumber": 2
  }
}
```

### User Behavior Events

**user_connected**
```json
{
  "userId": "user-id",
  "eventName": "user_connected",
  "properties": {
    "clientId": "client-123",
    "timestamp": 1234567890
  }
}
```

**user_disconnected**
```json
{
  "userId": "user-id",
  "eventName": "user_disconnected",
  "properties": {
    "clientId": "client-123",
    "duration": 5000,
    "updates": 42
  }
}
```

### Performance Events

**performance_metric**
```json
{
  "userId": "user-id",
  "eventName": "performance_metric",
  "properties": {
    "requestId": "req-id",
    "metric": "optimization_latency",
    "value": 5000,
    "unit": "ms"
  }
}
```

## API Endpoints

### Performance Metrics Endpoint

```bash
GET /api/v1/metrics
```

Returns current performance metrics in Prometheus format.

**Response:**
```
# HELP siliquesta_uptime_ms Application uptime in milliseconds
# TYPE siliquesta_uptime_ms gauge
siliquesta_uptime_ms 123456
# HELP siliquesta_heap_used_mb Heap memory used in MB
# TYPE siliquesta_heap_used_mb gauge
siliquesta_heap_used_mb 45.23
# HELP siliquesta_optimization_runs Counter for optimization_runs
# TYPE siliquesta_optimization_runs counter
siliquesta_optimization_runs 42
...
```

### Performance Report Endpoint

```bash
GET /api/v1/performance/report
```

Returns detailed performance report.

**Response:**
```json
{
  "summary": {
    "uptime": 123456,
    "memory": {
      "heapUsedMB": "45.23",
      "heapTotalMB": "256.00",
      "externalMB": "2.15",
      "rssMB": "512.50"
    },
    "totalOperations": 42
  },
  "operations": {
    "optimization": {
      "min": 1000,
      "p50": 5000,
      "p95": 8500,
      "p99": 9500,
      "max": 10000,
      "avg": 5200,
      "count": 42
    }
  },
  "health": {
    "status": "healthy",
    "heapUsagePercent": "17.66",
    "activeTimers": 0
  }
}
```

### Analytics Stats Endpoint

```bash
GET /api/v1/analytics/stats
```

Returns analytics client status.

**Response:**
```json
{
  "enabled": true,
  "bufferedEvents": 5,
  "activeSessions": 2
}
```

## Integration Points

### WebSocket Server

All WebSocket operations automatically track:
1. Connection events
2. Optimization start/completion
3. Errors with full context
4. Performance metrics

### Error Logger

All errors are automatically:
1. Logged to console/file
2. Sent to Sentry if configured
3. Tracked to PostHog analytics
4. Stored in local error history

### Performance Monitor

Measures:
1. Operation latencies with percentiles
2. Memory usage trends
3. Error rates by operation
4. System health metrics

## Best Practices

### 1. User Identification

Always provide userId for accurate user behavior tracking:
```javascript
analytics.trackOptimizationStart(userId, requestId, payload);
```

### 2. Context Attachment

Include context in error tracking:
```javascript
analytics.trackError(userId, requestId, 'operation', error, {
  isRetryable: true,
  attempts: 2,
  customData: 'value'
});
```

### 3. Performance Timing

Wrap critical operations:
```javascript
performanceMonitor.startTimer(operationId);
// ... perform operation ...
performanceMonitor.endTimer(operationId, 'operation_name');
```

### 4. Custom Metrics

Track domain-specific metrics:
```javascript
analytics.trackPerformance(userId, requestId, 'circuit_latency', 150, 'ms');
performanceMonitor.recordGauge('active_optimizations', 5);
```

## Monitoring & Alerts

### PostHog Dashboards

Create dashboards for:
- Optimization success rate
- Average optimization duration
- Error frequency by type
- User retention and engagement
- Subscription event tracking

### Performance Alerts

Monitor:
- p95 latency > 10s
- Memory usage > 85% of heap
- Error rate > 5%
- Circuit breaker state = OPEN

### Error Tracking

Review in PostHog:
- Most common errors
- Error trends over time
- Retryable vs permanent errors
- Error impact on user experience

## Troubleshooting

### Analytics Not Tracking

1. Check `POSTHOG_API_KEY` is set
2. Verify PostHog is reachable
3. Check error logs for initialization errors
4. Verify event format in buffer

### Performance Issues

1. Check memory metrics in `/api/v1/performance/report`
2. Review operation latency percentiles
3. Inspect active timer count
4. Check for memory leaks

### High Error Rates

1. Review error logs at `/api/v1/analytics/stats`
2. Check circuit breaker status
3. Review recent deployments
4. Analyze error patterns in PostHog

## Example Usage

```javascript
import { analytics } from './utils/analytics.js';
import { performanceMonitor } from './utils/performanceMonitor.js';

// Track optimization
const userId = 'user-123';
analytics.trackOptimizationStart(userId, requestId, payload);

// Measure performance
performanceMonitor.startTimer(requestId);
await runOptimization();
const duration = performanceMonitor.endTimer(requestId, 'optimization');

// Track completion
analytics.trackOptimizationComplete(requestId, duration, updateCount, result);

// Get metrics
const report = performanceMonitor.getReport();
const stats = analytics.getStats();
```

## References

- **PostHog Docs**: https://posthog.com/docs
- **Sentry Docs**: https://docs.sentry.io
- **Prometheus Format**: https://prometheus.io/docs/instrumenting/exposition_formats/
