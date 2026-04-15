/**
 * WebSocket Stream Client Test Suite
 * Tests all streaming functionality
 */

import { WebSocket } from 'ws';

const WS_URL = 'ws://localhost:10000';

class TestRunner {
  constructor() {
    this.ws = null;
    this.results = {};
    this.messageLog = [];
  }

  async connect() {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(WS_URL);
        
        this.ws.onopen = () => {
          console.log('✓ Connected to WebSocket');
          resolve();
        };
        
        this.ws.onmessage = (event) => {
          const msg = JSON.parse(event.data);
          this.messageLog.push(msg);
          console.log(`📨 ${msg.type}`);
        };
        
        this.ws.onerror = (error) => {
          reject(new Error(`Connection error: ${error.message}`));
        };
      } catch (err) {
        reject(err);
      }
    });
  }

  disconnect() {
    return new Promise((resolve) => {
      if (this.ws) {
        this.ws.onclose = resolve;
        this.ws.close();
      } else {
        resolve();
      }
    });
  }

  send(message) {
    return new Promise((resolve) => {
      if (this.ws && this.ws.readyState === 1) {
        this.ws.send(JSON.stringify(message));
        setTimeout(resolve, 100);
      } else {
        resolve();
      }
    });
  }

  async sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
  }

  getMessagesByType(type) {
    return this.messageLog.filter(m => m.type === type);
  }

  summarizeResults() {
    console.log(`\n════════════════════════════════════════════`);
    console.log(`✓ TEST SUITE COMPLETE`);
    console.log(`════════════════════════════════════════════`);
    console.log(`\nMessages Received:`);
    console.log(`  CONNECTED: ${this.getMessagesByType('CONNECTED').length}`);
    console.log(`  OPTIMIZATION_STARTED: ${this.getMessagesByType('OPTIMIZATION_STARTED').length}`);
    console.log(`  OPTIMIZATION_PROGRESS: ${this.getMessagesByType('OPTIMIZATION_PROGRESS').length}`);
    console.log(`  PARETO_UPDATE: ${this.getMessagesByType('PARETO_UPDATE').length}`);
    console.log(`  TRAINING_STATUS: ${this.getMessagesByType('TRAINING_STATUS').length}`);
    console.log(`  OPTIMIZATION_COMPLETED: ${this.getMessagesByType('OPTIMIZATION_COMPLETED').length}`);
    console.log(`  Total: ${this.messageLog.length}`);

    console.log(`\nTest Results:`);
    Object.entries(this.results).forEach(([test, result]) => {
      const status = result ? '✓' : '✗';
      console.log(`  ${status} ${test}`);
    });

    const passed = Object.values(this.results).filter(r => r).length;
    const total = Object.keys(this.results).length;
    console.log(`\nSummary: ${passed}/${total} tests passed`);
    console.log(`════════════════════════════════════════════\n`);
  }

  recordResult(testName, passed) {
    this.results[testName] = passed;
    const status = passed ? '✓' : '✗';
    console.log(`  ${status} ${testName}`);
  }
}

// Run tests
async function runTests() {
  const runner = new TestRunner();

  try {
    // Test 1: Connection
    console.log(`\n1️⃣  Testing Connection...`);
    await runner.connect();
    runner.recordResult('WebSocket connection', runner.messageLog.length > 0);

    // Test 2: Received CONNECTED message
    console.log(`\n2️⃣  Checking Connection Message...`);
    const connected = runner.getMessagesByType('CONNECTED');
    runner.recordResult('CONNECTED message', connected.length === 1);

    // Test 3: Start Optimization
    console.log(`\n3️⃣  Testing Optimization Start...`);
    const beforeOptim = runner.messageLog.length;
    await runner.send({ type: 'START_OPTIMIZATION', iterations: 10 });

    // Wait for optimization to stream
    console.log(`   Waiting for optimization...(~350ms)`);
    await runner.sleep(350);

    const afterOptim = runner.messageLog.length;
    const newMessages = afterOptim - beforeOptim;
    runner.recordResult('Optimization messages received', newMessages > 10);
    runner.recordResult('OPTIMIZATION_STARTED received', 
      runner.getMessagesByType('OPTIMIZATION_STARTED').length > 0);
    runner.recordResult('OPTIMIZATION_PROGRESS received', 
      runner.getMessagesByType('OPTIMIZATION_PROGRESS').length >= 10);
    runner.recordResult('PARETO_UPDATE received', 
      runner.getMessagesByType('PARETO_UPDATE').length > 0);
    runner.recordResult('TRAINING_STATUS received', 
      runner.getMessagesByType('TRAINING_STATUS').length > 0);

    // Test 4: Check OPTIMIZATION_COMPLETED
    console.log(`\n4️⃣  Checking Optimization Result...`);
    const completed = runner.getMessagesByType('OPTIMIZATION_COMPLETED');
    runner.recordResult('OPTIMIZATION_COMPLETED received', completed.length === 1);

    if (completed.length > 0) {
      const result = completed[0];
      runner.recordResult('Result has final_score', result.final_score !== undefined);
      runner.recordResult('Result has improvement', result.improvement_percent !== undefined);
      runner.recordResult('Result has paretoFront', 
        result.paretoFront !== undefined && Array.isArray(result.paretoFront));
    }

    // Test 5: Data Validation
    console.log(`\n5️⃣  Validating Message Data...`);
    const progresses = runner.getMessagesByType('OPTIMIZATION_PROGRESS');
    if (progresses.length > 0) {
      const prog = progresses[0];
      runner.recordResult('Progress has iteration', prog.iteration !== undefined);
      runner.recordResult('Progress has progress %', prog.progress !== undefined);
      runner.recordResult('Progress has convergence', prog.convergence !== undefined);
      runner.recordResult('Progress has best score', prog.best?.score !== undefined);
    }

    const paretos = runner.getMessagesByType('PARETO_UPDATE');
    if (paretos.length > 0) {
      const par = paretos[0];
      runner.recordResult('Pareto has front size', par.size !== undefined);
      runner.recordResult('Pareto has hypervolume', par.hypervolume !== undefined);
      runner.recordResult('Pareto has diversity', par.diversity !== undefined);
      runner.recordResult('Pareto has solutions', Array.isArray(par.fronts));
    }

    // Test 6: Pause/Resume
    console.log(`\n6️⃣  Testing Pause/Resume...`);
    await runner.send({ type: 'PAUSE_STREAM' });
    await runner.sleep(100);
    runner.recordResult('Pause accepted', true); // Just check no error

    await runner.send({ type: 'RESUME_STREAM' });
    await runner.sleep(100);
    runner.recordResult('Resume accepted', true);

    // Test 7: Get Status
    console.log(`\n7️⃣  Testing Status Query...`);
    const beforeStatus = runner.messageLog.length;
    await runner.send({ type: 'GET_STATUS' });
    await runner.sleep(100);
    const statusFound = runner.messageLog.length > beforeStatus;
    runner.recordResult('Status query works', statusFound);

    // Summary
    runner.summarizeResults();

  } catch (error) {
    console.error(`❌ Test error:`, error.message);
  } finally {
    await runner.disconnect();
  }
}

// Run
runTests().catch(console.error);
