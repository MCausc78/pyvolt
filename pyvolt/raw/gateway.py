from __future__ import annotations

import typing
import typing_extensions

from .authifier import (
    AuthifierCreateSessionEvent,
    AuthifierDeleteSessionEvent,
    AuthifierDeleteAllSessionsEvent,
)
from .channel_unreads import ChannelUnread
from .channel_webhooks import Webhook, PartialWebhook, FieldsWebhook
from .channels import (
    SavedMessagesChannel,
    DirectMessageChannel,
    GroupChannel,
    TextChannel,
    VoiceChannel,
    ServerChannel,
    Channel,
    PartialChannel,
    FieldsChannel,
)
from .emojis import ServerEmoji
from .messages import Message, PartialMessage, AppendMessage, FieldsMessage
from .safety_reports import CreatedReport
from .server_members import (
    Member,
    PartialMember,
    MemberCompositeKey,
    FieldsMember,
    RemovalIntention,
)
from .servers import Server, PartialServer, PartialRole, FieldsServer, FieldsRole
from .user_settings import UserSettings
from .users import User, PartialUser, FieldsUser


class ClientBulkEvent(typing.TypedDict):
    type: typing.Literal['Bulk']
    v: list[ClientEvent]


class ClientAuthenticatedEvent(typing.TypedDict):
    type: typing.Literal['Authenticated']


class ClientLogoutEvent(typing.TypedDict):
    type: typing.Literal['Logout']


class ClientReadyEvent(typing.TypedDict):
    type: typing.Literal['Ready']
    users: typing_extensions.NotRequired[list[User]]
    servers: typing_extensions.NotRequired[list[Server]]
    channels: typing_extensions.NotRequired[list[Channel]]
    members: typing_extensions.NotRequired[list[Member]]
    emojis: typing_extensions.NotRequired[list[ServerEmoji]]
    # Insert please....
    # me: User
    user_settings: typing_extensions.NotRequired[UserSettings]
    channel_unreads: typing_extensions.NotRequired[list[ChannelUnread]]


Ping = list[int] | int


class ClientPongEvent(typing.TypedDict):
    type: typing.Literal['Pong']
    data: Ping


class ClientMessageEvent(Message):
    type: typing.Literal['Message']


class ClientMessageUpdateEvent(typing.TypedDict):
    type: typing.Literal['MessageUpdate']
    id: str
    channel: str
    data: PartialMessage
    clear: list[FieldsMessage]


class ClientMessageAppendEvent(typing.TypedDict):
    type: typing.Literal['MessageAppend']
    id: str
    channel: str
    append: AppendMessage


class ClientMessageDeleteEvent(typing.TypedDict):
    type: typing.Literal['MessageDelete']
    id: str
    channel: str


class ClientMessageReactEvent(typing.TypedDict):
    type: typing.Literal['MessageReact']
    id: str
    channel_id: str
    user_id: str
    emoji_id: str


class ClientMessageUnreactEvent(typing.TypedDict):
    type: typing.Literal['MessageUnreact']
    id: str
    channel_id: str
    user_id: str
    emoji_id: str


class ClientMessageRemoveReactionEvent(typing.TypedDict):
    type: typing.Literal['MessageRemoveReaction']
    id: str
    channel_id: str
    emoji_id: str


class ClientBulkMessageDeleteEvent(typing.TypedDict):
    type: typing.Literal['BulkMessageDelete']
    channel: str
    ids: list[str]


class ClientServerCreateEvent(typing.TypedDict):
    type: typing.Literal['ServerCreate']
    id: str
    server: Server
    channels: list[ServerChannel]
    emojis: list[ServerEmoji]


class ClientServerUpdateEvent(typing.TypedDict):
    type: typing.Literal['ServerUpdate']
    id: str
    data: PartialServer
    clear: list[FieldsServer]


class ClientServerDeleteEvent(typing.TypedDict):
    type: typing.Literal['ServerDelete']
    id: str


class ClientServerMemberUpdateEvent(typing.TypedDict):
    type: typing.Literal['ServerMemberUpdate']
    id: MemberCompositeKey
    data: PartialMember
    clear: list[FieldsMember]


class ClientServerMemberJoinEvent(typing.TypedDict):
    type: typing.Literal['ServerMemberJoin']
    id: str
    user: str


class ClientServerMemberLeaveEvent(typing.TypedDict):
    type: typing.Literal['ServerMemberLeave']
    id: str
    user: str
    reason: RemovalIntention


class ClientServerRoleUpdateEvent(typing.TypedDict):
    type: typing.Literal['ServerRoleUpdate']
    id: str
    role_id: str
    data: PartialRole
    clear: list[FieldsRole]


class ClientServerRoleDeleteEvent(typing.TypedDict):
    type: typing.Literal['ServerRoleDelete']
    id: str
    role_id: str


class ClientUserUpdateEvent(typing.TypedDict):
    type: typing.Literal['UserUpdate']
    id: str
    data: PartialUser
    clear: list[FieldsUser]
    event_id: str | None


class ClientUserRelationshipEvent(typing.TypedDict):
    type: typing.Literal['UserRelationship']
    id: str
    user: User


class ClientUserSettingsUpdateEvent(typing.TypedDict):
    type: typing.Literal['UserSettingsUpdate']
    id: str
    update: UserSettings


class ClientUserPlatformWipeEvent(typing.TypedDict):
    type: typing.Literal['UserPlatformWipe']
    user_id: str
    flags: int


class ClientEmojiCreateEvent(ServerEmoji):
    type: typing.Literal['EmojiCreate']


class ClientEmojiDeleteEvent(typing.TypedDict):
    type: typing.Literal['EmojiDelete']
    id: str


# This event is weird...
# I would expect it to be dispatched to privileged users, but no.
# It ISN'T dispatched in WebSocket, never.
class ClientReportCreateEvent(CreatedReport):
    type: typing.Literal['ReportCreate']


class ClientSavedMessagesChannelCreateEvent(SavedMessagesChannel):
    type: typing.Literal['ChannelCreate']


class ClientDirectMessageChannelCreateEvent(DirectMessageChannel):
    type: typing.Literal['ChannelCreate']


class ClientGroupChannelCreateEvent(GroupChannel):
    type: typing.Literal['ChannelCreate']


class ClientTextChannelCreateEvent(TextChannel):
    type: typing.Literal['ChannelCreate']


class ClientVoiceChannelCreateEvent(VoiceChannel):
    type: typing.Literal['ChannelCreate']


ClientChannelCreateEvent = (
    ClientSavedMessagesChannelCreateEvent
    | ClientDirectMessageChannelCreateEvent
    | ClientGroupChannelCreateEvent
    | ClientTextChannelCreateEvent
    | ClientVoiceChannelCreateEvent
)


class ClientChannelUpdateEvent(typing.TypedDict):
    type: typing.Literal['ChannelUpdate']
    id: str
    data: PartialChannel
    clear: list[FieldsChannel]


class ClientChannelDeleteEvent(typing.TypedDict):
    type: typing.Literal['ChannelDelete']
    id: str


class ClientChannelGroupJoinEvent(typing.TypedDict):
    type: typing.Literal['ChannelGroupJoin']
    id: str
    user: str


class ClientChannelGroupLeaveEvent(typing.TypedDict):
    type: typing.Literal['ChannelGroupLeave']
    id: str
    user: str


class ClientChannelStartTypingEvent(typing.TypedDict):
    type: typing.Literal['ChannelStartTyping']
    id: str
    user: str


class ClientChannelStopTypingEvent(typing.TypedDict):
    type: typing.Literal['ChannelStopTyping']
    id: str
    user: str


class ClientChannelAckEvent(typing.TypedDict):
    type: typing.Literal['ChannelAck']
    id: str
    user: str
    message_id: str


class ClientWebhookCreateEvent(Webhook):
    type: typing.Literal['WebhookCreate']


class ClientWebhookUpdateEvent(typing.TypedDict):
    type: typing.Literal['WebhookUpdate']
    id: str
    data: PartialWebhook
    remove: list[FieldsWebhook]


class ClientWebhookDeleteEvent(typing.TypedDict):
    type: typing.Literal['WebhookDelete']
    id: str


class ClientCreateSessionAuthEvent(AuthifierCreateSessionEvent):
    type: typing.Literal['Auth']


class ClientDeleteSessionAuthEvent(AuthifierDeleteSessionEvent):
    type: typing.Literal['Auth']


class ClientDeleteAllSessionsAuthEvent(AuthifierDeleteAllSessionsEvent):
    type: typing.Literal['Auth']


ClientAuthEvent = ClientCreateSessionAuthEvent | ClientDeleteSessionAuthEvent | ClientDeleteAllSessionsAuthEvent

ClientEvent = (
    ClientBulkEvent
    | ClientAuthenticatedEvent
    | ClientLogoutEvent
    | ClientReadyEvent
    | ClientPongEvent
    | ClientMessageEvent
    | ClientMessageUpdateEvent
    | ClientMessageAppendEvent
    | ClientMessageDeleteEvent
    | ClientMessageReactEvent
    | ClientMessageUnreactEvent
    | ClientMessageRemoveReactionEvent
    | ClientBulkMessageDeleteEvent
    | ClientServerCreateEvent
    | ClientServerUpdateEvent
    | ClientServerDeleteEvent
    | ClientServerMemberUpdateEvent
    | ClientServerMemberJoinEvent
    | ClientServerMemberLeaveEvent
    | ClientServerRoleUpdateEvent
    | ClientServerRoleDeleteEvent
    | ClientUserUpdateEvent
    | ClientUserRelationshipEvent
    | ClientUserSettingsUpdateEvent
    | ClientUserPlatformWipeEvent
    | ClientEmojiCreateEvent
    | ClientEmojiDeleteEvent
    # | ClientReportCreateEvent
    | ClientChannelCreateEvent
    | ClientChannelUpdateEvent
    | ClientChannelDeleteEvent
    | ClientChannelGroupJoinEvent
    | ClientChannelGroupLeaveEvent
    | ClientChannelStartTypingEvent
    | ClientChannelStopTypingEvent
    | ClientChannelAckEvent
    | ClientWebhookCreateEvent
    | ClientWebhookUpdateEvent
    | ClientWebhookDeleteEvent
    | ClientAuthEvent
)


class ServerAuthenticateEvent(typing.TypedDict):
    type: typing.Literal['Authenticate']
    token: str


class ServerBeginTypingEvent(typing.TypedDict):
    type: typing.Literal['BeginTyping']
    channel: str


class ServerEndTypingEvent(typing.TypedDict):
    type: typing.Literal['EndTyping']
    channel: str


class ServerSubscribeEvent(typing.TypedDict):
    type: typing.Literal['Subscribe']
    server_id: str


class ServerPingEvent(typing.TypedDict):
    type: typing.Literal['Ping']
    data: Ping


ServerEvent = (
    ServerAuthenticateEvent | ServerBeginTypingEvent | ServerEndTypingEvent | ServerSubscribeEvent | ServerPingEvent
)


class BonfireConnectionParameters(typing.TypedDict):
    version: typing.Literal['1']
    format: typing.Literal['json', 'msgpack']
    token: typing_extensions.NotRequired[str]
    __user_settings_keys: typing_extensions.NotRequired[str]


__all__ = (
    'ClientBulkEvent',
    'ClientAuthenticatedEvent',
    'ClientLogoutEvent',
    'ClientReadyEvent',
    'Ping',
    'ClientPongEvent',
    'ClientMessageEvent',
    'ClientMessageUpdateEvent',
    'ClientMessageAppendEvent',
    'ClientMessageDeleteEvent',
    'ClientMessageReactEvent',
    'ClientMessageUnreactEvent',
    'ClientMessageRemoveReactionEvent',
    'ClientBulkMessageDeleteEvent',
    'ClientServerCreateEvent',
    'ClientServerUpdateEvent',
    'ClientServerDeleteEvent',
    'ClientServerMemberUpdateEvent',
    'ClientServerMemberJoinEvent',
    'ClientServerMemberLeaveEvent',
    'ClientServerRoleUpdateEvent',
    'ClientServerRoleDeleteEvent',
    'ClientUserUpdateEvent',
    'ClientUserRelationshipEvent',
    'ClientUserSettingsUpdateEvent',
    'ClientUserPlatformWipeEvent',
    'ClientEmojiCreateEvent',
    'ClientEmojiDeleteEvent',
    'ClientSavedMessagesChannelCreateEvent',
    'ClientDirectMessageChannelCreateEvent',
    'ClientGroupChannelCreateEvent',
    'ClientTextChannelCreateEvent',
    'ClientVoiceChannelCreateEvent',
    'ClientChannelCreateEvent',
    'ClientChannelUpdateEvent',
    'ClientChannelDeleteEvent',
    'ClientChannelGroupJoinEvent',
    'ClientChannelGroupLeaveEvent',
    'ClientChannelStartTypingEvent',
    'ClientChannelStopTypingEvent',
    'ClientChannelAckEvent',
    'ClientWebhookCreateEvent',
    'ClientWebhookUpdateEvent',
    'ClientWebhookDeleteEvent',
    'ClientCreateSessionAuthEvent',
    'ClientDeleteSessionAuthEvent',
    'ClientDeleteAllSessionsAuthEvent',
    'ClientAuthEvent',
    'ClientEvent',
    'ServerAuthenticateEvent',
    'ServerBeginTypingEvent',
    'ServerEndTypingEvent',
    'ServerSubscribeEvent',
    'ServerPingEvent',
    'ServerEvent',
    'BonfireConnectionParameters',
)
