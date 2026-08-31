"""SDL joystick selection and complete input snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .usb import THRUSTMASTER_VENDOR_ID


@dataclass(frozen=True, slots=True)
class ControllerSnapshot:
    name: str
    guid: str
    axes: tuple[float, ...]
    buttons: tuple[bool, ...]
    hats: tuple[tuple[int, int], ...]
    balls: tuple[tuple[int, int], ...] = ()

    @property
    def control_count(self) -> int:
        return len(self.axes) + len(self.buttons) + len(self.hats) + len(self.balls)


def _looks_like_thrustmaster(joystick: Any) -> bool:
    if "thrustmaster" in joystick.get_name().casefold():
        return True

    # SDL's Linux USB GUID contains the little-endian vendor ID (044f -> 4f04).
    # Prefer explicit vendor metadata when pygame/SDL exposes it, then use the
    # GUID only as a compatibility fallback.
    get_vendor = getattr(joystick, "get_vendor", None)
    if callable(get_vendor):
        try:
            if int(get_vendor()) == int(THRUSTMASTER_VENDOR_ID, 16):
                return True
        except (TypeError, ValueError, RuntimeError):
            pass
    try:
        return "4f04" in joystick.get_guid().casefold()
    except (AttributeError, RuntimeError):
        return False


class ControllerManager:
    """Own and poll the matching SDL joystick, including hot-plug rescans."""

    def __init__(self, pygame_module: Any) -> None:
        self.pg = pygame_module
        self.joystick: Any | None = None
        self.error = ""

    def close(self) -> None:
        if self.joystick is not None:
            try:
                self.joystick.quit()
            except self.pg.error:
                pass
        self.joystick = None

    def rescan(self, usb_match_present: bool) -> bool:
        """Open a Thrustmaster joystick and return whether one is ready."""

        self.close()
        self.error = ""
        candidates: list[Any] = []
        fallbacks: list[Any] = []
        try:
            for index in range(self.pg.joystick.get_count()):
                joystick = self.pg.joystick.Joystick(index)
                # pygame 2 initializes newly constructed handles. Retain the
                # guard for older compatible releases without triggering the
                # deprecated reinitialization path on current pygame-ce.
                if not joystick.get_init():
                    joystick.init()
                fallbacks.append(joystick)
                if _looks_like_thrustmaster(joystick):
                    candidates.append(joystick)
        except self.pg.error as exc:
            self.error = str(exc)

        # Some Linux drivers expose a generic SDL name. If USB positively found
        # a Thrustmaster and exactly one joystick exists, it is an unambiguous
        # and useful fallback.
        if not candidates and usb_match_present and len(fallbacks) == 1:
            candidates = fallbacks

        if candidates:
            self.joystick = candidates[0]
            for joystick in fallbacks:
                if joystick is not self.joystick:
                    joystick.quit()
            return True

        for joystick in fallbacks:
            joystick.quit()
        if not self.error:
            self.error = "No matching SDL joystick"
        return False

    def snapshot(self) -> ControllerSnapshot | None:
        joystick = self.joystick
        if joystick is None or not joystick.get_init():
            return None
        try:
            return ControllerSnapshot(
                name=joystick.get_name(),
                guid=joystick.get_guid(),
                axes=tuple(joystick.get_axis(index) for index in range(joystick.get_numaxes())),
                buttons=tuple(bool(joystick.get_button(index)) for index in range(joystick.get_numbuttons())),
                hats=tuple(joystick.get_hat(index) for index in range(joystick.get_numhats())),
                balls=tuple(joystick.get_ball(index) for index in range(joystick.get_numballs())),
            )
        except self.pg.error as exc:
            self.error = str(exc)
            self.close()
            return None
