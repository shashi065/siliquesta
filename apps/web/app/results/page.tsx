'use client';

import React, { startTransition, useState } from 'react';
import Layout from '@/components/Layout';
import SimulationVisualization from '@/components/SimulationVisualization';
import WaveformVisualization from '@/components/WaveformVisualization';
import TrustPanel from '@/components/TrustPanel';
import { Button, Tabs, StatsGrid } from '@/components/UIComponents';
import { Download, Share2, BookmarkPlus, Copy } from 'lucide-react';

export default function ResultsPage() {
  const [activeTab, setActiveTab] = useState('overview');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopy = (id: string) => {
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const tabs = [
    { label: 'Overview', value: 'overview' },
    { label: 'Analysis', value: 'analysis' },
    { label: 'Waveforms', value: 'waveforms' },
    { label: 'Confidence', value: 'confidence' },
    { label: 'Comparison', value: 'comparison' },
  ];

  return (
    <Layout>
      <div className="space-y-8 pb-12">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">Simulation #SIM-2024-0847</h1>
            <p className="text-slate-400">NAND Gate Optimization - Completed 2 hours ago</p>
          </div>

          <div className="flex gap-2">
            <Button variant="secondary" size="sm" icon={<BookmarkPlus className="w-4 h-4" />}>
              Save
            </Button>
            <Button variant="secondary" size="sm" icon={<Share2 className="w-4 h-4" />}>
              Share
            </Button>
            <Button variant="secondary" size="sm" icon={<Download className="w-4 h-4" />}>
              Export
            </Button>
          </div>
        </div>

        {/* Project ID Card */}
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 flex items-center justify-between interactive-surface">
          <div>
            <div className="text-xs text-slate-400 uppercase font-semibold">Project ID</div>
            <div className="text-lg font-mono text-cyan-400">sim_24084701_nand_opt</div>
          </div>
          <button
            onClick={() => handleCopy('sim_24084701_nand_opt')}
            className="p-2 hover:bg-slate-700 rounded-lg interactive-button text-slate-400 hover:text-slate-200"
          >
            <Copy className="w-5 h-5" />
          </button>
          {copiedId && <span className="text-emerald-400 text-sm">Copied!</span>}
        </div>

        {/* Tab Navigation */}
        <Tabs tabs={tabs} activeTab={activeTab} onTabChange={(value) => startTransition(() => setActiveTab(value))} />

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Key Metrics */}
            <StatsGrid
              stats={[
                { label: 'Status', value: 'Completed', unit: '✓' },
                { label: 'Simulation Time', value: '8.34', unit: 's' },
                { label: 'Parameters', value: '127', unit: 'tested' },
                { label: 'Data Points', value: '14.2K', unit: 'samples' },
              ]}
            />

            {/* Simulation Results */}
            <SimulationVisualization type="gain" title="Frequency Response Analysis" />
          </div>
        )}

        {activeTab === 'analysis' && (
          <div className="space-y-6">
            <SimulationVisualization type="all" title="Complete Analysis" />
          </div>
        )}

        {activeTab === 'waveforms' && (
          <div className="space-y-6">
            <WaveformVisualization title="Input/Output Waveforms" timeScale="ns" />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <WaveformVisualization title="Clock Signal" timeScale="ns" />
              <WaveformVisualization title="Data Signal" timeScale="ns" />
            </div>
          </div>
        )}

        {activeTab === 'confidence' && (
          <div className="space-y-6">
            <TrustPanel />

            {/* Additional Confidence Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 interactive-surface">
                <h3 className="text-lg font-semibold text-white mb-4">Performance Metrics</h3>
                <div className="space-y-3 text-sm">
                  <MetricRow label="Setup Time" value="0.82 ns" />
                  <MetricRow label="Hold Time" value="0.15 ns" />
                  <MetricRow label="Propagation Delay" value="2.05 ns" />
                  <MetricRow label="Clock Period" value="4.00 ns" />
                  <MetricRow label="Power Dissipation" value="125.3 mW" />
                  <MetricRow label="Leakage Power" value="12.4 µW" />
                </div>
              </div>

              <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 interactive-surface">
                <h3 className="text-lg font-semibold text-white mb-4">Design Parameters</h3>
                <div className="space-y-3 text-sm">
                  <MetricRow label="Transistor Width (µm)" value="2.0" />
                  <MetricRow label="Transistor Length (nm)" value="28" />
                  <MetricRow label="Supply Voltage" value="1.2 V" />
                  <MetricRow label="Temperature" value="25°C" />
                  <MetricRow label="Process Corner" value="TT" />
                  <MetricRow label="Load Capacitance" value="1.5 pF" />
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'comparison' && (
          <div className="space-y-6">
            <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 interactive-surface">
              <h3 className="text-lg font-semibold text-white mb-6">Compare with Previous Simulations</h3>

              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="text-left py-3 px-4 text-slate-400 font-medium">Metric</th>
                      <th className="text-right py-3 px-4 text-slate-400 font-medium">
                        Current <span className="inline-block ml-2 w-3 h-3 rounded-full bg-cyan-400" />
                      </th>
                      <th className="text-right py-3 px-4 text-slate-400 font-medium">
                        Previous <span className="inline-block ml-2 w-3 h-3 rounded-full bg-slate-600" />
                      </th>
                      <th className="text-right py-3 px-4 text-slate-400 font-medium">Change</th>
                    </tr>
                  </thead>
                  <tbody>
                    <ComparisonRow
                      metric="Delay (ns)"
                      current={2.05}
                      previous={2.18}
                      improved={true}
                    />
                    <ComparisonRow metric="Power (mW)" current={125.3} previous={138.5} improved={true} />
                    <ComparisonRow metric="Area (µm²)" current={1048} previous={1125} improved={true} />
                    <ComparisonRow metric="Accuracy" current={96.8} previous={94.2} improved={true} />
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center py-2 px-3 bg-slate-700/30 rounded border border-slate-600 interactive-surface">
      <span className="text-slate-400">{label}</span>
      <span className="font-semibold text-white">{value}</span>
    </div>
  );
}

function ComparisonRow({
  metric,
  current,
  previous,
  improved,
}: {
  metric: string;
  current: number;
  previous: number;
  improved: boolean;
}) {
  const change = current - previous;
  const percentChange = ((change / previous) * 100).toFixed(1);
  const isPositive = improved ? change < 0 : change > 0;

  return (
    <tr className="border-b border-slate-700 hover:bg-slate-700/30 transition-colors duration-150">
      <td className="py-3 px-4 text-slate-300">{metric}</td>
      <td className="py-3 px-4 text-right text-cyan-400 font-semibold">{current}</td>
      <td className="py-3 px-4 text-right text-slate-400">{previous}</td>
      <td className={`py-3 px-4 text-right font-semibold ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
        {isPositive ? '↓' : '↑'} {percentChange}%
      </td>
    </tr>
  );
}
