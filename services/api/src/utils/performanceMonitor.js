/**
 * Performance Monitoring & Metrics
 * Tracks: latency, memory, CPU, throughput, error rates
 */

class PerformanceMonitor {
  constructor() {
    this.metrics = new Map();
    this.timers = new Map();
    this.counters = new Map();
    this.histograms = new Map();
    this.startTime = Date.now();
    this.uptime = 0;
  }

  /**
   * Start timing an operation
   */
  startTimer(operationId) {
    this.timers.set(operationId, Date.now());
  }

  /**
   * End timing and record metric
   */
  endTimer(operationId, operation = 'unknown') {
    const startTime = this.timers.get(operationId);
    if (!startTime) {
      console.warn(`No timer found for ${operationId}`);
      return 0;
    }

    const duration = Date.now() - startTime;
    this.timers.delete(operationId);

    // Record in histogram for percentiles
    if (!this.histograms.has(operation)) {
      this.histograms.set(operation, []);
    }
    this.histograms.get(operation).push(duration);

    // Keep only last 1000 samples
    const samples = this.histograms.get(operation);
    if (samples.length > 1000) {
      samples.shift();
    }

    return duration;
  }

  /**
   * Increment a counter
   */
  incrementCounter(counterName, value = 1) {
    this.counters.set(counterName, (this.counters.get(counterName) || 0) + value);
  }

  /**
   * Record a gauge (instantaneous value)
   */
  recordGauge(gaugeName, value) {
    this.metrics.set(gaugeName, {
      type: 'gauge',
      value,
      timestamp: Date.now(),
    });
  }

  /**
   * Get current memory usage
   */
  getMemoryMetrics() {
    const memUsage = process.memoryUsage();
    return {
      heapUsedMB: (memUsage.heapUsed / 1024 / 1024).toFixed(2),
      heapTotalMB: (memUsage.heapTotal / 1024 / 1024).toFixed(2),
      externalMB: (memUsage.external / 1024 / 1024).toFixed(2),
      rssMB: (memUsage.rss / 1024 / 1024).toFixed(2),
    };
  }

  /**
   * Calculate percentiles for an operation
   */
  getPercentiles(operation) {
    const samples = this.histograms.get(operation) || [];
    if (samples.length === 0) return null;

    const sorted = [...samples].sort((a, b) => a - b);
    return {
      min: sorted[0],
      p50: sorted[Math.floor(sorted.length * 0.5)],
      p95: sorted[Math.floor(sorted.length * 0.95)],
      p99: sorted[Math.floor(sorted.length * 0.99)],
      max: sorted[sorted.length - 1],
      avg: Math.round(sorted.reduce((a, b) => a + b, 0) / sorted.length),
      count: sorted.length,
    };
  }

  /**
   * Get all metrics
   */
  getAllMetrics() {
    const now = Date.now();
    this.uptime = now - this.startTime;

    const operationPercentiles = {};
    for (const [op, samples] of this.histograms) {
      operationPercentiles[op] = this.getPercentiles(op);
    }

    return {
      timestamp: new Date().toISOString(),
      uptime: this.uptime,
      memory: this.getMemoryMetrics(),
      counters: Object.fromEntries(this.counters),
      percentiles: operationPercentiles,
      activeTimers: this.timers.size,
    };
  }

  /**
   * Get specific operation metrics
   */
  getOperationMetrics(operation) {
    return {
      operation,
      percentiles: this.getPercentiles(operation),
      sampleCount: this.histograms.get(operation)?.length || 0,
    };
  }

  /**
   * Reset metrics
   */
  reset() {
    this.metrics.clear();
    this.timers.clear();
    this.counters.clear();
    this.histograms.clear();
    this.startTime = Date.now();
    this.uptime = 0;
  }

  /**
   * Get performance report
   */
  getReport() {
    const metrics = this.getAllMetrics();
    return {
      summary: {
        uptime: metrics.uptime,
        memory: metrics.memory,
        totalOperations: Object.values(metrics.counters).reduce((a, b) => a + b, 0),
      },
      operations: metrics.percentiles,
      health: this.getHealthStatus(),
    };
  }

  /**
   * Determine health status
   */
  getHealthStatus() {
    const memMetrics = this.getMemoryMetrics();
    const heapPercent = (parseFloat(memMetrics.heapUsedMB) / parseFloat(memMetrics.heapTotalMB)) * 100;

    let status = 'healthy';
    if (heapPercent > 95) status = 'critical';
    else if (heapPercent > 85) status = 'warning';

    return {
      status,
      heapUsagePercent: heapPercent.toFixed(2),
      activeTimers: this.timers.size,
      bufferEvents: 0,
    };
  }

  /**
   * Export metrics for external monitoring
   */
  exportMetrics() {
    const metrics = this.getAllMetrics();
    const lines = [];

    // Prometheus-style format
    lines.push('# HELP siliquesta_uptime_ms Application uptime in milliseconds');
    lines.push('# TYPE siliquesta_uptime_ms gauge');
    lines.push(`siliquesta_uptime_ms ${metrics.uptime}`);

    lines.push('# HELP siliquesta_heap_used_mb Heap memory used in MB');
    lines.push('# TYPE siliquesta_heap_used_mb gauge');
    lines.push(`siliquesta_heap_used_mb ${metrics.memory.heapUsedMB}`);

    for (const [counter, value] of this.counters) {
      lines.push(`# HELP siliquesta_${counter} Counter for ${counter}`);
      lines.push(`# TYPE siliquesta_${counter} counter`);
      lines.push(`siliquesta_${counter} ${value}`);
    }

    for (const [op, percentiles] of Object.entries(metrics.percentiles)) {
      if (percentiles) {
        lines.push(`# HELP siliquesta_${op}_p95_ms 95th percentile latency for ${op}`);
        lines.push(`# TYPE siliquesta_${op}_p95_ms gauge`);
        lines.push(`siliquesta_${op}_p95_ms ${percentiles.p95}`);
      }
    }

    return lines.join('\n');
  }
}

export const performanceMonitor = new PerformanceMonitor();
export { PerformanceMonitor };
