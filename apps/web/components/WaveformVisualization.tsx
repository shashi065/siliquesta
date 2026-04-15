'use client';

import React, { useLayoutEffect, useRef } from 'react';
import { Download, ZoomIn, ZoomOut } from 'lucide-react';

interface WaveformData {
  time: number[];
  voltage: number[];
  current?: number[];
  power?: number[];
}

interface WaveformVisualizationProps {
  data?: WaveformData;
  title?: string;
  timeScale?: 'ns' | 'us' | 'ms';
  voltageRange?: [number, number];
}

export default function WaveformVisualization({
  data,
  title = 'Waveform Analysis',
  timeScale = 'ns',
  voltageRange = [0, 3.3],
}: WaveformVisualizationProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [zoomLevel, setZoomLevel] = React.useState(1);

  // Generate mock waveform data if none provided
  const generateMockWaveform = (): WaveformData => {
    const time = Array.from({ length: 1000 }, (_, i) => i * 0.1);
    const voltage = time.map((t) => {
      const freq = 1; // 1 GHz
      return 1.65 + 1.5 * Math.sin(2 * Math.PI * freq * t + Math.sin(2 * Math.PI * 0.1 * t));
    });
    const current = voltage.map((v) => (v / voltageRange[1]) * 100);
    return { time, voltage, current };
  };

  const waveformData = data || generateMockWaveform();

  // Draw waveform on canvas
  useLayoutEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    const padding = 40;
    const plotWidth = width - 2 * padding;
    const plotHeight = height - 2 * padding;

    // Clear canvas with dark background
    ctx.fillStyle = '#1e293b';
    ctx.fillRect(0, 0, width, height);

    // Draw grid
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 1;

    // Vertical grid lines
    const xSteps = 10;
    for (let i = 0; i <= xSteps; i++) {
      const x = padding + (plotWidth / xSteps) * i;
      ctx.beginPath();
      ctx.moveTo(x, padding);
      ctx.lineTo(x, height - padding);
      ctx.stroke();
    }

    // Horizontal grid lines
    const ySteps = 10;
    for (let i = 0; i <= ySteps; i++) {
      const y = height - padding - (plotHeight / ySteps) * i;
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(width - padding, y);
      ctx.stroke();
    }

    // Draw axes
    ctx.strokeStyle = '#64748b';
    ctx.lineWidth = 2;

    // X-axis
    ctx.beginPath();
    ctx.moveTo(padding, height - padding);
    ctx.lineTo(width - padding, height - padding);
    ctx.stroke();

    // Y-axis
    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, height - padding);
    ctx.stroke();

    // Draw voltage waveform
    ctx.strokeStyle = '#06B6D4';
    ctx.lineWidth = 2;
    ctx.beginPath();

    const timeScaleFactor = zoomLevel;
    const maxTime = waveformData.time[waveformData.time.length - 1];
    const minVoltage = voltageRange[0];
    const maxVoltage = voltageRange[1];

    for (let i = 0; i < waveformData.voltage.length; i++) {
      const x = padding + (waveformData.time[i] / maxTime) * plotWidth * timeScaleFactor;
      if (x > width - padding) break; // Stop drawing if outside canvas

      const y =
        height -
        padding -
        ((waveformData.voltage[i] - minVoltage) / (maxVoltage - minVoltage)) * plotHeight;

      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    }
    ctx.stroke();

    // Draw current waveform if available (secondary axis)
    if (waveformData.current) {
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 2;
      ctx.beginPath();

      for (let i = 0; i < waveformData.current.length; i++) {
        const x = padding + (waveformData.time[i] / maxTime) * plotWidth * timeScaleFactor;
        if (x > width - padding) break;

        // Scale current to fit on right axis (0-150 mA assumed)
        const y = height - padding - (waveformData.current[i] / 150) * plotHeight;

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();
    }

    // Draw axis labels
    ctx.fillStyle = '#cbd5e1';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'center';

    // X-axis labels (time)
    for (let i = 0; i <= xSteps; i++) {
      const x = padding + (plotWidth / xSteps) * i;
      const timeVal = (maxTime / xSteps) * i;
      ctx.fillText(`${timeVal.toFixed(1)}${timeScale}`, x, height - padding + 20);
    }

    // Y-axis labels (voltage)
    ctx.textAlign = 'right';
    for (let i = 0; i <= ySteps; i++) {
      const y = height - padding - (plotHeight / ySteps) * i;
      const voltVal = minVoltage + ((maxVoltage - minVoltage) / ySteps) * i;
      ctx.fillText(`${voltVal.toFixed(1)}V`, padding - 10, y + 5);
    }

    // Draw legend
    ctx.font = 'bold 14px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillStyle = '#06B6D4';
    ctx.fillRect(width - 200, 20, 15, 15);
    ctx.fillStyle = '#cbd5e1';
    ctx.fillText('Voltage', width - 175, 32);

    if (waveformData.current) {
      ctx.fillStyle = '#f59e0b';
      ctx.fillRect(width - 200, 50, 15, 15);
      ctx.fillStyle = '#cbd5e1';
      ctx.fillText('Current', width - 175, 62);
    }
  }, [waveformData, zoomLevel, voltageRange, timeScale]);

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 interactive-surface">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
        <div>
          <h3 className="text-lg font-semibold text-white">{title}</h3>
          <p className="text-sm text-slate-400">Time-domain analysis</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setZoomLevel((z) => Math.max(1, z - 0.2))}
            className="p-2 hover:bg-slate-700 rounded-lg interactive-button text-slate-300"
            title="Zoom Out"
          >
            <ZoomOut className="w-5 h-5" />
          </button>
          <span className="px-3 py-2 text-sm text-slate-400">{(zoomLevel * 100).toFixed(0)}%</span>
          <button
            onClick={() => setZoomLevel((z) => Math.min(5, z + 0.2))}
            className="p-2 hover:bg-slate-700 rounded-lg interactive-button text-slate-300"
            title="Zoom In"
          >
            <ZoomIn className="w-5 h-5" />
          </button>
          <button className="p-2 hover:bg-slate-700 rounded-lg interactive-button text-slate-300" title="Download">
            <Download className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Canvas */}
      <div className="p-4">
        <canvas
          ref={canvasRef}
          width={800}
          height={400}
          className="w-full border border-slate-700 rounded-lg bg-slate-800"
        />
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 px-6 py-4 border-t border-slate-700 bg-slate-700/30">
        <StatBox label="Peak Voltage" value="3.15V" />
        <StatBox label="Min Voltage" value="0.18V" />
        <StatBox label="Rise Time" value="0.8 ns" />
        <StatBox label="Fall Time" value="0.9 ns" />
      </div>
    </div>
  );
}

function StatBox({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs text-slate-400 mb-1">{label}</div>
      <div className="text-lg font-semibold text-cyan-400">{value}</div>
    </div>
  );
}
