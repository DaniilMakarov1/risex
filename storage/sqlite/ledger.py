"""Minimal SQLite-backed append-only ledger storage."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.accounting.ledger import (
    LedgerEvent,
    LedgerEventType,
    freeze_ledger_payload,
    ledger_payload_to_jsonable,
)
from core.domain.contracts import validate_timezone_aware_datetime


class SQLiteLedger:
    """Append-only SQLite implementation of the accounting ledger contract."""

    def __init__(self, path: str | Path) -> None:
        self._connection = sqlite3.connect(str(path))
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS ledger_events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                recorded_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def append(
        self,
        *,
        event_type: str | LedgerEventType,
        payload: Mapping[str, Any],
        recorded_at: datetime | None = None,
    ) -> LedgerEvent:
        event_recorded_at = recorded_at or datetime.now(UTC)
        validate_timezone_aware_datetime(event_recorded_at, "recorded_at")
        event_type_value = event_type.value if isinstance(event_type, LedgerEventType) else str(event_type)
        payload_json = json.dumps(
            ledger_payload_to_jsonable(payload),
            sort_keys=True,
            separators=(",", ":"),
        )
        with self._connection:
            cursor = self._connection.execute(
                """
                INSERT INTO ledger_events (event_type, recorded_at, payload_json)
                VALUES (?, ?, ?)
                """,
                (event_type_value, event_recorded_at.isoformat(), payload_json),
            )
        return LedgerEvent(
            sequence=int(cursor.lastrowid),
            event_type=event_type_value,
            payload=payload,
            recorded_at=event_recorded_at,
        )

    def records(self) -> tuple[LedgerEvent, ...]:
        rows = self._connection.execute(
            """
            SELECT sequence, event_type, recorded_at, payload_json
            FROM ledger_events
            ORDER BY sequence
            """
        ).fetchall()
        return tuple(
            LedgerEvent(
                sequence=int(sequence),
                event_type=str(event_type),
                recorded_at=datetime.fromisoformat(str(recorded_at)),
                payload=freeze_ledger_payload(json.loads(str(payload_json))),
            )
            for sequence, event_type, recorded_at, payload_json in rows
        )

    def close(self) -> None:
        self._connection.close()
