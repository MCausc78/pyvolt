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

import abc
from attrs import define, field
import logging
import typing

from .emoji import ServerEmoji, Emoji
from .enums import Enum
from .user import User

if typing.TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from .channel import DMChannel, GroupChannel, Channel
    from .message import Message
    from .read_state import ReadState
    from .server import Server, Member

_L = logging.getLogger(__name__)


class ContextType(Enum):
    UNDEFINED = 'UNDEFINED'
    """Context is not provided."""

    USER_REQUEST = 'USER_REQUEST'
    """The end user is asking for object."""

    LIBRARY_REQUEST = 'LIBRARY_REQUEST'
    """Library needs the object for internal purposes."""

    READY = 'READY'
    """Populated data from Ready event."""

    message_ack = 'MESSAGE_ACK'
    message_create = 'MESSAGE_CREATE'
    message_update = 'MESSAGE_UPDATE'
    message_append = 'MESSAGE_APPEND'
    message_delete = 'MESSAGE_DELETE'
    message_react = 'MESSAGE_REACT'
    message_unreact = 'MESSAGE_UNREACT'
    message_remove_reaction = 'MESSAGE_REMOVE_REACTION'
    message_bulk_delete = 'MESSAGE_BULK_DELETE'

    server_create = 'SERVER_CREATE'
    server_update = 'SERVER_UPDATE'
    server_delete = 'SERVER_DELETE'

    server_member_create = 'SERVER_MEMBER_CREATE'
    server_member_update = 'SERVER_MEMBER_UPDATE'
    server_member_delete = 'SERVER_MEMBER_DELETE'

    server_role_update = 'SERVER_ROLE_UPDATE'
    server_role_delete = 'SERVER_ROLE_DELETE'

    user_update = 'USER_UPDATE'
    user_relationship_update = 'USER_RELATIONSHIP_UPDATE'
    user_platform_wipe = 'USER_PLATFORM_WIPE'

    emoji_create = 'EMOJI_CREATE'
    emoji_delete = 'EMOJI_DELETE'

    channel_create = 'CHANNEL_CREATE'
    channel_update = 'CHANNEL_UPDATE'
    channel_delete = 'CHANNEL_DELETE'

    channel_group_join = 'CHANNEL_GROUP_JOIN'
    channel_group_leave = 'CHANNEL_GROUP_LEAVE'
    """Data from websocket event."""

    message = 'MESSAGE'
    """The library asks for object to provide value for `message.get_x()`."""


@define(slots=True)
class BaseContext:
    type: ContextType = field(repr=True, hash=True, kw_only=True, eq=True)


@define(slots=True)
class MessageContext(BaseContext):
    message: Message = field(repr=True, hash=True, kw_only=True, eq=True)


_UNDEFINED = BaseContext(type=ContextType.UNDEFINED)
_USER_REQUEST = BaseContext(type=ContextType.USER_REQUEST)
_READY = BaseContext(type=ContextType.READY)
_MESSAGE_ACK = BaseContext(type=ContextType.message_ack)
_MESSAGE_CREATE = BaseContext(type=ContextType.message_create)
_MESSAGE_UPDATE = BaseContext(type=ContextType.message_update)
_MESSAGE_APPEND = BaseContext(type=ContextType.message_append)
_MESSAGE_DELETE = BaseContext(type=ContextType.message_delete)
_MESSAGE_REACT = BaseContext(type=ContextType.message_react)
_MESSAGE_UNREACT = BaseContext(type=ContextType.message_unreact)
_MESSAGE_REMOVE_REACTION = BaseContext(type=ContextType.message_remove_reaction)
_MESSAGE_BULK_DELETE = BaseContext(type=ContextType.message_bulk_delete)
_SERVER_CREATE = BaseContext(type=ContextType.server_create)
_SERVER_UPDATE = BaseContext(type=ContextType.server_update)
_SERVER_DELETE = BaseContext(type=ContextType.server_delete)
_SERVER_MEMBER_CREATE = BaseContext(type=ContextType.server_member_create)
_SERVER_MEMBER_UPDATE = BaseContext(type=ContextType.server_member_update)
_SERVER_MEMBER_DELETE = BaseContext(type=ContextType.server_member_delete)
_SERVER_ROLE_UPDATE = BaseContext(type=ContextType.server_role_update)
_SERVER_ROLE_DELETE = BaseContext(type=ContextType.server_role_delete)
_USER_UPDATE = BaseContext(type=ContextType.user_update)
_USER_RELATIONSHIP_UPDATE = BaseContext(type=ContextType.user_relationship_update)
_USER_PLATFORM_WIPE = BaseContext(type=ContextType.user_platform_wipe)
_EMOJI_CREATE = BaseContext(type=ContextType.emoji_create)
_EMOJI_DELETE = BaseContext(type=ContextType.emoji_delete)
_CHANNEL_CREATE = BaseContext(type=ContextType.channel_create)
_CHANNEL_UPDATE = BaseContext(type=ContextType.channel_update)
_CHANNEL_DELETE = BaseContext(type=ContextType.channel_delete)
_CHANNEL_GROUP_JOIN = BaseContext(type=ContextType.channel_group_join)
_CHANNEL_GROUP_LEAVE = BaseContext(type=ContextType.channel_group_leave)


ProvideCacheContextIn = typing.Literal[
    'DMChannel.recipients',
    'DMChannel.get_initiator',
    'DMChannel.get_target',
    'GroupChannel.get_owner',
    'GroupChannel.last_message',
    'GroupChannel.recipients',
    'BaseServerChannel.get_server',
    'ServerEmoji.get_server',
    # TODO: events
    'BaseMessage.channel',
    'UserAddedSystemEvent.get_user',
    'UserAddedSystemEvent.get_by',
    'UserRemovedSystemEvent.get_user',
    'UserRemovedSystemEvent.get_by',
    'UserJoinedSystemEvent.get_user',
    'UserLeftSystemEvent.get_user',
    'UserKickedSystemEvent.get_user',
    'UserBannedSystemEvent.get_user',
    'ChannelRenamedSystemEvent.get_by',
    'ChannelDescriptionChangedSystemEvent.get_by',
    'ChannelIconChangedSystemEvent.get_by',
    'ChannelOwnershipChangedSystemEvent.get_from',
    'ChannelOwnershipChangedSystemEvent.get_to',
    'MessagePinnedSystemEvent.get_by',
    'MessageUnpinnedSystemEvent.get_by',
    'Message.get_author',
    'ReadState.get_channel',
    'BaseRole.get_server',
    'Server.get_owner',
    'BaseMember.get_server',
    'BaseUser.dm_channel_id',
    'BaseUser.dm_channel',
    'Webhook.channel',
]


class Cache(abc.ABC):
    ############
    # Channels #
    ############

    @abc.abstractmethod
    def get_channel(self, channel_id: str, ctx: BaseContext, /) -> Channel | None: ...

    def get_all_channels(self, ctx: BaseContext, /) -> Sequence[Channel]:
        return list(self.get_channels_mapping().values())

    @abc.abstractmethod
    def get_channels_mapping(self) -> Mapping[str, Channel]: ...

    @abc.abstractmethod
    def store_channel(self, channel: Channel, ctx: BaseContext, /) -> None: ...

    @abc.abstractmethod
    def delete_channel(self, channel_id: str, ctx: BaseContext, /) -> None: ...

    @abc.abstractmethod
    def get_private_channels_mapping(self) -> Mapping[str, DMChannel | GroupChannel]: ...

    ####################
    # Channel Messages #
    ####################
    @abc.abstractmethod
    def get_message(self, channel_id: str, message_id: str, ctx: BaseContext, /) -> Message | None: ...

    def get_all_messages_of(self, channel_id: str, ctx: BaseContext, /) -> Sequence[Message] | None:
        ms = self.get_messages_mapping_of(channel_id, ctx)
        if ms is None:
            return None
        return list(ms.values())

    @abc.abstractmethod
    def get_messages_mapping_of(self, channel_id: str, ctx: BaseContext, /) -> Mapping[str, Message] | None: ...

    @abc.abstractmethod
    def store_message(self, message: Message, ctx: BaseContext, /) -> None: ...

    @abc.abstractmethod
    def delete_message(self, channel_id: str, message_id: str, ctx: BaseContext, /) -> None: ...

    @abc.abstractmethod
    def delete_messages_of(self, channel_id: str, ctx: BaseContext, /) -> None: ...

    ###############
    # Read States #
    ###############
    @abc.abstractmethod
    def get_read_state(self, channel_id: str, ctx: BaseContext, /) -> ReadState | None: ...

    def get_all_read_states(self, ctx: BaseContext, /) -> Sequence[ReadState]:
        return list(self.get_read_states_mapping().values())

    @abc.abstractmethod
    def get_read_states_mapping(self) -> Mapping[str, ReadState]: ...

    @abc.abstractmethod
    def store_read_state(self, read_state: ReadState, ctx: BaseContext, /) -> None: ...

    @abc.abstractmethod
    def delete_read_state(self, channel_id: str, ctx: BaseContext, /) -> None: ...

    ##########
    # Emojis #
    ##########

    @abc.abstractmethod
    def get_emoji(self, emoji_id: str, ctx: BaseContext, /) -> Emoji | None: ...

    def get_all_emojis(self, ctx: BaseContext, /) -> Sequence[Emoji]:
        return list(self.get_emojis_mapping().values())

    @abc.abstractmethod
    def get_emojis_mapping(self) -> Mapping[str, Emoji]: ...

    @abc.abstractmethod
    def get_server_emojis_mapping(
        self,
    ) -> Mapping[str, Mapping[str, ServerEmoji]]: ...

    @abc.abstractmethod
    def get_server_emojis_mapping_of(self, server_id: str, ctx: BaseContext, /) -> Mapping[str, ServerEmoji] | None: ...

    @abc.abstractmethod
    def delete_server_emojis_of(self, server_id: str, ctx: BaseContext, /) -> None: ...

    @abc.abstractmethod
    def store_emoji(self, emoji: Emoji, ctx: BaseContext, /) -> None: ...

    @abc.abstractmethod
    def delete_emoji(self, emoji_id: str, server_id: str | None, ctx: BaseContext, /) -> None: ...

    ###########
    # Servers #
    ###########

    @abc.abstractmethod
    def get_server(self, server_id: str, ctx: BaseContext, /) -> Server | None: ...

    def get_all_servers(self, ctx: BaseContext, /) -> Sequence[Server]:
        return list(self.get_servers_mapping().values())

    @abc.abstractmethod
    def get_servers_mapping(self) -> Mapping[str, Server]: ...

    @abc.abstractmethod
    def store_server(self, server: Server, ctx: BaseContext, /) -> None: ...

    @abc.abstractmethod
    def delete_server(self, server_id: str, ctx: BaseContext, /) -> None: ...

    ##################
    # Server Members #
    ##################
    @abc.abstractmethod
    def get_server_member(self, server_id: str, user_id: str, ctx: BaseContext, /) -> Member | None: ...

    def get_all_server_members_of(self, server_id: str, ctx: BaseContext, /) -> Sequence[Member] | None:
        ms = self.get_server_members_mapping_of(server_id, ctx)
        if ms is None:
            return None
        return list(ms.values())

    @abc.abstractmethod
    def get_server_members_mapping_of(self, server_id: str, ctx: BaseContext, /) -> Mapping[str, Member] | None: ...

    @abc.abstractmethod
    def bulk_store_server_members(
        self,
        server_id: str,
        members: dict[str, Member],
        ctx: BaseContext,
        /,
    ) -> None: ...

    @abc.abstractmethod
    def overwrite_server_members(
        self,
        server_id: str,
        members: dict[str, Member],
        ctx: BaseContext,
        /,
    ) -> None: ...

    @abc.abstractmethod
    def store_server_member(self, member: Member, ctx: BaseContext, /) -> None: ...

    @abc.abstractmethod
    def delete_server_member(self, server_id: str, user_id: str, ctx: BaseContext, /) -> None: ...

    @abc.abstractmethod
    def delete_server_members_of(self, server_id: str, ctx: BaseContext, /) -> None: ...

    #########
    # Users #
    #########

    @abc.abstractmethod
    def get_user(self, user_id: str, ctx: BaseContext, /) -> User | None: ...

    def get_all_users(self, ctx: BaseContext, /) -> Sequence[User]:
        return list(self.get_users_mapping().values())

    @abc.abstractmethod
    def get_users_mapping(self) -> Mapping[str, User]: ...

    @abc.abstractmethod
    def store_user(self, user: User, ctx: BaseContext, /) -> None: ...

    @abc.abstractmethod
    def bulk_store_users(self, users: dict[str, User], ctx: BaseContext, /) -> None: ...

    ############################
    # Private Channels by User #
    ############################
    @abc.abstractmethod
    def get_private_channel_by_user(self, user_id: str, ctx: BaseContext, /) -> str | None: ...

    def get_all_private_channels_by_users(self, ctx: BaseContext, /) -> Sequence[str]:
        return list(self.get_private_channels_by_users_mapping().values())

    @abc.abstractmethod
    def get_private_channels_by_users_mapping(self) -> Mapping[str, str]: ...

    @abc.abstractmethod
    def store_private_channel_by_user(self, channel: DMChannel, ctx: BaseContext, /) -> None: ...

    # Should be implemented in `delete_channel`, or in event
    @abc.abstractmethod
    def delete_private_channel_by_user(self, user_id: str, ctx: BaseContext, /) -> None: ...


class EmptyCache(Cache):
    ############
    # Channels #
    ############

    def get_channel(self, channel_id: str, ctx: BaseContext, /) -> Channel | None:
        return None

    def get_channels_mapping(self) -> dict[str, Channel]:
        return {}

    def store_channel(self, channel: Channel, ctx: BaseContext, /) -> None:
        pass

    def delete_channel(self, channel_id: str, ctx: BaseContext, /) -> None:
        pass

    def get_private_channels_mapping(self) -> dict[str, DMChannel | GroupChannel]:
        return {}

    ####################
    # Channel Messages #
    ####################
    def get_message(self, channel_id: str, message_id: str, ctx: BaseContext, /) -> Message | None:
        return None

    def get_messages_mapping_of(self, channel_id: str, ctx: BaseContext, /) -> Mapping[str, Message] | None:
        return None

    def store_message(self, message: Message, ctx: BaseContext, /) -> None:
        pass

    def delete_message(self, channel_id: str, message_id: str, ctx: BaseContext, /) -> None:
        pass

    def delete_messages_of(self, channel_id: str, ctx: BaseContext, /) -> None:
        pass

    ###############
    # Read States #
    ###############
    def get_read_state(self, channel_id: str, ctx: BaseContext, /) -> ReadState | None:
        return None

    def get_read_states_mapping(self) -> dict[str, ReadState]:
        return {}

    def store_read_state(self, read_state: ReadState, ctx: BaseContext, /) -> None:
        pass

    def delete_read_state(self, channel_id: str, ctx: BaseContext, /) -> None:
        pass

    ##########
    # Emojis #
    ##########

    def get_emoji(self, emoji_id: str, ctx: BaseContext, /) -> Emoji | None:
        return None

    def get_emojis_mapping(self) -> dict[str, Emoji]:
        return {}

    def get_server_emojis_mapping(
        self,
    ) -> dict[str, dict[str, ServerEmoji]]:
        return {}

    def get_server_emojis_mapping_of(self, server_id: str, ctx: BaseContext, /) -> dict[str, ServerEmoji] | None:
        return None

    def delete_server_emojis_of(self, server_id: str, ctx: BaseContext, /) -> None:
        pass

    def store_emoji(self, emoji: Emoji, ctx: BaseContext, /) -> None:
        pass

    def delete_emoji(self, emoji_id: str, server_id: str | None, ctx: BaseContext, /) -> None:
        pass

    ###########
    # Servers #
    ###########

    def get_server(self, server_id: str, ctx: BaseContext, /) -> Server | None:
        return None

    def get_servers_mapping(self) -> dict[str, Server]:
        return {}

    def store_server(self, server: Server, ctx: BaseContext, /) -> None:
        pass

    def delete_server(self, server_id: str, ctx: BaseContext, /) -> None:
        pass

    ##################
    # Server Members #
    ##################
    def get_server_member(self, server_id: str, user_id: str, ctx: BaseContext, /) -> Member | None:
        return None

    def get_server_members_mapping_of(self, server_id: str, ctx: BaseContext, /) -> dict[str, Member] | None:
        return None

    def bulk_store_server_members(
        self,
        server_id: str,
        members: dict[str, Member],
        ctx: BaseContext,
        /,
    ) -> None:
        pass

    def overwrite_server_members(
        self,
        server_id: str,
        members: dict[str, Member],
        ctx: BaseContext,
        /,
    ) -> None:
        pass

    def store_server_member(self, member: Member, ctx: BaseContext, /) -> None:
        pass

    def delete_server_member(self, server_id: str, user_id: str, ctx: BaseContext, /) -> None:
        pass

    def delete_server_members_of(self, server_id: str, ctx: BaseContext, /) -> None:
        pass

    #########
    # Users #
    #########

    def get_user(self, user_id: str, ctx: BaseContext, /) -> User | None:
        return None

    def get_users_mapping(self) -> dict[str, User]:
        return {}

    def store_user(self, user: User, ctx: BaseContext, /) -> None:
        return None

    def bulk_store_users(self, users: dict[str, User], ctx: BaseContext, /) -> None:
        pass

    ############################
    # Private Channels by User #
    ############################
    def get_private_channel_by_user(self, user_id: str, ctx: BaseContext, /) -> str | None:
        return None

    def get_private_channels_by_users_mapping(self) -> dict[str, str]:
        return {}

    def store_private_channel_by_user(self, channel: DMChannel, ctx: BaseContext, /) -> None:
        pass

    def delete_private_channel_by_user(self, user_id: str, ctx: BaseContext, /) -> None:
        pass


V = typing.TypeVar('V')


def _put0(d: dict[str, V], k: str, max_size: int, required_keys: int = 1) -> bool:  # noqa: ARG001
    if max_size == 0:
        return False
    map_size = len(d)
    if map_size != 0 and max_size > 0 and len(d) >= max_size:
        keys = []
        i = 0
        for key in d.keys():
            keys.append(key)
            if i >= required_keys:
                break
            i += 1
        for key in keys:
            del d[key]
    return True


def _put1(d: dict[str, V], k: str, v: V, max_size: int) -> None:
    if _put0(d, k, max_size):
        d[k] = v


class MapCache(Cache):
    __slots__ = (
        '_channels',
        '_channels_max_size',
        '_emojis',
        '_emojis_max_size',
        '_private_channels',
        '_private_channels_by_user',
        '_private_channels_by_user_max_size',
        '_private_channels_max_size',
        '_messages',
        '_messages_max_size',
        '_read_states',
        '_read_states_max_size',
        '_servers',
        '_servers_max_size',
        '_server_emojis',
        '_server_emojis_max_size',
        '_server_members',
        '_server_members_max_size',
        '_users',
        '_users_max_size',
    )

    def __init__(
        self,
        *,
        channels_max_size: int = -1,
        emojis_max_size: int = -1,
        messages_max_size: int = 1000,
        private_channels_by_user_max_size: int = -1,
        private_channels_max_size: int = -1,
        read_states_max_size: int = -1,
        server_emojis_max_size: int = -1,
        server_members_max_size: int = -1,
        servers_max_size: int = -1,
        users_max_size: int = -1,
    ) -> None:
        self._channels: dict[str, Channel] = {}
        self._channels_max_size: int = channels_max_size
        self._emojis: dict[str, Emoji] = {}
        self._emojis_max_size: int = emojis_max_size
        self._private_channels: dict[str, DMChannel | GroupChannel] = {}
        self._private_channels_by_user: dict[str, str] = {}
        self._private_channels_by_user_max_size: int = private_channels_by_user_max_size
        self._private_channels_max_size: int = private_channels_max_size
        self._messages: dict[str, dict[str, Message]] = {}
        self._messages_max_size = messages_max_size
        self._read_states: dict[str, ReadState] = {}
        self._read_states_max_size: int = read_states_max_size
        self._servers: dict[str, Server] = {}
        self._servers_max_size: int = servers_max_size
        self._server_emojis: dict[str, dict[str, ServerEmoji]] = {}
        self._server_emojis_max_size: int = server_emojis_max_size
        self._server_members: dict[str, dict[str, Member]] = {}
        self._server_members_max_size: int = server_members_max_size
        self._users: dict[str, User] = {}
        self._users_max_size: int = users_max_size

    ############
    # Channels #
    ############

    def get_channel(self, channel_id: str, ctx: BaseContext, /) -> Channel | None:
        return self._channels.get(channel_id)

    def get_channels_mapping(self) -> Mapping[str, Channel]:
        return self._channels

    def store_channel(self, channel: Channel, ctx: BaseContext, /) -> None:
        _put1(self._channels, channel.id, channel, self._channels_max_size)

        from .channel import DMChannel, GroupChannel

        if isinstance(channel, (DMChannel, GroupChannel)):
            _put1(self._private_channels, channel.id, channel, self._private_channels_max_size)

    def delete_channel(self, channel_id: str, ctx: BaseContext, /) -> None:
        self._channels.pop(channel_id, None)

    def get_private_channels_mapping(self) -> Mapping[str, DMChannel | GroupChannel]:
        return self._private_channels

    ####################
    # Channel Messages #
    ####################
    def get_message(self, channel_id: str, message_id: str, ctx: BaseContext, /) -> Message | None:
        messages = self._messages.get(channel_id)
        if messages:
            return messages.get(message_id)
        return None

    def get_messages_mapping_of(self, channel_id: str, ctx: BaseContext, /) -> Mapping[str, Message] | None:
        return self._messages.get(channel_id)

    def store_message(self, message: Message, ctx: BaseContext, /) -> None:
        from .server import Member

        author = message._author
        if isinstance(author, Member):
            self.store_server_member(author, ctx)
            message._author = author.id
        elif isinstance(author, User):
            self.store_user(author, ctx)
            message._author = author.id

        d = self._messages.get(message.channel_id)
        if d is None:
            if self._messages_max_size == 0:
                return
            self._messages[message.channel_id] = {message.id: message}
        else:
            _put1(d, message.id, message, self._messages_max_size)

    def delete_message(self, channel_id: str, message_id: str, ctx: BaseContext, /) -> None:
        messages = self._messages.get(channel_id)
        if messages:
            messages.pop(message_id, None)

    def delete_messages_of(self, channel_id: str, ctx: BaseContext, /) -> None:
        self._messages.pop(channel_id, None)

    ###############
    # Read States #
    ###############
    def get_read_state(self, channel_id: str, ctx: BaseContext, /) -> ReadState | None:
        return self._read_states.get(channel_id)

    def get_read_states_mapping(self) -> Mapping[str, ReadState]:
        return self._read_states

    def store_read_state(self, read_state: ReadState, ctx: BaseContext, /) -> None:
        _put1(
            self._read_states,
            read_state.channel_id,
            read_state,
            self._read_states_max_size,
        )

    def delete_read_state(self, channel_id: str, ctx: BaseContext, /) -> None:
        self._read_states.pop(channel_id, None)

    ##########
    # Emojis #
    ##########

    def get_emoji(self, emoji_id: str, ctx: BaseContext, /) -> Emoji | None:
        return self._emojis.get(emoji_id)

    def get_emojis_mapping(self) -> Mapping[str, Emoji]:
        return self._emojis

    def get_server_emojis_mapping(
        self,
    ) -> Mapping[str, Mapping[str, ServerEmoji]]:
        return self._server_emojis

    def get_server_emojis_mapping_of(self, server_id: str, ctx: BaseContext, /) -> Mapping[str, ServerEmoji] | None:
        return self._server_emojis.get(server_id)

    def delete_server_emojis_of(self, server_id: str, ctx: BaseContext, /) -> None:
        self._server_emojis.pop(server_id, None)

    def store_emoji(self, emoji: Emoji, ctx: BaseContext, /) -> None:
        if isinstance(emoji, ServerEmoji):
            server_id = emoji.server_id
            if _put0(self._server_emojis, server_id, self._server_emojis_max_size):
                se = self._server_emojis
                s = se.get(server_id)
                if s is not None:
                    s[emoji.id] = emoji
                else:
                    se[server_id] = {emoji.id: emoji}
        _put1(self._emojis, emoji.id, emoji, self._emojis_max_size)

    def delete_emoji(self, emoji_id: str, server_id: str | None, ctx: BaseContext, /) -> None:
        emoji = self._emojis.pop(emoji_id, None)

        server_ids: tuple[str, ...] = ()
        if isinstance(emoji, ServerEmoji):
            if server_id:
                server_ids = (server_id, emoji.server_id)
            else:
                server_ids = (emoji.server_id,)

        for server_id in server_ids:
            server_emojis = self._server_emojis.get(server_id, {})
            server_emojis.pop(emoji_id, None)

    ###########
    # Servers #
    ###########

    def get_server(self, server_id: str, ctx: BaseContext, /) -> Server | None:
        return self._servers.get(server_id)

    def get_servers_mapping(self) -> Mapping[str, Server]:
        return self._servers

    def store_server(self, server: Server, ctx: BaseContext, /) -> None:
        if server.id not in self._server_emojis:
            _put1(self._server_emojis, server.id, {}, self._server_emojis_max_size)

        if (
            _put0(self._server_members, server.id, self._server_members_max_size)
            and server.id not in self._server_members
        ):
            self._server_members[server.id] = {}
        _put1(self._servers, server.id, server, self._servers_max_size)

    def delete_server(self, server_id: str, ctx: BaseContext, /) -> None:
        self._servers.pop(server_id, None)

    ##################
    # Server Members #
    ##################
    def get_server_member(self, server_id: str, user_id: str, ctx: BaseContext, /) -> Member | None:
        d = self._server_members.get(server_id)
        if d is None:
            return None
        return d.get(user_id)

    def get_server_members_mapping_of(self, server_id: str, ctx: BaseContext, /) -> Mapping[str, Member] | None:
        return self._server_members.get(server_id)

    def bulk_store_server_members(
        self,
        server_id: str,
        members: dict[str, Member],
        ctx: BaseContext,
        /,
    ) -> None:
        d = self._server_members.get(server_id)
        if d is None:
            self._server_members[server_id] = members
        else:
            d.update(members)

    def overwrite_server_members(
        self,
        server_id: str,
        members: dict[str, Member],
        ctx: BaseContext,
        /,
    ) -> None:
        self._server_members[server_id] = members

    def store_server_member(self, member: Member, ctx: BaseContext, /) -> None:
        if isinstance(member._user, User):
            self.store_user(member._user, ctx)
            member._user = member._user.id
        d = self._server_members.get(member.server_id)
        if d is None:
            if self._server_members_max_size == 0:
                return
            self._server_members[member.server_id] = {member.id: member}
        else:
            _put1(d, member.id, member, self._server_members_max_size)

    def delete_server_member(self, server_id: str, user_id: str, ctx: BaseContext, /) -> None:
        members = self._server_members.get(server_id)
        if members:
            members.pop(user_id, None)

    def delete_server_members_of(self, server_id: str, ctx: BaseContext, /) -> None:
        self._server_members.pop(server_id, None)

    #########
    # Users #
    #########

    def get_user(self, user_id: str, ctx: BaseContext, /) -> User | None:
        return self._users.get(user_id)

    def get_users_mapping(self) -> Mapping[str, User]:
        return self._users

    def store_user(self, user: User, ctx: BaseContext, /) -> None:
        _put1(self._users, user.id, user, self._users_max_size)

    def bulk_store_users(self, users: Mapping[str, User], ctx: BaseContext, /) -> None:
        self._users.update(users)

    ############################
    # Private Channels by User #
    ############################
    def get_private_channel_by_user(self, user_id: str, ctx: BaseContext, /) -> str | None:
        return self._private_channels_by_user.get(user_id)

    def get_private_channels_by_users_mapping(self) -> Mapping[str, str]:
        return self._private_channels_by_user

    def store_private_channel_by_user(self, channel: DMChannel, ctx: BaseContext, /) -> None:
        _put1(self._private_channels_by_user, channel.recipient_id, channel.id, self._private_channels_by_user_max_size)

    def delete_private_channel_by_user(self, user_id: str, ctx: BaseContext, /) -> None:
        self._private_channels_by_user.pop(user_id, None)


# re-export internal functions as well for future usage
__all__ = (
    'ContextType',
    'BaseContext',
    'MessageContext',
    '_UNDEFINED',
    '_USER_REQUEST',
    '_READY',
    '_MESSAGE_ACK',
    '_MESSAGE_CREATE',
    '_MESSAGE_UPDATE',
    '_MESSAGE_APPEND',
    '_MESSAGE_DELETE',
    '_MESSAGE_REACT',
    '_MESSAGE_UNREACT',
    '_MESSAGE_REMOVE_REACTION',
    '_MESSAGE_BULK_DELETE',
    '_SERVER_CREATE',
    '_SERVER_UPDATE',
    '_SERVER_DELETE',
    '_SERVER_MEMBER_CREATE',
    '_SERVER_MEMBER_UPDATE',
    '_SERVER_MEMBER_DELETE',
    '_SERVER_ROLE_UPDATE',
    '_SERVER_ROLE_DELETE',
    '_USER_UPDATE',
    '_USER_RELATIONSHIP_UPDATE',
    '_USER_PLATFORM_WIPE',
    '_EMOJI_CREATE',
    '_EMOJI_DELETE',
    '_CHANNEL_CREATE',
    '_CHANNEL_UPDATE',
    '_CHANNEL_DELETE',
    '_CHANNEL_GROUP_JOIN',
    '_CHANNEL_GROUP_LEAVE',
    'ProvideCacheContextIn',
    'Cache',
    'EmptyCache',
    '_put0',
    '_put1',
    'MapCache',
)
