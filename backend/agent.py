try:
    from .core import compute_core
except ImportError:
    from core import compute_core


def ai_agent(prompt, state):
    prompt = prompt.lower()

    if "reduce power" in prompt:
        state["vdd"] -= 0.1

    if "increase speed" in prompt:
        state["wn"] += 0.2

    return compute_core(state)
