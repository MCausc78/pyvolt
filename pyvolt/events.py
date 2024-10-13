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

from . import cache as caching, utils
from .channel import (
    PartialChannel,
    SavedMessagesChannel,
    DMChannel,
    GroupChannel,
    PrivateChannel,
    ServerTextChannel,
    ServerChannel,
    Channel,
)
from .emoji import ServerEmoji, DetachedEmoji
from .enums import MemberRemovalIntention, RelationshipStatus
from .read_state import ReadState
from .server import (
    PartialRole,
    Role,
    PartialServer,
    Server,
    PartialMember,
    Member,
)
from .user import (
    Relationship,
    PartialUser,
    User,
    OwnUser,
)

if typing.TYPE_CHECKING:
    import aiohttp

    from .authentication import Session
    from .channel import ChannelVoiceStateContainer
    from .client import Client
    from .flags import UserFlags
    from .message import PartialMessage, MessageAppendData, Message
    from .webhook import Webhook, PartialWebhook
    from .shard import Shard
    from .user_settings import UserSettings
    from .user import UserVoiceState, PartialUserVoiceState


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
    """Dispatched when initial state is available.

    .. warning::
        This event may be dispatched multiple times due to periodic reconnects.
    """

    event_name: typing.ClassVar[typing.Literal['ready']] = 'ready'

    users: list[User] = field(repr=True, kw_only=True)
    """The users that the client can see (from DMs, groups, and relationships).
    
    This attribute contains connected user, usually at end of list, but sometimes not at end.
    """

    servers: list[Server] = field(repr=True, kw_only=True)
    """The servers the connected user is in."""

    channels: list[Channel] = field(repr=True, kw_only=True)
    """The DM channels, server channels and groups the connected user participates in."""

    members: list[Member] = field(repr=True, kw_only=True)
    """The own members for servers."""

    emojis: list[ServerEmoji] = field(repr=True, kw_only=True)
    """The emojis from servers the user participating in."""

    me: OwnUser = field(repr=True, kw_only=True)
    """The connected user."""

    user_settings: UserSettings = field(repr=True, kw_only=True)
    """The settings for connected user.
    
    .. note::
        This attribute is unavailable on bot accounts.
    """

    read_states: list[ReadState] = field(repr=True, kw_only=True)
    """The read states for channels ever seen by user. This is not always populated, and unavailable for bots.

    .. note::
        This attribute is unavailable on bot accounts.
    """

    voice_states: list[ChannelVoiceStateContainer] = field(repr=True, kw_only=True)
    """The voice states of the text/voice channels."""

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
            elif channel.__class__ is SavedMessagesChannel or isinstance(channel, SavedMessagesChannel):
                state._saved_notes = channel  # type: ignore

        for m in self.members:
            cache.store_server_member(m, caching._READY)

        for e in self.emojis:
            cache.store_emoji(e, caching._READY)

        for rs in self.read_states:
            cache.store_read_state(rs, caching._READY)

        cache.bulk_store_channel_voice_states({vs.channel_id: vs for vs in self.voice_states}, caching._READY)

        return True


@define(slots=True)
class BaseChannelCreateEvent(BaseEvent):
    event_name: typing.ClassVar[str] = 'channel_create'


@define(slots=True)
class PrivateChannelCreateEvent(BaseChannelCreateEvent):
    """Dispatched when the user created a DM, or started participating in group."""

    event_name: typing.ClassVar[str] = 'private_channel_create'

    channel: PrivateChannel = field(repr=True, kw_only=True)
    """The joined DM or group channel."""

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
    """Dispatched when the channel is created in server or became open to the connected user."""

    event_name: typing.ClassVar[str] = 'server_channel_create'

    channel: ServerChannel = field(repr=True, kw_only=True)
    """The created server channel."""

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False

        cache.store_channel(self.channel, caching._CHANNEL_CREATE)
        return True


ChannelCreateEvent = PrivateChannelCreateEvent | ServerChannelCreateEvent


@define(slots=True)
class ChannelUpdateEvent(BaseEvent):
    """Dispatched when the channel is updated."""

    event_name: typing.ClassVar[typing.Literal['channel_update']] = 'channel_update'

    channel: PartialChannel = field(repr=True, kw_only=True)
    """The fields that were updated."""

    before: Channel | None = field(repr=True, kw_only=True)
    """The channel as it was before being updated, if available."""

    after: Channel | None = field(repr=True, kw_only=True)
    """The channel as it was updated, if available."""

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
    """Dispatched when the server channel or group is deleted or became hidden for the connected user."""

    event_name: typing.ClassVar[typing.Literal['channel_delete']] = 'channel_delete'

    channel_id: str = field(repr=True, kw_only=True)
    """The channel's ID that got deleted or hidden."""

    channel: Channel | None = field(repr=True, kw_only=True)
    """The deleted channel object, if available."""

    def before_dispatch(self) -> None:
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
        cache.delete_messages_of(self.channel_id, caching._CHANNEL_DELETE)
        return True


@define(slots=True)
class GroupRecipientAddEvent(BaseEvent):
    """Dispatched when recipient is added to the group."""

    event_name: typing.ClassVar[typing.Literal['recipient_add']] = 'recipient_add'

    channel_id: str = field(repr=True, kw_only=True)
    """The affected group's ID."""

    user_id: str = field(repr=True, kw_only=True)
    """The user's ID who was added to the group."""

    group: GroupChannel | None = field(repr=True, kw_only=True)
    """The group in cache (in previous state as it had no recipient), if available."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        group = cache.get_channel(self.channel_id, caching._CHANNEL_GROUP_JOIN)
        if not isinstance(group, GroupChannel):
            return
        self.group = group

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False

        if not self.group:
            return False

        self.group._join(self.user_id)
        cache.store_channel(self.group, caching._CHANNEL_GROUP_JOIN)

        return True


@define(slots=True)
class GroupRecipientRemoveEvent(BaseEvent):
    """Dispatched when recipient is removed from the group."""

    event_name: typing.ClassVar[typing.Literal['recipient_remove']] = 'recipient_remove'

    channel_id: str = field(repr=True, kw_only=True)
    """The affected group's ID."""

    user_id: str = field(repr=True, kw_only=True)
    """The user's ID who was removed from the group."""

    group: GroupChannel | None = field(repr=True, kw_only=True)
    """The group in cache (in previous state as it had recipient), if available."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        group = cache.get_channel(self.channel_id, caching._CHANNEL_GROUP_LEAVE)
        if not isinstance(group, GroupChannel):
            return
        self.group = group

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False

        if not self.group:
            return False

        self.group._leave(self.user_id)
        cache.store_channel(self.group, caching._CHANNEL_GROUP_LEAVE)

        return True


@define(slots=True)
class ChannelStartTypingEvent(BaseEvent):
    """Dispatched when someone starts typing in a channel."""

    event_name: typing.ClassVar[typing.Literal['channel_start_typing']] = 'channel_start_typing'

    channel_id: str = field(repr=True, kw_only=True)
    """The channel's ID where user started typing in."""

    user_id: str = field(repr=True, kw_only=True)
    """The user's ID who started typing."""


@define(slots=True)
class ChannelStopTypingEvent(BaseEvent):
    """Dispatched when someone stopped typing in a channel."""

    event_name: typing.ClassVar[typing.Literal['channel_stop_typing']] = 'channel_stop_typing'

    channel_id: str = field(repr=True, kw_only=True)
    """The channel's ID where user stopped typing in."""

    user_id: str = field(repr=True, kw_only=True)
    """The user's ID who stopped typing."""


@define(slots=True)
class MessageAckEvent(BaseEvent):
    """Dispatched when the connected user acknowledges the message in a channel (probably from remote device)."""

    event_name: typing.ClassVar[typing.Literal['message_ack']] = 'message_ack'

    channel_id: str = field(repr=True, kw_only=True)
    message_id: str = field(repr=True, kw_only=True)
    user_id: str = field(repr=True, kw_only=True)

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False

        read_state = cache.get_read_state(self.channel_id, caching._MESSAGE_ACK)
        if read_state:
            # opposite effect cannot be done
            if read_state.last_message_id and self.message_id >= read_state.last_message_id:
                acked_message_id = read_state.last_message_id

                read_state.mentioned_in = [m for m in read_state.mentioned_in if m >= acked_message_id]

            read_state.last_message_id = self.message_id
            cache.store_read_state(read_state, caching._MESSAGE_ACK)

        return True


@define(slots=True)
class MessageCreateEvent(BaseEvent):
    """Dispatched when someone sends message in a channel."""

    event_name: typing.ClassVar[typing.Literal['message_create']] = 'message_create'

    message: Message = field(repr=True, kw_only=True)
    """The message sent."""

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

        cache.store_message(self.message, caching._MESSAGE_CREATE)

        return True

    def call_object_handlers_hook(self, client: Client) -> utils.MaybeAwaitable[None]:
        if hasattr(client, 'on_message'):
            return client.on_message(self.message)


@define(slots=True)
class MessageUpdateEvent(BaseEvent):
    """Dispatched when the message is updated."""

    event_name: typing.ClassVar[typing.Literal['message_update']] = 'message_update'

    message: PartialMessage = field(repr=True, kw_only=True)
    """The fields that were updated."""

    before: Message | None = field(repr=True, kw_only=True)
    """The message as it was before being updated, if available."""

    after: Message | None = field(repr=True, kw_only=True)
    """The message as it was updated, if available."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache

        if not cache:
            return
        before = cache.get_message(self.message.channel_id, self.message.id, caching._MESSAGE_UPDATE)
        if not before:
            return
        self.before = before
        after = copy(before)
        after._update(self.message)
        self.after = after

    def process(self) -> bool:
        cache = self.shard.state.cache

        if not cache or not self.after:
            return False
        cache.store_message(self.after, caching._MESSAGE_UPDATE)
        return True


@define(slots=True)
class MessageAppendEvent(BaseEvent):
    """Dispatched when embeds are appended to the message."""

    event_name: typing.ClassVar[typing.Literal['message_append']] = 'message_append'

    data: MessageAppendData = field(repr=True, kw_only=True)
    """The data that got appended to message."""

    message: Message | None = field(repr=True, kw_only=True)
    """The message as it was before being updated, if available."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache

        if not cache:
            return
        self.message = cache.get_message(self.data.channel_id, self.data.id, caching._MESSAGE_APPEND)

    def process(self) -> bool:
        cache = self.shard.state.cache

        if not cache or not self.message:
            return False

        self.message._append(self.data)
        cache.store_message(self.message, caching._MESSAGE_APPEND)
        return True


@define(slots=True)
class MessageDeleteEvent(BaseEvent):
    """Dispatched when the message is deleted in channel."""

    event_name: typing.ClassVar[typing.Literal['message_delete']] = 'message_delete'

    channel_id: str = field(repr=True, kw_only=True)
    """The channel's ID the message was in."""

    message_id: str = field(repr=True, kw_only=True)
    """The deleted message's ID."""

    message: Message | None = field(repr=True, kw_only=True)
    """The deleted message object, if available."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache

        if not cache:
            return
        self.message = cache.get_message(self.channel_id, self.message_id, caching._MESSAGE_DELETE)

    def process(self) -> bool:
        cache = self.shard.state.cache

        if not cache:
            return False
        cache.delete_message(self.channel_id, self.message_id, caching._MESSAGE_DELETE)
        return True


@define(slots=True)
class MessageReactEvent(BaseEvent):
    """Dispatched when someone reacts to message."""

    event_name: typing.ClassVar[typing.Literal['message_react']] = 'message_react'

    channel_id: str = field(repr=True, kw_only=True)
    """The channel's ID the message is in."""

    message_id: str = field(repr=True, kw_only=True)
    """The message's ID that got a reaction."""

    user_id: str = field(repr=True, kw_only=True)
    """The user's ID that added a reaction to the message."""

    emoji: str = field(repr=True, kw_only=True)
    """The emoji that was reacted with. May be either ULID or Unicode emoji."""

    message: Message | None = field(repr=True, kw_only=True)
    """The message as it was before being updated, if available."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache

        if not cache:
            return
        self.message = cache.get_message(self.channel_id, self.message_id, caching._MESSAGE_REACT)

    def process(self) -> bool:
        cache = self.shard.state.cache

        if not cache or not self.message:
            return False
        self.message._react(self.user_id, self.emoji)
        cache.store_message(self.message, caching._MESSAGE_REACT)
        return True


@define(slots=True)
class MessageUnreactEvent(BaseEvent):
    """Dispatched when someone removes their reaction from message."""

    event_name: typing.ClassVar[typing.Literal['message_unreact']] = 'message_unreact'

    channel_id: str = field(repr=True, kw_only=True)
    """The channel's ID the message is in."""

    message_id: str = field(repr=True, kw_only=True)
    """The message's ID that lost a reaction."""

    user_id: str = field(repr=True, kw_only=True)
    """The user's ID that removed reaction from the message."""

    emoji: str = field(repr=True, kw_only=True)
    """The emoji that was reacted with before. May be either ULID or Unicode emoji."""

    message: Message | None = field(repr=True, kw_only=True)
    """The message as it was before being updated, if available."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache

        if not cache:
            return
        self.message = cache.get_message(self.channel_id, self.message_id, caching._MESSAGE_UNREACT)

    def process(self) -> bool:
        cache = self.shard.state.cache

        if not cache or not self.message:
            return False
        self.message._unreact(self.user_id, self.emoji)
        cache.store_message(self.message, caching._MESSAGE_UNREACT)
        return True


@define(slots=True)
class MessageClearReactionEvent(BaseEvent):
    """Dispatched when reactions for specific emoji are removed from message."""

    event_name: typing.ClassVar[typing.Literal['message_clear_reaction']] = 'message_clear_reaction'

    channel_id: str = field(repr=True, kw_only=True)
    """The channel's ID the message is in."""

    message_id: str = field(repr=True, kw_only=True)
    """The message's ID that lost reactions."""

    emoji: str = field(repr=True, kw_only=True)
    """The emoji whose reactions were removed. May be either ULID or Unicode emoji."""

    message: Message | None = field(repr=True, kw_only=True)
    """The message as it was before being updated, if available."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache

        if not cache:
            return
        self.message = cache.get_message(self.channel_id, self.message_id, caching._MESSAGE_REACT)

    def process(self) -> bool:
        cache = self.shard.state.cache

        if not cache or not self.message:
            return False
        self.message._clear(self.emoji)
        cache.store_message(self.message, caching._MESSAGE_REACT)
        return True


@define(slots=True)
class BulkMessageDeleteEvent(BaseEvent):
    """Dispatched when multiple messages are deleted from channel."""

    event_name: typing.ClassVar[typing.Literal['bulk_message_delete']] = 'bulk_message_delete'

    channel_id: str = field(repr=True, kw_only=True)
    """The channel's ID where messages got deleted from."""

    message_ids: list[str] = field(repr=True, kw_only=True)
    """The list of message's IDs that got deleted."""

    messages: list[Message] = field(repr=True, kw_only=True)
    """The list of messages, potentially retrieved from cache. Unlike :attr:`.message_ids`, some messages are
    not guaranteed to be here."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache

        if not cache:
            return

        for message_id in self.message_ids:
            message = cache.get_message(self.channel_id, message_id, caching._MESSAGE_BULK_DELETE)
            if message:
                self.messages.append(message)

    def process(self) -> bool:
        cache = self.shard.state.cache

        if not cache:
            return False

        for message_id in self.message_ids:
            cache.delete_message(self.channel_id, message_id, caching._MESSAGE_BULK_DELETE)

        return True


@define(slots=True)
class ServerCreateEvent(BaseEvent):
    """Dispatched when the server is created, or client joined server."""

    event_name: typing.ClassVar[typing.Literal['server_create']] = 'server_create'

    joined_at: datetime = field(repr=True, kw_only=True)
    """When the client got added to server, generated locally, and used internally."""

    server: Server = field(repr=True, kw_only=True)
    """The server that client was added to."""

    emojis: list[ServerEmoji] = field(repr=True, kw_only=True)
    """The server emojis."""

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
                    can_publish=True,
                    can_receive=True,
                ),
                caching._SERVER_CREATE,
            )

        for emoji in self.emojis:
            cache.store_emoji(emoji, caching._SERVER_CREATE)
        return True


@define(slots=True)
class ServerEmojiCreateEvent(BaseEvent):
    """Dispatched when emoji is created in server."""

    event_name: typing.ClassVar[typing.Literal['server_emoji_create']] = 'server_emoji_create'

    emoji: ServerEmoji = field(repr=True, kw_only=True)
    """The created emoji."""

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False
        cache.store_emoji(self.emoji, caching._EMOJI_CREATE)
        return True


@define(slots=True)
class ServerEmojiDeleteEvent(BaseEvent):
    """Dispatched when emoji is deleted from the server."""

    event_name: typing.ClassVar[typing.Literal['server_emoji_delete']] = 'server_emoji_delete'

    server_id: str | None = field(repr=True, kw_only=True)
    """The server's ID where emoji got deleted from."""

    emoji_id: str = field(repr=True, kw_only=True)
    """The deleted emoji's ID."""

    emoji: ServerEmoji | None = field(repr=True, kw_only=True)
    """The deleted emoji object, if available."""

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
    """Dispatched when the server details are updated."""

    event_name: typing.ClassVar[typing.Literal['server_update']] = 'server_update'

    server: PartialServer = field(repr=True, kw_only=True)
    """The fields that were updated."""

    before: Server | None = field(repr=True, kw_only=True)
    """The server as it was before being updated, if available."""

    after: Server | None = field(repr=True, kw_only=True)
    """The server as it was updated, if available."""

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
    """Dispatched when the server is deleted."""

    event_name: typing.ClassVar[typing.Literal['server_delete']] = 'server_delete'

    server_id: str = field(repr=True, kw_only=True)
    """The deleted server's ID."""

    server: Server | None = field(repr=True, kw_only=True)
    """The deleted server object, if available."""

    def before_dispatch(self) -> None:
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
    """Dispatched when the user got added to the server."""

    event_name: typing.ClassVar[typing.Literal['server_member_join']] = 'server_member_join'

    member: Member = field(repr=True, kw_only=True)
    """The joined member."""

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False
        cache.store_server_member(self.member, caching._SERVER_MEMBER_CREATE)
        return True


@define(slots=True)
class ServerMemberUpdateEvent(BaseEvent):
    """Dispatched when the member details are updated."""

    event_name: typing.ClassVar[typing.Literal['server_member_update']] = 'server_member_update'

    member: PartialMember = field(repr=True, kw_only=True)
    """The fields that were updated."""

    before: Member | None = field(repr=True, kw_only=True)
    """The member as it was before being updated, if available."""

    after: Member | None = field(repr=True, kw_only=True)
    """The member as it was updated, if available."""

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
    """Dispatched when the member (or client user) got removed from server."""

    event_name: typing.ClassVar[typing.Literal['server_member_remove']] = 'server_member_remove'

    server_id: str = field(repr=True, kw_only=True)
    """The server's ID from which the user was removed from."""

    user_id: str = field(repr=True, kw_only=True)
    """The removed user's ID."""

    member: Member | None = field(repr=True, kw_only=True)
    """The removed member object, if available."""

    reason: MemberRemovalIntention = field(repr=True, kw_only=True)
    """The reason why member was removed."""

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
    """Dispatched when the role got created or updated in server."""

    event_name: typing.ClassVar[typing.Literal['raw_server_role_update']] = 'raw_server_role_update'

    role: PartialRole = field(repr=True, kw_only=True)
    """The fields that got updated."""

    old_role: Role | None = field(repr=True, kw_only=True)
    """The role as it was before being updated, if available."""

    new_role: Role | None = field(repr=True, kw_only=True)
    """The role as it was created or updated, if available."""

    server: Server | None = field(repr=True, kw_only=True)
    """The server the role got created or updated in."""

    def before_dispatch(self) -> None:
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
    """Dispatched when the role got deleted from server."""

    event_name: typing.ClassVar[typing.Literal['server_role_delete']] = 'server_role_delete'

    server_id: str = field(repr=True, kw_only=True)
    """The server's ID the role was in."""

    role_id: str = field(repr=True, kw_only=True)
    """The deleted role's ID."""

    server: Server | None = field(repr=True, kw_only=True)
    """The server the role was deleted from, if available."""

    role: Role | None = field(repr=True, kw_only=True)
    """The deleted role object, if available."""

    def before_dispatch(self) -> None:
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
    """Dispatched when the user details are updated."""

    event_name: typing.ClassVar[typing.Literal['user_update']] = 'user_update'

    user: PartialUser = field(repr=True, kw_only=True)
    """The fields that were updated."""

    before: User | None = field(repr=True, kw_only=True)
    """The user as it was before being updated, if available."""

    after: User | None = field(repr=True, kw_only=True)
    """The user as it was updated, if available."""

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
    """Dispatched when the relationship with user was updated."""

    event_name: typing.ClassVar[typing.Literal['user_relationship_update']] = 'user_relationship_update'

    current_user_id: str = field(repr=True, kw_only=True)
    """The current user ID."""

    old_user: User | None = field(repr=True, kw_only=True)
    """The user as it was before being updated, if available."""

    new_user: User = field(repr=True, kw_only=True)
    """The user as it was updated."""

    before: RelationshipStatus | None = field(repr=True, kw_only=True)
    """The old relationship found in cache."""

    @property
    def after(self) -> RelationshipStatus:
        """The new relationship with the user."""
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
    """Dispatched when the user settings are changed, likely from remote device."""

    event_name: typing.ClassVar[typing.Literal['user_settings_update']] = 'user_settings_update'

    current_user_id: str = field(repr=True, kw_only=True)
    """The current user ID."""

    partial: UserSettings = field(repr=True, kw_only=True)
    """The fields that were updated."""

    before: UserSettings = field(repr=True, kw_only=True)
    """The settings as they were before being updated.
    
    .. note::
        This is populated properly only if user settings are available.
    """

    after: UserSettings = field(repr=True, kw_only=True)
    """The settings as they were updated."""

    def process(self) -> bool:
        settings = self.shard.state.settings
        if settings.mocked:
            return False
        settings._update(self.partial)
        return True


@define(slots=True)
class UserPlatformWipeEvent(BaseEvent):
    """Dispatched when the user has been platform banned or deleted their account.

    Clients should remove the following associated data:
    - DM Channels
    - Messages
    - Relationships
    - Server Memberships

    User flags are specified to explain why a wipe is occurring though not all reasons will necessarily ever appear.
    """

    event_name: typing.ClassVar[typing.Literal['user_platform_wipe']] = 'user_platform_wipe'

    user_id: str = field(repr=True, kw_only=True)
    """The wiped user's ID."""

    flags: UserFlags = field(repr=True, kw_only=True)
    """The user's flags, explaining reason of the wipe."""

    before: User | None = field(repr=True, kw_only=True)
    """The user as it would exist before, if available."""

    after: User | None = field(repr=True, kw_only=True)
    """The wiped user, if available."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return

        self.before = cache.get_user(self.user_id, caching._USER_PLATFORM_WIPE)

        before = self.before
        if before is not None:
            after = copy(before)
            after.name = 'Removed User'
            after.display_name = None
            after.internal_avatar = None
            after.flags = self.flags
            after.relationship = RelationshipStatus.none
            after.online = False
            self.after = after

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache or not self.after:
            return False
        cache.store_user(self.after, caching._USER_RELATIONSHIP_UPDATE)
        return True


@define(slots=True)
class WebhookCreateEvent(BaseEvent):
    """Dispatched when the webhook is created in a channel."""

    event_name: typing.ClassVar[typing.Literal['webhook_create']] = 'webhook_create'

    webhook: Webhook = field(repr=True, kw_only=True)
    """The created webhook."""


@define(slots=True)
class WebhookUpdateEvent(BaseEvent):
    """Dispatched when the webhook details are updated."""

    event_name: typing.ClassVar[typing.Literal['webhook_update']] = 'webhook_update'

    webhook: PartialWebhook = field(repr=True, kw_only=True)
    """The fields that were updated."""


@define(slots=True)
class WebhookDeleteEvent(BaseEvent):
    """Dispatched when the webhook is deleted."""

    event_name: typing.ClassVar[typing.Literal['webhook_delete']] = 'webhook_delete'

    webhook_id: str = field(repr=True, kw_only=True)
    """The deleted webhook's ID."""

    webhook: Webhook | None = field(repr=True, kw_only=True)
    """The deleted webhook object, if available."""


@define(slots=True)
class AuthifierEvent(BaseEvent):
    """Dispatched when Authifier-related event happens."""

    event_name: typing.ClassVar[str] = 'authifier'


@define(slots=True)
class SessionCreateEvent(AuthifierEvent):
    """Dispatched when new session is created."""

    event_name: typing.ClassVar[str] = 'session_create'

    session: Session = field(repr=True, kw_only=True)
    """The created session."""


@define(slots=True)
class SessionDeleteEvent(AuthifierEvent):
    """Dispatched when session is deleted."""

    event_name: typing.ClassVar[str] = 'session_delete'

    current_user_id: str = field(repr=True, kw_only=True)
    """The connected user's ID."""

    session_id: str = field(repr=True, kw_only=True)
    """The deleted session's ID."""


@define(slots=True)
class SessionDeleteAllEvent(AuthifierEvent):
    """Dispatched when all sessions are deleted (and optionally except one)."""

    event_name: typing.ClassVar[str] = 'session_delete_all'

    current_user_id: str = field(repr=True, kw_only=True)
    """The connected user's ID."""

    exclude_session_id: str | None = field(repr=True, kw_only=True)
    """The session's ID that is excluded from deletion, if any."""


@define(slots=True)
class LogoutEvent(BaseEvent):
    """Dispatched when the connected user got logged out."""

    event_name: typing.ClassVar[str] = 'logout'


@define(slots=True)
class VoiceChannelJoinEvent(BaseEvent):
    """Dispatched when a user joins a voice channel."""

    event_name: typing.ClassVar[str] = 'voice_channel_join'

    channel_id: str = field(repr=True, kw_only=True)
    """The channel's ID the user joined to."""

    state: UserVoiceState = field(repr=True, kw_only=True)
    """The user's voice state."""


@define(slots=True)
class VoiceChannelLeaveEvent(BaseEvent):
    """Dispatched when a user left voice channel."""

    event_name: typing.ClassVar[str] = 'voice_channel_leave'

    channel_id: str = field(repr=True, kw_only=True)
    """The channel's ID the user left from."""

    user_id: str = field(repr=True, kw_only=True)
    """The user's ID that left the voice channel."""

    state: UserVoiceState | None = field(repr=True, kw_only=True)
    """The user's voice state."""


@define(slots=True)
class UserVoiceStateUpdateEvent(BaseEvent):
    """Dispatched when a user's voice state is updated."""

    event_name: typing.ClassVar[str] = 'user_voice_state_update'

    channel_id: str = field(repr=True, kw_only=True)
    """The channel's ID the user left from."""

    user_id: str = field(repr=True, kw_only=True)
    """The user's ID that left the voice channel."""

    state: PartialUserVoiceState | None = field(repr=True, kw_only=True)
    """The fields that were updated."""


@define(slots=True)
class AuthenticatedEvent(BaseEvent):
    """Dispatched when the WebSocket was successfully authenticated."""

    event_name: typing.ClassVar[str] = 'authenticated'


@define(slots=True)
class BeforeConnectEvent(BaseEvent):
    """Dispatched before connection to Revolt WebSocket is made."""

    event_name: typing.ClassVar[str] = 'before_connect'


@define(slots=True)
class AfterConnectEvent(BaseEvent):
    """Dispatched after connection to Revolt WebSocket is made."""

    event_name: typing.ClassVar[str] = 'after_connect'

    socket: aiohttp.ClientWebSocketResponse = field(repr=True, kw_only=True)
    """The connected WebSocket."""


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
    'VoiceChannelJoinEvent',
    'VoiceChannelLeaveEvent',
    'UserVoiceStateUpdateEvent',
    'AuthenticatedEvent',
    'BeforeConnectEvent',
    'AfterConnectEvent',
)
