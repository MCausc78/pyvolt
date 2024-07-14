from __future__ import annotations

import typing as t

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
    Channel,
    PartialChannel,
    FieldsChannel,
)
from .emojis import ServerEmoji
from .messages import Message, PartialMessage, AppendMessage
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


class ClientBulkEvent(t.TypedDict):
    type: t.Literal["Bulk"]
    v: list[ClientEvent]


class ClientAuthenticatedEvent(t.TypedDict):
    type: t.Literal["Authenticated"]


class ClientLogoutEvent(t.TypedDict):
    type: t.Literal["Logout"]


class ClientReadyEvent(t.TypedDict):
    type: t.Literal["Ready"]
    users: t.NotRequired[list[User]]
    servers: t.NotRequired[list[Server]]
    channels: t.NotRequired[list[Channel]]
    members: t.NotRequired[list[Member]]
    emojis: t.NotRequired[list[ServerEmoji]]
    # Insert please....
    # me: User
    user_settings: t.NotRequired[UserSettings]
    channel_unreads: t.NotRequired[list[ChannelUnread]]


Ping = list[int] | int


class ClientPongEvent(t.TypedDict):
    type: t.Literal["Pong"]
    data: Ping


class ClientMessageEvent(Message):
    type: t.Literal["Message"]


class ClientMessageUpdateEvent(t.TypedDict):
    type: t.Literal["MessageUpdate"]
    id: str
    channel: str
    data: PartialMessage


class ClientMessageAppendEvent(t.TypedDict):
    type: t.Literal["MessageAppend"]
    id: str
    channel: str
    append: AppendMessage


class ClientMessageDeleteEvent(t.TypedDict):
    type: t.Literal["MessageDelete"]
    id: str
    channel: str


class ClientMessageReactEvent(t.TypedDict):
    type: t.Literal["MessageReact"]
    id: str
    channel_id: str
    user_id: str
    emoji_id: str


class ClientMessageUnreactEvent(t.TypedDict):
    type: t.Literal["MessageUnreact"]
    id: str
    channel_id: str
    user_id: str
    emoji_id: str


class ClientMessageRemoveReactionEvent(t.TypedDict):
    type: t.Literal["MessageRemoveReaction"]
    id: str
    channel_id: str
    emoji_id: str


class ClientBulkMessageDeleteEvent(t.TypedDict):
    type: t.Literal["BulkMessageDelete"]
    channel: str
    ids: list[str]


class ClientServerCreateEvent(t.TypedDict):
    type: t.Literal["ServerCreate"]
    id: str
    server: Server
    channels: list[Channel]
    emojis: list[ServerEmoji]


class ClientServerUpdateEvent(t.TypedDict):
    type: t.Literal["ServerUpdate"]
    id: str
    data: PartialServer
    clear: list[FieldsServer]


class ClientServerDeleteEvent(t.TypedDict):
    type: t.Literal["ServerDelete"]
    id: str


class ClientServerMemberUpdateEvent(t.TypedDict):
    type: t.Literal["ServerMemberUpdate"]
    id: MemberCompositeKey
    data: PartialMember
    clear: list[FieldsMember]


class ClientServerMemberJoinEvent(t.TypedDict):
    type: t.Literal["ServerMemberJoin"]
    id: str
    user: str


class ClientServerMemberLeaveEvent(t.TypedDict):
    type: t.Literal["ServerMemberLeave"]
    id: str
    user: str
    reason: RemovalIntention


class ClientServerRoleUpdateEvent(t.TypedDict):
    type: t.Literal["ServerRoleUpdate"]
    id: str
    role_id: str
    data: PartialRole
    clear: list[FieldsRole]


class ClientServerRoleDeleteEvent(t.TypedDict):
    type: t.Literal["ServerRoleDelete"]
    id: str
    role_id: str


class ClientUserUpdateEvent(t.TypedDict):
    type: t.Literal["UserUpdate"]
    id: str
    data: PartialUser
    clear: list[FieldsUser]
    event_id: str | None


class ClientUserRelationshipEvent(t.TypedDict):
    type: t.Literal["UserRelationship"]
    id: str
    user: User


class ClientUserSettingsUpdateEvent(t.TypedDict):
    type: t.Literal["UserSettingsUpdate"]
    id: str
    update: UserSettings


class ClientUserPlatformWipeEvent(t.TypedDict):
    type: t.Literal["UserPlatformWipe"]
    user_id: str
    flags: int


class ClientEmojiCreateEvent(ServerEmoji):
    type: t.Literal["EmojiCreate"]


class ClientEmojiDeleteEvent(t.TypedDict):
    type: t.Literal["EmojiDelete"]
    id: str


class ClientReportCreateEvent(CreatedReport):
    type: t.Literal["ReportCreate"]


class ClientSavedMessagesChannelCreateEvent(SavedMessagesChannel):
    type: t.Literal["ChannelCreate"]


class ClientDirectMessageChannelCreateEvent(DirectMessageChannel):
    type: t.Literal["ChannelCreate"]


class ClientGroupChannelCreateEvent(GroupChannel):
    type: t.Literal["ChannelCreate"]


class ClientTextChannelCreateEvent(TextChannel):
    type: t.Literal["ChannelCreate"]


class ClientVoiceChannelCreateEvent(VoiceChannel):
    type: t.Literal["ChannelCreate"]


ClientChannelCreateEvent = (
    ClientSavedMessagesChannelCreateEvent
    | ClientDirectMessageChannelCreateEvent
    | ClientGroupChannelCreateEvent
    | ClientTextChannelCreateEvent
    | ClientVoiceChannelCreateEvent
)


class ClientChannelUpdateEvent(t.TypedDict):
    type: t.Literal["ChannelUpdate"]
    id: str
    data: PartialChannel
    clear: list[FieldsChannel]


class ClientChannelDeleteEvent(t.TypedDict):
    type: t.Literal["ChannelDelete"]
    id: str


class ClientChannelGroupJoinEvent(t.TypedDict):
    type: t.Literal["ChannelGroupJoin"]
    id: str
    user: str


class ClientChannelGroupLeaveEvent(t.TypedDict):
    type: t.Literal["ChannelGroupLeave"]
    id: str
    user: str


class ClientChannelStartTypingEvent(t.TypedDict):
    type: t.Literal["ChannelStartTyping"]
    id: str
    user: str


class ClientChannelStopTypingEvent(t.TypedDict):
    type: t.Literal["ChannelStopTyping"]
    id: str
    user: str


class ClientChannelAckEvent(t.TypedDict):
    type: t.Literal["ChannelAck"]
    id: str
    user: str
    message_id: str


class ClientWebhookCreateEvent(Webhook):
    type: t.Literal["WebhookCreate"]


class ClientWebhookUpdateEvent(t.TypedDict):
    type: t.Literal["WebhookUpdate"]
    id: str
    data: PartialWebhook
    remove: list[FieldsWebhook]


class ClientWebhookDeleteEvent(t.TypedDict):
    type: t.Literal["WebhookDelete"]
    id: str


class ClientCreateSessionAuthEvent(AuthifierCreateSessionEvent):
    type: t.Literal["Auth"]


class ClientDeleteSessionAuthEvent(AuthifierDeleteSessionEvent):
    type: t.Literal["Auth"]


class ClientDeleteAllSessionsAuthEvent(AuthifierDeleteAllSessionsEvent):
    type: t.Literal["Auth"]


ClientAuthEvent = (
    ClientCreateSessionAuthEvent
    | ClientDeleteSessionAuthEvent
    | ClientDeleteAllSessionsAuthEvent
)

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
    | ClientReportCreateEvent
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


class ServerAuthenticateEvent(t.TypedDict):
    type: t.Literal["Authenticate"]
    token: str


class ServerBeginTypingEvent(t.TypedDict):
    type: t.Literal["BeginTyping"]
    channel: str


class ServerEndTypingEvent(t.TypedDict):
    type: t.Literal["EndTyping"]
    channel: str


class ServerSubscribeEvent(t.TypedDict):
    type: t.Literal["Subscribe"]
    server_id: str


class ServerPingEvent(t.TypedDict):
    type: t.Literal["Ping"]
    data: Ping


ServerEvent = (
    ServerAuthenticateEvent
    | ServerBeginTypingEvent
    | ServerEndTypingEvent
    | ServerSubscribeEvent
    | ServerPingEvent
)
