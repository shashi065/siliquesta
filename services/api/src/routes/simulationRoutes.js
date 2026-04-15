import express from 'express';
import { authenticate } from '../middleware/auth.js';
import { validateBody, validateQuery } from '../middleware/validation.js';
import {
  simulationValidationSchemas,
} from '../utils/validators.js';
import SimulationController from '../controllers/simulationController.js';

const router = express.Router();

/**
 * Simulation Routes
 * POST /api/simulations - Create simulation (requires projectId in body or query)
 * GET /api/simulations - Get simulations for a project
 * GET /api/simulations/:id - Get simulation
 * PATCH /api/simulations/:id - Update simulation
 * DELETE /api/simulations/:id - Delete simulation
 * POST /api/simulations/:id/run - Run simulation
 * GET /api/simulations/:id/results - Get results
 */

// All routes require authentication
router.use(authenticate);

// Create simulation
// Requires projectId in the body or query params
router.post(
  '/',
  validateBody(simulationValidationSchemas.create),
  (req, res, next) => {
    // Add projectId to params if provided in body or query
    if (req.body.projectId) {
      req.params.projectId = req.body.projectId;
    } else if (req.query.projectId) {
      req.params.projectId = req.query.projectId;
    }
    next();
  },
  SimulationController.createSimulation
);

// Get simulations for a project
router.get(
  '/',
  validateQuery(simulationValidationSchemas.query),
  SimulationController.getSimulations
);

// Get simulation by ID
router.get('/:id', SimulationController.getSimulationById);

// Run simulation
router.post('/:id/run', SimulationController.runSimulation);

// Get simulation results
router.get('/:id/results', SimulationController.getSimulationResults);

// Update simulation
router.patch(
  '/:id',
  validateBody(simulationValidationSchemas.update),
  SimulationController.updateSimulation
);

// Delete simulation
router.delete('/:id', SimulationController.deleteSimulation);

export default router;
