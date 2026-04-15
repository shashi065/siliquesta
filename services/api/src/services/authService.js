import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import dotenv from 'dotenv';
import { prisma } from '../config/database.js';

dotenv.config();

const BCRYPT_ROUNDS = parseInt(process.env.BCRYPT_ROUNDS) || 10;
const JWT_SECRET = process.env.JWT_SECRET;
const JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || '7d';
const JWT_REFRESH_SECRET = process.env.JWT_REFRESH_SECRET;
const JWT_REFRESH_EXPIRES_IN = process.env.JWT_REFRESH_EXPIRES_IN || '30d';

export class AuthService {
  /**
   * Hash password using bcrypt
   * @param {String} password - Plain password
   * @returns {Promise<String>} - Hashed password
   */
  static async hashPassword(password) {
    const salt = await bcrypt.genSalt(BCRYPT_ROUNDS);
    return bcrypt.hash(password, salt);
  }

  /**
   * Compare password with hash
   * @param {String} password - Plain password
   * @param {String} hash - Password hash
   * @returns {Promise<Boolean>}
   */
  static async comparePassword(password, hash) {
    return bcrypt.compare(password, hash);
  }

  /**
   * Generate JWT token
   * @param {Object} payload - Token payload
   * @param {String} secret - JWT secret
   * @param {String} expiresIn - Expiration time
   * @returns {String} - JWT token
   */
  static generateToken(payload, secret = JWT_SECRET, expiresIn = JWT_EXPIRES_IN) {
    return jwt.sign(payload, secret, { expiresIn });
  }

  /**
   * Verify JWT token
   * @param {String} token - JWT token
   * @param {String} secret - JWT secret
   * @returns {Object} - Decoded token
   */
  static verifyToken(token, secret = JWT_SECRET) {
    return jwt.verify(token, secret);
  }

  /**
   * Register new user
   * @param {Object} data - User registration data
   * @returns {Promise<Object>} - Created user and tokens
   */
  static async register(data) {
    const { email, name, password } = data;

    // Check if user already exists
    const existingUser = await prisma.user.findUnique({
      where: { email },
    });

    if (existingUser) {
      throw new Error('Email already registered');
    }

    // Hash password
    const hashedPassword = await this.hashPassword(password);

    // Create user
    const user = await prisma.user.create({
      data: {
        email,
        name,
        password: hashedPassword,
      },
      select: {
        id: true,
        email: true,
        name: true,
        role: true,
        createdAt: true,
      },
    });

    // Generate tokens
    const accessToken = this.generateToken({
      userId: user.id,
      email: user.email,
      role: user.role,
    });

    const refreshToken = this.generateToken(
      { userId: user.id },
      JWT_REFRESH_SECRET,
      JWT_REFRESH_EXPIRES_IN
    );

    return {
      user,
      accessToken,
      refreshToken,
    };
  }

  /**
   * Login user
   * @param {Object} data - Login credentials
   * @returns {Promise<Object>} - User and tokens
   */
  static async login(data) {
    const { email, password } = data;

    // Find user
    const user = await prisma.user.findUnique({
      where: { email },
    });

    if (!user) {
      throw new Error('Invalid email or password');
    }

    // Verify password
    const isPasswordValid = await this.comparePassword(password, user.password);

    if (!isPasswordValid) {
      throw new Error('Invalid email or password');
    }

    // Update last login
    await prisma.user.update({
      where: { id: user.id },
      data: { lastLogin: new Date() },
    });

    // Generate tokens
    const accessToken = this.generateToken({
      userId: user.id,
      email: user.email,
      role: user.role,
    });

    const refreshToken = this.generateToken(
      { userId: user.id },
      JWT_REFRESH_SECRET,
      JWT_REFRESH_EXPIRES_IN
    );

    // Remove password from user object
    const { password: _, ...userWithoutPassword } = user;

    return {
      user: userWithoutPassword,
      accessToken,
      refreshToken,
    };
  }

  /**
   * Refresh access token
   * @param {String} refreshToken - Refresh token
   * @returns {Promise<Object>} - New token pair
   */
  static async refreshToken(refreshToken) {
    try {
      const decoded = this.verifyToken(refreshToken, JWT_REFRESH_SECRET);

      // Get fresh user data
      const user = await prisma.user.findUnique({
        where: { id: decoded.userId },
        select: {
          id: true,
          email: true,
          name: true,
          role: true,
        },
      });

      if (!user) {
        throw new Error('User not found');
      }

      const newAccessToken = this.generateToken({
        userId: user.id,
        email: user.email,
        role: user.role,
      });

      const newRefreshToken = this.generateToken(
        { userId: user.id },
        JWT_REFRESH_SECRET,
        JWT_REFRESH_EXPIRES_IN
      );

      return {
        user,
        accessToken: newAccessToken,
        refreshToken: newRefreshToken,
      };
    } catch (error) {
      throw new Error('Invalid refresh token');
    }
  }

  /**
   * Get user by ID
   * @param {String} userId - User ID
   * @returns {Promise<Object>} - User data
   */
  static async getUserById(userId) {
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: {
        id: true,
        email: true,
        name: true,
        avatar: true,
        bio: true,
        role: true,
        isActive: true,
        createdAt: true,
        updatedAt: true,
        lastLogin: true,
      },
    });

    if (!user) {
      throw new Error('User not found');
    }

    return user;
  }

  /**
   * Update user profile
   * @param {String} userId - User ID
   * @param {Object} data - Update data
   * @returns {Promise<Object>} - Updated user
   */
  static async updateProfile(userId, data) {
    const user = await prisma.user.update({
      where: { id: userId },
      data: {
        ...(data.name && { name: data.name }),
        ...(data.bio && { bio: data.bio }),
        ...(data.avatar && { avatar: data.avatar }),
      },
      select: {
        id: true,
        email: true,
        name: true,
        avatar: true,
        bio: true,
        role: true,
        createdAt: true,
        updatedAt: true,
      },
    });

    return user;
  }

  /**
   * Change password
   * @param {String} userId - User ID
   * @param {String} oldPassword - Current password
   * @param {String} newPassword - New password
   * @returns {Promise<void>}
   */
  static async changePassword(userId, oldPassword, newPassword) {
    const user = await prisma.user.findUnique({
      where: { id: userId },
    });

    if (!user) {
      throw new Error('User not found');
    }

    // Verify old password
    const isPasswordValid = await this.comparePassword(oldPassword, user.password);

    if (!isPasswordValid) {
      throw new Error('Current password is incorrect');
    }

    // Hash new password
    const hashedPassword = await this.hashPassword(newPassword);

    // Update password
    await prisma.user.update({
      where: { id: userId },
      data: { password: hashedPassword },
    });
  }
}

export default AuthService;
