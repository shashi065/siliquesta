'use client';

import React from 'react';
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { TrendingUp, Clock, Zap, Target, CheckCircle2 } from 'lucide-react';

interface Project {
  id: string;
  name: string;
  created: string;
  status: 'completed' | 'running' | 'failed';
  simulations: number;
  accuracy: number;
}

interface DashboardMetrics {
  totalSimulations: number;
  avgAccuracy: number;
  successRate: number;
  totalTime: number;
}

const mockProjects: Project[] = [
  {
    id: '1',
    name: 'NAND Gate Optimization',
    created: '2 hours ago',
    status: 'completed',
    simulations: 2847,
    accuracy: 96.8,
  },
  {
    id: '2',
    name: 'Ring Oscillator Analysis',
    created: '1 day ago',
    status: 'completed',
    simulations: 1523,
    accuracy: 94.2,
  },
  {
    id: '3',
    name: 'PLL Stability Study',
    created: '3 days ago',
    status: 'completed',
    simulations: 3421,
    accuracy: 97.5,
  },
];

const mockTrendData = [
  { date: 'Mon', simulations: 2400, accuracy: 94.2 },
  { date: 'Tue', simulations: 1398, accuracy: 93.8 },
  { date: 'Wed', simulations: 2800, accuracy: 95.1 },
  { date: 'Thu', simulations: 3800, accuracy: 96.4 },
  { date: 'Fri', simulations: 3490, accuracy: 95.9 },
  { date: 'Sat', simulations: 2105, accuracy: 94.7 },
  { date: 'Sun', simulations: 2100, accuracy: 95.3 },
];

const mockAccuracyData = [
  { range: '90-92%', projects: 2 },
  { range: '92-94%', projects: 5 },
  { range: '94-96%', projects: 12 },
  { range: '96-98%', projects: 18 },
  { range: '98-99%', projects: 8 },
];

export default function Dashboard() {
  const metrics: DashboardMetrics = {
    totalSimulations: 9791,
    avgAccuracy: 95.3,
    successRate: 98.2,
    totalTime: 142.5,
  };

  const chartMotion = {
    isAnimationActive: true,
    animationDuration: 650,
    animationEasing: 'ease-out' as const,
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">Dashboard</h1>
          <p className="text-slate-400">Overview of your simulations and projects</p>
        </div>
        <button className="px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-white rounded-lg font-medium interactive-button">
          New Project
        </button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          icon={<Zap className="w-6 h-6 text-cyan-400" />}
          label="Total Simulations"
          value={metrics.totalSimulations.toLocaleString()}
          trend="+12%"
          trendUp={true}
        />
        <MetricCard
          icon={<Target className="w-6 h-6 text-emerald-400" />}
          label="Avg Accuracy"
          value={`${metrics.avgAccuracy}%`}
          trend="+0.8%"
          trendUp={true}
        />
        <MetricCard
          icon={<CheckCircle2 className="w-6 h-6 text-blue-400" />}
          label="Success Rate"
          value={`${metrics.successRate}%`}
          trend="+2.1%"
          trendUp={true}
        />
        <MetricCard
          icon={<Clock className="w-6 h-6 text-purple-400" />}
          label="Compute Hours"
          value={metrics.totalTime.toFixed(1)}
          trend="-5%"
          trendUp={false}
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Simulation Trends */}
        <div className="lg:col-span-2 bg-slate-800 rounded-xl p-6 border border-slate-700 interactive-surface">
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-white">Simulation Trends</h2>
            <p className="text-sm text-slate-400">Weekly activity</p>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={mockTrendData}>
              <defs>
                <linearGradient id="colorSim" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#06B6D4" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }} />
              <Area
                type="monotone"
                dataKey="simulations"
                stroke="#06B6D4"
                fillOpacity={1}
                fill="url(#colorSim)"
                {...chartMotion}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Accuracy Distribution */}
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 interactive-surface">
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-white">Accuracy Distribution</h2>
            <p className="text-sm text-slate-400">Your projects</p>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={mockAccuracyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="range" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }} />
              <Bar dataKey="projects" fill="#10b981" radius={[8, 8, 0, 0]} {...chartMotion} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Accuracy Trend Line */}
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 interactive-surface">
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-white">Accuracy Trend</h2>
          <p className="text-sm text-slate-400">7-day moving average</p>
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={mockTrendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="date" stroke="#94a3b8" />
            <YAxis domain={[92, 97]} stroke="#94a3b8" />
            <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }} />
            <Legend />
            <Line
              type="monotone"
              dataKey="accuracy"
              stroke="#06B6D4"
              strokeWidth={3}
              dot={{ fill: '#06B6D4', r: 5 }}
              activeDot={{ r: 7 }}
              {...chartMotion}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Recent Projects */}
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 interactive-surface">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-lg font-semibold text-white">Recent Projects</h2>
            <p className="text-sm text-slate-400">Your latest work</p>
          </div>
          <a href="/projects" className="text-cyan-400 hover:text-cyan-300 text-sm font-medium interactive-button rounded-lg px-2 py-1 -mx-2 -my-1">
            View All →
          </a>
        </div>

        <div className="space-y-4">
          {mockProjects.map((project) => (
            <div
              key={project.id}
              className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg hover:bg-slate-700 transition border border-slate-600 interactive-surface"
            >
              <div className="flex-1">
                <h3 className="font-medium text-white">{project.name}</h3>
                <div className="flex gap-4 mt-2 text-sm text-slate-400">
                  <span>{project.created}</span>
                  <span>•</span>
                  <span>{project.simulations.toLocaleString()} simulations</span>
                </div>
              </div>

              <div className="flex items-center gap-6">
                <div className="text-right">
                  <div className="text-sm font-medium text-white">{project.accuracy}%</div>
                  <div className="text-xs text-slate-400">Accuracy</div>
                </div>

                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    project.status === 'completed'
                      ? 'bg-emerald-900 text-emerald-200'
                      : project.status === 'running'
                      ? 'bg-blue-900 text-blue-200'
                      : 'bg-red-900 text-red-200'
                  }`}
                >
                  {project.status.charAt(0).toUpperCase() + project.status.slice(1)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

interface MetricCardProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  trend: string;
  trendUp: boolean;
}

function MetricCard({ icon, label, value, trend, trendUp }: MetricCardProps) {
  return (
    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 interactive-surface">
      <div className="flex items-start justify-between mb-4">
        <div className="p-3 bg-slate-700 rounded-lg">{icon}</div>
        <div className={`flex items-center gap-1 text-sm font-medium ${trendUp ? 'text-emerald-400' : 'text-orange-400'}`}>
          <TrendingUp className="w-4 h-4" />
          {trend}
        </div>
      </div>
      <div className="text-sm text-slate-400 mb-1">{label}</div>
      <div className="text-2xl font-bold text-white">{value}</div>
    </div>
  );
}
