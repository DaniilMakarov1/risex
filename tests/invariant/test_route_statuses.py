from core.domain.enums import RouteStatus


def test_route_statuses_do_not_include_canary_eligible() -> None:
    assert "CANARY_ELIGIBLE" not in {status.name for status in RouteStatus}
    assert "CANARY_ELIGIBLE" not in {status.value for status in RouteStatus}


def test_route_statuses_are_explicit_contract() -> None:
    assert {status.value for status in RouteStatus} == {
        "RESEARCH_ONLY",
        "PAPER_ELIGIBLE",
        "LIVE_ELIGIBLE",
        "REJECTED",
    }
