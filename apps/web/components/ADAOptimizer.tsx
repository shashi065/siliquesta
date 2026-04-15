'use client';

import { useState } from 'react';
import { optimizerAPI } from '@/utils/api';
import { useDesignStore } from '@/store/designStore';

interface OptimalDesign {
  rank: number;
  wn: number;
  wp: number;
  freq: number;
  power: number;
  delay: number;
  fom: number;
  explanation?: string;
}

export default function ADAOptimizer() {
  const { params, setError } = useDesignStore();
  const [loading, setLoading] = useState(false);
  const [designs, setDesigns] = useState<OptimalDesign[]>([]);
  const [tradeoffExplanation, setTradeoffExplanation] = useState<string[]>([]);

  const runOptimizer = async () => {
    try {
      setLoading(true);
      setError(null);

      const result = await optimizerAPI.run({
        wp: params.wp,
        vdd: params.vdd,
        temp: params.temp,
        cl_ff: params.cl_ff,
        tech_node: params.tech_node,
        min_freq: 3.0,
        max_power: 5.0,
        objective: 'pareto',
      });

      const payload = result as any;
      setDesigns(payload.ranking || payload.pareto_front || payload.optimal || []);
      setTradeoffExplanation(payload.explanation || []);
    } catch (err: any) {
      setError(err.message || 'Optimization failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 shadow-lg">
      <h2 className="text-2xl font-bold text-white mb-4">🚀 ADA Optimizer</h2>
      <p className="text-slate-400 mb-6">
        Autonomous Design Agent - Find Pareto-optimal CMOS designs
      </p>

      <button
        onClick={runOptimizer}
        disabled={loading}
        className="px-6 py-3 bg-gradient-to-r from-yellow-400 to-orange-600 text-white font-semibold rounded-lg hover:opacity-90 disabled:opacity-50 transition mb-6"
      >
        {loading ? 'Optimizing 10k designs...' : '⚡ Launch ADA (Pareto Front)'}
      </button>

      {designs.length > 0 && (
        <div className="space-y-4">
          {tradeoffExplanation.length > 0 && (
            <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-4 text-sm text-slate-300">
              <p className="mb-2 font-semibold text-cyan-400">Trade-off Summary</p>
              <ul className="space-y-1">
                {tradeoffExplanation.map((line, idx) => (
                  <li key={idx}>{line}</li>
                ))}
              </ul>
            </div>
          )}
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-slate-300">
              <thead className="bg-slate-700 text-cyan-400">
                <tr>
                  <th className="px-4 py-2 text-left">#</th>
                  <th className="px-4 py-2 text-left">WN (µm)</th>
                  <th className="px-4 py-2 text-left">WP (µm)</th>
                  <th className="px-4 py-2 text-left">Freq (GHz)</th>
                  <th className="px-4 py-2 text-left">Power (mW)</th>
                  <th className="px-4 py-2 text-left">Delay (ps)</th>
                  <th className="px-4 py-2 text-left">FOM</th>
                  <th className="px-4 py-2 text-center">Save</th>
                </tr>
              </thead>
              <tbody>
                {designs.slice(0, 8).map((design, idx) => (
                  <tr key={idx} className="border-t border-slate-700 hover:bg-slate-700">
                    <td className="px-4 py-2">{design.rank || idx + 1}</td>
                    <td className="px-4 py-2">{design.wn.toFixed(2)}</td>
                    <td className="px-4 py-2">{design.wp.toFixed(2)}</td>
                    <td className="px-4 py-2 text-green-400">{design.freq.toFixed(2)}</td>
                    <td className="px-4 py-2 text-orange-400">{design.power.toFixed(2)}</td>
                    <td className="px-4 py-2">{design.delay.toFixed(2)}</td>
                    <td className="px-4 py-2 text-cyan-400 font-bold">{design.fom.toFixed(3)}</td>
                    <td className="px-4 py-2 text-center">
                      <button className="px-3 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700">
                        💾
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
