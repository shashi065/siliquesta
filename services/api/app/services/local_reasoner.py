"""Deterministic local engineering reasoning for SILIQUESTA AI."""

from __future__ import annotations

from dataclasses import dataclass
import re

from app.services.cmos_engine import CMOSPhysicsEngine, ProcessCorner
from app.services.digital_twin_ml import DigitalTwinSurrogateService


@dataclass
class LocalReasoningResult:
    answer: str
    confidence: float
    route: str


class LocalReasoner:
    def __init__(self):
        self.twin = DigitalTwinSurrogateService()

    def can_answer_directly(self, message: str, context: dict) -> bool:
        msg = message.lower().strip()
        tokens = self._tokens(msg)
        direct_terms = (
            "hi",
            "hello",
            "hey",
            "who are you",
            "what is the current",
            "summary",
            "power",
            "frequency",
            "delay",
            "tradeoff",
            "pvt",
            "corner",
            "optimize",
            "optimization",
            "recommend",
            "voltage",
            "width",
            "wp/wn",
            "ratio",
            "spice",
            "netlist",
            "verilog",
            "rtl",
            "aging",
            "reliability",
            "predict",
            "forecast",
        )
        if any(term in msg for term in direct_terms):
            return True
        if tokens & {"ss", "tt", "ff", "sf", "fs", "pvt"}:
            return True
        if len(msg.split()) <= 8 and any(word in msg for word in ("freq", "power", "delay", "vdd", "wn", "wp")):
            return True
        return False

    def answer(self, message: str, context: dict) -> LocalReasoningResult:
        msg = message.lower().strip()
        tokens = self._tokens(msg)
        if msg in {"hi", "hello", "hey", "yo"}:
            return LocalReasoningResult(
                answer=(
                    "Hi. I’m SILIQUESTA AI. Ask me about simulation, SPICE behavior, PVT corners, "
                    "power-delay tradeoffs, reliability, or optimization."
                ),
                confidence=0.99,
                route="local-engine:greeting",
            )

        metrics = self._current_metrics(context)
        if any(term in msg for term in ("predict", "forecast", "future")):
            return self._predictive_answer(context, metrics)
        if any(term in msg for term in ("spice", "netlist")):
            return self._spice_answer(metrics)
        if any(term in msg for term in ("verilog", "rtl", "synthes")):
            return self._rtl_answer(metrics)
        if any(term in msg for term in ("tradeoff", "power delay", "delay power", "energy", "fom")):
            return self._tradeoff_answer(context, metrics)
        if any(term in msg for term in ("optimize", "optimization", "recommend", "improve")):
            return self._optimization_answer(context, metrics)
        if any(term in msg for term in ("aging", "reliability", "nbti", "hci", "electromigration")):
            return self._reliability_answer(context, metrics)
        if "corner" in msg or tokens & {"pvt", "ss", "tt", "ff", "sf", "fs"}:
            return self._pvt_answer(context, metrics)
        return self._summary_answer(context, metrics)

    def _tokens(self, message: str) -> set[str]:
        return {token for token in re.split(r"[^a-z0-9_]+", message.lower()) if token}

    def _corner(self, corner: str | None) -> ProcessCorner:
        if not corner:
            return ProcessCorner.TT
        return ProcessCorner.__members__.get(str(corner).upper(), ProcessCorner.TT)

    def _current_metrics(self, context: dict) -> dict:
        wn = float(context.get("wn", 0.5))
        wp = float(context.get("wp", 1.0))
        vdd = float(context.get("vdd", 1.2))
        temp = float(context.get("temp", 27))
        cl_ff = float(context.get("cl_ff", context.get("cl", 10)))
        tech_node = float(context.get("tech_node", 28))
        corner = self._corner(context.get("corner", "TT"))
        physics = CMOSPhysicsEngine.compute(
            wn=wn,
            wp=wp,
            vdd=vdd,
            temp=temp,
            cl_ff=cl_ff,
            corner=corner,
            tech_node=tech_node,
        )
        return {
            "wn": wn,
            "wp": wp,
            "vdd": vdd,
            "temp": temp,
            "cl_ff": cl_ff,
            "tech_node": tech_node,
            "corner": corner.value,
            "freq": float(context.get("freq", physics.freq)),
            "power": float(context.get("power", physics.power)),
            "delay": float(context.get("delay", physics.delay)),
            "fom": float(context.get("fom", physics.fom)),
            "ratio": wp / max(wn, 1e-9),
        }

    def _summary_answer(self, context: dict, m: dict) -> LocalReasoningResult:
        return LocalReasoningResult(
            answer=(
                f"Current operating point: {m['corner']} at {m['tech_node']}nm, "
                f"WN={m['wn']:.2f}um, WP={m['wp']:.2f}um, VDD={m['vdd']:.2f}V, Temp={m['temp']:.0f}C. "
                f"Estimated frequency is {m['freq']:.4f} GHz, power is {m['power']:.4f} mW, and delay is {m['delay']:.4f} ps. "
                f"WP/WN ratio is {m['ratio']:.2f}, so {'pull-up is reasonably balanced' if 1.8 <= m['ratio'] <= 2.6 else 'the inverter is not ideally balanced yet'}."
            ),
            confidence=0.90,
            route="local-engine:summary",
        )

    def _spice_answer(self, m: dict) -> LocalReasoningResult:
        l_um = max(m["tech_node"] / 1000.0, 0.0003)
        answer = (
            "Local SPICE starter for the current inverter:\n"
            f".param VDD={m['vdd']:.3f}\n"
            f"VDD vdd 0 {{VDD}}\n"
            "VIN in 0 PULSE(0 {VDD} 200p 20p 20p 10n 20n)\n"
            f"CL out 0 {m['cl_ff']:.3f}e-15\n"
            f"M1 out in 0 0 nmos W={m['wn']:.4f}e-6 L={l_um:.6f}e-6\n"
            f"M2 out in vdd vdd pmos W={m['wp']:.4f}e-6 L={l_um:.6f}e-6\n"
            ".tran 10p 40n\n"
            ".end\n\n"
            f"Use {m['corner']} as the first corner, then verify SS and FF before trusting timing margin."
        )
        return LocalReasoningResult(answer=answer, confidence=0.93, route="local-engine:spice")

    def _rtl_answer(self, m: dict) -> LocalReasoningResult:
        answer = (
            "Synthesizable RTL starter:\n"
            "module siliquesta_inv_wrapper (\n"
            "  input  wire in,\n"
            "  output wire out\n"
            ");\n"
            "  assign out = ~in;\n"
            "endmodule\n\n"
            f"This is a logical wrapper only. For the current {m['tech_node']}nm device-level point, "
            "keep RTL separate from transistor sizing and validate implementation timing after synthesis."
        )
        return LocalReasoningResult(answer=answer, confidence=0.84, route="local-engine:rtl")

    def _optimization_answer(self, context: dict, m: dict) -> LocalReasoningResult:
        base_corner = self._corner(m["corner"])
        drive_up = CMOSPhysicsEngine.compute(m["wn"] * 1.15, m["wp"] * 1.15, m["vdd"], m["temp"], m["cl_ff"], base_corner, m["tech_node"])
        lower_v = CMOSPhysicsEngine.compute(m["wn"], m["wp"], max(0.5, m["vdd"] * 0.9), m["temp"], m["cl_ff"], base_corner, m["tech_node"])
        rebalance_wp = max(m["wn"] * 2.1, 0.1)
        rebalance = CMOSPhysicsEngine.compute(m["wn"], rebalance_wp, m["vdd"], m["temp"], m["cl_ff"], base_corner, m["tech_node"])
        answer = (
            f"Best immediate levers from the current point: "
            f"1) Upsize both devices by 15% to about {drive_up.freq:.4f} GHz at {drive_up.power:.4f} mW and {drive_up.delay:.4f} ps. "
            f"2) Lower VDD to {max(0.5, m['vdd'] * 0.9):.2f}V to cut power toward {lower_v.power:.4f} mW, but frequency drops to {lower_v.freq:.4f} GHz. "
            f"3) Rebalance PMOS toward WP={rebalance_wp:.2f}um for a WP/WN ratio near 2.1, which predicts {rebalance.freq:.4f} GHz and {rebalance.delay:.4f} ps. "
            f"If your goal is performance, take option 1. If your goal is energy, take option 2."
        )
        return LocalReasoningResult(answer=answer, confidence=0.88, route="local-engine:optimize")

    def _tradeoff_answer(self, context: dict, m: dict) -> LocalReasoningResult:
        base_corner = self._corner(m["corner"])
        fast_bias = CMOSPhysicsEngine.compute(m["wn"] * 1.2, m["wp"] * 1.2, min(m["vdd"] * 1.05, 3.3), m["temp"], m["cl_ff"], base_corner, m["tech_node"])
        lean_bias = CMOSPhysicsEngine.compute(m["wn"], m["wp"], max(0.5, m["vdd"] * 0.92), m["temp"], m["cl_ff"], base_corner, m["tech_node"])
        answer = (
            f"Current tradeoff point is {m['freq']:.4f} GHz at {m['power']:.4f} mW with {m['delay']:.4f} ps delay. "
            f"If you bias for speed, a modest upsize and slight VDD increase moves toward {fast_bias.freq:.4f} GHz but power rises to {fast_bias.power:.4f} mW. "
            f"If you bias for efficiency, trimming VDD moves power toward {lean_bias.power:.4f} mW but frequency drops to {lean_bias.freq:.4f} GHz. "
            f"So the present point is a middle operating point, not the max-speed or min-energy extreme."
        )
        return LocalReasoningResult(answer=answer, confidence=0.89, route="local-engine:tradeoff")

    def _pvt_answer(self, context: dict, m: dict) -> LocalReasoningResult:
        corners = {}
        for c in ("SS", "TT", "FF"):
            result = CMOSPhysicsEngine.compute(m["wn"], m["wp"], m["vdd"], m["temp"], m["cl_ff"], self._corner(c), m["tech_node"])
            corners[c] = result
        return LocalReasoningResult(
            answer=(
                f"Corner view at VDD={m['vdd']:.2f}V and Temp={m['temp']:.0f}C: "
                f"SS gives {corners['SS'].freq:.4f} GHz / {corners['SS'].delay:.4f} ps, "
                f"TT gives {corners['TT'].freq:.4f} GHz / {corners['TT'].delay:.4f} ps, "
                f"and FF gives {corners['FF'].freq:.4f} GHz / {corners['FF'].delay:.4f} ps. "
                f"That means SS is your timing guardband corner and FF is your fastest, leakage-prone corner."
            ),
            confidence=0.87,
            route="local-engine:pvt",
        )

    def _reliability_answer(self, context: dict, m: dict) -> LocalReasoningResult:
        prediction = self.twin.predict(
            wn=m["wn"],
            wp=m["wp"],
            vdd=m["vdd"],
            temp=m["temp"],
            cl_ff=m["cl_ff"],
            tech_node=m["tech_node"],
            corner=m["corner"],
        )
        return LocalReasoningResult(
            answer=(
                f"Digital-twin estimate for this point: {prediction.freq_ghz:.4f} GHz, "
                f"{prediction.power_mw:.4f} mW, {prediction.delay_ps:.4f} ps with model confidence {prediction.confidence:.2f}. "
                f"Reliability risk rises most from VDD={m['vdd']:.2f}V and Temp={m['temp']:.0f}C together, so the safest mitigation is either lowering voltage or reducing thermal load before widening devices further."
            ),
            confidence=max(0.75, prediction.confidence),
            route="digital-twin:reliability",
        )

    def _predictive_answer(self, context: dict, m: dict) -> LocalReasoningResult:
        prediction = self.twin.predict(
            wn=m["wn"],
            wp=m["wp"],
            vdd=m["vdd"],
            temp=m["temp"],
            cl_ff=m["cl_ff"],
            tech_node=m["tech_node"],
            corner=m["corner"],
        )
        return LocalReasoningResult(
            answer=(
                f"Predicted operating point from the trained Digital Twin: "
                f"{prediction.freq_ghz:.4f} GHz, {prediction.power_mw:.4f} mW, {prediction.delay_ps:.4f} ps. "
                f"Estimated model error is about {prediction.estimated_error_percent:.2f}%, so use it for fast design guidance and confirm critical decisions with SPICE."
            ),
            confidence=max(0.72, prediction.confidence),
            route="digital-twin:predict",
        )
