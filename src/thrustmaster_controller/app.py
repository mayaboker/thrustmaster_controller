"""Command-line entry point and application loop."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import time
from typing import Sequence

from .controller import ControllerManager
from .demo import demo_snapshot
from .usb import DEFAULT_SYSFS_ROOT, USBDevice, find_thrustmaster_devices


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Find and visualize a Thrustmaster USB controller")
    parser.add_argument("--list", action="store_true", help="print matching USB devices and exit")
    parser.add_argument("--demo", action="store_true", help="show animated controls without hardware")
    parser.add_argument("--sysfs-root", type=Path, default=DEFAULT_SYSFS_ROOT, help="USB sysfs root (Linux)")
    parser.add_argument("--fps", type=int, default=60, help="display refresh rate (default: 60)")
    parser.add_argument("--frames", type=int, default=0, help=argparse.SUPPRESS)
    return parser


def describe_devices(devices: Sequence[USBDevice]) -> str:
    if not devices:
        return "No Thrustmaster USB devices found."
    lines = []
    for device in devices:
        serial = f", serial {device.serial}" if device.serial else ""
        lines.append(f"{device.usb_id}  {device.name}  ({device.location}{serial})")
    return "\n".join(lines)


def run(args: argparse.Namespace) -> int:
    devices = find_thrustmaster_devices(args.sysfs_root)
    if args.list:
        print(describe_devices(devices))
        return 0

    # Keep pygame's greeting out of a hardware utility's terminal output.
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    try:
        import pygame
    except ImportError:
        print("pygame-ce is required; install the project with: pip install -e .", file=sys.stderr)
        return 2

    from .ui import Dashboard

    pygame.init()
    pygame.joystick.init()
    flags = pygame.RESIZABLE
    surface = pygame.display.set_mode((1280, 800), flags)
    pygame.display.set_caption("Thrustmaster Controller Bring-up")
    pygame.display.set_icon(_make_icon(pygame))
    dashboard = Dashboard(pygame)
    manager = ControllerManager(pygame)
    if not args.demo:
        manager.rescan(bool(devices))

    clock = pygame.time.Clock()
    started = time.monotonic()
    last_scan = started
    running = True
    fullscreen = False
    frame_count = 0

    while running:
        rescan_requested = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    rescan_requested = True
                elif event.key == pygame.K_f:
                    fullscreen = not fullscreen
                    display_flags = pygame.FULLSCREEN if fullscreen else pygame.RESIZABLE
                    surface = pygame.display.set_mode((0, 0) if fullscreen else (1280, 800), display_flags)
            elif event.type in (pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED):
                rescan_requested = True

        now = time.monotonic()
        if rescan_requested or now - last_scan >= 1.0:
            devices = find_thrustmaster_devices(args.sysfs_root)
            if not args.demo and (rescan_requested or manager.joystick is None):
                manager.rescan(bool(devices))
            last_scan = now

        pygame.event.pump()
        snapshot = demo_snapshot(now - started) if args.demo else manager.snapshot()
        dashboard.render(surface, devices, snapshot, manager.error, now)
        pygame.display.flip()
        clock.tick(max(1, args.fps))
        frame_count += 1
        if args.frames and frame_count >= args.frames:
            running = False

    manager.close()
    pygame.joystick.quit()
    pygame.quit()
    return 0


def _make_icon(pg: object):
    surface = pg.Surface((32, 32), pg.SRCALPHA)
    pg.draw.circle(surface, (43, 214, 177), (16, 16), 12, 3)
    pg.draw.circle(surface, (255, 193, 77), (19, 13), 4)
    return surface


def main(argv: Sequence[str] | None = None) -> int:
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
