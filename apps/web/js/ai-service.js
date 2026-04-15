/**
 * AI Optimization Service - Call Python FastAPI optimization service
 */
class AIOptimizationService {
  constructor() {
    this.aiBaseUrl = API_CONFIG.AI_SERVICE_URL;
  }

  /**
   * Make request to AI service
   */
  async request(endpoint, options = {}) {
    const url = `${this.aiBaseUrl}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`AI Service error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`AI Service Error [${endpoint}]:`, error);
      throw error;
    }
  }

  /**
   * Check AI service health
   */
  async checkHealth() {
    try {
      return await this.request('/health');
    } catch (error) {
      console.warn('AI Service health check failed:', error);
      return null;
    }
  }

  /**
   * Optimize circuit parameters
   */
  async optimize(parameters, objectives = {}) {
    try {
      const payload = {
        parameters: {
          W_L_ratio: parameters.W_L_ratio || 10,
          finger_ratio: parameters.finger_ratio || 1,
          supply_voltage: parameters.supply_voltage || 1.8,
          operating_frequency: parameters.operating_frequency || 1e9,
          load_capacitance: parameters.load_capacitance || 1e-12,
          technology_node: parameters.technology_node || 28e-9,
          temperature: parameters.temperature || 27,
          bias_current: parameters.bias_current || 1e-6,
          ...(parameters.power_budget && { power_budget: parameters.power_budget }),
          ...(parameters.area_budget && { area_budget: parameters.area_budget }),
        },
        objectives: {
          minimize_power: objectives.minimize_power ?? true,
          minimize_area: objectives.minimize_area ?? false,
          maximize_speed: objectives.maximize_speed ?? true,
          maximize_gain: objectives.maximize_gain ?? false,
        },
        method: objectives.method || 'scipy',
        max_iterations: objectives.max_iterations || 500,
        tolerance: objectives.tolerance || 1e-6,
      };

      const response = await fetch(`${this.aiBaseUrl}/optimize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || `AI optimization failed: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('AI Optimization Error:', error);
      throw error;
    }
  }

  /**
   * Format optimization results
   */
  formatResults(optimizationResult) {
    if (!optimizationResult.success) {
      return null;
    }

    return {
      optimizedParams: optimizationResult.optimized_parameters,
      improvement: optimizationResult.overall_improvement,
      metrics: {
        original: optimizationResult.metrics_comparison.original,
        optimized: optimizationResult.metrics_comparison.optimized,
        improvements: optimizationResult.metrics_comparison.improvements,
      },
      executionTime: optimizationResult.execution_time,
      converged: optimizationResult.convergence,
    };
  }
}

// Global instance
window.aiService = new AIOptimizationService();
