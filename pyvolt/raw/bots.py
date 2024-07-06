from __future__ import annotations

import typing as t

from .users import User


class Bot(t.TypedDict):
    _id: str
    owner: str
    token: str
    public: bool
    analytics: t.NotRequired[bool]
    discoverable: t.NotRequired[bool]
    interactions_url: t.NotRequired[str]
    terms_of_service_url: t.NotRequired[str]
    privacy_policy_url: t.NotRequired[str]
    flags: int


FieldsBot = t.Literal["Token", "InteractionsURL"]


class PublicBot(t.TypedDict):
    _id: str
    username: str
    avatar: t.NotRequired[str]
    description: t.NotRequired[str]


class FetchBotResponse(t.TypedDict):
    bot: Bot
    user: User


class DataCreateBot(t.TypedDict):
    name: str


class DataEditBot(t.TypedDict):
    name: t.NotRequired[str]
    public: t.NotRequired[bool]
    analytics: t.NotRequired[bool]
    interactions_url: t.NotRequired[str]
    remove: t.NotRequired[list[FieldsBot]]


class ServerInviteBotDestination(t.TypedDict):
    server: str


class GroupInviteBotDestination(t.TypedDict):
    group: str


InviteBotDestination = ServerInviteBotDestination | GroupInviteBotDestination


class OwnedBotsResponse(t.TypedDict):
    bots: list[Bot]
    users: list[User]


class BotWithUserResponse(Bot):
    user: User


__all__ = (
    "Bot",
    "FieldsBot",
    "PublicBot",
    "FetchBotResponse",
    "DataCreateBot",
    "DataEditBot",
    "ServerInviteBotDestination",
    "GroupInviteBotDestination",
    "InviteBotDestination",
    "OwnedBotsResponse",
    "BotWithUserResponse",
)
