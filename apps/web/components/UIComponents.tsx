'use client';

import React from 'react';

/* Premium UI Components */

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  icon?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', isLoading, icon, children, className, ...props }, ref) => {
    const variants = {
      primary: 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-[0_12px_32px_rgba(34,211,238,0.14)]',
      secondary: 'bg-slate-700 hover:bg-slate-600 text-slate-100 border border-slate-600 hover:border-slate-500',
      ghost: 'hover:bg-slate-700/50 text-slate-300 hover:text-white border border-transparent',
      danger: 'bg-red-600 hover:bg-red-500 text-white shadow-[0_12px_32px_rgba(239,68,68,0.14)]',
    };

    const sizes = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2.5 text-base',
      lg: 'px-6 py-3 text-lg',
    };

    return (
      <button
        ref={ref}
        className={`
          rounded-lg font-semibold transition-all duration-150 interactive-button
          disabled:opacity-50 disabled:cursor-not-allowed
          flex items-center gap-2 justify-center
          ${variants[variant]}
          ${sizes[size]}
          ${className}
        `}
        disabled={isLoading || props.disabled}
        {...props}
      >
        {isLoading ? (
          <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
        ) : (
          icon
        )}
        {children}
      </button>
    );
  }
);
Button.displayName = 'Button';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
  glow?: boolean;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ hover = true, glow = false, className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={`
        bg-slate-800 rounded-xl border border-slate-700 p-6
        transition-all duration-300
        ${hover ? 'hover:border-slate-600 hover:shadow-lg hover:shadow-cyan-500/5' : ''}
        ${glow ? 'shadow-lg shadow-cyan-500/10' : ''}
        ${className}
      `}
      {...props}
    >
      {children}
    </div>
  )
);
Card.displayName = 'Card';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info';
}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ variant = 'default', className, children, ...props }, ref) => {
    const variants = {
      default: 'bg-slate-700 text-slate-300',
      success: 'bg-emerald-900/40 text-emerald-300 border border-emerald-700',
      warning: 'bg-yellow-900/40 text-yellow-300 border border-yellow-700',
      danger: 'bg-red-900/40 text-red-300 border border-red-700',
      info: 'bg-blue-900/40 text-blue-300 border border-blue-700',
    };

    return (
      <span
        ref={ref}
        className={`
          inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold
          ${variants[variant]}
          ${className}
        `}
        {...props}
      >
        {children}
      </span>
    );
  }
);
Badge.displayName = 'Badge';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, icon, className, ...props }, ref) => (
    <div>
      {label && <label className="block text-sm font-medium text-white mb-2">{label}</label>}
      <div className="relative">
        {icon && <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">{icon}</div>}
        <input
          ref={ref}
          className={`
            w-full px-4 py-2.5 bg-slate-700 border border-slate-600 rounded-lg
            text-white placeholder-slate-400
            focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20
            transition-all duration-200
            ${icon ? 'pl-10' : ''}
            ${error ? 'border-red-500 focus:ring-red-500/20' : ''}
            ${className}
          `}
          {...props}
        />
      </div>
      {error && <p className="text-red-400 text-sm mt-1">{error}</p>}
    </div>
  )
);
Input.displayName = 'Input';

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options: { value: string; label: string }[];
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, options, className, ...props }, ref) => (
    <div>
      {label && <label className="block text-sm font-medium text-white mb-2">{label}</label>}
      <select
        ref={ref}
        className={`
          w-full px-4 py-2.5 bg-slate-700 border border-slate-600 rounded-lg
          text-white
          focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20
          transition-all duration-200
          ${error ? 'border-red-500 focus:ring-red-500/20' : ''}
          ${className}
        `}
        {...props}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && <p className="text-red-400 text-sm mt-1">{error}</p>}
    </div>
  )
);
Select.displayName = 'Select';

interface ProgressBarProps {
  value: number;
  max?: number;
  showLabel?: boolean;
  color?: 'cyan' | 'emerald' | 'blue' | 'orange' | 'red';
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  showLabel = true,
  color = 'cyan',
}) => {
  const percentage = (value / max) * 100;
  const colors = {
    cyan: 'from-cyan-500 to-cyan-400',
    emerald: 'from-emerald-500 to-emerald-400',
    blue: 'from-blue-500 to-blue-400',
    orange: 'from-orange-500 to-orange-400',
    red: 'from-red-500 to-red-400',
  };

  return (
    <div>
      <div className="flex justify-between text-sm mb-2">
        <span className="text-slate-300">Progress</span>
        {showLabel && <span className="text-cyan-400 font-semibold">{percentage.toFixed(0)}%</span>}
      </div>
      <div className="w-full bg-slate-700 rounded-full h-3 overflow-hidden">
        <div
          className={`h-full bg-gradient-to-r ${colors[color]} transition-all duration-500 rounded-full`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

interface StatsProps {
  stats: { label: string; value: string | number; unit?: string; icon?: React.ReactNode }[];
}

export const StatsGrid: React.FC<StatsProps> = ({ stats }) => (
  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
    {stats.map((stat, idx) => (
      <div key={idx} className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
        <div className="flex items-start justify-between mb-2">
          {stat.icon && <div className="text-cyan-400">{stat.icon}</div>}
        </div>
        <div className="text-xs text-slate-400 mb-1">{stat.label}</div>
        <div className="text-2xl font-bold text-white">
          {stat.value}
          {stat.unit && <span className="text-sm text-slate-400 ml-1">{stat.unit}</span>}
        </div>
      </div>
    ))}
  </div>
);

interface TabsProps {
  tabs: { label: string; value: string }[];
  activeTab: string;
  onTabChange: (value: string) => void;
}

export const Tabs: React.FC<TabsProps> = ({ tabs, activeTab, onTabChange }) => (
  <div>
    <div className="flex gap-2 border-b border-slate-700 overflow-x-auto pb-1">
      {tabs.map((tab) => (
        <button
          key={tab.value}
          onClick={() => onTabChange(tab.value)}
          aria-pressed={activeTab === tab.value}
          className={`
            px-4 py-3 font-medium text-sm transition-all duration-200 border-b-2 rounded-t-xl interactive-button whitespace-nowrap
            ${
              activeTab === tab.value
                ? 'text-cyan-200 border-cyan-400 bg-cyan-400/8 active-mode-glow'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/70 border-transparent'
            }
          `}
        >
          {tab.label}
        </button>
      ))}
    </div>
  </div>
);

/* Animations */

export const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4 },
};

export const fadeIn = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  transition: { duration: 0.3 },
};

export const slideIn = {
  initial: { x: -20, opacity: 0 },
  animate: { x: 0, opacity: 1 },
  transition: { duration: 0.3 },
};
