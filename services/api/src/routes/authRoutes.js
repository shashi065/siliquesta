import express from 'express';
import Joi from 'joi';
import { authenticate } from '../middleware/auth.js';
import { validateBody } from '../middleware/validation.js';
import {
  userValidationSchemas,
} from '../utils/validators.js';
import AuthController from '../controllers/authController.js';

const router = express.Router();

/**
 * Auth Routes
 * POST /api/auth/signup - Create new account
 * POST /api/auth/login - Login
 * GET /api/auth/me - Get current user
 * PATCH /api/auth/profile - Update profile
 * POST /api/auth/refresh - Refresh token
 * POST /api/auth/logout - Logout
 * POST /api/auth/change-password - Change password
 */

// Public routes
router.post(
  '/signup',
  validateBody(userValidationSchemas.signup),
  AuthController.signup
);

router.post(
  '/register',
  validateBody(userValidationSchemas.signup),
  AuthController.signup
);

router.post(
  '/login',
  (req, res, next) => {
    if (!req.body.email && req.body.username) {
      req.body.email = req.body.username;
    }
    next();
  },
  validateBody(userValidationSchemas.login),
  AuthController.login
);

router.post('/refresh', AuthController.refreshToken);

// Protected routes
router.get('/me', authenticate, AuthController.getMe);

router.patch(
  '/profile',
  authenticate,
  validateBody(userValidationSchemas.update),
  AuthController.updateProfile
);

router.post('/logout', authenticate, AuthController.logout);

router.post(
  '/change-password',
  authenticate,
  validateBody(Joi.object({
    oldPassword: Joi.string().required(),
    newPassword: Joi.string().min(8).required(),
  })),
  AuthController.changePassword
);

export default router;
