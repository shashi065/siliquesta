'use client';

import React, { useEffect, useState } from 'react';
import {
  LineChart, Line, BarChart, Bar, ComposedChart, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area
} from 'recharts';

interface SimulationResult {
  frequency?: number;
  gain?: number;
  power?: number;
  delay?: number;
  phase?: number;
}

interface SimVisualizationProps {
  data?: SimulationResult[];
  type?: 'gain' | 'power' | 'delay' | 'all';
  title?: string;
}

// Mock data for different metrics
const mockGainData = [
  { freq: 1, gain: 12.5, phase: -45 },
  { freq: 10, gain: 18.2, phase: -60 },
  { freq: 100, gain: 25.8, phase: -90 },
  { freq: 1000, gain: 28.5, phase: -120 },
  { freq: 10000, gain: 22.3, phase: -135 },
  { freq: 100000, gain: 10.5, phase: -150 },
];

const mockPowerData = [
  { voltage: 0.6, power: 45.2, leakage: 2.1 },
  { voltage: 0.8, power: 78.5, leakage: 5.3 },
  { voltage: 1.0, power: 125.8, leakage: 12.4 },
  { voltage: 1.2, power: 185.2, leakage: 28.9 },
];

const mockDelayData = [
  { temp: -40, delay: 2.145, slew: 0.32 },
  { temp: 0, delay: 2.098, slew: 0.31 },
  { temp: 25, delay: 2.050, slew: 0.30 },
  { temp: 50, delay: 2.015, slew: 0.29 },
  { temp: 85, delay: 1.985, slew: 0.28 },
  { temp: 125, delay: 1.952, slew: 0.27 },
];

export default function SimulationVisualization({
  data,
  type = 'all',
  title = 'Simulation Results',
}: SimVisualizationProps) {
  const [showLoadHint, setShowLoadHint] = useState(true);

  useEffect(() => {
    setShowLoadHint(true);
    const timer = window.setTimeout(() => setShowLoadHint(false), 320);

    return () => window.clearTimeout(timer);
  }, [type, title]);

  const lineMotion = {
    isAnimationActive: true,
    animationDuration: 680,
    animationEasing: 'ease-out' as const,
  };

  const areaMotion = {
    isAnimationActive: true,
    animationDuration: 620,
    animationEasing: 'ease-out' as const,
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">{title}</h2>
        <div className="flex items-center gap-2">
          {showLoadHint && (
            <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full border border-cyan-400/20 bg-cyan-400/6 text-xs font-medium text-cyan-200">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-300 animate-pulse" />
              Syncing visuals
            </div>
          )}
          <button className="px-3 py-1 text-sm bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg interactive-button border border-slate-600/80">
            Export
          </button>
          <button className="px-3 py-1 text-sm bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg interactive-button border border-slate-600/80">
            Compare
          </button>
        </div>
      </div>

      {/* Gain & Phase Response */}
      {(type === 'gain' || type === 'all') && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Gain Response */}
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 interactive-surface">
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-white">Frequency Response</h3>
              <p className="text-sm text-slate-400">Gain (dB) vs Frequency</p>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={mockGainData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="freq"
                  scale="log"
                  stroke="#94a3b8"
                  label={{ value: 'Frequency (Hz)', position: 'insideBottom', offset: -5 }}
                />
                <YAxis stroke="#94a3b8" label={{ value: 'Gain (dB)', angle: -90, position: 'insideLeft' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="gain"
                  stroke="#06B6D4"
                  strokeWidth={2}
                  dot={{ fill: '#06B6D4' }}
                  name="Gain (dB)"
                  {...lineMotion}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Phase Response */}
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 interactive-surface">
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-white">Phase Response</h3>
              <p className="text-sm text-slate-400">Phase (degrees) vs Frequency</p>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={mockGainData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="freq"
                  scale="log"
                  stroke="#94a3b8"
                  label={{ value: 'Frequency (Hz)', position: 'insideBottom', offset: -5 }}
                />
                <YAxis stroke="#94a3b8" label={{ value: 'Phase (°)', angle: -90, position: 'insideLeft' }} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="phase"
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  dot={{ fill: '#8b5cf6' }}
                  name="Phase (°)"
                  {...lineMotion}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Power Consumption */}
      {(type === 'power' || type === 'all') && (
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 interactive-surface">
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-white">Power Consumption Analysis</h3>
            <p className="text-sm text-slate-400">Dynamic and Leakage Power vs Supply Voltage</p>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={mockPowerData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis
                dataKey="voltage"
                stroke="#94a3b8"
                label={{ value: 'Supply Voltage (V)', position: 'insideBottom', offset: -5 }}
              />
              <YAxis stroke="#94a3b8" label={{ value: 'Power (mW)', angle: -90, position: 'insideLeft' }} />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }} />
              <Legend />
              <Area
                type="monotone"
                dataKey="leakage"
                stackId="1"
                stroke="#ef4444"
                fill="#ef4444"
                opacity={0.6}
                name="Leakage"
                {...areaMotion}
              />
              <Area
                type="monotone"
                dataKey="power"
                stackId="1"
                stroke="#06B6D4"
                fill="#06B6D4"
                opacity={0.6}
                name="Dynamic"
                {...areaMotion}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Propagation Delay */}
      {(type === 'delay' || type === 'all') && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Delay vs Temperature */}
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 interactive-surface">
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-white">Delay Variation</h3>
              <p className="text-sm text-slate-400">Propagation Delay vs Temperature</p>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={mockDelayData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="temp"
                  stroke="#94a3b8"
                  label={{ value: 'Temperature (°C)', position: 'insideBottom', offset: -5 }}
                />
                <YAxis stroke="#94a3b8" label={{ value: 'Delay (ns)', angle: -90, position: 'insideLeft' }} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="delay"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  dot={{ fill: '#f59e0b' }}
                  name="Propagation Delay"
                  {...lineMotion}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Slew Rate vs Temperature */}
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 interactive-surface">
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-white">Slew Rate Analysis</h3>
              <p className="text-sm text-slate-400">Output Slew Rate vs Temperature</p>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={mockDelayData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="temp"
                  stroke="#94a3b8"
                  label={{ value: 'Temperature (°C)', position: 'insideBottom', offset: -5 }}
                />
                <YAxis stroke="#94a3b8" label={{ value: 'Slew Rate (V/ns)', angle: -90, position: 'insideLeft' }} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="slew"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={{ fill: '#10b981' }}
                  name="Slew Rate"
                  {...lineMotion}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Key Metrics Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricBox label="Max Gain" value="28.5 dB" unit="" />
        <MetricBox label="Total Power" value="185.2" unit="mW" />
        <MetricBox label="Max Delay" value="2.145" unit="ns" />
        <MetricBox label="Phase Margin" value="65°" unit="" />
      </div>
    </div>
  );
}

function MetricBox({ label, value, unit }: { label: string; value: string; unit: string }) {
  return (
    <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600 interactive-surface">
      <div className="text-sm text-slate-400 mb-2">{label}</div>
      <div className="text-xl font-bold text-white">
        {value} <span className="text-sm text-slate-400">{unit}</span>
      </div>
    </div>
  );
}
