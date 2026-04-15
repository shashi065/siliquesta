/**
 * Authentication Service - Handles login, signup, and JWT management
 */
class AuthService {
  constructor() {
    this.api = new APIClient();
    this.user = null;
    this.loadUser();
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    return !!this.api.token && !!this.user;
  }

  /**
   * Load user from localStorage
   */
  loadUser() {
    const user = localStorage.getItem('user');
    if (user) {
      this.user = JSON.parse(user);
    }
  }

  /**
   * Save user to localStorage
   */
  saveUser(user) {
    this.user = user;
    localStorage.setItem('user', JSON.stringify(user));
  }

  /**
   * Sign up new user
   */
  async signup(email, name, password) {
    try {
      const response = await this.api.post('/auth/signup', {
        email,
        name,
        password,
        confirmPassword: password,
      });

      this.api.setToken(response.accessToken);
      localStorage.setItem('refreshToken', response.refreshToken);
      this.saveUser(response.user);

      return response;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Login user
   */
  async login(email, password) {
    try {
      const response = await this.api.post('/auth/login', {
        email,
        password,
      });

      this.api.setToken(response.accessToken);
      localStorage.setItem('refreshToken', response.refreshToken);
      this.saveUser(response.user);

      return response;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Get current user profile
   */
  async getProfile() {
    try {
      const response = await this.api.get('/auth/me');
      this.saveUser(response.user);
      return response.user;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Update profile
   */
  async updateProfile(data) {
    try {
      const response = await this.api.patch('/auth/profile', data);
      this.saveUser(response.user);
      return response.user;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Logout user
   */
  logout() {
    this.user = null;
    this.api.setToken(null);
    localStorage.removeItem('user');
    localStorage.removeItem('refreshToken');
    window.location.href = '/login.html';
  }

  /**
   * Refresh access token
   */
  async refreshToken() {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await this.api.post('/auth/refresh', { refreshToken });

      this.api.setToken(response.accessToken);
      localStorage.setItem('refreshToken', response.refreshToken);
      this.saveUser(response.user);

      return response;
    } catch (error) {
      this.logout();
      throw error;
    }
  }

  /**
   * Check authentication and redirect if not authenticated
   */
  static requireAuth() {
    const auth = window.authService;
    if (!auth || !auth.isAuthenticated()) {
      window.location.href = '/login.html';
    }
  }
}

// Global instance
window.authService = new AuthService();
