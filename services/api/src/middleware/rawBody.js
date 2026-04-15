/**
 * Raw Body Middleware
 * Required for Stripe webhook signature verification
 * Must be applied BEFORE express.json() for the specific route
 */

export function handleRawBody() {
  return (req, res, buffer, encoding) => {
    if (buffer && buffer.length) {
      req.rawBody = buffer.toString(encoding || 'utf8');
    }
  };
}

/**
 * Alternative: Raw body middleware factory for specific routes
 */
export function rawBodyMiddleware() {
  return express.raw({ type: 'application/json' });
}

export default { handleRawBody, rawBodyMiddleware };
