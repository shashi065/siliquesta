import { asyncHandler } from '../middleware/errorHandler.js';
import AuthService from '../services/authService.js';

export class AuthController {
  /**
   * Sign up new user
   * POST /api/auth/signup
   */
  static signup = async (req, res, next) => {
    try {
      const data = req.validatedData;

      const result = await AuthService.register(data);

      res.status(201).json({
        message: 'User created successfully',
        user: result.user,
        accessToken: result.accessToken,
        refreshToken: result.refreshToken,
        access_token: result.accessToken,
        refresh_token: result.refreshToken,
      });
    } catch (error) {
      next(error);
    }
  };

  /**
   * Login user
   * POST /api/auth/login
   */
  static login = async (req, res, next) => {
    try {
      const data = req.validatedData;

      const result = await AuthService.login(data);

      res.status(200).json({
        message: 'Login successful',
        user: result.user,
        accessToken: result.accessToken,
        refreshToken: result.refreshToken,
        access_token: result.accessToken,
        refresh_token: result.refreshToken,
      });
    } catch (error) {
      // Don't send specific error details on login failure
      if (error.message === 'Invalid email or password') {
        return res.status(401).json({
          error: 'Unauthorized',
          message: 'Invalid email or password',
        });
      }
      next(error);
    }
  };

  /**
   * Get current user profile
   * GET /api/auth/me
   */
  static getMe = async (req, res, next) => {
    try {
      const userId = req.user.userId;

      const user = await AuthService.getUserById(userId);

      res.status(200).json({
        user,
      });
    } catch (error) {
      next(error);
    }
  };

  /**
   * Update user profile
   * PATCH /api/auth/profile
   */
  static updateProfile = async (req, res, next) => {
    try {
      const userId = req.user.userId;
      const data = req.validatedData;

      const user = await AuthService.updateProfile(userId, data);

      res.status(200).json({
        message: 'Profile updated successfully',
        user,
      });
    } catch (error) {
      next(error);
    }
  };

  /**
   * Change password
   * POST /api/auth/change-password
   */
  static changePassword = async (req, res, next) => {
    try {
      const userId = req.user.userId;
      const { oldPassword, newPassword } = req.validatedData;

      await AuthService.changePassword(userId, oldPassword, newPassword);

      res.status(200).json({
        message: 'Password changed successfully',
      });
    } catch (error) {
      if (error.message === 'Current password is incorrect') {
        return res.status(401).json({
          error: 'Unauthorized',
          message: 'Current password is incorrect',
        });
      }
      next(error);
    }
  };

  /**
   * Refresh access token
   * POST /api/auth/refresh
   */
  static refreshToken = async (req, res, next) => {
    try {
      const { refreshToken } = req.body;

      if (!refreshToken) {
        return res.status(400).json({
          error: 'Bad Request',
          message: 'Refresh token is required',
        });
      }

      const result = await AuthService.refreshToken(refreshToken);

      res.status(200).json({
        message: 'Token refreshed successfully',
        user: result.user,
        accessToken: result.accessToken,
        refreshToken: result.refreshToken,
        access_token: result.accessToken,
        refresh_token: result.refreshToken,
      });
    } catch (error) {
      res.status(401).json({
        error: 'Unauthorized',
        message: error.message,
      });
    }
  };

  /**
   * Logout
   * POST /api/auth/logout
   */
  static logout = async (req, res, next) => {
    try {
      // Invalidate token on client side
      res.status(200).json({
        message: 'Logged out successfully',
      });
    } catch (error) {
      next(error);
    }
  };
}

export default AuthController;
