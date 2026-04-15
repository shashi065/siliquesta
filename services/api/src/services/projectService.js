import { prisma } from '../config/database.js';
import { generateSlug } from '../utils/validators.js';

export class ProjectService {
  /**
   * Create a new project
   * @param {String} userId - User ID
   * @param {Object} data - Project data
   * @returns {Promise<Object>} - Created project
   */
  static async createProject(userId, data) {
    const { title, description, parameters, metadata } = data;

    // Generate unique slug
    let slug = generateSlug(title);
    let isSlugUnique = false;
    let counter = 1;

    while (!isSlugUnique) {
      const existing = await prisma.project.findUnique({
        where: { slug },
      });

      if (!existing) {
        isSlugUnique = true;
      } else {
        slug = `${generateSlug(title)}-${counter}`;
        counter++;
      }
    }

    const project = await prisma.project.create({
      data: {
        title,
        description,
        slug,
        userId,
        parameters: parameters || null,
        metadata: metadata || null,
      },
    });

    return project;
  }

  /**
   * Get project by ID
   * @param {String} projectId - Project ID
   * @param {String} userId - User ID (for authorization check)
   * @returns {Promise<Object>} - Project data
   */
  static async getProjectById(projectId, userId) {
    const project = await prisma.project.findFirst({
      where: {
        id: projectId,
        userId,
      },
      include: {
        simulations: {
          select: {
            id: true,
            title: true,
            status: true,
            createdAt: true,
          },
          orderBy: { createdAt: 'desc' },
          take: 5,
        },
      },
    });

    if (!project) {
      throw new Error('Project not found or unauthorized');
    }

    return project;
  }

  /**
   * Get all projects for a user with pagination
   * @param {String} userId - User ID
   * @param {Object} options - Query options (page, limit, status, search)
   * @returns {Promise<Object>} - Projects and pagination info
   */
  static async getUserProjects(userId, options = {}) {
    const {
      page = 1,
      limit = 10,
      status = 'active',
      search = '',
    } = options;

    const skip = (page - 1) * limit;

    const where = {
      userId,
      ...(status && { status }),
      ...(search && {
        OR: [
          { title: { contains: search, mode: 'insensitive' } },
          { description: { contains: search, mode: 'insensitive' } },
        ],
      }),
    };

    const [projects, total] = await Promise.all([
      prisma.project.findMany({
        where,
        skip,
        take: limit,
        orderBy: { createdAt: 'desc' },
      }),
      prisma.project.count({ where }),
    ]);

    return {
      data: projects,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit),
      },
    };
  }

  /**
   * Update project
   * @param {String} projectId - Project ID
   * @param {String} userId - User ID (for authorization check)
   * @param {Object} data - Update data
   * @returns {Promise<Object>} - Updated project
   */
  static async updateProject(projectId, userId, data) {
    // Verify ownership
    const project = await prisma.project.findFirst({
      where: {
        id: projectId,
        userId,
      },
    });

    if (!project) {
      throw new Error('Project not found or unauthorized');
    }

    const updatedProject = await prisma.project.update({
      where: { id: projectId },
      data: {
        ...(data.title && { title: data.title }),
        ...(data.description !== undefined && { description: data.description }),
        ...(data.status && { status: data.status }),
        ...(data.parameters && { parameters: data.parameters }),
        ...(data.metadata && { metadata: data.metadata }),
      },
    });

    return updatedProject;
  }

  /**
   * Delete project
   * @param {String} projectId - Project ID
   * @param {String} userId - User ID (for authorization check)
   * @returns {Promise<void>}
   */
  static async deleteProject(projectId, userId) {
    const project = await prisma.project.findFirst({
      where: {
        id: projectId,
        userId,
      },
    });

    if (!project) {
      throw new Error('Project not found or unauthorized');
    }

    await prisma.project.delete({
      where: { id: projectId },
    });
  }

  /**
   * Get project statistics
   * @param {String} projectId - Project ID
   * @param {String} userId - User ID
   * @returns {Promise<Object>} - Project statistics
   */
  static async getProjectStats(projectId, userId) {
    const project = await prisma.project.findFirst({
      where: {
        id: projectId,
        userId,
      },
    });

    if (!project) {
      throw new Error('Project not found or unauthorized');
    }

    const simulations = await prisma.simulation.groupBy({
      by: ['status'],
      where: { projectId },
      _count: true,
    });

    const stats = {
      total: 0,
      completed: 0,
      running: 0,
      failed: 0,
      pending: 0,
    };

    simulations.forEach((stat) => {
      stats.total += stat._count;
      stats[stat.status] = stat._count;
    });

    return stats;
  }
}

export default ProjectService;
