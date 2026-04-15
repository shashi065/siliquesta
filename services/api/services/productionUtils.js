/**
 * SILIQUESTA - Production Backend Utilities
 * Comprehensive validation, logging, error handling, and middleware
 */

const LOG_LEVELS = {
  DEBUG: 'DEBUG',
  INFO: 'INFO',
  WARN: 'WARN',
  ERROR: 'ERROR',
  FATAL: 'FATAL',
};

/**
 * Production-Grade Logger
 */
class Logger {
  constructor(module = 'SILIQUESTA') {
    this.module = module;
    this.logs = [];
    this.maxLogs = 10000;
  }

  log(level, message, data = null) {
    const timestamp = new Date().toISOString();
    const logEntry = {
      timestamp,
      level,
      module: this.module,
      message,
      data,
    };

    // Store in memory (typically would go to ELK, Datadog, etc.)
    this.logs.push(logEntry);
    if (this.logs.length > this.maxLogs) this.logs.shift();

    // Console output with color
    const colors = {
      DEBUG: '\x1b[36m',
      INFO: '\x1b[32m',
      WARN: '\x1b[33m',
      ERROR: '\x1b[31m',
      FATAL: '\x1b[41m',
    };

    const color = colors[level] || '';
    const reset = '\x1b[0m';
    console.log(
      `${color}[${timestamp}] [${level}] ${this.module}: ${message}${reset}`,
      data || ''
    );

    // Send to external logging service in production
    if (process.env.LOG_SERVICE_URL) {
      this.sendToExternalService(logEntry);
    }
  }

  debug(message, data) { this.log(LOG_LEVELS.DEBUG, message, data); }
  info(message, data) { this.log(LOG_LEVELS.INFO, message, data); }
  warn(message, data) { this.log(LOG_LEVELS.WARN, message, data); }
  error(message, data) { this.log(LOG_LEVELS.ERROR, message, data); }
  fatal(message, data) { this.log(LOG_LEVELS.FATAL, message, data); }

  async sendToExternalService(logEntry) {
    try {
      await fetch(process.env.LOG_SERVICE_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(logEntry),
      });
    } catch (err) {
      // Silently fail - don't break application if logging fails
    }
  }

  getLogs(filter = {}) {
    let filtered = this.logs;

    if (filter.level) {
      filtered = filtered.filter(log => log.level === filter.level);
    }

    if (filter.module) {
      filtered = filtered.filter(log => log.module === filter.module);
    }

    if (filter.since) {
      const sinceTime = new Date(filter.since).getTime();
      filtered = filtered.filter(log => new Date(log.timestamp).getTime() >= sinceTime);
    }

    return filtered;
  }
}

/**
 * Request/Response Validation using Joi patterns
 */
class Validator {
  static schemas = {
    project: {
      create: {
        name: { required: true, type: 'string', min: 1, max: 255 },
        description: { required: false, type: 'string', max: 1000 },
      },
      update: {
        name: { required: false, type: 'string', min: 1, max: 255 },
        description: { required: false, type: 'string', max: 1000 },
      },
    },
    simulation: {
      run: {
        projectId: { required: true, type: 'integer', positive: true },
        parameters: {
          required: true,
          type: 'object',
          properties: {
            wn: { type: 'number', min: 0.1, max: 10 },
            wp: { type: 'number', min: 0.1, max: 10 },
            vdd: { type: 'number', min: 0.8, max: 3.3 },
            temp: { type: 'number', min: -40, max: 150 },
            cl: { type: 'number', min: 1e-12, max: 1e-9 },
          },
        },
      },
    },
    sharing: {
      share: {
        collaboratorEmail: { required: true, type: 'email' },
        role: { required: true, type: 'string', enum: ['viewer', 'editor', 'admin'] },
      },
    },
  };

  static validate(data, schema) {
    const errors = [];

    if (!schema) {
      return { valid: false, errors: ['Unknown schema'] };
    }

    for (const [field, rules] of Object.entries(schema)) {
      const value = data[field];

      // Check required
      if (rules.required && (value === undefined || value === null || value === '')) {
        errors.push(`${field} is required`);
        continue;
      }

      if (value === undefined || value === null) continue;

      // Check type
      if (rules.type && typeof value !== rules.type) {
        errors.push(`${field} must be ${rules.type}`);
      }

      // Check string constraints
      if (rules.type === 'string') {
        if (rules.min && value.length < rules.min) {
          errors.push(`${field} must be at least ${rules.min} characters`);
        }
        if (rules.max && value.length > rules.max) {
          errors.push(`${field} must be at most ${rules.max} characters`);
        }
      }

      // Check number constraints
      if (rules.type === 'number') {
        if (rules.min !== undefined && value < rules.min) {
          errors.push(`${field} must be >= ${rules.min}`);
        }
        if (rules.max !== undefined && value > rules.max) {
          errors.push(`${field} must be <= ${rules.max}`);
        }
        if (rules.positive && value <= 0) {
          errors.push(`${field} must be positive`);
        }
      }

      // Check enum
      if (rules.enum && !rules.enum.includes(value)) {
        errors.push(`${field} must be one of: ${rules.enum.join(', ')}`);
      }

      // Check email
      if (rules.type === 'email') {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
          errors.push(`${field} must be valid email`);
        }
      }
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  static validateProject(data, action = 'create') {
    const schema = this.schemas.project[action];
    return this.validate(data, schema);
  }

  static validateSimulation(data) {
    const schema = this.schemas.simulation.run;
    return this.validate(data, schema);
  }

  static validateSharing(data) {
    const schema = this.schemas.sharing.share;
    return this.validate(data, schema);
  }
}

/**
 * Custom Application Errors
 */
class AppError extends Error {
  constructor(message, statusCode = 500, errorCode = 'INTERNAL_ERROR', context = {}) {
    super(message);
    this.statusCode = statusCode;
    this.errorCode = errorCode;
    this.context = context;
    this.timestamp = new Date().toISOString();
  }

  toJSON() {
    return {
      error: {
        message: this.message,
        code: this.errorCode,
        statusCode: this.statusCode,
        timestamp: this.timestamp,
        context: this.context,
      },
    };
  }
}

class ValidationError extends AppError {
  constructor(message, errors = []) {
    super(message, 400, 'VALIDATION_ERROR', { errors });
  }
}

class AuthenticationError extends AppError {
  constructor(message = 'Authentication failed') {
    super(message, 401, 'AUTH_ERROR');
  }
}

class AuthorizationError extends AppError {
  constructor(message = 'Not authorized') {
    super(message, 403, 'FORBIDDEN');
  }
}

class NotFoundError extends AppError {
  constructor(resource = 'Resource') {
    super(`${resource} not found`, 404, 'NOT_FOUND');
  }
}

class ConflictError extends AppError {
  constructor(message) {
    super(message, 409, 'CONFLICT');
  }
}

/**
 * Express Middleware Factory
 */
function createErrorHandler(logger) {
  return (err, req, res, next) => {
    logger.error('Request error', {
      path: req.path,
      method: req.method,
      error: err.message,
      stack: process.env.NODE_ENV === 'development' ? err.stack : undefined,
    });

    if (err instanceof AppError) {
      return res.status(err.statusCode).json(err.toJSON());
    }

    // Generic error
    res.status(500).json({
      error: {
        message: 'Internal server error',
        code: 'INTERNAL_ERROR',
        statusCode: 500,
      },
    });
  };
}

function createRequestLogger(logger) {
  return (req, res, next) => {
    const start = Date.now();

    res.on('finish', () => {
      const duration = Date.now() - start;
      const level = res.statusCode >= 400 ? 'WARN' : 'INFO';

      logger.log(level, `${req.method} ${req.path}`, {
        statusCode: res.statusCode,
        duration: `${duration}ms`,
        userId: req.userId,
      });
    });

    next();
  };
}

function createValidationMiddleware(logger) {
  return (schema, action = 'create') => {
    return (req, res, next) => {
      const data = req.body;

      if (action === 'project') {
        const result = Validator.validateProject(data, action);
        if (!result.valid) {
          return next(new ValidationError('Invalid project data', result.errors));
        }
      } else if (action === 'simulation') {
        const result = Validator.validateSimulation(data);
        if (!result.valid) {
          return next(new ValidationError('Invalid simulation data', result.errors));
        }
      } else if (action === 'sharing') {
        const result = Validator.validateSharing(data);
        if (!result.valid) {
          return next(new ValidationError('Invalid sharing data', result.errors));
        }
      }

      next();
    };
  };
}

/**
 * Project Versioning System
 */
class ProjectVersioning {
  constructor(db) {
    this.db = db;
  }

  async saveVersion(projectId, changes, userId, description = '') {
    const version = {
      projectId,
      userId,
      description,
      changes,
      timestamp: new Date().toISOString(),
      changeType: description.includes('deleted') ? 'delete' : 'update',
      metadata: {
        fieldsChanged: Object.keys(changes),
        changeCount: Object.keys(changes).length,
      },
    };

    // Store in database (example schema)
    // await this.db.query(
    //   'INSERT INTO project_versions (project_id, user_id, changes, description, created_at) VALUES ($1, $2, $3, $4, NOW())',
    //   [projectId, userId, JSON.stringify(changes), description]
    // );

    return version;
  }

  async getHistory(projectId, limit = 50) {
    // const result = await this.db.query(
    //   'SELECT * FROM project_versions WHERE project_id = $1 ORDER BY created_at DESC LIMIT $2',
    //   [projectId, limit]
    // );
    // return result.rows;
    return [];
  }

  async rollback(projectId, versionId) {
    // Implement rollback logic
    return { success: true };
  }
}

/**
 * Simulation History Tracking
 */
class SimulationHistory {
  constructor(db) {
    this.db = db;
  }

  async recordSimulation(projectId, userId, params, results, duration) {
    const record = {
      projectId,
      userId,
      parameters: params,
      results,
      duration,
      timestamp: new Date().toISOString(),
      status: 'completed',
      qualityScore: this.calculateQualityScore(results),
    };

    // Store in database
    // await this.db.query(
    //   'INSERT INTO simulation_history (project_id, user_id, parameters, results, duration, quality_score) VALUES ($1, $2, $3, $4, $5, $6)',
    //   [projectId, userId, JSON.stringify(params), JSON.stringify(results), duration, record.qualityScore]
    // );

    return record;
  }

  calculateQualityScore(results) {
    // Simple scoring based on results
    let score = 50;

    if (results.metrics) {
      if (results.metrics.frequency > 1e6) score += 20;
      if (results.metrics.power < 100e-9) score += 15;
      if (results.metrics.health > 90) score += 15;
    }

    return Math.min(100, score);
  }

  async getProjectSimulations(projectId, limit = 100) {
    // const result = await this.db.query(
    //   'SELECT * FROM simulation_history WHERE project_id = $1 ORDER BY timestamp DESC LIMIT $2',
    //   [projectId, limit]
    // );
    // return result.rows;
    return [];
  }

  async getSimulationTrend(projectId, timeWindow = '7d') {
    // Get simulation improvements over time
    return [];
  }
}

/**
 * Rate Limiting & Quota Management
 */
class RateLimiter {
  constructor(limits = {}) {
    this.limits = {
      simulationsPerHour: limits.simulationsPerHour || 100,
      projectsPerDay: limits.projectsPerDay || 50,
      requestsPerMinute: limits.requestsPerMinute || 60,
    };
    this.tracking = new Map();
  }

  checkLimit(userId, limitType) {
    const key = `${userId}:${limitType}`;
    const now = Date.now();
    const window = limitType === 'requestsPerMinute' ? 60000 : limitType === 'simulationsPerHour' ? 3600000 : 86400000;

    if (!this.tracking.has(key)) {
      this.tracking.set(key, []);
    }

    const requests = this.tracking.get(key).filter(timestamp => now - timestamp < window);
    const limit = this.limits[limitType] || 100;

    if (requests.length >= limit) {
      return {
        allowed: false,
        remaining: 0,
        resetTime: new Date(requests[0] + window),
      };
    }

    requests.push(now);
    this.tracking.set(key, requests);

    return {
      allowed: true,
      remaining: limit - requests.length,
      resetTime: new Date(now + window),
    };
  }
}

/**
 * Export all utilities
 */
module.exports = {
  Logger,
  Validator,
  AppError,
  ValidationError,
  AuthenticationError,
  AuthorizationError,
  NotFoundError,
  ConflictError,
  createErrorHandler,
  createRequestLogger,
  createValidationMiddleware,
  ProjectVersioning,
  SimulationHistory,
  RateLimiter,
  LOG_LEVELS,
};
