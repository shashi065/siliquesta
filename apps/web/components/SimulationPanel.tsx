'use client';

import { useState } from 'react';
import { useDesignStore } from '@/store/designStore';
import { simulationAPI } from '@/utils/api';

const TECH_NODES = [180, 130, 90, 65, 45, 32, 28, 22, 16, 10, 7, 5, 3, 1];
const CORNERS = ['SS', 'TT', 'FF', 'SF', 'FS', 'MC'];

export default function SimulationPanel() {
  const { params, setParams, setRunning, setResults, setError } = useDesignStore();
  const [loading, setLoading] = useState(false);

  const handleInputChange = (field: string, value: any) => {
    setParams({ ...params, [field]: value });
  };

  const runSimulation = async () => {
    try {
      setRunning(true);
      setLoading(true);
      setError(null);

      const result = await simulationAPI.run({
        wn: params.wn,
        wp: params.wp,
        vdd: params.vdd,
        temp: params.temp,
        cl_ff: params.cl_ff,
        corner: params.corner,
        tech_node: params.tech_node,
      });

      setResults(result as any);
    } catch (err: any) {
      setError(err.message || 'Simulation failed');
    } finally {
      setRunning(false);
      setLoading(false);
    }
  };

  const runSweep = async () => {
    try {
      setRunning(true);
      setLoading(true);
      setError(null);

      const result = await simulationAPI.sweep({
        wn_min: 0.1,
        wn_max: 5.0,
        wp: params.wp,
        vdd: params.vdd,
        temp: params.temp,
        cl_ff: params.cl_ff,
        corner: params.corner,
        tech_node: params.tech_node,
      });

      setResults(result as any);
    } catch (err: any) {
      setError(err.message || 'Sweep failed');
    } finally {
      setRunning(false);
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 shadow-lg interactive-surface">
      <h2 className="text-2xl font-bold text-white mb-6">CMOS Simulator</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* WN Input */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            WN (µm)
          </label>
          <input
            type="number"
            value={params.wn}
            onChange={(e) => handleInputChange('wn', parseFloat(e.target.value))}
            step="0.1"
            min="0.1"
            max="10"
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:border-cyan-400"
          />
        </div>

        {/* WP Input */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            WP (µm)
          </label>
          <input
            type="number"
            value={params.wp}
            onChange={(e) => handleInputChange('wp', parseFloat(e.target.value))}
            step="0.1"
            min="0.1"
            max="10"
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:border-cyan-400"
          />
        </div>

        {/* VDD Input */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            VDD (V)
          </label>
          <input
            type="number"
            value={params.vdd}
            onChange={(e) => handleInputChange('vdd', parseFloat(e.target.value))}
            step="0.1"
            min="0.5"
            max="3.3"
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:border-cyan-400"
          />
        </div>

        {/* Temperature Input */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Temp (°C)
          </label>
          <input
            type="number"
            value={params.temp}
            onChange={(e) => handleInputChange('temp', parseInt(e.target.value))}
            min="-40"
            max="125"
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:border-cyan-400"
          />
        </div>

        {/* CL_FF Input */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Load (femtofarads)
          </label>
          <input
            type="number"
            value={params.cl_ff}
            onChange={(e) => handleInputChange('cl_ff', parseFloat(e.target.value))}
            step="0.1"
            min="0.1"
            max="100"
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:border-cyan-400"
          />
        </div>

        {/* Corner Select */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Corner
          </label>
          <select
            value={params.corner}
            onChange={(e) => handleInputChange('corner', e.target.value)}
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:border-cyan-400"
          >
            {CORNERS.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>

        {/* Tech Node Select */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Tech Node (nm)
          </label>
          <select
            value={params.tech_node}
            onChange={(e) => handleInputChange('tech_node', parseInt(e.target.value))}
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:border-cyan-400"
          >
            {TECH_NODES.map((n) => (
              <option key={n} value={n}>
                {n}nm
              </option>
            ))}
          </select>
        </div>

        {/* Placeholder for alignment */}
        <div></div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <button
          onClick={runSimulation}
          disabled={loading}
          className="flex-1 px-6 py-3 bg-gradient-to-r from-cyan-400 to-blue-600 text-white font-semibold rounded-lg hover:opacity-90 disabled:opacity-50 interactive-button"
        >
          {loading ? 'Running...' : 'Run Simulation'}
        </button>
        <button
          onClick={runSweep}
          disabled={loading}
          className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-400 to-pink-600 text-white font-semibold rounded-lg hover:opacity-90 disabled:opacity-50 interactive-button"
        >
          {loading ? 'Sweeping...' : 'Run WN Sweep'}
        </button>
      </div>
    </div>
  );
}
