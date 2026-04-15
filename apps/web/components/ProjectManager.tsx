'use client';

import { useState, useEffect } from 'react';

interface Design {
  id: string;
  name: string;
  wn: number;
  wp: number;
  freq: number;
  power: number;
  delay: number;
  createdAt: string;
  corner: string;
  techNode: number;
}

interface Project {
  id: string;
  name: string;
  description: string;
  designs: Design[];
  createdAt: string;
}

export default function ProjectManager() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [showNewProject, setShowNewProject] = useState(false);
  const [projectName, setProjectName] = useState('');
  const [projectDesc, setProjectDesc] = useState('');

  // Mock load projects from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('projects');
    if (saved) {
      setProjects(JSON.parse(saved));
    }
  }, []);

  const createProject = async () => {
    if (!projectName.trim()) return;

    const newProject: Project = {
      id: Date.now().toString(),
      name: projectName,
      description: projectDesc,
      designs: [],
      createdAt: new Date().toISOString(),
    };

    const updated = [...projects, newProject];
    setProjects(updated);
    localStorage.setItem('projects', JSON.stringify(updated));

    setProjectName('');
    setProjectDesc('');
    setShowNewProject(false);
    setSelectedProject(newProject);
  };

  const deleteProject = (id: string) => {
    const updated = projects.filter((p) => p.id !== id);
    setProjects(updated);
    localStorage.setItem('projects', JSON.stringify(updated));
    if (selectedProject?.id === id) {
      setSelectedProject(null);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Projects List */}
      <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 shadow-lg">
        <h2 className="text-xl font-bold text-white mb-4">Projects</h2>

        <button
          onClick={() => setShowNewProject(!showNewProject)}
          className="w-full mb-4 px-4 py-2 bg-gradient-to-r from-cyan-400 to-blue-600 text-white font-semibold rounded-lg hover:opacity-90 transition"
        >
          + New Project
        </button>

        {showNewProject && (
          <div className="mb-4 space-y-2">
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="Project name"
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm"
            />
            <textarea
              value={projectDesc}
              onChange={(e) => setProjectDesc(e.target.value)}
              placeholder="Description (optional)"
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm h-16 resize-none"
            />
            <div className="flex gap-2">
              <button
                onClick={createProject}
                className="flex-1 px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
              >
                Create
              </button>
              <button
                onClick={() => setShowNewProject(false)}
                className="flex-1 px-3 py-1 bg-slate-600 text-white text-sm rounded hover:bg-slate-700"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        <div className="space-y-2 max-h-96 overflow-y-auto">
          {projects.map((project) => (
            <div
              key={project.id}
              onClick={() => setSelectedProject(project)}
              className={`p-3 rounded-lg cursor-pointer transition ${
                selectedProject?.id === project.id
                  ? 'bg-blue-600 border border-blue-400'
                  : 'bg-slate-700 border border-slate-600 hover:border-slate-500'
              }`}
            >
              <p className="text-white font-semibold text-sm">{project.name}</p>
              <p className="text-slate-400 text-xs">{project.designs.length} designs</p>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  deleteProject(project.id);
                }}
                className="text-red-400 text-xs mt-1 hover:text-red-300"
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Project Details */}
      <div className="lg:col-span-3">
        {selectedProject ? (
          <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 shadow-lg">
            <h2 className="text-2xl font-bold text-white mb-2">{selectedProject.name}</h2>
            <p className="text-slate-400 mb-4">{selectedProject.description}</p>

            <div className="mb-6 pb-6 border-b border-slate-700">
              <p className="text-sm text-slate-500">
                Created: {new Date(selectedProject.createdAt).toLocaleDateString()}
              </p>
            </div>

            {selectedProject.designs.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-slate-400 mb-4">No designs yet</p>
                <p className="text-sm text-slate-500">Create a design to get started</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-slate-300">
                  <thead className="bg-slate-700 text-cyan-400">
                    <tr>
                      <th className="px-4 py-2 text-left">Name</th>
                      <th className="px-4 py-2 text-left">Freq (GHz)</th>
                      <th className="px-4 py-2 text-left">Power (mW)</th>
                      <th className="px-4 py-2 text-left">Node (nm)</th>
                      <th className="px-4 py-2 text-left">Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedProject.designs.map((design) => (
                      <tr key={design.id} className="border-t border-slate-700">
                        <td className="px-4 py-2">{design.name}</td>
                        <td className="px-4 py-2 text-green-400">{design.freq.toFixed(2)}</td>
                        <td className="px-4 py-2 text-orange-400">{design.power.toFixed(2)}</td>
                        <td className="px-4 py-2">{design.techNode}</td>
                        <td className="px-4 py-2 text-slate-500 text-xs">
                          {new Date(design.createdAt).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-slate-800 rounded-lg border border-slate-700 p-12 text-center">
            <p className="text-slate-400">Select or create a project to get started</p>
          </div>
        )}
      </div>
    </div>
  );
}
