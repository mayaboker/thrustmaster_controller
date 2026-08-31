from pathlib import Path

from thrustmaster_controller.usb import find_thrustmaster_devices, iter_usb_devices


def make_device(root: Path, name: str, **fields: str) -> Path:
    device = root / name
    device.mkdir()
    for field, value in fields.items():
        (device / field).write_text(value, encoding="utf-8")
    return device


def test_finds_thrustmaster_by_vendor_id(tmp_path: Path) -> None:
    make_device(
        tmp_path,
        "3-4",
        idVendor="044F\n",
        idProduct="b10a\n",
        manufacturer="ThrustMaster, Inc.\n",
        product="T.16000M Joystick\n",
        busnum="3\n",
        devnum="4\n",
    )
    make_device(tmp_path, "3-5", idVendor="413c", idProduct="301a", product="Mouse")

    devices = find_thrustmaster_devices(tmp_path)

    assert len(devices) == 1
    assert devices[0].usb_id == "044f:b10a"
    assert devices[0].name == "T.16000M Joystick"
    assert devices[0].location == "bus 3, device 4"


def test_finds_rebranded_device_by_name(tmp_path: Path) -> None:
    make_device(tmp_path, "1-2", idVendor="1234", idProduct="abcd", product="Thrustmaster Prototype")

    assert len(find_thrustmaster_devices(tmp_path)) == 1


def test_skips_interfaces_and_handles_missing_root(tmp_path: Path) -> None:
    (tmp_path / "3-4:1.0").mkdir()

    assert iter_usb_devices(tmp_path) == []
    assert iter_usb_devices(tmp_path / "missing") == []
