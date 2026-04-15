'use client';

import { useState } from 'react';
import { useDesignStore } from '@/store/designStore';
import { pvtAPI } from '@/utils/api';

export default function PVTAnalyzer() {
  const { params, setResults, setError, setRunning } = useDesignStore();
  const [loading, setLoading] = useState(false);
  const [pvtData, setPvtData] = useState<any>(null);

  const runFullSweep = async () => {
    try {
      setLoading(true);
      setRunning(true);
      setError(null);

      const result = await pvtAPI.fullSweep({
        wn: params.wn,
        wp: params.wp,
        cl_ff: params.cl_ff,
        tech_node: params.tech_node,
      });

      setPvtData(result);
      setResults(result as any);
    } catch (err: any) {
      setError(err.message || 'PVT sweep failed');
    } finally {
      setLoading(false);
      setRunning(false);
    }
  };

  const runCornerSummary = async () => {
    try {
      setLoading(true);
      setRunning(true);
      setError(null);

      const result = await pvtAPI.cornerSummary({
        wn: params.wn,
        wp: params.wp,
        vdd: params.vdd,
        temp: params.temp,
        cl_ff: params.cl_ff,
        tech_node: params.tech_node,
      });

      setPvtData(result);
      setResults(result as any);
    } catch (err: any) {
      setError(err.message || 'Corner summary failed');
    } finally {
      setLoading(false);
      setRunning(false);
    }
  };

  return (
    <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 shadow-lg interactive-surface">
      <h2 className="text-2xl font-bold text-white mb-6">PVT Analysis</h2>

      <div className="flex gap-4 mb-6">
        <button
          onClick={runCornerSummary}
          disabled={loading}
          className="px-6 py-3 bg-gradient-to-r from-green-400 to-emerald-600 text-white font-semibold rounded-lg hover:opacity-90 disabled:opacity-50 interactive-button"
        >
          {loading ? 'Analyzing...' : 'Corner Summary'}
        </button>
        <button
          onClick={runFullSweep}
          disabled={loading}
          className="px-6 py-3 bg-gradient-to-r from-orange-400 to-red-600 text-white font-semibold rounded-lg hover:opacity-90 disabled:opacity-50 interactive-button"
        >
          {loading ? 'Sweeping...' : 'Full Sweep (5T×5V)'}
        </button>
      </div>

      {pvtData && (
        <div className="bg-slate-700 rounded-lg p-4 max-h-96 overflow-y-auto">
          <pre className="text-green-400 text-xs font-mono whitespace-pre-wrap">
            {JSON.stringify(pvtData, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
