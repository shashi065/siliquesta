'use client';

import Layout from '@/components/Layout';
import ADAOptimizer from '@/components/ADAOptimizer';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function OptimizerPage() {
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
          <h1 className="text-4xl font-bold text-white mb-2">🚀 Autonomous Design Agent</h1>
          <p className="text-slate-400">
            ADA explores 10,000+ design points to find Pareto-optimal solutions
          </p>
        </div>

        <ADAOptimizer />
      </div>
    </Layout>
  );
}
