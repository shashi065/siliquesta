import { validate, formatValidationErrors } from '../utils/validators.js';

/**
 * Validates request body against a schema
 */
export const validateBody = (schema) => {
  return (req, res, next) => {
    const { error, value } = validate(req.body, schema);

    if (error) {
      return res.status(400).json({
        error: 'Validation Error',
        message: 'Invalid input',
        details: formatValidationErrors(error),
      });
    }

    req.validatedData = value;
    next();
  };
};

/**
 * Validates request query against a schema
 */
export const validateQuery = (schema) => {
  return (req, res, next) => {
    const { error, value } = validate(req.query, schema);

    if (error) {
      return res.status(400).json({
        error: 'Validation Error',
        message: 'Invalid query parameters',
        details: formatValidationErrors(error),
      });
    }

    req.validatedQuery = value;
    next();
  };
};

/**
 * Validates request params against a schema
 */
export const validateParams = (schema) => {
  return (req, res, next) => {
    const { error, value } = validate(req.params, schema);

    if (error) {
      return res.status(400).json({
        error: 'Validation Error',
        message: 'Invalid path parameters',
        details: formatValidationErrors(error),
      });
    }

    req.validatedParams = value;
    next();
  };
};

export default { validateBody, validateQuery, validateParams };
