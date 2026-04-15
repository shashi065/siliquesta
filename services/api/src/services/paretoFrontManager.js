/**
 * Pareto Front Manager
 * Tracks and updates the Pareto frontier as solutions are generated
 */

export class ParetoFrontManager {
  constructor() {
    this.solutions = [];
    this.diversity = {
      spatialDiversity: 0,
      objectiveDiversity: 0,
    };
  }

  /**
   * Determine if a solution dominates another (for minimization)
   */
  static dominates(sol1, sol2) {
    // sol1 dominates sol2 if:
    // 1. It's better in at least one objective
    // 2. It's not worse in any objective
    let atLeastOneBetter = false;

    for (const key of ['power', 'delay', 'area']) {
      const val1 = sol1.metrics?.[key] ?? sol1[key];
      const val2 = sol2.metrics?.[key] ?? sol2[key];

      if (val1 > val2) {
        return false; // sol1 is worse in this objective
      }
      if (val1 < val2) {
        atLeastOneBetter = true; // sol1 is better in this objective
      }
    }

    return atLeastOneBetter;
  }

  /**
   * Add a solution and update Pareto front
   */
  addSolution(solution, metrics) {
    const candidate = {
      params: { ...solution },
      metrics: { ...metrics },
      timestamp: Date.now(),
      id: this.solutions.length,
    };

    // Remove dominated solutions
    this.solutions = this.solutions.filter(
      (existing) => !ParetoFrontManager.dominates(candidate, existing)
    );

    // Check if candidate is dominated by any existing solution
    const isDominated = this.solutions.some(
      (existing) => ParetoFrontManager.dominates(existing, candidate)
    );

    if (!isDominated) {
      this.solutions.push(candidate);
      this._updateDiversity();
      return true; // Solution was added to Pareto front
    }

    return false; // Solution was dominated
  }

  /**
   * Get current Pareto front
   */
  getParetoFront() {
    return this.solutions.map((sol) => ({
      params: sol.params,
      metrics: sol.metrics,
      id: sol.id,
    }));
  }

  /**
   * Get Pareto front summary for streaming
   */
  getStreamUpdate() {
    return {
      size: this.solutions.length,
      hypervolume: this._calculateHypervolume(),
      spreadMetric: this._calculateSpreadMetric(),
      diversity: this.diversity,
      fronts: this.solutions.slice(-5).map((sol) => ({
        params: this._roundParams(sol.params),
        metrics: this._roundMetrics(sol.metrics),
        crowdingDistance: this._calculateCrowdingDistance(sol),
      })),
    };
  }

  /**
   * Calculate hypervolume (approximation)
   */
  _calculateHypervolume() {
    if (this.solutions.length === 0) return 0;

    let volume = 0;
    const sorted = [...this.solutions].sort(
      (a, b) => a.metrics.power - b.metrics.power
    );

    for (let i = 0; i < sorted.length; i++) {
      const powerDelta = /**/ i === 0 ? sorted[i].metrics.power : sorted[i].metrics.power - sorted[i - 1].metrics.power;
      const delayMax = Math.max(
        ...sorted.slice(0, i + 1).map((s) => s.metrics.delay)
      );
      volume += powerDelta * delayMax;
    }

    return Math.round(volume * 100) / 100;
  }

  /**
   * Calculate spread metric (coverage of objective space)
   */
  _calculateSpreadMetric() {
    if (this.solutions.length < 2) return 0;

    const powers = this.solutions.map((s) => s.metrics.power);
    const delays = this.solutions.map((s) => s.metrics.delay);

    const powerSpread = Math.max(...powers) - Math.min(...powers);
    const delaySpread = Math.max(...delays) - Math.min(...delays);

    return Math.round((powerSpread + delaySpread) * 100) / 100;
  }

  /**
   * Update diversity metrics
   */
  _updateDiversity() {
    if (this.solutions.length < 2) {
      this.diversity = { spatialDiversity: 0, objectiveDiversity: 0 };
      return;
    }

    // Spatial diversity: average distance in parameter space
    let spatialDist = 0;
    for (let i = 0; i < this.solutions.length - 1; i++) {
      const p1 = this.solutions[i].params;
      const p2 = this.solutions[i + 1].params;
      const dist = Math.sqrt(
        Math.pow(p1.W - p2.W, 2) +
        Math.pow(p1.L - p2.L, 2) +
        Math.pow(p1.V - p2.V, 2)
      );
      spatialDist += dist;
    }

    // Objective diversity: variance in metrics
    const metrics = ['power', 'delay', 'area'];
    let objectiveDist = 0;
    for (const metric of metrics) {
      const values = this.solutions.map((s) => s.metrics[metric]);
      const mean = values.reduce((a, b) => a + b, 0) / values.length;
      const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
      objectiveDist += Math.sqrt(variance);
    }

    this.diversity = {
      spatialDiversity: Math.round((spatialDist / this.solutions.length) * 100) / 100,
      objectiveDiversity: Math.round((objectiveDist / metrics.length) * 100) / 100,
    };
  }

  /**
   * Calculate crowding distance for a solution
   */
  _calculateCrowdingDistance(solution) {
    const distances = [];

    for (const objective of ['power', 'delay', 'area']) {
      const values = this.solutions.map((s) => s.metrics[objective]).sort((a, b) => a - b);
      const minVal = values[0];
      const maxVal = values[values.length - 1];

      const idx = values.indexOf(solution.metrics[objective]);
      const distance =
        idx === 0 || idx === values.length - 1
          ? Infinity
          : (values[idx + 1] - values[idx - 1]) / (maxVal - minVal || 1);

      distances.push(distance);
    }

    return Math.min(...distances);
  }

  /**
   * Helper: round parameters
   */
  _roundParams(params) {
    return {
      W: Math.round(params.W * 100) / 100,
      L: Math.round(params.L * 100) / 100,
      V: Math.round(params.V * 100) / 100,
    };
  }

  /**
   * Helper: round metrics
   */
  _roundMetrics(metrics) {
    return {
      power: Math.round(metrics.power * 100) / 100,
      delay: Math.round(metrics.delay * 100) / 100,
      area: Math.round(metrics.area * 100) / 100,
      gain: Math.round(metrics.gain * 100) / 100,
      current: Math.round(metrics.current * 100) / 100,
      voltage: Math.round(metrics.voltage * 100) / 100,
    };
  }

  /**
   * Get all solutions for analysis
   */
  getAllSolutions() {
    return this.solutions;
  }

  /**
   * Clear the front
   */
  reset() {
    this.solutions = [];
    this.diversity = { spatialDiversity: 0, objectiveDiversity: 0 };
  }
}
