import random

try:
    from .core import compute_core
except ImportError:
    from core import compute_core


def run_optimizer():
    results = []

    for _ in range(300):
        state = {
            "wn": random.uniform(0.2, 1.5),
            "wp": random.uniform(0.5, 2.0),
            "vdd": random.uniform(0.8, 1.4),
            "cl": 10,
        }

        res = compute_core(state)
        results.append({**state, **res})

    pareto = []

    for r in results:
        dominated = False
        for o in results:
            if o is r:
                continue
            if (
                o["power"] <= r["power"]
                and o["delay"] <= r["delay"]
                and o["freq"] >= r["freq"]
                and (
                    o["power"] < r["power"]
                    or o["delay"] < r["delay"]
                    or o["freq"] > r["freq"]
                )
            ):
                dominated = True
                break
        if not dominated:
            pareto.append(r)

    return pareto
