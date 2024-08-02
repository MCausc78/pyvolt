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

import aiohttp
from attrs import define, field
import logging
import typing

from . import utils
from .bot import BaseBot
from .cdn import StatelessAsset, Asset
from .core import UNDEFINED, UndefinedOr, __version__ as version
from .enums import ServerActivity, BotUsage, ReviteBaseTheme
from .errors import DiscoveryError
from .server import ServerFlags, BaseServer
from .state import State
from .user import StatelessUserProfile, UserProfile

if typing.TYPE_CHECKING:
    from . import raw
    from .user_settings import ReviteThemeVariable

_L = logging.getLogger(__name__)

DEFAULT_DISCOVERY_USER_AGENT = f'pyvolt Discovery client (https://github.com/MCausc78/pyvolt, {version})'


@define(slots=True)
class DiscoveryServer(BaseServer):
    """Representation of a server on Revolt Discovery. The ID is a invite code."""

    name: str = field(repr=True, kw_only=True)
    """The server name."""

    description: str | None = field(repr=True, kw_only=True)
    """The server description."""

    internal_icon: StatelessAsset | None = field(repr=True, kw_only=True)
    """The stateless server icon."""

    internal_banner: StatelessAsset | None = field(repr=True, kw_only=True)
    """The stateless server banner."""

    flags: ServerFlags = field(repr=True, kw_only=True)
    """The server flags."""

    tags: list[str] = field(repr=True, kw_only=True)
    """The server tags."""

    member_count: int = field(repr=True, kw_only=True)
    """The server member count."""

    activity: ServerActivity = field(repr=True, kw_only=True)
    """The server activity."""

    @property
    def icon(self) -> Asset | None:
        """Optional[:class:`Asset`]: The server icon."""
        return self.internal_icon and self.internal_icon._stateful(self.state, 'icons')

    @property
    def invite_code(self) -> str:
        """:class:`str`: The server invite code. As an implementation detail, right now it returns server ID, but don't depend on that in future."""
        return self.id

    @property
    def banner(self) -> Asset | None:
        """Optional[:class:`Asset`]: The server banner."""
        return self.internal_banner and self.internal_banner._stateful(self.state, 'banners')


@define(slots=True)
class DiscoveryServersPage:
    servers: list[DiscoveryServer] = field(repr=True, kw_only=True)
    """The listed servers, up to 200 servers."""

    popular_tags: list[str] = field(repr=True, kw_only=True)
    """Popular tags used in discovery servers."""


@define(slots=True)
class DiscoveryBot(BaseBot):
    name: str = field(repr=True, kw_only=True)
    """The bot's name."""

    internal_avatar: StatelessAsset | None = field(repr=True, kw_only=True)
    """The stateless bot's avatar."""

    internal_profile: StatelessUserProfile = field(repr=True, kw_only=True)
    """The stateless bot's profile."""

    tags: list[str] = field(repr=True, kw_only=True)
    """The bot's tags."""

    server_count: int = field(repr=True, kw_only=True)
    """The bot's servers count."""

    usage: BotUsage = field(repr=True, kw_only=True)
    """How frequently is bot being used."""

    @property
    def avatar(self) -> Asset | None:
        """Optional[:class:`Asset`]: The bot's avatar."""
        return self.internal_avatar and self.internal_avatar._stateful(self.state, 'avatars')

    @property
    def description(self) -> str:
        """:class:`str`: The bot's profile description."""
        return self.internal_profile.content or ''

    @property
    def profile(self) -> UserProfile:
        """:class:`UserProfile`: The bot's profile."""
        return self.internal_profile._stateful(self.state, self.id)


@define(slots=True)
class DiscoveryBotsPage:
    bots: list[DiscoveryBot] = field(repr=True, kw_only=True)
    """The listed bots, up to 200 bots."""

    popular_tags: list[str] = field(repr=True, kw_only=True)
    """Popular tags used in discovery bots."""


@define(slots=True)
class DiscoveryTheme:
    state: State = field(repr=False)
    """State that controls this theme."""

    name: str = field(repr=True, kw_only=True)
    """The theme name."""

    description: str = field(repr=True, kw_only=True)
    """The theme description."""

    creator: str = field(repr=True, kw_only=True)
    """The theme creator."""

    slug: str = field(repr=True, kw_only=True)
    """The theme slug."""

    tags: list[str] = field(repr=True, kw_only=True)
    """The theme tags."""

    overrides: dict[ReviteThemeVariable, str] = field(repr=True, kw_only=True)
    """The theme overrides in format `{css_class: css_color}`."""

    version: str = field(repr=True, kw_only=True)
    """The theme version."""

    custom_css: str | None = field(repr=True, kw_only=True)
    """The theme CSS string."""

    def __hash__(self) -> int:
        return hash((self.name, self.creator))

    def __eq__(self, other: object) -> bool:
        return (
            self is other
            or isinstance(other, DiscoveryTheme)
            and self.name == other.name
            and self.creator == other.creator
        )

    async def apply(self, *, base_theme: UndefinedOr[ReviteBaseTheme] = UNDEFINED) -> None:
        """|coro|

        Applies the theme to current user account.
        """
        await self.state.settings.revite.edit(
            overrides=self.overrides,
            base_theme=base_theme,
            custom_css=self.custom_css,
        )


@define(slots=True)
class DiscoveryThemesPage:
    themes: list[DiscoveryTheme] = field(
        repr=True,
        kw_only=True,
    )
    """The listed themes, up to 200 themes."""

    popular_tags: list[str] = field(repr=True, kw_only=True)
    """Popular tags used in discovery themes."""


# 'relatedTags' contains deduplicated tags, calculated with:
# ```py
# deduplicated_tags = []
# for o in page_props[page_props['type']]:
#  for tag in o['tags']:
#   if tag not in deduplicated_tags:
#    deduplicated_tags.append(tag)
# ```


@define(slots=True)
class ServerSearchResult:
    """The server search result object."""

    query: str = field(repr=True, kw_only=True)
    """The lower-cased query."""

    count: int = field(repr=True, kw_only=True)
    """The servers count."""

    servers: list[DiscoveryServer] = field(repr=True, kw_only=True)
    """The listed servers."""

    related_tags: list[str] = field(repr=True, kw_only=True)
    """All of tags that listed servers have."""


@define(slots=True)
class BotSearchResult:
    """The bot search result object."""

    query: str = field(repr=True, kw_only=True)
    """The lower-cased query."""

    count: int = field(repr=True, kw_only=True)
    """The bots count."""

    bots: list[DiscoveryBot] = field(repr=True, kw_only=True)
    """The listed bots."""

    related_tags: list[str] = field(repr=True, kw_only=True)
    """All of tags that listed bots have."""


@define(slots=True)
class ThemeSearchResult:
    """The theme search result object."""

    query: str = field(repr=True, kw_only=True)
    """The lower-cased query."""

    count: int = field(repr=True, kw_only=True)
    """The themes count."""

    themes: list[DiscoveryTheme] = field(repr=True, kw_only=True)
    """The listed themes."""

    related_tags: list[str] = field(repr=True, kw_only=True)
    """All of tags that listed themes have."""


class DiscoveryClient:
    __slots__ = (
        '_base',
        'session',
        'state',
    )

    def __init__(self, *, base: str | None = None, session: aiohttp.ClientSession, state: State) -> None:
        self._base = 'https://rvlt.gg/_next/data/OddIUaX26creykRzYdVYw/' if base is None else base.rstrip('/') + '/'
        self.session = session
        self.state = state

    async def _request(self, method: str, path: str, **kwargs) -> aiohttp.ClientResponse:
        _L.debug('sending %s to %s params=%s', method, path, kwargs.get('params'))
        headers = {'user-agent': DEFAULT_DISCOVERY_USER_AGENT}
        headers.update(kwargs.pop('headers', {}))
        response = await self.session.request(method, self._base + path.lstrip('/'), headers=headers, **kwargs)
        if response.status >= 400:
            body = await utils._json_or_text(response)
            raise DiscoveryError(response, response.status, body)
        return response

    async def request(self, method: str, path: str, **kwargs) -> typing.Any:
        response = await self._request(method, path, **kwargs)
        result = await utils._json_or_text(response)
        _L.debug('received from %s %s: %s', method, path, result)
        response.close()
        return result

    async def servers(self) -> DiscoveryServersPage:
        """|coro|

        Retrieves servers on a main page.

        Returns
        -------
        :class:`DiscoveryServersPage`
            The servers page.
        """
        page: raw.NextPage[raw.DiscoveryServersPage] = await self.request(
            'GET', '/discover/servers.json', params={'embedded': 'true'}
        )
        return self.state.parser.parse_discovery_servers_page(page['pageProps'])

    async def bots(self) -> DiscoveryBotsPage:
        """|coro|

        Retrieves bots on a main page.

        Returns
        -------
        :class:`DiscoveryBotsPage`
            The bots page.
        """

        page: raw.NextPage[raw.DiscoveryBotsPage] = await self.request(
            'GET', '/discover/bots.json', params={'embedded': 'true'}
        )

        return self.state.parser.parse_discovery_bots_page(page['pageProps'])

    async def themes(self) -> DiscoveryThemesPage:
        """|coro|

        Retrieves themes on a main page.

        Returns
        -------
        :class:`DiscoveryThemesPage`
            The themes page.
        """
        page: raw.NextPage[raw.DiscoveryThemesPage] = await self.request(
            'GET', '/discover/themes.json', params={'embedded': 'true'}
        )
        return self.state.parser.parse_discovery_themes_page(page['pageProps'])

    async def search_servers(self, query: str) -> ServerSearchResult:
        """|coro|

        Searches for servers.

        Parameters
        ----------
        query: :class:`str`
            The query to search for.

        Returns
        -------
        :class:`ServerSearchResult`
            The search results.
        """
        page: raw.NextPage[raw.DiscoveryServerSearchResult] = await self.request(
            'GET',
            '/discover/search.json',
            params={
                'embedded': 'true',
                'query': query,
                'type': 'servers',
            },
        )

        return self.state.parser.parse_discovery_server_search_result(page['pageProps'])

    async def search_bots(self, query: str) -> BotSearchResult:
        """|coro|

        Searches for bots.

        Parameters
        ----------
        query: :class:`str`
            The query to search for.

        Returns
        -------
        :class:`BotSearchResult`
            The search results.
        """
        page: raw.NextPage[raw.DiscoveryBotSearchResult] = await self.request(
            'GET',
            '/discover/search.json',
            params={
                'embedded': 'true',
                'query': query,
                'type': 'bots',
            },
        )

        return self.state.parser.parse_discovery_bot_search_result(page['pageProps'])

    async def search_themes(self, query: str) -> ThemeSearchResult:
        """|coro|

        Searches for themes.

        Parameters
        ----------
        query: :class:`str`
            The query to search for.

        Returns
        -------
        :class:`ThemeSearchResult`
            The search results.
        """
        page: raw.NextPage[raw.DiscoveryThemeSearchResult] = await self.request(
            'GET',
            '/discover/search.json',
            params={
                'embedded': 'true',
                'query': query,
                'type': 'themes',
            },
        )

        return self.state.parser.parse_discovery_theme_search_result(page['pageProps'])


__all__ = (
    'DiscoveryServer',
    'DiscoveryServersPage',
    'DiscoveryBot',
    'DiscoveryBotsPage',
    'DiscoveryTheme',
    'DiscoveryThemesPage',
    'ServerSearchResult',
    'BotSearchResult',
    'ThemeSearchResult',
    'DiscoveryClient',
)
