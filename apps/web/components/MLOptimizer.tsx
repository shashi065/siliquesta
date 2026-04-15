/**
 * ML Optimizer Component
 * 
 * Real-time AI-powered circuit optimization using digital twin surrogate model.
 * - Fast predictions without simulation
 * - Confidence scores and uncertainty bounds
 * - Multi-objective optimization (performance/power/efficiency)
 */

'use client';

import React, { startTransition, useState } from 'react';
import {
  Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart,
} from 'recharts';
import { Zap, AlertCircle, Loader } from 'lucide-react';

interface OptimizationParams {
  wn: number;
  wp: number;
  vdd: number;
  temp: number;
  cl_ff: number;
  tech_node: number;
}

interface PredictedMetrics {
  freq_ghz: number;
  power_mw: number;
  delay_ps: number;
}

interface OptimizationResult {
  optimized_params: OptimizationParams;
  predicted_metrics: PredictedMetrics;
  confidence_score: number;
  uncertainty: number;
  estimated_error_percent: number;
  improvements: {
    freq_improvement_percent: number;
    power_reduction_percent: number;
    delay_improvement_percent: number;
    efficiency_improvement_percent: number;
  };
  recommendations: string[];
}

interface ImprovementData {
  name: string;
  improvement: number;
  color: string;
}

const MLOptimizer: React.FC = () => {
  const [baselineParams, setBaselineParams] = useState<OptimizationParams>({
    wn: 1.0,
    wp: 2.0,
    vdd: 1.8,
    temp: 27,
    cl_ff: 10.0,
    tech_node: 7.0,
  });

  const [objective, setObjective] = useState<'performance' | 'power' | 'efficiency' | 'balanced'>('balanced');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<OptimizationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleParamChange = (param: keyof OptimizationParams, value: string) => {
    setBaselineParams({
      ...baselineParams,
      [param]: parseFloat(value),
    });
  };

  const runOptimization = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/optimizer/ml-optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...baselineParams,
          objective,
          iterations: 100,
          method: 'two_stage',
        }),
      });

      if (!response.ok) {
        throw new Error(`Optimization failed: ${response.statusText}`);
      }

      const data = await response.json();
      // If async job, poll for results
      if (data.job_id) {
        pollJobResults(data.job_id);
      } else {
        setResult(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Optimization failed');
    } finally {
      setLoading(false);
    }
  };

  const pollJobResults = async (jobId: string) => {
    // Poll for job completion (in practice this would be via WebSocket or similar)
    let attempts = 0;
    const maxAttempts = 60; // 30 seconds max

    const poll = async () => {
      try {
        const response = await fetch(`/api/v1/jobs/${jobId}`);
        if (response.ok) {
          const data = await response.json();
          if (data.status === 'completed') {
            setResult(data.payload);
          } else if (data.status === 'failed') {
            setError(data.error_text || 'Optimization failed');
          } else if (attempts < maxAttempts) {
            attempts++;
            setTimeout(poll, 500);
          }
        }
      } catch (err) {
        if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 500);
        }
      }
    };

    poll();
  };

  const improvementData: ImprovementData[] = result
    ? [
        {
          name: 'Frequency',
          improvement: result.improvements.freq_improvement_percent,
          color: '#06B6D4',
        },
        {
          name: 'Power',
          improvement: result.improvements.power_reduction_percent,
          color: '#10B981',
        },
        {
          name: 'Efficiency',
          improvement: result.improvements.efficiency_improvement_percent,
          color: '#F59E0B',
        },
      ]
    : [];

  const getConfidenceColor = (confidence: number) => {
    if (confidence > 0.95) return 'text-green-400';
    if (confidence > 0.85) return 'text-blue-400';
    if (confidence > 0.70) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getConfidenceBg = (confidence: number) => {
    if (confidence > 0.95) return 'bg-green-900';
    if (confidence > 0.85) return 'bg-blue-900';
    if (confidence > 0.70) return 'bg-yellow-900';
    return 'bg-red-900';
  };

  const barMotion = {
    isAnimationActive: true,
    animationDuration: 620,
    animationEasing: 'ease-out' as const,
  };

  return (
    <div className="space-y-6">
      {/* Input Section */}
      <div className="glass rounded-lg p-6 border border-cyan-500/20">
        <h3 className="text-lg font-semibold mb-4 text-cyan-400">Circuit Parameters</h3>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
          {(Object.keys(baselineParams) as Array<keyof OptimizationParams>).map((param) => (
            <div key={param}>
              <label className="block text-sm text-slate-400 mb-1">
                {param.toUpperCase()}
              </label>
              <input
                type="number"
                step="0.01"
                value={baselineParams[param]}
                onChange={(e) => handleParamChange(param, e.target.value)}
                className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white"
              />
            </div>
          ))}
        </div>

        <div className="mb-6">
          <label className="block text-sm text-slate-400 mb-2">Optimization Objective</label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {(['performance', 'power', 'efficiency', 'balanced'] as const).map((opt) => (
              <button
                key={opt}
                onClick={() => startTransition(() => setObjective(opt))}
                className={`px-4 py-2 rounded-lg text-sm border interactive-button ${
                  objective === opt
                    ? 'bg-cyan-400/10 text-cyan-200 border-cyan-400/20 active-mode-glow'
                    : 'bg-slate-700 text-slate-300 border-slate-600 hover:bg-slate-600'
                }`}
              >
                {opt.charAt(0).toUpperCase() + opt.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={runOptimization}
          disabled={loading}
          className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 disabled:opacity-50 text-white font-semibold py-3 rounded-lg interactive-button"
        >
          {loading ? (
            <>
              <Loader className="inline mr-2 animate-spin" size={18} />
              Optimizing...
            </>
          ) : (
            <>
              <Zap className="inline mr-2" size={18} />
              Run ML Optimization
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="glass rounded-lg p-4 border border-red-500/50 bg-red-900/20">
          <div className="flex items-start gap-3">
            <AlertCircle className="text-red-400 mt-0.5 flex-shrink-0" size={18} />
            <p className="text-red-200">{error}</p>
          </div>
        </div>
      )}

      {result && (
        <>
          {/* Results Section */}
          <div className="glass rounded-lg p-6 border border-cyan-500/20">
            <h3 className="text-lg font-semibold mb-4 text-cyan-400">Optimization Results</h3>

            {/* Confidence Indicator */}
            <div className={`rounded-lg p-4 mb-6 ${getConfidenceBg(result.confidence_score)} border border-opacity-30`}>
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-slate-400">Model Confidence</p>
                  <p className={`text-3xl font-bold ${getConfidenceColor(result.confidence_score)}`}>
                    {(result.confidence_score * 100).toFixed(1)}%
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-slate-400">Uncertainty</p>
                  <p className="text-lg text-slate-300">{result.uncertainty.toFixed(6)}</p>
                  <p className="text-xs text-slate-500">Est. Error: {result.estimated_error_percent.toFixed(2)}%</p>
                </div>
              </div>
            </div>

            {/* Improvements Chart */}
            <div className="mb-6">
              <h4 className="text-sm font-medium text-slate-300 mb-3">Performance Improvements</h4>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={improvementData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="name" stroke="#94A3B8" />
                  <YAxis stroke="#94A3B8" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                  />
                  <Bar dataKey="improvement" fill="#06B6D4" radius={[8, 8, 0, 0]} {...barMotion} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Optimized Parameters */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6 p-4 bg-slate-900/50 rounded-lg border border-slate-700">
              {(Object.entries(result.optimized_params) as Array<[string, number]>).map(([key, value]) => (
                <div key={key}>
                  <p className="text-xs text-slate-500 uppercase">{key}</p>
                  <p className="text-lg font-semibold text-cyan-400">{value.toFixed(2)}</p>
                </div>
              ))}
            </div>

            {/* Predicted Metrics */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="glass rounded-lg p-4 border border-blue-500/30">
                <p className="text-xs text-slate-400 uppercase">Frequency</p>
                <p className="text-2xl font-bold text-blue-400">{result.predicted_metrics.freq_ghz.toFixed(2)}</p>
                <p className="text-xs text-slate-500">GHz</p>
              </div>
              <div className="glass rounded-lg p-4 border border-green-500/30">
                <p className="text-xs text-slate-400 uppercase">Power</p>
                <p className="text-2xl font-bold text-green-400">{result.predicted_metrics.power_mw.toFixed(2)}</p>
                <p className="text-xs text-slate-500">mW</p>
              </div>
              <div className="glass rounded-lg p-4 border border-orange-500/30">
                <p className="text-xs text-slate-400 uppercase">Delay</p>
                <p className="text-2xl font-bold text-orange-400">{result.predicted_metrics.delay_ps.toFixed(2)}</p>
                <p className="text-xs text-slate-500">ps</p>
              </div>
            </div>

            {/* Recommendations */}
            {result.recommendations.length > 0 && (
              <div className="bg-slate-900/30 rounded-lg p-4 border border-slate-700">
                <h4 className="text-sm font-medium text-slate-300 mb-3">Recommendations</h4>
                <ul className="space-y-2">
                  {result.recommendations.map((rec, idx) => (
                    <li key={idx} className="text-sm text-slate-400 flex items-start gap-2">
                      <span className="text-cyan-400 mt-0.5">•</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Model Metadata */}
          <div className="glass rounded-lg p-4 border border-slate-700 text-xs">
            <p className="text-slate-400">
              Model: {result.recommendations[0]?.includes('confidence') ? 'High-confidence' : 'Standard'} prediction
              from {result.recommendations.length} parameters
            </p>
          </div>
        </>
      )}
    </div>
  );
};

export default MLOptimizer;
