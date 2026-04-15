"""ML dependency validation."""

from __future__ import annotations

import os

import pytest


pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_ML_TESTS", "0") == "1",
    reason="ML stack validation skipped.",
)


def test_ml_stack_imports() -> None:
    import torch  # noqa: F401
    import xgboost  # noqa: F401
    import optuna  # noqa: F401
