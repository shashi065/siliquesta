def compute_core(state):
    wn = state["wn"]
    wp = state["wp"]
    vdd = state["vdd"]
    cl = state["cl"]

    freq = (wn / (wp + 0.5)) * vdd * 2
    power = (vdd ** 2) * freq * cl * 0.1
    delay = (1 / freq) * 1000

    return {"freq": freq, "power": power, "delay": delay}
