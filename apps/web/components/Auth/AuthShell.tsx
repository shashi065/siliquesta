'use client';

import type { ReactNode } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function AuthShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const isSignup = pathname === '/auth/signup';

  return (
    <div className="auth-experience">
      <div className="auth-orb auth-orb-a" aria-hidden="true" />
      <div className="auth-orb auth-orb-b" aria-hidden="true" />
      <div className="auth-orb auth-orb-c" aria-hidden="true" />

      <main className="auth-stage">
        <section className="auth-card">
          <div className="auth-brand">
            <span className="auth-badge">Cloud Workspace</span>
            <div className="auth-brand-mark">S</div>
            <div className="auth-display">SILIQUESTA</div>
            <p className="auth-subcopy">
              Enter the AI-native silicon workspace with the same luminous glass system
              used across the dashboard experience.
            </p>
          </div>

          <div className="auth-panel">
            <div className="auth-tabs" aria-label="Authentication tabs">
              <span
                className={`auth-tab-indicator${isSignup ? ' is-signup' : ''}`}
                aria-hidden="true"
              />
              <Link
                href="/auth/login"
                className={`auth-tab${!isSignup ? ' is-active' : ''}`}
              >
                Login
              </Link>
              <Link
                href="/auth/signup"
                className={`auth-tab${isSignup ? ' is-active' : ''}`}
              >
                Sign Up
              </Link>
            </div>

            <div key={pathname} className="auth-view">
              <div className="auth-copy">
                <h1 className="auth-title">
                  {isSignup ? 'Create your workspace access' : 'Welcome back to your workspace'}
                </h1>
                <p className="auth-description">
                  {isSignup
                    ? 'Set up your account to start running simulations, optimizer flows, and project reviews inside the unified dashboard.'
                    : 'Sign in to continue with your saved circuit runs, AI guidance, and synced project context.'}
                </p>
              </div>

              {children}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
