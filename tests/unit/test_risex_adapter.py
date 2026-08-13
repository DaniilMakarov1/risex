from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from core.domain.enums import ValueSource
from core.venues.risex import RiseXObservationAdapter


OBSERVED_AT = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
NEXT_FUNDING_NS = "1786518000000000000"


class FakeRiseXAPI:
    def __init__(
        self,
        *,
        markets_payload: dict[str, Any] | None = None,
        orderbook_payload: dict[str, Any] | None = None,
    ) -> None:
        self.calls: list[tuple[str, dict[str, str]]] = []
        self.markets_payload = markets_payload or _markets_payload()
        self.orderbook_payload = orderbook_payload or _orderbook_payload()

    def __call__(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        self.calls.append((path, params))
        if path == "/v1/markets":
            return self.markets_payload
        if path == "/v1/orderbook":
            return self.orderbook_payload
        raise AssertionError(f"unexpected RISEx endpoint: {path}")


def _markets_payload(
    *,
    market_id: str = "1",
    name: str = "BTC/USDC",
    active: Any = True,
    unlocked: Any = True,
    next_funding_time: str | None = NEXT_FUNDING_NS,
) -> dict[str, Any]:
    market: dict[str, Any] = {
        "market_id": market_id,
        "config": {"name": name, "unlocked": unlocked},
        "display_name": name,
        "underlying": name,
        "active": active,
    }
    if next_funding_time is not None:
        market["next_funding_time"] = next_funding_time
    return {"data": {"markets": [market]}, "request_id": "fixture-request"}


def _markets_payload_without_active() -> dict[str, Any]:
    payload = _markets_payload()
    del payload["data"]["markets"][0]["active"]
    return payload


def _markets_payload_without_unlocked() -> dict[str, Any]:
    payload = _markets_payload()
    del payload["data"]["markets"][0]["config"]["unlocked"]
    return payload


def _orderbook_payload(
    *,
    market_id: Any = "1",
    bids: list[dict[str, Any]] | None = None,
    asks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "data": {
            "market_id": market_id,
            "bids": bids
            if bids is not None
            else [{"price": "63669.7", "quantity": "0.000785", "order_count": 1}],
            "asks": asks
            if asks is not None
            else [{"price": "63669.8", "quantity": "0.000786", "order_count": 1}],
        },
        "request_id": "fixture-request",
    }


def _adapter(fake_api: FakeRiseXAPI) -> RiseXObservationAdapter:
    return RiseXObservationAdapter(fetch_json=fake_api, clock=lambda: OBSERVED_AT)


def test_fetch_observation_normalizes_public_risex_market_data_only() -> None:
    fake_api = FakeRiseXAPI()

    observation = _adapter(fake_api).fetch_observation("BTC-PERP")

    assert fake_api.calls == [
        ("/v1/markets", {}),
        ("/v1/orderbook", {"market_id": "1", "limit": "50"}),
    ]
    assert observation.venue == "RiseX"
    assert observation.symbol == "BTC-PERP"
    assert observation.observed_at == OBSERVED_AT
    assert observation.funding_settlement_at == datetime(2026, 8, 12, 7, 0, tzinfo=UTC)
    assert observation.order_book.venue == "RiseX"
    assert observation.order_book.symbol == "BTC-PERP"
    assert observation.order_book.bids[0].price == Decimal("63669.7")
    assert observation.order_book.bids[0].size == Decimal("0.000785")
    assert observation.order_book.asks[0].price == Decimal("63669.8")
    assert observation.order_book.asks[0].size == Decimal("0.000786")
    assert observation.expected_funding_usd.value is None
    assert observation.expected_funding_usd.source is ValueSource.UNKNOWN
    assert len(observation.fees.components) == 1
    assert observation.fees.components[0].amount_usd.value is None
    assert observation.fees.components[0].amount_usd.source is ValueSource.UNKNOWN


def test_fetch_observation_preserves_exact_risex_api_symbol_when_requested() -> None:
    fake_api = FakeRiseXAPI()

    observation = _adapter(fake_api).fetch_observation("BTC/USDC")

    assert observation.symbol == "BTC/USDC"
    assert observation.order_book.symbol == "BTC/USDC"


def test_fetch_observation_preserves_public_risex_funding_rate_metadata_only() -> None:
    markets_payload = _markets_payload()
    markets_payload["data"]["markets"][0]["funding_rate"] = "0.0002"
    fake_api = FakeRiseXAPI(markets_payload=markets_payload)

    observation = _adapter(fake_api).fetch_observation("BTC-PERP")

    assert observation.expected_funding_usd.value is None
    assert observation.expected_funding_usd.source is ValueSource.UNKNOWN
    assert observation.expected_funding_usd.metadata == {
        "public_funding_rate": "0.0002",
        "public_funding_rate_field": "funding_rate",
        "public_funding_rate_source": "OBSERVED",
    }


def test_fetch_observation_preserves_config_public_funding_rate_metadata_only() -> None:
    markets_payload = _markets_payload()
    markets_payload["data"]["markets"][0]["config"]["nextFundingRate"] = "-0.0001"
    fake_api = FakeRiseXAPI(markets_payload=markets_payload)

    observation = _adapter(fake_api).fetch_observation("BTC-PERP")

    assert observation.expected_funding_usd.value is None
    assert observation.expected_funding_usd.source is ValueSource.UNKNOWN
    assert observation.expected_funding_usd.metadata == {
        "public_funding_rate": "-0.0001",
        "public_funding_rate_field": "nextFundingRate",
        "public_funding_rate_source": "OBSERVED",
    }


@pytest.mark.parametrize("funding_rate", ("not-a-rate", "NaN", "Infinity"))
def test_fetch_observation_keeps_malformed_risex_funding_rate_unknown(
    funding_rate: str,
) -> None:
    markets_payload = _markets_payload()
    markets_payload["data"]["markets"][0]["fundingRate"] = funding_rate
    fake_api = FakeRiseXAPI(markets_payload=markets_payload)

    observation = _adapter(fake_api).fetch_observation("BTC-PERP")

    assert observation.expected_funding_usd.value is None
    assert observation.expected_funding_usd.source is ValueSource.UNKNOWN
    assert observation.expected_funding_usd.metadata == {}


def test_fetch_observation_fails_closed_when_market_is_missing() -> None:
    fake_api = FakeRiseXAPI(markets_payload={"data": {"markets": []}})

    with pytest.raises(ValueError, match="RISEx market not found"):
        _adapter(fake_api).fetch_observation("BTC-PERP")

    assert fake_api.calls == [("/v1/markets", {})]


@pytest.mark.parametrize(
    ("markets_payload", "message"),
    (
        (_markets_payload(active=False), "active must be true"),
        (_markets_payload_without_active(), "active must be true"),
        (_markets_payload(active=None), "active must be true"),
        (_markets_payload(active="true"), "active must be true"),
        (_markets_payload(unlocked=False), "config.unlocked must be true"),
        (_markets_payload_without_unlocked(), "config.unlocked must be true"),
        (_markets_payload(unlocked=None), "config.unlocked must be true"),
        (_markets_payload(unlocked="true"), "config.unlocked must be true"),
    ),
)
def test_fetch_observation_fails_closed_when_market_is_inactive_locked_or_malformed(
    markets_payload: dict[str, Any],
    message: str,
) -> None:
    fake_api = FakeRiseXAPI(markets_payload=markets_payload)

    with pytest.raises(ValueError, match=message):
        _adapter(fake_api).fetch_observation("BTC-PERP")


def test_fetch_observation_fails_closed_when_response_is_not_object() -> None:
    def malformed_fetch(path: str, params: dict[str, str]) -> list[str]:
        return ["not", "an", "object"]

    adapter = RiseXObservationAdapter(fetch_json=malformed_fetch, clock=lambda: OBSERVED_AT)

    with pytest.raises(ValueError, match="RISEx response must be a JSON object"):
        adapter.fetch_observation("BTC-PERP")


def test_fetch_observation_fails_closed_on_ambiguous_market() -> None:
    fake_api = FakeRiseXAPI(
        markets_payload={
            "data": {
                "markets": [
                    _markets_payload(market_id="1")["data"]["markets"][0],
                    _markets_payload(market_id="2")["data"]["markets"][0],
                ]
            }
        }
    )

    with pytest.raises(ValueError, match="ambiguous"):
        _adapter(fake_api).fetch_observation("BTC-PERP")


@pytest.mark.parametrize(
    ("markets_payload", "message"),
    (
        (_markets_payload(next_funding_time=None), "next_funding_time is required"),
        (_markets_payload(next_funding_time="not-a-timestamp"), "Unix nanosecond"),
        (_markets_payload(next_funding_time="0"), "next_funding_time must be positive"),
    ),
)
def test_fetch_observation_fails_closed_on_missing_or_invalid_settlement_time(
    markets_payload: dict[str, Any],
    message: str,
) -> None:
    fake_api = FakeRiseXAPI(markets_payload=markets_payload)

    with pytest.raises(ValueError, match=message):
        _adapter(fake_api).fetch_observation("BTC-PERP")


@pytest.mark.parametrize(
    ("orderbook_payload", "message"),
    (
        (
            {
                "data": {
                    "bids": [{"price": "1", "quantity": "1"}],
                    "asks": [{"price": "1", "quantity": "1"}],
                }
            },
            "orderbook requires market_id",
        ),
        (_orderbook_payload(market_id="2"), "market_id must match selected market_id"),
        ({"data": {"market_id": "1", "asks": [{"price": "1", "quantity": "1"}]}}, "bids"),
        (_orderbook_payload(bids=[]), "non-empty bids"),
        (_orderbook_payload(bids=[{"price": "0", "quantity": "1"}]), "bids.price must be positive"),
        (
            _orderbook_payload(asks=[{"price": "1", "quantity": "-1"}]),
            "asks.quantity must be positive",
        ),
        (
            _orderbook_payload(asks=[{"price": "not-a-price", "quantity": "1"}]),
            "asks.price must be a Decimal string",
        ),
    ),
)
def test_fetch_observation_fails_closed_on_missing_or_invalid_orderbook_data(
    orderbook_payload: dict[str, Any],
    message: str,
) -> None:
    fake_api = FakeRiseXAPI(orderbook_payload=orderbook_payload)

    with pytest.raises(ValueError, match=message):
        _adapter(fake_api).fetch_observation("BTC-PERP")


def test_fetch_observation_fails_closed_when_clock_returns_naive_timestamp() -> None:
    fake_api = FakeRiseXAPI()
    adapter = RiseXObservationAdapter(
        fetch_json=fake_api,
        clock=lambda: datetime(2026, 1, 1, 12, 0),
    )

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        adapter.fetch_observation("BTC-PERP")
