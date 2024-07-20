from __future__ import annotations

import typing

UserSettings = dict[str, tuple[int, str]]


class OptionsFetchSettings(typing.TypedDict):
    keys: list[str]


class OptionsSetSettings(typing.TypedDict):
    timestamp: typing.NotRequired[int]


DataSetSettings = dict[str, str]

__all__ = (
    "UserSettings",
    "OptionsFetchSettings",
    "OptionsSetSettings",
    "DataSetSettings",
)
