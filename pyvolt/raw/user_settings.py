from __future__ import annotations

import typing

UserSettings = dict[str, tuple[int, str]]


class OptionsFetchSettings(typing.TypedDict):
    keys: list[str]


class OptionsSetSettings(typing.TypedDict):
    timestamp: typing.NotRequired[int]


DataSetSettings = dict[str, str]


# Android User Settings
AndroidTheme = typing.Literal["Revolt", "Light", "Amoled", "None", "M3Dynamic"]
AndroidProfilePictureShape = int
AndroidMessageReplyStyle = typing.Literal["None", "SwipeFromEnd", "DoubleTap"]


class AndroidUserSettings(typing.TypedDict):
    theme: typing.NotRequired[AndroidTheme]
    colourOverrides: typing.NotRequired[dict[str, int]]
    # If not provided, defaults to SwipeFromEnd
    messageReplyStyle: typing.NotRequired[AndroidMessageReplyStyle]
    # If not provided, defaults to 50
    avatarRadius: typing.NotRequired[AndroidProfilePictureShape]


__all__ = (
    "UserSettings",
    "OptionsFetchSettings",
    "OptionsSetSettings",
    "DataSetSettings",
    "AndroidTheme",
    "AndroidProfilePictureShape",
    "AndroidMessageReplyStyle",
    "AndroidUserSettings",
)
