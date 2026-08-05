from dataclasses import fields

from core.economics.ev import EntryEV


def test_entry_ev_does_not_require_expected_basis_change() -> None:
    assert "expected_basis_change" not in {field.name for field in fields(EntryEV)}
