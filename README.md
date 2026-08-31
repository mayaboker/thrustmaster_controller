# Thrustmaster Controller

A Linux desktop prototype that finds Thrustmaster hardware on the USB bus and
visualizes every input exposed by the controller: buttons, axes, and hat
switches. Devices can be plugged and unplugged while the app is running.

The bring-up was developed against a T.16000M (`044f:b10a`), but no model-specific
button count or report layout is hard-coded. The UI is generated from the inputs
reported by SDL, so other Thrustmaster sticks, gamepads, and wheels can be
inspected too.

## Run

Python 3.10+, [uv](https://docs.astral.sh/uv/getting-started/installation/),
and access to the Linux input device are required.

```bash
uv sync
uv run thrustmaster-controller
```

If the USB device is shown but input cannot be opened, add your user to the
system `input` group or install an appropriate udev rule, then sign in again.

```bash
sudo usermod -aG input "$USER"
```

Useful options:

```bash
uv run thrustmaster-controller --list       # print matching USB devices and exit
uv run thrustmaster-controller --demo       # exercise the UI without hardware
uv run thrustmaster-controller --sysfs-root /path/to/fixture
```

Press `R` to rescan, `F` to toggle fullscreen, and `Esc` to exit.

## How it works

1. `usb.py` enumerates `/sys/bus/usb/devices` and matches USB vendor ID `044f`
   (Thrustmaster/Guillemot) or a case-insensitive Thrustmaster manufacturer or
   product string.
2. SDL, through pygame-ce's low-level joystick API, opens the corresponding
   Linux input device and handles its HID report mapping.
3. The dashboard polls and renders every reported control at 60 Hz. It rescans
   USB and joystick state automatically for hot-plug support.

SDL's joystick API is intentionally used instead of its standardized gamepad
API: flight sticks and wheels can expose controls that do not fit a console
gamepad mapping, and the prototype must show all of them.

## Development

```bash
uv sync
uv run pytest
```

`uv.lock` is committed; use `uv lock --upgrade` when intentionally updating
dependencies.

The repository's default branch is `develop`; hardware bring-up work is on
`feature/bringup`.
