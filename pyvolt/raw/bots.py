from __future__ import annotations

import typing
import typing_extensions

from .users import User


class Bot(typing.TypedDict):
    _id: str
    owner: str
    token: str
    public: bool
    analytics: typing_extensions.NotRequired[bool]
    discoverable: typing_extensions.NotRequired[bool]
    interactions_url: typing_extensions.NotRequired[str]
    terms_of_service_url: typing_extensions.NotRequired[str]
    privacy_policy_url: typing_extensions.NotRequired[str]
    flags: int


FieldsBot = typing.Literal['Token', 'InteractionsURL']


class PublicBot(typing.TypedDict):
    _id: str
    username: str
    avatar: typing_extensions.NotRequired[str]
    description: typing_extensions.NotRequired[str]


class FetchBotResponse(typing.TypedDict):
    bot: Bot
    user: User


class DataCreateBot(typing.TypedDict):
    name: str


class DataEditBot(typing.TypedDict):
    name: typing_extensions.NotRequired[str]
    public: typing_extensions.NotRequired[bool]
    analytics: typing_extensions.NotRequired[bool]
    interactions_url: typing_extensions.NotRequired[str]
    remove: typing_extensions.NotRequired[list[FieldsBot]]


class ServerInviteBotDestination(typing.TypedDict):
    server: str


class GroupInviteBotDestination(typing.TypedDict):
    group: str


InviteBotDestination = typing.Union[ServerInviteBotDestination, GroupInviteBotDestination]


class OwnedBotsResponse(typing.TypedDict):
    bots: list[Bot]
    users: list[User]


class BotWithUserResponse(Bot):
    user: User
