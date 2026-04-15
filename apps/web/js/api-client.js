// API Configuration - Environment-aware
function getAPIConfig() {
  const hostname = window.location.hostname;
  const protocol = window.location.protocol;
  
  // Production configuration
  if (hostname.includes('app.siliquesta.com') || hostname.includes('siliquesta.com')) {
    return {
      BACKEND_URL: 'https://api.siliquesta.com/api',
      AI_SERVICE_URL: 'https://ai.siliquesta.com',
      TIMEOUT: 30000,
      ENVIRONMENT: 'production'
    };
  }
  
  // Staging configuration
  if (hostname.includes('staging')) {
    return {
      BACKEND_URL: 'https://staging-api.siliquesta.com/api',
      AI_SERVICE_URL: 'https://staging-ai.siliquesta.com',
      TIMEOUT: 30000,
      ENVIRONMENT: 'staging'
    };
  }
  
  // Development configuration
  return {
    BACKEND_URL: 'http://localhost:5000/api',
    AI_SERVICE_URL: 'http://localhost:8000',
    TIMEOUT: 30000,
    ENVIRONMENT: 'development'
  };
}

const API_CONFIG = getAPIConfig();

/**
 * API Client - Handles all HTTP requests with JWT authentication
 */
class APIClient {
  constructor(baseUrl = API_CONFIG.BACKEND_URL) {
    this.baseUrl = baseUrl;
    this.token = localStorage.getItem('accessToken');
  }

  /**
   * Set auth token
   */
  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('accessToken', token);
    } else {
      localStorage.removeItem('accessToken');
    }
  }

  /**
   * Get auth headers
   */
  getHeaders(isJSON = true) {
    const headers = {};
    if (isJSON) {
      headers['Content-Type'] = 'application/json';
    }
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  /**
   * Make HTTP request
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      ...options,
      headers: {
        ...this.getHeaders(),
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        if (response.status === 401) {
          // Token expired or invalid
          this.setToken(null);
          window.location.href = '/login.html';
        }
        const error = await response.json();
        throw new Error(error.message || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      throw error;
    }
  }

  /**
   * GET request
   */
  get(endpoint, options = {}) {
    return this.request(endpoint, { method: 'GET', ...options });
  }

  /**
   * POST request
   */
  post(endpoint, body, options = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
      ...options,
    });
  }

  /**
   * PATCH request
   */
  patch(endpoint, body, options = {}) {
    return this.request(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(body),
      ...options,
    });
  }

  /**
   * DELETE request
   */
  delete(endpoint, options = {}) {
    return this.request(endpoint, { method: 'DELETE', ...options });
  }
}

/**
 * Export for use in other modules
 */
window.APIClient = APIClient;
