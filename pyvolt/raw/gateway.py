from __future__ import annotations

import typing as t

from . import (
    authifier,
    channel_webhooks,
    channels,
    emojis,
    messages,
    safety_reports,
    server_members,
    servers,
    user_settings,
    users,
)


class ClientBulkEvent(t.TypedDict):
    type: t.Literal["Bulk"]
    v: list[ClientEvent]


class ClientAuthenticatedEvent(t.TypedDict):
    type: t.Literal["Authenticated"]


class ClientLogoutEvent(t.TypedDict):
    type: t.Literal["Logout"]


class ClientReadyEvent(t.TypedDict):
    type: t.Literal["Ready"]
    users: list[users.User]
    servers: list[servers.Server]
    channels: list[channels.Channel]
    members: list[server_members.Member]
    emojis: list[emojis.ServerEmoji]


Ping = list[int] | int


class ClientPongEvent(t.TypedDict):
    type: t.Literal["Pong"]
    data: Ping


class ClientMessageEvent(messages.Message):
    type: t.Literal["Message"]


class ClientMessageUpdateEvent(t.TypedDict):
    type: t.Literal["MessageUpdate"]
    id: str
    channel: str
    data: messages.PartialMessage


class ClientMessageAppendEvent(t.TypedDict):
    type: t.Literal["MessageAppend"]
    id: str
    channel: str
    append: messages.AppendMessage


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
    server: servers.Server
    channels: list[channels.Channel]
    emojis: list[emojis.ServerEmoji]


class ClientServerUpdateEvent(t.TypedDict):
    type: t.Literal["ServerUpdate"]
    id: str
    data: servers.PartialServer
    clear: list[servers.FieldsServer]


class ClientServerDeleteEvent(t.TypedDict):
    type: t.Literal["ServerDelete"]
    id: str


class ClientServerMemberUpdateEvent(t.TypedDict):
    type: t.Literal["ServerMemberUpdate"]
    id: server_members.MemberCompositeKey
    data: server_members.PartialMember
    clear: list[server_members.FieldsMember]


class ClientServerMemberJoinEvent(t.TypedDict):
    type: t.Literal["ServerMemberJoin"]
    id: str
    user: str


class ClientServerMemberLeaveEvent(t.TypedDict):
    type: t.Literal["ServerMemberLeave"]
    id: str
    user: str


class ClientServerRoleUpdateEvent(t.TypedDict):
    type: t.Literal["ServerRoleUpdate"]
    id: str
    role_id: str
    data: servers.PartialRole
    clear: list[servers.FieldsRole]


class ClientServerRoleDeleteEvent(t.TypedDict):
    type: t.Literal["ServerRoleDelete"]
    id: str
    role_id: str


class ClientUserUpdateEvent(t.TypedDict):
    type: t.Literal["UserUpdate"]
    id: str
    data: users.PartialUser
    clear: list[users.FieldsUser]
    event_id: str | None


class ClientUserRelationshipEvent(t.TypedDict):
    type: t.Literal["UserRelationship"]
    id: str
    user: users.User


class ClientUserSettingsUpdateEvent(t.TypedDict):
    type: t.Literal["UserSettingsUpdate"]
    id: str
    update: user_settings.UserSettings


class ClientUserPlatformWipeEvent(t.TypedDict):
    type: t.Literal["UserPlatformWipe"]
    user_id: str
    flags: int


class ClientEmojiCreateEvent(emojis.ServerEmoji):
    type: t.Literal["EmojiCreate"]


class ClientEmojiDeleteEvent(t.TypedDict):
    type: t.Literal["EmojiDelete"]
    id: str


class ClientReportCreateEvent(safety_reports.CreatedReport):
    type: t.Literal["ReportCreate"]


class ClientSavedMessagesChannelCreateEvent(channels.SavedMessagesChannel):
    type: t.Literal["ChannelCreate"]


class ClientDirectMessageChannelCreateEvent(channels.DirectMessageChannel):
    type: t.Literal["ChannelCreate"]


class ClientGroupChannelCreateEvent(channels.GroupChannel):
    type: t.Literal["ChannelCreate"]


class ClientTextChannelCreateEvent(channels.TextChannel):
    type: t.Literal["ChannelCreate"]


class ClientVoiceChannelCreateEvent(channels.VoiceChannel):
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
    data: channels.PartialChannel
    clear: list[channels.FieldsChannel]


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


class ClientWebhookCreateEvent(channel_webhooks.Webhook):
    type: t.Literal["WebhookCreate"]


class ClientWebhookUpdateEvent(t.TypedDict):
    type: t.Literal["WebhookUpdate"]
    id: str
    data: channel_webhooks.PartialWebhook
    remove: list[channel_webhooks.FieldsWebhook]


class ClientWebhookDeleteEvent(t.TypedDict):
    type: t.Literal["WebhookDelete"]
    id: str


class ClientCreateSessionAuthEvent(authifier.AuthifierCreateSessionEvent):
    type: t.Literal["Auth"]


class ClientDeleteSessionAuthEvent(authifier.AuthifierDeleteSessionEvent):
    type: t.Literal["Auth"]


class ClientDeleteAllSessionsAuthEvent(authifier.AuthifierDeleteAllSessionsEvent):
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
