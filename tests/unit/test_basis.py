from decimal import Decimal

from apps.research_runner.fake_data import build_fake_route_and_snapshot
from core.economics.basis import calculate_current_unwind_pnl_usd


def test_current_unwind_pnl_uses_current_quotes_without_basis_forecast() -> None:
    _, snapshot = build_fake_route_and_snapshot()

    assert calculate_current_unwind_pnl_usd(
        risex_entry_quote=snapshot.risex_entry_quote,
        hedge_entry_quote=snapshot.hedge_entry_quote,
        risex_exit_quote=snapshot.risex_estimated_exit_quote,
        hedge_exit_quote=snapshot.hedge_estimated_exit_quote,
        realized_cashflows_usd=Decimal("2.5"),
    ) == Decimal("2.00")
