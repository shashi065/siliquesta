import axios, { AxiosError } from 'axios';

const { API_BASE } = require('../../../shared/api-config.js');

const API_BASE_URL = API_BASE;

// Error types
export class APIError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public context?: any
  ) {
    super(detail);
    this.name = 'APIError';
  }
}

// Create axios client
const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Utility functions
const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// Validate job response format
const validateJobResponse = (response: any) => {
  const jobId = response.job_id || response.job_key || response.task_id;
  const status = (response.status || 'queued').toLowerCase();
  
  if (!jobId) {
    throw new APIError(422, 'No job_id in response: ' + JSON.stringify(response));
  }
  
  return {
    job_id: jobId,
    status: status === 'success' ? 'completed' : status,
    result: response.result || response.data,
    error: response.error || response.error_message || null,
  };
};

// Enhanced job polling with better error handling
async function awaitJobResult<T>(jobId: string, timeoutMs: number = 120000, pollMs: number = 1200): Promise<T> {
  const started = Date.now();
  let lastError: Error | null = null;
  let pollCount = 0;
  
  while (Date.now() - started < timeoutMs) {
    pollCount++;
    
    try {
      // Try /jobs endpoint first (Celery status)
      try {
        const response = await client.get(`/jobs/${jobId}`) as any;
        const job = validateJobResponse(response);
        
        if (job.status === 'completed') {
          return job.result as T;
        } else if (job.status === 'failed') {
          throw new APIError(500, `Job failed: ${job.error || 'Unknown error'}`);
        }
        // Still running, keep polling
        await sleep(pollMs);
        continue;
      } catch (jobsError) {
        // If /jobs endpoint fails, try /results
        if ((jobsError as any)?.status === 404 || (jobsError as any)?.response?.status === 404) {
          try {
            const resultResponse = await client.get(`/results/${jobId}`) as any;
            const job = validateJobResponse(resultResponse);
            
            if (job.status === 'completed') {
              return job.result as T;
            } else if (job.status === 'failed') {
              throw new APIError(500, `Job failed: ${job.error || 'Unknown error'}`);
            }
          } catch (resultsError) {
            lastError = resultsError as Error;
          }
        } else {
          lastError = jobsError as Error;
        }
      }
    } catch (err) {
      lastError = err as Error;
      if (pollCount % 5 === 0) {
        console.warn(`Poll ${pollCount} for job ${jobId}, retrying...`);
      }
    }
    
    // If we haven't gotten a result yet, keep polling
    if (Date.now() - started < timeoutMs) {
      await sleep(pollMs);
    }
  }
  
  const error = lastError || new Error('Timeout waiting for job result');
  throw new APIError(504, `Job ${jobId} timed out`, { pollCount, jobId });
}

// Enhanced job submission with validation
async function submitJob<T>(path: string, payload?: unknown): Promise<T> {
  const response = await client.post(path, payload) as any;
  
  // Validate response has required fields
  const job = validateJobResponse(response);
  
  if (job.status === 'queued' && job.job_id) {
    try {
      return await awaitJobResult<T>(job.job_id, 120000);
    } catch (err) {
      if (err instanceof APIError) {
        throw err;
      }
      throw new APIError(500, 'Job execution failed', { jobId: job.job_id });
    }
  }
  
  // If not queued, return result directly
  return (job.result || response) as T;
}

// Request interceptor - add auth token
client.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle errors and validate
client.interceptors.response.use(
  (response) => response.data || response,
  (error: AxiosError) => {
    const status = error.response?.status || 0;
    const errorData = error.response?.data as any;
    const detail = errorData?.detail || errorData?.message || error.message || 'Unknown error';
    
    // Log error details
    console.error('API Error:', {
      status,
      message: detail,
      data: errorData,
      url: error.config?.url,
      timestamp: new Date().toISOString(),
    });
    
    // Handle authentication errors
    if (status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        if (!window.location.pathname.includes('/auth')) {
          window.location.href = '/auth/login';
        }
      }
    }
    
    throw new APIError(status, detail, errorData);
  }
);

export const simulationAPI = {
  run: (params: {
    wn: number;
    wp: number;
    vdd: number;
    temp: number;
    cl_ff: number;
    corner: string;
    tech_node: number;
  }) => submitJob('/simulate', params),
  sweep: (params: {
    wn_min: number;
    wn_max: number;
    wp: number;
    vdd: number;
    temp: number;
    cl_ff: number;
    corner: string;
    tech_node: number;
  }) =>
    submitJob(`/simulate/sweep?max_wn=${params.wn_max}`, {
      wn: params.wn_min,
      wp: params.wp,
      vdd: params.vdd,
      temp: params.temp,
      cl_ff: params.cl_ff,
      corner: params.corner,
      tech_node: params.tech_node,
    }),
  batch: (simulations: any[]) =>
    submitJob('/simulate/batch', { simulations }),
};

export const pvtAPI = {
  cornerSummary: (params: {
    wn: number;
    wp: number;
    vdd: number;
    temp: number;
    cl_ff: number;
    tech_node: number;
  }) =>
    submitJob(`/pvt/corner-summary?vdd=${params.vdd}&temp=${params.temp}`, {
      wn: params.wn,
      wp: params.wp,
      cl_ff: params.cl_ff,
      tech_node: params.tech_node,
    }),
  fullSweep: (params: {
    wn: number;
    wp: number;
    cl_ff: number;
    tech_node: number;
  }) =>
    submitJob('/pvt/full-sweep', {
      wn: params.wn,
      wp: params.wp,
      cl_ff: params.cl_ff,
      tech_node: params.tech_node,
    }),
};

export const optimizerAPI = {
  run: (params: {
    wp: number;
    vdd: number;
    temp: number;
    cl_ff: number;
    tech_node: number;
    max_power?: number;
    min_freq?: number;
    objective?: string;
  }) => submitJob('/optimize', params),
};

export const twinAPI = {
  computeAging: (params: any) =>
    submitJob('/twin/compute-aging', params),
};

export const aiAPI = {
  chat: (data: { 
    message: string
    context?: Record<string, unknown>
    use_external_api?: boolean
  }) =>
    submitJob('/ai/chat', data),
  generateCode: (prompt: string, language: string = 'verilog') =>
    submitJob('/ai/generate-code', { prompt, language }),
  predictFailure: (params: any) =>
    submitJob('/ai/predict-failure', params),
};

export const authAPI = {
  login: (data: { 
    email: string
    password: string
  }) => {
    const formData = new URLSearchParams();
    formData.set('username', data.email);
    formData.set('password', data.password);
    return client.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
  },
  signup: (data: { 
    email: string
    password: string
    full_name: string
  }) =>
    client.post('/auth/signup', {
      email: data.email,
      password: data.password,
      name: data.full_name,
    }),
  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },
};

export const userAPI = {
  getProfile: () => client.get('/users/me'),
  getSavedDesigns: (userId: string) => client.get(`/users/${userId}/designs`),
};

export const designAPI = {
  create: (data: any) => client.post('/designs', data),
  list: () => client.get('/designs'),
  get: (id: string) => client.get(`/designs/${id}`),
  update: (id: string, data: any) => client.put(`/designs/${id}`, data),
  delete: (id: string) => client.delete(`/designs/${id}`),
  save: (data: any) => client.post('/designs/save', data),
};

export const projectsAPI = {
  create: (data: { name: string; description?: string; tags?: string[] }) => 
    client.post('/projects', data),
  list: () => 
    client.get('/projects'),
  get: (projectId: number) => 
    client.get(`/projects/${projectId}`),
  update: (projectId: number, data: { name?: string; description?: string; tags?: string[]; design_state?: any }) => 
    client.put(`/projects/${projectId}`, data),
  delete: (projectId: number) => 
    client.delete(`/projects/${projectId}`),
  saveDesign: (projectId: number, designData: any) => 
    client.post(`/projects/${projectId}/save-design`, designData),
  getDesignState: (projectId: number) => 
    client.get(`/projects/${projectId}/design-state`),
};

export default client;
