"""Pygame dashboard rendering for arbitrary joystick layouts."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import math
from typing import Any, Sequence

from .controller import ControllerSnapshot
from .usb import USBDevice

BG = (10, 15, 24)
PANEL = (18, 27, 40)
PANEL_ALT = (22, 33, 48)
BORDER = (39, 55, 72)
TEXT = (224, 233, 241)
MUTED = (128, 148, 168)
ACCENT = (43, 214, 177)
ACCENT_DARK = (18, 92, 83)
ACTIVE = (255, 193, 77)
DANGER = (244, 99, 105)


@dataclass(slots=True)
class Activity:
    label: str
    value: str
    timestamp: float


class Dashboard:
    def __init__(self, pg: Any) -> None:
        self.pg = pg
        self.font_small = pg.font.Font(None, 19)
        self.font = pg.font.Font(None, 23)
        self.font_medium = pg.font.Font(None, 29)
        self.font_large = pg.font.Font(None, 40)
        self.previous: ControllerSnapshot | None = None
        self.activity: deque[Activity] = deque(maxlen=5)

    def _text(
        self,
        surface: Any,
        value: str,
        position: tuple[int, int],
        *,
        color: tuple[int, int, int] = TEXT,
        font: Any | None = None,
        anchor: str = "topleft",
    ) -> Any:
        image = (font or self.font).render(value, True, color)
        rect = image.get_rect()
        setattr(rect, anchor, position)
        surface.blit(image, rect)
        return rect

    def _panel(self, surface: Any, rect: Any, title: str) -> None:
        self.pg.draw.rect(surface, PANEL, rect, border_radius=12)
        self.pg.draw.rect(surface, BORDER, rect, 1, border_radius=12)
        self._text(surface, title.upper(), (rect.x + 17, rect.y + 14), color=MUTED, font=self.font_small)

    def _record_activity(self, snapshot: ControllerSnapshot | None, now: float) -> None:
        previous = self.previous
        if snapshot is None:
            self.previous = None
            return
        if previous is not None:
            for index, value in enumerate(snapshot.buttons):
                old = previous.buttons[index] if index < len(previous.buttons) else False
                if value != old:
                    self.activity.appendleft(Activity(f"Button {index + 1}", "pressed" if value else "released", now))
            for index, value in enumerate(snapshot.axes):
                old = previous.axes[index] if index < len(previous.axes) else 0.0
                if abs(value - old) >= 0.08:
                    self.activity.appendleft(Activity(f"Axis {index + 1}", f"{value:+.3f}", now))
            for index, value in enumerate(snapshot.hats):
                old = previous.hats[index] if index < len(previous.hats) else (0, 0)
                if value != old:
                    self.activity.appendleft(Activity(f"Hat {index + 1}", f"{value[0]:+d}, {value[1]:+d}", now))
        self.previous = snapshot

    def render(
        self,
        surface: Any,
        usb_devices: Sequence[USBDevice],
        snapshot: ControllerSnapshot | None,
        error: str,
        now: float,
    ) -> None:
        self._record_activity(snapshot, now)
        surface.fill(BG)
        width, height = surface.get_size()
        margin = max(16, width // 70)
        header_h = 104

        self._text(surface, "THRUSTMASTER", (margin, 20), color=ACCENT, font=self.font_small)
        self._text(surface, "Controller bring-up", (margin, 41), font=self.font_large)
        status = "LIVE INPUT" if snapshot else ("USB DETECTED" if usb_devices else "WAITING FOR DEVICE")
        status_color = ACCENT if snapshot else (ACTIVE if usb_devices else MUTED)
        status_image = self.font_small.render(f"●  {status}", True, status_color)
        status_rect = status_image.get_rect(topright=(width - margin, 25))
        chip = status_rect.inflate(25, 16)
        self.pg.draw.rect(surface, PANEL_ALT, chip, border_radius=chip.height // 2)
        self.pg.draw.rect(surface, BORDER, chip, 1, border_radius=chip.height // 2)
        surface.blit(status_image, status_rect)
        self._text(surface, "R rescan   F fullscreen   Esc quit", (width - margin, 68), color=MUTED, font=self.font_small, anchor="topright")

        body = self.pg.Rect(margin, header_h, width - margin * 2, height - header_h - margin)
        gap = 14
        left_w = int(body.width * 0.62)
        left = self.pg.Rect(body.x, body.y, left_w, body.height)
        right = self.pg.Rect(left.right + gap, body.y, body.width - left_w - gap, body.height)

        identity_h = 108
        identity = self.pg.Rect(left.x, left.y, left.width, identity_h)
        visual = self.pg.Rect(left.x, identity.bottom + gap, left.width, max(180, int((left.height - identity_h - gap * 2) * 0.43)))
        buttons = self.pg.Rect(left.x, visual.bottom + gap, left.width, left.bottom - visual.bottom - gap)
        axes_h = max(225, int(right.height * 0.48))
        axes = self.pg.Rect(right.x, right.y, right.width, axes_h)
        hats = self.pg.Rect(right.x, axes.bottom + gap, right.width, max(128, int((right.height - axes_h - gap * 2) * 0.48)))
        events = self.pg.Rect(right.x, hats.bottom + gap, right.width, right.bottom - hats.bottom - gap)

        self._draw_identity(surface, identity, usb_devices, snapshot, error)
        self._draw_sticks(surface, visual, snapshot)
        self._draw_buttons(surface, buttons, snapshot)
        self._draw_axes(surface, axes, snapshot)
        self._draw_hats(surface, hats, snapshot)
        self._draw_events(surface, events, now)

    def _draw_identity(self, surface: Any, rect: Any, devices: Sequence[USBDevice], snapshot: ControllerSnapshot | None, error: str) -> None:
        self._panel(surface, rect, "Device")
        if devices:
            device = devices[0]
            self._text(surface, device.name, (rect.x + 17, rect.y + 39), font=self.font_medium)
            detail = f"USB {device.usb_id}  ·  {device.location}"
            if device.serial:
                detail += f"  ·  S/N {device.serial}"
            self._text(surface, detail, (rect.x + 17, rect.y + 72), color=MUTED, font=self.font_small)
        else:
            self._text(surface, "Connect a Thrustmaster USB controller", (rect.x + 17, rect.y + 43), color=MUTED)
        if snapshot:
            controls = f"{len(snapshot.axes)} axes  ·  {len(snapshot.buttons)} buttons  ·  {len(snapshot.hats)} hats"
            self._text(surface, controls, (rect.right - 17, rect.y + 42), color=ACCENT, font=self.font_small, anchor="topright")
        elif error and devices:
            self._text(surface, error[:54], (rect.right - 17, rect.y + 42), color=DANGER, font=self.font_small, anchor="topright")

    def _draw_sticks(self, surface: Any, rect: Any, snapshot: ControllerSnapshot | None) -> None:
        self._panel(surface, rect, "Stick space")
        values = snapshot.axes if snapshot else ()
        pair_count = max(1, min(3, math.ceil(len(values) / 2)))
        available_w = rect.width - 34
        cell_w = available_w / pair_count
        radius = int(min((rect.height - 76) / 2, cell_w * 0.32, 62))
        center_y = rect.y + 47 + radius
        for pair in range(pair_count):
            center_x = int(rect.x + 17 + cell_w * (pair + 0.5))
            x = values[pair * 2] if pair * 2 < len(values) else 0.0
            y = values[pair * 2 + 1] if pair * 2 + 1 < len(values) else 0.0
            self.pg.draw.circle(surface, PANEL_ALT, (center_x, center_y), radius)
            self.pg.draw.circle(surface, BORDER, (center_x, center_y), radius, 2)
            self.pg.draw.line(surface, BORDER, (center_x - radius + 8, center_y), (center_x + radius - 8, center_y), 1)
            self.pg.draw.line(surface, BORDER, (center_x, center_y - radius + 8), (center_x, center_y + radius - 8), 1)
            knob = (int(center_x + x * (radius - 12)), int(center_y + y * (radius - 12)))
            self.pg.draw.line(surface, ACCENT_DARK, (center_x, center_y), knob, 4)
            self.pg.draw.circle(surface, ACCENT, knob, 8)
            label = f"AXES {pair * 2 + 1}/{pair * 2 + 2}"
            self._text(surface, label, (center_x, rect.bottom - 24), color=MUTED, font=self.font_small, anchor="center")

    def _draw_buttons(self, surface: Any, rect: Any, snapshot: ControllerSnapshot | None) -> None:
        self._panel(surface, rect, "Buttons")
        values = snapshot.buttons if snapshot else ()
        count = max(1, len(values))
        columns = min(8, max(4, math.ceil(math.sqrt(count * 1.7))))
        rows = math.ceil(count / columns)
        grid = self.pg.Rect(rect.x + 15, rect.y + 38, rect.width - 30, rect.height - 50)
        cell_w = grid.width / columns
        cell_h = grid.height / max(1, rows)
        radius = int(max(10, min(22, cell_w * 0.24, cell_h * 0.30)))
        for index in range(count):
            column, row = index % columns, index // columns
            center = (int(grid.x + (column + 0.5) * cell_w), int(grid.y + (row + 0.42) * cell_h))
            pressed = values[index] if index < len(values) else False
            fill = ACTIVE if pressed else PANEL_ALT
            outline = ACTIVE if pressed else BORDER
            self.pg.draw.circle(surface, fill, center, radius)
            self.pg.draw.circle(surface, outline, center, radius, 2)
            self._text(surface, str(index + 1), center, color=BG if pressed else TEXT, font=self.font_small, anchor="center")

    def _draw_axes(self, surface: Any, rect: Any, snapshot: ControllerSnapshot | None) -> None:
        self._panel(surface, rect, "All axes")
        values = snapshot.axes if snapshot else ()
        if not values:
            self._text(surface, "No axis data", (rect.centerx, rect.centery), color=MUTED, font=self.font_small, anchor="center")
            return
        content_y = rect.y + 44
        row_h = min(38, (rect.height - 53) / len(values))
        for index, value in enumerate(values):
            y = int(content_y + index * row_h)
            self._text(surface, f"A{index + 1}", (rect.x + 17, y), color=MUTED, font=self.font_small)
            self._text(surface, f"{value:+.3f}", (rect.right - 17, y), color=TEXT, font=self.font_small, anchor="topright")
            bar = self.pg.Rect(rect.x + 53, y + 5, rect.width - 127, 8)
            self.pg.draw.rect(surface, PANEL_ALT, bar, border_radius=4)
            self.pg.draw.line(surface, BORDER, (bar.centerx, bar.y - 3), (bar.centerx, bar.bottom + 3), 1)
            marker_x = int(bar.centerx + max(-1.0, min(1.0, value)) * (bar.width / 2 - 5))
            self.pg.draw.circle(surface, ACCENT, (marker_x, bar.centery), 6)

    def _draw_hats(self, surface: Any, rect: Any, snapshot: ControllerSnapshot | None) -> None:
        self._panel(surface, rect, "Hat switches")
        values = snapshot.hats if snapshot else ()
        if not values:
            self._text(surface, "No hat data", (rect.centerx, rect.centery), color=MUTED, font=self.font_small, anchor="center")
            return
        slot_w = (rect.width - 30) / len(values)
        size = int(min(64, rect.height - 69, slot_w * 0.60))
        for index, (x_value, y_value) in enumerate(values):
            center = (int(rect.x + 15 + slot_w * (index + 0.5)), int(rect.y + 47 + size / 2))
            step = size // 3
            for x in (-1, 0, 1):
                for y in (-1, 0, 1):
                    cell = self.pg.Rect(center[0] + x * step - step // 2, center[1] - y * step - step // 2, step - 2, step - 2)
                    active = (x, y) == (x_value, y_value)
                    self.pg.draw.rect(surface, ACTIVE if active else PANEL_ALT, cell, border_radius=3)
            self._text(surface, f"HAT {index + 1}  {x_value:+d},{y_value:+d}", (center[0], rect.bottom - 22), color=MUTED, font=self.font_small, anchor="center")

    def _draw_events(self, surface: Any, rect: Any, now: float) -> None:
        self._panel(surface, rect, "Recent input")
        if not self.activity:
            self._text(surface, "Move a control…", (rect.x + 17, rect.y + 43), color=MUTED, font=self.font_small)
            return
        y = rect.y + 39
        for item in list(self.activity)[: max(1, (rect.height - 44) // 23)]:
            age = max(0.0, now - item.timestamp)
            color = ACCENT if age < 0.6 else MUTED
            self._text(surface, item.label, (rect.x + 17, y), color=color, font=self.font_small)
            self._text(surface, item.value, (rect.right - 17, y), color=color, font=self.font_small, anchor="topright")
            y += 23
