from core.domain.enums import ValueSource


def test_value_source_is_explicit_contract() -> None:
    assert {source.value for source in ValueSource} == {
        "DOCUMENTED",
        "OBSERVED",
        "ESTIMATED_FROM_ORDERBOOK",
        "ESTIMATED_FROM_LAST_VALUE",
        "USER_CONFIGURED",
        "UNKNOWN",
    }
