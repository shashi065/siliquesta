'use client';

import React from 'react';
import { Loader, AlertTriangle, XCircle, CheckCircle2 } from 'lucide-react';

/* Loading States */

export function LoadingSpinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeClasses = {
    sm: 'w-6 h-6',
    md: 'w-10 h-10',
    lg: 'w-16 h-16',
  };

  return (
    <div className="flex items-center justify-center">
      <Loader className={`${sizeClasses[size]} text-cyan-400 animate-spin`} />
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 animate-pulse">
      <div className="space-y-4">
        <div className="h-6 bg-slate-700 rounded w-3/4" />
        <div className="space-y-2">
          <div className="h-4 bg-slate-700 rounded w-full" />
          <div className="h-4 bg-slate-700 rounded w-5/6" />
        </div>
        <div className="h-32 bg-slate-700 rounded" />
      </div>
    </div>
  );
}

export function SimulationLoadingState() {
  return (
    <div className="bg-slate-800 rounded-xl p-8 border border-slate-700 text-center">
      <div className="flex justify-center mb-6">
        <div className="relative w-16 h-16">
          <div className="absolute inset-0 rounded-full border-4 border-slate-700" />
          <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-cyan-400 border-r-cyan-400 animate-spin" />
        </div>
      </div>
      <h3 className="text-xl font-semibold text-white mb-2">Running Simulation</h3>
      <p className="text-slate-400 mb-6">Computing physics-based metrics...</p>

      {/* Progress bar */}
      <div className="w-full max-w-xs mx-auto mb-4">
        <div className="flex justify-between text-xs text-slate-400 mb-2">
          <span>Progress</span>
          <span>67%</span>
        </div>
        <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
          <div className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 w-2/3 transition-all" />
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-2 text-sm text-slate-400 mt-6">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>Parameter validation</span>
        </div>
        <div className="flex items-center gap-2">
          <Loader className="w-4 h-4 text-cyan-400 animate-spin" />
          <span>SPICE simulation</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full border-2 border-slate-600" />
          <span>ML prediction</span>
        </div>
      </div>
    </div>
  );
}

/* Error States */

export function ErrorState({
  title = 'Something went wrong',
  message = 'An unexpected error occurred. Please try again.',
  onRetry,
}: {
  title?: string;
  message?: string;
  onRetry?: () => void;
}) {
  return (
    <div className="bg-red-900/20 border border-red-700 rounded-xl p-8 text-center">
      <div className="flex justify-center mb-4">
        <XCircle className="w-12 h-12 text-red-400" />
      </div>
      <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
      <p className="text-red-200 mb-6">{message}</p>
      <div className="flex gap-3 justify-center">
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition"
          >
            Try Again
          </button>
        )}
        <button className="px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition">
          Contact Support
        </button>
      </div>
    </div>
  );
}

export function ValidationError({
  errors,
}: {
  errors: { field: string; message: string }[];
}) {
  return (
    <div className="bg-yellow-900/20 border border-yellow-700 rounded-xl p-6">
      <div className="flex items-start gap-3 mb-6">
        <AlertTriangle className="w-6 h-6 text-yellow-400 flex-shrink-0 mt-0.5" />
        <div>
          <h3 className="text-lg font-semibold text-white mb-1">Validation Errors</h3>
          <p className="text-yellow-200 text-sm">Please fix the following issues:</p>
        </div>
      </div>

      <div className="space-y-3">
        {errors.map((error, idx) => (
          <div key={idx} className="flex gap-3 p-3 bg-yellow-900/30 rounded-lg border border-yellow-700">
            <div className="text-yellow-400 font-semibold flex-shrink-0">{error.field}</div>
            <div className="text-yellow-200 text-sm">{error.message}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* Success State */

export function SuccessMessage({
  title = 'Success!',
  message = 'Operation completed successfully.',
  action,
}: {
  title?: string;
  message?: string;
  action?: { label: string; onClick: () => void };
}) {
  return (
    <div className="bg-emerald-900/20 border border-emerald-700 rounded-xl p-6">
      <div className="flex items-start gap-3">
        <CheckCircle2 className="w-6 h-6 text-emerald-400 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-white mb-1">{title}</h3>
          <p className="text-emerald-200">{message}</p>
          {action && (
            <button
              onClick={action.onClick}
              className="mt-4 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium transition text-sm"
            >
              {action.label}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

/* Toast Notification */

export function Toast({
  type = 'info',
  title,
  message,
}: {
  type?: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
}) {
  const colors = {
    success: 'bg-emerald-600 border-emerald-500',
    error: 'bg-red-600 border-red-500',
    warning: 'bg-yellow-600 border-yellow-500',
    info: 'bg-blue-600 border-blue-500',
  };

  const icons = {
    success: <CheckCircle2 className="w-5 h-5" />,
    error: <XCircle className="w-5 h-5" />,
    warning: <AlertTriangle className="w-5 h-5" />,
    info: <Loader className="w-5 h-5" />,
  };

  return (
    <div
      className={`${colors[type]} border rounded-lg p-4 flex gap-3 items-start text-white shadow-lg animate-in slide-in-from-top`}
    >
      {icons[type]}
      <div>
        <h4 className="font-semibold">{title}</h4>
        <p className="text-sm opacity-90">{message}</p>
      </div>
    </div>
  );
}
