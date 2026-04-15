"""Reference-guided multi-objective optimizer for SILIQUESTA."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any

from app.services.cmos_engine import CMOSPhysicsEngine, DigitalTwin, ProcessCorner

try:
    import optuna  # type: ignore
except Exception:  # pragma: no cover - optional runtime dependency
    optuna = None


@dataclass
class Candidate:
    wn: float
    wp: float
    vdd: float
    temp: float
    cl_ff: float
    corner: str
    tech_node: float
    freq: float
    power: float
    delay: float
    fom: float
    reliability_score: float
    lifetime_years: float
    constraint_penalty: float
    explanation: str = ""
    rank_score: float = 0.0

    def objective_vector(self) -> tuple[float, float, float, float]:
        return (self.freq, -self.power, -self.delay, self.reliability_score)

    def payload(self) -> dict[str, Any]:
        return {
            "wn": round(self.wn, 4),
            "wp": round(self.wp, 4),
            "vdd": round(self.vdd, 4),
            "temp": round(self.temp, 2),
            "cl_ff": round(self.cl_ff, 4),
            "corner": self.corner,
            "tech_node": self.tech_node,
            "freq": round(self.freq, 4),
            "power": round(self.power, 4),
            "delay": round(self.delay, 4),
            "fom": round(self.fom, 4),
            "reliability_score": round(self.reliability_score, 4),
            "lifetime_years": round(self.lifetime_years, 4),
            "constraint_penalty": round(self.constraint_penalty, 4),
            "rank_score": round(self.rank_score, 6),
            "explanation": self.explanation,
        }


class AutonomousDesignAgent:
    """Multi-objective evolutionary optimizer with local exploitation refinement."""

    def __init__(self, seed: int = 42) -> None:
        self.random = random.Random(seed)

    def optimize(
        self,
        *,
        wn: float,
        wp: float,
        vdd: float,
        temp: float,
        cl_ff: float,
        corner: str,
        tech_node: float,
        max_power: float,
        min_freq: float,
        min_lifetime_years: float,
        population_size: int = 48,
        generations: int = 10,
    ) -> dict[str, Any]:
        seed = abs(hash((round(wn, 6), round(wp, 6), round(vdd, 6), round(temp, 4), round(cl_ff, 6), round(tech_node, 4), corner, max_power, min_freq, min_lifetime_years, population_size, generations))) % (2**31 - 1)
        self.random = random.Random(seed)
        population = [
            self._random_candidate(wn, wp, vdd, temp, cl_ff, corner, tech_node)
            for _ in range(population_size)
        ]
        population.extend(
            [
                self._evaluate(wn, wp, vdd, temp, cl_ff, corner, tech_node, max_power, min_freq, min_lifetime_years),
                self._evaluate(max(0.08, wn * 0.85), wp * 1.08, vdd, temp, cl_ff, corner, tech_node, max_power, min_freq, min_lifetime_years),
                self._evaluate(wn * 1.1, max(0.08, wp * 0.92), vdd, temp, cl_ff, corner, tech_node, max_power, min_freq, min_lifetime_years),
            ]
        )

        evaluated = [self._apply_constraints(c, max_power, min_freq, min_lifetime_years) for c in population]
        for _ in range(generations):
            fronts = self._non_dominated_sort(evaluated)
            parents = self._select_parents(fronts, population_size)
            children: list[Candidate] = []
            while len(children) < population_size:
                p1 = self.random.choice(parents)
                p2 = self.random.choice(parents)
                child = self._crossover_mutate(p1, p2)
                child_eval = self._evaluate(
                    child.wn, child.wp, child.vdd, child.temp, child.cl_ff, child.corner, child.tech_node,
                    max_power, min_freq, min_lifetime_years,
                )
                children.append(self._apply_constraints(child_eval, max_power, min_freq, min_lifetime_years))
            evaluated = self._next_generation(evaluated + children, population_size)

        refined = self._bayesian_refinement(
            evaluated,
            max_power=max_power,
            min_freq=min_freq,
            min_lifetime_years=min_lifetime_years,
            seed=seed,
        )
        archive = self._next_generation(evaluated + refined, population_size + 24)
        pareto_front = self._non_dominated_sort(archive)[0]
        self._score_candidates(archive)
        ranked = sorted(archive, key=lambda c: (-c.rank_score, c.constraint_penalty, -c.freq))

        summary = {
            "optimizer": "reference-guided-evolutionary-ada",
            "population_size": population_size,
            "generations": generations,
            "evaluated_points": len(archive),
            "pareto_front": [candidate.payload() for candidate in pareto_front[:20]],
            "ranked_solutions": [candidate.payload() for candidate in ranked[:20]],
            "recommendation": ranked[0].payload() if ranked else None,
            "tradeoff_summary": self._tradeoff_summary(ranked[:5]),
            "bayesian_refinement": "optuna" if optuna is not None else "local-refinement",
        }
        summary["best_design"] = summary["recommendation"]
        summary["ranking"] = summary["ranked_solutions"]
        summary["explanation"] = summary["tradeoff_summary"]
        return summary

    def _random_candidate(self, wn: float, wp: float, vdd: float, temp: float, cl_ff: float, corner: str, tech_node: float) -> Candidate:
        return Candidate(
            wn=max(0.08, wn * self.random.uniform(0.35, 2.4)),
            wp=max(0.08, wp * self.random.uniform(0.35, 2.4)),
            vdd=max(0.35, vdd * self.random.uniform(0.78, 1.18)),
            temp=max(-40.0, min(125.0, temp + self.random.uniform(-35.0, 35.0))),
            cl_ff=max(0.5, cl_ff * self.random.uniform(0.4, 2.2)),
            corner=corner,
            tech_node=tech_node,
            freq=0.0,
            power=0.0,
            delay=0.0,
            fom=0.0,
            reliability_score=0.0,
            lifetime_years=0.0,
            constraint_penalty=0.0,
        )

    def _evaluate(
        self,
        wn: float,
        wp: float,
        vdd: float,
        temp: float,
        cl_ff: float,
        corner: str,
        tech_node: float,
        max_power: float,
        min_freq: float,
        min_lifetime_years: float,
    ) -> Candidate:
        corner_enum = ProcessCorner[corner] if corner in ProcessCorner.__members__ else ProcessCorner.TT
        result = CMOSPhysicsEngine.compute(
            wn=wn,
            wp=wp,
            vdd=vdd,
            temp=temp,
            cl_ff=cl_ff,
            corner=corner_enum,
            tech_node=tech_node,
        )
        aging = DigitalTwin.compute_aging(
            wn=wn,
            wp=wp,
            vdd=vdd,
            temp=temp,
            cl_ff=cl_ff,
            tech_node=tech_node,
            corner=corner,
            years=10,
        )
        lifetime = float(aging["mtf_em"])
        reliability_score = min(99.0, max(0.0, float(aging["health_score"])))
        candidate = Candidate(
            wn=wn,
            wp=wp,
            vdd=vdd,
            temp=temp,
            cl_ff=cl_ff,
            corner=corner,
            tech_node=tech_node,
            freq=result.freq,
            power=result.power,
            delay=result.delay,
            fom=result.fom,
            reliability_score=reliability_score,
            lifetime_years=lifetime,
            constraint_penalty=0.0,
        )
        return self._apply_constraints(candidate, max_power, min_freq, min_lifetime_years)

    def _apply_constraints(self, candidate: Candidate, max_power: float, min_freq: float, min_lifetime_years: float) -> Candidate:
        penalty = 0.0
        if candidate.power > max_power:
            penalty += (candidate.power - max_power) * 6.0
        if candidate.freq < min_freq:
            penalty += (min_freq - candidate.freq) * 8.0
        if candidate.lifetime_years < min_lifetime_years:
            penalty += (min_lifetime_years - candidate.lifetime_years) * 4.0
        candidate.constraint_penalty = round(penalty, 6)
        candidate.explanation = self._explain(candidate)
        return candidate

    def _dominates(self, a: Candidate, b: Candidate) -> bool:
        if a.constraint_penalty < b.constraint_penalty:
            return True
        if a.constraint_penalty > b.constraint_penalty:
            return False
        a_vec = a.objective_vector()
        b_vec = b.objective_vector()
        return all(ax >= bx for ax, bx in zip(a_vec, b_vec)) and any(ax > bx for ax, bx in zip(a_vec, b_vec))

    def _non_dominated_sort(self, population: list[Candidate]) -> list[list[Candidate]]:
        if not population:
            return []
        dominates: dict[int, set[int]] = {i: set() for i in range(len(population))}
        dominated_by_count: dict[int, int] = {i: 0 for i in range(len(population))}
        fronts: list[list[int]] = [[]]
        for i, candidate in enumerate(population):
            for j, other in enumerate(population):
                if i == j:
                    continue
                if self._dominates(candidate, other):
                    dominates[i].add(j)
                elif self._dominates(other, candidate):
                    dominated_by_count[i] += 1
            if dominated_by_count[i] == 0:
                fronts[0].append(i)
        level = 0
        while level < len(fronts) and fronts[level]:
            next_front: list[int] = []
            for i in fronts[level]:
                for j in dominates[i]:
                    dominated_by_count[j] -= 1
                    if dominated_by_count[j] == 0:
                        next_front.append(j)
            if next_front:
                fronts.append(next_front)
            level += 1
        return [[population[i] for i in front] for front in fronts if front]

    def _crowding_distance(self, front: list[Candidate]) -> dict[int, float]:
        if not front:
            return {}
        distances = {id(candidate): 0.0 for candidate in front}
        objectives = [
            lambda c: c.freq,
            lambda c: -c.power,
            lambda c: -c.delay,
            lambda c: c.reliability_score,
        ]
        for getter in objectives:
            ordered = sorted(front, key=getter)
            distances[id(ordered[0])] = float("inf")
            distances[id(ordered[-1])] = float("inf")
            min_v = getter(ordered[0])
            max_v = getter(ordered[-1])
            span = max(max_v - min_v, 1e-9)
            for idx in range(1, len(ordered) - 1):
                prev_v = getter(ordered[idx - 1])
                next_v = getter(ordered[idx + 1])
                distances[id(ordered[idx])] += (next_v - prev_v) / span
        return distances

    def _select_parents(self, fronts: list[list[Candidate]], population_size: int) -> list[Candidate]:
        selected: list[Candidate] = []
        for front in fronts:
            if len(selected) + len(front) <= population_size:
                selected.extend(front)
            else:
                distances = self._crowding_distance(front)
                selected.extend(sorted(front, key=lambda c: distances[id(c)], reverse=True)[: population_size - len(selected)])
                break
        return selected or fronts[0]

    def _next_generation(self, combined: list[Candidate], population_size: int) -> list[Candidate]:
        fronts = self._non_dominated_sort(combined)
        return self._select_parents(fronts, population_size)

    def _crossover_mutate(self, a: Candidate, b: Candidate) -> Candidate:
        mix = self.random.uniform(0.35, 0.65)
        wn = max(0.08, a.wn * mix + b.wn * (1 - mix))
        wp = max(0.08, a.wp * (1 - mix) + b.wp * mix)
        vdd = max(0.35, a.vdd * mix + b.vdd * (1 - mix))
        temp = max(-40.0, min(125.0, a.temp * mix + b.temp * (1 - mix)))
        cl_ff = max(0.5, a.cl_ff * mix + b.cl_ff * (1 - mix))
        wn *= self.random.uniform(0.9, 1.1)
        wp *= self.random.uniform(0.9, 1.1)
        vdd *= self.random.uniform(0.97, 1.03)
        temp += self.random.uniform(-5.0, 5.0)
        cl_ff *= self.random.uniform(0.92, 1.08)
        return Candidate(
            wn=wn,
            wp=wp,
            vdd=vdd,
            temp=temp,
            cl_ff=cl_ff,
            corner=a.corner,
            tech_node=a.tech_node,
            freq=0.0,
            power=0.0,
            delay=0.0,
            fom=0.0,
            reliability_score=0.0,
            lifetime_years=0.0,
            constraint_penalty=0.0,
        )

    def _bayesian_refinement(
        self,
        candidates: list[Candidate],
        *,
        max_power: float,
        min_freq: float,
        min_lifetime_years: float,
        seed: int,
    ) -> list[Candidate]:
        if optuna is not None:
            return self._optuna_refinement(candidates, max_power, min_freq, min_lifetime_years, seed=seed)
        return self._local_refinement(candidates, max_power, min_freq, min_lifetime_years)

    def _local_refinement(
        self,
        candidates: list[Candidate],
        max_power: float,
        min_freq: float,
        min_lifetime_years: float,
    ) -> list[Candidate]:
        self._score_candidates(candidates)
        anchors = sorted(candidates, key=lambda c: (-c.rank_score, c.constraint_penalty))[:8]
        refined: list[Candidate] = []
        for anchor in anchors:
            for factor in (0.94, 0.98, 1.02, 1.06):
                refined.append(
                    self._evaluate(
                        wn=max(0.08, anchor.wn * factor),
                        wp=max(0.08, anchor.wp / factor),
                        vdd=max(0.35, anchor.vdd * (1.0 + (factor - 1.0) * 0.25)),
                        temp=anchor.temp,
                        cl_ff=max(0.5, anchor.cl_ff * (1.0 + (factor - 1.0) * 0.4)),
                        corner=anchor.corner,
                        tech_node=anchor.tech_node,
                        max_power=max_power,
                        min_freq=min_freq,
                        min_lifetime_years=min_lifetime_years,
                    )
                )
        return refined

    def _optuna_refinement(
        self,
        candidates: list[Candidate],
        max_power: float,
        min_freq: float,
        min_lifetime_years: float,
        *,
        seed: int,
    ) -> list[Candidate]:
        self._score_candidates(candidates)
        anchors = sorted(candidates, key=lambda c: (-c.rank_score, c.constraint_penalty))[:5]
        if not anchors:
            return []
        anchor = anchors[0]

        def objective(trial):
            wn = trial.suggest_float("wn", max(0.08, anchor.wn * 0.6), anchor.wn * 1.5)
            wp = trial.suggest_float("wp", max(0.08, anchor.wp * 0.6), anchor.wp * 1.5)
            vdd = trial.suggest_float("vdd", max(0.35, anchor.vdd * 0.9), anchor.vdd * 1.08)
            cl_ff = trial.suggest_float("cl_ff", max(0.5, anchor.cl_ff * 0.75), anchor.cl_ff * 1.25)
            candidate = self._evaluate(
                wn=wn,
                wp=wp,
                vdd=vdd,
                temp=anchor.temp,
                cl_ff=cl_ff,
                corner=anchor.corner,
                tech_node=anchor.tech_node,
                max_power=max_power,
                min_freq=min_freq,
                min_lifetime_years=min_lifetime_years,
            )
            score = (
                candidate.freq * 0.5
                - candidate.power * 0.25
                - candidate.delay * 0.2
                + candidate.reliability_score * 0.05
                - candidate.constraint_penalty * 10.0
            )
            trial.set_user_attr("candidate", candidate.payload())
            return score

        sampler = optuna.samplers.TPESampler(seed=seed)
        study = optuna.create_study(direction="maximize", sampler=sampler)
        study.optimize(objective, n_trials=24, show_progress_bar=False)
        refined: list[Candidate] = []
        for trial in study.trials:
            data = trial.user_attrs.get("candidate")
            if not data:
                continue
            refined.append(
                Candidate(
                    wn=float(data["wn"]),
                    wp=float(data["wp"]),
                    vdd=float(data["vdd"]),
                    temp=float(data["temp"]),
                    cl_ff=float(data["cl_ff"]),
                    corner=str(data["corner"]),
                    tech_node=float(data["tech_node"]),
                    freq=float(data["freq"]),
                    power=float(data["power"]),
                    delay=float(data["delay"]),
                    fom=float(data["fom"]),
                    reliability_score=float(data["reliability_score"]),
                    lifetime_years=float(data["lifetime_years"]),
                    constraint_penalty=float(data["constraint_penalty"]),
                    explanation=str(data["explanation"]),
                    rank_score=float(data["rank_score"]),
                )
            )
        return refined

    def _score_candidates(self, candidates: list[Candidate]) -> None:
        if not candidates:
            return
        freq_min, freq_max = self._range(c.freq for c in candidates)
        power_min, power_max = self._range(c.power for c in candidates)
        delay_min, delay_max = self._range(c.delay for c in candidates)
        rel_min, rel_max = self._range(c.reliability_score for c in candidates)
        for candidate in candidates:
            freq_score = self._normalize(candidate.freq, freq_min, freq_max)
            power_score = 1.0 - self._normalize(candidate.power, power_min, power_max)
            delay_score = 1.0 - self._normalize(candidate.delay, delay_min, delay_max)
            rel_score = self._normalize(candidate.reliability_score, rel_min, rel_max)
            candidate.rank_score = max(
                0.0,
                (0.35 * freq_score + 0.25 * power_score + 0.2 * delay_score + 0.2 * rel_score)
                - 0.02 * candidate.constraint_penalty,
            )

    @staticmethod
    def _normalize(value: float, low: float, high: float) -> float:
        if math.isclose(high, low):
            return 1.0
        return max(0.0, min(1.0, (value - low) / (high - low)))

    @staticmethod
    def _range(values) -> tuple[float, float]:
        values = list(values)
        return (min(values), max(values))

    @staticmethod
    def _explain(candidate: Candidate) -> str:
        if candidate.constraint_penalty > 0:
            return (
                f"Violates one or more constraints. freq={candidate.freq:.2f}GHz, "
                f"power={candidate.power:.2f}mW, lifetime={candidate.lifetime_years:.1f}y."
            )
        dominant = max(
            [
                ("performance", candidate.freq),
                ("efficiency", candidate.fom),
                ("reliability", candidate.reliability_score),
            ],
            key=lambda item: item[1],
        )[0]
        return (
            f"{dominant.capitalize()}-leaning solution with {candidate.freq:.2f}GHz, "
            f"{candidate.power:.2f}mW, {candidate.delay:.3f}ps delay, "
            f"and {candidate.lifetime_years:.1f}y projected EM life."
        )

    @staticmethod
    def _tradeoff_summary(top: list[Candidate]) -> list[str]:
        lines: list[str] = []
        for idx, candidate in enumerate(top, start=1):
            lines.append(
                f"#{idx}: {candidate.freq:.2f}GHz / {candidate.power:.2f}mW / "
                f"{candidate.delay:.3f}ps / reliability {candidate.reliability_score:.1f}%."
            )
        return lines
