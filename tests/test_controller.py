from thrustmaster_controller.controller import ControllerSnapshot, _looks_like_thrustmaster


class FakeJoystick:
    def __init__(self, name: str, guid: str, vendor: int | None = None) -> None:
        self.name = name
        self.guid = guid
        self.vendor = vendor

    def get_name(self) -> str:
        return self.name

    def get_guid(self) -> str:
        return self.guid

    def get_vendor(self) -> int | None:
        return self.vendor


def test_matches_name_vendor_and_linux_guid() -> None:
    assert _looks_like_thrustmaster(FakeJoystick("ThrustMaster T.16000M", "other"))
    assert _looks_like_thrustmaster(FakeJoystick("Generic stick", "other", 0x044F))
    assert _looks_like_thrustmaster(FakeJoystick("Generic stick", "03004f0400000000"))
    assert not _looks_like_thrustmaster(FakeJoystick("Other stick", "0300000000000000"))


def test_snapshot_control_count_includes_every_input() -> None:
    snapshot = ControllerSnapshot("stick", "guid", (0.0, 1.0), (True, False, True), ((0, 1),), ((2, 3),))

    assert snapshot.control_count == 7
