'use client';


import { useDesignStore } from '@/store/designStore';

export default function ResultsDisplay() {
  const { results, error } = useDesignStore();

  if (error) {
    return (
      <div className="bg-red-900 border border-red-700 rounded-lg p-4 mb-6">
        <p className="text-red-100">❌ {error}</p>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 text-center">
        <p className="text-slate-400">Run a simulation to see results</p>
      </div>
    );
  }

  const metrics = [
    { label: 'Frequency', value: (results as any).freq?.toFixed(2) || 'N/A', unit: 'GHz' },
    { label: 'Dynamic Power', value: (results as any).power_dyn?.toFixed(3) || (results as any).power?.toFixed(3) || 'N/A', unit: 'mW' },
    { label: 'Static Power', value: (results as any).power_leak?.toFixed(3) || 'N/A', unit: 'mW' },
    { label: 'Delay', value: (results as any).delay?.toFixed(2) || 'N/A', unit: 'ps' },
    { label: 'FOM', value: (results as any).fom?.toFixed(3) || 'N/A', unit: 'GHz/mW' },
    { label: 'Temperature', value: (results as any).temp_actual?.toFixed(1) || 'N/A', unit: '°C' },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {metrics.map((metric) => (
        <div
          key={metric.label}
          className="bg-gradient-to-br from-slate-800 to-slate-700 border border-slate-600 rounded-lg p-4"
        >
          <p className="text-slate-400 text-sm font-medium">{metric.label}</p>
          <p className="text-2xl font-bold text-cyan-400 mt-2">
            {metric.value} <span className="text-sm text-slate-400">{metric.unit}</span>
          </p>
        </div>
      ))}
    </div>
  );
}
