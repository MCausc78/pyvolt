from __future__ import annotations

import typing
import typing_extensions


class ChannelUnread(typing.TypedDict):
    _id: ChannelCompositeKey
    last_id: typing_extensions.NotRequired[str]
    mentions: typing_extensions.NotRequired[list[str]]


class ChannelCompositeKey(typing.TypedDict):
    channel: str
    user: str
