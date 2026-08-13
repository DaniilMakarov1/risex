from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from core.domain.enums import ValueSource
from core.venues.hyperliquid import HyperliquidObservationAdapter


OBSERVED_AT_MS = 1_754_450_974_231
NEXT_FUNDING_MS = 1_786_518_000_000


class FakeHyperliquidInfoAPI:
    def __init__(
        self,
        *,
        meta_payload: Any | None = None,
        orderbook_payload: Any | None = None,
        predicted_fundings_payload: Any | None = None,
    ) -> None:
        self.calls: list[dict[str, Any]] = []
        self.meta_payload = _meta_payload() if meta_payload is None else meta_payload
        self.orderbook_payload = (
            _orderbook_payload() if orderbook_payload is None else orderbook_payload
        )
        self.predicted_fundings_payload = (
            _predicted_fundings_payload()
            if predicted_fundings_payload is None
            else predicted_fundings_payload
        )

    def __call__(self, body: dict[str, Any]) -> Any:
        self.calls.append(body)
        if body == {"type": "metaAndAssetCtxs"}:
            return self.meta_payload
        if body == {"type": "l2Book", "coin": "BTC"}:
            return self.orderbook_payload
        if body == {"type": "predictedFundings"}:
            return self.predicted_fundings_payload
        raise AssertionError(f"unexpected Hyperliquid info request: {body}")


def _market(coin: str = "BTC", *, is_delisted: Any | None = None) -> dict[str, Any]:
    market: dict[str, Any] = {
        "name": coin,
        "szDecimals": 5,
        "maxLeverage": 50,
    }
    if is_delisted is not None:
        market["isDelisted"] = is_delisted
    return market


def _asset_context() -> dict[str, Any]:
    return {
        "dayNtlVlm": "1169046.29406",
        "funding": "0.0000125",
        "markPx": "14.3161",
        "midPx": "14.314",
        "openInterest": "688.11",
        "oraclePx": "14.32",
    }


def _meta_payload(
    *,
    universe: list[Any] | None = None,
    asset_contexts: list[Any] | None = None,
) -> list[Any]:
    return [
        {"universe": [_market()] if universe is None else universe},
        [_asset_context()] if asset_contexts is None else asset_contexts,
    ]


def _orderbook_payload(
    *,
    coin: Any = "BTC",
    time: Any = OBSERVED_AT_MS,
    bids: list[Any] | None = None,
    asks: list[Any] | None = None,
) -> dict[str, Any]:
    return {
        "coin": coin,
        "time": time,
        "levels": [
            bids
            if bids is not None
            else [{"px": "113377.0", "sz": "7.6699", "n": 17}],
            asks
            if asks is not None
            else [{"px": "113397.0", "sz": "0.11543", "n": 3}],
        ],
    }


def _predicted_fundings_payload(
    *,
    coin: str = "BTC",
    venue_entries: list[Any] | None = None,
    next_funding_time: Any = NEXT_FUNDING_MS,
) -> list[Any]:
    entries = venue_entries
    if entries is None:
        entries = [
            [
                "HlPerp",
                {
                    "fundingRate": "0.0000125",
                    "nextFundingTime": next_funding_time,
                },
            ]
        ]
    return [[coin, entries]]


def _adapter(fake_api: FakeHyperliquidInfoAPI) -> HyperliquidObservationAdapter:
    return HyperliquidObservationAdapter(post_info_json=fake_api)


def test_fetch_observation_normalizes_public_hyperliquid_market_data_only() -> None:
    fake_api = FakeHyperliquidInfoAPI()

    observation = _adapter(fake_api).fetch_observation("BTC")

    assert fake_api.calls == [
        {"type": "metaAndAssetCtxs"},
        {"type": "l2Book", "coin": "BTC"},
        {"type": "predictedFundings"},
    ]
    assert observation.venue == "Hyperliquid"
    assert observation.symbol == "BTC"
    assert observation.observed_at == datetime(2025, 8, 6, 3, 29, 34, 231000, tzinfo=UTC)
    assert observation.funding_settlement_at == datetime(2026, 8, 12, 7, 0, tzinfo=UTC)
    assert observation.order_book.venue == "Hyperliquid"
    assert observation.order_book.symbol == "BTC"
    assert observation.order_book.bids[0].price == Decimal("113377.0")
    assert observation.order_book.bids[0].size == Decimal("7.6699")
    assert observation.order_book.asks[0].price == Decimal("113397.0")
    assert observation.order_book.asks[0].size == Decimal("0.11543")
    assert observation.expected_funding_usd.value is None
    assert observation.expected_funding_usd.source is ValueSource.UNKNOWN
    assert observation.expected_funding_usd.metadata == {
        "public_funding_rate": "0.0000125",
        "public_funding_rate_field": "fundingRate",
        "public_funding_rate_source": "OBSERVED",
    }
    assert len(observation.fees.components) == 1
    assert observation.fees.components[0].amount_usd.value is None
    assert observation.fees.components[0].amount_usd.source is ValueSource.UNKNOWN


def test_fetch_observation_accepts_perp_suffix_when_hyperliquid_coin_matches_base() -> None:
    fake_api = FakeHyperliquidInfoAPI()

    observation = _adapter(fake_api).fetch_observation("BTC-PERP")

    assert observation.symbol == "BTC"
    assert observation.order_book.symbol == "BTC"


def test_fetch_observation_fails_closed_when_symbol_is_empty() -> None:
    fake_api = FakeHyperliquidInfoAPI()

    with pytest.raises(ValueError, match="symbol must be non-empty"):
        _adapter(fake_api).fetch_observation(" ")

    assert fake_api.calls == []


@pytest.mark.parametrize(
    ("meta_payload", "message"),
    (
        ({"not": "a list"}, r"\[meta, asset_contexts\]"),
        ([{"universe": []}], r"\[meta, asset_contexts\]"),
        (["not-meta", []], "meta object"),
        ([{}, []], "universe list"),
        ([{"universe": []}, "not-contexts"], "asset contexts list"),
        ([{"universe": [_market()]}, []], "align with universe"),
        ([{"universe": ["not-a-market"]}, [_asset_context()]], "malformed market"),
        ([{"universe": [{"szDecimals": 5}]}, [_asset_context()]], "requires name"),
        ([{"universe": [_market()]}, ["not-context"]], "asset context must be an object"),
        (_meta_payload(universe=[_market(is_delisted=True)]), "market is delisted"),
    ),
)
def test_fetch_observation_fails_closed_on_malformed_meta_and_asset_contexts(
    meta_payload: Any,
    message: str,
) -> None:
    fake_api = FakeHyperliquidInfoAPI(meta_payload=meta_payload)

    with pytest.raises(ValueError, match=message):
        _adapter(fake_api).fetch_observation("BTC")

    assert fake_api.calls == [{"type": "metaAndAssetCtxs"}]


def test_fetch_observation_fails_closed_when_market_is_missing() -> None:
    fake_api = FakeHyperliquidInfoAPI(
        meta_payload=_meta_payload(
            universe=[_market("ETH")],
            asset_contexts=[_asset_context()],
        )
    )

    with pytest.raises(ValueError, match="market not found"):
        _adapter(fake_api).fetch_observation("BTC")


def test_fetch_observation_fails_closed_when_market_lookup_is_ambiguous() -> None:
    fake_api = FakeHyperliquidInfoAPI(
        meta_payload=_meta_payload(
            universe=[_market("BTC-PERP"), _market("BTC")],
            asset_contexts=[_asset_context(), _asset_context()],
        )
    )

    with pytest.raises(ValueError, match="ambiguous"):
        _adapter(fake_api).fetch_observation("BTC-PERP")


@pytest.mark.parametrize("funding_rate", (None, "not-a-rate", "NaN", "Infinity"))
def test_fetch_observation_keeps_malformed_hyperliquid_funding_rate_unknown(
    funding_rate: Any,
) -> None:
    funding_payload = {"nextFundingTime": NEXT_FUNDING_MS}
    if funding_rate is not None:
        funding_payload["fundingRate"] = funding_rate
    fake_api = FakeHyperliquidInfoAPI(
        predicted_fundings_payload=_predicted_fundings_payload(
            venue_entries=[["HlPerp", funding_payload]]
        )
    )

    observation = _adapter(fake_api).fetch_observation("BTC")

    assert observation.expected_funding_usd.value is None
    assert observation.expected_funding_usd.source is ValueSource.UNKNOWN
    assert observation.expected_funding_usd.metadata == {}


@pytest.mark.parametrize(
    ("orderbook_payload", "message"),
    (
        (["not", "an", "object"], "object payload"),
        (_orderbook_payload(coin=None), "requires coin"),
        (_orderbook_payload(coin="ETH"), "coin must match selected market"),
        (_orderbook_payload(time=None), "l2Book.time is required"),
        (_orderbook_payload(time="not-a-timestamp"), "Unix millisecond"),
        (_orderbook_payload(time=0), "l2Book.time must be positive"),
        ({"coin": "BTC", "time": OBSERVED_AT_MS}, "bid and ask levels"),
        ({"coin": "BTC", "time": OBSERVED_AT_MS, "levels": [[]]}, "bid and ask levels"),
        (_orderbook_payload(bids=[]), "non-empty bids"),
        (_orderbook_payload(bids=[{"px": "0", "sz": "1"}]), "bids.px must be positive"),
        (_orderbook_payload(asks=[{"px": "1", "sz": "-1"}]), "asks.sz must be positive"),
        (
            _orderbook_payload(asks=[{"px": "not-a-price", "sz": "1"}]),
            "asks.px must be a Decimal string",
        ),
    ),
)
def test_fetch_observation_fails_closed_on_malformed_l2_book(
    orderbook_payload: Any,
    message: str,
) -> None:
    fake_api = FakeHyperliquidInfoAPI(orderbook_payload=orderbook_payload)

    with pytest.raises(ValueError, match=message):
        _adapter(fake_api).fetch_observation("BTC")

    assert fake_api.calls == [
        {"type": "metaAndAssetCtxs"},
        {"type": "l2Book", "coin": "BTC"},
    ]


@pytest.mark.parametrize(
    ("predicted_fundings_payload", "message"),
    (
        ({"not": "a list"}, "response requires a list"),
        ([["BTC"]], "malformed coin entry"),
        ([[None, []]], "coin entry requires coin"),
        ([["BTC", "not-venues"]], "coin entry requires venues"),
        ([["ETH", []]], "predicted funding not found"),
        ([["BTC", []], ["BTC", []]], "ambiguous"),
        ([["BTC", ["not-venue"]]], "malformed venue entry"),
        ([["BTC", [[None, {}]]]], "venue entry requires venue"),
        ([["BTC", [["HlPerp", "not-object"]]]], "requires an object"),
        ([["BTC", [["BinPerp", {"nextFundingTime": NEXT_FUNDING_MS}]]]], "HlPerp"),
        (
            [["BTC", [["HlPerp", {"nextFundingTime": NEXT_FUNDING_MS}], ["HlPerp", {"nextFundingTime": NEXT_FUNDING_MS}]]]],
            "ambiguous",
        ),
        (_predicted_fundings_payload(next_funding_time=None), "nextFundingTime is required"),
        (_predicted_fundings_payload(next_funding_time="not-a-timestamp"), "Unix millisecond"),
        (_predicted_fundings_payload(next_funding_time=0), "nextFundingTime must be positive"),
    ),
)
def test_fetch_observation_fails_closed_on_malformed_predicted_funding(
    predicted_fundings_payload: Any,
    message: str,
) -> None:
    fake_api = FakeHyperliquidInfoAPI(
        predicted_fundings_payload=predicted_fundings_payload
    )

    with pytest.raises(ValueError, match=message):
        _adapter(fake_api).fetch_observation("BTC")

    assert fake_api.calls == [
        {"type": "metaAndAssetCtxs"},
        {"type": "l2Book", "coin": "BTC"},
        {"type": "predictedFundings"},
    ]
