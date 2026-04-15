# Analytics Integration - Quick Start

## What Was Added

### 1. Analytics Tracking (`src/utils/analytics.js`)
- PostHog integration for event tracking
- Automatic event batching (50 events or 10 seconds)
- Tracks:
  - Optimization runs (start/completion)
  - User behavior (connections/disconnections)  
  - Errors with retry context
  - Custom performance metrics
  - Subscription events

### 2. Performance Monitoring (`src/utils/performanceMonitor.js`)
- Real-time operation latency tracking
- Memory usage monitoring
- Percentile analysis (p50, p95, p99)
- Error and success counting
- Prometheus metrics export
- Health status detection

### 3. Error Logger Integration (`src/utils/errorLogger.js`)
- Automatic analytics event emission on errors
- Error categorization (retryable vs permanent)
- Sentry integration for production errors
- Unified error tracking pipeline

### 4. WebSocket Integration (`src/wsServer.js`)
- Automatic connection/disconnection tracking
- Optimization lifecycle events
- Real-time performance metrics collection
- Error tracking with full context

### 5. Monitoring Endpoints (`src/server.js`)
- `/metrics` - Prometheus format metrics
- `/api/v1/performance/report` - Detailed performance report
- `/api/v1/analytics/stats` - Analytics client status

## Configuration

### Step 1: Set Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Add PostHog credentials:

```env
POSTHOG_API_KEY=phc_your_key_here
POSTHOG_HOST=https://app.posthog.com
```

(Optional) Add Sentry for error tracking:

```env
SENTRY_DSN=https://your_sentry_dsn@sentry.io/project_id
```

### Step 2: Install Dependencies

```bash
cd services/api
npm install
```

PostHog and Sentry are now in `package.json`:
- `posthog-node` - Analytics SDK
- `@sentry/node` - Error tracking (optional)

### Step 3: Verify Integration

Check logs on startup:

```
✓ PostHog analytics initialized
✓ PostHog client ready
```

If you see errors, verify your POSTHOG_API_KEY is valid.

## Testing the Integration

### 1. Check Performance Metrics

```bash
curl http://localhost:10000/metrics
```

You should see Prometheus-format metrics.

### 2. Get Performance Report

```bash
curl http://localhost:10000/api/v1/performance/report | jq
```

Returns JSON with memory, latency percentiles, and health status.

### 3. Check Analytics Status

```bash
curl http://localhost:10000/api/v1/analytics/stats | jq
```

Returns analytics client status and buffered event count.

### 4. View WebSocket Events

Connect to WebSocket and trigger an optimization:

```javascript
const ws = new WebSocket('ws://localhost:10000');

ws.onmessage = (e) => {
  const data = JSON.parse(e.data);
  console.log('Event:', data.type);
};

// Send optimization
ws.send(JSON.stringify({
  type: 'START_OPTIMIZATION',
  payload: { iterations: 25 }
}));
```

Watch for:
- `CONNECTED` - Connection established
- `OPTIMIZATION_STARTED` - Event tracked
- `OPTIMIZATION_COMPLETED` - Completion tracked
- Check PostHog dashboard for events

## Tracked Metrics

### Operations Tracked

1. **Optimization Lifecycle**
   - Start time
   - Duration
   - Completion status
   - Result quality (best score, Pareto front size)
   - Memory usage

2. **Errors**
   - Error type and message
   - Operation causing error
   - Retry attempts
   - Success/failure of retries
   - Error categorization

3. **User Behavior**
   - Connection events
   - Disconnection events
   - Session duration
   - Update count
   - Client ID tracking

4. **Performance**
   - Operation latency (p50, p95, p99)
   - Memory usage trends
   - Heap percentage
   - Active timers
   - Error rates

### Event Format Example

```json
{
  "distinctId": "user-123",
  "event": "optimization_completed",
  "properties": {
    "requestId": "req-456",
    "duration": 5234,
    "updateCount": 42,
    "success": true,
    "bestScore": 0.95,
    "env": "production",
    "appVersion": "1.0.0"
  },
  "timestamp": "2026-04-14T12:34:56.789Z"
}
```

## PostHog Dashboard Setup

### Create Analytics Insights

1. **Optimization Success Rate**
   - Event: `optimization_completed`
   - Filter: `success = true`
   - Breakdown: By day/week

2. **Average Optimization Time**
   - Event: `optimization_completed`
   - Property: `duration`
   - Calculation: Average
   - Trend: By day

3. **Error Frequency**
   - Event: `error_occurred`
   - Count unique
   - Breakdown: By operation

4. **User Retention**
   - Event: `user_connected`
   - Retention: N-day retention
   - Cohort by signup date

5. **Performance SLO**
   - Event: `optimization_completed`
   - Filter: `duration > 10000`
   - Percentage: Monitor for SLO violations

### Create Alerts

Set up notifications for:

- Error rate spike > 5% per minute
- p95 latency > 10 seconds
- Memory heap usage > 85%
- Optimization failure rate > 2%

## Troubleshooting

### 1. PostHog Events Not Appearing

**Symptom**: No events in PostHog dashboard after 1-2 minutes

**Solutions**:
- Verify `POSTHOG_API_KEY` is correct
- Check network connectivity to PostHog
- Review application logs for errors
- Wait up to 5 seconds for batch flush
- Check PostHog status page

**Debug**:
```bash
# Check analytics status
curl http://localhost:10000/api/v1/analytics/stats

# Should show enabled: true
```

### 2. Performance Report Shows No Data

**Symptom**: Empty performance report response

**Solutions**:
- Run an optimization to generate metrics
- Check WebSocket is connected successfully
- Wait for operations to complete

**Debug**:
```bash
# Generate test load
for i in {1..5}; do
  echo "Optimization $i"
  # Send WebSocket messages
done

# Check metrics
curl http://localhost:10000/metrics | head -20
```

### 3. High Memory Usage Reported

**Symptom**: Heap usage > 90% in health check

**Solutions**:
1. Scale up Node.js heap: `NODE_OPTIONS=--max-old-space-size=4096`
2. Reduce optimizationBuffer size in wsServer.js
3. Enable periodic garbage collection
4. Review long-running operations

### 4. Circuit Breaker Opens

**Symptom**: "Circuit breaker is OPEN" errors

**This is normal** - means:
- Too many failures occurred
- System is protecting itself
- Will auto-recover in 60 seconds
- Check error logs for root cause

## Performance Targets

### Latency SLOs

- p50: < 3 seconds
- p95: < 8 seconds  
- p99: < 10 seconds
- max: < 60 seconds (timeout)

### Error Targets

- Error rate: < 1% per optimization
- Retry success rate: > 70%
- Circuit breaker triggers: < 1 per hour

### Memory Targets

- Heap usage: < 70% normal load
- Memory growth: < 50MB per hour
- GC pause time: < 100ms

## Next Steps

1. **Deploy to Production**
   - Set PostHog API key in production environment
   - Enable Sentry DSN for error tracking
   - Configure alerts in PostHog dashboard

2. **Monitor Key Metrics**
   - Set up dashboards for KPIs
   - Create alerts for anomalies
   - Review reports weekly

3. **Optimize Based on Data**
   - Identify slow operations
   - Track user behavior trends
   - Reduce error-prone code paths

4. **Scale Infrastructure**
   - Monitor resource usage trends
   - Plan capacity based on growth
   - Optimize expensive operations

## References

- **PostHog Docs**: https://posthog.com/docs
- **Performance Report**: http://localhost:10000/api/v1/performance/report
- **Metrics Export**: http://localhost:10000/metrics
- **Guide**: See ANALYTICS_INTEGRATION.md for full documentation
