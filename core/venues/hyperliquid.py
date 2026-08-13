"""Read-only Hyperliquid market-data adapter."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.request import Request, urlopen

from core.domain.contracts import (
    EstimatedValue,
    FeeComponent,
    FeeModel,
    OrderBook,
    OrderBookLevel,
    VenueObservation,
)
from core.domain.enums import ValueSource


class HyperliquidObservationAdapter:
    """Fetch and normalize one read-only Hyperliquid venue observation."""

    name = "Hyperliquid"

    def __init__(
        self,
        *,
        base_url: str = "https://api.hyperliquid.xyz",
        post_info_json: Callable[[Mapping[str, Any]], Any] | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._post_info_json = post_info_json

    def fetch_observation(self, symbol: str) -> VenueObservation:
        """Fetch and normalize one Hyperliquid observation for one requested symbol."""

        requested_symbol = _normalize_requested_symbol(symbol)
        coin = _select_coin(
            self._post_info({"type": "metaAndAssetCtxs"}),
            requested_symbol,
        )
        order_book, observed_at = _parse_order_book(
            self._post_info({"type": "l2Book", "coin": coin}),
            symbol=coin,
        )
        funding_settlement_at, funding_metadata = _parse_predicted_funding(
            self._post_info({"type": "predictedFundings"}),
            coin=coin,
        )

        return VenueObservation(
            venue=self.name,
            symbol=coin,
            observed_at=observed_at,
            order_book=order_book,
            expected_funding_usd=EstimatedValue(
                value=None,
                source=ValueSource.UNKNOWN,
                description=(
                    "Hyperliquid public market data exposes funding rates, "
                    "not notional-specific funding cash flow."
                ),
                metadata=funding_metadata,
            ),
            funding_settlement_at=funding_settlement_at,
            fees=FeeModel(
                components=(
                    FeeComponent(
                        name="hyperliquid_fee_cash_flow_unknown",
                        amount_usd=EstimatedValue(
                            value=None,
                            source=ValueSource.UNKNOWN,
                            description=(
                                "Hyperliquid fees are schedule and account-tier based, "
                                "not a per-observation USD cash value."
                            ),
                        ),
                    ),
                )
            ),
        )

    def _post_info(self, body: Mapping[str, Any]) -> Any:
        if self._post_info_json is not None:
            return self._post_info_json(dict(body))

        request = Request(
            f"{self._base_url}/info",
            data=json.dumps(dict(body)).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=10) as response:
            return json.load(response)


def _normalize_requested_symbol(symbol: str) -> str:
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("symbol must be non-empty")
    return symbol.strip()


def _coin_candidates(symbol: str) -> tuple[str, ...]:
    candidates = [symbol]
    if symbol.endswith("-PERP"):
        candidates.append(symbol.removesuffix("-PERP"))
    return tuple(dict.fromkeys(candidates))


def _select_coin(payload: Any, requested_symbol: str) -> str:
    if not isinstance(payload, list) or len(payload) != 2:
        raise ValueError("Hyperliquid metaAndAssetCtxs response requires [meta, asset_contexts]")

    meta, asset_contexts = payload
    if not isinstance(meta, Mapping):
        raise ValueError("Hyperliquid metaAndAssetCtxs response requires a meta object")
    universe = meta.get("universe")
    if not isinstance(universe, list):
        raise ValueError("Hyperliquid metaAndAssetCtxs response requires a universe list")
    if not isinstance(asset_contexts, list):
        raise ValueError("Hyperliquid metaAndAssetCtxs response requires an asset contexts list")
    if len(asset_contexts) != len(universe):
        raise ValueError("Hyperliquid asset contexts must align with universe")

    candidates = set(_coin_candidates(requested_symbol))
    matches: list[str] = []
    for index, market in enumerate(universe):
        if not isinstance(market, Mapping):
            raise ValueError("Hyperliquid universe contains a malformed market")
        raw_name = market.get("name")
        if not isinstance(raw_name, str) or not raw_name.strip():
            raise ValueError("Hyperliquid market requires name")
        context = asset_contexts[index]
        if not isinstance(context, Mapping):
            raise ValueError("Hyperliquid asset context must be an object")
        coin = raw_name.strip()
        if coin in candidates:
            if market.get("isDelisted") is True:
                raise ValueError("Hyperliquid market is delisted")
            matches.append(coin)

    if not matches:
        raise ValueError(f"Hyperliquid market not found for symbol {requested_symbol}")
    if len(matches) > 1:
        raise ValueError(f"Hyperliquid market lookup is ambiguous for symbol {requested_symbol}")
    return matches[0]


def _parse_epoch_milliseconds(raw_value: Any, field_name: str) -> datetime:
    if raw_value is None:
        raise ValueError(f"Hyperliquid {field_name} is required")
    try:
        timestamp_ms = int(str(raw_value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Hyperliquid {field_name} must be a Unix millisecond timestamp") from exc
    if timestamp_ms <= 0:
        raise ValueError(f"Hyperliquid {field_name} must be positive")

    seconds, milliseconds = divmod(timestamp_ms, 1000)
    return datetime.fromtimestamp(seconds, tz=UTC).replace(
        microsecond=milliseconds * 1000
    )


def _parse_positive_decimal(raw_value: Any, field_name: str) -> Decimal:
    if raw_value is None:
        raise ValueError(f"Hyperliquid {field_name} is required")
    try:
        value = Decimal(str(raw_value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Hyperliquid {field_name} must be a Decimal string") from exc
    if not value.is_finite() or value <= Decimal("0"):
        raise ValueError(f"Hyperliquid {field_name} must be positive")
    return value


def _parse_finite_decimal(raw_value: Any) -> Decimal | None:
    if raw_value is None:
        return None
    try:
        value = Decimal(str(raw_value))
    except (InvalidOperation, ValueError):
        return None
    if not value.is_finite():
        return None
    return value


def _parse_levels(raw_levels: Any, side: str) -> tuple[OrderBookLevel, ...]:
    if not isinstance(raw_levels, list) or not raw_levels:
        raise ValueError(f"Hyperliquid l2Book requires non-empty {side}")

    levels: list[OrderBookLevel] = []
    for raw_level in raw_levels:
        if not isinstance(raw_level, Mapping):
            raise ValueError(f"Hyperliquid l2Book {side} contains a malformed level")
        levels.append(
            OrderBookLevel(
                price=_parse_positive_decimal(raw_level.get("px"), f"{side}.px"),
                size=_parse_positive_decimal(raw_level.get("sz"), f"{side}.sz"),
            )
        )
    return tuple(levels)


def _parse_order_book(payload: Any, *, symbol: str) -> tuple[OrderBook, datetime]:
    if not isinstance(payload, Mapping):
        raise ValueError("Hyperliquid l2Book response requires an object payload")
    raw_coin = payload.get("coin")
    if not isinstance(raw_coin, str) or not raw_coin.strip():
        raise ValueError("Hyperliquid l2Book requires coin")
    if raw_coin.strip() != symbol:
        raise ValueError("Hyperliquid l2Book coin must match selected market")

    levels = payload.get("levels")
    if not isinstance(levels, list) or len(levels) != 2:
        raise ValueError("Hyperliquid l2Book requires bid and ask levels")

    return (
        OrderBook(
            venue=HyperliquidObservationAdapter.name,
            symbol=symbol,
            bids=_parse_levels(levels[0], "bids"),
            asks=_parse_levels(levels[1], "asks"),
        ),
        _parse_epoch_milliseconds(payload.get("time"), "l2Book.time"),
    )


def _parse_predicted_funding(payload: Any, *, coin: str) -> tuple[datetime, dict[str, str]]:
    if not isinstance(payload, list):
        raise ValueError("Hyperliquid predictedFundings response requires a list")

    matching_coin_entries = []
    for raw_coin_entry in payload:
        if not isinstance(raw_coin_entry, list) or len(raw_coin_entry) != 2:
            raise ValueError("Hyperliquid predictedFundings contains a malformed coin entry")
        raw_coin, raw_venues = raw_coin_entry
        if not isinstance(raw_coin, str) or not raw_coin.strip():
            raise ValueError("Hyperliquid predictedFundings coin entry requires coin")
        if not isinstance(raw_venues, list):
            raise ValueError("Hyperliquid predictedFundings coin entry requires venues")
        if raw_coin.strip() == coin:
            matching_coin_entries.append(raw_venues)

    if not matching_coin_entries:
        raise ValueError(f"Hyperliquid predicted funding not found for coin {coin}")
    if len(matching_coin_entries) > 1:
        raise ValueError(f"Hyperliquid predicted funding lookup is ambiguous for coin {coin}")

    hyperliquid_entries = []
    for raw_venue_entry in matching_coin_entries[0]:
        if not isinstance(raw_venue_entry, list) or len(raw_venue_entry) != 2:
            raise ValueError("Hyperliquid predictedFundings contains a malformed venue entry")
        raw_venue_name, raw_funding = raw_venue_entry
        if not isinstance(raw_venue_name, str):
            raise ValueError("Hyperliquid predictedFundings venue entry requires venue")
        if raw_venue_name == "HlPerp":
            if not isinstance(raw_funding, Mapping):
                raise ValueError("Hyperliquid HlPerp predicted funding requires an object")
            hyperliquid_entries.append(raw_funding)

    if not hyperliquid_entries:
        raise ValueError(f"Hyperliquid HlPerp predicted funding not found for coin {coin}")
    if len(hyperliquid_entries) > 1:
        raise ValueError(f"Hyperliquid HlPerp predicted funding is ambiguous for coin {coin}")
    funding_payload = hyperliquid_entries[0]
    funding_settlement_at = _parse_epoch_milliseconds(
        funding_payload.get("nextFundingTime"),
        "nextFundingTime",
    )
    funding_rate = _parse_finite_decimal(funding_payload.get("fundingRate"))
    if funding_rate is None:
        return funding_settlement_at, {}
    return funding_settlement_at, {
        "public_funding_rate": str(funding_rate),
        "public_funding_rate_field": "fundingRate",
        "public_funding_rate_source": ValueSource.OBSERVED.value,
    }
