import { prisma } from '../config/database.js';

const SIMULATION_TIMEOUT = parseInt(process.env.SIMULATION_TIMEOUT) || 30000;
const SIMULATION_MAX_ITERATIONS = parseInt(process.env.SIMULATION_MAX_ITERATIONS) || 10000;

export class SimulationService {
  /**
   * Create a new simulation
   * @param {String} projectId - Project ID
   * @param {String} userId - User ID
   * @param {Object} data - Simulation data
   * @returns {Promise<Object>} - Created simulation
   */
  static async createSimulation(projectId, userId, data) {
    const { title, description, input, parameters, config } = data;

    // Verify project ownership
    const project = await prisma.project.findFirst({
      where: {
        id: projectId,
        userId,
      },
    });

    if (!project) {
      throw new Error('Project not found or unauthorized');
    }

    const simulation = await prisma.simulation.create({
      data: {
        title,
        description,
        input,
        parameters: parameters || null,
        config: config || null,
        projectId,
        userId,
        status: 'pending',
      },
    });

    return simulation;
  }

  /**
   * Get simulation by ID
   * @param {String} simulationId - Simulation ID
   * @param {String} userId - User ID (for authorization check)
   * @returns {Promise<Object>} - Simulation data
   */
  static async getSimulationById(simulationId, userId) {
    const simulation = await prisma.simulation.findFirst({
      where: {
        id: simulationId,
        userId,
      },
      include: {
        project: {
          select: {
            id: true,
            title: true,
            slug: true,
          },
        },
      },
    });

    if (!simulation) {
      throw new Error('Simulation not found or unauthorized');
    }

    return simulation;
  }

  /**
   * Get all simulations for a project
   * @param {String} projectId - Project ID
   * @param {String} userId - User ID
   * @param {Object} options - Query options
   * @returns {Promise<Object>} - Simulations and pagination info
   */
  static async getProjectSimulations(projectId, userId, options = {}) {
    const {
      page = 1,
      limit = 10,
      status = null,
    } = options;

    const skip = (page - 1) * limit;

    // Verify project ownership
    const project = await prisma.project.findFirst({
      where: {
        id: projectId,
        userId,
      },
    });

    if (!project) {
      throw new Error('Project not found or unauthorized');
    }

    const where = {
      projectId,
      ...(status && { status }),
    };

    const [simulations, total] = await Promise.all([
      prisma.simulation.findMany({
        where,
        skip,
        take: limit,
        orderBy: { createdAt: 'desc' },
        select: {
          id: true,
          title: true,
          description: true,
          status: true,
          duration: true,
          createdAt: true,
          completedAt: true,
        },
      }),
      prisma.simulation.count({ where }),
    ]);

    return {
      data: simulations,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit),
      },
    };
  }

  /**
   * Run simulation (execute computation)
   * @param {String} simulationId - Simulation ID
   * @param {String} userId - User ID
   * @returns {Promise<Object>} - Updated simulation with results
   */
  static async runSimulation(simulationId, userId) {
    // Fetch simulation
    const simulation = await prisma.simulation.findFirst({
      where: {
        id: simulationId,
        userId,
      },
    });

    if (!simulation) {
      throw new Error('Simulation not found or unauthorized');
    }

    if (simulation.status === 'running') {
      throw new Error('Simulation is already running');
    }

    if (simulation.status === 'completed') {
      throw new Error('Cannot restart completed simulation');
    }

    try {
      // Mark as running
      await prisma.simulation.update({
        where: { id: simulationId },
        data: {
          status: 'running',
          startedAt: new Date(),
        },
      });

      const startTime = Date.now();

      // Execute simulation
      const result = await this.executeSimulation(simulation.input, simulation.parameters);

      const duration = Date.now() - startTime;

      // Update with results
      const updatedSimulation = await prisma.simulation.update({
        where: { id: simulationId },
        data: {
          status: 'completed',
          completedAt: new Date(),
          duration,
          output: result.output,
          results: result.metrics,
        },
      });

      return updatedSimulation;
    } catch (error) {
      // Mark as failed
      await prisma.simulation.update({
        where: { id: simulationId },
        data: {
          status: 'failed',
          error: error.message,
        },
      });

      throw error;
    }
  }

  /**
   * Execute the actual simulation computation
   * @param {Object} input - Simulation input
   * @param {Object} parameters - Simulation parameters
   * @returns {Promise<Object>} - Computation results
   */
  static async executeSimulation(input, parameters = {}) {
    // Basic simulation computation
    // This is a placeholder that can be replaced with actual ML/simulation logic

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Simulation timeout'));
      }, SIMULATION_TIMEOUT);

      try {
        // Simulate computation
        const iterations = Math.min(
          parameters.iterations || 100,
          SIMULATION_MAX_ITERATIONS
        );

        const output = {
          processedAt: new Date().toISOString(),
          iterationsCompleted: iterations,
          input,
        };

        // Basic metrics calculation
        const metrics = {
          convergence: Math.random() * 0.99 + 0.01,
          error: Math.random() * 0.1,
          accuracy: Math.random() * 0.95 + 0.05,
          iterationsRun: iterations,
          timestamp: new Date().toISOString(),
        };

        clearTimeout(timeout);
        resolve({ output, metrics });
      } catch (error) {
        clearTimeout(timeout);
        reject(error);
      }
    });
  }

  /**
   * Update simulation
   * @param {String} simulationId - Simulation ID
   * @param {String} userId - User ID
   * @param {Object} data - Update data
   * @returns {Promise<Object>} - Updated simulation
   */
  static async updateSimulation(simulationId, userId, data) {
    const simulation = await prisma.simulation.findFirst({
      where: {
        id: simulationId,
        userId,
      },
    });

    if (!simulation) {
      throw new Error('Simulation not found or unauthorized');
    }

    const updatedSimulation = await prisma.simulation.update({
      where: { id: simulationId },
      data: {
        ...(data.status && { status: data.status }),
        ...(data.output && { output: data.output }),
        ...(data.results && { results: data.results }),
      },
    });

    return updatedSimulation;
  }

  /**
   * Delete simulation
   * @param {String} simulationId - Simulation ID
   * @param {String} userId - User ID
   * @returns {Promise<void>}
   */
  static async deleteSimulation(simulationId, userId) {
    const simulation = await prisma.simulation.findFirst({
      where: {
        id: simulationId,
        userId,
      },
    });

    if (!simulation) {
      throw new Error('Simulation not found or unauthorized');
    }

    await prisma.simulation.delete({
      where: { id: simulationId },
    });
  }

  /**
   * Get simulation results by ID
   * @param {String} simulationId - Simulation ID
   * @param {String} userId - User ID
   * @returns {Promise<Object>} - Simulation results
   */
  static async getSimulationResults(simulationId, userId) {
    const simulation = await prisma.simulation.findFirst({
      where: {
        id: simulationId,
        userId,
      },
      select: {
        id: true,
        title: true,
        status: true,
        input: true,
        output: true,
        results: true,
        duration: true,
        error: true,
        createdAt: true,
        completedAt: true,
      },
    });

    if (!simulation) {
      throw new Error('Simulation not found or unauthorized');
    }

    if (simulation.status !== 'completed' && simulation.status !== 'failed') {
      throw new Error('Simulation has not finished yet');
    }

    return simulation;
  }
}

export default SimulationService;
