from core.domain.enums import RejectReason


def test_reject_reasons_are_centralized_contract() -> None:
    assert {reason.value for reason in RejectReason} >= {
        "TECHNICALLY_NOT_EXECUTABLE",
        "REQUIRED_LIVE_DATA_MISSING",
        "MIN_NET_PROFIT_NOT_MET",
        "USER_RULE_VIOLATED",
        "VENUE_MARKET_OR_MODE_DISABLED",
        "LEDGER_NOT_RECONCILED",
        "CAPTURE_PLAN_NOT_FRESH",
        "MIN_LEG_NOTIONAL_NOT_MET",
        "ORDERBOOK_NOT_EXECUTABLE_FOR_MIN_NOTIONAL",
        "LIVE_TRADING_DISABLED",
        "LIVE_GATES_NOT_IMPLEMENTED",
    }
