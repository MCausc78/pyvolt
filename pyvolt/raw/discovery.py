# [unofficial API]

from __future__ import annotations

import typing
import typing_extensions

from .files import File
from .user_settings import ReviteThemeVariable
from .users import UserProfile

# Servers
DiscoverableServerActivity = typing.Literal['high', 'medium', 'low', 'no']


class DiscoverableServer(typing.TypedDict):
    _id: str
    name: str
    description: typing.Optional[str]
    icon: typing_extensions.NotRequired[File]
    banner: typing_extensions.NotRequired[File]
    flags: typing_extensions.NotRequired[int]
    tags: list[str]
    members: int
    activity: DiscoverableServerActivity


class DiscoverableServersPage(typing.TypedDict):
    servers: list[DiscoverableServer]
    popularTags: list[str]


class DiscoverableServerSearchResult(typing.TypedDict):
    query: str
    count: int
    type: typing.Literal['servers']
    servers: list[DiscoverableServer]
    relatedTags: list[str]


# Bots
DiscoverableBotUsage = typing.Literal['high', 'medium', 'low']


class DiscoverableBot(typing.TypedDict):
    _id: str
    username: str
    avatar: typing_extensions.NotRequired[File]
    profile: UserProfile
    tags: list[str]
    servers: int
    usage: DiscoverableBotUsage


class DiscoverableBotsPage(typing.TypedDict):
    bots: list[DiscoverableBot]
    popularTags: list[str]


class DiscoverableBotSearchResult(typing.TypedDict):
    query: str
    count: int
    type: typing.Literal['bots']
    bots: list[DiscoverableBot]
    relatedTags: list[str]


# Themes
class DiscoverableTheme(typing.TypedDict):
    name: str
    version: str
    slug: str
    creator: str
    description: str
    tags: list[str]
    variables: dict[ReviteThemeVariable, str]
    css: typing_extensions.NotRequired[str]


class DiscoverableThemesPage(typing.TypedDict):
    themes: list[DiscoverableTheme]
    popularTags: list[str]


class DiscoverableThemeSearchResult(typing.TypedDict):
    query: str
    count: int
    type: typing.Literal['themes']
    themes: list[DiscoverableTheme]
    relatedTags: list[str]


P = typing.TypeVar('P')


class NextPage(typing.Generic[P], typing.TypedDict):
    pageProps: P
    __N_SSP: bool
