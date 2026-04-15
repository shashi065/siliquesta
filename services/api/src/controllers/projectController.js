import ProjectService from '../services/projectService.js';

export class ProjectController {
  /**
   * Create a new project
   * POST /api/projects
   */
  static createProject = async (req, res, next) => {
    try {
      const userId = req.user.userId;
      const data = req.validatedData;

      const project = await ProjectService.createProject(userId, data);

      res.status(201).json({
        message: 'Project created successfully',
        project,
      });
    } catch (error) {
      next(error);
    }
  };

  /**
   * Get all projects for current user
   * GET /api/projects
   */
  static getProjects = async (req, res, next) => {
    try {
      const userId = req.user.userId;
      const query = req.validatedQuery;

      const result = await ProjectService.getUserProjects(userId, query);

      res.status(200).json({
        message: 'Projects retrieved successfully',
        ...result,
      });
    } catch (error) {
      next(error);
    }
  };

  /**
   * Get single project by ID
   * GET /api/projects/:id
   */
  static getProjectById = async (req, res, next) => {
    try {
      const userId = req.user.userId;
      const { id } = req.params;

      const project = await ProjectService.getProjectById(id, userId);

      res.status(200).json({
        message: 'Project retrieved successfully',
        project,
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
   * Update project
   * PATCH /api/projects/:id
   */
  static updateProject = async (req, res, next) => {
    try {
      const userId = req.user.userId;
      const { id } = req.params;
      const data = req.validatedData;

      const project = await ProjectService.updateProject(id, userId, data);

      res.status(200).json({
        message: 'Project updated successfully',
        project,
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
   * Delete project
   * DELETE /api/projects/:id
   */
  static deleteProject = async (req, res, next) => {
    try {
      const userId = req.user.userId;
      const { id } = req.params;

      await ProjectService.deleteProject(id, userId);

      res.status(200).json({
        message: 'Project deleted successfully',
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
   * Get project statistics
   * GET /api/projects/:id/stats
   */
  static getProjectStats = async (req, res, next) => {
    try {
      const userId = req.user.userId;
      const { id } = req.params;

      const stats = await ProjectService.getProjectStats(id, userId);

      res.status(200).json({
        message: 'Project statistics retrieved successfully',
        stats,
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
}

export default ProjectController;
