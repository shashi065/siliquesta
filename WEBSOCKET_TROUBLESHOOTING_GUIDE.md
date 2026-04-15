# WebSocket Streaming - Troubleshooting Guide

## Connection Issues

### Problem: "WebSocket connection refused"

**Symptoms:**
- Browser console: `WebSocket is closed with code: 1006`
- `client.connected` is always false
- Network tab shows connection fails immediately

**Root Causes & Solutions:**

```javascript
// 1. Server not running
const server = require('http').createServer(app);
const { initWebSocket } = require('./wsServer');
initWebSocket(server);
server.listen(3000);  // Must be started!

// 2. Wrong port
const client = new OptimizerStreamClient('ws://localhost:3000');  
// Change 3000 to actual server port

// 3. Wrong hostname
const client = new OptimizerStreamClient('ws://example.com:3000');
// For localhost: use 'localhost' or '127.0.0.1' but NOT 'example.com'

// 4. Protocol mismatch (HTTP vs HTTPS)
// - If site is HTTPS, use: ws://... (for dev) or wss://... (for production)
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const client = new OptimizerStreamClient(`${protocol}//localhost:3000`);

// 5. CORS not enabled for WebSocket
// Add to server.js:
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
  next();
});
```

**Diagnostic Script:**
```javascript
async function diagnoseConnection() {
  try {
    console.log('1. Checking server endpoint...');
    const response = await fetch('http://localhost:3000/health');
    console.log('✓ Server is running:', response.ok);
  } catch (e) {
    console.error('✗ Server not responding:', e.message);
    return;
  }
  
  try {
    console.log('2. Attempting WebSocket connection...');
    const ws = new WebSocket('ws://localhost:3000');
    ws.onopen = () => {
      console.log('✓ WebSocket connected');
      ws.close();
    };
    ws.onerror = (e) => console.error('✗ WebSocket error:', e);
    ws.onclose = (e) => {
      console.log(`✗ WebSocket closed: code=${e.code} reason=${e.reason}`);
    };
  } catch (e) {
    console.error('✗ WebSocket exception:', e.message);
  }
}

diagnoseConnection();
```

---

## Message Reception Issues

### Problem: "No progress updates received"

**Symptoms:**
- Connected successfully
- `progress` event never fires
- `completed` event never fires
- Only `started` event fires

**Root Causes & Solutions:**

```javascript
// 1. Not awaiting connection before starting
// WRONG:
const client = new OptimizerStreamClient();
client.startOptimization({...});  // Starts too early!

// RIGHT:
const client = new OptimizerStreamClient();
await client.connect();  // Wait for connection first!
client.startOptimization({...});

// 2. Event listener registered AFTER optimization starts
// WRONG:
await client.startOptimization({...});
client.on('progress', (data) => console.log(data));  // Too late!

// RIGHT:
client.on('progress', (data) => console.log(data));
await client.startOptimization({...});

// 3. Wrong optimization parameters
// WRONG: iterations: 0 (no iterations to run)
await client.startOptimization({ iterations: 0 });

// RIGHT:
await client.startOptimization({ iterations: 25 });

// 4. Server-side ParetoFrontManager error
// Check server logs for:
// "Error in optimization: ParetoFrontManager not initialized"
// Solution: Verify paretoFrontManager.js is imported in aiOptimizer.js
```

**Diagnostic Script:**
```javascript
async function diagnoseMessages() {
  const client = new OptimizerStreamClient();
  
  let progressCount = 0;
  let paretoCount = 0;
  let statusCount = 0;
  
  client.on('progress', () => progressCount++);
  client.on('pareto:update', () => paretoCount++);
  client.on('status:update', () => statusCount++);
  
  console.log('Starting optimization...');
  await client.connect();
  const result = await client.startOptimization({
    iterations: 10,
    objective: 'pareto'
  });
  
  console.log(`Progress messages: ${progressCount} (expected: 10+)`);
  console.log(`Pareto updates: ${paretoCount} (expected: 2+)`);
  console.log(`Status updates: ${statusCount} (expected: 1+)`);
  
  if (progressCount === 0) {
    console.error('✗ No progress messages - check server logs');
  } else {
    console.log('✓ Messages flowing correctly');
  }
}

diagnoseMessages();
```

---

## UI Update Issues

### Problem: "Progress bar not updating"

**Symptoms:**
- WebSocket connected
- Messages arriving (confirmed in DevTools Network tab)
- UI elements not changing
- No JavaScript errors

**Root Causes & Solutions:**

```javascript
// 1. HTML elements don't exist
// WRONG: HTML missing
document.getElementById('optimizer-progress-bar');  // Returns null!

// RIGHT: Add required HTML
<div id="optimizer-progress-bar" class="progress-fill"></div>

// 2. CSS not applied
// WRONG: Missing CSS styles
.progress-fill { }  // No width/height/background!

// RIGHT: Complete CSS
.progress-fill {
  width: 0%;
  height: 25px;
  background-color: #4CAF50;
  transition: width 0.3s ease;
}

// 3. StreamUIHandler not initialized
// WRONG:
const client = new OptimizerStreamClient();
await client.connect();
await client.startOptimization({...});  // No UI handler!

// RIGHT:
const client = new OptimizerStreamClient();
const ui = new StreamUIHandler(client);  // Initialize UI handler
await client.connect();
await client.startOptimization({...});

// 4. Class not imported correctly
// WRONG:
const client = require('optimizer-stream-client.js');  // CommonJS

// RIGHT:
import { OptimizerStreamClient } from './optimizer-stream-client.js';

// 5. Update frequency too low
// Solution: StreamUIHandler uses requestAnimationFrame (60 FPS max)
// This is already optimal - don't override with setTimeout
```

**Diagnostic Script:**
```javascript
function diagnoseUI() {
  const elements = [
    'optimizer-progress-bar',
    'optimizer-iterations',
    'optimizer-convergence',
    'optimizer-message',
    'optimizer-pareto'
  ];
  
  console.log('Checking required HTML elements:');
  for (const id of elements) {
    const el = document.getElementById(id);
    if (!el) {
      console.error(`✗ Missing: <div id="${id}">`);
    } else {
      console.log(`✓ Found: #${id}`);
      const styles = window.getComputedStyle(el);
      console.log(`  - Display: ${styles.display}`);
      console.log(`  - Visibility: ${styles.visibility}`);
    }
  }
  
  // Check CSS transitions
  const bar = document.getElementById('optimizer-progress-bar');
  if (bar) {
    const transition = window.getComputedStyle(bar).transition;
    console.log(`\nProgress bar transition: ${transition || 'none'}`);
  }
}

diagnoseUI();
```

---

## Performance Issues

### Problem: "Browser freezing during optimization"

**Symptoms:**
- UI becomes unresponsive during optimization
- Animations stutter
- High CPU usage
- FPS drops to < 30

**Root Causes & Solutions:**

```javascript
// 1. Updates on main thread blocking UI
// WRONG: Doing heavy operations in event handler
client.on('progress', (data) => {
  // Heavy computation blocks UI
  const bigArray = [...Array(1000000)].map((_, i) => i * i);
  updateDOM();  // Happens AFTER computation
});

// RIGHT: Defer heavy work to background
client.on('progress', (data) => {
  updateDOM();  // Do this first (fast)
  
  // Heavy work in separate microtask
  Promise.resolve().then(() => {
    const bigArray = [...Array(1000000)].map((_, i) => i * i);
    analyzeResults(bigArray);
  });
});

// 2. Too many DOM updates per message
// WRONG: Updating DOM for each message
client.on('progress', (data) => {
  document.getElementById('progress').style.width = data.progress + '%';
  document.getElementById('iteration').textContent = data.iteration;
  document.getElementById('score').textContent = data.best.score;
  document.getElementById('convergence').textContent = data.convergence.rate;
  // ... 10 more updates
});

// RIGHT: Use StreamUIHandler (batches via requestAnimationFrame)
const ui = new StreamUIHandler(client);
// Automatically batches and defers updates

// 3. Message buffering disabled
// Check wsServer.js has buffering:
const BUFFER_FLUSH_INTERVAL = 50;  // ms
const BUFFER_MAX_SIZE = 5;         // messages
// If these are 0, server sends too many messages!

// 4. Memory leak in event handlers
// WRONG: Listeners never removed
client.on('progress', callback);  // Listener accumulates
client.on('progress', callback);  // Another listener
client.on('progress', callback);  // Another listener

// RIGHT: Remove listeners when done
const handler = (data) => updateUI(data);
client.on('progress', handler);

// Later, to clean up:
client.off('progress', handler);

// Or disconnect client:
client.disconnect();  // Removes all listeners
```

**Diagnostic Script:**
```javascript
async function diagnosePerformance() {
  const client = new OptimizerStreamClient();
  const ui = new StreamUIHandler(client);
  
  let frameCount = 0;
  let fps = 0;
  let lastTime = performance.now();
  
  // Measure FPS
  function measureFPS() {
    frameCount++;
    const now = performance.now();
    if (now - lastTime >= 1000) {
      fps = frameCount;
      console.log(`FPS: ${fps}`);
      frameCount = 0;
      lastTime = now;
    }
    requestAnimationFrame(measureFPS);
  }
  
  // Measure memory
  let maxMemory = 0;
  function measureMemory() {
    if (performance.memory) {
      const mb = (performance.memory.usedJSHeapSize / 1048576).toFixed(2);
      maxMemory = Math.max(maxMemory, performance.memory.usedJSHeapSize);
      console.log(`Memory: ${mb}MB`);
    }
    setTimeout(measureMemory, 1000);
  }
  
  measureFPS();
  measureMemory();
  
  await client.connect();
  const result = await client.startOptimization({
    iterations: 25,
    objective: 'pareto'
  });
  
  console.log(`\n=== Performance Summary ===`);
  console.log(`Minimum FPS: ${fps}`);
  console.log(`Max Memory: ${(maxMemory / 1048576).toFixed(2)}MB`);
  console.log(`Result: ${result.final_score.toFixed(4)}`);
}

diagnosePerformance();
```

---

## Data Validation Issues

### Problem: "Results seem incorrect"

**Symptoms:**
- Pareto front contains dominated solutions
- Converge rate is not monotonic
- Improvement percent negative
- NaN values in results

**Root Causes & Solutions:**

```javascript
// 1. Dominated solutions in Pareto front
// This indicates ParetoFrontManager bug or not initialized
// Solution: Verify in aiOptimizer.js:
const paretoManager = new ParetoFrontManager();
// And after each solution:
paretoManager.addSolution(solution);

// 2. Convergence rate NaN
// WRONG: Division by zero in convergence calculation
convergence_rate = improvement / iterations;  // If improvement is 0?

// RIGHT: Handle edge cases
convergence_rate = iterations > 0 ? improvement / iterations : 0;

// 3. Negative improvement percent
// WRONG: Current score worse than initial score
initial_score = 100;
current_score = 50;
improvement = ((current_score - initial_score) / initial_score) * 100;  // Negative!

// This is valid! It means optimization got worse (bad solution)
// Only valid if optimization minimizes objective

// RIGHT: Understand optimization direction
if (objective === 'minimize') {
  improvement = ((initial_score - current_score) / initial_score) * 100;
} else if (objective === 'maximize') {
  improvement = ((current_score - initial_score) / initial_score) * 100;
}

// 4. Final score is 0 or very small
// WRONG: Optimization didn't change anything
// RIGHT: Check if optimization actually ran:
if (result.iterations_completed < iterations_requested) {
  console.log('Optimization stopped early');
}

// 5. Pareto front always same size
// WRONG: Not finding new solutions
// Check:
// - Are parameters being modified?
paretoManager.addSolution() correctly called?
// - Is domination check working?
```

**Validation Script:**
```javascript
async function validateResults() {
  const client = new OptimizerStreamClient();
  await client.connect();
  
  const result = await client.startOptimization({
    iterations: 25,
    objective: 'pareto'
  });
  
  console.log('=== Result Validation ===');
  
  // Check 1: Score is numeric
  if (typeof result.final_score !== 'number' || isNaN(result.final_score)) {
    console.error('✗ Invalid score:', result.final_score);
  } else {
    console.log('✓ Score is numeric:', result.final_score);
  }
  
  // Check 2: Improvement is reasonable
  if (result.improvement_percent < -100 || result.improvement_percent > 100) {
    console.warn('⚠ Unusual improvement:', result.improvement_percent + '%');
  } else {
    console.log('✓ Improvement is reasonable:', result.improvement_percent + '%');
  }
  
  // Check 3: Pareto front is valid
  const frontSolutions = result.paretoFront;
  console.log(`✓ Pareto front size: ${frontSolutions.length}`);
  
  // Verify non-domination
  let allNonDominated = true;
  for (let i = 0; i < frontSolutions.length; i++) {
    for (let j = 0; j < frontSolutions.length; j++) {
      if (i !== j) {
        const si = frontSolutions[i].metrics;
        const sj = frontSolutions[j].metrics;
        
        // i should not dominate j
        const iDominates = 
          si.power <= sj.power &&
          si.delay <= sj.delay &&
          si.area <= sj.area &&
          (si.power < sj.power || si.delay < sj.delay || si.area < sj.area);
        
        if (iDominates) {
          console.error(`✗ Pareto violation: ${i} dominates ${j}`);
          allNonDominated = false;
        }
      }
    }
  }
  
  if (allNonDominated) {
    console.log('✓ All solutions in Pareto front are non-dominated');
  }
  
  // Check 4: Iterations completed
  if (result.iterations_completed === result.total_iterations) {
    console.log('✓ Completed all iterations');
  } else {
    console.warn(`⚠ Stopped early: ${result.iterations_completed}/${result.total_iterations}`);
  }
  
  // Check 5: Convergence trend
  if (result.convergence_trend < 0) {
    console.warn('⚠ Convergence trending downward (optimization slowing)');
  } else {
    console.log('✓ Convergence trending upward');
  }
}

validateResults();
```

---

## Network Issues

### Problem: "WebSocket disconnects randomly"

**Symptoms:**
- Connection drops after 1-5 minutes
- `disconnected` event fires unexpectedly
- Works on WiFi but not on mobile
- Works locally but not on production

**Root Causes & Solutions:**

```javascript
// 1. Network timeout (proxy/firewall)
// WRONG: No keep-alive mechanism
// WebSocket can timeout after 30-60 seconds of inactivity

// RIGHT: Implement ping/pong
// Server (wsServer.js should have):
ws.on('pong', () => {
  console.log('Pong received - connection alive');
});

// Client periodically sends ping:
setInterval(() => {
  if (client.connected) {
    ws.ping();  // ws module auto-responds with pong
  }
}, 30000);  // Every 30 seconds

// 2. Mobile 4G/5G switching
// WRONG: Assumes persistent connection
// When phone switches networks, connection breaks

// RIGHT: Implement auto-reconnection
client.on('disconnected', async () => {
  console.log('Connection lost, attempting to reconnect...');
  await new Promise(r => setTimeout(r, 1000));
  try {
    await client.connect();
  } catch (err) {
    console.error('Reconnection failed:', err);
  }
});

// 3. Proxy/NAT timeout
// These typically timeout connections after 60-120 seconds
// Solution: Use keepalive (see #1)

// 4. Server-side resource leak
// After many optimizations, server runs out of memory
// Check server logs for:
// "FATAL: out of memory"
// Solution:
// - Reduce history size in client
// - Implement server-side cleanup of closed connections
// - Add garbage collection monitoring

// 5. SSL/TLS certificate issues (wss://)
// WRONG: Self-signed cert without trust
// Browser refuses connection with console warning

// RIGHT: For production
// - Use valid certificate from trusted CA
// - For dev: Add self-signed cert to browser trust
```

**Diagnostic Script:**
```javascript
async function diagnoseNetworkStability() {
  const client = new OptimizerStreamClient();
  
  let disconnections = 0;
  let reconnectionAttempts = 0;
  
  client.on('disconnected', async () => {
    disconnections++;
    console.log(`Disconnection #${disconnections}`);
    
    // Try to reconnect
    reconnectionAttempts++;
    await new Promise(r => setTimeout(r, 1000));
    try {
      await client.connect();
      console.log(`✓ Reconnected`);
    } catch (err) {
      console.error(`✗ Reconnection failed: ${err.message}`);
    }
  });
  
  // Simulate long-running optimization
  await client.connect();
  
  console.log('Starting 10-minute network stability test...');
  const startTime = performance.now();
  
  // Ping every 30 seconds
  const pingInterval = setInterval(() => {
    const elapsed = ((performance.now() - startTime) / 1000).toFixed(1);
    console.log(`${elapsed}s: Checking connection...`);
    
    if (!client.connected) {
      console.warn(`${elapsed}s: ✗ NOT connected`);
    } else {
      console.log(`${elapsed}s: ✓ Connected`);
    }
  }, 30000);
  
  // Run for 10 minutes or until disconnected
  await new Promise(r => {
    setTimeout(r, 600000);  // 10 minutes
  });
  
  clearInterval(pingInterval);
  console.log(`\n=== Network Stability Report ===`);
  console.log(`Total uptime: ${((performance.now() - startTime) / 1000 / 60).toFixed(1)} minutes`);
  console.log(`Disconnections: ${disconnections}`);
  console.log(`Reconnection attempts: ${reconnectionAttempts}`);
}

// Run: diagnoseNetworkStability();
```

---

## Quick Reference

| Issue | Likely Cause | Quick Fix |
|-------|--------------|-----------|
| Won't connect | Server not running | `node services/api/src/server.js` |
| Connected but no updates | Event listeners added too late | Add listeners BEFORE calling `startOptimization()` |
| UI not updating | Missing HTML elements | Check browser DevTools, add missing `<div>` elements |
| Frozen browser | Too many DOM updates | Use `StreamUIHandler` for automatic batching |
| Random disconnects | Network timeout | Implement keepalive pings (every 30s) |
| Memory growing | Memory leak | Call `client.disconnect()` to clean up |
| Wrong results | Pareto manager issue | Check import in aiOptimizer.js |
| Super slow | Message buffering disabled | Verify `BUFFER_FLUSH_INTERVAL = 50` in wsServer.js |

---

## Getting Help

If issue not in this guide:

1. **Run diagnostic script** (see above for each section)
2. **Check browser console** for error messages
3. **Check server logs** for server-side errors
4. **Enable debug mode** in client:
   ```javascript
   const client = new OptimizerStreamClient();
   client.debug = true;  // Extra logging
   ```
5. **Review WEBSOCKET_UPGRADE_README.md** message type specifications
6. **Check network tab** in DevTools for message content
7. **Run validation checklist** to verify setup

---

**Document updated: 2024**
**Last tested with: Node.js 18+, Chrome 120+**
