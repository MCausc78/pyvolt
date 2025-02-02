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

from inspect import isawaitable
import logging
import re
import typing

import aiohttp
from attrs import define, field

from multidict import CIMultiDict

from . import utils
from .bot import BaseBot
from .core import UNDEFINED, UndefinedOr, __version__ as version
from .errors import DiscoverError, InvalidData
from .server import ServerFlags, BaseServer

if typing.TYPE_CHECKING:
    from . import raw
    from .cdn import StatelessAsset, Asset
    from .enums import ServerActivity, BotUsage, ReviteBaseTheme
    from .settings import ReviteThemeVariable
    from .state import State
    from .user import StatelessUserProfile, UserProfile

_L = logging.getLogger(__name__)
DEFAULT_DISCOVERY_USER_AGENT = f'pyvolt Discovery client (https://github.com/MCausc78/pyvolt, {version})'

_new_server_flags = ServerFlags.__new__


@define(slots=True)
class DiscoverableServer(BaseServer):
    """Represents a server on Revolt Discovery. The ID is a invite code."""

    name: str = field(repr=True, kw_only=True)
    """:class:`str`: The server's name."""

    description: str | None = field(repr=True, kw_only=True)
    """Optional[:class:`str`]: The server's description."""

    internal_icon: StatelessAsset | None = field(repr=True, kw_only=True)
    """Optional[:class:`.StatelessAsset`]: The stateless server icon."""

    internal_banner: StatelessAsset | None = field(repr=True, kw_only=True)
    """Optional[:class:`.StatelessAsset`]: The stateless server banner."""

    raw_flags: int = field(repr=True, kw_only=True)
    """:class:`int`: The server's flags raw value."""

    tags: list[str] = field(repr=True, kw_only=True)
    """List[:class:`str`]: The server's tags."""

    member_count: int = field(repr=True, kw_only=True)
    """:class:`int`: The server's member count."""

    activity: ServerActivity = field(repr=True, kw_only=True)
    """:class:`.ServerActivity`: The server's activity."""

    @property
    def flags(self) -> ServerFlags:
        """:class:`.ServerFlags`: The server's flags."""
        ret = _new_server_flags(ServerFlags)
        ret.value = self.raw_flags
        return ret

    @property
    def icon(self) -> Asset | None:
        """Optional[:class:`.Asset`]: The server's icon."""
        return self.internal_icon and self.internal_icon.attach_state(self.state, 'icons')

    @property
    def invite_code(self) -> str:
        """:class:`str`: The server invite code. As an implementation detail, right now it returns server ID, but don't depend on that in future."""
        return self.id

    @property
    def banner(self) -> Asset | None:
        """Optional[:class:`.Asset`]: The server's banner."""
        return self.internal_banner and self.internal_banner.attach_state(self.state, 'banners')


@define(slots=True)
class DiscoverableServersPage:
    servers: list[DiscoverableServer] = field(repr=True, kw_only=True)
    """List[:class:`.DiscoverableServer`]: The listed servers, up to 200 servers."""

    popular_tags: list[str] = field(repr=True, kw_only=True)
    """List[:class:`str`]: Popular tags used in discovery servers."""


@define(slots=True)
class DiscoverableBot(BaseBot):
    name: str = field(repr=True, kw_only=True)
    """:class:`str`: The bot's name."""

    internal_avatar: StatelessAsset | None = field(repr=True, kw_only=True)
    """Optional[:class:`.StatelessAsset`]: The stateless bot's avatar."""

    internal_profile: StatelessUserProfile = field(repr=True, kw_only=True)
    """Optional[:class:`.StatelessUserProfile`]: The stateless bot's profile."""

    tags: list[str] = field(repr=True, kw_only=True)
    """List[:class:`int`]: The bot's tags."""

    server_count: int = field(repr=True, kw_only=True)
    """:class:`int`: The bot's servers count."""

    usage: BotUsage = field(repr=True, kw_only=True)
    """:class:`.BotUsage`: How frequently is bot being used."""

    @property
    def avatar(self) -> Asset | None:
        """Optional[:class:`.Asset`]: The bot's avatar."""
        return self.internal_avatar and self.internal_avatar.attach_state(self.state, 'avatars')

    @property
    def description(self) -> str:
        """:class:`str`: The bot's profile description."""
        return self.internal_profile.content or ''

    @property
    def profile(self) -> UserProfile:
        """:class:`.UserProfile`: The bot's profile."""
        return self.internal_profile.attach_state(self.state, self.id)


@define(slots=True)
class DiscoverableBotsPage:
    bots: list[DiscoverableBot] = field(repr=True, kw_only=True)
    """List[:class:`.DiscoverableBot`]: The listed bots, up to 200 bots."""

    popular_tags: list[str] = field(repr=True, kw_only=True)
    """List[:class:`str`]: Popular tags used in discovery bots."""


@define(slots=True)
class DiscoverableTheme:
    state: State = field(repr=False)
    """:class:`.State`: State that controls this theme."""

    name: str = field(repr=True, kw_only=True)
    """:class:`str`: The theme name."""

    description: str = field(repr=True, kw_only=True)
    """:class:`str`: The theme description."""

    creator: str = field(repr=True, kw_only=True)
    """:class:`str`: The theme creator."""

    slug: str = field(repr=True, kw_only=True)
    """:class:`str`: The theme slug."""

    tags: list[str] = field(repr=True, kw_only=True)
    """List[:class:`str`]: The theme tags."""

    overrides: dict[ReviteThemeVariable, str] = field(repr=True, kw_only=True)
    """Dict[:class:`.ReviteThemeVariable`, :class:`str`]: The theme overrides in format `{css_class: css_color}`."""

    version: str = field(repr=True, kw_only=True)
    """:class:`str`: The theme version."""

    custom_css: str | None = field(repr=True, kw_only=True)
    """Optional[:class:`str`]: The theme CSS string."""

    def __hash__(self) -> int:
        return hash((self.name, self.creator))

    def __eq__(self, other: object, /) -> bool:
        return (
            self is other
            or isinstance(other, DiscoverableTheme)
            and self.name == other.name
            and self.creator == other.creator
        )

    async def apply(self, *, base_theme: UndefinedOr[ReviteBaseTheme] = UNDEFINED) -> None:
        """|coro|

        Applies the theme to current user account.

        Parameters
        ----------
        base_theme: UndefinedOr[:class:`.ReviteBaseTheme`]
            The base theme to use, when applying theme.
        """
        await self.state.settings.revite.edit(
            overrides=self.overrides,
            base_theme=base_theme,
            custom_css=self.custom_css,
        )


@define(slots=True)
class DiscoverableThemesPage:
    themes: list[DiscoverableTheme] = field(repr=True, kw_only=True)
    """List[:class:`.DiscoverableTheme`]: The listed themes, up to 200 themes."""

    popular_tags: list[str] = field(repr=True, kw_only=True)
    """List[:class:`str`]: The popular tags used in discoverable themes."""


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
    """:class:`str`: The lower-cased query."""

    count: int = field(repr=True, kw_only=True)
    """:class:`int`: The servers count."""

    servers: list[DiscoverableServer] = field(repr=True, kw_only=True)
    """List[:class:`.DiscoverableServer`]: The listed servers."""

    related_tags: list[str] = field(repr=True, kw_only=True)
    """List[:class:`str`]: All of tags that listed servers have."""


@define(slots=True)
class BotSearchResult:
    """The bot search result object."""

    query: str = field(repr=True, kw_only=True)
    """:class:`str`: The lower-cased query."""

    count: int = field(repr=True, kw_only=True)
    """:class:`int`: The bots count."""

    bots: list[DiscoverableBot] = field(repr=True, kw_only=True)
    """List[:class:`.DiscoverableBot`]: The listed bots."""

    related_tags: list[str] = field(repr=True, kw_only=True)
    """List[:class:`str`]: All of tags that listed bots have."""


@define(slots=True)
class ThemeSearchResult:
    """The theme search result object."""

    query: str = field(repr=True, kw_only=True)
    """:class:`str`: The lower-cased query."""

    count: int = field(repr=True, kw_only=True)
    """:class:`int`: The themes count."""

    themes: list[DiscoverableTheme] = field(repr=True, kw_only=True)
    """List[:class:`.DiscoverableTheme`]: The listed themes."""

    related_tags: list[str] = field(repr=True, kw_only=True)
    """List[:class:`str`]: All of tags that listed themes have."""


DISCOVERY_BUILD_ID: str = '9I_qurZmA2SKF8CAOcQAv'

RE_DISCOVERY_BUILD_ID: re.Pattern = re.compile(r'"buildId":\s*"([0-9A-Za-z_-]+)"')


class DiscoveryClient:
    __slots__ = (
        '_base',
        'session',
        'state',
        'user_agent',
    )

    def __init__(
        self,
        *,
        base: str | None = None,
        session: aiohttp.ClientSession,
        state: State,
        user_agent: str = '',
    ) -> None:
        self._base: str = f'https://rvlt.gg/_next/data/{DISCOVERY_BUILD_ID}' if base is None else base.rstrip('/')
        self.session: aiohttp.ClientSession = session
        self.state: State = state
        self.user_agent: str = user_agent or DEFAULT_DISCOVERY_USER_AGENT

    def with_base(self, base: str, /) -> None:
        self._base = base.rstrip('/')

    async def fetch_build_id(self) -> str:
        """|coro|

        Retrieves latest discover client build ID.

        .. note::
            This always retrieves **only from** `official Discover instance <https://rvlt.gg/>`_.

        Raises
        ------
        DiscoverError
            Fetching the main page failed.
        InvalidData
            If library is unable look up build ID.

        Returns
        -------
        :class:`str`
            The build ID.
        """
        async with self.session.get('https://rvlt.gg/discover/servers') as response:
            data = await utils._json_or_text(response)
            if response.status != 200:
                data = await utils._json_or_text(response)
                raise DiscoverError(response, response.status, data)
            match = RE_DISCOVERY_BUILD_ID.search(data)
            if match is None:
                raise InvalidData(
                    f'Unable to find build ID. Please file an issue on https://github.com/MCausc78/pyvolt with following data: {data}'
                )
            return match.group(1)

    def add_headers(
        self,
        headers: CIMultiDict[typing.Any],
        method: str,
        path: str,
        /,
    ) -> utils.MaybeAwaitable[None]:
        headers['User-Agent'] = self.user_agent

    async def send_request(
        self,
        session: aiohttp.ClientSession,
        method: str,
        url: str,
        /,
        *,
        headers: CIMultiDict[typing.Any],
        **kwargs,
    ) -> aiohttp.ClientResponse:
        return await session.request(
            method,
            url,
            headers=headers,
            **kwargs,
        )

    async def raw_request(self, method: str, path: str, /, **kwargs) -> aiohttp.ClientResponse:
        _L.debug('Sending %s to %s params=%s', method, path, kwargs.get('params'))

        headers: CIMultiDict[typing.Any] = CIMultiDict(kwargs.pop('headers', {}))
        tmp = self.add_headers(headers, method, path)
        if isawaitable(tmp):
            await tmp

        url = self._base + path

        for i in range(2):
            response = await self.send_request(self.session, method, url, headers=headers, **kwargs)
            if response.status >= 400:
                data = await utils._json_or_text(response)
                if (
                    i == 1
                    and response.status == 404
                    and self._base.startswith('https://rvlt.gg/_next/data/')
                    and isinstance(data, str)
                ):
                    match = RE_DISCOVERY_BUILD_ID.search(data)
                    if match is not None:
                        self._base = f'https://rvlt.gg/_next/data/{match.group(1)}'
                    continue
                raise DiscoverError(response, response.status, data)
            return response
        raise RuntimeError('Unreachable code in HTTP handling')

    async def use_latest_build_id(self) -> str:
        """|coro|

        Retrieves latest discover client build ID and uses it.

        This follows same exceptions and notes as :meth:`.fetch_build_id`.

        Returns
        -------
        :class:`str`
            The build ID.
        """
        build_id = await self.fetch_build_id()
        self._base = f'https://rvlt.gg/_next/data/{build_id}'
        return build_id

    async def request(self, method: str, path: str, /, **kwargs) -> typing.Any:
        response = await self.raw_request(method, path, **kwargs)
        result = await utils._json_or_text(response)
        _L.debug('received from %s %s: %s', method, path, result)
        response.close()
        return result

    async def servers(self) -> DiscoverableServersPage:
        """|coro|

        Retrieves servers on a main page.

        Raises
        ------
        DiscoverError
            Getting the servers failed.

        Returns
        -------
        :class:`DiscoverableServersPage`
            The servers page.
        """
        page: raw.NextPage[raw.DiscoverableServersPage] = await self.request(
            'GET', '/discover/servers.json', params={'embedded': 'true'}
        )
        return self.state.parser.parse_discoverable_servers_page(page['pageProps'])

    async def bots(self) -> DiscoverableBotsPage:
        """|coro|

        Retrieves bots on a main page.

        Raises
        ------
        DiscoverError
            Getting the bots failed.

        Returns
        -------
        :class:`DiscoverableBotsPage`
            The bots page.
        """

        page: raw.NextPage[raw.DiscoverableBotsPage] = await self.request(
            'GET', '/discover/bots.json', params={'embedded': 'true'}
        )

        return self.state.parser.parse_discoverable_bots_page(page['pageProps'])

    async def themes(self) -> DiscoverableThemesPage:
        """|coro|

        Retrieves themes on a main page.

        Raises
        ------
        DiscoverableError
            Getting the themes failed.

        Returns
        -------
        :class:`DiscoverableThemesPage`
            The themes page.
        """
        page: raw.NextPage[raw.DiscoverableThemesPage] = await self.request(
            'GET', '/discover/themes.json', params={'embedded': 'true'}
        )
        return self.state.parser.parse_discoverable_themes_page(page['pageProps'])

    async def search_servers(self, query: str) -> ServerSearchResult:
        """|coro|

        Searches for servers.

        Parameters
        ----------
        query: :class:`str`
            The query to search for.

        Raises
        ------
        DiscoverError
            Searching failed.

        Returns
        -------
        :class:`ServerSearchResult`
            The search results.
        """
        page: raw.NextPage[raw.DiscoverableServerSearchResult] = await self.request(
            'GET',
            '/discover/search.json',
            params={
                'embedded': 'true',
                'query': query,
                'type': 'servers',
            },
        )

        return self.state.parser.parse_discoverable_server_search_result(page['pageProps'])

    async def search_bots(self, query: str) -> BotSearchResult:
        """|coro|

        Searches for bots.

        Parameters
        ----------
        query: :class:`str`
            The query to search for.

        Raises
        ------
        DiscoverError
            Searching failed.

        Returns
        -------
        :class:`BotSearchResult`
            The search results.
        """
        page: raw.NextPage[raw.DiscoverableBotSearchResult] = await self.request(
            'GET',
            '/discover/search.json',
            params={
                'embedded': 'true',
                'query': query,
                'type': 'bots',
            },
        )

        return self.state.parser.parse_discoverable_bot_search_result(page['pageProps'])

    async def search_themes(self, query: str) -> ThemeSearchResult:
        """|coro|

        Searches for themes.

        Parameters
        ----------
        query: :class:`str`
            The query to search for.

        Raises
        ------
        DiscoverError
            Searching failed.

        Returns
        -------
        :class:`ThemeSearchResult`
            The search results.
        """
        page: raw.NextPage[raw.DiscoverableThemeSearchResult] = await self.request(
            'GET',
            '/discover/search.json',
            params={
                'embedded': 'true',
                'query': query,
                'type': 'themes',
            },
        )

        return self.state.parser.parse_discoverable_theme_search_result(page['pageProps'])


__all__ = (
    'DiscoverableServer',
    'DiscoverableServersPage',
    'DiscoverableBot',
    'DiscoverableBotsPage',
    'DiscoverableTheme',
    'DiscoverableThemesPage',
    'ServerSearchResult',
    'BotSearchResult',
    'ThemeSearchResult',
    'DISCOVERY_BUILD_ID',
    'RE_DISCOVERY_BUILD_ID',
    'DiscoveryClient',
)
