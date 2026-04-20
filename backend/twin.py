def digital_twin(base):
    timeline = []

    for t in range(10):
        timeline.append(
            {
                "t": t,
                "freq": base["freq"] * (1 - 0.02 * t),
                "power": base["power"] * (1 + 0.03 * t),
                "delay": base["delay"] * (1 + 0.04 * t),
            }
        )

    return timeline
