from __future__ import annotations

import typing as t

from .basic import Bool
from .channel_webhooks import MessageWebhook
from .embeds import Embed
from .files import File
from .server_members import Member
from .users import User


class Message(t.TypedDict):
    _id: str
    nonce: t.NotRequired[str]
    channel: str
    author: str
    user: t.NotRequired[User]
    member: t.NotRequired[Member]
    webhook: t.NotRequired[MessageWebhook]
    content: t.NotRequired[str]
    system: t.NotRequired[SystemMessage]
    attachments: t.NotRequired[list[File]]
    edited: t.NotRequired[str]
    embeds: t.NotRequired[list[Embed]]
    mentions: t.NotRequired[list[str]]
    replies: t.NotRequired[list[str]]
    reactions: t.NotRequired[dict[str, list[str]]]
    interactions: t.NotRequired[Interactions]
    masquerade: t.NotRequired[Masquerade]
    flags: t.NotRequired[int]


class PartialMessage(t.TypedDict):
    content: t.NotRequired[str]
    edited: t.NotRequired[str]
    embeds: t.NotRequired[list[Embed]]
    reactions: t.NotRequired[dict[str, list[str]]]


class MessagesAndUsersBulkMessageResponse(t.TypedDict):
    messages: list[Message]
    users: list[User]
    members: t.NotRequired[list[Member]]


BulkMessageResponse = list[Message] | MessagesAndUsersBulkMessageResponse


class TextSystemMessage(t.TypedDict):
    type: t.Literal["text"]
    content: str


class UserAddedSystemMessage(t.TypedDict):
    type: t.Literal["user_added"]
    id: str
    by: str


class UserRemoveSystemMessage(t.TypedDict):
    type: t.Literal["user_remove"]
    id: str
    by: str


class UserJoinedSystemMessage(t.TypedDict):
    type: t.Literal["user_joined"]
    id: str


class UserLeftSystemMessage(t.TypedDict):
    type: t.Literal["user_left"]
    id: str


class UserKickedSystemMessage(t.TypedDict):
    type: t.Literal["user_kicked"]
    id: str


class UserBannedSystemMessage(t.TypedDict):
    type: t.Literal["user_banned"]
    id: str


class ChannelRenamedSystemMessage(t.TypedDict):
    type: t.Literal["channel_renamed"]
    by: str


class ChannelDescriptionChangedSystemMessage(t.TypedDict):
    type: t.Literal["channel_description_changed"]
    by: str


class ChannelIconChangedSystemMessage(t.TypedDict):
    type: t.Literal["channel_icon_changed"]
    by: str


ChannelOwnershipChangedSystemMessage = t.TypedDict(
    "ChannelOwnershipChangedSystemMessage",
    {"type": t.Literal["channel_ownership_changed"], "from": str, "to": str},
)

SystemMessage = (
    TextSystemMessage
    | UserAddedSystemMessage
    | UserRemoveSystemMessage
    | UserJoinedSystemMessage
    | UserLeftSystemMessage
    | UserKickedSystemMessage
    | UserBannedSystemMessage
    | ChannelRenamedSystemMessage
    | ChannelDescriptionChangedSystemMessage
    | ChannelIconChangedSystemMessage
    | ChannelOwnershipChangedSystemMessage
)


class Masquerade(t.TypedDict):
    name: t.NotRequired[str]
    avatar: t.NotRequired[str]
    colour: t.NotRequired[str]


class Interactions(t.TypedDict):
    reactions: t.NotRequired[list[str]]
    restrict_reactions: t.NotRequired[bool]


class AppendMessage(t.TypedDict):
    embeds: t.NotRequired[list[Embed]]


MessageSort = t.Literal["Relevance", "Latest", "Oldest"]


class SendableEmbed(t.TypedDict):
    icon_url: t.NotRequired[str]
    url: t.NotRequired[str]
    title: t.NotRequired[str]
    description: t.NotRequired[str]
    media: t.NotRequired[str]
    colour: t.NotRequired[str]


class ReplyIntent(t.TypedDict):
    id: str
    mention: bool


class DataMessageSend(t.TypedDict):
    content: t.NotRequired[str]
    attachments: t.NotRequired[list[str]]
    replies: t.NotRequired[list[ReplyIntent]]
    embeds: t.NotRequired[list[SendableEmbed]]
    masquerade: t.NotRequired[Masquerade]
    interactions: t.NotRequired[Interactions]
    flags: t.NotRequired[int]


class OptionsQueryMessages(t.TypedDict):
    limit: t.NotRequired[int]
    before: t.NotRequired[str]
    after: t.NotRequired[str]
    sort: t.NotRequired[MessageSort]
    nearby: t.NotRequired[str]
    include_users: t.NotRequired[Bool]


class DataMessageSearch(t.TypedDict):
    query: str
    limit: t.NotRequired[int]
    before: t.NotRequired[str]
    after: t.NotRequired[str]
    sort: t.NotRequired[MessageSort]
    include_users: t.NotRequired[Bool]


class DataEditMessage(t.TypedDict):
    content: t.NotRequired[str]
    embeds: t.NotRequired[list[SendableEmbed]]


class OptionsBulkDelete(t.TypedDict):
    ids: list[str]


class OptionsUnreact(t.TypedDict):
    user_id: t.NotRequired[str]
    remove_all: t.NotRequired[Bool]


__all__ = (
    "Message",
    "PartialMessage",
    "MessagesAndUsersBulkMessageResponse",
    "BulkMessageResponse",
    "TextSystemMessage",
    "UserAddedSystemMessage",
    "UserRemoveSystemMessage",
    "UserJoinedSystemMessage",
    "UserLeftSystemMessage",
    "UserKickedSystemMessage",
    "UserBannedSystemMessage",
    "ChannelRenamedSystemMessage",
    "ChannelDescriptionChangedSystemMessage",
    "ChannelIconChangedSystemMessage",
    "ChannelOwnershipChangedSystemMessage",
    "SystemMessage",
    "Masquerade",
    "Interactions",
    "AppendMessage",
    "MessageSort",
    "SendableEmbed",
    "ReplyIntent",
    "DataMessageSend",
    "OptionsQueryMessages",
    "DataMessageSearch",
    "DataEditMessage",
    "OptionsBulkDelete",
    "OptionsUnreact",
)
