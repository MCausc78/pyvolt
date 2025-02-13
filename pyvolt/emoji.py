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

import typing

from attrs import define, field

from .base import Base
from .cdn import AssetMetadata, Asset
from .enums import AssetMetadataType


@define(slots=True)
class BaseEmoji(Base):
    """Represents an emoji on Revolt."""

    creator_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The user's ID who uploaded this emoji."""

    name: str = field(repr=True, kw_only=True)
    """:class:`str`: The emoji's name."""

    animated: bool = field(repr=True, kw_only=True)
    """:class:`bool`: Whether the emoji is animated."""

    nsfw: bool = field(repr=True, kw_only=True)
    """:class:`bool`: Whether the emoji is marked as NSFW."""

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, BaseEmoji) and self.id == other.id

    def __str__(self) -> str:
        return f':{self.id}:'

    @property
    def image(self) -> Asset:
        """:class:`.Asset`: The emoji asset."""
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
    """Represents an emoji in Revolt :class:`.Server`."""

    server_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The server's ID the emoji belongs to."""

    async def delete(self) -> None:
        """|coro|

        Deletes a emoji.

        You must have :attr:`~Permissions.manage_customization` to do this if you do not own
        the emoji, unless it was detached (already deleted).

        .. note::
            If deleting detached emoji, this will successfully return.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +-----------+-------------------------------------------+
            | Value     | Reason                                    |
            +-----------+-------------------------------------------+
            | ``IsBot`` | The current token belongs to bot account. |
            +-----------+-------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------------------+-----------------------------------------------------------+
            | Value                            | Reason                                                    |
            +----------------------------------+-----------------------------------------------------------+
            | ``MissingPermission``            | You do not have the proper permissions to delete a emoji. |
            +----------------------------------+-----------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+---------------------------------+
            | Value        | Reason                          |
            +--------------+---------------------------------+
            | ``NotFound`` | The emoji/server was not found. |
            +--------------+---------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """
        return await self.state.http.delete_emoji(self.id)


@define(slots=True)
class DetachedEmoji(BaseEmoji):
    """Represents a deleted emoji on Revolt."""


Emoji = typing.Union[ServerEmoji, DetachedEmoji]
ResolvableEmoji = typing.Union[BaseEmoji, str]


def resolve_emoji(resolvable: ResolvableEmoji, /) -> str:
    """:class:`str`: Resolves emoji's ID from parameter.

    Parameters
    ----------
    resolvable: :class:`.ResolvableEmoji`
        The object to resolve ID from.

    Returns
    -------
    :class:`str`
        The resolved emoji's ID.
    """
    return resolvable.id if isinstance(resolvable, BaseEmoji) else resolvable


__all__ = (
    'BaseEmoji',
    'ServerEmoji',
    'DetachedEmoji',
    'Emoji',
    'ResolvableEmoji',
    'resolve_emoji',
)
