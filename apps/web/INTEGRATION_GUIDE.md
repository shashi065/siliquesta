# Frontend Integration Guide - Backend API Wiring

This guide explains how to connect the investor-grade SaaS frontend to the Phase 4 Cloud Execution backend.

---

## Overview

The frontend components are designed to work with RESTful APIs. This document shows how to integrate them with the SILIQUESTA backend services.

---

## API Endpoints

### Dashboard Data

**GET** `/api/v1/dashboard/metrics`
```json
{
  "totalSimulations": 9791,
  "avgAccuracy": 95.3,
  "successRate": 98.2,
  "totalComputeHours": 142.5
}
```

**GET** `/api/v1/dashboard/projects?limit=10`
```json
{
  "projects": [
    {
      "id": "proj_123",
      "name": "NAND Gate Optimization",
      "created": "2026-04-10T10:30:00Z",
      "status": "completed",
      "simulations": 2847,
      "accuracy": 96.8
    }
  ]
}
```

**GET** `/api/v1/dashboard/trends?days=7`
```json
{
  "trends": [
    {
      "date": "2026-04-05",
      "simulations": 2400,
      "accuracy": 94.2
    }
  ]
}
```

### Simulation Results

**GET** `/api/v1/simulations/{simulation_id}/results`
```json
{
  "id": "sim_123",
  "projectId": "proj_123",
  "status": "completed",
  "createdAt": "2026-04-10T10:30:00Z",
  "frequencyResponse": {
    "frequencies": [1, 10, 100, 1000, 10000, 100000],
    "gain": [12.5, 18.2, 25.8, 28.5, 22.3, 10.5],
    "phase": [-45, -60, -90, -120, -135, -150]
  },
  "powerAnalysis": {
    "voltages": [0.6, 0.8, 1.0, 1.2],
    "dynamicPower": [45.2, 78.5, 125.8, 185.2],
    "leakagePower": [2.1, 5.3, 12.4, 28.9]
  },
  "delayAnalysis": {
    "temperatures": [-40, 0, 25, 50, 85, 125],
    "delays": [2.145, 2.098, 2.050, 2.015, 1.985, 1.952],
    "slewRates": [0.32, 0.31, 0.30, 0.29, 0.28, 0.27]
  }
}
```

### Waveform Data

**GET** `/api/v1/simulations/{simulation_id}/waveforms`
```json
{
  "id": "wave_123",
  "timestamps": [0, 0.1, 0.2, ..., 99.9],
  "voltage": [1.65, 1.72, 1.58, ..., 1.67],
  "current": [10.2, 12.5, 8.3, ..., 11.1],
  "power": [16.8, 21.3, 13.1, ..., 18.6]
}
```

### Confidence Metrics

**GET** `/api/v1/simulations/{simulation_id}/confidence`
```json
{
  "overallConfidence": 96.8,
  "modelAccuracy": 97.2,
  "validationScore": 95.1,
  "convergenceQuality": 98.5,
  "dataQuality": 94.3,
  "uncertaintyRange": [0.8, 1.2]
}
```

### Job Queue Status

**GET** `/api/v1/jobs/queue/stats`
```json
{
  "totalQueued": 5,
  "totalRunning": 4,
  "totalCompleted": 1247,
  "estimatedWaitTime": "1.5 minutes",
  "workerUtilization": 87
}
```

---

## Integration Examples

### 1. Connecting Dashboard to API

```tsx
// app/dashboard/page.tsx
import { useEffect, useState } from 'react';
import Dashboard from '@/components/Dashboard';

export default function DashboardPage() {
  const [metrics, setMetrics] = useState(null);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [metricsRes, projectsRes] = await Promise.all([
          fetch('/api/v1/dashboard/metrics'),
          fetch('/api/v1/dashboard/projects?limit=10')
        ]);
        
        const metricsData = await metricsRes.json();
        const projectsData = await projectsRes.json();
        
        setMetrics(metricsData);
        setProjects(projectsData.projects);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <SkeletonCard />;
  }

  return (
    <Layout>
      <Dashboard metrics={metrics} projects={projects} />
    </Layout>
  );
}
```

### 2. Connecting SimulationVisualization to Results

```tsx
// app/results/page.tsx
import { useEffect, useState } from 'react';
import SimulationVisualization from '@/components/SimulationVisualization';
import { useSearchParams } from 'next/navigation';

export default function ResultsPage() {
  const searchParams = useSearchParams();
  const simId = searchParams.get('sim');
  const [results, setResults] = useState(null);

  useEffect(() => {
    const fetchResults = async () => {
      const res = await fetch(`/api/v1/simulations/${simId}/results`);
      const data = await res.json();
      setResults(data);
    };

    fetchResults();
  }, [simId]);

  if (!results) return <LoadingSpinner />;

  // Transform API data for Recharts
  const gainData = results.frequencyResponse.frequencies.map((freq, idx) => ({
    freq,
    gain: results.frequencyResponse.gain[idx],
    phase: results.frequencyResponse.phase[idx]
  }));

  return (
    <Layout>
      <SimulationVisualization data={gainData} type="gain" />
    </Layout>
  );
}
```

### 3. Connecting WaveformVisualization

```tsx
// components/WaveformVisualizationWithData.tsx
import { useEffect, useState } from 'react';
import WaveformVisualization from '@/components/WaveformVisualization';

export default function WaveformWithData({ simulationId }) {
  const [waveformData, setWaveformData] = useState(null);

  useEffect(() => {
    const fetchWaveform = async () => {
      const res = await fetch(`/api/v1/simulations/${simulationId}/waveforms`);
      const data = await res.json();
      
      setWaveformData({
        time: data.timestamps,
        voltage: data.voltage,
        current: data.current
      });
    };

    fetchWaveform();
  }, [simulationId]);

  return (
    <WaveformVisualization 
      data={waveformData}
      title="Simulation Waveforms"
      timeScale="ns"
    />
  );
}
```

### 4. Connecting TrustPanel

```tsx
// components/TrustPanelWithData.tsx
import { useEffect, useState } from 'react';
import TrustPanel from '@/components/TrustPanel';

export default function TrustPanelWithData({ simulationId }) {
  const [confidence, setConfidence] = useState(null);

  useEffect(() => {
    const fetchConfidence = async () => {
      const res = await fetch(`/api/v1/simulations/${simulationId}/confidence`);
      const data = await res.json();
      setConfidence(data);
    };

    fetchConfidence();
  }, [simulationId]);

  if (!confidence) return <LoadingSpinner />;

  return <TrustPanel confidence={confidence} />;
}
```

### 5. Handling Job Queue (Cloud Execution)

```tsx
// hooks/useJobQueue.ts
import { useState, useEffect } from 'react';

export function useJobQueue(jobId) {
  const [status, setStatus] = useState({
    state: 'queued',
    progress: 0,
    result: null
  });

  useEffect(() => {
    const pollJob = async () => {
      const res = await fetch(`/api/v1/jobs/${jobId}`);
      const data = await res.json();
      
      if (data.status === 'completed') {
        setStatus({
          state: 'completed',
          progress: 100,
          result: data.result
        });
      } else if (data.status === 'running') {
        setStatus({
          state: 'running',
          progress: data.progress || 50,
          result: null
        });
      }
    };

    const interval = setInterval(pollJob, 1000);
    return () => clearInterval(interval);
  }, [jobId]);

  return status;
}
```

---

## API Error Handling

### Graceful Error Handling

```tsx
import { ErrorState, ValidationError } from '@/components/LoadingStates';

function MyComponent() {
  const [error, setError] = useState(null);
  const [validationErrors, setValidationErrors] = useState([]);

  const handleFetch = async () => {
    try {
      const res = await fetch('/api/v1/simulations');
      
      if (!res.ok) {
        if (res.status === 400) {
          const errors = await res.json();
          setValidationErrors(errors.details);
        } else if (res.status === 500) {
          setError('Server error. Please try again.');
        }
        return;
      }
      
      const data = await res.json();
      // Process data
    } catch (err) {
      setError(err.message);
    }
  };

  if (validationErrors.length > 0) {
    return <ValidationError errors={validationErrors} />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={handleFetch} />;
  }

  return <YourComponent />;
}
```

---

## Data Transformation Utilities

### Create a data utilities file

```tsx
// utils/dataTransform.ts

export function transformFrequencyResponse(apiData) {
  return apiData.frequencies.map((freq, idx) => ({
    freq,
    gain: apiData.gain[idx],
    phase: apiData.phase[idx]
  }));
}

export function transformPowerAnalysis(apiData) {
  return apiData.voltages.map((voltage, idx) => ({
    voltage,
    power: apiData.dynamicPower[idx],
    leakage: apiData.leakagePower[idx]
  }));
}

export function transformDelayAnalysis(apiData) {
  return apiData.temperatures.map((temp, idx) => ({
    temp,
    delay: apiData.delays[idx],
    slew: apiData.slewRates[idx]
  }));
}

export function transformTrendData(apiData) {
  return apiData.map(point => ({
    date: new Date(point.date).toLocaleDateString('en-US', {
      weekday: 'short'
    }),
    simulations: point.simulations,
    accuracy: point.accuracy
  }));
}
```

---

## State Management

### Using a store for shared state

```tsx
// store/simulationStore.ts
import { create } from 'zustand';

interface SimulationStore {
  selectedSimulation: string | null;
  results: any | null;
  confidence: any | null;
  loading: boolean;
  setSelectedSimulation: (id: string) => void;
  fetchResults: (id: string) => Promise<void>;
  fetchConfidence: (id: string) => Promise<void>;
}

export const useSimulationStore = create<SimulationStore>((set) => ({
  selectedSimulation: null,
  results: null,
  confidence: null,
  loading: false,

  setSelectedSimulation: (id: string) => {
    set({ selectedSimulation: id });
  },

  fetchResults: async (id: string) => {
    set({ loading: true });
    try {
      const res = await fetch(`/api/v1/simulations/${id}/results`);
      const data = await res.json();
      set({ results: data });
    } finally {
      set({ loading: false });
    }
  },

  fetchConfidence: async (id: string) => {
    try {
      const res = await fetch(`/api/v1/simulations/${id}/confidence`);
      const data = await res.json();
      set({ confidence: data });
    } catch (error) {
      console.error('Failed to fetch confidence:', error);
    }
  }
}));
```

---

## Real-Time Updates

### WebSocket integration

```tsx
// hooks/useSimulationWS.ts
import { useEffect, useState } from 'react';

export function useSimulationWS(jobId: string) {
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const ws = new WebSocket(`wss://api.siliquesta.com/ws/jobs/${jobId}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStatus(data.status);
      setProgress(data.progress);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => ws.close();
  }, [jobId]);

  return { status, progress };
}
```

---

## Testing Integration

### Mock API for development

```tsx
// __mocks__/api.ts
export const mockDashboardMetrics = {
  totalSimulations: 9791,
  avgAccuracy: 95.3,
  successRate: 98.2,
  totalComputeHours: 142.5
};

export const mockProjects = [
  {
    id: 'proj_1',
    name: 'NAND Gate Optimization',
    created: '2026-04-10T10:30:00Z',
    status: 'completed',
    simulations: 2847,
    accuracy: 96.8
  }
];

// Use in tests
jest.mock('fetch', () =>
  jest.fn()
    .mockResolvedValueOnce(mockDashboardMetrics)
    .mockResolvedValueOnce(mockProjects)
);
```

---

## Performance Optimization

### Implement caching

```tsx
// utils/cache.ts
const cache = new Map();

export async function cachedFetch(url, TTL = 5 * 60 * 1000) {
  const cached = cache.get(url);
  
  if (cached && Date.now() - cached.timestamp < TTL) {
    return cached.data;
  }

  const response = await fetch(url);
  const data = await response.json();
  
  cache.set(url, {
    data,
    timestamp: Date.now()
  });

  return data;
}
```

### Implement pagination

```tsx
// hooks/usePagination.ts
export function usePagination(url, pageSize = 10) {
  const [items, setItems] = useState([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  useEffect(() => {
    const fetchPage = async () => {
      const res = await fetch(`${url}?page=${page}&limit=${pageSize}`);
      const data = await res.json();
      setItems([...items, ...data.items]);
      setHasMore(data.hasMore);
    };

    fetchPage();
  }, [page]);

  return { items, page, setPage, hasMore };
}
```

---

## Deployment Checklist

- [ ] All API endpoints configured
- [ ] Environment variables set (.env.local)
- [ ] Error handling tested
- [ ] Loading states verified
- [ ] Real data connected
- [ ] Performance profiled
- [ ] Accessibility audited
- [ ] Cross-browser tested

---

## Environment Configuration

```bash
# .env.local
NEXT_PUBLIC_API_URL=https://api.siliquesta.com/api/v1
NEXT_PUBLIC_WS_URL=wss://api.siliquesta.com/ws
API_KEY=your_key_here
```

---

## Support

For integration issues:
1. Check backend API documentation
2. Verify endpoint URLs
3. Check response format
4. Look at browser DevTools Network tab
5. Review component props documentation

---

**Version:** 1.0.0  
**Last Updated:** April 12, 2026

This integration guide provides everything needed to connect the investor-grade frontend to the SILIQUESTA backend services.
