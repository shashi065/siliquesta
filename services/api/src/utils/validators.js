import Joi from 'joi';

// User Validation Schemas
export const userValidationSchemas = {
  signup: Joi.object({
    email: Joi.string().email().required(),
    name: Joi.string().min(2).max(50).required(),
    password: Joi.string().min(8).required(),
    confirmPassword: Joi.string().valid(Joi.ref('password')).optional(),
  }),

  login: Joi.object({
    email: Joi.string().email(),
    username: Joi.string().email(),
    password: Joi.string().required(),
  }).or('email', 'username'),

  update: Joi.object({
    email: Joi.string().email(),
    name: Joi.string().min(2).max(50),
    bio: Joi.string().max(500),
    avatar: Joi.string().uri(),
  }).min(1),
};

// Project Validation Schemas
export const projectValidationSchemas = {
  create: Joi.object({
    title: Joi.string().min(3).max(100).required(),
    description: Joi.string().max(500),
    parameters: Joi.object().optional(),
    metadata: Joi.object().optional(),
  }),

  update: Joi.object({
    title: Joi.string().min(3).max(100),
    description: Joi.string().max(500),
    status: Joi.string().valid('active', 'archived', 'deleted'),
    parameters: Joi.object().optional(),
    metadata: Joi.object().optional(),
  }).min(1),

  query: Joi.object({
    page: Joi.number().integer().min(1).default(1),
    limit: Joi.number().integer().min(1).max(100).default(10),
    status: Joi.string().valid('active', 'archived', 'deleted'),
    search: Joi.string().max(50),
  }),
};

// Simulation Validation Schemas
export const simulationValidationSchemas = {
  create: Joi.object({
    title: Joi.string().min(3).max(100).required(),
    description: Joi.string().max(500),
    input: Joi.object().required(),
    parameters: Joi.object().optional(),
    config: Joi.object().optional(),
  }),

  update: Joi.object({
    status: Joi.string().valid('pending', 'running', 'completed', 'failed'),
    output: Joi.object().optional(),
    results: Joi.object().optional(),
  }).min(1),

  query: Joi.object({
    page: Joi.number().integer().min(1).default(1),
    limit: Joi.number().integer().min(1).max(100).default(10),
    status: Joi.string().valid('pending', 'running', 'completed', 'failed'),
  }),
};

/**
 * Validates data against a schema
 * @param {Object} data - Data to validate
 * @param {Object} schema - Joi schema
 * @returns {Object} - { value, error }
 */
export const validate = (data, schema) => {
  return schema.validate(data, {
    abortEarly: false,
    stripUnknown: true,
  });
};

/**
 * Generate a slug from a string
 * @param {String} text - Text to convert to slug
 * @returns {String} - Slugified text
 */
export const generateSlug = (text) => {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-');
};

/**
 * Format error messages from Joi validation
 * @param {Object} error - Joi validation error
 * @returns {Object} - Formatted error messages
 */
export const formatValidationErrors = (error) => {
  const errors = {};
  error.details.forEach((detail) => {
    errors[detail.path[0]] = detail.message;
  });
  return errors;
};
