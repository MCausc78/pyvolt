from __future__ import annotations

import typing as t

UserSettings = dict[str, tuple[int, str]]


class OptionsFetchSettings(t.TypedDict):
    keys: list[str]


class OptionsSetSettings(t.TypedDict):
    timestamp: t.NotRequired[int]


DataSetSettings = dict[str, str]

__all__ = (
    "UserSettings",
    "OptionsFetchSettings",
    "OptionsSetSettings",
    "DataSetSettings",
)
