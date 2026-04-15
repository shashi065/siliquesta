import { WebSocketServer } from 'ws';
import jwt from 'jsonwebtoken';
import { optimizeCircuit } from './services/aiOptimizer.js';
import { assertUsageAvailable, incrementUsage } from './services/subscriptionService.js';
import {
  ErrorLogger,
  executeWithRetry,
  executeWithTimeout,
  executeWithFallback,
  CircuitBreaker,
  HealthCheck,
  generateRequestId,
  ErrorContext,
  analytics,
  performanceMonitor,
} from './utils/errorLogger.js';

const errorLogger = new ErrorLogger('WebSocket-Server');
const optimizationCircuitBreaker = new CircuitBreaker({
  failureThreshold: 5,
  resetTimeout: 60000,
});
const healthCheck = new HealthCheck();

const OPEN = 1;
const OPTIMIZATION_TIMEOUT = 60000;
const MAX_RETRIES = 3;
const RETRY_DELAY = 100;

export function initWebSocket(server) {
  const wss = new WebSocketServer({ server });
  healthCheck.register('ws-server', async () => (wss.clients.size >= 0), 30000);
  healthCheck.register('database', async () => true, 60000);

  wss.on('connection', (ws) => {
    const clientId = generateClientId();
    const streamState = {
      active: false,
      startTime: null,
      lastUpdateTime: null,
      updateCount: 0,
      requestId: generateRequestId(),
      healthCheckInterval: null,
      heartbeatInterval: null,
    };

    const connectionContext = new ErrorContext('connection', { clientId, requestId: streamState.requestId });

    sendUpdate(ws, {
      type: 'CONNECTED',
      message: 'SILIQUESTA real-time optimizer ready',
      clientId,
      requestId: streamState.requestId,
      timestamp: Date.now(),
    });

    streamState.heartbeatInterval = setInterval(() => {
      if (ws.readyState === OPEN) {
        try {
          ws.ping(() => {});
        } catch (err) {
          errorLogger.warn('Heartbeat failed', connectionContext, { error: err.message });
        }
      }
    }, 30000);

    errorLogger.info('Client connected', connectionContext, { clientsConnected: wss.clients.size });

    // Track connection in analytics
    if (analytics) {
      analytics.trackUserAction('user-' + clientId, 'connected', { clientId, timestamp: Date.now() });
    }

    ws.on('message', async (msg) => {
      const messageContext = new ErrorContext('message-handler', { clientId, requestId: streamState.requestId });
      let data;
      try {
        data = await executeWithTimeout(async () => JSON.parse(msg.toString()), 5000, 'JSON-parse');
      } catch (parseError) {
        errorLogger.error(parseError, messageContext, { rawMessage: msg.toString().slice(0, 100) });
        sendUpdate(ws, { type: 'ERROR', message: 'Invalid WebSocket payload: ' + parseError.message, requestId: streamState.requestId, timestamp: Date.now() });
        return;
      }

      try {
        switch (data.type) {
          case 'START_OPTIMIZATION': await handleOptimizationStart(ws, data, streamState, errorLogger); break;
          case 'PAUSE_STREAM': handlePauseStream(ws, streamState, errorLogger); break;
          case 'RESUME_STREAM': handleResumeStream(ws, streamState, errorLogger); break;
          case 'GET_STATUS': handleGetStatus(ws, streamState, errorLogger); break;
          case 'HEALTH_CHECK': handleHealthCheck(ws, streamState, errorLogger); break;
          default: errorLogger.warn(`Unsupported message type: ${data.type}`, messageContext); sendUpdate(ws, { type: 'ERROR', message: `Unsupported event: ${data.type}`, requestId: streamState.requestId, timestamp: Date.now() });
        }
      } catch (handlerError) {
        errorLogger.error(handlerError, messageContext, { messageType: data.type });
        sendUpdate(ws, { type: 'ERROR', message: 'Handler error: ' + handlerError.message, requestId: streamState.requestId, timestamp: Date.now() });
      }
    });

    ws.on('close', () => {
      streamState.active = false;
      clearInterval(streamState.heartbeatInterval);
      clearInterval(streamState.healthCheckInterval);
      const duration = streamState.startTime ? Date.now() - streamState.startTime : 0;
      errorLogger.info('Client disconnected', connectionContext, { totalUpdates: streamState.updateCount, duration });

      // Track disconnection in analytics
      if (analytics) {
        analytics.trackUserAction('user-' + clientId, 'disconnected', { clientId, duration, updates: streamState.updateCount });
      }
    });

    ws.on('error', (error) => {
      const errorContext = new ErrorContext('websocket-error', { clientId, requestId: streamState.requestId });
      errorLogger.error(error, errorContext, { connectionState: ws.readyState });
    });

    ws.on('pong', () => { streamState.lastUpdateTime = Date.now(); });

    ws.on('ping', () => {
      try {
        ws.pong(() => {});
      } catch (err) {
        const errorContext = new ErrorContext('websocket-pong', { clientId });
        errorLogger.warn('Failed to respond to ping', errorContext);
      }
    });
  });

  return wss;
}

async function handleOptimizationStart(ws, data, streamState, logger) {
  // Start performance tracking
  const perfTimer = streamState.requestId;
  if (performanceMonitor) {
    performanceMonitor.startTimer(perfTimer);
  }
  if (streamState.active) {
    sendUpdate(ws, { type: 'ERROR', message: 'Optimization already in progress', requestId: streamState.requestId, timestamp: Date.now() });
    return;
  }

  const optimizationContext = new ErrorContext('optimization-start', { requestId: streamState.requestId, clientId: data.clientId });
  streamState.active = true;
  streamState.startTime = Date.now();
  streamState.updateCount = 0;

  try {
    let userId = null;
    try {
      userId = await executeWithTimeout(async () => getUserIdFromPayload(data.payload || {}), 5000, 'user-extraction');
    } catch (err) {
      logger.warn('Failed to extract user ID', optimizationContext);
    }

    if (userId) {
      try {
        await executeWithRetry('check-usage', async () => assertUsageAvailable(userId), { maxAttempts: MAX_RETRIES, baseDelay: RETRY_DELAY, logger, metadata: { userId } });
      } catch (err) {
        logger.error(err, optimizationContext, { step: 'usage-check' });
        sendUpdate(ws, { type: 'ERROR', message: 'Subscription check failed: ' + err.message, requestId: streamState.requestId, timestamp: Date.now() });
        streamState.active = false;
        return;
      }
    }

    sendUpdate(ws, { type: 'OPTIMIZATION_STARTED', payload: data.payload, requestId: streamState.requestId, timestamp: Date.now() });

    let updateBuffer = [];
    let bufferFlushTimeout;

    const flushBuffer = () => {
      if (updateBuffer.length > 0 && ws.readyState === 1) {
        try {
          updateBuffer.forEach((update) => {
            if (ws.readyState === 1) {
              ws.send(JSON.stringify(update));
              streamState.updateCount += 1;
              streamState.lastUpdateTime = Date.now();
            }
          });
        } catch (flushErr) {
          logger.error(flushErr, optimizationContext, { step: 'buffer-flush' });
        }
        updateBuffer = [];
      }
      clearTimeout(bufferFlushTimeout);
    };

    const sendUpdateCallback = (update) => {
      try {
        if (ws.readyState !== 1) return;
        update.clientTimestamp = Date.now();
        update.streamElapsed = Date.now() - streamState.startTime;
        update.requestId = streamState.requestId;
        updateBuffer.push(update);
        if (updateBuffer.length >= 5) flushBuffer();
        clearTimeout(bufferFlushTimeout);
        bufferFlushTimeout = setTimeout(flushBuffer, 50);
      } catch (err) {
        logger.warn('Error in update callback', optimizationContext);
      }
    };

    let result;
    try {
      result = await executeWithTimeout(async () => optimizationCircuitBreaker.execute(async () => executeWithRetry('run-optimization', async () => optimizeCircuit(data.payload || {}, sendUpdateCallback), { maxAttempts: MAX_RETRIES, baseDelay: RETRY_DELAY, logger, metadata: { iterations: data.payload?.iterations || 25 } })), OPTIMIZATION_TIMEOUT, 'optimization-execution');
    } catch (timeoutOrRetryError) {
      logger.error(timeoutOrRetryError, optimizationContext, { step: 'optimization-timeout-or-retry' });
      result = { best: { score: 0, improvementPercent: 0, params: {} }, paretoFront: [], paretoMetrics: { size: 0, hypervolume: 0, diversity: {} }, error: timeoutOrRetryError.message, partial: true };
    }

    flushBuffer();
    clearTimeout(bufferFlushTimeout);

    if (userId) {
      try {
        const planResult = await executeWithRetry('increment-usage', async () => incrementUsage(userId), { maxAttempts: MAX_RETRIES, baseDelay: RETRY_DELAY, logger });
        result.plan = planResult;
      } catch (err) {
        logger.error(err, optimizationContext, { step: 'usage-increment' });
      }
    }

    if (ws.readyState === 1) {
      sendUpdate(ws, { type: 'OPTIMIZATION_COMPLETED', best: result.best, paretoFront: result.paretoFront, paretoMetrics: result.paretoMetrics, result, duration: Date.now() - streamState.startTime, totalUpdates: streamState.updateCount, requestId: streamState.requestId, timestamp: Date.now() });
    }

    logger.info('Optimization complete', optimizationContext, { duration: Date.now() - streamState.startTime, updates: streamState.updateCount });
  } catch (error) {
    logger.error(error, optimizationContext, { step: 'optimization-handler' });

    // Track error in performance monitor
    if (performanceMonitor) {
      performanceMonitor.incrementCounter('optimization_errors');
      if (performanceMonitor.timers.has(perfTimer)) {
        performanceMonitor.endTimer(perfTimer, 'optimization_error');
      }
    }

    // Track error in analytics
    if (analytics) {
      const userId = 'anonymous';
      analytics.trackError(userId, streamState.requestId, 'optimization', error, { step: 'optimization-handler' });
    }

    if (ws.readyState === 1) {
      sendUpdate(ws, { type: 'ERROR', message: 'Optimization failed: ' + (error.message || String(error)), duration: Date.now() - streamState.startTime, requestId: streamState.requestId, timestamp: Date.now() });
    }
  } finally {
    streamState.active = false;
  }
}

function handlePauseStream(ws, streamState, logger) {
  if (!streamState.active) {
    sendUpdate(ws, { type: 'WARNING', message: 'No active stream to pause', timestamp: Date.now() });
    return;
  }
  sendUpdate(ws, { type: 'STREAM_PAUSED', timestamp: Date.now() });
}

function handleResumeStream(ws, streamState, logger) {
  sendUpdate(ws, { type: 'STREAM_RESUMED', timestamp: Date.now() });
}

function handleGetStatus(ws, streamState, logger) {
  const status = {
    type: 'STATUS',
    active: streamState.active,
    duration: streamState.active ? Date.now() - streamState.startTime : null,
    updateCount: streamState.updateCount,
    timestamp: Date.now(),
  };

  // Add performance metrics if available
  if (performanceMonitor) {
    status.performance = {
      memoryMetrics: performanceMonitor.getMemoryMetrics(),
      operationMetrics: performanceMonitor.getOperationMetrics('optimization'),
    };
  }

  sendUpdate(ws, status);
}

function handleHealthCheck(ws, streamState, logger) {
  const health = {
    type: 'HEALTH_CHECK_RESPONSE',
    timestamp: Date.now(),
    uptime: streamState.startTime ? Date.now() - streamState.startTime : 0,
  };

  // Include performance health
  if (performanceMonitor) {
    const healthStatus = performanceMonitor.getHealthStatus();
    health.status = healthStatus.status;
    health.heapUsagePercent = healthStatus.heapUsagePercent;
  } else {
    health.status = 'healthy';
  }

  sendUpdate(ws, health);
}

function sendUpdate(ws, data) {
  if (ws && ws.readyState === 1) {
    try {
      ws.send(JSON.stringify(data));
    } catch (error) {
      console.error('Error sending WebSocket update:', error.message);
    }
  }
}

function getUserIdFromPayload(payload) {
  const token = payload?.token;
  if (!token || !process.env.JWT_SECRET) return null;
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    return decoded.userId || decoded.id || null;
  } catch {
    return null;
  }
}

function generateClientId() {
  return `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}
