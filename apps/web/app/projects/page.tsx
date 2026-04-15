'use client';

import Layout from '@/components/Layout';
import ProjectManager from '@/components/ProjectManager';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function ProjectsPage() {
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
          <h1 className="text-4xl font-bold text-white mb-2">Design Library</h1>
          <p className="text-slate-400">
            Organize designs into projects and build your Design DNA
          </p>
        </div>

        <ProjectManager />
      </div>
    </Layout>
  );
}
