/**
 * Standalone WebSocket Test Server
 * Tests: Connection, message reception, Pareto updates, convergence metrics
 * No database required
 */

import http from 'http';
import { WebSocketServer } from 'ws';
import { ParetoFrontManager } from './services/paretoFrontManager.js';

const PORT = 10000;

// Create minimal HTTP server
const server = http.createServer((req, res) => {
  if (req.url === '/') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      message: 'WebSocket Test Server',
      ws: `ws://localhost:${PORT}`
    }));
  } else if (req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok' }));
  } else {
    res.writeHead(404);
    res.end('Not Found');
  }
});

// WebSocket server
const wss = new WebSocketServer({ server });

console.log(`✓ WebSocket Test Server starting on ws://localhost:${PORT}`);

wss.on('connection', (ws) => {
  console.log(`✓ Client connected`);
  
  let optimizationRunning = false;
  const paretoManager = new ParetoFrontManager();
  
  // Send ready message
  ws.send(JSON.stringify({
    type: 'CONNECTED',
    message: 'WebSocket test server ready',
    timestamp: Date.now()
  }));

  ws.on('message', async (msg) => {
    try {
      const data = JSON.parse(msg.toString());
      console.log(`📨 Received: ${data.type}`);

      switch (data.type) {
        case 'START_OPTIMIZATION':
          await handleOptimization(ws, data, paretoManager);
          break;
          
        case 'PAUSE_STREAM':
          optimizationRunning = false;
          ws.send(JSON.stringify({
            type: 'STATUS',
            message: 'Optimization paused',
            timestamp: Date.now()
          }));
          console.log('⏸️  Optimization paused');
          break;
          
        case 'RESUME_STREAM':
          optimizationRunning = true;
          ws.send(JSON.stringify({
            type: 'STATUS',
            message: 'Optimization resumed',
            timestamp: Date.now()
          }));
          console.log('▶️  Optimization resumed');
          break;
          
        case 'GET_STATUS':
          ws.send(JSON.stringify({
            type: 'STATUS',
            active: optimizationRunning,
            paretoFrontSize: paretoManager.solutions.length,
            timestamp: Date.now()
          }));
          break;

        default:
          console.log(`❓ Unknown message type: ${data.type}`);
      }
    } catch (err) {
      console.error(`❌ Error processing message:`, err.message);
      ws.send(JSON.stringify({
        type: 'ERROR',
        message: err.message,
        timestamp: Date.now()
      }));
    }
  });

  ws.on('close', () => {
    console.log(`✗ Client disconnected`);
    optimizationRunning = false;
  });

  ws.on('error', (err) => {
    console.error(`❌ WebSocket error:`, err.message);
  });
});

// Simulate optimization with streaming
async function handleOptimization(ws, params, paretoManager) {
  const iterations = params.iterations || 25;
  console.log(`🚀 Starting optimization: ${iterations} iterations`);

  // Send OPTIMIZATION_STARTED
  ws.send(JSON.stringify({
    type: 'OPTIMIZATION_STARTED',
    iterations: iterations,
    timestamp: Date.now()
  }));

  let best = {
    score: 1.0,
    improvement: 0,
    params: { W: 2.5, L: 1.5, V: 1.0 }
  };

  // Main loop
  for (let i = 1; i <= iterations; i++) {
    // Simulate work
    await new Promise(r => setTimeout(r, 35));

    // Simulate improvement
    const improvement = (Math.random() * 0.05) + (i * 0.01);
    best.score -= improvement;
    best.improvement += improvement;

    // Generate metrics
    const power = 2.5 - (best.improvement * 0.8);
    const delay = 20 - (best.improvement * 5);
    const area = 50 - (best.improvement * 3);

    // Add to Pareto front every 3 iterations
    if (i % 3 === 0) {
      paretoManager.addSolution(
        { W: 2.5 + Math.random() * 0.5, L: 1.5 + Math.random() * 0.3, V: 1.0 },
        { power: Math.max(0.5, power), delay: Math.max(5, delay), area: Math.max(20, area) }
      );
    }

    // OPTIMIZATION_PROGRESS (every iteration)
    ws.send(JSON.stringify({
      type: 'OPTIMIZATION_PROGRESS',
      iteration: i,
      total: iterations,
      progress: Math.round((i / iterations) * 100),
      best: {
        score: best.score,
        improvementPercent: (best.improvement * 100).toFixed(2),
        params: best.params
      },
      convergence: {
        rate: (best.improvement / i).toFixed(4),
        trend: (Math.sin(i / 5) * 0.01).toFixed(4),
        noImprovementIterations: Math.random() > 0.7 ? 1 : 0
      },
      timestamp: Date.now()
    }));

    // PARETO_UPDATE (every 5 iterations)
    if (i % 5 === 0 && paretoManager.solutions.length > 0) {
      ws.send(JSON.stringify({
        type: 'PARETO_UPDATE',
        iteration: i,
        size: paretoManager.solutions.length,
        hypervolume: (100 + paretoManager.solutions.length * 5).toFixed(2),
        diversity: {
          spatialDiversity: (0.7 + Math.random() * 0.3).toFixed(2),
          objectiveDiversity: (0.6 + Math.random() * 0.4).toFixed(2)
        },
        fronts: paretoManager.solutions.slice(0, 3).map(s => ({
          params: s.params,
          metrics: s.metrics,
          crowdingDistance: (Math.random() * 0.5).toFixed(2)
        })),
        timestamp: Date.now()
      }));
    }

    // TRAINING_STATUS (every 10 iterations)
    if (i % 10 === 0) {
      ws.send(JSON.stringify({
        type: 'TRAINING_STATUS',
        phase: i < iterations ? 'optimizing' : 'completed',
        progress: Math.round((i / iterations) * 100),
        paretoFrontSize: paretoManager.solutions.length,
        estTimeRemaining: (iterations - i) * 35,
        timestamp: Date.now()
      }));
    }
  }

  // OPTIMIZATION_COMPLETED
  ws.send(JSON.stringify({
    type: 'OPTIMIZATION_COMPLETED',
    final_score: best.score,
    improvement_percent: (best.improvement * 100).toFixed(2),
    iterations_completed: iterations,
    total_iterations: iterations,
    convergence_trend: 'positive',
    paretoFront: paretoManager.solutions,
    timestamp: Date.now()
  }));

  console.log(`✅ Optimization complete`);
}

// Start server
server.listen(PORT, '0.0.0.0', () => {
  console.log(`\n═══════════════════════════════════════════`);
  console.log(`✓ WebSocket Test Server Running`);
  console.log(`  Port: ${PORT}`);
  console.log(`  WebSocket: ws://localhost:${PORT}`);
  console.log(`  Health: http://localhost:${PORT}/health`);
  console.log(`═══════════════════════════════════════════\n`);
});

server.on('error', (err) => {
  console.error(`❌ Server error:`, err.message);
  if (err.code === 'EADDRINUSE') {
    console.error(`Port ${PORT} is already in use. Try another port.`);
  }
});
