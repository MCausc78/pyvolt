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
from pyvolt import BaseCacheContext, Server

if typing.TYPE_CHECKING:
    from .bot import Bot
    from .context import Context


@define(slots=True)
class CommandsCacheContext(BaseCacheContext):
    """Represents a cache context related to commands extension."""


@define(slots=True)
class MemberConverterCacheContext(CommandsCacheContext):
    """Represents a cache context that was created in :class:`MemberConverter`."""

    argument: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """:class:`str`: The argument."""

    context: Context[Bot] = field(repr=True, hash=True, kw_only=True, eq=True)
    """:class:`Context`: The context."""

    server: Server = field(repr=True, hash=True, kw_only=True, eq=True)
    """:class:`.Server`: The server the lookup was done in."""


@define(slots=True)
class UserConverterCacheContext(CommandsCacheContext):
    """Represents a cache context that was created in :class:`UserConverter`."""

    argument: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """:class:`str`: The argument."""

    context: Context[Bot] = field(repr=True, hash=True, kw_only=True, eq=True)
    """:class:`Context`: The context."""


@define(slots=True)
class ServerConverterCacheContext(CommandsCacheContext):
    """Represents a cache context that was created in :class:`ServerConverter`."""

    argument: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """:class:`str`: The argument."""

    context: Context[Bot] = field(repr=True, hash=True, kw_only=True, eq=True)
    """:class:`Context`: The context."""


@define(slots=True)
class MessageConverterCacheContext(CommandsCacheContext):
    """Represents a cache context that was created in :meth:`MessageConverter.convert`."""

    argument: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """:class:`str`: The argument."""

    context: Context[Bot] = field(repr=True, hash=True, kw_only=True, eq=True)
    """:class:`Context`: The context."""

    server_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """:class:`str`: The server's ID the message is in. May be empty or not exist."""


@define(slots=True)
class BaseServerChannelConverterCacheContext(CommandsCacheContext):
    """Represents a cache context that was created in :meth:`ServerChannelConverter.convert`, :meth:`TextChannelConverter.convert`, or :meth:`VoiceChannelConverter.convert`."""

    argument: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """:class:`str`: The argument."""

    context: Context[Bot] = field(repr=True, hash=True, kw_only=True, eq=True)
    """:class:`Context`: The context."""

    server_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """:class:`str`: The server's ID. May be empty."""


@define(slots=True)
class ServerChannelConverterCacheContext(BaseServerChannelConverterCacheContext):
    """Represents a cache context that was created in :meth:`ServerChannelConverter.convert`."""


@define(slots=True)
class TextChannelConverterCacheContext(BaseServerChannelConverterCacheContext):
    """Represents a cache context that was created in :meth:`TextChannelConverter.convert`."""


@define(slots=True)
class VoiceChannelConverterCacheContext(BaseServerChannelConverterCacheContext):
    """Represents a cache context that was created in :meth:`VoiceChannelConverter.convert`."""


@define(slots=True)
class EmojiConverterCacheContext(CommandsCacheContext):
    """Represents a cache context that was created in :meth:`EmojiConverter.convert`."""

    context: Context[Bot] = field(repr=True, hash=True, kw_only=True, eq=True)
    """:class:`Context`: The context."""

    argument: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """:class:`str`: The argument."""


__all__ = (
    'CommandsCacheContext',
    'MemberConverterCacheContext',
    'UserConverterCacheContext',
    'ServerConverterCacheContext',
    'MessageConverterCacheContext',
    'BaseServerChannelConverterCacheContext',
    'ServerChannelConverterCacheContext',
    'TextChannelConverterCacheContext',
    'VoiceChannelConverterCacheContext',
    'EmojiConverterCacheContext',
)
