# [unofficial API]

from __future__ import annotations

import typing

from .files import File
from .users import UserProfile

# Servers
DiscoveryServerActivity = typing.Literal["high", "medium", "low", "no"]


class DiscoveryServer(typing.TypedDict):
    _id: str
    name: str
    description: str | None
    icon: typing.NotRequired[File]
    banner: typing.NotRequired[File]
    flags: typing.NotRequired[int]
    tags: list[str]
    members: int
    activity: DiscoveryServerActivity


class DiscoveryServersPage(typing.TypedDict):
    servers: list[DiscoveryServer]
    popularTags: list[str]


class DiscoveryServerSearchResult(typing.TypedDict):
    query: str
    count: int
    type: typing.Literal["servers"]
    servers: list[DiscoveryServer]
    relatedTags: list[str]


# Bots
DiscoveryBotUsage = typing.Literal["high", "medium", "low"]


class DiscoveryBot(typing.TypedDict):
    _id: str
    username: str
    avatar: typing.NotRequired[File]
    profile: UserProfile
    tags: list[str]
    servers: int
    usage: DiscoveryBotUsage


class DiscoveryBotsPage(typing.TypedDict):
    bots: list[DiscoveryBot]
    popularTags: list[str]


class DiscoveryBotSearchResult(typing.TypedDict):
    query: str
    count: int
    type: typing.Literal["bots"]
    bots: list[DiscoveryBot]
    relatedTags: list[str]


# Themes
class DiscoveryTheme(typing.TypedDict):
    name: str
    version: str
    slug: str
    creator: str
    description: str
    tags: list[str]
    variables: dict[str, str]
    css: typing.NotRequired[str]


class DiscoveryThemesPage(typing.TypedDict):
    themes: list[DiscoveryTheme]
    popularTags: list[str]


class DiscoveryThemeSearchResult(typing.TypedDict):
    query: str
    count: int
    type: typing.Literal["themes"]
    themes: list[DiscoveryTheme]
    relatedTags: list[str]


P = typing.TypeVar("P")


class NextPage(typing.Generic[P], typing.TypedDict):
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
