/**
 * Simulation Service - Handle simulation execution and results
 */
class SimulationService {
  constructor() {
    this.api = new APIClient();
  }

  /**
   * Create new simulation
   */
  async createSimulation(projectId, title, description, input, parameters = {}) {
    try {
      const response = await this.api.post('/simulations', {
        title,
        description,
        input,
        parameters,
        projectId,
      });

      return response.simulation;
    } catch (error) {
      console.error('Error creating simulation:', error);
      throw error;
    }
  }

  /**
   * Get simulations for a project
   */
  async getSimulations(projectId, page = 1, limit = 10, status = null) {
    try {
      const params = new URLSearchParams({
        projectId,
        page,
        limit,
        ...(status && { status }),
      });

      const response = await this.api.get(`/simulations?${params}`);
      return response;
    } catch (error) {
      console.error('Error fetching simulations:', error);
      throw error;
    }
  }

  /**
   * Get single simulation
   */
  async getSimulation(simulationId) {
    try {
      const response = await this.api.get(`/simulations/${simulationId}`);
      return response.simulation;
    } catch (error) {
      console.error('Error fetching simulation:', error);
      throw error;
    }
  }

  /**
   * Run simulation (execute)
   */
  async runSimulation(simulationId) {
    try {
      const response = await this.api.post(`/simulations/${simulationId}/run`, {});
      return response.simulation;
    } catch (error) {
      console.error('Error running simulation:', error);
      throw error;
    }
  }

  /**
   * Get simulation results
   */
  async getResults(simulationId) {
    try {
      const response = await this.api.get(`/simulations/${simulationId}/results`);
      return response.simulation;
    } catch (error) {
      console.error('Error fetching results:', error);
      throw error;
    }
  }

  /**
   * Update simulation
   */
  async updateSimulation(simulationId, updates) {
    try {
      const response = await this.api.patch(`/simulations/${simulationId}`, updates);
      return response.simulation;
    } catch (error) {
      console.error('Error updating simulation:', error);
      throw error;
    }
  }

  /**
   * Delete simulation
   */
  async deleteSimulation(simulationId) {
    try {
      await this.api.delete(`/simulations/${simulationId}`);
      return true;
    } catch (error) {
      console.error('Error deleting simulation:', error);
      throw error;
    }
  }

  /**
   * Format simulation results for display
   */
  formatResults(simulation) {
    if (!simulation.results) {
      return null;
    }

    return {
      gain: simulation.results?.original?.gain || 'N/A',
      power: simulation.results?.original?.power_consumption || 'N/A',
      delay: simulation.results?.original?.propagation_delay || 'N/A',
      area: simulation.results?.original?.area || 'N/A',
      convergence: simulation.results?.original?.convergence ?? true,
    };
  }
}

// Global instance
window.simulationService = new SimulationService();
