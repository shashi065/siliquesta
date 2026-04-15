"""Test helpers."""

from __future__ import annotations

import time
from typing import Callable


def wait_for(predicate: Callable[[], bool], timeout: float = 120.0, interval: float = 2.0) -> None:
    start = time.time()
    while time.time() - start < timeout:
        if predicate():
            return
        time.sleep(interval)
    raise TimeoutError("Timed out waiting for condition.")
