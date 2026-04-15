'use client';

import Layout from '@/components/Layout';
import AIChat from '@/components/AIChat';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function AILabPage() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/auth/login');
    }
  }, [router]);

  return (
    <Layout>
      <div className="space-y-8 h-full">
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">🤖 AI Lab</h1>
          <p className="text-slate-400">
            Chat with Ollama AI for design recommendations, code generation, and troubleshooting
          </p>
        </div>

        <div className="h-96 lg:h-screen">
          <AIChat />
        </div>
      </div>
    </Layout>
  );
}
