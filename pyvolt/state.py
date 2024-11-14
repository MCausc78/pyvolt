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

from .core import ZID
from .parser import Parser
from .user_settings import UserSettings
from .user import RelationshipStatus, User

if typing.TYPE_CHECKING:
    from .cache import ProvideCacheContextIn, Cache
    from .cdn import CDNClient
    from .channel import SavedMessagesChannel
    from .http import HTTPClient
    from .shard import Shard
    from .user import OwnUser


class State:
    """Represents a manager for all pyvolt objects.

    Attributes
    ----------
    provide_cache_context_in: List[:class:`ProvideCacheContextIn`]
        The methods/properties that do provide cache context.
    parser: :class:`Parser`
        The parser.
    system: :class:`User`
        The Revolt#0000 sentinel user.
    voice_url: :class:`str`
        The URL to voice server.
    """

    __slots__ = (
        '_cache',
        'provide_cache_context_in',
        '_cdn_client',
        '_http',
        'parser',
        '_shard',
        '_me',
        '_saved_notes',
        '_settings',
        'system',
        'voice_url',
    )

    def __init__(
        self,
        *,
        cache: Cache | None = None,
        provide_cache_context_in: list[ProvideCacheContextIn] | None = None,
        cdn_client: CDNClient | None = None,
        http: HTTPClient | None = None,
        parser: Parser | None = None,
        shard: Shard | None = None,
    ) -> None:
        self._cache = cache
        self.provide_cache_context_in: list[ProvideCacheContextIn] = provide_cache_context_in or []
        self._cdn_client = cdn_client
        self._http = http
        self.parser = parser if parser else Parser(state=self)
        self._shard = shard
        self._me: OwnUser | None = None
        self._saved_notes: SavedMessagesChannel | None = None
        self._settings: UserSettings | None = None
        self.system = User(
            state=self,
            id=ZID,
            name='Revolt',
            discriminator='0000',
            internal_avatar=None,
            display_name=None,
            raw_badges=0,
            status=None,
            raw_flags=0,
            privileged=True,
            bot=None,
            relationship=RelationshipStatus.none,
            online=True,
        )
        self.voice_url: str = ''

    def setup(
        self,
        *,
        cache: Cache | None = None,
        cdn_client: CDNClient | None = None,
        http: HTTPClient | None = None,
        parser: Parser | None = None,
        shard: Shard | None = None,
    ) -> State:
        if cache:
            self._cache = cache
        if cdn_client:
            self._cdn_client = cdn_client
        if http:
            self._http = http
        if parser:
            self.parser = parser
        if shard:
            self._shard = shard
        return self

    @property
    def cache(self) -> Cache | None:
        return self._cache

    @property
    def cdn_client(self) -> CDNClient:
        assert self._cdn_client, 'State has no CDN client attached'
        return self._cdn_client

    @property
    def http(self) -> HTTPClient:
        assert self._http, 'State has no HTTP client attached'
        return self._http

    @property
    def shard(self) -> Shard:
        assert self._shard, 'State has no shard attached'
        return self._shard

    @property
    def me(self) -> OwnUser | None:
        """Optional[:class:`OwnUser`]: The currently logged in user."""
        # assert self._me, "State has no current user attached"
        return self._me

    @property
    def saved_notes(self) -> SavedMessagesChannel | None:
        """Optional[:class:`SavedMessagesChannel`]: The Saved Notes channel."""
        return self._saved_notes

    @property
    def settings(self) -> UserSettings:
        """:class:`UserSettings`: The current user settings."""
        if self._settings:
            return self._settings
        self._settings = UserSettings(data={}, state=self, mocked=True, partial=True)
        return self._settings


__all__ = ('State',)
