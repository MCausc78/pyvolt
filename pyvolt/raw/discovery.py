# [unofficial API]

from __future__ import annotations

import typing as t

from . import files, users

# Servers
DiscoveryServerActivity = t.Literal["high", "medium", "low", "no"]


class DiscoveryServer(t.TypedDict):
    _id: str
    name: str
    description: str | None
    icon: t.NotRequired[files.File]
    banner: t.NotRequired[files.File]
    flags: t.NotRequired[int]
    tags: list[str]
    members: int
    activity: DiscoveryServerActivity


class DiscoveryServersPage(t.TypedDict):
    servers: list[DiscoveryServer]
    popularTags: list[str]


class DiscoveryServerSearchResult(t.TypedDict):
    query: str
    count: int
    type: t.Literal["servers"]
    servers: list[DiscoveryServer]
    relatedTags: list[str]


# Bots
DiscoveryBotUsage = t.Literal["high", "medium", "low"]


class DiscoveryBot(t.TypedDict):
    _id: str
    username: str
    avatar: t.NotRequired[files.File]
    profile: users.UserProfile
    tags: list[str]
    servers: int
    usage: DiscoveryBotUsage


class DiscoveryBotsPage(t.TypedDict):
    bots: list[DiscoveryBot]
    popularTags: list[str]


class DiscoveryBotSearchResult(t.TypedDict):
    query: str
    count: int
    type: t.Literal["bots"]
    bots: list[DiscoveryBot]
    relatedTags: list[str]


# Themes
class DiscoveryTheme(t.TypedDict):
    name: str
    version: str
    slug: str
    creator: str
    description: str
    tags: list[str]
    variables: dict[str, str]
    css: t.NotRequired[str]


class DiscoveryThemesPage(t.TypedDict):
    themes: list[DiscoveryTheme]
    popularTags: list[str]


class DiscoveryThemeSearchResult(t.TypedDict):
    query: str
    count: int
    type: t.Literal["themes"]
    themes: list[DiscoveryTheme]
    relatedTags: list[str]


P = t.TypeVar("P")


class NextPage(t.Generic[P], t.TypedDict):
    pageProps: P
    __N_SSP: bool


__all__ = (
    "DiscoveryServerActivity",
    "DiscoveryServer",
    "DiscoveryServersPage",
    "DiscoveryServerSearchResult",
    "DiscoveryBotUsage",
    "DiscoveryBot",
    "DiscoveryBotsPage",
    "DiscoveryBotSearchResult",
    "DiscoveryTheme",
    "DiscoveryThemesPage",
    "DiscoveryThemeSearchResult",
    "NextPage",
)
