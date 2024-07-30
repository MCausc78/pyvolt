"""
The MIT License (MIT)

Copyright (c) 2024-present MCausc78

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

from attrs import define, field
from copy import copy
from datetime import datetime
import typing

from . import cache as caching

from .auth import Session
from .channel import (
    PartialChannel,
    DMChannel,
    GroupChannel,
    PrivateChannel,
    ServerTextChannel,
    ServerChannel,
    Channel,
)
from .emoji import ServerEmoji, DetachedEmoji
from .message import PartialMessage, MessageAppendData, Message
from .read_state import ReadState
from .server import (
    PartialRole,
    Role,
    PartialServer,
    Server,
    PartialMember,
    Member,
    MemberRemovalIntention,
)
from .shard import Shard
from .user_settings import UserSettings
from .user import (
    UserFlags,
    RelationshipStatus,
    Relationship,
    PartialUser,
    User,
    OwnUser,
)
from .webhook import Webhook, PartialWebhook


@define(slots=True)
class BaseEvent:
    shard: Shard = field(repr=True, kw_only=True)
    is_cancelled: bool = field(default=False, repr=True, kw_only=True)

    def set_cancelled(self, value: bool, /) -> bool:
        """Whether to cancel event processing (updating cache) or not."""
        if self.is_cancelled is value:
            return False
        self.is_cancelled = value
        return True

    def cancel(self) -> bool:
        """Cancels the event processing (updating cache)."""
        return self.set_cancelled(True)

    def uncancel(self, value: bool, /) -> bool:
        """Uncancels the event processing (updating cache)."""
        return self.set_cancelled(False)

    async def abefore_dispatch(self) -> None:
        pass

    def before_dispatch(self) -> None:
        pass

    async def aprocess(self) -> typing.Any:
        pass

    def process(self) -> typing.Any:
        pass


@define(slots=True)
class ReadyEvent(BaseEvent):
    users: list[User] = field(repr=True, kw_only=True)
    servers: list[Server] = field(repr=True, kw_only=True)
    channels: list[Channel] = field(repr=True, kw_only=True)
    members: list[Member] = field(repr=True, kw_only=True)
    emojis: list[ServerEmoji] = field(repr=True, kw_only=True)

    me: OwnUser = field(repr=True, kw_only=True)
    user_settings: UserSettings = field(repr=True, kw_only=True)
    read_states: list[ReadState] = field(repr=True, kw_only=True)

    def before_dispatch(self) -> None:
        # People expect bot.me to be available upon `ReadyEvent` dispatching
        state = self.shard.state
        state._me = self.me
        state._settings = self.user_settings

    def process(self) -> bool:
        state = self.shard.state
        cache = state.cache

        if not cache:
            return False

        for u in self.users:
            cache.store_user(u, caching._READY)

        for s in self.servers:
            cache.store_server(s, caching._READY)

        for channel in self.channels:
            cache.store_channel(channel, caching._READY)
            if channel.__class__ is DMChannel or isinstance(channel, DMChannel):
                cache.store_private_channel_by_user(channel, caching._READY)  # type: ignore

        for m in self.members:
            cache.store_server_member(m, caching._READY)

        for e in self.emojis:
            cache.store_emoji(e, caching._READY)

        for rs in self.read_states:
            cache.store_read_state(rs, caching._READY)

        return True


@define(slots=True)
class BaseChannelCreateEvent(BaseEvent):
    pass


@define(slots=True)
class PrivateChannelCreateEvent(BaseChannelCreateEvent):
    channel: PrivateChannel = field(repr=True, kw_only=True)

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False

        channel = self.channel
        cache.store_channel(channel, caching._CHANNEL_CREATE)

        if isinstance(channel, DMChannel):
            cache.store_private_channel_by_user(channel, caching._CHANNEL_CREATE)

        return True


@define(slots=True)
class ServerChannelCreateEvent(BaseChannelCreateEvent):
    channel: ServerChannel = field(repr=True, kw_only=True)

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False

        cache.store_channel(self.channel, caching._CHANNEL_CREATE)
        return True


ChannelCreateEvent = PrivateChannelCreateEvent | ServerChannelCreateEvent


@define(slots=True)
class ChannelUpdateEvent(BaseEvent):
    channel: PartialChannel = field(repr=True, kw_only=True)

    before: Channel | None = field(repr=True, kw_only=True)
    after: Channel | None = field(repr=True, kw_only=True)

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        before = cache.get_channel(self.channel.id, caching._CHANNEL_UPDATE)
        self.before = before
        if not before:
            return

        after = copy(before)
        after._update(self.channel)
        self.after = after

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache or not self.after:
            return False
        cache.store_channel(self.after, caching._CHANNEL_UPDATE)
        return True


@define(slots=True)
class ChannelDeleteEvent(BaseEvent):
    channel_id: str = field(repr=True, kw_only=True)

    channel: Channel | None = field(repr=True, kw_only=True)

    def before_process(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        self.channel = cache.get_channel(self.channel_id, caching._CHANNEL_DELETE)

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False

        cache.delete_channel(self.channel_id, caching._CHANNEL_DELETE)
        # TODO: Remove when backend will tell us to update all channels. (ServerUpdate event)
        if isinstance(self.channel, ServerChannel):
            server = cache.get_server(self.channel.server_id, caching._CHANNEL_DELETE)
            if server:
                try:
                    server.internal_channels[1].remove(self.channel.id)  # type: ignore # cached servers have only channel IDs internally
                except ValueError:
                    pass
                else:
                    cache.store_server(server, caching._CHANNEL_DELETE)
        elif isinstance(self.channel, DMChannel):
            cache.delete_private_channel_by_user(self.channel.recipient_id, caching._CHANNEL_DELETE)

        return True


@define(slots=True)
class GroupRecipientAddEvent(BaseEvent):
    channel_id: str = field(repr=True, kw_only=True)
    user_id: str = field(repr=True, kw_only=True)

    group: GroupChannel | None = field(repr=True, kw_only=True)

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        group = cache.get_channel(self.channel_id, caching._CHANNEL_GROUP_JOIN)
        if not isinstance(group, GroupChannel):
            return
        self.group = group

    def process(self) -> bool:
        if not self.group:
            return False
        self.group._join(self.user_id)
        return True


@define(slots=True)
class GroupRecipientRemoveEvent(BaseEvent):
    channel_id: str = field(repr=True, kw_only=True)
    user_id: str = field(repr=True, kw_only=True)

    group: GroupChannel | None = field(repr=True, kw_only=True)

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        group = cache.get_channel(self.channel_id, caching._CHANNEL_GROUP_LEAVE)
        if not isinstance(group, GroupChannel):
            return
        self.group = group

    def process(self) -> bool:
        if not self.group:
            return False
        self.group._leave(self.user_id)
        return True


@define(slots=True)
class ChannelStartTypingEvent(BaseEvent):
    channel_id: str = field(repr=True, kw_only=True)
    user_id: str = field(repr=True, kw_only=True)


@define(slots=True)
class ChannelStopTypingEvent(BaseEvent):
    channel_id: str = field(repr=True, kw_only=True)
    user_id: str = field(repr=True, kw_only=True)


@define(slots=True)
class MessageAckEvent(BaseEvent):
    channel_id: str = field(repr=True, kw_only=True)
    message_id: str = field(repr=True, kw_only=True)
    user_id: str = field(repr=True, kw_only=True)

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False

        read_state = cache.get_read_state(self.channel_id, caching._MESSAGE_ACK)
        if read_state:
            # TODO: What we should do in case of mentions? This solution sucks.
            if read_state.last_message_id and self.message_id >= read_state.last_message_id:
                try:
                    read_state.mentioned_in.remove(self.message_id)
                except ValueError:
                    pass

            read_state.last_message_id = self.message_id
            cache.store_read_state(read_state, caching._MESSAGE_ACK)

        return True


@define(slots=True)
class MessageCreateEvent(BaseEvent):
    message: Message = field(repr=True, kw_only=True)

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False

        author = self.message._author
        if isinstance(author, Member):
            if isinstance(author._user, User):
                cache.store_user(author._user, caching._MESSAGE_CREATE)
            cache.store_server_member(author, caching._MESSAGE_CREATE)
        elif isinstance(author, User):
            cache.store_user(author, caching._MESSAGE_CREATE)

        read_state = cache.get_read_state(self.message.channel_id, caching._MESSAGE_CREATE)
        if read_state:
            if read_state.user_id in self.message.mention_ids and self.message.id not in read_state.mentioned_in:
                read_state.mentioned_in.append(self.message.id)
                cache.store_read_state(read_state, caching._MESSAGE_CREATE)

        channel = cache.get_channel(self.message.channel_id, caching._MESSAGE_CREATE)
        if channel and isinstance(
            channel,
            (DMChannel, GroupChannel, ServerTextChannel),
        ):
            channel.last_message_id = self.message.id

        return True


@define(slots=True)
class MessageUpdateEvent(BaseEvent):
    message: PartialMessage = field(repr=True, kw_only=True)

    before: Message | None = field(repr=True, kw_only=True)
    after: Message | None = field(repr=True, kw_only=True)


@define(slots=True)
class MessageAppendEvent(BaseEvent):
    data: MessageAppendData = field(repr=True, kw_only=True)


@define(slots=True)
class MessageDeleteEvent(BaseEvent):
    channel_id: str = field(repr=True, kw_only=True)
    message_id: str = field(repr=True, kw_only=True)


@define(slots=True)
class MessageReactEvent(BaseEvent):
    channel_id: str = field(repr=True, kw_only=True)
    message_id: str = field(repr=True, kw_only=True)
    user_id: str = field(repr=True, kw_only=True)

    emoji: str = field(repr=True, kw_only=True)
    """May be either ULID or Unicode."""


@define(slots=True)
class MessageUnreactEvent(BaseEvent):
    channel_id: str = field(repr=True, kw_only=True)
    message_id: str = field(repr=True, kw_only=True)
    user_id: str = field(repr=True, kw_only=True)

    emoji: str = field(repr=True, kw_only=True)
    """May be either ULID or Unicode."""


@define(slots=True)
class MessageClearReactionEvent(BaseEvent):
    channel_id: str = field(repr=True, kw_only=True)
    message_id: str = field(repr=True, kw_only=True)

    emoji: str = field(repr=True, kw_only=True)
    """May be either ULID or Unicode."""


@define(slots=True)
class BulkMessageDeleteEvent(BaseEvent):
    channel_id: str = field(repr=True, kw_only=True)
    message_ids: list[str] = field(repr=True, kw_only=True)


@define(slots=True)
class ServerCreateEvent(BaseEvent):
    joined_at: datetime = field(repr=True, kw_only=True)
    server: Server = field(repr=True, kw_only=True)
    emojis: list[ServerEmoji] = field(repr=True, kw_only=True)

    def process(self) -> bool:
        state = self.shard.state

        cache = state.cache
        if not cache:
            return False

        for channel in self.server._prepare_cached():
            cache.store_channel(channel, caching._SERVER_CREATE)
        cache.store_server(self.server, caching._SERVER_CREATE)

        if state.me:
            cache.store_server_member(
                Member(
                    state=state,
                    server_id=self.server.id,
                    _user=state.me.id,
                    joined_at=self.joined_at,
                    nick=None,
                    internal_server_avatar=None,
                    roles=[],
                    timed_out_until=None,
                ),
                caching._SERVER_CREATE,
            )

        for emoji in self.emojis:
            cache.store_emoji(emoji, caching._SERVER_CREATE)
        return True


@define(slots=True)
class ServerEmojiCreateEvent(BaseEvent):
    emoji: ServerEmoji = field(repr=True, kw_only=True)

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False
        cache.store_emoji(self.emoji, caching._EMOJI_CREATE)
        return True


@define(slots=True)
class ServerEmojiDeleteEvent(BaseEvent):
    emoji: ServerEmoji | None = field(repr=True, kw_only=True)
    server_id: str | None = field(repr=True, kw_only=True)
    emoji_id: str = field(repr=True, kw_only=True)

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        emoji = cache.get_emoji(self.emoji_id, caching._EMOJI_DELETE)
        if not isinstance(emoji, DetachedEmoji):
            self.emoji = emoji

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False
        cache.delete_emoji(self.emoji_id, self.server_id, caching._EMOJI_DELETE)
        return True


@define(slots=True)
class ServerUpdateEvent(BaseEvent):
    server: PartialServer = field(repr=True, kw_only=True)

    before: Server | None = field(repr=True, kw_only=True)
    after: Server | None = field(repr=True, kw_only=True)

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        before = cache.get_server(self.server.id, caching._SERVER_UPDATE)
        self.before = before
        if not before:
            return

        after = copy(before)
        after._update(self.server)
        self.after = after

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache or not self.after:
            return False
        cache.store_server(self.after, caching._SERVER_UPDATE)
        return True


@define(slots=True)
class ServerDeleteEvent(BaseEvent):
    server_id: str = field(repr=True, kw_only=True)
    server: Server | None = field(repr=True, kw_only=True)

    def before_process(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        self.server = cache.get_server(self.server_id, caching._SERVER_DELETE)

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False
        cache.delete_server_emojis_of(self.server_id, caching._SERVER_DELETE)
        cache.delete_server_members_of(self.server_id, caching._SERVER_DELETE)
        cache.delete_server(self.server_id, caching._SERVER_DELETE)
        return True


@define(slots=True)
class ServerMemberJoinEvent(BaseEvent):
    member: Member = field(repr=True, kw_only=True)

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False
        cache.store_server_member(self.member, caching._SERVER_MEMBER_CREATE)
        return True


@define(slots=True)
class ServerMemberUpdateEvent(BaseEvent):
    member: PartialMember = field(repr=True, kw_only=True)

    before: Member | None = field(repr=True, kw_only=True)
    after: Member | None = field(repr=True, kw_only=True)

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        before = cache.get_server_member(self.member.server_id, self.member.id, caching._SERVER_MEMBER_UPDATE)
        self.before = before
        if not before:
            return

        after = copy(before)
        after._update(self.member)
        self.after = after

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache or not self.after:
            return False
        cache.store_server_member(self.after, caching._SERVER_MEMBER_UPDATE)
        return True


@define(slots=True)
class ServerMemberRemoveEvent(BaseEvent):
    server_id: str = field(repr=True, kw_only=True)
    user_id: str = field(repr=True, kw_only=True)

    member: Member | None = field(repr=True, kw_only=True)
    reason: MemberRemovalIntention = field(repr=True, kw_only=True)

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        self.member = cache.get_server_member(self.server_id, self.user_id, caching._SERVER_MEMBER_DELETE)

    def process(self) -> bool:
        state = self.shard.state
        cache = state.cache
        if not cache:
            return False

        me = state.me
        is_me = me.id == self.user_id if me else False

        cache.delete_server_member(self.server_id, self.user_id, caching._SERVER_MEMBER_DELETE)
        if is_me:
            cache.delete_server_emojis_of(self.server_id, caching._SERVER_MEMBER_DELETE)
            cache.delete_server_members_of(self.server_id, caching._SERVER_MEMBER_DELETE)
            cache.delete_server(self.server_id, caching._SERVER_MEMBER_DELETE)
        return True


@define(slots=True)
class RawServerRoleUpdateEvent(BaseEvent):
    role: PartialRole = field(repr=True, kw_only=True)

    old_role: Role | None = field(repr=True, kw_only=True)
    new_role: Role | None = field(repr=True, kw_only=True)

    server: Server | None = field(repr=True, kw_only=True)

    def before_process(self) -> None:
        self.new_role = self.role.into_full()

        cache = self.shard.state.cache
        if not cache:
            return
        self.server = cache.get_server(self.role.server_id, caching._SERVER_ROLE_UPDATE)
        if self.server:
            self.old_role = self.server.roles.get(self.role.id)

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache or not self.server:
            return False

        self.server._role_update_full(self.new_role or self.role)
        cache.store_server(self.server, caching._SERVER_ROLE_UPDATE)
        return True


@define(slots=True)
class ServerRoleDeleteEvent(BaseEvent):
    server_id: str = field(repr=True, kw_only=True)
    role_id: str = field(repr=True, kw_only=True)

    server: Server | None = field(repr=True, kw_only=True)
    role: Role | None = field(repr=True, kw_only=True)

    def before_process(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        self.server = cache.get_server(self.server_id, caching._SERVER_ROLE_DELETE)
        if self.server:
            self.role = self.server.roles.get(self.role_id)

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache or not self.server:
            return False

        self.server.roles.pop(self.role_id, None)

        cache.store_server(self.server, caching._SERVER_ROLE_DELETE)
        return True


@define(slots=True)
class UserUpdateEvent(BaseEvent):
    user: PartialUser = field(repr=True, kw_only=True)

    before: User | None = field(repr=True, kw_only=True)
    after: User | None = field(repr=True, kw_only=True)

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        before = cache.get_user(self.user.id, caching._USER_UPDATE)
        self.before = before
        if not before:
            return

        after = copy(before)
        after._update(self.user)
        self.after = after

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache or not self.after:
            return False
        cache.store_user(self.after, caching._USER_UPDATE)
        return True


@define(slots=True)
class UserRelationshipUpdateEvent(BaseEvent):
    current_user_id: str = field(repr=True, kw_only=True)
    """The current user ID."""

    old_user: User | None = field(repr=True, kw_only=True)
    new_user: User = field(repr=True, kw_only=True)

    before: RelationshipStatus | None = field(repr=True, kw_only=True)
    """Old relationship found in cache."""

    @property
    def after(self) -> RelationshipStatus:
        """New relationship with the user."""
        return self.new_user.relationship

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        self.old_user = cache.get_user(self.new_user.id, caching._USER_RELATIONSHIP_UPDATE)

        if self.old_user:
            self.before = self.old_user.relationship

    def process(self) -> bool:
        me = self.shard.state.me

        if me:
            if self.new_user.relationship is RelationshipStatus.none:
                me.relations.pop(self.new_user.id, None)
            else:
                relation = me.relations.get(self.new_user.id)

                if relation:
                    me.relations[self.new_user.id].status = self.new_user.relationship
                else:
                    me.relations[self.new_user.id] = Relationship(
                        id=self.new_user.id, status=self.new_user.relationship
                    )

        cache = self.shard.state.cache
        if not cache:
            return False
        cache.store_user(self.new_user, caching._USER_RELATIONSHIP_UPDATE)
        return True


@define(slots=True)
class UserSettingsUpdateEvent(BaseEvent):
    """User settings were updated remotely."""

    current_user_id: str = field(repr=True, kw_only=True)
    """The current user ID."""

    partial: UserSettings = field(repr=True, kw_only=True)

    before: UserSettings = field(repr=True, kw_only=True)
    after: UserSettings = field(repr=True, kw_only=True)

    def process(self) -> bool:
        settings = self.shard.state.settings
        if settings.mocked:
            return False
        settings._update(self.partial)
        return True


@define(slots=True)
class UserPlatformWipeEvent(BaseEvent):
    """
    User has been platform banned or deleted their account.

    Clients should remove the following associated data:
    - Messages
    - DM Channels
    - Relationships
    - Server Memberships

    User flags are specified to explain why a wipe is occurring though not all reasons will necessarily ever appear.
    """

    user_id: str = field(repr=True, kw_only=True)
    flags: UserFlags = field(repr=True, kw_only=True)


@define(slots=True)
class WebhookCreateEvent(BaseEvent):
    webhook: Webhook = field(repr=True, kw_only=True)


@define(slots=True)
class WebhookUpdateEvent(BaseEvent):
    new_webhook: PartialWebhook = field(repr=True, kw_only=True)


@define(slots=True)
class WebhookDeleteEvent(BaseEvent):
    webhook: Webhook | None = field(repr=True, kw_only=True)
    webhook_id: str = field(repr=True, kw_only=True)


@define(slots=True)
class AuthifierEvent(BaseEvent):
    pass


@define(slots=True)
class SessionCreateEvent(AuthifierEvent):
    session: Session = field(repr=True, kw_only=True)


@define(slots=True)
class SessionDeleteEvent(AuthifierEvent):
    user_id: str = field(repr=True, kw_only=True)
    session_id: str = field(repr=True, kw_only=True)


@define(slots=True)
class SessionDeleteAllEvent(AuthifierEvent):
    user_id: str = field(repr=True, kw_only=True)
    exclude_session_id: str | None = field(repr=True, kw_only=True)


@define(slots=True)
class LogoutEvent(BaseEvent):
    pass


@define(slots=True)
class AuthenticatedEvent(BaseEvent):
    pass


__all__ = (
    'BaseEvent',
    'ReadyEvent',
    'BaseChannelCreateEvent',
    'PrivateChannelCreateEvent',
    'ServerChannelCreateEvent',
    'ChannelCreateEvent',
    'ChannelUpdateEvent',
    'ChannelDeleteEvent',
    'GroupRecipientAddEvent',
    'GroupRecipientRemoveEvent',
    'ChannelStartTypingEvent',
    'ChannelStopTypingEvent',
    'MessageAckEvent',
    'MessageCreateEvent',
    'MessageUpdateEvent',
    'MessageAppendEvent',
    'MessageDeleteEvent',
    'MessageReactEvent',
    'MessageUnreactEvent',
    'MessageClearReactionEvent',
    'BulkMessageDeleteEvent',
    'ServerCreateEvent',
    'ServerEmojiCreateEvent',
    'ServerEmojiDeleteEvent',
    'ServerUpdateEvent',
    'ServerDeleteEvent',
    'ServerMemberJoinEvent',
    'ServerMemberUpdateEvent',
    'ServerMemberRemoveEvent',
    'RawServerRoleUpdateEvent',
    'ServerRoleDeleteEvent',
    'UserUpdateEvent',
    'UserRelationshipUpdateEvent',
    'UserSettingsUpdateEvent',
    'UserPlatformWipeEvent',
    'WebhookCreateEvent',
    'WebhookUpdateEvent',
    'WebhookDeleteEvent',
    'AuthifierEvent',
    'SessionCreateEvent',
    'SessionDeleteEvent',
    'SessionDeleteAllEvent',
    'LogoutEvent',
    'AuthenticatedEvent',
)
