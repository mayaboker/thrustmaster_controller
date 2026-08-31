from __future__ import annotations

from dataclasses import dataclass

import pygame


@dataclass(frozen=True, slots=True)
class ControllerSnapshot:
    name: str
    axes: tuple[float, ...]
    buttons: tuple[bool, ...]
    hats: tuple[tuple[int, int], ...]


def _looks_like_thrustmaster(joystick) -> bool:
    name = joystick.get_name().casefold()
    guid = joystick.get_guid().casefold()
    return "thrustmaster" in name or guid[8:12] == "4f04"


class ControllerManager:
    def __init__(self) -> None:
        self.joystick = None
        self.error = ""

    def close(self) -> None:
        if self.joystick is not None:
            try:
                self.joystick.quit()
            except pygame.error:
                pass
        self.joystick = None

    def rescan(self) -> bool:
        self.close()
        self.error = ""
        joysticks = []
        try:
            joysticks = [pygame.joystick.Joystick(index) for index in range(pygame.joystick.get_count())]
            self.joystick = next(
                (joystick for joystick in joysticks if _looks_like_thrustmaster(joystick)),
                None,
            )
        except pygame.error as exc:
            self.error = str(exc)

        for joystick in joysticks:
            if joystick is not self.joystick:
                joystick.quit()
        if self.joystick is None and not self.error:
            self.error = "No matching SDL joystick"
        return self.joystick is not None

    def snapshot(self) -> ControllerSnapshot | None:
        joystick = self.joystick
        if joystick is None or not joystick.get_init():
            return None
        try:
            return ControllerSnapshot(
                name=joystick.get_name(),
                axes=tuple(joystick.get_axis(index) for index in range(joystick.get_numaxes())),
                buttons=tuple(bool(joystick.get_button(index)) for index in range(joystick.get_numbuttons())),
                hats=tuple(joystick.get_hat(index) for index in range(joystick.get_numhats())),
            )
        except pygame.error as exc:
            self.error = str(exc)
            self.close()
            return None
