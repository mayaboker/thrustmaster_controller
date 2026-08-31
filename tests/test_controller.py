from thrustmaster_controller.controller import _looks_like_thrustmaster


class FakeJoystick:
    def __init__(self, name: str, guid: str) -> None:
        self.name = name
        self.guid = guid

    def get_name(self) -> str:
        return self.name

    def get_guid(self) -> str:
        return self.guid


def test_matches_name_and_linux_guid() -> None:
    assert _looks_like_thrustmaster(FakeJoystick("ThrustMaster T.16000M", "other"))
    assert _looks_like_thrustmaster(FakeJoystick("Generic stick", "030065a94f0400000ab1000000010000"))
    assert not _looks_like_thrustmaster(FakeJoystick("Other stick", "0300000000000000"))
