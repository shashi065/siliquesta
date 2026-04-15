"""
SPICE-backed PVT analysis with memoized point evaluations.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import os
from typing import Dict, Iterable, List, Tuple

from app.services.spice_engine import SpiceEngine


class SpicePVTService:
    CORNERS = ["SS", "TT", "FF", "SF", "FS", "MC"]
    TEMPERATURES = [-40, 0, 27, 85, 125]
    STANDARD_VOLTAGES = [0.5, 0.75, 1.0, 1.2, 1.5, 1.8, 2.5, 3.3]

    @staticmethod
    def _voltage_window(tech_node: float) -> Tuple[float, float]:
        tn = float(tech_node)
        if tn >= 28:
            return 0.5, 3.3
        if tn >= 7:
            return 0.5, 1.8
        if tn >= 3:
            return 0.45, 1.2
        if tn >= 1:
            return 0.35, 0.95
        return 0.3, 0.8

    @classmethod
    def supported_voltages(cls, tech_node: float) -> List[float]:
        vmin, vmax = cls._voltage_window(tech_node)
        return [v for v in cls.STANDARD_VOLTAGES if vmin <= v <= vmax]

    @staticmethod
    @lru_cache(maxsize=8192)
    def run_point(
        wn: float,
        wp: float,
        vdd: float,
        temp: float,
        cl_ff: float,
        corner: str,
        tech_node: float,
    ) -> Dict:
        result = SpiceEngine.run_inverter_transient(
            wn=float(wn),
            wp=float(wp),
            vdd=float(vdd),
            temp=float(temp),
            cl_ff=float(cl_ff),
            corner=str(corner),
            tech_node=float(tech_node),
        )
        return {
            "freq": result.freq,
            "power": result.power,
            "delay": result.delay,
            "fom": result.fom,
            "id_n": result.id_n,
            "id_p": result.id_p,
            "vth": result.vth,
            "cox": result.cox,
            "vov": result.vov,
            "source": result.source,
            "spice_verified": result.spice_verified,
            "switching": result.switching,
        }

    @classmethod
    def corner_summary(
        cls,
        wn: float,
        wp: float,
        vdd: float,
        temp: float,
        cl_ff: float,
        tech_node: float,
    ) -> Dict:
        summary: Dict[str, Dict] = {}
        for corner in cls.CORNERS:
            summary[corner] = cls.run_point(wn, wp, vdd, temp, cl_ff, corner, tech_node)
        return summary

    @classmethod
    def _point_specs(
        cls,
        wn: float,
        wp: float,
        cl_ff: float,
        tech_node: float,
    ) -> Iterable[Tuple[str, float, float]]:
        for corner in cls.CORNERS:
            for temp in cls.TEMPERATURES:
                for vdd in cls.supported_voltages(tech_node):
                    yield corner, temp, vdd

    @classmethod
    def run_full_sweep(
        cls,
        wn: float,
        wp: float,
        cl_ff: float,
        tech_node: float,
    ) -> Dict[str, List[Dict]]:
        results: Dict[str, List[Dict]] = {corner: [] for corner in cls.CORNERS}
        specs = list(cls._point_specs(wn, wp, cl_ff, tech_node))
        max_workers = max(1, int(os.getenv("PVT_SPICE_MAX_WORKERS", "4")))

        def simulate(spec: Tuple[str, float, float]) -> Tuple[str, Dict]:
            corner, temp, vdd = spec
            point = cls.run_point(wn, wp, vdd, temp, cl_ff, corner, tech_node)
            return corner, {
                "temp": temp,
                "vdd": vdd,
                "freq": point["freq"],
                "power": point["power"],
                "delay": point["delay"],
                "source": point["source"],
                "spice_verified": point["spice_verified"],
                "switching": point["switching"],
            }

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            for corner, payload in pool.map(simulate, specs):
                results[corner].append(payload)

        for corner in results:
            results[corner].sort(key=lambda row: (row["temp"], row["vdd"]))
        return results
