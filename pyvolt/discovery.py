from __future__ import annotations

import aiohttp
from attrs import define, field
import logging
import typing as t

from . import cdn, core, utils
from .bot import BaseBot
from .enums import Enum
from .errors import DiscoveryError
from .server import ServerFlags, BaseServer
from .state import State
from .user import StatelessUserProfile, UserProfile

if t.TYPE_CHECKING:
    from . import raw

_L = logging.getLogger(__name__)

DEFAULT_DISCOVERY_USER_AGENT = (
    f"pyvolt Discovery client (https://github.com/MCausc78/pyvolt, {core.__version__})"
)


class ServerActivity(Enum):
    high = "high"
    medium = "medium"
    low = "low"
    no = "no"


@define(slots=True)
class DiscoveryServer(BaseServer):
    """Representation of a server on Revolt Discovery. The ID is a invite code."""

    name: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The server name."""

    description: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The server description."""

    internal_icon: cdn.StatelessAsset | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The stateless server icon."""

    internal_banner: cdn.StatelessAsset | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The stateless server banner."""

    flags: ServerFlags = field(repr=True, hash=True, kw_only=True, eq=True)
    """The server flags."""

    tags: list[str] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The server tags."""

    member_count: int = field(repr=True, hash=True, kw_only=True, eq=True)
    """The server member count."""

    activity: ServerActivity = field(repr=True, hash=True, kw_only=True, eq=True)
    """The server activity."""

    @property
    def icon(self) -> cdn.Asset | None:
        """The server icon."""
        return self.internal_icon and self.internal_icon._stateful(self.state, "icons")

    @property
    def invite_code(self) -> str:
        """The server invite code. As an implementation detail, right now it returns server ID, but don't depend on that in future."""
        return self.id

    @property
    def banner(self) -> cdn.Asset | None:
        """The server banner."""
        return self.internal_banner and self.internal_banner._stateful(
            self.state, "banners"
        )


@define(slots=True)
class DiscoveryServersPage:
    servers: list[DiscoveryServer] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The listed servers, up to 200 servers."""

    popular_tags: list[str] = field(repr=True, hash=True, kw_only=True, eq=True)
    """Popular tags used in discovery servers."""


class BotUsage(Enum):
    high = "high"
    medium = "medium"
    low = "low"


@define(slots=True)
class DiscoveryBot(BaseBot):
    name: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The bot's name."""

    internal_avatar: cdn.StatelessAsset | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The stateless bot's avatar."""

    internal_profile: StatelessUserProfile = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The stateless bot's profile."""

    tags: list[str] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The bot's tags."""

    server_count: int = field(repr=True, hash=True, kw_only=True, eq=True)
    """The bot's servers count."""

    usage: BotUsage = field(repr=True, hash=True, kw_only=True, eq=True)
    """How frequently is bot being used."""

    @property
    def avatar(self) -> cdn.Asset | None:
        """The bot's avatar."""
        return self.internal_avatar and self.internal_avatar._stateful(
            self.state, "avatars"
        )

    @property
    def description(self) -> str:
        """The bot's profile description."""
        return self.internal_profile.content or ""

    @property
    def profile(self) -> UserProfile:
        """The bot's profile."""
        return self.internal_profile._stateful(self.state, self.id)


@define(slots=True)
class DiscoveryBotsPage:
    bots: list[DiscoveryBot] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The listed bots, up to 200 bots."""

    popular_tags: list[str] = field(repr=True, hash=True, kw_only=True, eq=True)
    """Popular tags used in discovery bots."""


@define(slots=True)
class DiscoveryTheme:
    state: State = field(repr=False, hash=True, eq=True)
    """State that controls this theme."""

    name: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The theme name."""

    description: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The theme description."""

    creator: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The theme creator."""

    slug: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The theme slug."""

    tags: list[str] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The theme tags."""

    variables: dict[str, str] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The theme color mapping in format `{css_class: css_color}`."""

    version: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The theme version."""

    css: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The theme CSS."""

    # TODO: Add `Theme.apply` method.
    # The `theme` user setting has following JSON payload:
    # - `appearance:theme:overrides` object, containing `Theme.variables` value
    # - [Optional, if `Theme.css` is not none] `appearance:theme:css` object, containing `Theme.css` value
    # Example:
    # setting = {
    #   "appearance:theme:base": "dark",
    #   "appearance:theme:overrides": theme.variables,
    # }
    # if theme.css is not None:
    #   setting["appearance:theme:css"] = theme.css
    # payload = {"theme": to_json(setting)} # "Modify User Settings" payload
    # await http.set_user_settings(payload)


@define(slots=True)
class DiscoveryThemesPage:
    themes: list[DiscoveryTheme] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The listed themes, up to 200 themes."""

    popular_tags: list[str] = field(repr=True, hash=True, kw_only=True, eq=True)
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

    query: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The lower-cased query."""

    count: int = field(repr=True, hash=True, kw_only=True, eq=True)
    """The servers count."""

    servers: list[DiscoveryServer] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The listed servers."""

    related_tags: list[str] = field(repr=True, hash=True, kw_only=True, eq=True)
    """All of tags that listed servers have."""


@define(slots=True)
class BotSearchResult:
    """The bot search result object."""

    query: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The lower-cased query."""

    count: int = field(repr=True, hash=True, kw_only=True, eq=True)
    """The bots count."""

    bots: list[DiscoveryBot] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The listed bots."""

    related_tags: list[str] = field(repr=True, hash=True, kw_only=True, eq=True)
    """All of tags that listed bots have."""


@define(slots=True)
class ThemeSearchResult:
    """The theme search result object."""

    query: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The lower-cased query."""

    count: int = field(repr=True, hash=True, kw_only=True, eq=True)
    """The themes count."""

    themes: list[DiscoveryTheme] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The listed themes."""

    related_tags: list[str] = field(repr=True, hash=True, kw_only=True, eq=True)
    """All of tags that listed themes have."""


class DiscoveryClient:
    def __init__(
        self, *, base: str | None = None, session: aiohttp.ClientSession, state: State
    ) -> None:
        self._base = (
            "https://rvlt.gg/_next/data/OddIUaX26creykRzYdVYw/"
            if base is None
            else base.rstrip("/") + "/"
        )
        self.session = session
        self.state = state

    async def _request(
        self, method: str, path: str, **kwargs
    ) -> aiohttp.ClientResponse:
        _L.debug("sending %s to %s params=%s", method, path, kwargs.get("params"))
        headers = {"user-agent": DEFAULT_DISCOVERY_USER_AGENT}
        headers.update(kwargs.pop("headers", {}))
        response = await self.session.request(
            method, self._base + path.lstrip("/"), headers=headers, **kwargs
        )
        if response.status >= 400:
            body = await utils._json_or_text(response)
            raise DiscoveryError(response, response.status, body)
        return response

    async def request(self, method: str, path: str, **kwargs) -> t.Any:
        async with await self._request(method, path, **kwargs) as response:
            result = await utils._json_or_text(response)
        _L.debug("received from %s %s: %s", method, path, result)
        return result

    async def servers(self) -> DiscoveryServersPage:
        page: raw.NextPage[raw.DiscoveryServersPage] = await self.request(
            "GET", "/discover/servers.json", params={"embedded": "true"}
        )
        return self.state.parser.parse_discovery_servers_page(page["pageProps"])

    async def bots(self) -> DiscoveryBotsPage:
        page: raw.NextPage[raw.DiscoveryBotsPage] = await self.request(
            "GET", "/discover/bots.json", params={"embedded": "true"}
        )

        return self.state.parser.parse_discovery_bots_page(page["pageProps"])

    async def themes(self) -> DiscoveryThemesPage:
        page: raw.NextPage[raw.DiscoveryThemesPage] = await self.request(
            "GET", "/discover/themes.json", params={"embedded": "true"}
        )
        return self.state.parser.parse_discovery_themes_page(page["pageProps"])

    async def search_servers(self, query: str) -> ServerSearchResult:
        page: raw.NextPage[raw.DiscoveryServerSearchResult] = await self.request(
            "GET",
            "/discover/search.json",
            params={
                "embedded": "true",
                "query": query,
                "type": "servers",
            },
        )

        return self.state.parser.parse_discovery_server_search_result(page["pageProps"])

    async def search_bots(self, query: str) -> BotSearchResult:
        page: raw.NextPage[raw.DiscoveryBotSearchResult] = await self.request(
            "GET",
            "/discover/search.json",
            params={
                "embedded": "true",
                "query": query,
                "type": "bots",
            },
        )

        return self.state.parser.parse_discovery_bot_search_result(page["pageProps"])

    async def search_themes(self, query: str) -> ThemeSearchResult:
        page: raw.NextPage[raw.DiscoveryThemeSearchResult] = await self.request(
            "GET",
            "/discover/search.json",
            params={
                "embedded": "true",
                "query": query,
                "type": "themes",
            },
        )

        return self.state.parser.parse_discovery_theme_search_result(page["pageProps"])


__all__ = (
    "ServerActivity",
    "DiscoveryServer",
    "DiscoveryServersPage",
    "BotUsage",
    "DiscoveryBot",
    "DiscoveryBotsPage",
    "DiscoveryTheme",
    "DiscoveryThemesPage",
    "ServerSearchResult",
    "BotSearchResult",
    "ThemeSearchResult",
    "DiscoveryClient",
)
