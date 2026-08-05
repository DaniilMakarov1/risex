from core.domain.enums import CaptureState


def test_capture_states_are_explicit_contract() -> None:
    assert {state.value for state in CaptureState} == {
        "DISCOVERED",
        "UNDERWRITING",
        "REJECTED",
        "APPROVED",
        "ENTERING",
        "PARTIALLY_ENTERED",
        "HEDGED",
        "WAITING_SETTLEMENT",
        "SETTLED",
        "EXITING",
        "CLOSED",
        "FAILED",
        "EMERGENCY_FLATTENED",
    }


def test_capture_states_do_not_include_forbidden_lifecycle_terms() -> None:
    state_names_and_values = {item for state in CaptureState for item in (state.name, state.value)}

    for forbidden_term in {"CANARY", "HOLD", "HOLDING_NEXT_CYCLE", "NEXT_CYCLE"}:
        assert all(forbidden_term not in item for item in state_names_and_values)
