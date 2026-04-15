# WebSocket Streaming - Implementation Guide

## Quick Start (5 minutes)

### Step 1: Include the client library

```html
<script type="module">
  import { OptimizerStreamClient, StreamUIHandler } from './optimizer-stream-client.js';
  
  window.initOptimizer = async function() {
    const client = new OptimizerStreamClient();
    const ui = new StreamUIHandler(client);
    
    await client.connect();
    window.optimizerClient = client;
  }
</script>
```

### Step 2: Add HTML elements for real-time display

```html
<div class="optimizer-panel">
  <!-- Progress Bar -->
  <div class="progress-container">
    <div id="optimizer-progress-bar" class="progress-fill"></div>
  </div>
  
  <!-- Metrics Row -->
  <div class="metrics-row">
    <div>
      <span>Iteration:</span>
      <span id="optimizer-iterations">0/25</span>
    </div>
    <div>
      <span>Convergence:</span>
      <span id="optimizer-convergence">0.0%</span>
    </div>
    <div>
      <span>Pareto Front:</span>
      <span id="optimizer-status">Initializing...</span>
    </div>
  </div>
  
  <!-- Pareto Front Display -->
  <div id="optimizer-pareto" class="pareto-display"></div>
  
  <!-- Status Message -->
  <div id="optimizer-message" class="status-message"></div>
</div>
```

### Step 3: Start optimization

```javascript
async function startOptimization() {
  const client = window.optimizerClient;
  
  try {
    const result = await client.startOptimization({
      W: 2.5,
      L: 1.5,
      V: 1.0,
      iterations: 25,
      objective: 'pareto',
      max_power: 6.0,
      max_delay: 30.0
    });
    
    console.log('✓ Optimization complete');
    console.log('Improvement:', result.improvement_percent);
    console.log('Pareto front size:', result.paretoFront.length);
    
  } catch (error) {
    console.error('✗ Optimization failed:', error);
  }
}
```

## Example 1: Progress Display

### HTML
```html
<div class="progress-demo">
  <h2>Optimization Progress</h2>
  
  <!-- Main Progress Bar -->
  <div class="progress-bar-container">
    <div id="demo-progress" class="progress-bar-fill"></div>
  </div>
  <p>Progress: <span id="demo-progress-text">0</span>%</p>
  
  <!-- Iteration Counter -->
  <p>Iteration: <span id="demo-iteration">0</span> / <span id="demo-total">25</span></p>
  
  <!-- Convergence Rate -->
  <p>Convergence Rate: <span id="demo-convergence">0.00</span></p>
  
  <!-- Start Button -->
  <button onclick="startProgressDemo()">Start Optimization</button>
</div>
```

### JavaScript
```javascript
async function startProgressDemo() {
  const client = new OptimizerStreamClient();
  await client.connect();
  
  // Update UI on progress events
  client.on('progress', (data) => {
    document.getElementById('demo-progress').style.width = data.progress + '%';
    document.getElementById('demo-progress-text').textContent = Math.round(data.progress);
    document.getElementById('demo-iteration').textContent = data.iteration;
    document.getElementById('demo-total').textContent = data.total;
    document.getElementById('demo-convergence').textContent = data.convergence.rate.toFixed(4);
  });
  
  // Start optimization
  await client.startOptimization({
    W: 2.5,
    L: 1.5,
    V: 1.0,
    iterations: 25,
    objective: 'pareto'
  });
}
```

### CSS
```css
.progress-bar-container {
  width: 100%;
  height: 25px;
  background-color: #e0e0e0;
  border-radius: 12px;
  overflow: hidden;
  margin: 15px 0;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #4CAF50, #81C784);
  width: 0%;
  transition: width 0.3s ease;
}
```

## Example 2: Pareto Front Visualization

### HTML
```html
<div class="pareto-demo">
  <h2>Pareto Front Evolution</h2>
  
  <div class="pareto-stats">
    <div class="stat">
      <label>Front Size</label>
      <span id="pareto-size">0</span>
    </div>
    <div class="stat">
      <label>Hypervolume</label>
      <span id="pareto-hypervolume">0.00</span>
    </div>
    <div class="stat">
      <label>Diversity</label>
      <span id="pareto-diversity">0.00</span>
    </div>
  </div>
  
  <!-- Solutions List -->
  <div id="pareto-solutions" class="solutions-list"></div>
  
  <button onclick="startParetoDemo()">Start Optimization</button>
</div>
```

### JavaScript
```javascript
async function startParetoDemo() {
  const client = new OptimizerStreamClient();
  await client.connect();
  
  client.on('pareto:update', (data) => {
    // Update statistics
    document.getElementById('pareto-size').textContent = data.size;
    document.getElementById('pareto-hypervolume').textContent = data.hypervolume.toFixed(2);
    document.getElementById('pareto-diversity').textContent = 
      data.diversity.spatialDiversity.toFixed(3);
    
    // Display Pareto solutions
    const solutionsList = document.getElementById('pareto-solutions');
    solutionsList.innerHTML = data.fronts.map((front, i) => `
      <div class="solution-card">
        <h4>Solution ${i + 1}</h4>
        <div class="param-grid">
          <div>W: ${front.params.W.toFixed(2)} μm</div>
          <div>L: ${front.params.L.toFixed(2)} μm</div>
          <div>V: ${front.params.V.toFixed(2)} V</div>
        </div>
        <div class="metrics-grid">
          <div>Power: ${front.metrics.power.toFixed(2)} W</div>
          <div>Delay: ${front.metrics.delay.toFixed(2)} ns</div>
          <div>Area: ${front.metrics.area.toFixed(2)} μm²</div>
        </div>
      </div>
    `).join('');
  });
  
  await client.startOptimization({
    iterations: 25,
    objective: 'pareto'
  });
}
```

### CSS
```css
.pareto-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-bottom: 20px;
}

.stat {
  padding: 15px;
  background: #f5f5f5;
  border-radius: 8px;
  text-align: center;
}

.stat label {
  display: block;
  font-size: 0.9em;
  color: #666;
  margin-bottom: 5px;
}

.stat span {
  display: block;
  font-size: 1.5em;
  font-weight: bold;
  color: #333;
}

.solutions-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 10px;
  margin-bottom: 15px;
}

.solution-card {
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: #fafafa;
}

.solution-card h4 {
  margin: 0 0 10px;
  color: #333;
}

.param-grid, .metrics-grid {
  font-size: 0.85em;
  line-height: 1.6;
}

.metrics-grid {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #ddd;
  color: #666;
}
```

## Example 3: Training Status Monitor

### HTML
```html
<div class="training-monitor">
  <h2>Training Status</h2>
  
  <div class="phase-badge" id="phase-badge">Initializing...</div>
  
  <div class="status-grid">
    <div class="status-item">
      <span class="label">Phase</span>
      <span id="phase-status">initialization</span>
    </div>
    <div class="status-item">
      <span class="label">Progress</span>
      <span id="progress-status">0%</span>
    </div>
    <div class="status-item">
      <span class="label">Est. Time</span>
      <span id="time-status">--</span>
    </div>
    <div class="status-item">
      <span class="label">Solutions</span>
      <span id="solutions-status">0</span>
    </div>
  </div>
  
  <!-- Timeline -->
  <div class="timeline" id="timeline"></div>
  
  <button onclick="startStatusDemo()">Start Monitoring</button>
</div>
```

### JavaScript
```javascript
const statusEvents = [];

async function startStatusDemo() {
  const client = new OptimizerStreamClient();
  await client.connect();
  
  // Clear previous events
  statusEvents.length = 0;
  document.getElementById('timeline').innerHTML = '';
  
  client.on('status:update', (data) => {
    // Update status display
    document.getElementById('phase-badge').textContent = data.phase.toUpperCase();
    document.getElementById('phase-badge').className = 
      `phase-badge phase-${data.phase}`;
    
    document.getElementById('phase-status').textContent = data.phase;
    document.getElementById('progress-status').textContent = data.progress + '%';
    document.getElementById('solutions-status').textContent = data.paretoFrontSize;
    
    if (data.estTimeRemaining) {
      const secs = (data.estTimeRemaining / 1000).toFixed(1);
      document.getElementById('time-status').textContent = secs + 's';
    }
    
    // Add timeline event
    statusEvents.push({
      phase: data.phase,
      time: new Date().toLocaleTimeString()
    });
    
    updateTimeline();
  });
  
  await client.startOptimization({
    iterations: 25,
    objective: 'pareto'
  });
}

function updateTimeline() {
  const timeline = document.getElementById('timeline');
  timeline.innerHTML = statusEvents.map(e => `
    <div class="timeline-item">
      <span class="time">${e.time}</span>
      <span class="event">${e.phase}</span>
    </div>
  `).join('');
}
```

### CSS
```css
.phase-badge {
  display: inline-block;
  padding: 10px 15px;
  border-radius: 20px;
  font-weight: bold;
  margin-bottom: 15px;
  text-transform: uppercase;
  font-size: 0.9em;
}

.phase-badge.phase-initialization { background: #E3F2FD; color: #1976D2; }
.phase-badge.phase-optimizing { background: #FFF3E0; color: #F57C00; }
.phase-badge.phase-completed { background: #E8F5E9; color: #388E3C; }

.status-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 20px;
}

.status-item {
  padding: 12px;
  background: #f5f5f5;
  border-radius: 6px;
}

.status-item .label {
  display: block;
  font-size: 0.85em;
  color: #999;
  margin-bottom: 5px;
}

.status-item span:last-child {
  display: block;
  font-size: 1.4em;
  font-weight: bold;
  color: #333;
}

.timeline {
  border-left: 3px solid #ccc;
  padding-left: 15px;
  margin: 20px 0;
}

.timeline-item {
  padding: 10px 0;
  position: relative;
}

.timeline-item::before {
  content: '';
  position: absolute;
  left: -21px;
  top: 12px;
  width: 12px;
  height: 12px;
  background: #4CAF50;
  border-radius: 50%;
}

.timeline-item .time {
  display: block;
  font-size: 0.85em;
  color: #999;
}

.timeline-item .event {
  display: block;
  font-weight: bold;
  color: #333;
}
```

## Example 4: Real-Time Analytics Dashboard

### HTML
```html
<div class="analytics-dashboard">
  <h2>Real-Time Analytics</h2>
  
  <div class="dashboard-grid">
    <!-- Improvement Chart -->
    <div class="chart-container">
      <h3>Improvement Trend</h3>
      <canvas id="improvement-chart"></canvas>
    </div>
    
    <!-- Convergence Chart -->
    <div class="chart-container">
      <h3>Convergence Rate</h3>
      <canvas id="convergence-chart"></canvas>
    </div>
    
    <!-- Pareto Evolution -->
    <div class="chart-container">
      <h3>Pareto Front Size</h3>
      <canvas id="pareto-chart"></canvas>
    </div>
    
    <!-- Metrics Table -->
    <div class="table-container">
      <h3>Current Metrics</h3>
      <table>
        <tbody id="metrics-table"></tbody>
      </table>
    </div>
  </div>
  
  <button onclick="startAnalyticsDemo()">Start Demo</button>
</div>
```

### JavaScript (with Chart.js)
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@3"></script>
<script>
async function startAnalyticsDemo() {
  const client = new OptimizerStreamClient();
  await client.connect();
  
  // Initialize charts
  const improvementCtx = document.getElementById('improvement-chart').getContext('2d');
  const convergenceCtx = document.getElementById('convergence-chart').getContext('2d');
  const paretoCtx = document.getElementById('pareto-chart').getContext('2d');
  
  const improvementChart = new Chart(improvementCtx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: 'Improvement %',
        data: [],
        borderColor: '#4CAF50',
        backgroundColor: 'rgba(76, 175, 80, 0.1)',
        tension: 0.4
      }]
    }
  });
  
  const convergenceChart = new Chart(convergenceCtx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: 'Convergence Rate',
        data: [],
        borderColor: '#FF9800',
        backgroundColor: 'rgba(255, 152, 0, 0.1)',
        tension: 0.4
      }]
    }
  });
  
  const paretoChart = new Chart(paretoCtx, {
    type: 'bar',
    data: {
      labels: [],
      datasets: [{
        label: 'Pareto Front Size',
        data: [],
        backgroundColor: '#2196F3',
        borderColor: '#1976D2',
        borderWidth: 1
      }]
    }
  });
  
  // Update on progress
  client.on('progress', (data) => {
    improvementChart.data.labels.push(data.iteration);
    improvementChart.data.datasets[0].data.push(data.best.improvementPercent);
    
    convergenceChart.data.labels.push(data.iteration);
    convergenceChart.data.datasets[0].data.push(data.convergence.rate);
    
    // Keep data bounded
    if (improvementChart.data.labels.length > 30) {
      improvementChart.data.labels.shift();
      improvementChart.data.datasets[0].data.shift();
      
      convergenceChart.data.labels.shift();
      convergenceChart.data.datasets[0].data.shift();
    }
    
    improvementChart.update('none');
    convergenceChart.update('none');
    
    // Update metrics table
    const table = document.getElementById('metrics-table');
    table.innerHTML = `
      <tr><td>Current Score</td><td>${data.best.score.toFixed(4)}</td></tr>
      <tr><td>Improvement</td><td>${data.best.improvementPercent.toFixed(2)}%</td></tr>
      <tr><td>Convergence</td><td>${data.convergence.rate.toFixed(4)}</td></tr>
      <tr><td>No Improve</td><td>${data.convergence.noImprovementIterations}</td></tr>
    `;
  });
  
  // Update on Pareto
  client.on('pareto:update', (data) => {
    paretoChart.data.labels.push(data.iteration);
    paretoChart.data.datasets[0].data.push(data.size);
    
    if (paretoChart.data.labels.length > 30) {
      paretoChart.data.labels.shift();
      paretoChart.data.datasets[0].data.shift();
    }
    
    paretoChart.update('none');
  });
  
  // Start optimization
  await client.startOptimization({
    iterations: 25,
    objective: 'pareto'
  });
}
</script>
```

## Troubleshooting

### Issue: No connection
```javascript
// Check if server is running and WebSocket is active
const client = new OptimizerStreamClient();
try {
  await client.connect();
} catch (err) {
  console.error('Connection failed:', err.message);
}
```

### Issue: No progress updates
```javascript
// Ensure listener is registered BEFORE starting
client.on('progress', (data) => console.log(data));
// THEN start optimization
await client.startOptimization({...});
```

### Issue: High CPU usage
```javascript
// Reduce update frequency or buffer size
// Disable animations during optimization
document.body.style.animation = 'none';

// Use requestAnimationFrame (already done in StreamUIHandler)
requestAnimationFrame(() => {
  // DOM updates here
});
```

### Issue: WebSocket closed
```javascript
// Implement reconnection logic
client.on('disconnected', async () => {
  console.log('Disconnected, retrying...');
  await new Promise(r => setTimeout(r, 1000));
  try {
    await client.connect();
  } catch (err) {
    console.error('Reconnection failed:', err);
  }
});
```

## Performance Tips

1. **Batch UI Updates**: Updates are already batched every 50ms
2. **Limit History**: History is automatically bounded
3. **Debounce Chart Updates**: Update charts every N iterations (shown in examples)
4. **Use requestAnimationFrame**: Included in StreamUIHandler
5. **Throttle Event Handlers**: Count iterations before updating DOM

## Next Steps

1. Copy `optimizer-stream-client.js` to your project
2. Include in your HTML or import as module
3. Implement UI elements from examples
4. Test with development server
5. Deploy to production

---

**Ready to integrate? Start with Example 1 (Progress Display)**
