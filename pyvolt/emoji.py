"""
The MIT License (MIT)

Copyright (c) 2024-present MCausc78

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

from attrs import define, field

from .base import Base
from .cdn import AssetMetadataType, AssetMetadata, Asset


@define(slots=True)
class BaseEmoji(Base):
    """Representation of an emoji on Revolt."""

    creator_id: str = field(repr=True, kw_only=True)
    """The user ID of the uploader."""

    name: str = field(repr=True, kw_only=True)
    """Emoji name."""

    animated: bool = field(repr=True, kw_only=True)
    """Whether the emoji is animated."""

    nsfw: bool = field(repr=True, kw_only=True)
    """Whether the emoji is marked as NSFW."""

    def __str__(self) -> str:
        return f':{self.id}:'

    @property
    def image(self) -> Asset:
        """:class:`Asset`: The emoji asset."""
        return Asset(
            id=self.id,
            filename='',
            metadata=AssetMetadata(
                type=AssetMetadataType.video if self.animated else AssetMetadataType.image,
                width=0,
                height=0,
            ),
            content_type='',
            size=0,
            deleted=False,
            reported=False,
            message_id=None,
            user_id=None,
            server_id=None,
            object_id=None,
            state=self.state,
            tag='emojis',
        )


@define(slots=True)
class ServerEmoji(BaseEmoji):
    """Representation of an emoji in server on Revolt."""

    server_id: str = field(repr=True, kw_only=True)
    """What server owns this emoji."""


@define(slots=True)
class DetachedEmoji(BaseEmoji):
    """Representation of an deleted emoji on Revolt."""


Emoji = ServerEmoji | DetachedEmoji
ResolvableEmoji = Emoji | str


def resolve_emoji(resolvable: ResolvableEmoji) -> str:
    return str(resolvable.id) if isinstance(resolvable, (ServerEmoji, DetachedEmoji)) else resolvable


__all__ = (
    'BaseEmoji',
    'ServerEmoji',
    'DetachedEmoji',
    'Emoji',
    'ResolvableEmoji',
    'resolve_emoji',
)
