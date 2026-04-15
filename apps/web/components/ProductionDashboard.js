/**
 * SILIQUESTA - Production Dashboard Component
 * Professional SaaS-grade UI for project management, simulations, and optimization
 */

class ProductionDashboard {
  constructor() {
    this.currentProject = null;
    this.simulations = [];
    this.optimizations = [];
    this.projects = [];
    this.activeTab = 'dashboard';
    this.init();
  }

  init() {
    this.setupEventListeners();
    this.loadDashboard();
  }

  setupEventListeners() {
    // Tab navigation
    document.querySelectorAll('[data-tab]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        this.switchTab(e.target.dataset.tab);
      });
    });

    // Project list
    document.addEventListener('projectSelected', (e) => {
      this.selectProject(e.detail);
    });

    // Simulation callbacks
    document.addEventListener('simulationComplete', (e) => {
      this.onSimulationComplete(e.detail);
    });
  }

  switchTab(tabName) {
    this.activeTab = tabName;

    // Update UI
    document.querySelectorAll('[data-tab]').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    document.querySelectorAll('.tab-pane').forEach(pane => {
      pane.classList.toggle('hidden', pane.id !== `tab-${tabName}`);
    });

    if (tabName === 'dashboard') this.loadDashboard();
    else if (tabName === 'simulations') this.loadSimulations();
    else if (tabName === 'optimization') this.loadOptimization();
  }

  /**
   * Dashboard Tab - Overview of recent activity
   */
  async loadDashboard() {
    const dashboard = document.getElementById('tab-dashboard');
    if (!dashboard) return;

    try {
      const [projects, recentSims, suggestions] = await Promise.all([
        this.getRecentProjects(5),
        this.getRecentSimulations(5),
        this.getOptimizationSuggestions(),
      ]);

      dashboard.innerHTML = this.renderDashboard(projects, recentSims, suggestions);
    } catch (error) {
      console.error('Dashboard load error:', error);
      dashboard.innerHTML = `<div class="error">Failed to load dashboard: ${error.message}</div>`;
    }
  }

  renderDashboard(projects, simulations, suggestions) {
    return `
      <div class="dashboard-container">
        <div class="dashboard-header">
          <h1>Dashboard</h1>
          <p class="subtitle">Welcome back! Here's your recent activity.</p>
        </div>

        <div class="dashboard-grid">
          <!-- Stats Cards -->
          <div class="stats-section">
            <div class="stat-card">
              <div class="stat-icon">📁</div>
              <div class="stat-content">
                <div class="stat-value">${projects.length}</div>
                <div class="stat-label">Recent Projects</div>
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon">⚡</div>
              <div class="stat-content">
                <div class="stat-value">${simulations.length}</div>
                <div class="stat-label">Recent Simulations</div>
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon">✅</div>
              <div class="stat-content">
                <div class="stat-value">${simulations.filter(s => s.status === 'completed').length}</div>
                <div class="stat-label">Completed</div>
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon">⏱️</div>
              <div class="stat-content">
                <div class="stat-value">${this.formatAvgTime(simulations)}</div>
                <div class="stat-label">Avg. Time</div>
              </div>
            </div>
          </div>

          <!-- Recent Projects -->
          <div class="section">
            <h2>Recent Projects</h2>
            <div class="project-list-compact">
              ${projects.map(p => `
                <div class="project-card-compact" onclick="window.projectService.selectProject(${p.id})">
                  <div class="project-icon">📋</div>
                  <div class="project-info">
                    <h3>${p.name}</h3>
                    <p>${p.description || 'No description'}</p>
                  </div>
                  <div class="project-meta">
                    <span class="date">${new Date(p.updated_at).toLocaleDateString()}</span>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>

          <!-- Recent Simulations -->
          <div class="section">
            <h2>Recent Simulations</h2>
            <div class="simulation-timeline">
              ${simulations.map((s, i) => `
                <div class="timeline-item">
                  <div class="timeline-marker ${s.status}"></div>
                  <div class="timeline-content">
                    <h4>${s.type || 'Simulation'} - ${s.status}</h4>
                    <p>Frequency: <strong>${this.formatFreq(s.results?.metrics?.frequency)}</strong></p>
                    <p>Power: <strong>${this.formatPower(s.results?.metrics?.power)}</strong></p>
                    <span class="time">${new Date(s.timestamp).toLocaleString()}</span>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>

          <!-- Optimization Suggestions -->
          <div class="section">
            <h2>AI Suggestions</h2>
            <div class="suggestions-list">
              ${suggestions.map(s => `
                <div class="suggestion-card">
                  <div class="suggestion-icon">💡</div>
                  <div class="suggestion-content">
                    <h4>${s.title}</h4>
                    <p>${s.description}</p>
                    <div class="suggestion-impact">
                      <span class="impact positive">+${s.expectedImprovement}% improvement</span>
                    </div>
                  </div>
                  <button class="suggestion-action" onclick="window.applyOptimization('${s.id}')">
                    Apply →
                  </button>
                </div>
              `).join('')}
            </div>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Simulations Tab - History and details
   */
  async loadSimulations() {
    const tab = document.getElementById('tab-simulations');
    if (!tab) return;

    try {
      const simulations = this.currentProject ? 
        await this.getProjectSimulations(this.currentProject.id) : 
        await this.getRecentSimulations(50);

      tab.innerHTML = this.renderSimulationsTab(simulations);
      this.renderSimulationCharts(simulations);
    } catch (error) {
      tab.innerHTML = `<div class="error">Failed to load simulations: ${error.message}</div>`;
    }
  }

  renderSimulationsTab(simulations) {
    return `
      <div class="simulations-container">
        <div class="section-header">
          <h2>Simulation History</h2>
          <p>${simulations.length} simulation(s)</p>
        </div>

        <div class="simulation-filters">
          <button class="filter-btn active" data-filter="all">All</button>
          <button class="filter-btn" data-filter="completed">Completed</button>
          <button class="filter-btn" data-filter="running">Running</button>
          <button class="filter-btn" data-filter="failed">Failed</button>
        </div>

        <div class="simulation-table">
          <table>
            <thead>
              <tr>
                <th>Project</th>
                <th>Status</th>
                <th>Frequency</th>
                <th>Power</th>
                <th>Health</th>
                <th>Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              ${simulations.map(sim => `
                <tr class="sim-row ${sim.status}">
                  <td>${sim.projectName}</td>
                  <td><span class="status-badge ${sim.status}">${sim.status}</span></td>
                  <td>${this.formatFreq(sim.results?.metrics?.frequency)}</td>
                  <td>${this.formatPower(sim.results?.metrics?.power)}</td>
                  <td><span class="health-score">${sim.results?.metrics?.health?.toFixed(0) || 'N/A'}%</span></td>
                  <td>${new Date(sim.timestamp).toLocaleDateString()}</td>
                  <td>
                    <button class="btn-small" onclick="window.viewSimulationDetails(${sim.id})">Details</button>
                    <button class="btn-small" onclick="window.downloadResults(${sim.id})">Download</button>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>

        <div id="simulation-charts" class="charts-section"></div>
      </div>
    `;
  }

  renderSimulationCharts(simulations) {
    const chartContainer = document.getElementById('simulation-charts');
    if (!chartContainer || simulations.length === 0) return;

    // Frequency trend chart
    const freqs = simulations
      .filter(s => s.results?.metrics?.frequency)
      .map(s => s.results.metrics.frequency / 1e6);

    const powers = simulations
      .filter(s => s.results?.metrics?.power)
      .map(s => s.results.metrics.power * 1e9);

    chartContainer.innerHTML = `
      <div class="chart-row">
        <div class="chart">
          <h3>Frequency Trend</h3>
          <canvas id="freq-chart"></canvas>
        </div>
        <div class="chart">
          <h3>Power Consumption</h3>
          <canvas id="power-chart"></canvas>
        </div>
      </div>
    `;

    // Simple text-based charts (in real app, use Chart.js or D3)
    this.renderSimpleChart('freq-chart', freqs, 'MHz');
    this.renderSimpleChart('power-chart', powers, 'nW');
  }

  /**
   * Optimization Tab - Comparison and suggestions
   */
  async loadOptimization() {
    const tab = document.getElementById('tab-optimization');
    if (!tab) return;

    if (!this.currentProject) {
      tab.innerHTML = '<div class="info">Please select a project first</div>';
      return;
    }

    try {
      const [baseline, optimized, suggestions] = await Promise.all([
        this.getBaselineMetrics(this.currentProject.id),
        this.getOptimizedMetrics(this.currentProject.id),
        this.getOptimizationSuggestions(),
      ]);

      tab.innerHTML = this.renderOptimizationTab(baseline, optimized, suggestions);
    } catch (error) {
      tab.innerHTML = `<div class="error">Failed to load optimization: ${error.message}</div>`;
    }
  }

  renderOptimizationTab(baseline, optimized, suggestions) {
    const improvements = {
      freq: ((optimized.frequency - baseline.frequency) / baseline.frequency * 100).toFixed(1),
      power: ((baseline.power - optimized.power) / baseline.power * 100).toFixed(1),
      health: (optimized.health - baseline.health).toFixed(1),
    };

    return `
      <div class="optimization-container">
        <div class="section-header">
          <h2>AI Optimization</h2>
          <p>Baseline vs. AI-Optimized Designs</p>
        </div>

        <!-- Comparison Grid -->
        <div class="comparison-grid">
          <div class="comparison-item">
            <div class="metric">
              <div class="metric-label">Frequency</div>
              <div class="metric-baseline">${this.formatFreq(baseline.frequency)}</div>
              <div class="metric-optimized">${this.formatFreq(optimized.frequency)}</div>
              <div class="metric-improvement ${improvements.freq > 0 ? 'positive' : 'negative'}">
                ${improvements.freq > 0 ? '+' : ''}${improvements.freq}%
              </div>
            </div>
          </div>

          <div class="comparison-item">
            <div class="metric">
              <div class="metric-label">Power</div>
              <div class="metric-baseline">${this.formatPower(baseline.power)}</div>
              <div class="metric-optimized">${this.formatPower(optimized.power)}</div>
              <div class="metric-improvement ${improvements.power > 0 ? 'positive' : 'negative'}">
                ${improvements.power > 0 ? '+' : ''}${improvements.power}%
              </div>
            </div>
          </div>

          <div class="comparison-item">
            <div class="metric">
              <div class="metric-label">Reliability</div>
              <div class="metric-baseline">${baseline.health?.toFixed(0) || 'N/A'}%</div>
              <div class="metric-optimized">${optimized.health?.toFixed(0) || 'N/A'}%</div>
              <div class="metric-improvement positive">
                +${improvements.health}%
              </div>
            </div>
          </div>

          <div class="comparison-item">
            <div class="metric">
              <div class="metric-label">Design Cost</div>
              <div class="metric-baseline">$${baseline.cost?.toFixed(0) || '0'}</div>
              <div class="metric-optimized">$${optimized.cost?.toFixed(0) || '0'}</div>
              <div class="metric-improvement negative">
                ${((optimized.cost - baseline.cost) / baseline.cost * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        </div>

        <!-- Parameter Changes -->
        <div class="section">
          <h3>Recommended Parameter Changes</h3>
          <table class="parameter-table">
            <thead>
              <tr>
                <th>Parameter</th>
                <th>Current</th>
                <th>Optimized</th>
                <th>Impact</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>NMOS Width (Wn)</td>
                <td>${baseline.params.wn.toFixed(2)}</td>
                <td>${optimized.params.wn.toFixed(2)}</td>
                <td class="positive">+${((optimized.params.wn - baseline.params.wn) / baseline.params.wn * 100).toFixed(0)}%</td>
              </tr>
              <tr>
                <td>PMOS Width (Wp)</td>
                <td>${baseline.params.wp.toFixed(2)}</td>
                <td>${optimized.params.wp.toFixed(2)}</td>
                <td class="positive">+${((optimized.params.wp - baseline.params.wp) / baseline.params.wp * 100).toFixed(0)}%</td>
              </tr>
              <tr>
                <td>Supply Voltage (Vdd)</td>
                <td>${baseline.params.vdd.toFixed(2)}V</td>
                <td>${optimized.params.vdd.toFixed(2)}V</td>
                <td class="positive">${(optimized.params.vdd - baseline.params.vdd).toFixed(2)}V</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Action Buttons -->
        <div class="action-buttons">
          <button class="btn btn-primary" onclick="window.applyOptimization()">
            Apply Optimization
          </button>
          <button class="btn btn-secondary" onclick="window.exportComparison()">
            Export Comparison
          </button>
          <button class="btn btn-secondary" onclick="window.runNewOptimization()">
            Run New Optimization
          </button>
        </div>
      </div>
    `;
  }

  /**
   * Helper methods
   */
  formatFreq(freq) {
    if (!freq) return 'N/A';
    if (freq >= 1e9) return (freq / 1e9).toFixed(2) + ' GHz';
    return (freq / 1e6).toFixed(2) + ' MHz';
  }

  formatPower(power) {
    if (!power) return 'N/A';
    if (power >= 1) return (power).toFixed(2) + ' W';
    if (power >= 1e-3) return (power * 1e3).toFixed(2) + ' mW';
    if (power >= 1e-6) return (power * 1e6).toFixed(2) + ' µW';
    return (power * 1e9).toFixed(2) + ' nW';
  }

  formatAvgTime(simulations) {
    if (simulations.length === 0) return 'N/A';
    const times = simulations
      .filter(s => s.duration)
      .map(s => s.duration);
    const avg = times.reduce((a, b) => a + b, 0) / times.length;
    return (avg / 1000).toFixed(1) + 's';
  }

  renderSimpleChart(canvasId, data, label) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min || 1;

    ctx.clearRect(0, 0, width, height);
    ctx.strokeStyle = '#3b82f6';
    ctx.lineWidth = 2;

    const pointWidth = width / (data.length - 1 || 1);
    ctx.beginPath();

    data.forEach((value, i) => {
      const x = i * pointWidth;
      const y = height - ((value - min) / range) * height * 0.8 - height * 0.1;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });

    ctx.stroke();
  }

  /**
   * Data fetching (mock implementations)
   */
  async getRecentProjects(limit) {
    return [
      {
        id: 1,
        name: 'CPU Core - 5nm',
        description: 'High-performance processor optimization',
        updated_at: new Date(Date.now() - 3600000),
      },
      {
        id: 2,
        name: 'Memory Controller',
        description: 'DRAM interface optimization',
        updated_at: new Date(Date.now() - 86400000),
      },
    ].slice(0, limit);
  }

  async getRecentSimulations(limit) {
    return [
      {
        id: 1,
        projectName: 'CPU Core - 5nm',
        type: 'Circuit Analysis',
        status: 'completed',
        timestamp: new Date(),
        duration: 2300,
        results: {
          metrics: {
            frequency: 2.4e9,
            power: 45e-9,
            health: 94.5,
          },
        },
      },
      {
        id: 2,
        projectName: 'Memory Controller',
        type: 'Optimization',
        status: 'running',
        timestamp: new Date(Date.now() - 60000),
        duration: 60000,
        results: {
          metrics: {
            frequency: 1.8e9,
            power: 32e-9,
            health: 91.2,
          },
        },
      },
    ].slice(0, limit);
  }

  async getProjectSimulations(projectId) {
    return await this.getRecentSimulations(50);
  }

  async getOptimizationSuggestions() {
    return [
      {
        id: 'opt1',
        title: 'Increase Transistor Sizing',
        description: 'Increase Wn/Wp ratio for better frequency',
        expectedImprovement: 12,
      },
      {
        id: 'opt2',
        title: 'Optimize Supply Voltage',
        description: 'Reduce Vdd to 1.1V for lower power',
        expectedImprovement: 18,
      },
    ];
  }

  async getBaselineMetrics() {
    return {
      frequency: 1.8e9,
      power: 50e-9,
      health: 92.0,
      cost: 150,
      params: { wn: 0.5, wp: 1.0, vdd: 1.2 },
    };
  }

  async getOptimizedMetrics() {
    return {
      frequency: 2.0e9,
      power: 41e-9,
      health: 95.5,
      cost: 160,
      params: { wn: 0.65, wp: 1.25, vdd: 1.15 },
    };
  }

  selectProject(projectId) {
    this.currentProject = { id: projectId };
  }

  onSimulationComplete(data) {
    this.simulations.unshift(data);
    if (this.activeTab === 'simulations') {
      this.loadSimulations();
    }
  }
}

// Export or use globally
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ProductionDashboard;
} else {
  window.ProductionDashboard = ProductionDashboard;
}
