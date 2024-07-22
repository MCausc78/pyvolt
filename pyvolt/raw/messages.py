from __future__ import annotations

import typing

from .basic import Bool
from .channel_webhooks import MessageWebhook
from .embeds import Embed
from .files import File
from .server_members import Member
from .users import User


class Message(typing.TypedDict):
    _id: str
    nonce: typing.NotRequired[str]
    channel: str
    author: str
    user: typing.NotRequired[User]
    member: typing.NotRequired[Member]
    webhook: typing.NotRequired[MessageWebhook]
    content: typing.NotRequired[str]
    system: typing.NotRequired[SystemMessage]
    attachments: typing.NotRequired[list[File]]
    edited: typing.NotRequired[str]
    embeds: typing.NotRequired[list[Embed]]
    mentions: typing.NotRequired[list[str]]
    replies: typing.NotRequired[list[str]]
    reactions: typing.NotRequired[dict[str, list[str]]]
    interactions: typing.NotRequired[Interactions]
    masquerade: typing.NotRequired[Masquerade]
    pinned: typing.NotRequired[bool]
    flags: typing.NotRequired[int]


class PartialMessage(typing.TypedDict):
    content: typing.NotRequired[str]
    edited: typing.NotRequired[str]
    embeds: typing.NotRequired[list[Embed]]
    pinned: typing.NotRequired[bool]
    reactions: typing.NotRequired[dict[str, list[str]]]


class MessagesAndUsersBulkMessageResponse(typing.TypedDict):
    messages: list[Message]
    users: list[User]
    members: typing.NotRequired[list[Member]]


BulkMessageResponse = list[Message] | MessagesAndUsersBulkMessageResponse


class TextSystemMessage(typing.TypedDict):
    type: typing.Literal['text']
    content: str


class UserAddedSystemMessage(typing.TypedDict):
    type: typing.Literal['user_added']
    id: str
    by: str


class UserRemoveSystemMessage(typing.TypedDict):
    type: typing.Literal['user_remove']
    id: str
    by: str


class UserJoinedSystemMessage(typing.TypedDict):
    type: typing.Literal['user_joined']
    id: str


class UserLeftSystemMessage(typing.TypedDict):
    type: typing.Literal['user_left']
    id: str


class UserKickedSystemMessage(typing.TypedDict):
    type: typing.Literal['user_kicked']
    id: str


class UserBannedSystemMessage(typing.TypedDict):
    type: typing.Literal['user_banned']
    id: str


class ChannelRenamedSystemMessage(typing.TypedDict):
    type: typing.Literal['channel_renamed']
    by: str


class ChannelDescriptionChangedSystemMessage(typing.TypedDict):
    type: typing.Literal['channel_description_changed']
    by: str


class ChannelIconChangedSystemMessage(typing.TypedDict):
    type: typing.Literal['channel_icon_changed']
    by: str


ChannelOwnershipChangedSystemMessage = typing.TypedDict(
    'ChannelOwnershipChangedSystemMessage',
    {'type': typing.Literal['channel_ownership_changed'], 'from': str, 'to': str},
)


class MessagePinnedSystemMessage(typing.TypedDict):
    type: typing.Literal['message_pinned']
    id: str
    by: str


class MessageUnpinnedSystemMessage(typing.TypedDict):
    type: typing.Literal['message_unpinned']
    id: str
    by: str


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
    | MessagePinnedSystemMessage
    | MessageUnpinnedSystemMessage
)


class Masquerade(typing.TypedDict):
    name: typing.NotRequired[str]
    avatar: typing.NotRequired[str]
    colour: typing.NotRequired[str]


class Interactions(typing.TypedDict):
    reactions: typing.NotRequired[list[str]]
    restrict_reactions: typing.NotRequired[bool]


class AppendMessage(typing.TypedDict):
    embeds: typing.NotRequired[list[Embed]]


MessageSort = typing.Literal['Relevance', 'Latest', 'Oldest']


class SendableEmbed(typing.TypedDict):
    icon_url: typing.NotRequired[str]
    url: typing.NotRequired[str]
    title: typing.NotRequired[str]
    description: typing.NotRequired[str]
    media: typing.NotRequired[str]
    colour: typing.NotRequired[str]


class ReplyIntent(typing.TypedDict):
    id: str
    mention: bool


class DataMessageSend(typing.TypedDict):
    content: typing.NotRequired[str]
    attachments: typing.NotRequired[list[str]]
    replies: typing.NotRequired[list[ReplyIntent]]
    embeds: typing.NotRequired[list[SendableEmbed]]
    masquerade: typing.NotRequired[Masquerade]
    interactions: typing.NotRequired[Interactions]
    flags: typing.NotRequired[int]


class OptionsQueryMessages(typing.TypedDict):
    limit: typing.NotRequired[int]
    before: typing.NotRequired[str]
    after: typing.NotRequired[str]
    sort: typing.NotRequired[MessageSort]
    nearby: typing.NotRequired[str]
    include_users: typing.NotRequired[Bool]


class DataMessageSearch(typing.TypedDict):
    query: typing.NotRequired[str]
    pinned: typing.NotRequired[bool]
    limit: typing.NotRequired[int]
    before: typing.NotRequired[str]
    after: typing.NotRequired[str]
    sort: typing.NotRequired[MessageSort]
    include_users: typing.NotRequired[bool]


class DataEditMessage(typing.TypedDict):
    content: typing.NotRequired[str]
    embeds: typing.NotRequired[list[SendableEmbed]]


class OptionsBulkDelete(typing.TypedDict):
    ids: list[str]


class OptionsUnreact(typing.TypedDict):
    user_id: typing.NotRequired[str]
    remove_all: typing.NotRequired[Bool]


FieldsMessage = typing.Literal['Pinned']

__all__ = (
    'Message',
    'PartialMessage',
    'MessagesAndUsersBulkMessageResponse',
    'BulkMessageResponse',
    'TextSystemMessage',
    'UserAddedSystemMessage',
    'UserRemoveSystemMessage',
    'UserJoinedSystemMessage',
    'UserLeftSystemMessage',
    'UserKickedSystemMessage',
    'UserBannedSystemMessage',
    'ChannelRenamedSystemMessage',
    'ChannelDescriptionChangedSystemMessage',
    'ChannelIconChangedSystemMessage',
    'ChannelOwnershipChangedSystemMessage',
    'MessagePinnedSystemMessage',
    'MessageUnpinnedSystemMessage',
    'SystemMessage',
    'Masquerade',
    'Interactions',
    'AppendMessage',
    'MessageSort',
    'SendableEmbed',
    'ReplyIntent',
    'DataMessageSend',
    'OptionsQueryMessages',
    'DataMessageSearch',
    'DataEditMessage',
    'OptionsBulkDelete',
    'OptionsUnreact',
    'FieldsMessage',
)
