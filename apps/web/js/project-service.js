/**
 * Projects Service - Handle project management (CRUD operations)
 */
class ProjectService {
  constructor() {
    this.api = new APIClient();
  }

  /**
   * Create new project with circuit JSON
   */
  async createProject(title, description, circuitData) {
    try {
      const response = await this.api.post('/projects', {
        title,
        description,
        parameters: circuitData,
        metadata: {
          createdFrom: 'frontend',
          timestamp: new Date().toISOString(),
        },
      });

      return response.project;
    } catch (error) {
      console.error('Error creating project:', error);
      throw error;
    }
  }

  /**
   * Get all user projects
   */
  async getProjects(page = 1, limit = 10, status = 'active', search = '') {
    try {
      const params = new URLSearchParams({
        page,
        limit,
        status,
        ...(search && { search }),
      });

      const response = await this.api.get(`/projects?${params}`);
      return response;
    } catch (error) {
      console.error('Error fetching projects:', error);
      throw error;
    }
  }

  /**
   * Get single project
   */
  async getProject(projectId) {
    try {
      const response = await this.api.get(`/projects/${projectId}`);
      return response.project;
    } catch (error) {
      console.error('Error fetching project:', error);
      throw error;
    }
  }

  /**
   * Update project
   */
  async updateProject(projectId, updates) {
    try {
      const response = await this.api.patch(`/projects/${projectId}`, updates);
      return response.project;
    } catch (error) {
      console.error('Error updating project:', error);
      throw error;
    }
  }

  /**
   * Delete project
   */
  async deleteProject(projectId) {
    try {
      await this.api.delete(`/projects/${projectId}`);
      return true;
    } catch (error) {
      console.error('Error deleting project:', error);
      throw error;
    }
  }

  /**
   * Get project statistics
   */
  async getProjectStats(projectId) {
    try {
      const response = await this.api.get(`/projects/${projectId}/stats`);
      return response.stats;
    } catch (error) {
      console.error('Error fetching project stats:', error);
      throw error;
    }
  }

  /**
   * Share project with another user
   */
  async shareProject(projectId, collaboratorEmail, role = 'viewer') {
    try {
      const response = await this.api.post(`/projects/${projectId}/share`, {
        collaborator_email: collaboratorEmail,
        role
      });
      return response;
    } catch (error) {
      console.error('Error sharing project:', error);
      throw error;
    }
  }

  /**
   * List all collaborators on a project
   */
  async getProjectCollaborators(projectId) {
    try {
      const response = await this.api.get(`/projects/${projectId}/shares`);
      return response;
    } catch (error) {
      console.error('Error fetching collaborators:', error);
      throw error;
    }
  }

  /**
   * Update collaborator role
   */
  async updateCollaboratorRole(projectId, shareId, newRole) {
    try {
      const response = await this.api.put(`/projects/${projectId}/shares/${shareId}`, {
        role: newRole
      });
      return response;
    } catch (error) {
      console.error('Error updating collaborator:', error);
      throw error;
    }
  }

  /**
   * Remove collaborator from project
   */
  async removeCollaborator(projectId, shareId) {
    try {
      await this.api.delete(`/projects/${projectId}/shares/${shareId}`);
      return true;
    } catch (error) {
      console.error('Error removing collaborator:', error);
      throw error;
    }
  }

  /**
   * Get all projects shared with the current user
   */
  async getSharedProjects() {
    try {
      const response = await this.api.get('/projects/shared');
      return response;
    } catch (error) {
      console.error('Error fetching shared projects:', error);
      throw error;
    }
  }
}

// Global instance
window.projectService = new ProjectService();
