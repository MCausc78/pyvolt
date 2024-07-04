import typing as t

T = t.TypeVar("T")


class BaseEmoji(t.Generic[T], t.TypedDict):
    _id: str
    parent: T
    creator_id: str
    name: str
    animated: t.NotRequired[bool]
    nsfw: t.NotRequired[bool]


ServerEmoji = BaseEmoji["ServerEmojiParent"]
DetachedEmoji = BaseEmoji["DetachedEmojiParent"]
Emoji = BaseEmoji["EmojiParent"]


class ServerEmojiParent(t.TypedDict):
    type: t.Literal["Server"]
    id: str


class DetachedEmojiParent(t.TypedDict):
    type: t.Literal["Detached"]


EmojiParent = ServerEmojiParent | DetachedEmojiParent


class DataCreateEmoji(t.TypedDict):
    name: str
    parent: EmojiParent
    nsfw: t.NotRequired[bool]


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
