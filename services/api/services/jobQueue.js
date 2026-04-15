/**
 * SILIQUESTA - Background Job Queue System
 * Redis-backed asynchronous job processing using BullMQ
 * 
 * Supports:
 * - Long-running simulations
 * - Batch optimizations
 * - Result caching
 * - Job prioritization
 * - Retry logic & dead-letter handling
 */

const Redis = require('redis');

/**
 * Job Queue Manager
 * Handles simulation and optimization jobs
 */
class JobQueueManager {
  constructor(redisConfig = {}) {
    this.redisUrl = redisConfig.url || 'redis://localhost:6379';
    this.redis = null;
    this.queues = new Map();
    this.workers = new Map();
    this.cacheExpiry = redisConfig.cacheExpiry || 3600; // 1 hour default
  }

  async initialize() {
    // In production, use actual Redis client
    // this.redis = Redis.createClient({ url: this.redisUrl });
    // await this.redis.connect();
    
    // For now, use in-memory queue
    this.jobStore = new Map();
    this.jobResults = new Map();
    this.jobCounters = {};
    
    console.log('✓ Job queue system initialized');
  }

  /**
   * Create a simulation job
   */
  async queueSimulation(jobData) {
    const job = {
      id: this.generateJobId('SIM'),
      type: 'simulation',
      projectId: jobData.projectId,
      userId: jobData.userId,
      parameters: jobData.parameters,
      priority: jobData.priority || 5,
      createdAt: new Date().toISOString(),
      status: 'queued',
      attempts: 0,
      maxAttempts: 3,
      timeout: jobData.timeout || 300000, // 5 minutes
    };

    this.jobStore.set(job.id, job);
    this.jobCounters.simulations = (this.jobCounters.simulations || 0) + 1;

    console.log(`[JOB] Simulation job queued: ${job.id}`);

    return job;
  }

  /**
   * Create an optimization job
   */
  async queueOptimization(jobData) {
    const job = {
      id: this.generateJobId('OPT'),
      type: 'optimization',
      projectId: jobData.projectId,
      userId: jobData.userId,
      objectives: jobData.objectives || { freq: 0.35, power: -0.20, health: 0.30, cost: -0.15 },
      iterations: jobData.iterations || 50,
      priority: jobData.priority || 7, // Optimizations get higher priority
      createdAt: new Date().toISOString(),
      status: 'queued',
      attempts: 0,
      maxAttempts: 2,
    };

    this.jobStore.set(job.id, job);
    this.jobCounters.optimizations = (this.jobCounters.optimizations || 0) + 1;

    console.log(`[JOB] Optimization job queued: ${job.id}`);

    return job;
  }

  /**
   * Process a simulation job
   */
  async processSimulation(jobId) {
    const job = this.jobStore.get(jobId);
    if (!job) throw new Error(`Job not found: ${jobId}`);

    try {
      job.status = 'processing';
      job.startedAt = new Date().toISOString();

      // Simulate processing
      const results = await this.runSimulation(job.parameters);

      job.status = 'completed';
      job.completedAt = new Date().toISOString();
      job.results = results;

      this.jobResults.set(jobId, {
        results,
        projectId: job.projectId,
        userId: job.userId,
        timestamp: new Date().toISOString(),
      });

      console.log(`[JOB] Simulation completed: ${jobId}`);

      return results;
    } catch (error) {
      job.attempts++;

      if (job.attempts >= job.maxAttempts) {
        job.status = 'failed';
        job.error = error.message;
        console.error(`[JOB] Simulation failed (max retries): ${jobId}`, error.message);
      } else {
        job.status = 'queued';
        console.warn(`[JOB] Simulation retry ${job.attempts}/${job.maxAttempts}: ${jobId}`);
      }

      throw error;
    }
  }

  /**
   * Process an optimization job
   */
  async processOptimization(jobId) {
    const job = this.jobStore.get(jobId);
    if (!job) throw new Error(`Job not found: ${jobId}`);

    try {
      job.status = 'processing';
      job.startedAt = new Date().toISOString();
      job.progress = 0;

      // Simulate optimization with progress updates
      const results = await this.runOptimization(
        job.objectives,
        job.iterations,
        (progress) => {
          job.progress = progress;
        }
      );

      job.status = 'completed';
      job.completedAt = new Date().toISOString();
      job.results = results;

      this.jobResults.set(jobId, {
        results,
        projectId: job.projectId,
        userId: job.userId,
        timestamp: new Date().toISOString(),
      });

      console.log(`[JOB] Optimization completed: ${jobId}`);

      return results;
    } catch (error) {
      job.attempts++;

      if (job.attempts >= job.maxAttempts) {
        job.status = 'failed';
        job.error = error.message;
        console.error(`[JOB] Optimization failed (max retries): ${jobId}`, error.message);
      } else {
        job.status = 'queued';
        console.warn(`[JOB] Optimization retry ${job.attempts}/${job.maxAttempts}: ${jobId}`);
      }

      throw error;
    }
  }

  /**
   * Get job status
   */
  getJobStatus(jobId) {
    const job = this.jobStore.get(jobId);
    if (!job) return null;

    return {
      id: job.id,
      type: job.type,
      status: job.status,
      progress: job.progress || 0,
      createdAt: job.createdAt,
      startedAt: job.startedAt,
      completedAt: job.completedAt,
      attempts: `${job.attempts}/${job.maxAttempts}`,
    };
  }

  /**
   * Get job results
   */
  getJobResults(jobId) {
    const result = this.jobResults.get(jobId);
    if (!result) return null;

    return {
      jobId,
      ...result,
    };
  }

  /**
   * Queue simulation with caching
   */
  async simulateWithCache(projectId, parameters, cacheKey) {
    // Check cache
    const cached = this.jobResults.get(cacheKey);
    if (cached && Date.now() - new Date(cached.timestamp).getTime() < this.cacheExpiry * 1000) {
      console.log(`[CACHE] Hit for ${cacheKey}`);
      return { ...cached.results, cached: true };
    }

    // Queue new simulation
    const job = await this.queueSimulation({
      projectId,
      parameters,
      userId: 'system',
    });

    const results = await this.processSimulation(job.id);

    // Cache results
    this.jobResults.set(cacheKey, {
      results,
      projectId,
      timestamp: new Date().toISOString(),
    });

    return results;
  }

  /**
   * Get queue statistics
   */
  getQueueStats() {
    const queuedJobs = Array.from(this.jobStore.values()).filter(j => j.status === 'queued');
    const processingJobs = Array.from(this.jobStore.values()).filter(j => j.status === 'processing');
    const completedJobs = Array.from(this.jobStore.values()).filter(j => j.status === 'completed');
    const failedJobs = Array.from(this.jobStore.values()).filter(j => j.status === 'failed');

    return {
      total: this.jobStore.size,
      queued: queuedJobs.length,
      processing: processingJobs.length,
      completed: completedJobs.length,
      failed: failedJobs.length,
      throughput: this.jobCounters,
      avgProcessingTime: this.calculateAvgProcessingTime(),
    };
  }

  /**
   * Internal: run simulation
   */
  async runSimulation(parameters) {
    // Simulated simulation results
    await new Promise(resolve => setTimeout(resolve, 500));

    return {
      metrics: {
        frequency: 1e6 + Math.random() * 500e3,
        power: 50e-9 + Math.random() * 50e-9,
        health: 90 + Math.random() * 10,
        delay: 1e-9,
        gain: 20 + Math.random() * 10,
      },
      parameters,
      simTime: 0.523,
    };
  }

  /**
   * Internal: run optimization
   */
  async runOptimization(objectives, iterations, progressCallback) {
    for (let i = 0; i < iterations; i++) {
      await new Promise(resolve => setTimeout(resolve, 10));
      if (progressCallback) progressCallback((i / iterations) * 100);
    }

    return {
      optimizedParams: {
        wn: 0.6 + Math.random() * 0.1,
        wp: 1.1 + Math.random() * 0.1,
        vdd: 1.15,
      },
      metrics: {
        frequency: 1.2e6,
        power: 45e-9,
        health: 95,
      },
      improvement: 15.5,
      iterations,
    };
  }

  /**
   * Helper: generate job ID
   */
  generateJobId(prefix) {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 8);
    return `${prefix}-${timestamp}-${random}`;
  }

  /**
   * Calculate average processing time
   */
  calculateAvgProcessingTime() {
    const completed = Array.from(this.jobStore.values()).filter(j => j.status === 'completed');
    if (completed.length === 0) return 0;

    const times = completed.map(j => {
      const start = new Date(j.startedAt).getTime();
      const end = new Date(j.completedAt).getTime();
      return end - start;
    });

    return times.reduce((a, b) => a + b, 0) / times.length;
  }

  /**
   * Cleanup old jobs
   */
  cleanup(maxAge = 86400000) { // 24 hours
    const now = Date.now();
    let removed = 0;

    for (const [jobId, job] of this.jobStore.entries()) {
      const age = now - new Date(job.createdAt).getTime();

      if (age > maxAge && (job.status === 'completed' || job.status === 'failed')) {
        this.jobStore.delete(jobId);
        this.jobResults.delete(jobId);
        removed++;
      }
    }

    console.log(`[CLEANUP] Removed ${removed} old jobs`);
  }
}

/**
 * Cache Manager
 * Redis-backed caching for simulation results and computations
 */
class CacheManager {
  constructor(redisUrl = 'redis://localhost:6379') {
    this.redisUrl = redisUrl;
    this.cache = new Map();
    this.expiryTimes = new Map();
  }

  set(key, value, ttl = 3600) {
    this.cache.set(key, value);
    this.expiryTimes.set(key, Date.now() + ttl * 1000);

    // Cleanup on expiry
    setTimeout(() => {
      this.delete(key);
    }, ttl * 1000);
  }

  get(key) {
    const value = this.cache.get(key);
    
    // Check expiry
    const expiry = this.expiryTimes.get(key);
    if (expiry && Date.now() > expiry) {
      this.delete(key);
      return null;
    }

    return value;
  }

  delete(key) {
    this.cache.delete(key);
    this.expiryTimes.delete(key);
  }

  clear() {
    this.cache.clear();
    this.expiryTimes.clear();
  }

  getStats() {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys()),
    };
  }
}

/**
 * Worker Pool
 * Manages concurrent job processing
 */
class WorkerPool {
  constructor(numWorkers = 4) {
    this.numWorkers = numWorkers;
    this.activeWorkers = 0;
    this.maxWorkers = numWorkers;
    this.taskQueue = [];
  }

  async execute(task) {
    if (this.activeWorkers >= this.maxWorkers) {
      // Queue task
      return new Promise((resolve, reject) => {
        this.taskQueue.push({ task, resolve, reject });
      });
    }

    try {
      this.activeWorkers++;
      const result = await task();
      return result;
    } finally {
      this.activeWorkers--;
      this.processQueue();
    }
  }

  processQueue() {
    if (this.taskQueue.length === 0 || this.activeWorkers >= this.maxWorkers) {
      return;
    }

    const { task, resolve, reject } = this.taskQueue.shift();
    this.execute(task)
      .then(resolve)
      .catch(reject);
  }

  getStats() {
    return {
      active: this.activeWorkers,
      max: this.maxWorkers,
      queueLength: this.taskQueue.length,
      utilization: ((this.activeWorkers / this.maxWorkers) * 100).toFixed(1) + '%',
    };
  }
}

module.exports = {
  JobQueueManager,
  CacheManager,
  WorkerPool,
};
