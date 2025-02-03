from __future__ import annotations

import typing
import typing_extensions

T = typing.TypeVar('T')


class BaseEmoji(typing.Generic[T], typing.TypedDict):
    _id: str
    parent: T
    creator_id: str
    name: str
    animated: typing_extensions.NotRequired[bool]
    nsfw: typing_extensions.NotRequired[bool]


ServerEmoji = BaseEmoji['ServerEmojiParent']
DetachedEmoji = BaseEmoji['DetachedEmojiParent']
Emoji = BaseEmoji['EmojiParent']


class ServerEmojiParent(typing.TypedDict):
    type: typing.Literal['Server']
    id: str


class DetachedEmojiParent(typing.TypedDict):
    type: typing.Literal['Detached']


EmojiParent = typing.Union[ServerEmojiParent, DetachedEmojiParent]


class DataCreateEmoji(typing.TypedDict):
    name: str
    parent: EmojiParent
    nsfw: typing_extensions.NotRequired[bool]
