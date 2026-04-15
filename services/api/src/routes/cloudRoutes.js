import express from 'express';
import { authenticate, optionalAuth } from '../middleware/auth.js';
import AuthService from '../services/authService.js';
import { assertUsageAvailable, incrementUsage } from '../services/subscriptionService.js';
import {
  buildAiReply,
  buildOptimizerCandidates,
  buildPvtSweep,
  buildTradeoffExplanation,
  buildTwinAging,
  rankOptimizerCandidates,
  simulateCmos,
} from '../services/cmosEngine.js';

const router = express.Router();
const AI_URL = (process.env.AI_URL || 'http://localhost:8001').replace(/\/+$/, '');
const NORMALIZED_AI_URL = /^https?:\/\//i.test(AI_URL) ? AI_URL : `http://${AI_URL}`;

function summarizeCandidate(metrics, params = {}) {
  return {
    wn: Number(params.wn ?? params.WN ?? 0),
    wp: Number(params.wp ?? params.WP ?? 0),
    freq: Number(metrics.freq || 0),
    power: Number(metrics.power || 0),
    delay: Number(metrics.delay || 0),
    fom: Number(metrics.fom || 0),
    vth: Number(metrics.vth || 0),
  };
}

function scoreCandidate(candidate, baseline) {
  const basePower = Math.max(Number(baseline.power || 0), 0.001);
  const baseDelay = Math.max(Number(baseline.delay || 0), 0.001);
  const baseArea = Math.max(Number(baseline.wn || 0) + Number(baseline.wp || 0), 0.001);
  const area = Math.max(Number(candidate.wn || 0) + Number(candidate.wp || 0), 0.001);
  return (
    0.45 * (Number(candidate.power || 0) / basePower) +
    0.4 * (Number(candidate.delay || 0) / baseDelay) +
    0.15 * (area / baseArea)
  );
}

function buildImprovementSummary(before, after) {
  const beforeScore = scoreCandidate(before, before);
  const afterScore = scoreCandidate(after, before);
  const improvementPercent = beforeScore > 0
    ? ((beforeScore - afterScore) / beforeScore) * 100
    : 0;
  const delayDelta = before.delay - after.delay;
  const powerDelta = before.power - after.power;
  const freqDelta = after.freq - before.freq;
  const statements = [];

  if (delayDelta > 0.0001) {
    statements.push(`Reduced delay by ${delayDelta.toFixed(3)} ps`);
  }
  if (powerDelta > 0.0001) {
    statements.push(`cut power by ${powerDelta.toFixed(3)} mW`);
  }
  if (freqDelta > 0.0001) {
    statements.push(`raised frequency by ${freqDelta.toFixed(3)} GHz`);
  }
  if (!statements.length) {
    statements.push('preserved the operating point while improving overall ranking stability');
  }

  return {
    improvementPercent: +improvementPercent.toFixed(2),
    reasoning: `${statements.join(', ')} using WN ${after.wn.toFixed(2)} µm and WP ${after.wp.toFixed(2)} µm.`,
  };
}

function buildConstraintValidation(params, candidate) {
  const maxPower = Number.isFinite(Number(params.max_power)) ? Number(params.max_power) : null;
  const minFreq = Number.isFinite(Number(params.min_freq)) ? Number(params.min_freq) : null;
  const validation = {
    power: {
      enabled: maxPower !== null,
      target: maxPower,
      actual: Number(candidate?.power || 0),
      passed: maxPower === null ? true : Number(candidate?.power || 0) <= maxPower,
    },
    frequency: {
      enabled: minFreq !== null,
      target: minFreq,
      actual: Number(candidate?.freq || 0),
      passed: minFreq === null ? true : Number(candidate?.freq || 0) >= minFreq,
    },
  };

  validation.all_passed = validation.power.passed && validation.frequency.passed;
  return validation;
}

function buildConfidence(bestDesign, baseline, exactCandidates, source) {
  if (!bestDesign) {
    return 0.18;
  }

  const powerGain = Math.max(0, (Number(baseline.power || 0) - Number(bestDesign.power || 0)) / Math.max(Number(baseline.power || 0), 0.001));
  const delayGain = Math.max(0, (Number(baseline.delay || 0) - Number(bestDesign.delay || 0)) / Math.max(Number(baseline.delay || 0), 0.001));
  const candidateDepth = Math.min(exactCandidates / 80, 1);
  const sourceBoost = source === 'ai-service' ? 0.08 : source === 'cloud-engine' ? 0.04 : 0;
  const confidence = 0.42 + powerGain * 0.18 + delayGain * 0.18 + candidateDepth * 0.15 + sourceBoost;
  return +Math.min(Math.max(confidence, 0.2), 0.98).toFixed(2);
}

async function callAiOptimizer(params) {
  const response = await fetch(`${NORMALIZED_AI_URL}/optimize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      parameters: {
        W_L_ratio: Math.max(Number(params.wn || 0.5) / Math.max(Number(params.wp || 1.0), 0.1), 0.1),
        finger_ratio: 1,
        supply_voltage: Number(params.vdd || 1.2),
        operating_frequency: Math.max(Number(params.min_freq || 1), 1) * 1e9,
        load_capacitance: Math.max(Number(params.cl_ff || 10), 1) * 1e-15,
        technology_node: Math.max(Number(params.tech_node || 28), 0.3) * 1e-9,
        temperature: Number(params.temp || 27),
        power_budget: Math.max(Number(params.max_power || 5), 0.1) * 1e-3,
      },
      objectives: {
        minimize_power: params.objective !== 'freq',
        maximize_speed: params.objective !== 'power',
        minimize_area: false,
        maximize_gain: params.objective === 'fom',
      },
      method: 'hybrid',
      max_iterations: 200,
    }),
  });

  if (!response.ok) {
    throw new Error(`AI optimizer failed with ${response.status}`);
  }

  return response.json();
}

router.get('/users/me', authenticate, async (req, res, next) => {
  try {
    const user = await AuthService.getUserById(req.user.userId);
    res.status(200).json({
      ...user,
      plan: 'BETA',
    });
  } catch (error) {
    next(error);
  }
});

router.post('/simulate', async (req, res) => {
  const metrics = simulateCmos(req.body || {});
  res.status(200).json({
    status: 'completed',
    simulation: metrics,
    metrics,
    source: 'cloud-engine',
  });
});

router.post('/pvt/full-sweep', async (req, res) => {
  const payload = buildPvtSweep(req.body || {});
  res.status(200).json({
    status: 'completed',
    pvt_results: payload,
    source: 'cloud-engine',
  });
});

router.post('/optimize', optionalAuth, async (req, res) => {
  const params = req.body || {};
  let planState;

  try {
    planState = await assertUsageAvailable(req.user?.userId);
  } catch (error) {
    return res.status(error.statusCode || 403).json({
      message: error.message || 'Usage limit exceeded',
      plan: error.payload,
    });
  }

  const objective = params.objective || 'pareto';
  const baseline = summarizeCandidate(
    simulateCmos(params),
    {
      wn: Number(params.wn || 0.5),
      wp: Number(params.wp || 1.0),
    }
  );
  let candidates = buildOptimizerCandidates(params);
  let exactCandidates = candidates.length;
  let source = 'cloud-engine';
  let aiSuggestion = null;
  let iterations = 12;

  if (!candidates.length) {
    candidates = buildOptimizerCandidates({
      ...params,
      max_power: Number.POSITIVE_INFINITY,
      min_freq: 0,
    });
    source = 'relaxed';
    iterations += 4;
  }

  try {
    aiSuggestion = await callAiOptimizer(params);
    iterations += Math.min(Number(aiSuggestion?.iterations_used || 8), 24);
  } catch (error) {
    source = source === 'relaxed' ? source : 'local-ranked';
    iterations += 7;
  }

  let ranked = rankOptimizerCandidates(candidates, objective).slice(0, 8);
  if (aiSuggestion?.optimized_parameters) {
    const aiDesign = simulateCmos({
      ...params,
      wn: +(Number(params.wn || 0.5) * Number(aiSuggestion.optimized_parameters.W_L_ratio || 1)).toFixed(2),
      wp: Number(params.wp || 1.0),
    });
    ranked = [
      {
        wn: +(Number(params.wn || 0.5) * Number(aiSuggestion.optimized_parameters.W_L_ratio || 1)).toFixed(2),
        wp: Number(params.wp || 1.0).toFixed ? +Number(params.wp || 1.0).toFixed(2) : Number(params.wp || 1.0),
        ...aiDesign,
      },
      ...ranked,
    ]
      .filter(
        (item, index, arr) =>
          arr.findIndex(
            (candidate) => candidate.wn === item.wn && candidate.wp === item.wp
          ) === index
      )
      .slice(0, 8);
    source = 'ai-service';
  }

  const bestDesign = ranked[0] || null;
  const after = bestDesign
    ? summarizeCandidate(bestDesign, bestDesign)
    : baseline;
  const summary = buildImprovementSummary(baseline, after);
  const constraints = buildConstraintValidation(params, after);
  const confidence = buildConfidence(after, baseline, exactCandidates, source);
  const usage = await incrementUsage(req.user?.userId);
  res.status(200).json({
    status: 'completed',
    before: baseline,
    after,
    pareto_front: ranked,
    optimal: ranked,
    best_design: bestDesign,
    ranking: ranked.map((item, index) => ({
      rank: index + 1,
      ...item,
    })),
    valid_candidates: exactCandidates,
    iterations,
    confidence,
    constraint_validation: constraints,
    plan: usage || planState,
    improvement_percent: summary.improvementPercent,
    explanation: buildTradeoffExplanation(bestDesign, objective),
    reasoning: summary.reasoning,
    source,
  });
});

router.post('/twin/compute-aging', async (req, res) => {
  const twin = buildTwinAging(req.body || {});
  res.status(200).json({
    status: 'completed',
    ...twin,
    source: 'cloud-engine',
  });
});

router.post('/ai/chat', async (req, res) => {
  const message = req.body?.message || '';
  const context = req.body?.context || {};
  res.status(200).json({
    status: 'completed',
    response: buildAiReply(message, context),
    source: 'cloud-engine',
  });
});

export default router;
