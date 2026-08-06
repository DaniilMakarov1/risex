"""Scoped economics input/data exceptions."""

from __future__ import annotations


class EconomicsInputError(ValueError):
    """Expected missing or invalid economics input that must fail closed."""
