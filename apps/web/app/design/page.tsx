'use client';

import Layout from '@/components/Layout';
import SimulationPanel from '@/components/SimulationPanel';
import ResultsDisplay from '@/components/ResultsDisplay';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function DesignPage() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/auth/login');
    }
  }, [router]);

  return (
    <Layout>
      <div className="space-y-8">
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">CMOS Design Studio</h1>
          <p className="text-slate-400">
            Configure transistor parameters and run simulations with real physics
          </p>
        </div>

        <SimulationPanel />

        <div>
          <h2 className="text-2xl font-bold text-white mb-4">Results</h2>
          <ResultsDisplay />
        </div>
      </div>
    </Layout>
  );
}
