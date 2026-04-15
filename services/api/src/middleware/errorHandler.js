/**
 * Async error wrapper (clean + consistent naming)
 */
export const asyncHandler = (fn) => (req, res, next) => {
  Promise.resolve(fn(req, res, next)).catch(next);
};

/**
 * Error handling middleware
 * Catches and formats all errors in the application
 */
export const errorHandler = (err, req, res, next) => {
  console.error("Error:", err);

  // Prisma errors
  if (err.code === "P2025") {
    return res.status(404).json({
      error: "Not Found",
      message: "The requested resource does not exist",
    });
  }

  if (err.code === "P2002") {
    const field = err.meta?.target?.[0] || "field";
    return res.status(409).json({
      error: "Conflict",
      message: `${field} already exists`,
    });
  }

  // JWT errors
  if (err.name === "JsonWebTokenError") {
    return res.status(401).json({
      error: "Unauthorized",
      message: "Invalid token",
    });
  }

  if (err.name === "TokenExpiredError") {
    return res.status(401).json({
      error: "Unauthorized",
      message: "Token has expired",
    });
  }

  // Validation errors (Joi)
  if (err.details && Array.isArray(err.details)) {
    return res.status(400).json({
      error: "Validation Error",
      message: "Invalid input",
      details: err.details.map((d) => ({
        field: d.path?.[0],
        message: d.message,
      })),
    });
  }

  // Default error response
  const statusCode = err.statusCode || 500;
  const message = err.message || "Internal Server Error";

  res.status(statusCode).json({
    error: err.error || "Error",
    message,
    ...(process.env.NODE_ENV === "development" && { stack: err.stack }),
  });
};

export default errorHandler;