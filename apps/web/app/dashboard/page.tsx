'use client';

import React from 'react';
import Layout from '@/components/Layout';
import Dashboard from '@/components/Dashboard';
import SimulationVisualization from '@/components/SimulationVisualization';
import WaveformVisualization from '@/components/WaveformVisualization';
import TrustPanel from '@/components/TrustPanel';
import { ErrorBoundary } from '@/components/ErrorBoundary';

export default function DashboardPage() {
  return (
    <Layout>
      <ErrorBoundary>
        <div className="space-y-8">
          {/* Main Dashboard */}
          <Dashboard />

          {/* Simulation Visualizations */}
          <section className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-3xl font-bold text-white">Simulation Results</h2>
                <p className="text-slate-400 mt-2">Latest circuit analysis and performance metrics</p>
              </div>
            </div>

            <SimulationVisualization type="all" title="Circuit Performance Analysis" />
          </section>

          {/* Waveform Analysis */}
          <section className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">Signal Analysis</h2>
              <p className="text-slate-400">Time-domain waveform visualization</p>
            </div>

            <WaveformVisualization title="Output Signal" timeScale="ns" />
          </section>

          {/* Trust & Confidence */}
          <section className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">Model Confidence & Reliability</h2>
              <p className="text-slate-400">AI-powered accuracy assessment and validation metrics</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <TrustPanel />
              </div>

              {/* Additional Trust Information */}
              <div className="space-y-6">
                <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                  <h3 className="text-lg font-semibold text-white mb-4">Validation Status</h3>
                  <div className="space-y-3">
                    <ValidationItem
                      label="Silicon Area"
                      value="2.4 mm²"
                      status="optimal"
                    />
                    <ValidationItem
                      label="Power Budget"
                      value="45.2 mW"
                      status="optimal"
                    />
                    <ValidationItem
                      label="Timing Slack"
                      value="0.8 ns"
                      status="good"
                    />
                    <ValidationItem
                      label="DFM Score"
                      value="94%"
                      status="optimal"
                    />
                  </div>
                </div>

                <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                  <h3 className="text-lg font-semibold text-white mb-4">Next Steps</h3>
                  <ol className="space-y-2 text-sm text-slate-300">
                    <li className="flex gap-2">
                      <span className="text-cyan-400 font-bold">1.</span>
                      <span>Review PVT corners</span>
                    </li>
                    <li className="flex gap-2">
                      <span className="text-cyan-400 font-bold">2.</span>
                      <span>Run DRC/LVS checks</span>
                    </li>
                    <li className="flex gap-2">
                      <span className="text-cyan-400 font-bold">3.</span>
                      <span>Prepare for tapeout</span>
                    </li>
                  </ol>
                </div>
              </div>
            </div>
          </section>
        </div>
      </ErrorBoundary>
    </Layout>
  );
}

function ValidationItem({
  label,
  value,
  status,
}: {
  label: string;
  value: string;
  status: 'optimal' | 'good' | 'warning';
}) {
  const colors = {
    optimal: 'text-emerald-400',
    good: 'text-blue-400',
    warning: 'text-yellow-400',
  };

  const icons = {
    optimal: '✓',
    good: '◐',
    warning: '⚠',
  };

  return (
    <div className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg border border-slate-600">
      <span className="text-sm text-slate-400">{label}</span>
      <div className="flex items-center gap-2">
        <span className={`text-sm font-semibold ${colors[status]}`}>{value}</span>
        <span className={`text-lg ${colors[status]}`}>{icons[status]}</span>
      </div>
    </div>
  );
}
