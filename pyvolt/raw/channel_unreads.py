from __future__ import annotations

import typing as t


class ChannelUnread(t.TypedDict):
    _id: ChannelCompositeKey
    last_id: t.NotRequired[str]
    mentions: t.NotRequired[list[str]]


class ChannelCompositeKey(t.TypedDict):
    channel: str
    user: str


__all__ = ("ChannelUnread", "ChannelCompositeKey")
