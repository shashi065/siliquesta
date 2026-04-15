import express from 'express';
import { authenticate } from '../middleware/auth.js';
import { validateBody, validateQuery } from '../middleware/validation.js';
import {
  projectValidationSchemas,
} from '../utils/validators.js';
import ProjectController from '../controllers/projectController.js';

const router = express.Router();

/**
 * Project Routes
 * POST /api/projects - Create project
 * GET /api/projects - Get all projects
 * GET /api/projects/:id - Get project
 * PATCH /api/projects/:id - Update project
 * DELETE /api/projects/:id - Delete project
 * GET /api/projects/:id/stats - Get project stats
 */

// All routes require authentication
router.use(authenticate);

// Create project
router.post(
  '/',
  validateBody(projectValidationSchemas.create),
  ProjectController.createProject
);

// Get all projects with filtering and pagination
router.get(
  '/',
  validateQuery(projectValidationSchemas.query),
  ProjectController.getProjects
);

// Get project by ID
router.get('/:id', ProjectController.getProjectById);

// Get project statistics
router.get('/:id/stats', ProjectController.getProjectStats);

// Update project
router.patch(
  '/:id',
  validateBody(projectValidationSchemas.update),
  ProjectController.updateProject
);

// Delete project
router.delete('/:id', ProjectController.deleteProject);

export default router;
