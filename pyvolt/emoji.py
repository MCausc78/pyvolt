from __future__ import annotations

from attrs import define, field

from . import core
from .base import Base


@define(slots=True)
class BaseEmoji(Base):
    """Representation of an emoji on Revolt."""

    id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    """Unique emoji ID."""

    creator_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    """Uploader user ID."""

    name: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """Emoji name."""

    animated: bool = field(repr=True, hash=True, kw_only=True, eq=True)
    """Whether the emoji is animated."""

    nsfw: bool = field(repr=True, hash=True, kw_only=True, eq=True)
    """Whether the emoji is marked as NSFW."""


@define(slots=True)
class ServerEmoji(BaseEmoji):
    """Representation of an emoji in server on Revolt."""

    server_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    """What server owns this emoji."""


@define(slots=True)
class DetachedEmoji(BaseEmoji):
    """Representation of an deleted emoji on Revolt."""


Emoji = ServerEmoji | DetachedEmoji
ResolvableEmoji = Emoji | str


def resolve_emoji(resolvable: ResolvableEmoji) -> str:
    return str(
        resolvable.id
        if isinstance(resolvable, (ServerEmoji, DetachedEmoji))
        else resolvable
    )


__all__ = (
    "BaseEmoji",
    "ServerEmoji",
    "DetachedEmoji",
    "Emoji",
    "ResolvableEmoji",
    "resolve_emoji",
)
