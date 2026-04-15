const TECH_SCALE = {
  180: 1.0,
  90: 0.52,
  45: 0.28,
  28: 0.2,
  14: 0.105,
  7: 0.065,
  5: 0.045,
  3: 0.028,
  2: 0.02,
  1: 0.012,
  0.7: 0.009,
  0.5: 0.007,
  0.3: 0.005,
};

function stableHash(parts) {
  const input = Array.isArray(parts) ? parts.join('|') : String(parts);
  let hash = 2166136261;
  for (let i = 0; i < input.length; i += 1) {
    hash ^= input.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function seededUnit(seed, channel = 0) {
  let x = (seed + channel * 0x9e3779b9) >>> 0;
  x ^= x >>> 16;
  x = Math.imul(x, 0x7feb352d);
  x ^= x >>> 15;
  x = Math.imul(x, 0x846ca68b);
  x ^= x >>> 16;
  return (x >>> 0) / 4294967295;
}

function normalizeTechNode(techNode) {
  const value = Number(techNode);
  return Number.isFinite(value) ? value : 28;
}

export function simulateCmos({
  wn,
  wp,
  vdd,
  temp,
  cl_ff,
  corner,
  tech_node,
}) {
  const techNode = normalizeTechNode(tech_node);
  const mcSeed = stableHash([
    Number(wn).toFixed(4),
    Number(wp).toFixed(4),
    Number(vdd).toFixed(4),
    Number(temp).toFixed(2),
    Number(cl_ff).toFixed(4),
    String(corner),
    String(techNode),
  ]);

  const mcProfile = {
    mu: 0.82 + seededUnit(mcSeed, 0) * 0.36,
    vth: 0.9 + seededUnit(mcSeed, 1) * 0.2,
    cox_k: 0.95 + seededUnit(mcSeed, 2) * 0.1,
  };

  const cornerModel = {
    SS: { mu: 0.7, vth: 1.1, cox_k: 0.9 },
    TT: { mu: 1.0, vth: 1.0, cox_k: 1.0 },
    FF: { mu: 1.3, vth: 0.9, cox_k: 1.08 },
    SF: { mu: 1.12, vth: 0.95, cox_k: 1.03 },
    FS: { mu: 0.88, vth: 1.05, cox_k: 0.97 },
    MC: mcProfile,
  }[corner] || { mu: 1.0, vth: 1.0, cox_k: 1.0 };

  const ts = TECH_SCALE[techNode] || 0.2;
  const tk = Number(temp) + 273.15;
  const tf = Math.pow(300 / tk, 1.5);
  const epsOx = 3.9 * 8.854e-12;
  const tox = ts * 1.2e-9;
  const cox = epsOx / tox;

  const muN0 = 420e-4;
  const muP0 = 150e-4;
  const muN = muN0 * tf * cornerModel.mu;
  const muP = muP0 * tf * cornerModel.mu;
  const vth0 = Math.min((0.32 * Number(vdd)) / 1.2, 0.4);
  const vth = vth0 * cornerModel.vth;

  const quantumPenalty = techNode < 1 ? 1 + (1 - techNode) * 0.35 : 1;
  const quantumLeakage = techNode < 1 ? 1 + (1 - techNode) * 1.8 : 1;
  const vov = Math.max(Number(vdd) - vth, 0.05) / quantumPenalty;
  const lmin = ts * 28e-9;
  const wnMeters = Number(wn) * 1e-6;
  const wpMeters = Number(wp) * 1e-6;
  const idN =
    0.5 * muN * cox * cornerModel.cox_k * (wnMeters / lmin) * vov * vov;
  const idP =
    0.5 * muP * cox * cornerModel.cox_k * (wpMeters / lmin) * vov * vov;
  const id = Math.min(idN, idP);
  const cl =
    Number(cl_ff) * 1e-15 + (wnMeters + wpMeters) * cox * lmin * 2;
  const tpd = (cl * Number(vdd)) / Math.max(id / quantumPenalty, 1e-13);
  const freqHz = 0.5 / tpd;
  const alpha = 0.1;
  const pDyn = alpha * cl * Number(vdd) * Number(vdd) * freqHz;
  const nVt = 1.3 * 0.02585 * (tk / 300);
  const iLeak =
    1e-9 * Number(wn) * Math.exp(-vth / nVt) * cornerModel.mu * tf;
  const pStat = Number(vdd) * iLeak * quantumLeakage;
  const powerWatts = pDyn + pStat;
  const fom = freqHz / Math.max(powerWatts, 1e-15);

  return {
    freq: +(freqHz / 1e9).toFixed(4),
    power: +(powerWatts * 1e3).toFixed(4),
    delay: +(tpd * 1e12).toFixed(4),
    fom: +(fom / 1e9).toFixed(3),
    id_n: +(idN * 1e6).toFixed(3),
    id_p: +(idP * 1e6).toFixed(3),
    vth: +vth.toFixed(4),
    cox: +(cox * 1e-3).toFixed(3),
    vov: +vov.toFixed(3),
  };
}

export function buildPvtSweep(params) {
  const corners = ['SS', 'TT', 'FF', 'SF', 'FS', 'MC'];
  const temps = [-40, 0, 27, 85, 125];
  const baseMin = Math.max(0.38, +(Number(params.vdd || 1.2) * 0.72).toFixed(2));
  const baseMax = Math.min(3.3, +(Number(params.vdd || 1.2) * 1.28).toFixed(2));
  const vdds = [
    baseMin,
    +((baseMin + baseMax) / 2).toFixed(2),
    +Number(params.vdd || 1.2).toFixed(2),
    baseMax,
  ]
    .filter((value, index, arr) => arr.indexOf(value) === index)
    .sort((a, b) => a - b);

  const result = {};
  for (const sweepCorner of corners) {
    result[sweepCorner] = temps.flatMap((sweepTemp) =>
      vdds.map((sweepVdd) => ({
        temp: sweepTemp,
        vdd: sweepVdd,
        ...simulateCmos({
          ...params,
          temp: sweepTemp,
          vdd: sweepVdd,
          corner: sweepCorner,
        }),
      }))
    );
  }

  return result;
}

export function buildTwinAging(params) {
  const years = Math.max(Number(params.years || 10), 1);
  const base = simulateCmos(params);
  const normYears = Math.max(years / 10, 0.1);
  const stress = Math.max(Number(params.vdd || 1.0) / 1.0, 0.6);
  const thermal = Math.max((Number(params.temp || 27) + 40) / 165, 0.15);
  const geom = Math.max(
    0.75,
    Math.min((Number(params.wn || 0.5) + Number(params.wp || 1.0)) / 2.5, 1.6)
  );
  const techFactor = Math.max(1, 28 / Math.max(Number(params.tech_node || 28), 0.3));
  const nbtiDvthMv =
    8.5 *
    Math.pow(normYears, 0.24) *
    Math.pow(stress, 1.55) *
    Math.pow(thermal, 1.15) *
    techFactor /
    geom;
  const hciDidPercent =
    1.6 *
    Math.pow(normYears, 0.42) *
    Math.pow(stress, 2.1) *
    Math.pow(thermal, 1.2) *
    techFactor /
    geom;
  const mtfYears = Math.max(
    3,
    42 * geom * Math.exp((95 - Number(params.temp || 27)) / 70) / Math.pow(stress, 2.8)
  );
  const healthScore = Math.max(
    55,
    Math.min(99.2, 100 - nbtiDvthMv * 0.55 - hciDidPercent * 1.9 - Math.max(0, 10 - mtfYears) * 0.7)
  );
  const degradedFrequency = +(base.freq * Math.max(healthScore / 100, 0.6)).toFixed(4);
  const frequencyLossPercent = +((1 - degradedFrequency / base.freq) * 100).toFixed(2);
  const powerIncreasePercent = +Math.max(nbtiDvthMv / 50, 0).toFixed(2);

  return {
    years,
    nbti_dvth_mv: +nbtiDvthMv.toFixed(2),
    hci_did_percent: +hciDidPercent.toFixed(3),
    mtf_years: +mtfYears.toFixed(2),
    health_score: +healthScore.toFixed(2),
    degraded_frequency_ghz: degradedFrequency,
    frequency_loss_percent: frequencyLossPercent,
    power_increase_percent: powerIncreasePercent,
    reliability_score:
      healthScore >= 90 ? 'Excellent' : healthScore >= 80 ? 'Good' : healthScore >= 70 ? 'Caution' : 'Critical',
    recommendations: {
      status: 'MODELLED',
      action:
        healthScore >= 85
          ? 'Nominal aging margin is acceptable for beta operation.'
          : 'Reduce VDD or launch ADA to recover long-term reliability margin.',
      avs_table: [
        { year: 0, vdd: Number(params.vdd || 1.0) },
        { year: Math.round(years / 2), vdd: +(Number(params.vdd || 1.0) + 0.03).toFixed(2) },
        { year, vdd: +(Number(params.vdd || 1.0) + 0.05).toFixed(2) },
      ],
    },
  };
}

export function buildOptimizerCandidates(params) {
  const maxPower = Number.isFinite(Number(params.max_power))
    ? Number(params.max_power)
    : Number.POSITIVE_INFINITY;
  const minFreq = Number.isFinite(Number(params.min_freq))
    ? Number(params.min_freq)
    : 0;
  const candidates = [];
  for (let wn = 0.1; wn <= 5.01; wn += 0.1) {
    for (let wp = 0.1; wp <= 5.01; wp += 0.1) {
      const point = simulateCmos({
        ...params,
        wn: +wn.toFixed(1),
        wp: +wp.toFixed(1),
      });
      if (point.power <= maxPower && point.freq >= minFreq) {
        candidates.push({
          wn: +wn.toFixed(1),
          wp: +wp.toFixed(1),
          ...point,
        });
      }
    }
  }
  return candidates;
}

export function rankOptimizerCandidates(candidates, objective = 'pareto') {
  if (!candidates.length) {
    return [];
  }

  if (objective === 'power') {
    return [...candidates].sort((a, b) => a.power - b.power || b.freq - a.freq);
  }
  if (objective === 'freq') {
    return [...candidates].sort((a, b) => b.freq - a.freq || a.power - b.power);
  }
  if (objective === 'fom') {
    return [...candidates].sort((a, b) => b.fom - a.fom || b.freq - a.freq);
  }

  const maxFreq = Math.max(...candidates.map((item) => item.freq), 1);
  const maxPower = Math.max(...candidates.map((item) => item.power), 1);
  return [...candidates].sort((a, b) => {
    const scoreA = a.freq / maxFreq - (a.power / maxPower) * 0.4;
    const scoreB = b.freq / maxFreq - (b.power / maxPower) * 0.4;
    return scoreB - scoreA;
  });
}

export function buildTradeoffExplanation(bestDesign, objective = 'pareto') {
  if (!bestDesign) {
    return 'No design satisfied the current constraints.';
  }

  if (objective === 'power') {
    return `Lowest-power candidate holds ${bestDesign.power.toFixed(3)} mW at ${bestDesign.freq.toFixed(3)} GHz.`;
  }
  if (objective === 'freq') {
    return `Highest-frequency candidate reaches ${bestDesign.freq.toFixed(3)} GHz with ${bestDesign.power.toFixed(3)} mW.`;
  }
  if (objective === 'fom') {
    return `Best figure-of-merit design balances ${bestDesign.freq.toFixed(3)} GHz against ${bestDesign.power.toFixed(3)} mW.`;
  }
  return `Pareto-ranked candidate uses WN ${bestDesign.wn.toFixed(1)} µm and WP ${bestDesign.wp.toFixed(1)} µm to balance ${bestDesign.freq.toFixed(3)} GHz at ${bestDesign.power.toFixed(3)} mW.`;
}

export function buildAiReply(message, context = {}) {
  const lower = String(message || '').toLowerCase();
  const freq = Number(context.freq || 0);
  const power = Number(context.power || 0);
  const delay = Number(context.delay || 0);
  const wn = Number(context.wn || 0.5);
  const wp = Number(context.wp || 1.0);
  const corner = context.corner || 'TT';
  const techNode = context.tech_node || context.techNode || 28;

  if (/spice|netlist/.test(lower)) {
    return [
      '.title SILIQUESTA inverter',
      `VDD vdd 0 ${Number(context.vdd || 1.2).toFixed(2)}`,
      `VIN in 0 PULSE(0 ${Number(context.vdd || 1.2).toFixed(2)} 0 10p 10p 1n 2n)`,
      `MNMOS out in 0 0 nmos W=${wn.toFixed(2)}u L=${normalizeTechNode(techNode).toFixed(2)}n`,
      `MPMOS out in vdd vdd pmos W=${wp.toFixed(2)}u L=${normalizeTechNode(techNode).toFixed(2)}n`,
      '.tran 10p 5n',
      '.end',
    ].join('\n');
  }

  if (/aging|lifetime|reliability/.test(lower)) {
    return `Reliability view: ${corner} at ${techNode}nm is currently estimated near ${delay.toFixed(3)} ps delay. Lowering VDD or reducing load capacitance will improve long-term NBTI/HCI margin.`;
  }

  if (/optimi|tradeoff|pareto/.test(lower)) {
    return `Optimization readout: WN/WP=${wn.toFixed(2)}/${wp.toFixed(2)} currently yields ${freq.toFixed(3)} GHz at ${power.toFixed(3)} mW. Increase WN to push frequency, or trim VDD/load to lower power.`;
  }

  return `SILIQUESTA analysis: ${corner} corner at ${techNode}nm is tracking ${freq.toFixed(3)} GHz, ${power.toFixed(3)} mW, and ${delay.toFixed(3)} ps. Run ADA for a wider Pareto search or PVT for confidence across operating conditions.`;
}
