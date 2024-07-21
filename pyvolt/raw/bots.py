from __future__ import annotations

import typing

from .users import User


class Bot(typing.TypedDict):
    _id: str
    owner: str
    token: str
    public: bool
    analytics: typing.NotRequired[bool]
    discoverable: typing.NotRequired[bool]
    interactions_url: typing.NotRequired[str]
    terms_of_service_url: typing.NotRequired[str]
    privacy_policy_url: typing.NotRequired[str]
    flags: int


FieldsBot = typing.Literal['Token', 'InteractionsURL']


class PublicBot(typing.TypedDict):
    _id: str
    username: str
    avatar: typing.NotRequired[str]
    description: typing.NotRequired[str]


class FetchBotResponse(typing.TypedDict):
    bot: Bot
    user: User


class DataCreateBot(typing.TypedDict):
    name: str


class DataEditBot(typing.TypedDict):
    name: typing.NotRequired[str]
    public: typing.NotRequired[bool]
    analytics: typing.NotRequired[bool]
    interactions_url: typing.NotRequired[str]
    remove: typing.NotRequired[list[FieldsBot]]


class ServerInviteBotDestination(typing.TypedDict):
    server: str


class GroupInviteBotDestination(typing.TypedDict):
    group: str


InviteBotDestination = ServerInviteBotDestination | GroupInviteBotDestination


class OwnedBotsResponse(typing.TypedDict):
    bots: list[Bot]
    users: list[User]


class BotWithUserResponse(Bot):
    user: User


__all__ = (
    'Bot',
    'FieldsBot',
    'PublicBot',
    'FetchBotResponse',
    'DataCreateBot',
    'DataEditBot',
    'ServerInviteBotDestination',
    'GroupInviteBotDestination',
    'InviteBotDestination',
    'OwnedBotsResponse',
    'BotWithUserResponse',
)
