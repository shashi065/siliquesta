/**
 * SILIQUESTA - Realistic Circuit Simulation Engine
 * 
 * Transistor-level circuit modeling with MOSFET physics
 * Extensible architecture: can graduate to SPICE later
 * 
 * Features:
 * - MOSFET device modeling (I-V characteristics)
 * - Gain calculation (Av = -gm * (ro || RL))
 * - Delay estimation (RC delay model)
 * - Power consumption (static + dynamic)
 * - Temperature effects on parameters
 * - Process variations
 */

class MOSFETModel {
  /**
   * MOSFET Device Parameters
   * VTH: Threshold voltage (V)
   * KN: Transconductance parameter (A/V²)
   * λ: Channel length modulation (1/V)
   */
  constructor(params = {}) {
    this.vth = params.vth || 0.4;        // Threshold voltage (V)
    this.kn = params.kn || 20e-6;        // Transconductance (A/V²)
    this.lambda = params.lambda || 0.02; // Channel modulation
    this.cgs = params.cgs || 1e-12;      // Gate-source cap (F)
    this.cdb = params.cdb || 0.5e-12;    // Drain-bulk cap (F)
    this.rd = params.rd || 100;          // Drain resistance (Ω)
  }

  /**
   * Calculate drain current using MOSFET equation
   * Id = (Kn/2) * (W/L) * (Vgs - Vth)²(1 + λ*Vds)
   */
  drainCurrent(vgs, vds, wl = 1) {
    if (vgs <= this.vth) return 1e-9; // Cutoff region
    
    const veff = vgs - this.vth;
    const id = (this.kn * wl / 2) * Math.pow(veff, 2) * (1 + this.lambda * vds);
    
    return Math.max(id, 1e-9); // Prevent negative current
  }

  /**
   * Calculate transconductance (gm = ∂Id/∂Vgs)
   * gm = Kn * (W/L) * (Vgs - Vth)
   */
  transconductance(vgs, wl = 1) {
    if (vgs <= this.vth) return 1e-9;
    const gm = this.kn * wl * (vgs - this.vth);
    return gm;
  }

  /**
   * Calculate output impedance (ro = 1 / (λ * Id))
   */
  outputImpedance(id) {
    return 1 / (this.lambda * Math.max(id, 1e-9));
  }

  /**
   * Temperature effect on threshold voltage
   * VTH(T) = VTH(T0) - (dVTH/dT) * (T - T0)
   */
  adjustVthTemperature(tempC, tempRef = 27) {
    const dvthdt = -0.0002; // V/°C (typical)
    return this.vth + dvthdt * (tempC - tempRef);
  }

  /**
   * Temperature effect on transconductance
   * KN scales inversely with temperature
   */
  adjustKnTemperature(tempC, tempRef = 27) {
    const tempK = tempC + 273.15;
    const tempRefK = tempRef + 273.15;
    const mu_ratio = Math.pow(tempRefK / tempK, 1.5); // Mobility tempco
    return this.kn * mu_ratio;
  }
}

class CircuitSimulator {
  /**
   * Initialize circuit with device and load parameters
   */
  constructor(config = {}) {
    this.vdd = config.vdd || 1.2;           // Supply voltage (V)
    this.temp = config.temp || 27;          // Temperature (°C)
    this.processVariation = config.processVariation || 0; // -0.1 to +0.1
    this.loadCapacitance = config.cl || 10e-12; // Load cap (F)
    this.loadResistance = config.rl || 10000;   // Load resistance (Ω)
    
    // Create NMOS and PMOS transistors
    this.nmos = new MOSFETModel(config.nmos || {});
    this.pmos = new MOSFETModel({
      vth: -(config.pmos?.vth || 0.4),
      kn: (config.pmos?.kn || 10e-6),
      lambda: config.pmos?.lambda || 0.02,
      cgs: config.pmos?.cgs || 1e-12,
      cdb: config.pmos?.cdb || 0.5e-12,
      rd: config.pmos?.rd || 200,
    });

    // Apply process variation
    if (this.processVariation !== 0) {
      const factor = 1 + this.processVariation;
      this.nmos.kn *= factor;
      this.pmos.kn *= factor;
    }

    // Apply temperature effects
    this.nmos.vth = this.nmos.adjustVthTemperature(this.temp);
    this.nmos.kn = this.nmos.adjustKnTemperature(this.temp);
    this.pmos.vth = this.pmos.adjustVthTemperature(this.temp);
    this.pmos.kn = this.pmos.adjustKnTemperature(this.temp);
  }

  /**
   * Simulate inverter circuit to find operating point
   * Returns: Vout, current, power metrics
   */
  simulateInverter(vin, params = {}) {
    const wl_n = params.wl_n || 1;
    const wl_p = params.wl_p || params.wl_n ? params.wl_n * 2 : 2; // Typically 2x for PMOS

    // DC operating point
    let vout = this.vdd / 2; // Initial guess
    const iterations = 10;
    
    // Iterative solution for Vout
    for (let i = 0; i < iterations; i++) {
      const vgs_n = vin;
      const vds_n = vout;
      const vsg_p = this.vdd - vin;
      const vds_p = this.vdd - vout;

      const id_n = this.nmos.drainCurrent(vgs_n, vds_n, wl_n);
      const id_p = this.pmos.drainCurrent(vsg_p, vds_p, wl_p);

      // Current mismatch
      const delta = id_n - id_p;
      if (Math.abs(delta) < 1e-12) break;

      // Adjust Vout
      const gm_n = this.nmos.transconductance(vgs_n, wl_n);
      const gm_p = this.pmos.transconductance(vsg_p, wl_p);
      vout -= delta / (gm_n + gm_p);
      vout = Math.max(0, Math.min(this.vdd, vout));
    }

    // Calculate metrics
    const vgs_n = vin;
    const vds_n = vout;
    const vsg_p = this.vdd - vin;
    const vds_p = this.vdd - vout;

    const id_n = this.nmos.drainCurrent(vgs_n, vds_n, wl_n);
    const id_p = this.pmos.drainCurrent(vsg_p, vds_p, wl_p);
    const id_total = (Math.abs(id_n) + Math.abs(id_p)) / 2;

    // Gain (small-signal)
    const gm_n = this.nmos.transconductance(vgs_n, wl_n);
    const gm_p = this.pmos.transconductance(vsg_p, wl_p);
    const ro_n = this.nmos.outputImpedance(id_n);
    const ro_p = this.pmos.outputImpedance(id_p);
    const ro_total = (ro_n * ro_p) / (ro_n + ro_p);
    const rl_eff = (this.loadResistance * ro_total) / (this.loadResistance + ro_total);
    const av = -gm_n * rl_eff; // Voltage gain

    // Static power
    const p_static = id_total * this.vdd;

    return {
      vout,
      gain: av,
      current: id_total,
      powerStatic: p_static,
      gm: gm_n,
      ro: ro_total,
      vth_n: this.nmos.vth,
    };
  }

  /**
   * Delay calculation using RC model
   * τ = RC (simple model)
   * More realistic: accounts for ramp
   */
  calculateDelay(riseTime = 100e-12, input) {
    const r_eff = this.nmos.rd + this.pmos.rd;
    const tau = r_eff * this.loadCapacitance;
    
    // Rise/fall time = 2.2 * τ (63%)
    const t_delay = 0.69 * tau; // 50% point
    
    return {
      delay: t_delay,
      tau,
      riseTime: 2.2 * tau,
      fallTime: 2.2 * tau,
    };
  }

  /**
   * Power consumption breakdown
   */
  calculatePower(frequency, dutyCycle = 0.5) {
    // Static power (leakage)
    const p_static = 10e-9; // 10 nW baseline

    // Dynamic power = 0.5 * CL * VDD² * f
    const p_dynamic = 0.5 * this.loadCapacitance * Math.pow(this.vdd, 2) * frequency;

    // Short-circuit power (simplified)
    const p_shortcircuit = 0.1 * p_dynamic;

    // Total power
    const p_total = p_static + p_dynamic + p_shortcircuit;

    // Energy per cycle
    const energy = p_total / frequency;

    return {
      staticPower: p_static,
      dynamicPower: p_dynamic,
      shortcircuitPower: p_shortcircuit,
      totalPower: p_total,
      energyPerCycle: energy,
    };
  }

  /**
   * Simulate logic gate (inverter or buffer)
   */
  simulateLogicGate(logicType = 'inverter', inputs = [0.6]) {
    // For inverter, single input
    const vin = inputs[0] || 0;
    
    let output;
    if (logicType === 'inverter') {
      output = this.simulateInverter(vin, {});
    } else if (logicType === 'buffer') {
      // Two inverters cascaded
      const inv1 = this.simulateInverter(vin, {});
      output = this.simulateInverter(inv1.vout, {});
      output.delay *= 2; // Approximate
    } else if (logicType === 'nand') {
      // Simplified NAND
      const allHigh = inputs.every(i => i > 0.6);
      output = this.simulateInverter(allHigh ? 0 : this.vdd, {});
    } else if (logicType === 'nor') {
      // Simplified NOR
      const anyHigh = inputs.some(i => i > 0.6);
      output = this.simulateInverter(anyHigh ? this.vdd : 0, {});
    }

    return output;
  }

  /**
   * Ring oscillator frequency estimation
   * f = 1 / (2 * N * tpd) where N = number of stages
   */
  estimateRingOscillatorFreq(stages = 5) {
    const delayPerStage = this.calculateDelay().delay;
    const frequency = 1 / (2 * stages * delayPerStage);
    return frequency;
  }

  /**
   * NBTI (Negative Bias Temperature Instability) aging simulation
   * ΔVth ∝ t^n * exp(Ea / kT)
   * Simplified model: degradation increases with time, temp, voltage stress
   */
  simulateAging(operatingHoursPerDay = 24, operatingDaysPerYear = 365, years = 10) {
    // NBTI parameters
    const Ea = 0.1; // Activation energy (eV)
    const k = 8.617e-5; // Boltzmann constant (eV/K)
    const T = this.temp + 273.15; // Temperature (K)
    
    const stressExp = Math.exp(-Ea / (k * T));
    const totalHours = operatingHoursPerDay * operatingDaysPerYear * years;
    
    // NBTI degradation: ΔVth approximately proportional to time^0.25
    const timeExponent = 0.25;
    const nBTI = 0.001 * Math.pow(totalHours, timeExponent) * stressExp; // 1 mV baseline
    
    // HCI (Hot Carrier Injection)
    const hCI = 0.0005 * Math.pow(totalHours, 0.1); // 0.5 mV baseline
    
    // Total degradation
    const totalDegradation = nBTI + hCI;
    
    // Health score (100% = fresh, lower = aged)
    const healthScore = Math.max(0, 100 - (totalDegradation * 100 / 0.1));
    
    return {
      nBTI,
      hCI,
      totalDegradation,
      healthScore,
      vthDegradation: totalDegradation,
      frequencyDegradation: totalDegradation / this.nmos.vth * 30, // ~30% freq drop per mV Vth
    };
  }

  /**
   * Combined simulation with aging effects
   */
  simulateWithAging(params) {
    const baselineMetrics = this.simulateLogicGate('inverter', [0.6]);
    const agingMetrics = this.simulateAging(
      params.hoursPerDay || 24,
      params.daysPerYear || 365,
      params.years || 10
    );

    // Frequency degradation
    const freq0 = this.estimateRingOscillatorFreq();
    const freqDegraded = freq0 * (1 - agingMetrics.frequencyDegradation / 100);

    // Power increase (degraded device is less efficient)
    const powerMetrics = this.calculatePower(freq0);
    const powerDegraded = powerMetrics.totalPower * (1 + agingMetrics.totalDegradation * 10);

    return {
      baseline: {
        gain: baselineMetrics.gain,
        frequency: freq0,
        power: powerMetrics.totalPower,
        vthMargin: this.vdd / 4,
      },
      degraded: {
        frequency: freqDegraded,
        power: powerDegraded,
        vthMargin: this.vdd / 4 - agingMetrics.totalDegradation,
        healthScore: agingMetrics.healthScore,
      },
      agingParameters: agingMetrics,
    };
  }
}

/**
 * Export for use in simulation jobs
 */
module.exports = {
  MOSFETModel,
  CircuitSimulator,

  /**
   * Quick simulate function
   */
  simulate(config) {
    const sim = new CircuitSimulator(config);
    
    // Test points
    const metrics = {
      vin0: sim.simulateLogicGate('inverter', [0.3]),
      vin_mid: sim.simulateLogicGate('inverter', [0.6]),
      vin1: sim.simulateLogicGate('inverter', [0.9]),
      delay: sim.calculateDelay(),
      power: sim.calculatePower(1e6), // 1 MHz
      frequency: sim.estimateRingOscillatorFreq(),
      aging: sim.simulateAging()
    };

    // Combined result
    return {
      success: true,
      timestamp: new Date().toISOString(),
      circuit: config,
      metrics,
      summary: {
        estimatedGain: Math.abs(metrics.vin_mid.gain).toFixed(2),
        estimatedFrequency: (metrics.frequency / 1e6).toFixed(2) + ' MHz',
        estimatedPower: (metrics.power.totalPower * 1e9).toFixed(2) + ' nW',
        healthAfter10Y: metrics.aging.healthScore.toFixed(1) + '%',
      }
    };
  }
};
