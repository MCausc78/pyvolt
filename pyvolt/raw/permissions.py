from __future__ import annotations

import typing as t


class Override(t.TypedDict):
    allow: int
    deny: int


class OverrideField(t.TypedDict):
    a: int
    d: int


__all__ = ("Override", "OverrideField")
