"""Read-only RISEx market-data adapter."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

from core.domain.contracts import (
    EstimatedValue,
    FeeComponent,
    FeeModel,
    OrderBook,
    OrderBookLevel,
    VenueObservation,
)
from core.domain.enums import ValueSource


class RiseXObservationAdapter:
    """Fetch and normalize one read-only RISEx venue observation."""

    name = "RiseX"

    def __init__(
        self,
        *,
        base_url: str = "https://api.testnet.rise.trade",
        orderbook_limit: int = 50,
        fetch_json: Callable[[str, Mapping[str, str]], Mapping[str, Any]] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if orderbook_limit <= 0:
            raise ValueError("orderbook_limit must be positive")
        self._base_url = base_url.rstrip("/")
        self._orderbook_limit = orderbook_limit
        self._fetch_json = fetch_json
        self._clock = clock or (lambda: datetime.now(UTC))

    def fetch_observation(self, symbol: str) -> VenueObservation:
        """Fetch and normalize one RISEx observation for one requested symbol."""

        normalized_symbol = _normalize_requested_symbol(symbol)
        markets_payload = self._get_json("/v1/markets", {})
        market = _select_market(markets_payload, normalized_symbol)
        market_id = str(market["market_id"])
        funding_settlement_at = _parse_unix_nanoseconds(
            market.get("next_funding_time"),
            "next_funding_time",
        )

        orderbook_payload = self._get_json(
            "/v1/orderbook",
            {"market_id": market_id, "limit": str(self._orderbook_limit)},
        )
        order_book = _parse_order_book(orderbook_payload, symbol=normalized_symbol)

        return VenueObservation(
            venue=self.name,
            symbol=normalized_symbol,
            observed_at=self._clock(),
            order_book=order_book,
            expected_funding_usd=EstimatedValue(
                value=None,
                source=ValueSource.UNKNOWN,
                description=(
                    "RISEx public market data exposes funding rates, "
                    "not notional-specific funding cash flow."
                ),
            ),
            funding_settlement_at=funding_settlement_at,
            fees=FeeModel(
                components=(
                    FeeComponent(
                        name="risex_fee_cash_flow_unknown",
                        amount_usd=EstimatedValue(
                            value=None,
                            source=ValueSource.UNKNOWN,
                            description=(
                                "RISEx fee schedule is bps/account-tier based, "
                                "not a per-observation USD cash value."
                            ),
                        ),
                    ),
                )
            ),
        )

    def _get_json(self, path: str, params: Mapping[str, str]) -> Mapping[str, Any]:
        if self._fetch_json is not None:
            payload = self._fetch_json(path, dict(params))
            if not isinstance(payload, Mapping):
                raise ValueError("RISEx response must be a JSON object")
            return payload

        url = f"{self._base_url}{path}"
        if params:
            url = f"{url}?{urlencode(params)}"
        with urlopen(url, timeout=10) as response:
            payload = json.load(response)
        if not isinstance(payload, Mapping):
            raise ValueError("RISEx response must be a JSON object")
        return payload


def _normalize_requested_symbol(symbol: str) -> str:
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("symbol must be non-empty")
    return symbol.strip()


def _api_symbol_candidates(symbol: str) -> tuple[str, ...]:
    candidates = [symbol]
    if symbol.endswith("-PERP"):
        candidates.append(f"{symbol.removesuffix('-PERP')}/USDC")
    return tuple(dict.fromkeys(candidates))


def _data_object(payload: Mapping[str, Any], field_name: str) -> Mapping[str, Any]:
    data = payload.get("data", payload)
    if not isinstance(data, Mapping):
        raise ValueError(f"RISEx {field_name} response requires an object payload")
    return data


def _select_market(payload: Mapping[str, Any], symbol: str) -> Mapping[str, Any]:
    data = _data_object(payload, "markets")
    markets = data.get("markets")
    if not isinstance(markets, list):
        raise ValueError("RISEx markets response requires a markets list")

    candidates = set(_api_symbol_candidates(symbol))
    matches: list[Mapping[str, Any]] = []
    for market in markets:
        if not isinstance(market, Mapping):
            raise ValueError("RISEx markets response contains a malformed market")
        config = market.get("config")
        if not isinstance(config, Mapping):
            raise ValueError("RISEx market requires a config object")
        names = {
            str(config.get("name", "")),
            str(market.get("display_name", "")),
            str(market.get("underlying", "")),
        }
        if names & candidates:
            matches.append(market)

    if not matches:
        raise ValueError(f"RISEx market not found for symbol {symbol}")
    if len(matches) > 1:
        raise ValueError(f"RISEx market lookup is ambiguous for symbol {symbol}")
    market_id = matches[0].get("market_id")
    if market_id is None or str(market_id).strip() == "":
        raise ValueError("RISEx market requires market_id")
    return matches[0]


def _parse_unix_nanoseconds(raw_value: Any, field_name: str) -> datetime:
    if raw_value is None:
        raise ValueError(f"RISEx {field_name} is required")
    try:
        timestamp_ns = int(str(raw_value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"RISEx {field_name} must be a Unix nanosecond timestamp") from exc
    if timestamp_ns <= 0:
        raise ValueError(f"RISEx {field_name} must be positive")

    seconds, nanoseconds = divmod(timestamp_ns, 1_000_000_000)
    return datetime.fromtimestamp(seconds, tz=UTC).replace(
        microsecond=nanoseconds // 1000
    )


def _parse_positive_decimal(raw_value: Any, field_name: str) -> Decimal:
    if raw_value is None:
        raise ValueError(f"RISEx {field_name} is required")
    try:
        value = Decimal(str(raw_value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"RISEx {field_name} must be a Decimal string") from exc
    if not value.is_finite() or value <= Decimal("0"):
        raise ValueError(f"RISEx {field_name} must be positive")
    return value


def _parse_levels(raw_levels: Any, side: str) -> tuple[OrderBookLevel, ...]:
    if not isinstance(raw_levels, list) or not raw_levels:
        raise ValueError(f"RISEx orderbook requires non-empty {side}")

    levels: list[OrderBookLevel] = []
    for raw_level in raw_levels:
        if not isinstance(raw_level, Mapping):
            raise ValueError(f"RISEx orderbook {side} contains a malformed level")
        levels.append(
            OrderBookLevel(
                price=_parse_positive_decimal(raw_level.get("price"), f"{side}.price"),
                size=_parse_positive_decimal(
                    raw_level.get("quantity"),
                    f"{side}.quantity",
                ),
            )
        )
    return tuple(levels)


def _parse_order_book(payload: Mapping[str, Any], *, symbol: str) -> OrderBook:
    data = _data_object(payload, "orderbook")
    return OrderBook(
        venue=RiseXObservationAdapter.name,
        symbol=symbol,
        bids=_parse_levels(data.get("bids"), "bids"),
        asks=_parse_levels(data.get("asks"), "asks"),
    )
