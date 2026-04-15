import { create } from 'zustand';

export interface SimulationParams {
  wn: number;
  wp: number;
  vdd: number;
  temp: number;
  cl_ff: number;
  corner: string;
  tech_node: number;
}

export interface SimulationResult {
  freq: number;
  power: number;
  delay: number;
  fom: number;
  id_n: number;
  id_p: number;
  vth: number;
  cox: number;
  vov: number;
}

interface DesignStore {
  // State
  params: SimulationParams;
  results: SimulationResult | null;
  isRunning: boolean;
  error: string | null;

  // Actions
  setParams: (params: Partial<SimulationParams>) => void;
  setResults: (results: SimulationResult) => void;
  setRunning: (running: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

const defaultParams: SimulationParams = {
  wn: 0.5,
  wp: 1.0,
  vdd: 1.2,
  temp: 27,
  cl_ff: 10,
  corner: 'TT',
  tech_node: 28,
};

export const useDesignStore = create<DesignStore>((set) => ({
  params: defaultParams,
  results: null,
  isRunning: false,
  error: null,

  setParams: (newParams) =>
    set((state) => ({
      params: { ...state.params, ...newParams },
    })),

  setResults: (results) => set({ results }),
  setRunning: (running) => set({ isRunning: running }),
  setError: (error) => set({ error }),
  reset: () =>
    set({
      params: defaultParams,
      results: null,
      isRunning: false,
      error: null,
    }),
}));
