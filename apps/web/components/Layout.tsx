'use client';

import { ReactNode, useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useDesignStore } from '@/store/designStore';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [showLoadLine, setShowLoadLine] = useState(true);
  useDesignStore();

  const navigationItems = [
    { href: '/design', label: 'Design' },
    { href: '/analyzer', label: 'Analyzer' },
    { href: '/optimizer', label: 'Optimizer' },
    { href: '/ai-lab', label: 'AI Lab' },
    { href: '/projects', label: 'Projects' },
  ];

  useEffect(() => {
    setShowLoadLine(true);
    const timer = window.setTimeout(() => setShowLoadLine(false), 420);

    return () => window.clearTimeout(timer);
  }, [pathname]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    router.push('/auth/login');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="bg-slate-900 border-b border-slate-700 sticky top-0 z-40 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-2 interactive-button rounded-xl px-1 py-1">
              <div className="w-8 h-8 bg-gradient-to-br from-cyan-400 to-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold">S</span>
              </div>
              <span className="text-xl font-bold text-white hidden sm:inline">SILIQUESTA</span>
            </Link>

            {/* Navigation */}
            <nav className="hidden md:flex gap-8">
              {navigationItems.map((item) => {
                const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`rounded-full px-3 py-2 text-sm font-medium border interactive-button ${
                      isActive
                        ? 'active-mode-glow bg-cyan-400/8 text-cyan-200 border-cyan-400/20'
                        : 'text-slate-300 border-transparent hover:text-cyan-300 hover:bg-slate-800/70'
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>

            {/* User Menu */}
            <div className="flex items-center gap-4">
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center text-white font-bold interactive-button"
              >
                U
              </button>
              {isMenuOpen && (
                <div className="absolute top-16 right-4 bg-slate-800 border border-slate-700 rounded-lg shadow-lg animate-scale-in">
                  <button
                    onClick={handleLogout}
                    className="block w-full text-left px-4 py-2 text-sm text-slate-300 hover:text-red-400 rounded-lg interactive-button"
                  >
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
        <div aria-hidden="true" className={`fast-load-line ${showLoadLine ? 'is-visible' : ''}`} />
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 border-t border-slate-700 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-slate-400 text-sm">
            <p>SILIQUESTA v2.0 | Advanced CMOS Design Platform</p>
            <p className="mt-2">Powered by FastAPI, Ollama AI, and PostgreSQL</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
