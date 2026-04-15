import { ParetoFrontManager } from './paretoFrontManager.js';

const DEFAULT_ITERATIONS = 25;

export async function optimizeCircuit(input = {}, sendUpdate = () => {}) {
  const normalized = normalizeInput(input);
  const paretoFront = new ParetoFrontManager();
  
  // Initial evaluation
  const before = {
    params: { ...normalized.initial },
    result: simulate(normalized.initial),
  };
  const beforeScore = evaluate(before.result, before.result, normalized.weights);

  // Add initial solution to Pareto front
  paretoFront.addSolution(before.params, before.result);

  let best = {
    params: { ...before.params },
    result: before.result,
    score: beforeScore,
  };

  let current = { ...normalized.initial };
  let improvementTrend = [];
  let convergenceMetrics = {
    noImproveCount: 0,
    lastBestScore: beforeScore,
  };

  // Send training initialization
  sendUpdate({
    type: 'TRAINING_STATUS',
    phase: 'initialization',
    totalIterations: normalized.iterations,
    timestamp: Date.now(),
  });

  // Main optimization loop
  for (let iteration = 1; iteration <= normalized.iterations; iteration += 1) {
    const result = simulate(current);
    const score = evaluate(result, before.result, normalized.weights);
    const constraints = validateConstraints(result, normalized.constraints);

    // Update best solution
    let isImprovement = false;
    if (constraints.all_passed && score < best.score) {
      best = {
        params: { ...current },
        result,
        score,
      };
      isImprovement = true;
      convergenceMetrics.noImproveCount = 0;
    } else {
      convergenceMetrics.noImproveCount += 1;
    }

    // Add to Pareto front
    const paretoAdded = paretoFront.addSolution(current, result);

    // Track improvement trend
    improvementTrend.push({
      iteration,
      score,
      improvement: beforeScore - score,
    });
    if (improvementTrend.length > 10) improvementTrend.shift();

    // Calculate convergence rate
    const convergenceRate = calculateConvergenceRate(improvementTrend);

    // Send optimization progress update
    sendUpdate({
      type: 'OPTIMIZATION_PROGRESS',
      iteration,
      totalIterations: normalized.iterations,
      progress: Math.round((iteration / normalized.iterations) * 100),
      current: {
        params: flattenParams(current),
        metrics: result,
        score: round(score, 4),
        constraints,
        isImprovement,
      },
      best: {
        params: flattenParams(best.params),
        metrics: best.result,
        score: round(best.score, 4),
        improvementPercent: round(((beforeScore - best.score) / Math.max(beforeScore, 0.0001)) * 100, 2),
      },
      convergence: {
        rate: round(convergenceRate, 3),
        noImprovementIterations: convergenceMetrics.noImproveCount,
        estimatedRemainingIterations: estimateRemainingIterations(
          convergenceRate,
          normalized.iterations - iteration
        ),
      },
      timestamp: Date.now(),
    });

    // Send Pareto front update (every 5 iterations or when significant change)
    if (iteration % 5 === 0 || paretoAdded) {
      sendUpdate({
        type: 'PARETO_UPDATE',
        iteration,
        paretoMetrics: paretoFront.getStreamUpdate(),
        timestamp: Date.now(),
      });
    }

    // Send training status update (every 10 iterations)
    if (iteration % 10 === 0) {
      sendUpdate({
        type: 'TRAINING_STATUS',
        phase: 'optimizing',
        iteration,
        totalIterations: normalized.iterations,
        progress: Math.round((iteration / normalized.iterations) * 100),
        paretoFrontSize: paretoFront.getParetoFront().length,
        estTimeRemaining: estimateTimeRemaining(normalized.iterations - iteration),
        timestamp: Date.now(),
      });
    }

    // Mutation and pause for streaming
    current = mutate(current, iteration, best.params, normalized.objective);
    await pause(30);
  }

  // Final evaluation
  const improvement = Math.max(0, ((beforeScore - best.score) / Math.max(beforeScore, 0.0001)) * 100);
  const constraintValidation = validateConstraints(best.result, normalized.constraints);

  const result = {
    before: {
      ...flattenParams(before.params),
      ...before.result,
      score: round(beforeScore, 4),
    },
    after: {
      ...flattenParams(best.params),
      ...best.result,
      score: round(best.score, 4),
    },
    best,
    improvement_percent: round(improvement, 2),
    iterations: normalized.iterations,
    confidence: buildConfidence(improvement, constraintValidation, normalized.iterations),
    constraint_validation: constraintValidation,
    reasoning: buildReasoning(before.result, best.result, best.params),
    paretoFront: paretoFront.getParetoFront(),
    paretoMetrics: paretoFront.getStreamUpdate(),
  };

  // Send final training status
  sendUpdate({
    type: 'TRAINING_STATUS',
    phase: 'completed',
    totalIterations: normalized.iterations,
    paretoFrontSize: paretoFront.getParetoFront().length,
    timestamp: Date.now(),
  });

  return result;
}

/**
 * Calculate convergence rate from recent improvements
 */
function calculateConvergenceRate(improvementTrend) {
  if (improvementTrend.length < 2) return 0;

  const recent = improvementTrend.slice(-5);
  const oldAvg = recent.slice(0, Math.ceil(recent.length / 2))
    .reduce((a, b) => a + b.improvement, 0) / Math.ceil(recent.length / 2);
  const newAvg = recent.slice(Math.ceil(recent.length / 2))
    .reduce((a, b) => a + b.improvement, 0) / Math.floor(recent.length / 2);

  return Math.max(0, (newAvg - oldAvg) / Math.max(oldAvg, 0.001));
}

/**
 * Estimate remaining iterations needed for convergence
 */
function estimateRemainingIterations(convergenceRate, remainingIter) {
  if (convergenceRate < 0.01) return remainingIter;
  if (convergenceRate > 0.1) return Math.max(1, Math.floor(remainingIter * 0.3));
  return Math.max(1, Math.floor(remainingIter * 0.6));
}

/**
 * Estimate time remaining (rough estimate)
 */
function estimateTimeRemaining(iterationsLeft) {
  // 30ms per iteration + small overhead
  return iterationsLeft * 35;
}

export function simulate(p = {}) {
  const W = clamp(Number(p.W ?? p.wn ?? 1), 0.5, 5);
  const L = clamp(Number(p.L ?? p.l ?? 1), 0.5, 5);
  const V = clamp(Number(p.V ?? p.vdd ?? 1.2), 0.8, 1.5);
  const k = 0.5;
  const vth = 0.4;
  const overdrive = Math.max(V - vth, 0.05);
  const id = k * (W / L) * overdrive ** 2;
  const gain = id * 10;
  const delay = 1 / (id + 0.1);
  const power = id * V;
  const area = W * L;

  return {
    gain: round(gain),
    delay: round(delay),
    power: round(power),
    area: round(area),
    voltage: round(V),
    current: round(id),
  };
}

export function evaluate(result, baseline = result, weights = {}) {
  const power = normalize(result.power, baseline.power);
  const delay = normalize(result.delay, baseline.delay);
  const area = normalize(result.area, baseline.area);
  const gain = normalize(result.gain, baseline.gain);

  return round(
    (weights.power ?? 0.5) * power +
      (weights.delay ?? 0.35) * delay +
      (weights.area ?? 0.15) * area -
      (weights.gain ?? 0.08) * gain,
    4
  );
}

function normalizeInput(input) {
  const payload = input.payload || input;
  const raw = typeof payload.input === 'string' ? parseTextInput(payload.input) : {};
  const source = {
    ...raw,
    ...payload,
    ...(payload.parameters || {}),
    ...(payload.constraints || {}),
  };

  const initial = {
    W: clamp(Number(source.W ?? source.wn ?? source.width ?? 1), 0.5, 5),
    L: clamp(Number(source.L ?? source.length ?? 1), 0.5, 5),
    V: clamp(Number(source.V ?? source.vdd ?? source.voltage ?? 1.2), 0.8, 1.5),
  };

  const objective = String(source.objective || 'pareto').toLowerCase();
  const weights = objective === 'power'
    ? { power: 0.68, delay: 0.18, area: 0.14, gain: 0.06 }
    : objective === 'freq'
      ? { power: 0.2, delay: 0.58, area: 0.12, gain: 0.12 }
      : { power: 0.5, delay: 0.35, area: 0.15, gain: 0.08 };

  return {
    initial,
    objective,
    weights,
    iterations: clamp(Math.round(Number(source.iterations || DEFAULT_ITERATIONS)), 5, 50),
    constraints: {
      max_power: numberOrNull(source.max_power ?? source.maxPower),
      max_delay: numberOrNull(source.max_delay ?? source.maxDelay),
      min_gain: numberOrNull(source.min_gain ?? source.minGain),
    },
  };
}

function mutate(current, iteration, best, objective) {
  const phase = iteration / DEFAULT_ITERATIONS;
  const widthBias = objective === 'freq' ? 0.18 : objective === 'power' ? -0.08 : 0.06;
  const voltageBias = objective === 'freq' ? 0.035 : objective === 'power' ? -0.025 : -0.006;
  const lengthBias = objective === 'freq' ? -0.035 : objective === 'power' ? 0.025 : -0.01;

  return {
    W: clamp(best.W + widthBias + Math.sin(iteration * 1.7) * (0.22 - phase * 0.08), 0.5, 5),
    L: clamp(best.L + lengthBias + Math.cos(iteration * 1.3) * (0.16 - phase * 0.05), 0.5, 5),
    V: clamp(best.V + voltageBias + Math.sin(iteration * 0.9) * (0.06 - phase * 0.02), 0.8, 1.5),
  };
}

function validateConstraints(result, constraints) {
  const powerPassed = constraints.max_power === null || result.power <= constraints.max_power;
  const delayPassed = constraints.max_delay === null || result.delay <= constraints.max_delay;
  const gainPassed = constraints.min_gain === null || result.gain >= constraints.min_gain;

  return {
    power: { enabled: constraints.max_power !== null, target: constraints.max_power, actual: result.power, passed: powerPassed },
    delay: { enabled: constraints.max_delay !== null, target: constraints.max_delay, actual: result.delay, passed: delayPassed },
    gain: { enabled: constraints.min_gain !== null, target: constraints.min_gain, actual: result.gain, passed: gainPassed },
    all_passed: powerPassed && delayPassed && gainPassed,
  };
}

function buildConfidence(improvement, constraints, iterations) {
  const improvementSignal = Math.min(Math.max(improvement / 45, 0), 1) * 0.2;
  const iterationSignal = Math.min(iterations / 25, 1) * 0.15;
  const constraintSignal = constraints.all_passed ? 0.12 : -0.08;
  return round(clamp(0.58 + improvementSignal + iterationSignal + constraintSignal, 0.35, 0.93), 2);
}

function buildReasoning(before, after, params) {
  const powerDelta = before.power - after.power;
  const delayDelta = before.delay - after.delay;
  const gainDelta = after.gain - before.gain;
  const statements = [];

  if (delayDelta > 0.01) statements.push(`reduced delay by ${round(delayDelta)} through width and overdrive tuning`);
  if (powerDelta > 0.01) statements.push(`lowered power by ${round(powerDelta)} while preserving drive current`);
  if (gainDelta > 0.01) statements.push(`improved gain by ${round(gainDelta)} using a stronger W/L operating point`);

  return `${statements.length ? statements.join(', ') : 'selected the most stable tradeoff candidate'} at W=${round(params.W)}um, L=${round(params.L)}um, V=${round(params.V)}V.`;
}

function parseTextInput(text) {
  return String(text)
    .split(/\r?\n/)
    .reduce((acc, line) => {
      const [key, ...rest] = line.split('=');
      if (!key || !rest.length) return acc;
      const value = rest.join('=').trim();
      const numeric = Number(value);
      acc[key.trim()] = Number.isFinite(numeric) && value !== '' ? numeric : value;
      return acc;
    }, {});
}

function flattenParams(params) {
  return {
    W: round(params.W),
    L: round(params.L),
    V: round(params.V),
    wn: round(params.W),
    wp: round(params.L),
    vdd: round(params.V),
  };
}

function normalize(value, baseline) {
  return Number(value || 0) / Math.max(Number(baseline || 0), 0.0001);
}

function numberOrNull(value) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

function pause(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function clamp(x, min, max) {
  return Math.max(min, Math.min(max, x));
}

function round(x, digits = 2) {
  const factor = 10 ** digits;
  return Math.round(Number(x) * factor) / factor;
}
