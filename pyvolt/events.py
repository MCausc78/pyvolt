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

from copy import copy
from datetime import datetime
import typing

# Due to Pyright being stupid (or attrs), we have to cast everything to typing.Any
from typing import cast as _cast

from attrs import Factory, define, field

from . import cache as caching, utils
from .channel import (
    PartialChannel,
    SavedMessagesChannel,
    DMChannel,
    GroupChannel,
    PrivateChannel,
    BaseServerChannel,
    TextChannel,
    ServerChannel,
    Channel,
)
from .emoji import ServerEmoji
from .enums import MemberRemovalIntention, RelationshipStatus
from .flags import UserFlags
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
    from .safety_reports import CreatedReport
    from .settings import UserSettings
    from .shard import Shard
    from .user import UserVoiceState, PartialUserVoiceState
    from .webhook import Webhook, PartialWebhook

_new_user_flags = UserFlags.__new__


@define(slots=True)
class BaseEvent:
    """Base class for all events."""

    # shard: Shard = field(repr=True, kw_only=True)
    is_canceled: bool = field(default=False, repr=True, kw_only=True)
    """:class:`bool`: Whether the event is canceled."""

    def set_canceled(self, value: bool, /) -> bool:
        """Whether to cancel event processing (updating cache) or not."""
        if self.is_canceled is value:
            return False
        self.is_canceled = value
        return True

    def cancel(self) -> bool:
        """Cancels the event processing (updating cache).

        Returns
        -------
        :class:`bool`
            Whether the event was not canceled before.
        """
        return self.set_canceled(True)

    def uncancel(self) -> bool:
        """Uncancels the event processing (updating cache).

        Returns
        -------
        :class:`bool`
            Whether the event was not canceled before.
        """
        return self.set_canceled(False)

    async def abefore_dispatch(self) -> None:
        """|coro|

        Asynchronous version of :meth:`.before_dispatch`.
        """
        pass

    def before_dispatch(self) -> None:
        """Called before handlers are invoked."""
        pass

    async def aprocess(self) -> typing.Any:
        """|coro|

        Asynchronous version of :meth:`.process`.
        """
        pass

    def process(self) -> typing.Any:
        """Any: Called when handlers got invoked and temporary subscriptions were handled and removed."""
        pass


@define(slots=True)
class ShardEvent(BaseEvent):
    """Base class for events arrived over WebSocket."""

    shard: Shard = field(repr=True, kw_only=True)
    """:class:`.Shard`: The shard the event arrived on."""


@define(slots=True)
class ReadyEvent(ShardEvent):
    """Dispatched when initial state is available.

    .. warning::
        This event may be dispatched multiple times due to periodic reconnects.
    """

    event_name: typing.ClassVar[typing.Literal['ready']] = 'ready'

    users: list[User] = field(repr=True, kw_only=True)
    """List[:class:`.User`]: The users that the client can see (from DMs, groups, and relationships).
    
    This attribute contains connected user, usually at end of list, but sometimes not at end.
    """

    servers: list[Server] = field(repr=True, kw_only=True)
    """List[:class:`.Server`]: The servers the connected user is in."""

    channels: list[Channel] = field(repr=True, kw_only=True)
    """List[:class:`.Channel`]: The DM channels, server channels and groups the connected user participates in."""

    members: list[Member] = field(repr=True, kw_only=True)
    """List[:class:`.Member`]: The own members for servers."""

    emojis: list[ServerEmoji] = field(repr=True, kw_only=True)
    """List[:class:`.ServerEmoji`]: The emojis from servers the user participating in."""

    me: OwnUser = field(repr=True, kw_only=True)
    """:class:`.OwnUser`: The connected user."""

    user_settings: UserSettings = field(repr=True, kw_only=True)
    """:class:`.UserSettings`: The settings for connected user.
    
    .. note::
        This attribute is unavailable on bot accounts.
    """

    read_states: list[ReadState] = field(repr=True, kw_only=True)
    """List[:class:`.ReadState`]: The read states for channels ever seen by user. This is not always populated, and unavailable for bots.

    .. note::
        This attribute is unavailable on bot accounts.
    """

    voice_states: list[ChannelVoiceStateContainer] = field(repr=True, kw_only=True)
    """List[:class:`.ChannelVoiceStateContainer`]: The voice states of the text/voice channels."""

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

        ctx = (
            caching.ReadyEventCacheContext(
                type=caching.CacheContextType.ready_event,
                event=self,
            )
            if 'ReadyEvent' in state.provide_cache_context_in
            else caching._READY_EVENT
        )

        for u in self.users:
            cache.store_user(u, ctx)

        for s in self.servers:
            cache.store_server(s, ctx)

        for channel in self.channels:
            cache.store_channel(channel, ctx)
            if channel.__class__ is DMChannel or isinstance(channel, DMChannel):
                cache.store_private_channel_by_user(channel, ctx)  # type: ignore
            elif channel.__class__ is SavedMessagesChannel or isinstance(channel, SavedMessagesChannel):
                state._saved_notes = channel  # type: ignore

        for m in self.members:
            cache.store_server_member(m, ctx)

        for e in self.emojis:
            cache.store_emoji(e, ctx)

        for rs in self.read_states:
            cache.store_read_state(rs, ctx)

        cache.bulk_store_channel_voice_states({vs.channel_id: vs for vs in self.voice_states}, ctx)

        return True


@define(slots=True)
class BaseChannelCreateEvent(ShardEvent):
    """Base class for events when a channel is created."""

    event_name: typing.ClassVar[str] = 'channel_create'


@define(slots=True)
class PrivateChannelCreateEvent(BaseChannelCreateEvent):
    """Dispatched when the user created a DM, or started participating in group."""

    event_name: typing.ClassVar[str] = 'private_channel_create'

    channel: PrivateChannel = field(repr=True, kw_only=True)
    """:class:`.PrivateChannel`: The joined DM or group channel."""

    def process(self) -> bool:
        state = self.shard.state
        cache = state.cache

        if not cache:
            return False

        ctx = (
            caching.PrivateChannelCreateEventCacheContext(
                type=caching.CacheContextType.private_channel_create_event,
                event=self,
            )
            if 'PrivateChannelCreate' in state.provide_cache_context_in
            else caching._PRIVATE_CHANNEL_CREATE_EVENT
        )

        channel = self.channel
        cache.store_channel(channel, ctx)

        if isinstance(channel, DMChannel):
            cache.store_private_channel_by_user(channel, ctx)

        return True


@define(slots=True)
class ServerChannelCreateEvent(BaseChannelCreateEvent):
    """Dispatched when the channel is created in server or became open to the connected user."""

    event_name: typing.ClassVar[str] = 'server_channel_create'

    channel: ServerChannel = field(repr=True, kw_only=True)
    """:class:`.ServerChannel`: The created server channel."""

    def process(self) -> bool:
        state = self.shard.state
        cache = state.cache

        if not cache:
            return False

        ctx = (
            caching.ServerChannelCreateEventCacheContext(
                type=caching.CacheContextType.server_channel_create_event,
                event=self,
            )
            if 'ServerChannelCreate' in state.provide_cache_context_in
            else caching._SERVER_CHANNEL_CREATE_EVENT
        )

        cache.store_channel(self.channel, ctx)
        return True


ChannelCreateEvent = PrivateChannelCreateEvent | ServerChannelCreateEvent


@define(slots=True)
class ChannelUpdateEvent(ShardEvent):
    """Dispatched when the channel is updated."""

    event_name: typing.ClassVar[typing.Literal['channel_update']] = 'channel_update'

    channel: PartialChannel = field(repr=True, kw_only=True)
    """:class:`.PartialChannel`: The fields that were updated."""

    before: Channel | None = field(repr=True, kw_only=True)
    """Optional[:class:`.Channel`]: The channel as it was before being updated, if available."""

    after: Channel | None = field(repr=True, kw_only=True)
    """Optional[:class:`.Channel`]: The channel as it was updated, if available."""

    cache_context: caching.UndefinedCacheContext | caching.ChannelUpdateEventCacheContext = field(
        default=Factory(
            lambda self: _cast(
                'typing.Any',
                caching.ChannelUpdateEventCacheContext(
                    type=caching.CacheContextType.channel_update_event,
                    event=self,
                )
                if 'ChannelUpdateEvent' in self.shard.state.provide_cache_context_in
                else caching._CHANNEL_UPDATE_EVENT,
            ),
            takes_self=True,
        ),
        repr=False,
        hash=False,
        init=False,
        eq=False,
    )
    """Union[:class:`.UndefinedCacheContextType`, :class:`.ChannelUpdateEventCacheContext`]: The cache context used."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        before = cache.get_channel(self.channel.id, self.cache_context)
        self.before = before
        if not before:
            return

        after = copy(before)
        after.locally_update(self.channel)
        self.after = after

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache or not self.after:
            return False
        cache.store_channel(self.after, self.cache_context)
        return True


@define(slots=True)
class ChannelDeleteEvent(ShardEvent):
    """Dispatched when the server channel or group is deleted or became hidden for the connected user."""

    event_name: typing.ClassVar[typing.Literal['channel_delete']] = 'channel_delete'

    channel_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The channel's ID that got deleted or hidden."""

    channel: Channel | None = field(repr=True, kw_only=True)
    """Optional[:class:`.Channel`]: The deleted channel object, if available."""

    cache_context: caching.UndefinedCacheContext | caching.ChannelDeleteEventCacheContext = field(
        default=Factory(
            lambda self: _cast(
                'typing.Any',
                caching.ChannelDeleteEventCacheContext(
                    type=caching.CacheContextType.channel_delete_event,
                    event=self,
                )
                if 'ChannelDeleteEvent' in self.shard.state.provide_cache_context_in
                else caching._CHANNEL_DELETE_EVENT,
            ),
            takes_self=True,
        ),
        repr=False,
        hash=False,
        init=False,
        eq=False,
    )
    """Union[:class:`.UndefinedCacheContext`, :class:`.ChannelDeleteEventCacheContext`]: The cache context used."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        self.channel = cache.get_channel(self.channel_id, self.cache_context)

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False

        cache.delete_channel(self.channel_id, self.cache_context)
        # TODO: Remove when backend will tell us to update all channels. (ServerUpdate event)
        if isinstance(self.channel, BaseServerChannel):
            server = cache.get_server(self.channel.server_id, self.cache_context)
            if server:
                try:
                    server.internal_channels[1].remove(self.channel.id)  # type: ignore # cached servers have only channel IDs internally
                except ValueError:
                    pass
                else:
                    cache.store_server(server, self.cache_context)
        elif isinstance(self.channel, DMChannel):
            cache.delete_private_channel_by_user(self.channel.recipient_id, self.cache_context)
        cache.delete_messages_of(self.channel_id, self.cache_context)
        return True


@define(slots=True)
class GroupRecipientAddEvent(ShardEvent):
    """Dispatched when recipient is added to the group."""

    event_name: typing.ClassVar[typing.Literal['recipient_add']] = 'recipient_add'

    channel_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The affected group's ID."""

    user_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The user's ID who was added to the group."""

    group: GroupChannel | None = field(repr=True, kw_only=True)
    """Optional[:class:`.GroupChannel`]: The group in cache (in previous state as it had no recipient), if available."""

    cache_context: caching.UndefinedCacheContext | caching.GroupRecipientAddEventCacheContext = field(
        default=Factory(
            lambda self: _cast(
                'typing.Any',
                caching.GroupRecipientAddEventCacheContext(
                    type=caching.CacheContextType.group_recipient_add_event,
                    event=self,
                )
                if 'GroupRecipientAddEvent' in self.shard.state.provide_cache_context_in
                else caching._GROUP_RECIPIENT_ADD_EVENT,
            ),
            takes_self=True,
        ),
        repr=False,
        hash=False,
        init=False,
        eq=False,
    )
    """Union[:class:`.UndefinedCacheContext`, :class:`.GroupRecipientAddEventCacheContext`]: The cache context used."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        group = cache.get_channel(self.channel_id, self.cache_context)
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
        cache.store_channel(self.group, self.cache_context)

        return True


@define(slots=True)
class GroupRecipientRemoveEvent(ShardEvent):
    """Dispatched when recipient is removed from the group."""

    event_name: typing.ClassVar[typing.Literal['recipient_remove']] = 'recipient_remove'

    channel_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The affected group's ID."""

    user_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The user's ID who was removed from the group."""

    group: GroupChannel | None = field(repr=True, kw_only=True)
    """Optional[:class:`.GroupChannel`]: The group in cache (in previous state as it had recipient), if available."""

    cache_context: caching.UndefinedCacheContext | caching.GroupRecipientRemoveEventCacheContext = field(
        default=Factory(
            lambda self: _cast(
                'typing.Any',
                caching.GroupRecipientRemoveEventCacheContext(
                    type=caching.CacheContextType.group_recipient_remove_event,
                    event=self,
                )
                if 'GroupRecipientRemoveEvent' in self.shard.state.provide_cache_context_in
                else caching._GROUP_RECIPIENT_REMOVE_EVENT,
            ),
            takes_self=True,
        ),
        repr=False,
        hash=False,
        init=False,
        eq=False,
    )
    """Union[:class:`.UndefinedCacheContext`, :class:`.GroupRecipientRemoveEventCacheContext`]: The cache context used."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        group = cache.get_channel(self.channel_id, self.cache_context)
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
        cache.store_channel(self.group, self.cache_context)

        return True


@define(slots=True)
class ChannelStartTypingEvent(ShardEvent):
    """Dispatched when someone starts typing in a channel."""

    event_name: typing.ClassVar[typing.Literal['channel_start_typing']] = 'channel_start_typing'

    channel_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The channel's ID where user started typing in."""

    user_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The user's ID who started typing."""


@define(slots=True)
class ChannelStopTypingEvent(ShardEvent):
    """Dispatched when someone stopped typing in a channel."""

    event_name: typing.ClassVar[typing.Literal['channel_stop_typing']] = 'channel_stop_typing'

    channel_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The channel's ID where user stopped typing in."""

    user_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The user's ID who stopped typing."""


@define(slots=True)
class MessageAckEvent(ShardEvent):
    """Dispatched when the connected user acknowledges the message in a channel (usually from remote device)."""

    event_name: typing.ClassVar[typing.Literal['message_ack']] = 'message_ack'

    channel_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The channel's ID the message is in."""

    message_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The message's ID that got acknowledged."""

    user_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The connected user's ID."""

    def process(self) -> bool:
        state = self.shard.state
        cache = state.cache

        if not cache:
            return False

        ctx = (
            caching.MessageAckEventCacheContext(
                type=caching.CacheContextType.message_ack_event,
                event=self,
            )
            if 'MessageAck' in state.provide_cache_context_in
            else caching._MESSAGE_ACK_EVENT
        )

        read_state = cache.get_read_state(self.channel_id, ctx)
        if read_state:
            # opposite effect cannot be done
            if read_state.last_acked_message_id and self.message_id >= read_state.last_acked_message_id:
                acked_message_id = read_state.last_acked_message_id

                read_state.mentioned_in = [m for m in read_state.mentioned_in if m >= acked_message_id]

            read_state.last_acked_message_id = self.message_id
            cache.store_read_state(read_state, ctx)

        return True


@define(slots=True)
class MessageCreateEvent(ShardEvent):
    """Dispatched when someone sends message in a channel."""

    event_name: typing.ClassVar[typing.Literal['message_create']] = 'message_create'

    message: Message = field(repr=True, kw_only=True)
    """:class:`.Message`: The message sent."""

    def process(self) -> bool:
        state = self.shard.state
        cache = state.cache

        if not cache:
            return False

        ctx = (
            caching.MessageCreateEventCacheContext(
                type=caching.CacheContextType.message_create_event,
                event=self,
            )
            if 'MessageCreate' in state.provide_cache_context_in
            else caching._MESSAGE_CREATE_EVENT
        )

        author = self.message._author
        if isinstance(author, Member):
            if isinstance(author._user, User):
                cache.store_user(author._user, ctx)
            cache.store_server_member(author, ctx)
        elif isinstance(author, User):
            cache.store_user(author, ctx)

        channel = cache.get_channel(self.message.channel_id, ctx)
        if channel and isinstance(
            channel,
            (DMChannel, GroupChannel, TextChannel),
        ):
            channel.last_message_id = self.message.id

        read_state = cache.get_read_state(self.message.channel_id, ctx)
        if read_state:
            flags = self.message.flags

            # TODO: Maybe ignore @everyone and @online pings in DM and groups?
            mentioned = read_state.user_id in self.message.mention_ids or flags.mention_everyone or flags.mention_online

            role_mention_ids = self.message.role_mention_ids
            if not mentioned and role_mention_ids and isinstance(channel, BaseServerChannel):
                server_id = channel.server_id
                me = cache.get_server_member(server_id, read_state.user_id, ctx)
                if me is not None:
                    mentioned = any(role_id in role_mention_ids for role_id in me.roles)

            if mentioned and self.message.id not in read_state.mentioned_in:
                read_state.mentioned_in.append(self.message.id)
                cache.store_read_state(read_state, ctx)

        channel = cache.get_channel(self.message.channel_id, ctx)
        if channel and isinstance(
            channel,
            (DMChannel, GroupChannel, TextChannel),
        ):
            channel.last_message_id = self.message.id

        cache.store_message(self.message, ctx)

        return True

    def call_object_handlers_hook(self, client: Client, /) -> utils.MaybeAwaitable[None]:
        if hasattr(client, 'on_message'):
            return client.on_message(self.message)


@define(slots=True)
class MessageUpdateEvent(ShardEvent):
    """Dispatched when the message is updated."""

    event_name: typing.ClassVar[typing.Literal['message_update']] = 'message_update'

    message: PartialMessage = field(repr=True, kw_only=True)
    """:class:`.PartialMessage`: The fields that were updated."""

    before: Message | None = field(repr=True, kw_only=True)
    """Optional[:class:`.Message`]: The message as it was before being updated, if available."""

    after: Message | None = field(repr=True, kw_only=True)
    """Optional[:class:`.Message`]: The message as it was updated, if available."""

    cache_context: caching.UndefinedCacheContext | caching.MessageUpdateEventCacheContext = field(
        default=Factory(
            lambda self: _cast(
                'typing.Any',
                caching.MessageUpdateEventCacheContext(
                    type=caching.CacheContextType.message_update_event,
                    event=self,
                )
                if 'MessageUpdateEvent' in self.shard.state.provide_cache_context_in
                else caching._MESSAGE_UPDATE_EVENT,
            ),
            takes_self=True,
        ),
        repr=False,
        hash=False,
        init=False,
        eq=False,
    )
    """Union[:class:`.UndefinedCacheContext`, :class:`.MessageUpdateEventCacheContext`]: The cache context used."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache

        if not cache:
            return
        before = cache.get_message(self.message.channel_id, self.message.id, self.cache_context)
        if not before:
            return
        self.before = before
        after = copy(before)
        after.locally_update(self.message)
        self.after = after

    def process(self) -> bool:
        cache = self.shard.state.cache

        if not cache or not self.after:
            return False
        cache.store_message(self.after, self.cache_context)
        return True


@define(slots=True)
class MessageAppendEvent(ShardEvent):
    """Dispatched when embeds are appended to the message."""

    event_name: typing.ClassVar[typing.Literal['message_append']] = 'message_append'

    data: MessageAppendData = field(repr=True, kw_only=True)
    """:class:`.MessageAppendData`: The data that got appended to message."""

    message: Message | None = field(repr=True, kw_only=True)
    """Optional[:class:`.Message`]: The message as it was before being updated, if available."""

    cache_context: caching.UndefinedCacheContext | caching.MessageAppendEventCacheContext = field(
        default=Factory(
            lambda self: _cast(
                'typing.Any',
                caching.MessageAppendEventCacheContext(
                    type=caching.CacheContextType.message_append_event,
                    event=self,
                )
                if 'MessageAppendEvent' in self.shard.state.provide_cache_context_in
                else caching._MESSAGE_APPEND_EVENT,
            ),
            takes_self=True,
        ),
        repr=False,
        hash=False,
        init=False,
        eq=False,
    )
    """Union[:class:`.UndefinedCacheContext`, :class:`.MessageAppendEventCacheContext`]: The cache context used."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache

        if not cache:
            return
        self.message = cache.get_message(self.data.channel_id, self.data.id, self.cache_context)

    def process(self) -> bool:
        cache = self.shard.state.cache

        if not cache or not self.message:
            return False

        self.message.locally_append(self.data)
        cache.store_message(self.message, self.cache_context)
        return True


@define(slots=True)
class MessageDeleteEvent(ShardEvent):
    """Dispatched when the message is deleted in channel."""

    event_name: typing.ClassVar[typing.Literal['message_delete']] = 'message_delete'

    channel_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The channel's ID the message was in."""

    message_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The deleted message's ID."""

    message: Message | None = field(repr=True, kw_only=True)
    """Optional[:class:`.Message`]: The deleted message object, if available."""

    cache_context: caching.UndefinedCacheContext | caching.MessageDeleteEventCacheContext = field(
        default=Factory(
            lambda self: _cast(
                'typing.Any',
                caching.MessageDeleteEventCacheContext(
                    type=caching.CacheContextType.message_delete_event,
                    event=self,
                )
                if 'MessageDeleteEvent' in self.shard.state.provide_cache_context_in
                else caching._MESSAGE_DELETE_EVENT,
            ),
            takes_self=True,
        ),
        repr=False,
        hash=False,
        init=False,
        eq=False,
    )
    """Union[:class:`.UndefinedCacheContext`, :class:`.MessageDeleteEventCacheContext`]: The cache context used."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache

        if not cache:
            return
        self.message = cache.get_message(self.channel_id, self.message_id, self.cache_context)

    def process(self) -> bool:
        cache = self.shard.state.cache

        if not cache:
            return False
        cache.delete_message(self.channel_id, self.message_id, self.cache_context)
        return True


@define(slots=True)
class MessageReactEvent(ShardEvent):
    """Dispatched when someone reacts to message."""

    event_name: typing.ClassVar[typing.Literal['message_react']] = 'message_react'

    channel_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The channel's ID the message is in."""

    message_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The message's ID that got a reaction."""

    user_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The user's ID that added a reaction to the message."""

    emoji: str = field(repr=True, kw_only=True)
    """:class:`str`: The emoji that was reacted with. May be either ULID or Unicode emoji."""

    message: Message | None = field(repr=True, kw_only=True)
    """Optional[:class:`.Message`]: The message as it was before being updated, if available."""

    cache_context: caching.UndefinedCacheContext | caching.MessageReactEventCacheContext = field(
        default=Factory(
            lambda self: _cast(
                'typing.Any',
                caching.MessageReactEventCacheContext(
                    type=caching.CacheContextType.message_react_event,
                    event=self,
                )
                if 'MessageReactEvent' in self.shard.state.provide_cache_context_in
                else caching._MESSAGE_REACT_EVENT,
            ),
            takes_self=True,
        ),
        repr=False,
        hash=False,
        # init=False,
        # eq=False,
    )
    """Union[:class:`.UndefinedCacheContext`, :class:`.MessageReactEventCacheContext`]: The cache context used."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache

        if not cache:
            return
        self.message = cache.get_message(self.channel_id, self.message_id, self.cache_context)

    def process(self) -> bool:
        cache = self.shard.state.cache

        if not cache or not self.message:
            return False
        self.message.locally_react(self.user_id, self.emoji)
        cache.store_message(self.message, self.cache_context)
        return True


@define(slots=True)
class MessageUnreactEvent(ShardEvent):
    """Dispatched when someone removes their reaction from message."""

    event_name: typing.ClassVar[typing.Literal['message_unreact']] = 'message_unreact'

    channel_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The channel's ID the message is in."""

    message_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The message's ID that lost a reaction."""

    user_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The user's ID that removed reaction from the message."""

    emoji: str = field(repr=True, kw_only=True)
    """:class:`str`: The emoji that was reacted with before. May be either ULID or Unicode emoji."""

    message: Message | None = field(repr=True, kw_only=True)
    """Optional[:class:`.Message`]: The message as it was before being updated, if available."""

    cache_context: caching.UndefinedCacheContext | caching.MessageUnreactEventCacheContext = field(
        default=Factory(
            lambda self: _cast(
                'typing.Any',
                caching.MessageUnreactEventCacheContext(
                    type=caching.CacheContextType.message_unreact_event,
                    event=self,
                )
                if 'MessageUnreactEvent' in self.shard.state.provide_cache_context_in
                else caching._MESSAGE_UNREACT_EVENT,
            ),
            takes_self=True,
        ),
        repr=False,
        hash=False,
        init=False,
        eq=False,
    )
    """Union[:class:`.UndefinedCacheContext`, :class:`.MessageUnreactEventCacheContext`]: The cache context used."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache

        if not cache:
            return
        self.message = cache.get_message(self.channel_id, self.message_id, self.cache_context)

    def process(self) -> bool:
        cache = self.shard.state.cache

        if not cache or not self.message:
            return False
        self.message.locally_unreact(self.user_id, self.emoji)
        cache.store_message(self.message, self.cache_context)
        return True


@define(slots=True)
class MessageClearReactionEvent(ShardEvent):
    """Dispatched when reactions for specific emoji are removed from message."""

    event_name: typing.ClassVar[typing.Literal['message_clear_reaction']] = 'message_clear_reaction'

    channel_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The channel's ID the message is in."""

    message_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The message's ID that lost reactions."""

    emoji: str = field(repr=True, kw_only=True)
    """:class:`str`: The emoji whose reactions were removed. May be either ULID or Unicode emoji."""

    message: Message | None = field(repr=True, kw_only=True)
    """Optional[:class:`.Message`]: The message as it was before being updated, if available."""

    cache_context: caching.UndefinedCacheContext | caching.MessageClearReactionEventCacheContext = field(
        default=Factory(
            lambda self: _cast(
                'typing.Any',
                caching.MessageClearReactionEventCacheContext(
                    type=caching.CacheContextType.message_clear_reaction_event,
                    event=self,
                )
                if 'MessageClearReactionEvent' in self.shard.state.provide_cache_context_in
                else caching._MESSAGE_CLEAR_REACTION_EVENT,
            ),
            takes_self=True,
        ),
        repr=False,
        hash=False,
        init=False,
        eq=False,
    )
    """Union[:class:`.UndefinedCacheContext`, :class:`.MessageClearReactionEventCacheContext`]: The cache context used."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache

        if not cache:
            return
        self.message = cache.get_message(self.channel_id, self.message_id, self.cache_context)

    def process(self) -> bool:
        cache = self.shard.state.cache

        if not cache or not self.message:
            return False
        self.message.locally_clear_reactions(self.emoji)
        cache.store_message(self.message, self.cache_context)
        return True


@define(slots=True)
class MessageDeleteBulkEvent(ShardEvent):
    """Dispatched when multiple messages are deleted from channel."""

    event_name: typing.ClassVar[typing.Literal['message_delete_bulk']] = 'message_delete_bulk'

    channel_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The channel's ID where messages got deleted from."""

    message_ids: list[str] = field(repr=True, kw_only=True)
    """List[:class:`str`]: The list of message's IDs that got deleted."""

    messages: list[Message] = field(repr=True, kw_only=True)
    """List[:class:`.Message`]: The list of deleted messages, potentially retrieved from cache.
    
    Unlike :attr:`.message_ids`, some messages are
    not guaranteed to be here.
    """

    cache_context: caching.UndefinedCacheContext | caching.MessageDeleteBulkEventCacheContext = field(
        default=Factory(
            lambda self: _cast(
                'typing.Any',
                caching.MessageDeleteBulkEventCacheContext(
                    type=caching.CacheContextType.message_delete_bulk_event,
                    event=self,
                )
                if 'MessageDeleteBulkEvent' in self.shard.state.provide_cache_context_in
                else caching._MESSAGE_DELETE_BULK_EVENT,
            ),
            takes_self=True,
        ),
        repr=False,
        hash=False,
        init=False,
        eq=False,
    )
    """Union[:class:`.UndefinedCacheContext`, :class:`.MessageDeleteBulkEventCacheContext`]: The cache context used."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache

        if not cache:
            return

        for message_id in self.message_ids:
            message = cache.get_message(self.channel_id, message_id, self.cache_context)
            if message:
                self.messages.append(message)

    def process(self) -> bool:
        cache = self.shard.state.cache

        if not cache:
            return False

        for message_id in self.message_ids:
            cache.delete_message(self.channel_id, message_id, self.cache_context)

        return True


@define(slots=True)
class ServerCreateEvent(ShardEvent):
    """Dispatched when the server is created, or client joined server."""

    event_name: typing.ClassVar[typing.Literal['server_create']] = 'server_create'

    joined_at: datetime = field(repr=True, kw_only=True)
    """:class:`~datetime.datetime`: When the client got added to server, generated locally, and used internally."""

    server: Server = field(repr=True, kw_only=True)
    """:class:`.Server`: The server that client was added to."""

    emojis: list[ServerEmoji] = field(repr=True, kw_only=True)
    """List[:class:`.ServerEmoji`]: The server emojis."""

    voice_states: list[ChannelVoiceStateContainer] = field(repr=True, kw_only=True)
    """List[:class:`.ChannelVoiceStateContainer`]: The voice states of the text/voice channels in the server."""

    def process(self) -> bool:
        state = self.shard.state
        cache = state.cache

        if not cache:
            return False

        ctx = (
            caching.ServerCreateEventCacheContext(
                type=caching.CacheContextType.server_create_event,
                event=self,
            )
            if 'ServerCreateEvent' in state.provide_cache_context_in
            else caching._SERVER_CREATE_EVENT
        )

        for channel in self.server.prepare_cached():
            cache.store_channel(channel, ctx)
        cache.store_server(self.server, ctx)

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
                ctx,
            )

        for emoji in self.emojis:
            cache.store_emoji(emoji, ctx)

        cache.bulk_store_channel_voice_states({vs.channel_id: vs for vs in self.voice_states}, ctx)

        return True


@define(slots=True)
class ServerEmojiCreateEvent(ShardEvent):
    """Dispatched when emoji is created in server."""

    event_name: typing.ClassVar[typing.Literal['server_emoji_create']] = 'server_emoji_create'

    emoji: ServerEmoji = field(repr=True, kw_only=True)
    """:class:`.ServerEmoji`: The created emoji."""

    def process(self) -> bool:
        state = self.shard.state
        cache = state.cache

        if not cache:
            return False

        ctx = (
            caching.ServerEmojiCreateEventCacheContext(
                type=caching.CacheContextType.server_emoji_create_event,
                event=self,
            )
            if 'ServerEmojiCreateEvent' in state.provide_cache_context_in
            else caching._SERVER_EMOJI_CREATE_EVENT
        )

        cache.store_emoji(self.emoji, ctx)
        return True


@define(slots=True)
class ServerEmojiDeleteEvent(ShardEvent):
    """Dispatched when emoji is deleted from the server."""

    event_name: typing.ClassVar[typing.Literal['server_emoji_delete']] = 'server_emoji_delete'

    server_id: str | None = field(repr=True, kw_only=True)
    """:class:`str`: The server's ID where emoji got deleted from."""

    emoji_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The deleted emoji's ID."""

    emoji: ServerEmoji | None = field(repr=True, kw_only=True)
    """Optional[:class:`.ServerEmoji`]: The deleted emoji object, if available."""

    cache_context: caching.UndefinedCacheContext | caching.ServerEmojiDeleteEventCacheContext = field(
        default=Factory(
            lambda self: _cast(
                'typing.Any',
                caching.ServerEmojiDeleteEventCacheContext(
                    type=caching.CacheContextType.server_emoji_delete_event,
                    event=self,
                )
                if 'ServerEmojiDeleteEvent' in self.shard.state.provide_cache_context_in
                else caching._SERVER_EMOJI_DELETE_EVENT,
            ),
            takes_self=True,
        ),
        repr=False,
        hash=False,
        init=False,
        eq=False,
    )
    """Union[:class:`.UndefinedCacheContext`, :class:`.ServerEmojiDeleteEventCacheContext`]: The cache context used."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return

        emoji = cache.get_emoji(self.emoji_id, self.cache_context)
        if isinstance(emoji, ServerEmoji):
            self.emoji = emoji
            self.server_id = emoji.server_id

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False
        cache.delete_emoji(self.emoji_id, self.server_id, self.cache_context)
        return True


@define(slots=True)
class ServerUpdateEvent(ShardEvent):
    """Dispatched when the server details are updated."""

    event_name: typing.ClassVar[typing.Literal['server_update']] = 'server_update'

    server: PartialServer = field(repr=True, kw_only=True)
    """:class:`.PartialServer`: The fields that were updated."""

    before: Server | None = field(repr=True, kw_only=True)
    """Optional[:class:`.Server`]: The server as it was before being updated, if available."""

    after: Server | None = field(repr=True, kw_only=True)
    """Optional[:class:`.Server`]: The server as it was updated, if available."""

    cache_context: caching.UndefinedCacheContext | caching.ServerUpdateEventCacheContext = field(
        default=Factory(
            lambda self: _cast(
                'typing.Any',
                caching.ServerUpdateEventCacheContext(
                    type=caching.CacheContextType.server_update_event,
                    event=self,
                )
                if 'ServerUpdateEvent' in self.shard.state.provide_cache_context_in
                else caching._SERVER_UPDATE_EVENT,
            ),
            takes_self=True,
        ),
        repr=False,
        hash=False,
        init=False,
        eq=False,
    )
    """Union[:class:`.UndefinedCacheContext`, :class:`.ServerUpdateEventCacheContext`]: The cache context used."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        before = cache.get_server(self.server.id, self.cache_context)
        self.before = before
        if not before:
            return

        after = copy(before)
        after.locally_update(self.server)
        self.after = after

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache or not self.after:
            return False
        cache.store_server(self.after, self.cache_context)
        return True


@define(slots=True)
class ServerDeleteEvent(ShardEvent):
    """Dispatched when the server is deleted."""

    event_name: typing.ClassVar[typing.Literal['server_delete']] = 'server_delete'

    server_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The deleted server's ID."""

    server: Server | None = field(repr=True, kw_only=True)
    """Optional[:class:`.Server`]: The deleted server object, if available."""

    cache_context: caching.UndefinedCacheContext | caching.ServerDeleteEventCacheContext = field(
        default=Factory(
            lambda self: _cast(
                'typing.Any',
                caching.ServerDeleteEventCacheContext(
                    type=caching.CacheContextType.server_delete_event,
                    event=self,
                )
                if 'ServerDeleteEvent' in self.shard.state.provide_cache_context_in
                else caching._SERVER_DELETE_EVENT,
            ),
            takes_self=True,
        ),
        repr=False,
        hash=False,
        init=False,
        eq=False,
    )
    """Union[:class:`.UndefinedCacheContext`, :class:`.ServerDeleteEventCacheContext`]: The cache context used."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        self.server = cache.get_server(self.server_id, self.cache_context)

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache:
            return False

        cache.delete_server_emojis_of(self.server_id, self.cache_context)
        cache.delete_server_members_of(self.server_id, self.cache_context)
        cache.delete_server(self.server_id, self.cache_context)

        if self.server is not None:
            for channel_id in self.server.internal_channels[1]:
                assert isinstance(channel_id, str)
                cache.delete_read_state(channel_id, self.cache_context)
                cache.delete_channel_voice_state(channel_id, self.cache_context)

        return True


@define(slots=True)
class ServerMemberJoinEvent(ShardEvent):
    """Dispatched when the user got added to the server."""

    event_name: typing.ClassVar[typing.Literal['server_member_join']] = 'server_member_join'

    member: Member = field(repr=True, kw_only=True)
    """:class:`.Member`: The joined member."""

    def process(self) -> bool:
        state = self.shard.state
        cache = state.cache

        if not cache:
            return False

        ctx = (
            caching.ServerMemberJoinEventCacheContext(
                type=caching.CacheContextType.server_member_join_event,
                event=self,
            )
            if 'ServerMemberJoinEvent' in state.provide_cache_context_in
            else caching._SERVER_MEMBER_JOIN_EVENT
        )

        cache.store_server_member(self.member, ctx)
        return True


@define(slots=True)
class ServerMemberUpdateEvent(ShardEvent):
    """Dispatched when the member details are updated."""

    event_name: typing.ClassVar[typing.Literal['server_member_update']] = 'server_member_update'

    member: PartialMember = field(repr=True, kw_only=True)
    """:class:`.PartialMember`: The fields that were updated."""

    before: Member | None = field(repr=True, kw_only=True)
    """Optional[:class:`.Member`]: The member as it was before being updated, if available."""

    after: Member | None = field(repr=True, kw_only=True)
    """Optional[:class:`.Member`]: The member as it was updated, if available."""

    cache_context: caching.UndefinedCacheContext | caching.ServerMemberUpdateEventCacheContext = field(
        default=Factory(
            lambda self: _cast(
                'typing.Any',
                caching.ServerMemberUpdateEventCacheContext(
                    type=caching.CacheContextType.server_member_update_event,
                    event=self,
                )
                if 'ServerMemberUpdateEvent' in self.shard.state.provide_cache_context_in
                else caching._SERVER_MEMBER_UPDATE_EVENT,
            ),
            takes_self=True,
        ),
        repr=False,
        hash=False,
        init=False,
        eq=False,
    )
    """Union[:class:`.UndefinedCacheContext`, :class:`.ServerMemberUpdateEventCacheContext`]: The cache context used."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        before = cache.get_server_member(self.member.server_id, self.member.id, self.cache_context)
        self.before = before
        if not before:
            return

        after = copy(before)
        after.locally_update(self.member)
        self.after = after

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache or not self.after:
            return False
        cache.store_server_member(self.after, self.cache_context)
        return True


@define(slots=True)
class ServerMemberRemoveEvent(ShardEvent):
    """Dispatched when the member (or client user) got removed from server."""

    event_name: typing.ClassVar[typing.Literal['server_member_remove']] = 'server_member_remove'

    server_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The server's ID from which the user was removed from."""

    user_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The removed user's ID."""

    member: Member | None = field(repr=True, kw_only=True)
    """Optional[:class:`.Member`]: The removed member object, if available."""

    reason: MemberRemovalIntention = field(repr=True, kw_only=True)
    """:class:`.MemberRemovalIntention`: The reason why member was removed."""

    cache_context: caching.UndefinedCacheContext | caching.ServerMemberRemoveEventCacheContext = field(
        default=Factory(
            lambda self: _cast(
                'typing.Any',
                caching.ServerMemberRemoveEventCacheContext(
                    type=caching.CacheContextType.server_member_remove_event,
                    event=self,
                )
                if 'ServerMemberRemoveEvent' in self.shard.state.provide_cache_context_in
                else caching._SERVER_MEMBER_REMOVE_EVENT,
            ),
            takes_self=True,
        ),
        repr=False,
        hash=False,
        init=False,
        eq=False,
    )
    """Union[:class:`.UndefinedCacheContext`, :class:`.ServerMemberRemoveEventCacheContext`]: The cache context used."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        self.member = cache.get_server_member(self.server_id, self.user_id, self.cache_context)

    def process(self) -> bool:
        state = self.shard.state
        cache = state.cache
        if not cache:
            return False

        me = state.me
        is_me = me.id == self.user_id if me else False

        cache.delete_server_member(self.server_id, self.user_id, self.cache_context)
        if is_me:
            cache.delete_server_emojis_of(self.server_id, self.cache_context)
            cache.delete_server_members_of(self.server_id, self.cache_context)
            server = cache.delete_server(self.server_id, self.cache_context)

            if server is not None:
                for channel_id in server.internal_channels[1]:
                    assert isinstance(channel_id, str)
                    cache.delete_channel_voice_state(channel_id, self.cache_context)

        return True


@define(slots=True)
class RawServerRoleUpdateEvent(ShardEvent):
    """Dispatched when the role got created or updated in server."""

    event_name: typing.ClassVar[typing.Literal['raw_server_role_update']] = 'raw_server_role_update'

    role: PartialRole = field(repr=True, kw_only=True)
    """:class:`.PartialRole`: The fields that got updated."""

    old_role: Role | None = field(repr=True, kw_only=True)
    """Optional[:class:`.Role`]: The role as it was before being updated, if available."""

    new_role: Role | None = field(repr=True, kw_only=True)
    """Optional[:class:`.Role`]: The role as it was created or updated, if available."""

    server: Server | None = field(repr=True, kw_only=True)
    """Optional[:class:`.Server`]: The server the role got created or updated in."""

    cache_context: caching.UndefinedCacheContext | caching.RawServerRoleUpdateEventCacheContext = field(
        default=Factory(
            lambda self: _cast(
                'typing.Any',
                caching.RawServerRoleUpdateEventCacheContext(
                    type=caching.CacheContextType.raw_server_role_update_event,
                    event=self,
                )
                if 'RawServerRoleUpdateEvent' in self.shard.state.provide_cache_context_in
                else caching._RAW_SERVER_ROLE_UPDATE_EVENT,
            ),
            takes_self=True,
        ),
        repr=False,
        hash=False,
        init=False,
        eq=False,
    )
    """Union[:class:`.UndefinedCacheContext`, :class:`.RawServerRoleUpdateEventCacheContext`]: The cache context used."""

    def before_dispatch(self) -> None:
        self.new_role = self.role.into_full()

        cache = self.shard.state.cache
        if not cache:
            return

        self.server = cache.get_server(self.role.server_id, self.cache_context)

        if self.server is None:
            return

        old = self.old_role = self.server.roles.get(self.role.id)
        if old is not None:
            new = copy(old)
            new.locally_update(self.role)
            self.new_role = new

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache or self.server is None:
            return False

        self.server.upsert_role(self.new_role or self.role)
        cache.store_server(self.server, self.cache_context)
        return True


@define(slots=True)
class ServerRoleDeleteEvent(ShardEvent):
    """Dispatched when the role got deleted from server."""

    event_name: typing.ClassVar[typing.Literal['server_role_delete']] = 'server_role_delete'

    server_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The server's ID the role was in."""

    role_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The deleted role's ID."""

    server: Server | None = field(repr=True, kw_only=True)
    """Optional[:class:`.Server`]: The server the role was deleted from, if available."""

    role: Role | None = field(repr=True, kw_only=True)
    """Optional[:class:`.Role`]: The deleted role object, if available."""

    cache_context: caching.UndefinedCacheContext | caching.ServerRoleDeleteEventCacheContext = field(
        default=Factory(
            lambda self: _cast(
                'typing.Any',
                caching.ServerRoleDeleteEventCacheContext(
                    type=caching.CacheContextType.server_role_delete_event,
                    event=self,
                )
                if 'ServerRoleDeleteEvent' in self.shard.state.provide_cache_context_in
                else caching._SERVER_ROLE_DELETE_EVENT,
            ),
            takes_self=True,
        ),
        repr=False,
        hash=False,
        init=False,
        eq=False,
    )
    """Union[:class:`.UndefinedCacheContext`, :class:`.ServerRoleDeleteEventCacheContext`]: The cache context used."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        self.server = cache.get_server(self.server_id, self.cache_context)
        if self.server:
            self.role = self.server.roles.get(self.role_id)

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache or not self.server:
            return False

        self.server.roles.pop(self.role_id, None)

        cache.store_server(self.server, self.cache_context)
        return True


@define(slots=True)
class ReportCreateEvent(ShardEvent):
    """Dispatched when the report was created.

    .. warning::
        This event is not dispatched over WebSocket.
    """

    event_name: typing.ClassVar[typing.Literal['report_create']] = 'report_create'

    report: CreatedReport = field(repr=True, kw_only=True)
    """:class:`.CreatedReport`: The created report."""


@define(slots=True)
class UserUpdateEvent(ShardEvent):
    """Dispatched when the user details are updated."""

    event_name: typing.ClassVar[typing.Literal['user_update']] = 'user_update'

    user: PartialUser = field(repr=True, kw_only=True)
    """:class:`.PartialUser`: The fields that were updated."""

    before: User | None = field(repr=True, kw_only=True)
    """:class:`.User`: The user as it was before being updated, if available."""

    after: User | None = field(repr=True, kw_only=True)
    """:class:`.User`: The user as it was updated, if available."""

    cache_context: caching.UndefinedCacheContext | caching.UserUpdateEventCacheContext = field(
        default=Factory(
            lambda self: _cast(
                'typing.Any',
                caching.UserUpdateEventCacheContext(
                    type=caching.CacheContextType.user_update_event,
                    event=self,
                )
                if 'UserUpdateEvent' in self.shard.state.provide_cache_context_in
                else caching._USER_UPDATE_EVENT,
            ),
            takes_self=True,
        ),
        repr=False,
        hash=False,
        init=False,
        eq=False,
    )
    """Union[:class:`.UndefinedCacheContext`, :class:`.UserUpdateEventCacheContext`]: The cache context used."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        before = cache.get_user(self.user.id, self.cache_context)
        self.before = before
        if not before:
            return

        after = copy(before)
        after.locally_update(self.user)
        self.after = after

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache or not self.after:
            return False
        cache.store_user(self.after, self.cache_context)
        return True


@define(slots=True)
class UserRelationshipUpdateEvent(ShardEvent):
    """Dispatched when the relationship with user was updated."""

    event_name: typing.ClassVar[typing.Literal['user_relationship_update']] = 'user_relationship_update'

    current_user_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The current user ID."""

    old_user: User | None = field(repr=True, kw_only=True)
    """Optional[:class:`.User`]: The user as it was before being updated, if available."""

    new_user: User = field(repr=True, kw_only=True)
    """:class:`.User`: The user as it was updated."""

    before: RelationshipStatus | None = field(repr=True, kw_only=True)
    """Optional[:class:`.RelationshipStatus`]: The old relationship found in cache."""

    cache_context: caching.UndefinedCacheContext | caching.UserRelationshipUpdateEventCacheContext = field(
        default=Factory(
            lambda self: _cast(
                'typing.Any',
                caching.UserRelationshipUpdateEventCacheContext(
                    type=caching.CacheContextType.user_relationship_update_event,
                    event=self,
                )
                if 'UserRelationshipUpdateEvent' in self.shard.state.provide_cache_context_in
                else caching._USER_RELATIONSHIP_UPDATE_EVENT,
            ),
            takes_self=True,
        ),
        repr=False,
        hash=False,
        init=False,
        eq=False,
    )
    """Union[:class:`.UndefinedCacheContext`, :class:`.UserRelationshipUpdateEventCacheContext`]: The cache context used."""

    @property
    def after(self) -> RelationshipStatus:
        """:class:`.RelationshipStatus`: The new relationship with the user."""
        return self.new_user.relationship

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        self.old_user = cache.get_user(self.new_user.id, self.cache_context)

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
        cache.store_user(self.new_user, self.cache_context)
        return True


@define(slots=True)
class UserSettingsUpdateEvent(ShardEvent):
    """Dispatched when the user settings are changed, likely from remote device."""

    event_name: typing.ClassVar[typing.Literal['user_settings_update']] = 'user_settings_update'

    current_user_id: str = field(repr=True, kw_only=True)
    """The current user ID."""

    partial: UserSettings = field(repr=True, kw_only=True)
    """:class:`.UserSettings`: The fields that were updated."""

    before: UserSettings = field(repr=True, kw_only=True)
    """:class:`.UserSettings`: The settings as they were before being updated.
    
    .. note::
        This is populated properly only if user settings are available.
    """

    after: UserSettings = field(repr=True, kw_only=True)
    """:class:`.UserSettings`: The settings as they were updated."""

    def process(self) -> bool:
        settings = self.shard.state.settings
        if settings.mocked:
            return False
        settings.locally_update(self.partial)
        return True


@define(slots=True)
class UserPlatformWipeEvent(ShardEvent):
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
    """:class:`str`: The wiped user's ID."""

    raw_flags: int = field(repr=True, kw_only=True)
    """:class:`int`: The user's flags raw value, explaining reason of the wipe."""

    before: User | None = field(repr=True, kw_only=True)
    """Optional[:class:`.User`]: The user as it would exist before, if available."""

    after: User | None = field(repr=True, kw_only=True)
    """Optional[:class:`.User`]: The wiped user, if available."""

    cache_context: caching.UndefinedCacheContext | caching.UserPlatformWipeEventCacheContext = field(
        default=Factory(
            lambda self: _cast(
                'typing.Any',
                caching.UserPlatformWipeEventCacheContext(
                    type=caching.CacheContextType.user_platform_wipe_event,
                    event=self,
                )
                if 'UserPlatformWipeEvent' in self.shard.state.provide_cache_context_in
                else caching._USER_PLATFORM_WIPE_EVENT,
            ),
            takes_self=True,
        ),
        repr=False,
        hash=False,
        init=False,
        eq=False,
    )
    """Union[:class:`.UndefinedCacheContext`, :class:`.UserPlatformWipeEventCacheContext`]: The cache context used."""

    @property
    def flags(self) -> UserFlags:
        """:class:`.UserFlags`: The user's flags, explaining reason of the wipe."""
        ret = _new_user_flags(UserFlags)
        ret.value = self.raw_flags
        return ret

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return

        self.before = cache.get_user(self.user_id, self.cache_context)

        before = self.before
        if before is not None:
            after = copy(before)
            after.name = 'Removed User'
            after.display_name = None
            after.internal_avatar = None
            after.raw_flags = self.raw_flags
            after.relationship = RelationshipStatus.none
            after.online = False
            self.after = after

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache or not self.after:
            return False
        cache.store_user(self.after, self.cache_context)
        return True


@define(slots=True)
class WebhookCreateEvent(ShardEvent):
    """Dispatched when the webhook is created in a channel."""

    event_name: typing.ClassVar[typing.Literal['webhook_create']] = 'webhook_create'

    webhook: Webhook = field(repr=True, kw_only=True)
    """:class:`.Webhook`: The created webhook."""


@define(slots=True)
class WebhookUpdateEvent(ShardEvent):
    """Dispatched when the webhook details are updated."""

    event_name: typing.ClassVar[typing.Literal['webhook_update']] = 'webhook_update'

    webhook: PartialWebhook = field(repr=True, kw_only=True)
    """:class:`.PartialWebhook`: The fields that were updated."""


@define(slots=True)
class WebhookDeleteEvent(ShardEvent):
    """Dispatched when the webhook is deleted."""

    event_name: typing.ClassVar[typing.Literal['webhook_delete']] = 'webhook_delete'

    webhook_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The deleted webhook's ID."""

    webhook: Webhook | None = field(repr=True, kw_only=True)
    """Optional[:class:`.Webhook`]: The deleted webhook object, if available."""


@define(slots=True)
class AuthifierEvent(ShardEvent):
    """Dispatched when Authifier-related event happens."""

    event_name: typing.ClassVar[str] = 'authifier'


@define(slots=True)
class SessionCreateEvent(AuthifierEvent):
    """Dispatched when new session is created."""

    event_name: typing.ClassVar[str] = 'session_create'

    session: Session = field(repr=True, kw_only=True)
    """:class:`.Session`: The created session."""


@define(slots=True)
class SessionDeleteEvent(AuthifierEvent):
    """Dispatched when session is deleted."""

    event_name: typing.ClassVar[str] = 'session_delete'

    current_user_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The connected user's ID."""

    session_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The deleted session's ID."""


@define(slots=True)
class SessionDeleteAllEvent(AuthifierEvent):
    """Dispatched when all sessions are deleted (and optionally except one)."""

    event_name: typing.ClassVar[str] = 'session_delete_all'

    current_user_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The connected user's ID."""

    exclude_session_id: str | None = field(repr=True, kw_only=True)
    """Optional[:class:`str`]: The session's ID that is excluded from deletion, if any."""


@define(slots=True)
class LogoutEvent(ShardEvent):
    """Dispatched when the connected user got logged out."""

    event_name: typing.ClassVar[str] = 'logout'


@define(slots=True)
class VoiceChannelJoinEvent(ShardEvent):
    """Dispatched when a user joins a voice channel."""

    event_name: typing.ClassVar[str] = 'voice_channel_join'

    channel_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The channel's ID the user joined to."""

    state: UserVoiceState = field(repr=True, kw_only=True)
    """:class:`.UserVoiceState`: The user's voice state."""

    def process(self) -> bool:
        state = self.shard.state
        cache = state.cache

        if not cache:
            return False

        ctx = (
            caching.VoiceChannelJoinEventCacheContext(
                type=caching.CacheContextType.voice_channel_join_event,
                event=self,
            )
            if 'VoiceChannelJoinEvent' in state.provide_cache_context_in
            else caching._VOICE_CHANNEL_JOIN_EVENT
        )

        cs = cache.get_channel_voice_state(self.channel_id, ctx)
        if cs is not None:
            cs.locally_add(self.state)
        else:
            cs = ChannelVoiceStateContainer(
                channel_id=self.channel_id,
                participants={self.state.user_id: self.state},
            )
        cache.store_channel_voice_state(cs, ctx)

        return True


@define(slots=True)
class VoiceChannelLeaveEvent(ShardEvent):
    """Dispatched when a user left voice channel."""

    event_name: typing.ClassVar[str] = 'voice_channel_leave'

    channel_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The channel's ID the user left from."""

    user_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The user's ID that left the voice channel."""

    container: ChannelVoiceStateContainer | None = field(repr=True, kw_only=True)
    """Optional[:class:`.ChannelVoiceStateContainer`]: The channel's voice state container."""

    state: UserVoiceState | None = field(repr=True, kw_only=True)
    """Optional[:class:`.UserVoiceState`]: The user's voice state."""

    cache_context: caching.UndefinedCacheContext | caching.VoiceChannelLeaveEventCacheContext = field(
        default=Factory(
            lambda self: _cast(
                'typing.Any',
                caching.VoiceChannelLeaveEventCacheContext(
                    type=caching.CacheContextType.voice_channel_leave_event,
                    event=self,
                )
                if 'VoiceChannelLeaveEvent' in self.shard.state.provide_cache_context_in
                else caching._VOICE_CHANNEL_LEAVE_EVENT,
            ),
            takes_self=True,
        ),
        repr=False,
        hash=False,
        init=False,
        eq=False,
    )
    """Union[:class:`.UndefinedCacheContext`, :class:`.VoiceChannelLeaveEventCacheContext`]: The cache context used."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache
        if not cache:
            return
        self.container = cache.get_channel_voice_state(self.channel_id, self.cache_context)

        if self.container is None:
            return
        self.state = self.container.participants.get(self.user_id)

    def process(self) -> bool:
        cache = self.shard.state.cache
        if not cache or not self.container:
            return False

        container = self.container
        container.locally_remove(self.user_id)
        cache.store_channel_voice_state(container, self.cache_context)

        return True


@define(slots=True)
class UserVoiceStateUpdateEvent(ShardEvent):
    """Dispatched when a user's voice state is updated."""

    event_name: typing.ClassVar[str] = 'user_voice_state_update'

    channel_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The channel's ID the user's voice state is in."""

    container: ChannelVoiceStateContainer | None = field(repr=True, kw_only=True)
    """Optional[:class:`.ChannelVoiceStateContainer`]: The channel's voice state container."""

    state: PartialUserVoiceState = field(repr=True, kw_only=True)
    """:class:`.PartialUserVoiceState`: The fields that were updated."""

    before: UserVoiceState | None = field(repr=True, kw_only=True)
    """Optional[:class:`.UserVoiceState`]: The user's voice state as it was before being updated, if available."""

    after: UserVoiceState | None = field(repr=True, kw_only=True)
    """Optional[:class:`.UserVoiceState`]: The user's voice state as it was updated, if available."""

    cache_context: caching.UndefinedCacheContext | caching.UserVoiceStateUpdateEventCacheContext = field(
        default=Factory(
            lambda self: _cast(
                'typing.Any',
                caching.UserVoiceStateUpdateEventCacheContext(
                    type=caching.CacheContextType.user_voice_state_update_event,
                    event=self,
                )
                if 'UserVoiceStateUpdateEvent' in self.shard.state.provide_cache_context_in
                else caching._USER_VOICE_STATE_UPDATE_EVENT,
            ),
            takes_self=True,
        ),
        repr=False,
        hash=False,
        init=False,
        eq=False,
    )
    """Union[:class:`.UndefinedCacheContext`, :class:`.UserVoiceStateUpdateEventCacheContext`]: The cache context used."""

    def before_dispatch(self) -> None:
        cache = self.shard.state.cache

        if not cache:
            return

        container = cache.get_channel_voice_state(self.channel_id, self.cache_context)
        if not container:
            return

        self.container = container

        before = container.participants.get(self.state.user_id)
        self.before = before

        if before:
            after = copy(before)
            after.locally_update(self.state)
            self.after = after

    def process(self) -> bool:
        cache = self.shard.state.cache

        if not cache or not self.container:
            return False

        cache.store_channel_voice_state(self.container, self.cache_context)
        return True


@define(slots=True)
class AuthenticatedEvent(ShardEvent):
    """Dispatched when the WebSocket was successfully authenticated."""

    event_name: typing.ClassVar[str] = 'authenticated'


@define(slots=True)
class BeforeConnectEvent(ShardEvent):
    """Dispatched before connection to Revolt WebSocket is made."""

    event_name: typing.ClassVar[str] = 'before_connect'


@define(slots=True)
class AfterConnectEvent(ShardEvent):
    """Dispatched after connection to Revolt WebSocket is made."""

    event_name: typing.ClassVar[str] = 'after_connect'

    socket: aiohttp.ClientWebSocketResponse = field(repr=True, kw_only=True)
    """:class:`aiohttp.ClientWebSocketResponse`: The connected WebSocket."""


__all__ = (
    'BaseEvent',
    'ShardEvent',
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
    'MessageDeleteBulkEvent',
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
    'ReportCreateEvent',
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
