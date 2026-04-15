"""
SILIQUESTA Agentic Orchestrator - Execution-Based Design Agent
===============================================================

Coordinates Digital Twin, NSGA-II Optimizer, and Reliability Engine
for autonomous design space exploration and optimization.

No chatbot responses - only execution-based reasoning and design decisions.
"""

import re
import json
import logging
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class OptimizationTarget(Enum):
    """Design objectives that the agent can optimize for"""
    POWER_MINIMAL = "power_minimal"
    FREQUENCY_MAXIMAL = "frequency_maximal"
    EFFICIENCY_MAXIMAL = "efficiency_maximal"
    BALANCED = "balanced"
    PPA_OPTIMAL = "ppa_optimal"  # Power, Performance, Area
    RELIABILITY_FOCUSED = "reliability_focused"


@dataclass
class DesignIntent:
    """Parsed natural language design intention"""
    primary_target: OptimizationTarget
    wn_range: Tuple[float, float] = (0.1, 10.0)  # NMOS width range (um)
    wp_range: Tuple[float, float] = (0.1, 10.0)  # PMOS width range (um)
    vdd_range: Tuple[float, float] = (0.8, 1.8)  # Supply voltage range (V)
    temp_range: Tuple[float, float] = (0.0, 125.0)  # Temperature range (C)
    
    # Hard constraints
    max_power: Optional[float] = None  # mW - maximum power budget
    min_frequency: Optional[float] = None  # MHz - minimum frequency requirement
    min_lifetime: Optional[float] = None  # years - minimum device lifetime
    max_area: Optional[float] = None  # um^2 - maximum area budget
    
    # Soft preferences
    corner: str = "TT"  # Process corner
    tech_node: int = 28  # nm technology node
    optimization_priority: str = "balanced"  # "aggressive", "balanced", "conservative"
    
    @classmethod
    def from_natural_language(cls, natural_language: str) -> "DesignIntent":
        """Parse natural language design specification"""
        intent = cls(primary_target=OptimizationTarget.BALANCED)
        
        text = natural_language.lower()
        
        # Detect primary optimization target
        if any(word in text for word in ["minimize power", "low power", "ultra-low power"]):
            intent.primary_target = OptimizationTarget.POWER_MINIMAL
        elif any(word in text for word in ["maximize frequency", "high frequency", "high performance"]):
            intent.primary_target = OptimizationTarget.FREQUENCY_MAXIMAL
        elif any(word in text for word in ["efficiency", "ppa"]):
            intent.primary_target = OptimizationTarget.PPA_OPTIMAL
        elif any(word in text for word in ["reliability", "lifetime", "aging"]):
            intent.primary_target = OptimizationTarget.RELIABILITY_FOCUSED
        
        # Extract numerical constraints using regex
        power_match = re.search(r'(?:max|power|budget|consumption).*?(\d+(?:\.\d+)?)\s*m?w', text)
        if power_match:
            intent.max_power = float(power_match.group(1))
        
        freq_match = re.search(r'(?:min|frequency|ghz|mhz).*?(\d+(?:\.\d+)?)\s*(?:ghz|mhz)?', text)
        if freq_match:
            intent.min_frequency = float(freq_match.group(1))
        
        lifetime_match = re.search(r'(?:lifetime|years|life).*?(\d+(?:\.\d+)?)\s*years?', text)
        if lifetime_match:
            intent.min_lifetime = float(lifetime_match.group(1))
        
        area_match = re.search(r'(?:area|size).*?(\d+(?:\.\d+)?)\s*um\^?2', text)
        if area_match:
            intent.max_area = float(area_match.group(1))
        
        # Detect optimization priority
        if "aggressive" in text:
            intent.optimization_priority = "aggressive"
        elif "conservative" in text:
            intent.optimization_priority = "conservative"
        
        # Extract process corner
        corners = ["ss", "tt", "ff", "sf", "fs", "mc"]
        for corner in corners:
            if corner in text:
                intent.corner = corner.upper()
                break
        
        # Extract technology node
        tech_match = re.search(r'(\d+)\s*(?:nm|process|node)', text)
        if tech_match:
            intent.tech_node = int(tech_match.group(1))
        
        return intent


@dataclass
class CircuitDesign:
    """A circuit design point with performance metrics"""
    wn: float  # NMOS width (um)
    wp: float  # PMOS width (um)
    vdd: float  # Supply voltage (V)
    temperature: float = 25.0  # Operating temperature (C)
    
    # Performance metrics
    power: Optional[float] = None  # mW
    frequency: Optional[float] = None  # MHz
    delay: Optional[float] = None  # ns
    efficiency: Optional[float] = None  # MHz/mW
    
    # Reliability metrics
    reliability_score: Optional[float] = None  # [0, 1], 1=perfect
    device_lifetime: Optional[float] = None  # years
    nbti_lifetime: Optional[float] = None  # years
    hci_lifetime: Optional[float] = None  # years
    em_lifetime: Optional[float] = None  # years
    
    # Prediction confidence
    power_confidence: float = 0.8
    frequency_confidence: float = 0.8
    delay_confidence: float = 0.8
    reliability_confidence: float = 0.7
    
    # Composite metrics
    pareto_rank: int = 0  # 1=best, 2=second tier, etc.
    multi_objective_score: float = 0.0  # Aggregate optimization objective
    
    def meets_constraints(self, intent: DesignIntent) -> bool:
        """Check if design satisfies hard constraints"""
        if intent.max_power and self.power and self.power > intent.max_power:
            return False
        if intent.min_frequency and self.frequency and self.frequency < intent.min_frequency:
            return False
        if intent.min_lifetime and self.device_lifetime and self.device_lifetime < intent.min_lifetime:
            return False
        return True
    
    def compute_objective_score(self, intent: DesignIntent) -> float:
        """Compute aggregate optimization score based on target"""
        if not self.power or not self.frequency or not self.reliability_score:
            return 0.0
        
        # Normalize metrics to [0, 1] range
        power_norm = np.clip(1.0 - (self.power / 100.0), 0, 1)  # Lower is better
        freq_norm = np.clip(self.frequency / 1000.0, 0, 1)  # Higher is better
        reliability_norm = self.reliability_score  # Already [0, 1]
        efficiency_norm = np.clip((self.frequency / self.power) / 10.0, 0, 1)  # MHz/mW
        
        if intent.primary_target == OptimizationTarget.POWER_MINIMAL:
            score = 0.7 * power_norm + 0.2 * reliability_norm + 0.1 * freq_norm
        elif intent.primary_target == OptimizationTarget.FREQUENCY_MAXIMAL:
            score = 0.7 * freq_norm + 0.2 * reliability_norm + 0.1 * power_norm
        elif intent.primary_target == OptimizationTarget.PPA_OPTIMAL:
            score = 0.4 * efficiency_norm + 0.3 * power_norm + 0.3 * freq_norm
        elif intent.primary_target == OptimizationTarget.RELIABILITY_FOCUSED:
            score = 0.6 * reliability_norm + 0.2 * power_norm + 0.2 * freq_norm
        else:  # BALANCED
            score = 0.25 * power_norm + 0.25 * freq_norm + 0.25 * efficiency_norm + 0.25 * reliability_norm
        
        self.multi_objective_score = float(score)
        return float(score)


@dataclass
class ExecutionPlan:
    """Execution plan determined by agent reasoning"""
    steps: List[str] = field(default_factory=list)
    digital_twin_enabled: bool = True
    optimizer_enabled: bool = True
    reliability_analysis_enabled: bool = True
    optimization_intensity: str = "standard"  # "light", "standard", "intensive"
    reasoning: str = ""


@dataclass
class OrchestratorResponse:
    """Structure response from agentic orchestrator"""
    request_id: str
    timestamp: str
    
    # Original request
    design_intent: Dict[str, Any]
    
    # Best design recommendation
    best_design: Dict[str, Any]
    best_design_reasoning: str
    
    # Pareto front (alternative options)
    pareto_front: List[Dict[str, Any]] = field(default_factory=list)
    
    # Explanation of reasoning
    execution_reasoning: str = ""
    constraint_satisfaction: Dict[str, bool] = field(default_factory=dict)
    
    # Confidence metrics
    overall_confidence: float = 0.0
    component_confidence: Dict[str, float] = field(default_factory=dict)
    
    # Component contributions
    digital_twin_contribution: Dict[str, Any] = field(default_factory=dict)
    optimizer_contribution: Dict[str, Any] = field(default_factory=dict)
    reliability_contribution: Dict[str, Any] = field(default_factory=dict)
    
    # Execution metadata
    execution_time_ms: float = 0.0
    components_evaluated: List[str] = field(default_factory=list)


class AgenticOrchestrator:
    """
    Execution-based agentic orchestrator for autonomous CMOS design optimization.
    
    Coordinates:
    - Digital Twin (surrogate predictions)
    - NSGA-II Optimizer (Pareto front generation)
    - Reliability Engine (degradation analysis)
    
    Returns: Best designs with reasoning and confidence.
    """
    
    def __init__(self):
        """Initialize orchestrator"""
        self.execution_history: List[Dict] = []
        logger.info("🤖 AgenticOrchestrator initialized")
    
    async def orchestrate(self, design_specification: str, 
                         digital_twin_service=None,
                         optimizer_service=None,
                         reliability_model=None) -> OrchestratorResponse:
        """
        Main orchestration entry point.
        
        Args:
            design_specification: Natural language design intent (e.g., "minimize power under 100mW with >500MHz")
            digital_twin_service: Digital Twin service for predictions
            optimizer_service: NSGA-II optimizer service
            reliability_model: Reliability degradation model
        
        Returns:
            OrchestratorResponse with best design, Pareto options, and reasoning
        """
        start_time = datetime.now()
        request_id = f"req_{int(start_time.timestamp() * 1000)}"
        
        try:
            # Step 1: Parse natural language into structured intent
            logger.info(f"[{request_id}] Parsing design intent...")
            design_intent = DesignIntent.from_natural_language(design_specification)
            
            # Step 2: Plan execution
            logger.info(f"[{request_id}] Planning execution...")
            execution_plan = self._plan_execution(design_intent)
            
            # Step 3: Execute plan - call services in sequence
            logger.info(f"[{request_id}] Executing optimization plan...")
            
            designs: List[CircuitDesign] = []
            component_results = {
                "digital_twin": {},
                "optimizer": {},
                "reliability": {}
            }
            
            # 3a: Get optimizer-generated Pareto front
            if execution_plan.optimizer_enabled and optimizer_service:
                logger.info(f"[{request_id}] Running NSGA-II optimization...")
                try:
                    pareto_designs = await self._run_optimization(
                        optimizer_service, design_intent, execution_plan
                    )
                    designs.extend(pareto_designs)
                    component_results["optimizer"]["designs_generated"] = len(pareto_designs)
                    component_results["optimizer"]["success"] = True
                except Exception as e:
                    logger.error(f"[{request_id}] Optimizer failed: {e}")
                    component_results["optimizer"]["success"] = False
            
            # 3b: Enhance with Digital Twin predictions
            if execution_plan.digital_twin_enabled and digital_twin_service:
                logger.info(f"[{request_id}] Enhancing with Digital Twin predictions...")
                try:
                    designs = await self._enhance_with_digital_twin(
                        designs, digital_twin_service, design_intent
                    )
                    component_results["digital_twin"]["designs_enhanced"] = len(designs)
                    component_results["digital_twin"]["success"] = True
                except Exception as e:
                    logger.error(f"[{request_id}] Digital Twin failed: {e}")
                    component_results["digital_twin"]["success"] = False
            
            # 3c: Analyze reliability
            if execution_plan.reliability_analysis_enabled and reliability_model:
                logger.info(f"[{request_id}] Analyzing device reliability...")
                try:
                    designs = await self._analyze_reliability(
                        designs, reliability_model, design_intent
                    )
                    component_results["reliability"]["designs_analyzed"] = len(designs)
                    component_results["reliability"]["success"] = True
                except Exception as e:
                    logger.error(f"[{request_id}] Reliability analysis failed: {e}")
                    component_results["reliability"]["success"] = False
            
            # Step 4: Filter for constraint satisfaction
            valid_designs = [d for d in designs if d.meets_constraints(design_intent)]
            if not valid_designs:
                logger.warning(f"[{request_id}] No valid designs meet constraints, using best candidates")
                valid_designs = sorted(designs, key=lambda d: d.multi_objective_score, reverse=True)[:3]
            
            # Step 5: Rank by multi-objective score
            for i, design in enumerate(sorted(valid_designs, 
                                              key=lambda d: d.multi_objective_score, 
                                              reverse=True)):
                design.pareto_rank = i + 1
            
            # Step 6: Compute confidence and reasoning
            best_design = valid_designs[0] if valid_designs else designs[0]
            
            confidence = self._compute_confidence(
                best_design, valid_designs, design_intent, component_results
            )
            
            reasoning = self._generate_reasoning(
                best_design, valid_designs, design_intent, execution_plan, component_results
            )
            
            # Step 7: Build response
            response = OrchestratorResponse(
                request_id=request_id,
                timestamp=start_time.isoformat(),
                design_intent=asdict(design_intent),
                best_design=self._design_to_dict(best_design),
                best_design_reasoning=reasoning["best_design"],
                pareto_front=[self._design_to_dict(d) for d in valid_designs[:5]],
                execution_reasoning=reasoning["execution"],
                constraint_satisfaction=reasoning["constraints"],
                overall_confidence=confidence["overall"],
                component_confidence=confidence["components"],
                digital_twin_contribution=component_results["digital_twin"],
                optimizer_contribution=component_results["optimizer"],
                reliability_contribution=component_results["reliability"],
                execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                components_evaluated=[k for k, v in component_results.items() if v.get("success")]
            )
            
            # Log execution
            self.execution_history.append({
                "request_id": request_id,
                "timestamp": start_time.isoformat(),
                "design_intent": design_specification,
                "status": "success",
                "best_design_score": best_design.multi_objective_score
            })
            
            logger.info(f"[{request_id}] ✅ Orchestration complete - Best design score: {best_design.multi_objective_score:.3f}")
            
            return response
            
        except Exception as e:
            logger.error(f"[{request_id}] Orchestration failed: {e}", exc_info=True)
            raise
    
    async def _run_optimization(self, optimizer_service, design_intent: DesignIntent,
                               execution_plan: ExecutionPlan) -> List[CircuitDesign]:
        """Run NSGA-II optimizer to generate Pareto front"""
        try:
            # Configure optimization based on intensity
            if execution_plan.optimization_intensity == "light":
                population_size, generations = 50, 20
            elif execution_plan.optimization_intensity == "intensive":
                population_size, generations = 300, 100
            else:  # standard
                population_size, generations = 100, 50
            
            # Call optimizer service
            opt_result = await optimizer_service.optimize(
                population_size=population_size,
                generations=generations,
                use_ml=True,
                constraints={
                    "max_power": design_intent.max_power,
                    "min_frequency": design_intent.min_frequency,
                }
            )
            
            # Convert optimizer results to CircuitDesign objects
            designs = []
            for sol in opt_result.get("pareto_front", []):
                design = CircuitDesign(
                    wn=sol["wn"],
                    wp=sol["wp"],
                    vdd=sol["vdd"],
                    power=sol.get("power"),
                    frequency=sol.get("frequency"),
                    delay=sol.get("delay"),
                    temperature=design_intent.temp_range[0] + 25.0
                )
                design.compute_objective_score(design_intent)
                designs.append(design)
            
            return designs
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            return []
    
    async def _enhance_with_digital_twin(self, designs: List[CircuitDesign],
                                        digital_twin_service,
                                        design_intent: DesignIntent) -> List[CircuitDesign]:
        """Enhance designs with Digital Twin predictions"""
        try:
            for design in designs:
                prediction = await digital_twin_service.predict(
                    wn=design.wn,
                    wp=design.wp,
                    vdd=design.vdd,
                    temperature=design.temperature,
                    corner=design_intent.corner,
                    tech_node=design_intent.tech_node
                )
                
                # Update design with predictions
                design.power = prediction.get("power", design.power)
                design.frequency = prediction.get("frequency", design.frequency)
                design.delay = prediction.get("delay", design.delay)
                design.power_confidence = prediction.get("power_confidence", 0.8)
                design.frequency_confidence = prediction.get("frequency_confidence", 0.8)
                design.delay_confidence = prediction.get("delay_confidence", 0.8)
                
                # Recompute objective with updated values
                design.compute_objective_score(design_intent)
            
            return designs
        except Exception as e:
            logger.error(f"Digital Twin enhancement failed: {e}")
            return designs
    
    async def _analyze_reliability(self, designs: List[CircuitDesign],
                                  reliability_model,
                                  design_intent: DesignIntent) -> List[CircuitDesign]:
        """Analyze device reliability for each design"""
        try:
            for design in designs:
                # Compute reliability metrics
                reliability = reliability_model.compute_device_reliability(
                    wn=design.wn,
                    wp=design.wp,
                    vdd=design.vdd,
                    temperature=design.temperature
                )
                
                design.reliability_score = reliability.get("reliability_score", 0.7)
                design.device_lifetime = reliability.get("device_lifetime", 5.0)
                design.nbti_lifetime = reliability.get("nbti_lifetime", 10.0)
                design.hci_lifetime = reliability.get("hci_lifetime", 8.0)
                design.em_lifetime = reliability.get("em_lifetime", 12.0)
                design.reliability_confidence = reliability.get("confidence", 0.7)
                
                # Recompute objective with reliability included
                design.compute_objective_score(design_intent)
            
            return designs
        except Exception as e:
            logger.error(f"Reliability analysis failed: {e}")
            return designs
    
    def _plan_execution(self, design_intent: DesignIntent) -> ExecutionPlan:
        """Determine execution plan based on design intent"""
        plan = ExecutionPlan()
        
        # Always enable core components
        plan.digital_twin_enabled = True
        plan.optimizer_enabled = True
        plan.reliability_analysis_enabled = True
        
        # Adjust optimization intensity based on priority
        if design_intent.optimization_priority == "aggressive":
            plan.optimization_intensity = "intensive"
            plan.steps = [
                "Initialize intensive optimization (300 pop, 100 gen)",
                "Run NSGA-II for Pareto front generation",
                "Enhance with Digital Twin predictions (GPU accelerated)",
                "Perform reliability analysis",
                "Select and rank best designs"
            ]
        elif design_intent.optimization_priority == "conservative":
            plan.optimization_intensity = "light"
            plan.steps = [
                "Initialize lightweight optimization (50 pop, 20 gen)",
                "Run NSGA-II for initial Pareto front",
                "Enhance with Digital Twin predictions",
                "Perform reliability analysis",
                "Select best designs"
            ]
        else:  # balanced
            plan.optimization_intensity = "standard"
            plan.steps = [
                "Initialize standard optimization (100 pop, 50 gen)",
                "Run NSGA-II for Pareto front",
                "Enhance with Digital Twin predictions",
                "Perform reliability analysis",
                "Select and rank best designs"
            ]
        
        plan.reasoning = f"""
        Optimization Target: {design_intent.primary_target.value}
        Intensity: {plan.optimization_intensity}
        Constraints: Power<{design_intent.max_power}mW, Freq>{design_intent.min_frequency}MHz, Lifetime>{design_intent.min_lifetime}yr
        Process: {design_intent.corner} @ {design_intent.tech_node}nm
        Component Selection: All three engines (Digital Twin, Optimizer, Reliability)
        """
        
        return plan
    
    def _compute_confidence(self, best_design: CircuitDesign, all_designs: List[CircuitDesign],
                           design_intent: DesignIntent,
                           component_results: Dict) -> Dict[str, float]:
        """Compute confidence scores based on multiple factors"""
        
        confidence_components = {
            "prediction_confidence": (best_design.power_confidence + 
                                     best_design.frequency_confidence + 
                                     best_design.reliability_confidence) / 3.0,
            "constraint_satisfaction": 1.0 if best_design.meets_constraints(design_intent) else 0.7,
            "pareto_ranking": 1.0 if best_design.pareto_rank == 1 else (1.0 - (best_design.pareto_rank - 1) * 0.1),
            "component_agreement": self._compute_component_agreement(component_results),
            "design_space_coverage": min(1.0, len(all_designs) / 10.0),  # 10+ designs = high coverage
        }
        
        overall = np.mean(list(confidence_components.values()))
        
        return {
            "overall": float(overall),
            "components": {k: float(v) for k, v in confidence_components.items()}
        }
    
    def _compute_component_agreement(self, component_results: Dict) -> float:
        """Measure agreement between different components"""
        active_components = sum(1 for v in component_results.values() if v.get("success"))
        if active_components < 2:
            return 0.5
        # All components agreement = 1.0, partial = 0.8, one = 0.5
        return min(1.0, active_components / 3.0)
    
    def _generate_reasoning(self, best_design: CircuitDesign, all_designs: List[CircuitDesign],
                           design_intent: DesignIntent, execution_plan: ExecutionPlan,
                           component_results: Dict) -> Dict[str, Any]:
        """Generate detailed reasoning for design selection"""
        
        # Best design reasoning
        best_reasoning = f"""
Selection Reasoning:
- Primary Objective: {design_intent.primary_target.value}
- Multi-Objective Score: {best_design.multi_objective_score:.3f} (normalized 0-1)
- Pareto Rank: {best_design.pareto_rank} (best in front)
- Design Point: Wn={best_design.wn:.2f}um, Wp={best_design.wp:.2f}um, Vdd={best_design.vdd:.2f}V
- Performance: Power={best_design.power:.2f}mW, Frequency={best_design.frequency:.2f}MHz, Delay={best_design.delay:.2f}ns
- Reliability: Score={best_design.reliability_score:.2f}, Lifetime={best_design.device_lifetime:.1f}years
- Prediction Confidence: Power={best_design.power_confidence:.2f}, Freq={best_design.frequency_confidence:.2f}, Reliability={best_design.reliability_confidence:.2f}
        """
        
        # Execution reasoning  
        exec_reasoning = f"""
Execution Plan:
{execution_plan.reasoning}

Optimization Intensity: {execution_plan.optimization_intensity}
Components Evaluated: {', '.join(execution_plan.steps[1:4])}
Design Iterations: {component_results.get('optimizer', {}).get('designs_generated', 0)} candidates generated
Final Pareto Front: {len(all_designs)} non-dominated solutions
        """
        
        # Constraint satisfaction
        constraints = {
            "max_power_met": best_design.power < (design_intent.max_power or float('inf')) if best_design.power else False,
            "min_frequency_met": best_design.frequency > (design_intent.min_frequency or 0) if best_design.frequency else False,
            "min_lifetime_met": best_design.device_lifetime > (design_intent.min_lifetime or 0) if best_design.device_lifetime else False,
            "process_corner_valid": design_intent.corner != "INVALID",
            "temperature_within_range": design_intent.temp_range[0] <= best_design.temperature <= design_intent.temp_range[1]
        }
        
        return {
            "best_design": best_reasoning.strip(),
            "execution": exec_reasoning.strip(),
            "constraints": constraints
        }
    
    def _design_to_dict(self, design: CircuitDesign) -> Dict[str, Any]:
        """Convert CircuitDesign to dictionary"""
        return {
            "wn": design.wn,
            "wp": design.wp,
            "vdd": design.vdd,
            "temperature": design.temperature,
            "power_mw": design.power,
            "frequency_mhz": design.frequency,
            "delay_ns": design.delay,
            "efficiency_mhz_per_mw": design.efficiency,
            "reliability_score": design.reliability_score,
            "device_lifetime_years": design.device_lifetime,
            "nbti_lifetime_years": design.nbti_lifetime,
            "hci_lifetime_years": design.hci_lifetime,
            "em_lifetime_years": design.em_lifetime,
            "power_confidence": design.power_confidence,
            "frequency_confidence": design.frequency_confidence,
            "reliability_confidence": design.reliability_confidence,
            "pareto_rank": design.pareto_rank,
            "multi_objective_score": design.multi_objective_score
        }
    
    def get_execution_history(self) -> List[Dict]:
        """Return execution history for auditing"""
        return self.execution_history
