import SimulationService from '../services/simulationService.js';

export class SimulationController {
  /**
   * Create a new simulation
   * POST /api/simulations
   */
  static createSimulation = async (req, res, next) => {
    try {
      const userId = req.user.userId;
      const { projectId } = req.params;
      const data = req.validatedData;

      const simulation = await SimulationService.createSimulation(
        projectId,
        userId,
        data
      );

      res.status(201).json({
        message: 'Simulation created successfully',
        simulation,
      });
    } catch (error) {
      if (error.message.includes('not found')) {
        return res.status(404).json({
          error: 'Not Found',
          message: error.message,
        });
      }
      next(error);
    }
  };

  /**
   * Get all simulations for a project
   * GET /api/simulations?projectId=:id
   */
  static getSimulations = async (req, res, next) => {
    try {
      const userId = req.user.userId;
      const { projectId } = req.query;
      const query = req.validatedQuery;

      if (!projectId) {
        return res.status(400).json({
          error: 'Bad Request',
          message: 'projectId query parameter is required',
        });
      }

      const result = await SimulationService.getProjectSimulations(
        projectId,
        userId,
        query
      );

      res.status(200).json({
        message: 'Simulations retrieved successfully',
        ...result,
      });
    } catch (error) {
      if (error.message.includes('not found')) {
        return res.status(404).json({
          error: 'Not Found',
          message: error.message,
        });
      }
      next(error);
    }
  };

  /**
   * Get single simulation by ID
   * GET /api/simulations/:id
   */
  static getSimulationById = async (req, res, next) => {
    try {
      const userId = req.user.userId;
      const { id } = req.params;

      const simulation = await SimulationService.getSimulationById(id, userId);

      res.status(200).json({
        message: 'Simulation retrieved successfully',
        simulation,
      });
    } catch (error) {
      if (error.message.includes('not found')) {
        return res.status(404).json({
          error: 'Not Found',
          message: error.message,
        });
      }
      next(error);
    }
  };

  /**
   * Run simulation
   * POST /api/simulations/:id/run
   */
  static runSimulation = async (req, res, next) => {
    try {
      const userId = req.user.userId;
      const { id } = req.params;

      const simulation = await SimulationService.runSimulation(id, userId);

      res.status(200).json({
        message: 'Simulation completed successfully',
        simulation,
      });
    } catch (error) {
      if (error.message.includes('not found')) {
        return res.status(404).json({
          error: 'Not Found',
          message: error.message,
        });
      }

      if (
        error.message === 'Simulation is already running' ||
        error.message === 'Cannot restart completed simulation'
      ) {
        return res.status(409).json({
          error: 'Conflict',
          message: error.message,
        });
      }

      next(error);
    }
  };

  /**
   * Update simulation
   * PATCH /api/simulations/:id
   */
  static updateSimulation = async (req, res, next) => {
    try {
      const userId = req.user.userId;
      const { id } = req.params;
      const data = req.validatedData;

      const simulation = await SimulationService.updateSimulation(id, userId, data);

      res.status(200).json({
        message: 'Simulation updated successfully',
        simulation,
      });
    } catch (error) {
      if (error.message.includes('not found')) {
        return res.status(404).json({
          error: 'Not Found',
          message: error.message,
        });
      }
      next(error);
    }
  };

  /**
   * Delete simulation
   * DELETE /api/simulations/:id
   */
  static deleteSimulation = async (req, res, next) => {
    try {
      const userId = req.user.userId;
      const { id } = req.params;

      await SimulationService.deleteSimulation(id, userId);

      res.status(200).json({
        message: 'Simulation deleted successfully',
      });
    } catch (error) {
      if (error.message.includes('not found')) {
        return res.status(404).json({
          error: 'Not Found',
          message: error.message,
        });
      }
      next(error);
    }
  };

  /**
   * Get simulation results
   * GET /api/simulations/:id/results
   */
  static getSimulationResults = async (req, res, next) => {
    try {
      const userId = req.user.userId;
      const { id } = req.params;

      const results = await SimulationService.getSimulationResults(id, userId);

      res.status(200).json({
        message: 'Simulation results retrieved successfully',
        simulation: results,
      });
    } catch (error) {
      if (error.message.includes('not found')) {
        return res.status(404).json({
          error: 'Not Found',
          message: error.message,
        });
      }

      if (error.message === 'Simulation has not finished yet') {
        return res.status(409).json({
          error: 'Conflict',
          message: error.message,
        });
      }

      next(error);
    }
  };
}

export default SimulationController;
