/**
 * WebSocket Stream Client - Real-Time Optimizer
 * Handles: optimization progress, Pareto updates, training status
 * Non-blocking UI with real-time feedback
 */

export class OptimizerStreamClient {
  constructor(wsUrl = null) {
    this.wsUrl = wsUrl || this.getWebSocketUrl();
    this.ws = null;
    this.listeners = new Map();
    this.state = {
      connected: false,
      active: false,
      progress: 0,
      currentIteration: 0,
      totalIterations: 0,
      startTime: null,
      paretoFrontSize: 0,
      convergenceRate: 0,
    };
    this.history = {
      progress: [],
      paretoUpdates: [],
      statusUpdates: [],
    };
  }

  /**
   * Get WebSocket URL based on current location
   */
  getWebSocketUrl() {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const host = window.location.host || 'localhost:10000';
    return `${protocol}://${host}`;
  }

  /**
   * Connect to WebSocket server
   */
  connect() {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('WebSocket connection timeout'));
      }, 5000);

      try {
        this.ws = new WebSocket(this.wsUrl);

        this.ws.onopen = () => {
          clearTimeout(timeout);
          this.state.connected = true;
          this.emit('connected');
          console.log('✓ WebSocket connected');
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(JSON.parse(event.data));
        };

        this.ws.onerror = (error) => {
          clearTimeout(timeout);
          this.state.connected = false;
          console.error('WebSocket error:', error);
          this.emit('error', error);
          reject(error);
        };

        this.ws.onclose = () => {
          this.state.connected = false;
          this.state.active = false;
          this.emit('disconnected');
          console.log('✓ WebSocket disconnected');
        };
      } catch (error) {
        clearTimeout(timeout);
        reject(error);
      }
    });
  }

  /**
   * Handle incoming WebSocket messages
   */
  handleMessage(message) {
    const { type } = message;

    switch (type) {
      case 'CONNECTED':
        this.emit('ready', message);
        break;

      case 'OPTIMIZATION_STARTED':
        this.state.active = true;
        this.state.startTime = Date.now();
        this.emit('optimization:start', message);
        break;

      case 'OPTIMIZATION_PROGRESS':
        this.updateProgress(message);
        break;

      case 'PARETO_UPDATE':
        this.updateParetoFront(message);
        break;

      case 'TRAINING_STATUS':
        this.updateTrainingStatus(message);
        break;

      case 'OPTIMIZATION_COMPLETED':
        this.state.active = false;
        this.emit('optimization:complete', message);
        break;

      case 'ERROR':
        this.state.active = false;
        this.emit('error', message);
        break;

      case 'STREAM_PAUSED':
        this.emit('stream:paused');
        break;

      case 'STREAM_RESUMED':
        this.emit('stream:resumed');
        break;

      case 'STATUS':
        this.emit('status', message);
        break;

      default:
        console.warn('Unknown message type:', type);
    }
  }

  /**
   * Update progress from optimization update
   */
  updateProgress(message) {
    this.state.progress = message.progress;
    this.state.currentIteration = message.iteration;
    this.state.totalIterations = message.totalIterations;
    this.state.convergenceRate = message.convergence?.rate ?? 0;

    this.history.progress.push({
      iteration: message.iteration,
      progress: message.progress,
      score: message.best?.score,
      improvement: message.best?.improvementPercent,
      timestamp: message.timestamp,
    });

    // Keep history bounded
    if (this.history.progress.length > 100) {
      this.history.progress.shift();
    }

    this.emit('progress', {
      progress: this.state.progress,
      iteration: this.state.currentIteration,
      total: this.state.totalIterations,
      best: message.best,
      convergence: message.convergence,
      isImprovement: message.current?.isImprovement,
    });
  }

  /**
   * Update Pareto front
   */
  updateParetoFront(message) {
    const metrics = message.paretoMetrics;
    this.state.paretoFrontSize = metrics.size;

    this.history.paretoUpdates.push({
      iteration: message.iteration,
      size: metrics.size,
      hypervolume: metrics.hypervolume,
      diversity: metrics.diversity,
      timestamp: message.timestamp,
    });

    // Keep history bounded
    if (this.history.paretoUpdates.length > 50) {
      this.history.paretoUpdates.shift();
    }

    this.emit('pareto:update', {
      size: metrics.size,
      hypervolume: metrics.hypervolume,
      spreadMetric: metrics.spreadMetric,
      diversity: metrics.diversity,
      fronts: metrics.fronts,
      iteration: message.iteration,
    });
  }

  /**
   * Update training status
   */
  updateTrainingStatus(message) {
    this.history.statusUpdates.push({
      phase: message.phase,
      progress: message.progress,
      iteration: message.iteration,
      paretoFrontSize: message.paretoFrontSize,
      timestamp: message.timestamp,
    });

    // Keep history bounded
    if (this.history.statusUpdates.length > 50) {
      this.history.statusUpdates.shift();
    }

    this.emit('status:update', {
      phase: message.phase,
      progress: message.progress,
      paretoFrontSize: message.paretoFrontSize,
      estTimeRemaining: message.estTimeRemaining,
    });
  }

  /**
   * Start optimization with streaming
   */
  async startOptimization(payload) {
    if (!this.state.connected) {
      throw new Error('WebSocket not connected');
    }

    if (this.state.active) {
      throw new Error('Optimization already in progress');
    }

    return new Promise((resolve, reject) => {
      const completionHandler = (message) => {
        this.removeListener('optimization:complete', completionHandler);
        this.removeListener('error', errorHandler);
        resolve(message);
      };

      const errorHandler = (message) => {
        this.removeListener('optimization:complete', completionHandler);
        this.removeListener('error', errorHandler);
        reject(new Error(message.message || 'Optimization failed'));
      };

      this.on('optimization:complete', completionHandler);
      this.on('error', errorHandler);

      this.ws.send(JSON.stringify({
        type: 'START_OPTIMIZATION',
        payload,
      }));
    });
  }

  /**
   * Pause stream
   */
  pauseStream() {
    if (!this.state.connected) {
      throw new Error('WebSocket not connected');
    }

    this.ws.send(JSON.stringify({ type: 'PAUSE_STREAM' }));
  }

  /**
   * Resume stream
   */
  resumeStream() {
    if (!this.state.connected) {
      throw new Error('WebSocket not connected');
    }

    this.ws.send(JSON.stringify({ type: 'RESUME_STREAM' }));
  }

  /**
   * Get current status
   */
  async getStatus() {
    return new Promise((resolve) => {
      const handler = (message) => {
        this.removeListener('status', handler);
        resolve(message);
      };

      this.on('status', handler);
      this.ws.send(JSON.stringify({ type: 'GET_STATUS' }));

      // Timeout after 5 seconds
      setTimeout(() => {
        this.removeListener('status', handler);
      }, 5000);
    });
  }

  /**
   * Get state snapshot
   */
  getState() {
    return { ...this.state };
  }

  /**
   * Get history data
   */
  getHistory(type = 'all') {
    if (type === 'all') {
      return this.history;
    }
    return this.history[`${type}Updates`] || [];
  }

  /**
   * Event emitter methods
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    if (!this.listeners.has(event)) return;
    const listeners = this.listeners.get(event);
    const index = listeners.indexOf(callback);
    if (index > -1) {
      listeners.splice(index, 1);
    }
  }

  removeListener(event, callback) {
    this.off(event, callback);
  }

  emit(event, data) {
    if (!this.listeners.has(event)) return;
    this.listeners.get(event).forEach((callback) => {
      try {
        callback(data);
      } catch (error) {
        console.error(`Error in listener for ${event}:`, error);
      }
    });
  }

  /**
   * Cleanup
   */
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.state.connected = false;
    this.state.active = false;
  }
}

/**
 * UI Handler for real-time updates
 * Non-blocking with smooth animations
 */
export class StreamUIHandler {
  constructor(client) {
    this.client = client;
    this.setupEventHandlers();
  }

  setupEventHandlers() {
    // Progress updates
    this.client.on('progress', (data) => {
      this.updateProgressBar(data.progress);
      this.updateIterationCounter(data.iteration, data.total);
      this.updateConvergenceIndicator(data.convergence);
      if (data.isImprovement) {
        this.flashImprovement();
      }
    });

    // Pareto updates
    this.client.on('pareto:update', (data) => {
      this.updateParetoDisplay(data);
    });

    // Status updates
    this.client.on('status:update', (data) => {
      this.updateStatusDisplay(data);
    });

    // Optimization events
    this.client.on('optimization:start', () => {
      this.showOptimizationStarted();
    });

    this.client.on('optimization:complete', (data) => {
      this.showOptimizationComplete(data);
    });

    // Error handling
    this.client.on('error', (error) => {
      this.showError(error.message);
    });
  }

  /**
   * Update progress bar (non-blocking animation)
   */
  updateProgressBar(progress) {
    const progressBar = document.getElementById('optimizer-progress-bar');
    if (progressBar) {
      requestAnimationFrame(() => {
        progressBar.style.width = `${progress}%`;
      });
    }
  }

  /**
   * Update iteration counter
   */
  updateIterationCounter(current, total) {
    const counter = document.getElementById('optimizer-iterations');
    if (counter) {
      counter.textContent = `${current}/${total}`;
    }
  }

  /**
   * Update convergence indicator
   */
  updateConvergenceIndicator(convergence) {
    const indicator = document.getElementById('optimizer-convergence');
    if (indicator) {
      requestAnimationFrame(() => {
        indicator.textContent = `Rate: ${(convergence.rate * 100).toFixed(1)}%`;
        indicator.className = convergence.rate > 0.05 ? 'good' : 'neutral';
      });
    }
  }

  /**
   * Flash improvement indicator
   */
  flashImprovement() {
    const indicator = document.getElementById('optimizer-improvement');
    if (indicator) {
      requestAnimationFrame(() => {
        indicator.classList.add('flash');
        setTimeout(() => {
          indicator.classList.remove('flash');
        }, 300);
      });
    }
  }

  /**
   * Update Pareto front display
   */
  updateParetoDisplay(data) {
    const display = document.getElementById('optimizer-pareto');
    if (display) {
      requestAnimationFrame(() => {
        display.innerHTML = `
          <div class="pareto-metrics">
            <div>Size: <strong>${data.size}</strong></div>
            <div>Hypervolume: <strong>${data.hypervolume.toFixed(2)}</strong></div>
            <div>Diversity: <strong>${data.diversity.spatialDiversity.toFixed(3)}</strong></div>
          </div>
          <div class="pareto-fronts">
            ${data.fronts.map((f, i) => `
              <div class="front-item">
                <span>P${i}: W=${f.params.W} L=${f.params.L} V=${f.params.V}</span>
              </div>
            `).join('')}
          </div>
        `;
      });
    }
  }

  /**
   * Update status display
   */
  updateStatusDisplay(data) {
    const display = document.getElementById('optimizer-status');
    if (display) {
      requestAnimationFrame(() => {
        let phase = data.phase;
        if (data.phase === 'optimizing') {
          phase = `${data.phase} (${data.progress}%)`;
        }
        display.innerHTML = `
          <div>Phase: <strong>${phase}</strong></div>
          <div>Pareto Front: <strong>${data.paretoFrontSize}</strong> solutions</div>
          <div>Time Est: <strong>${(data.estTimeRemaining / 1000).toFixed(1)}s</strong></div>
        `;
      });
    }
  }

  /**
   * Show optimization started
   */
  showOptimizationStarted() {
    const display = document.getElementById('optimizer-message');
    if (display) {
      display.innerHTML = '🚀 Optimization started...';
      display.className = 'status-info';
    }
  }

  /**
   * Show optimization complete
   */
  showOptimizationComplete(data) {
    const display = document.getElementById('optimizer-message');
    if (display) {
      const improvement = data.result.improvement_percent.toFixed(2);
      display.innerHTML = `✓ Complete! ${improvement}% improvement`;
      display.className = 'status-success';
    }
  }

  /**
   * Show error message
   */
  showError(message) {
    const display = document.getElementById('optimizer-message');
    if (display) {
      display.innerHTML = `✗ Error: ${message}`;
      display.className = 'status-error';
    }
  }
}

/**
 * Initialize streaming on page load
 */
export async function initializeOptimizationStream() {
  const client = new OptimizerStreamClient();
  const uiHandler = new StreamUIHandler(client);

  try {
    await client.connect();
    console.log('✓ Stream client ready');
  } catch (error) {
    console.error('✗ Failed to connect:', error);
  }

  return { client, uiHandler };
}
