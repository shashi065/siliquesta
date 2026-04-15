'use client';

import Layout from '@/components/Layout';
import PVTAnalyzer from '@/components/PVTAnalyzer';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function AnalyzerPage() {
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
          <h1 className="text-4xl font-bold text-white mb-2">PVT Analyzer</h1>
          <p className="text-slate-400">
            Analyze process, voltage, and temperature variations across all corners
          </p>
        </div>

        <PVTAnalyzer />
      </div>
    </Layout>
  );
}
