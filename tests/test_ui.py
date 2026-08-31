from thrustmaster_controller.ui import T16000M_BUTTON_POSITIONS


def test_t16000m_layout_covers_zero_based_buttons() -> None:
    assert set(T16000M_BUTTON_POSITIONS) == set(range(16))
    assert all(0.0 <= x <= 1.0 and 0.0 <= y <= 1.0 for x, y in T16000M_BUTTON_POSITIONS.values())
