"""Animated, hardware-free input used for demos and UI smoke tests."""

from __future__ import annotations

import math

from .controller import ControllerSnapshot


def demo_snapshot(elapsed_seconds: float) -> ControllerSnapshot:
    phase = elapsed_seconds
    active = int(phase * 2.5) % 16
    hat_step = int(phase * 1.5) % 9
    hats = ((-1, 1), (0, 1), (1, 1), (-1, 0), (0, 0), (1, 0), (-1, -1), (0, -1), (1, -1))
    return ControllerSnapshot(
        name="Thrustmaster demo controller",
        guid="demo-044f",
        axes=(
            math.sin(phase * 1.2),
            math.cos(phase * 1.0),
            math.sin(phase * 0.7),
            math.cos(phase * 0.55),
        ),
        buttons=tuple(index == active for index in range(16)),
        hats=(hats[hat_step],),
    )
