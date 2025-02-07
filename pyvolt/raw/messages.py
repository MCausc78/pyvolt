from __future__ import annotations

import typing
import typing_extensions

from .basic import Bool
from .channel_webhooks import MessageWebhook
from .embeds import Embed
from .files import File
from .server_members import Member
from .users import User


class Message(typing.TypedDict):
    _id: str
    nonce: typing_extensions.NotRequired[str]
    channel: str
    author: str
    user: typing_extensions.NotRequired[User]
    member: typing_extensions.NotRequired[Member]
    webhook: typing_extensions.NotRequired[MessageWebhook]
    content: typing_extensions.NotRequired[str]
    system: typing_extensions.NotRequired[SystemMessage]
    attachments: typing_extensions.NotRequired[list[File]]
    edited: typing_extensions.NotRequired[str]
    embeds: typing_extensions.NotRequired[list[Embed]]
    mentions: typing_extensions.NotRequired[list[str]]
    role_mentions: typing_extensions.NotRequired[list[str]]
    replies: typing_extensions.NotRequired[list[str]]
    reactions: typing_extensions.NotRequired[dict[str, list[str]]]
    interactions: typing_extensions.NotRequired[Interactions]
    masquerade: typing_extensions.NotRequired[Masquerade]
    pinned: typing_extensions.NotRequired[bool]
    flags: typing_extensions.NotRequired[int]


class PartialMessage(typing.TypedDict):
    content: typing_extensions.NotRequired[str]
    edited: typing_extensions.NotRequired[str]
    embeds: typing_extensions.NotRequired[list[Embed]]
    pinned: typing_extensions.NotRequired[bool]
    reactions: typing_extensions.NotRequired[dict[str, list[str]]]


class MessagesAndUsersBulkMessageResponse(typing.TypedDict):
    messages: list[Message]
    users: list[User]
    members: typing_extensions.NotRequired[list[Member]]


BulkMessageResponse = typing.Union[list[Message], MessagesAndUsersBulkMessageResponse]


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
    name: str
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


class CallStartedSystemMessage(typing.TypedDict):
    type: typing.Literal['call_started']
    by: str


SystemMessage = typing.Union[
    TextSystemMessage,
    UserAddedSystemMessage,
    UserRemoveSystemMessage,
    UserJoinedSystemMessage,
    UserLeftSystemMessage,
    UserKickedSystemMessage,
    UserBannedSystemMessage,
    ChannelRenamedSystemMessage,
    ChannelDescriptionChangedSystemMessage,
    ChannelIconChangedSystemMessage,
    ChannelOwnershipChangedSystemMessage,
    MessagePinnedSystemMessage,
    MessageUnpinnedSystemMessage,
    CallStartedSystemMessage,
]


class Masquerade(typing.TypedDict):
    name: typing_extensions.NotRequired[str]
    avatar: typing_extensions.NotRequired[str]
    colour: typing_extensions.NotRequired[str]


class Interactions(typing.TypedDict):
    reactions: typing_extensions.NotRequired[list[str]]
    restrict_reactions: typing_extensions.NotRequired[bool]


class AppendMessage(typing.TypedDict):
    embeds: typing_extensions.NotRequired[list[Embed]]


MessageSort = typing.Literal['Relevance', 'Latest', 'Oldest']


class SendableEmbed(typing.TypedDict):
    icon_url: typing_extensions.NotRequired[str]
    url: typing_extensions.NotRequired[str]
    title: typing_extensions.NotRequired[str]
    description: typing_extensions.NotRequired[str]
    media: typing_extensions.NotRequired[str]
    colour: typing_extensions.NotRequired[str]


class ReplyIntent(typing.TypedDict):
    id: str
    mention: bool


class DataMessageSend(typing.TypedDict):
    content: typing_extensions.NotRequired[str]
    attachments: typing_extensions.NotRequired[list[str]]
    replies: typing_extensions.NotRequired[list[ReplyIntent]]
    embeds: typing_extensions.NotRequired[list[SendableEmbed]]
    masquerade: typing_extensions.NotRequired[Masquerade]
    interactions: typing_extensions.NotRequired[Interactions]
    flags: typing_extensions.NotRequired[int]


class OptionsQueryMessages(typing.TypedDict):
    limit: typing_extensions.NotRequired[int]
    before: typing_extensions.NotRequired[str]
    after: typing_extensions.NotRequired[str]
    sort: typing_extensions.NotRequired[MessageSort]
    nearby: typing_extensions.NotRequired[str]
    include_users: typing_extensions.NotRequired[Bool]


class DataMessageSearch(typing.TypedDict):
    query: typing_extensions.NotRequired[str]
    pinned: typing_extensions.NotRequired[bool]
    limit: typing_extensions.NotRequired[int]
    before: typing_extensions.NotRequired[str]
    after: typing_extensions.NotRequired[str]
    sort: typing_extensions.NotRequired[MessageSort]
    include_users: typing_extensions.NotRequired[bool]


class DataEditMessage(typing.TypedDict):
    content: typing_extensions.NotRequired[str]
    embeds: typing_extensions.NotRequired[list[SendableEmbed]]


class OptionsBulkDelete(typing.TypedDict):
    ids: list[str]


class OptionsUnreact(typing.TypedDict):
    user_id: typing_extensions.NotRequired[str]
    remove_all: typing_extensions.NotRequired[Bool]


FieldsMessage = typing.Literal['Pinned']
