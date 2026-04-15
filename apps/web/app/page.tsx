import Link from 'next/link';
import { Zap, BarChart3, TrendingUp, CheckCircle2, Cpu, Clock } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-slate-900/80 backdrop-blur border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-cyan-400 to-blue-600 rounded-lg flex items-center justify-center shadow-glow-sm">
                <span className="text-white text-lg font-bold">S</span>
              </div>
              <span className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                SILIQUESTA
              </span>
            </div>
            <nav className="flex gap-2 sm:gap-6">
              <Link
                href="/auth/login"
                className="px-4 py-2 text-slate-300 hover:text-cyan-400 transition font-medium"
              >
                Login
              </Link>
              <Link
                href="/auth/signup"
                className="px-6 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-lg hover:shadow-glow transition font-semibold"
              >
                Sign Up
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-32">
        <div className="text-center space-y-8 animate-slide-in-up">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-500/10 border border-cyan-500/30 rounded-full">
            <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            <span className="text-sm font-medium text-cyan-300">Backed by quantum-inspired algorithms</span>
          </div>

          <h1 className="text-5xl sm:text-7xl font-bold text-white leading-tight">
            Advanced CMOS Design
            <br />
            <span className="bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 bg-clip-text text-transparent">
              Platform
            </span>
          </h1>

          <p className="text-lg sm:text-xl text-slate-300 max-w-2xl mx-auto leading-relaxed">
            Powered by real physics simulation, Ollama AI co-pilot, and 50x faster than traditional EDA.
            Design. Optimize. Predict. Tape out with confidence.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-8">
            <Link
              href="/auth/signup"
              className="px-8 py-4 bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-semibold rounded-lg hover:shadow-glow-lg transition duration-300 transform hover:scale-105"
            >
              Start Free Trial
            </Link>
            <Link
              href="#features"
              className="px-8 py-4 border border-slate-500 text-slate-300 font-semibold rounded-lg hover:border-cyan-400 hover:text-cyan-400 transition"
            >
              Watch Demo
            </Link>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mt-16 pt-16 border-t border-slate-700">
            <div className="text-center">
              <div className="text-3xl font-bold text-cyan-400">50x</div>
              <div className="text-sm text-slate-400">Faster simulation</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-cyan-400">98%</div>
              <div className="text-sm text-slate-400">Accuracy</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-cyan-400">1M+</div>
              <div className="text-sm text-slate-400">Simulations</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 border-t border-slate-700">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-white mb-4">
            Built for Deep-Tech Teams
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">
            Enterprise-grade features for serious chip design. No approximations. Real physics.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {[
            {
              icon: <Zap className="w-8 h-8 text-cyan-400" />,
              title: 'Real Physics Engine',
              desc: 'Actual CMOS equations, not approximations. Propagation delay, power, thermal effects modeled accurately.',
              highlight: 'Enterprise'
            },
            {
              icon: <Cpu className="w-8 h-8 text-blue-400" />,
              title: 'Local AI Co-pilot',
              desc: 'Ollama-powered design assistance. No cloud APIs. Runs 100% on your infrastructure.',
              highlight: 'Privacy First'
            },
            {
              icon: <TrendingUp className="w-8 h-8 text-emerald-400" />,
              title: '50x Performance',
              desc: 'FastAPI async backend with optimized physics engine. Simulate in milliseconds, not seconds.',
              highlight: 'Production Ready'
            },
            {
              icon: <BarChart3 className="w-8 h-8 text-orange-400" />,
              title: 'Advanced PVT Analysis',
              desc: 'All corners, temperatures, voltages. Corner summary or complete sweep with statistical analysis.',
              highlight: 'Tapeout Ready'
            },
            {
              icon: <Cpu className="w-8 h-8 text-purple-400" />,
              title: 'ADA Optimizer',
              desc: 'Autonomous design agent. Pareto front exploration. 10,000+ design variations in minutes.',
              highlight: 'AI-Driven'
            },
            {
              icon: <Clock className="w-8 h-8 text-red-400" />,
              title: 'Digital Twin',
              desc: 'Aging prediction with NBTI, HCI, EM models. Reliability forecasting for product lifetime.',
              highlight: 'Predictive'
            },
          ].map((item, idx) => (
            <div
              key={idx}
              className="group bg-slate-800 border border-slate-700 rounded-xl p-8 hover:border-cyan-400 hover:shadow-glow-lg hover:shadow-cyan-500/10 transition-all duration-300 transform hover:-translate-y-1"
            >
              <div className="mb-4 p-3 bg-slate-700/50 rounded-lg w-fit group-hover:bg-cyan-500/10 transition">
                {item.icon}
              </div>
              <div className="inline-block px-2 py-1 text-xs font-semibold text-cyan-300 bg-cyan-500/10 rounded mb-3">
                {item.highlight}
              </div>
              <h3 className="text-xl font-bold text-white mb-3">{item.title}</h3>
              <p className="text-slate-400 leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Stack */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 bg-gradient-to-r from-slate-800/50 to-slate-700/50 rounded-2xl my-16 border border-slate-700">
        <h2 className="text-3xl font-bold text-white mb-8 text-center">
          Enterprise-Grade <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">Tech Stack</span>
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {[
            { label: 'Frontend', tech: 'Next.js 14 + React 18' },
            { label: 'Backend', tech: 'FastAPI + Python 3.11' },
            { label: 'Database', tech: 'PostgreSQL' },
            { label: 'AI Engine', tech: 'Ollama + LLaMA 2' },
            { label: 'Cache', tech: 'Redis' },
            { label: 'Orchestration', tech: 'Docker + K8s' },
            { label: 'ML Framework', tech: 'PyTorch + ONNX' },
            { label: 'Vector DB', tech: 'FAISS' },
          ].map((item, idx) => (
            <div
              key={idx}
              className="bg-slate-700/40 border border-slate-600 rounded-xl p-4 hover:border-cyan-400/50 transition backdrop-blur"
            >
              <p className="text-slate-400 text-xs font-semibold uppercase tracking-wide mb-2">{item.label}</p>
              <p className="text-cyan-300 font-bold text-sm">{item.tech}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
        <h2 className="text-3xl font-bold text-white mb-6">Ready to Design at Silicon Speed?</h2>
        <p className="text-lg text-slate-400 mb-8">
          Join 500+ engineers accelerating chip design with SILIQUESTA. Start free. Scale to production.
        </p>
        <Link
          href="/auth/signup"
          className="inline-block px-8 py-4 bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-semibold rounded-lg hover:shadow-glow-xl transition duration-300 transform hover:scale-105"
        >
          Launch Your Free Trial
        </Link>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900/50 border-t border-slate-700 mt-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
            <div>
              <h4 className="text-white font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-slate-400 text-sm">
                <li><a href="#" className="hover:text-cyan-400">Features</a></li>
                <li><a href="#" className="hover:text-cyan-400">Pricing</a></li>
                <li><a href="#" className="hover:text-cyan-400">Docs</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-slate-400 text-sm">
                <li><a href="#" className="hover:text-cyan-400">About</a></li>
                <li><a href="#" className="hover:text-cyan-400">Blog</a></li>
                <li><a href="#" className="hover:text-cyan-400">Contact</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Legal</h4>
              <ul className="space-y-2 text-slate-400 text-sm">
                <li><a href="#" className="hover:text-cyan-400">Privacy</a></li>
                <li><a href="#" className="hover:text-cyan-400">Terms</a></li>
                <li><a href="#" className="hover:text-cyan-400">Security</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Follow</h4>
              <ul className="space-y-2 text-slate-400 text-sm">
                <li><a href="#" className="hover:text-cyan-400">Twitter</a></li>
                <li><a href="#" className="hover:text-cyan-400">GitHub</a></li>
                <li><a href="#" className="hover:text-cyan-400">LinkedIn</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-slate-700 pt-8 text-center text-slate-400">
            <p>SILIQUESTA v2.0 | Advanced CMOS Design Platform</p>
            <p className="text-sm mt-2">© 2026 SILIQUESTA Inc. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
