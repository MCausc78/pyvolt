from __future__ import annotations

from attrs import define, field
from copy import copy
import typing as t

from . import (
    auth,
    cache as caching,
    channel as channels,
    core,
    emoji as emojis,
    message as messages,
    server as servers,
    shard as sharding,
    user_settings,
    user as users,
    webhook as webhooks,
)


@define(slots=True)
class BaseEvent:
    shard: sharding.Shard = field(repr=True, hash=True, kw_only=True, eq=True)
    is_cancelled: bool = field(
        default=False, repr=True, hash=True, kw_only=True, eq=True
    )

    def set_cancel(self, value: bool, /) -> bool:
        """Whether to cancel event processing (updating cache) or not."""
        if self.is_cancelled is value:
            return False
        self.is_cancelled = value
        return True

    async def abefore_dispatch(self) -> None:
        pass

    def before_dispatch(self) -> None:
        pass

    async def aprocess(self) -> t.Any:
        pass

    def process(self) -> t.Any:
        pass


@define(slots=True)
class ReadyEvent(BaseEvent):
    users: list[users.User] = field(repr=True, hash=True, kw_only=True, eq=True)
    servers: list[servers.Server] = field(repr=True, hash=True, kw_only=True, eq=True)
    channels: list[channels.Channel] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    members: list[servers.Member] = field(repr=True, hash=True, kw_only=True, eq=True)
    emojis: list[emojis.ServerEmoji] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )

    old_me: users.SelfUser | None = field(repr=True, hash=True, kw_only=True, eq=True)
    new_me: users.SelfUser | None = field(repr=True, hash=True, kw_only=True, eq=True)

    def process(self) -> bool:
        state = self.shard.state
        state._me = self.new_me

        cache = state.cache

        if not cache:
            return False

        for u in self.users:
            cache.store_user(u, caching._READY)

        for s in self.servers:
            cache.store_server(s, caching._READY)

        for c in self.channels:
            cache.store_channel(c, caching._READY)

        for m in self.members:
            cache.store_server_member(m, caching._READY)

        for e in self.emojis:
            cache.store_emoji(e, caching._READY)

        return True


@define(slots=True)
class BaseChannelCreateEvent(BaseEvent):
    def _process(self, channel: channels.Channel) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False
        cache.store_channel(channel, caching._CHANNEL_CREATE)
        return True


@define(slots=True)
class PrivateChannelCreateEvent(BaseChannelCreateEvent):
    channel: channels.PrivateChannel = field(
        repr=True, hash=True, kw_only=True, eq=True
    )

    def process(self) -> bool:
        return self._process(self.channel)


@define(slots=True)
class ServerChannelCreateEvent(BaseChannelCreateEvent):
    channel: channels.ServerChannel = field(repr=True, hash=True, kw_only=True, eq=True)

    def process(self) -> bool:
        return self._process(self.channel)


ChannelCreateEvent = PrivateChannelCreateEvent | ServerChannelCreateEvent


@define(slots=True)
class ChannelUpdateEvent(BaseEvent):
    channel: channels.PartialChannel = field(
        repr=True, hash=True, kw_only=True, eq=True
    )

    before: channels.Channel | None = field(repr=True, hash=True, kw_only=True, eq=True)
    after: channels.Channel | None = field(repr=True, hash=True, kw_only=True, eq=True)

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
    channel_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)

    channel: channels.Channel | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )

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
        return True


@define(slots=True)
class GroupRecipientAddEvent(BaseEvent):
    channel_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    user_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)

    group: channels.GroupChannel | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        group = cache.get_channel(self.channel_id, caching._CHANNEL_GROUP_JOIN)
        if not isinstance(group, channels.GroupChannel):
            return
        self.group = group

    def process(self) -> bool:
        if not self.group:
            return False
        self.group._join(self.user_id)
        return True


@define(slots=True)
class GroupRecipientRemoveEvent(BaseEvent):
    channel_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    user_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)

    group: channels.GroupChannel | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        group = cache.get_channel(self.channel_id, caching._CHANNEL_GROUP_LEAVE)
        if not isinstance(group, channels.GroupChannel):
            return
        self.group = group

    def process(self) -> bool:
        if not self.group:
            return False
        self.group._leave(self.user_id)
        return True


@define(slots=True)
class ChannelStartTypingEvent(BaseEvent):
    channel_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    user_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)


@define(slots=True)
class ChannelStopTypingEvent(BaseEvent):
    channel_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    user_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)


@define(slots=True)
class MessageAckEvent(BaseEvent):
    channel_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    message_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    user_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False

        read_state = cache.get_read_state(self.channel_id, caching._MESSAGE_ACK)
        if read_state:
            # TODO: Still think what we should do in case of mentions.
            if (
                read_state.last_message_id
                and self.message_id >= read_state.last_message_id
            ):
                try:
                    read_state.mentioned_in.remove(self.message_id)
                except ValueError:
                    pass

            read_state.last_message_id = self.message_id
            cache.store_read_state(read_state, caching._MESSAGE_ACK)

        return True


@define(slots=True)
class MessageCreateEvent(BaseEvent):
    message: messages.Message = field(repr=True, hash=True, kw_only=True, eq=True)

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False

        author = self.message._author
        if isinstance(author, servers.Member):
            if isinstance(author._user, users.User):
                cache.store_user(author._user, caching._MESSAGE_CREATE)
        elif isinstance(author, users.User):
            cache.store_user(author, caching._MESSAGE_CREATE)
        else:
            pass

        read_state = cache.get_read_state(
            self.message.channel_id, caching._MESSAGE_CREATE
        )
        if read_state:
            if (
                read_state.user_id in self.message.mention_ids
                and self.message.id not in read_state.mentioned_in
            ):
                read_state.mentioned_in.append(self.message.id)
                cache.store_read_state(read_state, caching._MESSAGE_CREATE)

        channel = cache.get_channel(self.message.channel_id, caching._MESSAGE_CREATE)
        if channel and isinstance(
            channel,
            (channels.DMChannel, channels.GroupChannel, channels.ServerTextChannel),
        ):
            channel.last_message_id = self.message.id

        return True


@define(slots=True)
class MessageUpdateEvent(BaseEvent):
    message: messages.PartialMessage = field(
        repr=True, hash=True, kw_only=True, eq=True
    )

    before: messages.Message | None = field(repr=True, hash=True, kw_only=True, eq=True)
    after: messages.Message | None = field(repr=True, hash=True, kw_only=True, eq=True)


@define(slots=True)
class MessageAppendEvent(BaseEvent):
    data: messages.MessageAppendData = field(
        repr=True, hash=True, kw_only=True, eq=True
    )


@define(slots=True)
class MessageDeleteEvent(BaseEvent):
    channel_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    message_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)


@define(slots=True)
class MessageReactEvent(BaseEvent):
    channel_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    message_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    user_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)

    emoji: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """May be either ULID or Unicode."""


@define(slots=True)
class MessageUnreactEvent(BaseEvent):
    channel_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    message_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    user_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)

    emoji: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """May be either ULID or Unicode."""


@define(slots=True)
class MessageClearReactionEvent(BaseEvent):
    channel_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    message_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)

    emoji: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """May be either ULID or Unicode."""


@define(slots=True)
class BulkMessageDeleteEvent(BaseEvent):
    channel_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    message_ids: list[core.ULID] = field(repr=True, hash=True, kw_only=True, eq=True)


@define(slots=True)
class ServerCreateEvent(BaseEvent):
    server: servers.Server = field(repr=True, hash=True, kw_only=True, eq=True)
    emojis: list[emojis.ServerEmoji] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False
        cache.store_server(self.server, caching._SERVER_CREATE)
        for emoji in self.emojis:
            cache.store_emoji(emoji, caching._SERVER_CREATE)
        return True


@define(slots=True)
class ServerEmojiCreateEvent(BaseEvent):
    emoji: emojis.ServerEmoji = field(repr=True, hash=True, kw_only=True, eq=True)

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False
        cache.store_emoji(self.emoji, caching._EMOJI_CREATE)
        return True


@define(slots=True)
class ServerEmojiDeleteEvent(BaseEvent):
    emoji: emojis.ServerEmoji | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    server_id: core.ULID | None = field(repr=True, hash=True, kw_only=True, eq=True)
    emoji_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        emoji = cache.get_emoji(self.emoji_id, caching._EMOJI_DELETE)
        if not isinstance(emoji, emojis.DetachedEmoji):
            self.emoji = emoji

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False
        cache.delete_emoji(self.emoji_id, self.server_id, caching._EMOJI_DELETE)
        return True


@define(slots=True)
class ServerUpdateEvent(BaseEvent):
    server: servers.PartialServer = field(repr=True, hash=True, kw_only=True, eq=True)

    before: servers.Server | None = field(repr=True, hash=True, kw_only=True, eq=True)
    after: servers.Server | None = field(repr=True, hash=True, kw_only=True, eq=True)

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
    server_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    server: servers.Server | None = field(repr=True, hash=True, kw_only=True, eq=True)

    def before_process(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        self.server = cache.get_server(self.server_id, caching._SERVER_DELETE)

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False
        cache.delete_server(self.server_id, caching._SERVER_DELETE)
        return True


@define(slots=True)
class ServerMemberUpdateEvent(BaseEvent):
    member: servers.PartialMember = field(repr=True, hash=True, kw_only=True, eq=True)

    before: servers.Member | None = field(repr=True, hash=True, kw_only=True, eq=True)
    after: servers.Member | None = field(repr=True, hash=True, kw_only=True, eq=True)

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        before = cache.get_server_member(
            self.member.server_id, self.member.id, caching._SERVER_MEMBER_UPDATE
        )
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
class ServerMemberJoinEvent(BaseEvent):
    member: servers.Member = field(repr=True, hash=True, kw_only=True, eq=True)

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False
        cache.store_server_member(self.member, caching._SERVER_MEMBER_CREATE)
        return True


@define(slots=True)
class ServerMemberLeaveEvent(BaseEvent):
    server_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    user_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)

    member: servers.Member | None = field(repr=True, hash=True, kw_only=True, eq=True)

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        self.member = cache.get_server_member(
            self.server_id, self.user_id, caching._SERVER_MEMBER_DELETE
        )

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False
        cache.delete_server_member(
            self.server_id, self.user_id, caching._SERVER_MEMBER_DELETE
        )
        return True


@define(slots=True)
class RawServerRoleUpdateEvent(BaseEvent):
    role: servers.PartialRole = field(repr=True, hash=True, kw_only=True, eq=True)

    old_role: servers.Role | None = field(repr=True, hash=True, kw_only=True, eq=True)
    new_role: servers.Role | None = field(repr=True, hash=True, kw_only=True, eq=True)

    server: servers.Server | None = field(repr=True, hash=True, kw_only=True, eq=True)

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
    server_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    role_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)

    server: servers.Server | None = field(repr=True, hash=True, kw_only=True, eq=True)
    role: servers.Role | None = field(repr=True, hash=True, kw_only=True, eq=True)

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

        try:
            del self.server.roles[self.role_id]
        except KeyError:
            pass

        cache.store_server(self.server, caching._SERVER_ROLE_DELETE)
        return True


@define(slots=True)
class UserUpdateEvent(BaseEvent):
    user: users.PartialUser = field(repr=True, hash=True, kw_only=True, eq=True)

    before: users.User | None = field(repr=True, hash=True, kw_only=True, eq=True)
    after: users.User | None = field(repr=True, hash=True, kw_only=True, eq=True)

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
    current_user_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    """The current user ID."""

    old_user: users.User | None = field(repr=True, hash=True, kw_only=True, eq=True)
    new_user: users.User = field(repr=True, hash=True, kw_only=True, eq=True)

    before: users.RelationshipStatus | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """Old relationship found in cache."""

    @property
    def after(self) -> users.RelationshipStatus:
        """New relationship with the user."""
        return self.new_user.relationship

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        self.old_user = cache.get_user(
            self.new_user.id, caching._USER_RELATIONSHIP_UPDATE
        )

        if self.old_user:
            self.before = self.old_user.relationship

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False
        cache.store_user(self.new_user, caching._USER_RELATIONSHIP_UPDATE)
        return True


@define(slots=True)
class UserSettingsUpdateEvent(BaseEvent):
    """User settings were updated remotely."""

    current_user_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    """The current user ID."""

    before: user_settings.UserSettings | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    after: user_settings.UserSettings = field(
        repr=True, hash=True, kw_only=True, eq=True
    )


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

    user_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    flags: users.UserFlags = field(repr=True, hash=True, kw_only=True, eq=True)


@define(slots=True)
class WebhookCreateEvent(BaseEvent):
    webhook: webhooks.Webhook = field(repr=True, hash=True, kw_only=True, eq=True)


@define(slots=True)
class WebhookUpdateEvent(BaseEvent):
    webhook: webhooks.PartialWebhook = field(
        repr=True, hash=True, kw_only=True, eq=True
    )


@define(slots=True)
class WebhookDeleteEvent(BaseEvent):
    webhook: webhooks.Webhook | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    webhook_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)


@define(slots=True)
class AuthifierEvent(BaseEvent):
    pass


@define(slots=True)
class SessionCreateEvent(AuthifierEvent):
    session: auth.Session = field(repr=True, hash=True, kw_only=True, eq=True)


@define(slots=True)
class SessionDeleteEvent(AuthifierEvent):
    user_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    session_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)


@define(slots=True)
class SessionDeleteAllEvent(AuthifierEvent):
    user_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    exclude_session_id: core.ULID | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )


@define(slots=True)
class LogoutEvent(BaseEvent):
    pass
