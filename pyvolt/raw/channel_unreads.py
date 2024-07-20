from __future__ import annotations

import typing


class ChannelUnread(typing.TypedDict):
    _id: ChannelCompositeKey
    last_id: typing.NotRequired[str]
    mentions: typing.NotRequired[list[str]]


class ChannelCompositeKey(typing.TypedDict):
    channel: str
    user: str


__all__ = ("ChannelUnread", "ChannelCompositeKey")
