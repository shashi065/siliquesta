// Enhanced API response validation and error handling.

import { AxiosError, AxiosResponse } from 'axios';

// Response validators
export interface APIResponse<T = any> {
  success?: boolean;
  data?: T;
  error?: string;
  job_id?: string;
  status?: string;
  timestamp?: string;
}

export interface JobResponse {
  job_id: string;
  job_key?: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  result?: any;
  error?: string | null;
}

export const validateJobResponse = (response: any): JobResponse => {
  if (!response) {
    throw new Error('Empty response received');
  }

  // Normalize response formats
  const jobId = response.job_id || response.job_key || response.task_id;
  const status = (response.status || 'queued').toLowerCase();

  if (!jobId) {
    throw new Error('No job_id in response: ' + JSON.stringify(response));
  }

  if (!['queued', 'running', 'completed', 'failed', 'success'].includes(status)) {
    throw new Error(`Invalid status: ${status}`);
  }

  return {
    job_id: jobId,
    job_key: response.job_key,
    status: status === 'success' ? 'completed' : status as any,
    result: response.result || response.data,
    error: response.error || response.error_message || null,
  };
};

export const validateSimulationResult = (result: any): boolean => {
  if (!result) return false;

  const isNumeric = (n: any) => !Number.isNaN(parseFloat(n)) && isFinite(n);
  const isPositive = (n: any) => isNumeric(n) && parseFloat(n) > 0;

  const hasValidFreq = isPositive(result.freq);
  const hasValidPower = isNumeric(result.dynamic_power) || isNumeric(result.power);
  const hasValidDelay = isNumeric(result.delay);

  return hasValidFreq && hasValidPower && hasValidDelay;
};

export const validateOptimizationResult = (result: any): boolean => {
  if (!result) return false;

  const hasParams = result.optimized_params && typeof result.optimized_params === 'object';
  const hasConfidence = typeof result.confidence_score === 'number' && 
                        result.confidence_score >= 0 && 
                        result.confidence_score <= 1;
  const hasMetrics = result.predicted_metrics || result.predictedMetrics;

  return hasParams && hasConfidence && hasMetrics;
};

export const normalizeSimulationResult = (result: any) => {
  return {
    freq: parseFloat(result.freq) || 0,
    power: parseFloat(result.dynamic_power || result.power || 0),
    staticPower: parseFloat(result.static_power || 0),
    delay: parseFloat(result.delay) || 0,
    energyPerCycle: parseFloat(result.energy_per_cycle) || undefined,
    powerDelayProduct: parseFloat(result.power_delay_product) || undefined,
    corner: result.corner || 'tt',
    vdd: parseFloat(result.vdd) || 1.2,
    temp: parseFloat(result.temp) || 25,
    techNode: parseFloat(result.tech_node) || 28,
    timestamp: result.timestamp || new Date().toISOString(),
  };
};

export const normalizeOptimizationResult = (result: any) => {
  return {
    optimizedParams: {
      wn: parseFloat(result.optimized_params?.wn) || 0,
      wp: parseFloat(result.optimized_params?.wp) || 0,
      vdd: parseFloat(result.optimized_params?.vdd) || 0,
      temp: parseFloat(result.optimized_params?.temp) || 0,
      cl_ff: parseFloat(result.optimized_params?.cl_ff) || 0,
    },
    predictedMetrics: {
      freq: parseFloat(result.predicted_metrics?.freq_ghz || result.predictedMetrics?.freq || 0),
      power: parseFloat(result.predicted_metrics?.power_mw || result.predictedMetrics?.power || 0),
      delay: parseFloat(result.predicted_metrics?.delay_ps || result.predictedMetrics?.delay || 0),
    },
    confidenceScore: parseFloat(result.confidence_score || result.confidenceScore || 0.5),
    uncertainty: parseFloat(result.uncertainty || 0.1),
    improvement: parseFloat(result.improvements?.freq || result.improvement_percent || 0),
    algorithm: result.algorithm || 'ml',
    iterations: result.iterations || 0,
    executionTimeMs: result.execution_time_ms || result.executionTime || 0,
    timestamp: result.timestamp || new Date().toISOString(),
  };
};
