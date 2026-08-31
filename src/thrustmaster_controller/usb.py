from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

THRUSTMASTER_VENDOR_ID = "044f"
DEFAULT_SYSFS_ROOT = Path("/sys/bus/usb/devices")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


@dataclass(frozen=True, slots=True)
class USBDevice:
    sysfs_name: str
    vendor_id: str
    product_id: str
    manufacturer: str = ""
    product: str = ""
    serial: str = ""
    bus_number: str = ""
    device_number: str = ""

    @property
    def name(self) -> str:
        return self.product or self.manufacturer or "Thrustmaster USB device"

    @property
    def usb_id(self) -> str:
        return f"{self.vendor_id}:{self.product_id}"

    @property
    def location(self) -> str:
        if self.bus_number and self.device_number:
            return f"bus {self.bus_number}, device {self.device_number}"
        return self.sysfs_name

    @property
    def is_thrustmaster(self) -> bool:
        searchable = f"{self.manufacturer} {self.product}".casefold()
        return self.vendor_id.casefold() == THRUSTMASTER_VENDOR_ID or "thrustmaster" in searchable


def iter_usb_devices(sysfs_root: Path | str = DEFAULT_SYSFS_ROOT) -> list[USBDevice]:
    root = Path(sysfs_root)
    try:
        entries = sorted(root.iterdir(), key=lambda path: path.name)
    except OSError:
        return []

    devices: list[USBDevice] = []
    for entry in entries:
        vendor_id = _read_text(entry / "idVendor").casefold()
        product_id = _read_text(entry / "idProduct").casefold()
        if not vendor_id or not product_id:
            continue
        devices.append(
            USBDevice(
                sysfs_name=entry.name,
                vendor_id=vendor_id.zfill(4),
                product_id=product_id.zfill(4),
                manufacturer=_read_text(entry / "manufacturer"),
                product=_read_text(entry / "product"),
                serial=_read_text(entry / "serial"),
                bus_number=_read_text(entry / "busnum"),
                device_number=_read_text(entry / "devnum"),
            )
        )
    return devices


def find_thrustmaster_devices(
    sysfs_root: Path | str = DEFAULT_SYSFS_ROOT,
) -> list[USBDevice]:
    return [device for device in iter_usb_devices(sysfs_root) if device.is_thrustmaster]
