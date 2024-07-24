from __future__ import annotations

import typing

from . import core
from .user_settings import UserSettings
from .user import UserBadges, UserFlags, RelationshipStatus, User

if typing.TYPE_CHECKING:
    from .cache import Cache
    from .cdn import CDNClient
    from .channel import SavedMessagesChannel
    from .http import HTTPClient
    from .parser import Parser
    from .shard import Shard
    from .user import OwnUser


class State:
    __slots__ = (
        '_cache',
        '_cdn_client',
        '_http',
        '_parser',
        '_shard',
        '_me',
        '_saved_notes',
        '_settings',
        'system',
    )

    def __init__(
        self,
        *,
        cache: Cache | None = None,
        cdn_client: CDNClient | None = None,
        http: HTTPClient | None = None,
        parser: Parser | None = None,
        shard: Shard | None = None,
    ) -> None:
        self._cache = cache
        self._cdn_client = cdn_client
        self._http = http
        self._parser = parser
        self._shard = shard
        self._me: OwnUser | None = None
        self._saved_notes: SavedMessagesChannel | None = None
        self._settings: UserSettings | None = None
        self.system = User(
            state=self,
            id=core.ZID,
            name='Revolt',
            discriminator='0000',
            internal_avatar=None,
            display_name=None,
            badges=UserBadges.NONE,
            status=None,
            flags=UserFlags.NONE,
            privileged=True,
            bot=None,
            relationship=RelationshipStatus.none,
            online=True,
        )

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
            self._parser = parser
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
    def parser(self) -> Parser:
        assert self._parser, 'State has no parser attached'
        return self._parser

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
