from __future__ import annotations

import typing

T = typing.TypeVar("T")


class BaseEmoji(typing.Generic[T], typing.TypedDict):
    _id: str
    parent: T
    creator_id: str
    name: str
    animated: typing.NotRequired[bool]
    nsfw: typing.NotRequired[bool]


ServerEmoji = BaseEmoji["ServerEmojiParent"]
DetachedEmoji = BaseEmoji["DetachedEmojiParent"]
Emoji = BaseEmoji["EmojiParent"]


class ServerEmojiParent(typing.TypedDict):
    type: typing.Literal["Server"]
    id: str


class DetachedEmojiParent(typing.TypedDict):
    type: typing.Literal["Detached"]


EmojiParent = ServerEmojiParent | DetachedEmojiParent


class DataCreateEmoji(typing.TypedDict):
    name: str
    parent: EmojiParent
    nsfw: typing.NotRequired[bool]


__all__ = (
    "BaseEmoji",
    "ServerEmoji",
    "DetachedEmoji",
    "Emoji",
    "ServerEmojiParent",
    "DetachedEmojiParent",
    "EmojiParent",
    "DataCreateEmoji",
)
