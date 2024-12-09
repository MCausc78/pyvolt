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

from abc import ABC, abstractmethod
import logging
import typing

from attrs import define, field

from .emoji import DetachedEmoji, ServerEmoji, Emoji
from .enums import Enum
from .user import User

if typing.TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from .channel import DMChannel, GroupChannel, Channel, ChannelVoiceStateContainer
    from .message import Message
    from .read_state import ReadState
    from .server import Server, Member

_L = logging.getLogger(__name__)


class CacheContextType(Enum):
    undefined = 'UNDEFINED'
    """Context is not provided."""

    user_request = 'USER_REQUEST'
    """The end user is asking for object."""

    library_request = 'LIBRARY_REQUEST'
    """Library needs the object for internal purposes."""

    ready = 'READY'
    message_ack = 'MESSAGE_ACK'
    message_create = 'MESSAGE_CREATE'
    message_update = 'MESSAGE_UPDATE'
    message_append = 'MESSAGE_APPEND'
    message_delete = 'MESSAGE_DELETE'
    message_react = 'MESSAGE_REACT'
    message_unreact = 'MESSAGE_UNREACT'
    message_clear_reaction = 'MESAGE_CLEAR_REACTION'
    message_delete_bulk = 'MESSAGE_DELETE_BULK'

    server_create = 'SERVER_CREATE'
    server_update = 'SERVER_UPDATE'
    server_delete = 'SERVER_DELETE'

    server_member_add = 'SERVER_MEMBER_ADD'
    server_member_update = 'SERVER_MEMBER_UPDATE'
    server_member_remove = 'SERVER_MEMBER_REMOVE'

    server_role_update = 'SERVER_ROLE_UPDATE'
    server_role_delete = 'SERVER_ROLE_DELETE'

    user_update = 'USER_UPDATE'
    user_relationship_update = 'USER_RELATIONSHIP_UPDATE'
    user_platform_wipe = 'USER_PLATFORM_WIPE'

    server_emoji_create = 'SERVER_EMOJI_CREATE'
    server_emoji_delete = 'SERVER_EMOJI_DELETE'

    channel_create = 'CHANNEL_CREATE'
    channel_update = 'CHANNEL_UPDATE'
    channel_delete = 'CHANNEL_DELETE'

    group_recipient_add = 'GROUP_RECIPIENT_ADD'
    group_recipient_remove = 'GROUP_RECIPIENT_REMOVE'

    voice_channel_join = 'VOICE_CHANNEL_JOIN'
    voice_channel_leave = 'VOICE_CHANNEL_LEAVE'
    user_voice_state_update = 'USER_VOICE_STATE_UPDATE'
    """Data from websocket event."""

    emoji = 'EMOJI'
    member = 'MEMBER'
    message = 'MESSAGE'
    role = 'ROLE'
    server = 'SERVER'
    user = 'USER'
    webhook = 'WEBHOOK'


@define(slots=True)
class BaseCacheContext:
    """Represents a cache context."""

    type: CacheContextType = field(repr=True, hash=True, kw_only=True, eq=True)
    """The context's type."""


@define(slots=True)
class DetachedEmojiCacheContext(BaseCacheContext):
    """Represents a cache context that involves a detached emoji."""

    emoji: DetachedEmoji = field(repr=True, hash=True, kw_only=True, eq=True)
    """The detached emoji involved."""


@define(slots=True)
class MessageCacheContext(BaseCacheContext):
    """Represents a cache context that involves a message."""

    message: Message = field(repr=True, hash=True, kw_only=True, eq=True)
    """The message involved."""


@define(slots=True)
class ServerCacheContext(BaseCacheContext):
    """Represents a cache context that involves a server."""

    server: Server = field(repr=True, hash=True, kw_only=True, eq=True)
    """The server involved."""


@define(slots=True)
class ServerEmojiCacheContext(BaseCacheContext):
    """Represents a cache context that involves a server emoji."""

    emoji: ServerEmoji = field(repr=True, hash=True, kw_only=True, eq=True)
    """The emoji involved."""


@define(slots=True)
class UserCacheContext(BaseCacheContext):
    """Represents a cache context that involves a user."""

    user: User = field(repr=True, hash=True, kw_only=True, eq=True)
    """The user involved."""


_UNDEFINED = BaseCacheContext(type=CacheContextType.undefined)
_USER_REQUEST = BaseCacheContext(type=CacheContextType.user_request)
_READY = BaseCacheContext(type=CacheContextType.ready)
_MESSAGE_ACK = BaseCacheContext(type=CacheContextType.message_ack)
_MESSAGE_CREATE = BaseCacheContext(type=CacheContextType.message_create)
_MESSAGE_UPDATE = BaseCacheContext(type=CacheContextType.message_update)
_MESSAGE_APPEND = BaseCacheContext(type=CacheContextType.message_append)
_MESSAGE_DELETE = BaseCacheContext(type=CacheContextType.message_delete)
_MESSAGE_REACT = BaseCacheContext(type=CacheContextType.message_react)
_MESSAGE_UNREACT = BaseCacheContext(type=CacheContextType.message_unreact)
_MESSAGE_CLEAR_REACTION = BaseCacheContext(type=CacheContextType.message_clear_reaction)
_MESSAGE_DELETE_BULK = BaseCacheContext(type=CacheContextType.message_delete_bulk)
_SERVER_CREATE = BaseCacheContext(type=CacheContextType.server_create)
_SERVER_UPDATE = BaseCacheContext(type=CacheContextType.server_update)
_SERVER_DELETE = BaseCacheContext(type=CacheContextType.server_delete)
_SERVER_MEMBER_ADD = BaseCacheContext(type=CacheContextType.server_member_add)
_SERVER_MEMBER_UPDATE = BaseCacheContext(type=CacheContextType.server_member_update)
_SERVER_MEMBER_REMOVE = BaseCacheContext(type=CacheContextType.server_member_remove)
_SERVER_ROLE_UPDATE = BaseCacheContext(type=CacheContextType.server_role_update)
_SERVER_ROLE_DELETE = BaseCacheContext(type=CacheContextType.server_role_delete)
_USER_UPDATE = BaseCacheContext(type=CacheContextType.user_update)
_USER_RELATIONSHIP_UPDATE = BaseCacheContext(type=CacheContextType.user_relationship_update)
_USER_PLATFORM_WIPE = BaseCacheContext(type=CacheContextType.user_platform_wipe)
_SERVER_EMOJI_CREATE = BaseCacheContext(type=CacheContextType.server_emoji_create)
_SERVER_EMOJI_DELETE = BaseCacheContext(type=CacheContextType.server_emoji_delete)
_CHANNEL_CREATE = BaseCacheContext(type=CacheContextType.channel_create)
_CHANNEL_UPDATE = BaseCacheContext(type=CacheContextType.channel_update)
_CHANNEL_DELETE = BaseCacheContext(type=CacheContextType.channel_delete)
_GROUP_RECIPIENT_ADD = BaseCacheContext(type=CacheContextType.group_recipient_add)
_GROUP_RECIPIENT_REMOVE = BaseCacheContext(type=CacheContextType.group_recipient_remove)
_VOICE_CHANNEL_JOIN = BaseCacheContext(type=CacheContextType.voice_channel_join)
_VOICE_CHANNEL_LEAVE = BaseCacheContext(type=CacheContextType.voice_channel_leave)
_USER_VOICE_STATE_UPDATE = BaseCacheContext(type=CacheContextType.user_voice_state_update)

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


class Cache(ABC):
    """An ABC that represents cache.

    .. note::
        This class might not be what you're looking for.
        Head over to :class:`.EmptyCache` and :class:`.MapCache` for implementations.
    """

    __slots__ = ()

    ############
    # Channels #
    ############

    @abstractmethod
    def get_channel(self, channel_id: str, ctx: BaseCacheContext, /) -> Channel | None:
        """Optional[:class:`.Channel`]: Retrieves a channel using ID.

        Parameters
        ----------
        channel_id: :class:`str`
            The channel's ID.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    def get_all_channels(self, ctx: BaseCacheContext, /) -> Sequence[Channel]:
        """Sequence[:class:`.Channel`]: Retrieves all available channels as sequence.

        Parameters
        ----------
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        return list(self.get_channels_mapping().values())

    @abstractmethod
    def get_channels_mapping(self) -> Mapping[str, Channel]:
        """Mapping[:class:`str`, :class:`.Channel`]: Retrieves all available channels as mapping."""
        ...

    @abstractmethod
    def store_channel(self, channel: Channel, ctx: BaseCacheContext, /) -> None:
        """Stores a channel.

        Parameters
        ----------
        channel: :class:`.Channel`
            The channel to store.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    @abstractmethod
    def delete_channel(self, channel_id: str, ctx: BaseCacheContext, /) -> None:
        """Deletes a channel.

        Parameters
        ----------
        channel_id: :class:`str`
            The channel's ID.
        ctx: :class:`.BaseCacheContext`
            The context.
        """

        ...

    @abstractmethod
    def get_private_channels_mapping(self) -> Mapping[str, DMChannel | GroupChannel]:
        """Mapping[:class:`str`, Union[:class:`.DMChannel`, :class:`.GroupChannel`]]: Retrieve all private channels as mapping."""
        ...

    ####################
    # Channel Messages #
    ####################
    @abstractmethod
    def get_message(self, channel_id: str, message_id: str, ctx: BaseCacheContext, /) -> Message | None:
        """Optional[:class:`.Message`]: Retrieves a message in channel using channel and message IDs.

        Parameters
        ----------
        channel_id: :class:`str`
            The channel's ID.
        message_id: :class:`str`
            The message's ID.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    def get_all_messages_of(self, channel_id: str, ctx: BaseCacheContext, /) -> Sequence[Message] | None:
        """Optional[Sequence[:class:`.Message`]]: Retrieves all messages from a channel.

        Parameters
        ----------
        channel_id: :class:`str`
            The channel's ID.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ms = self.get_messages_mapping_of(channel_id, ctx)
        if ms is None:
            return None
        return list(ms.values())

    @abstractmethod
    def get_messages_mapping_of(self, channel_id: str, ctx: BaseCacheContext, /) -> Mapping[str, Message] | None:
        """Optional[Mapping[:class:`str`, :class:`.Message`]]: Retrieves all messages from a channel as mapping.

        Parameters
        ----------
        channel_id: :class:`str`
            The channel's ID.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    @abstractmethod
    def store_message(self, message: Message, ctx: BaseCacheContext, /) -> None:
        """Stores a message.

        Parameters
        ----------
        message: :class:`.Message`
            The message to store.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    @abstractmethod
    def delete_message(self, channel_id: str, message_id: str, ctx: BaseCacheContext, /) -> None:
        """Deletes a message from channel.

        Parameters
        ----------
        channel_id: :class:`str`
            The channel's ID.
        message_id: :class:`str`
            The message's ID.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    @abstractmethod
    def delete_messages_of(self, channel_id: str, ctx: BaseCacheContext, /) -> None:
        """Deletes all messages from a channel.

        Parameters
        ----------
        channel_id: :class:`str`
            The channel's ID.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    ###############
    # Read States #
    ###############
    @abstractmethod
    def get_read_state(self, channel_id: str, ctx: BaseCacheContext, /) -> ReadState | None:
        """Optional[:class:`.ReadState`]: Retrieves a read state using ID.

        Parameters
        ----------
        channel_id: :class:`str`
            The channel's ID.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    def get_all_read_states(self, ctx: BaseCacheContext, /) -> Sequence[ReadState]:
        """Sequence[:class:`.ReadState`]: Retrieves all available read states as sequence.

        Parameters
        ----------
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        return list(self.get_read_states_mapping().values())

    @abstractmethod
    def get_read_states_mapping(self) -> Mapping[str, ReadState]:
        """Mapping[:class:`str`, :class:`.ReadState`]: Retrieves all available read states as mapping."""
        ...

    @abstractmethod
    def store_read_state(self, read_state: ReadState, ctx: BaseCacheContext, /) -> None:
        """Stores a channel.

        Parameters
        ----------
        channel: :class:`.Channel`
            The channel to store.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    @abstractmethod
    def delete_read_state(self, channel_id: str, ctx: BaseCacheContext, /) -> None:
        """Deletes a read state.

        Parameters
        ----------
        channel_id: :class:`str`
            The channel's ID.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    ##########
    # Emojis #
    ##########

    @abstractmethod
    def get_emoji(self, emoji_id: str, ctx: BaseCacheContext, /) -> Emoji | None:
        """Optional[:class:`.Emoji`]: Retrieves an emoji using ID.

        Parameters
        ----------
        emoji_id: :class:`str`
            The emoji's ID.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    def get_all_emojis(self, ctx: BaseCacheContext, /) -> Sequence[Emoji]:
        """Sequence[:class:`.Emoji`]: Retrieves all available emojis as sequence.

        Parameters
        ----------
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        return list(self.get_emojis_mapping().values())

    @abstractmethod
    def get_emojis_mapping(self) -> Mapping[str, Emoji]:
        """Mapping[:class:`str`, :class:`.ReadState`]: Retrieves all available read states as mapping."""
        ...

    @abstractmethod
    def get_server_emojis_mapping(
        self,
    ) -> Mapping[str, Mapping[str, ServerEmoji]]:
        """Mapping[:class:`str`, Mapping[:class:`str`, :class:`.ServerEmoji`]]: Retrieves all available server emojis as mapping of server ID to mapping of emoji IDs."""
        ...

    @abstractmethod
    def get_server_emojis_mapping_of(
        self, server_id: str, ctx: BaseCacheContext, /
    ) -> Mapping[str, ServerEmoji] | None:
        """Optional[Mapping[:class:`str`, :class:`.ServerEmoji`]]: Retrieves all emojis from a server as mapping.

        Parameters
        ----------
        server_id: :class:`str`
            The server's ID.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    @abstractmethod
    def delete_server_emojis_of(self, server_id: str, ctx: BaseCacheContext, /) -> None:
        """Deletes all emojis from a server.

        Parameters
        ----------
        server_id: :class:`str`
            The server's ID.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    @abstractmethod
    def store_emoji(self, emoji: Emoji, ctx: BaseCacheContext, /) -> None:
        """Stores an emoji.

        Parameters
        ----------
        emoji: :class:`.Emoji`
            The emoji to store.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    @abstractmethod
    def delete_emoji(self, emoji_id: str, server_id: str | None, ctx: BaseCacheContext, /) -> None:
        """Deletes an emoji from server.

        Parameters
        ----------
        emoji_id: :class:`str`
            The emoji's ID.
        server_id: Optional[:class:`str`]
            The server's ID. ``None`` if server ID is unavailable.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    ###########
    # Servers #
    ###########

    @abstractmethod
    def get_server(self, server_id: str, ctx: BaseCacheContext, /) -> Server | None:
        """Optional[:class:`.Server`]: Retrieves a server using ID.

        Parameters
        ----------
        server_id: :class:`str`
            The server's ID.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    def get_all_servers(self, ctx: BaseCacheContext, /) -> Sequence[Server]:
        """Sequence[:class:`.Server`]: Retrieves all available servers as sequence.

        Parameters
        ----------
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        return list(self.get_servers_mapping().values())

    @abstractmethod
    def get_servers_mapping(self) -> Mapping[str, Server]:
        """Mapping[:class:`str`, :class:`.Server`]: Retrieves all available servers as mapping."""
        ...

    @abstractmethod
    def store_server(self, server: Server, ctx: BaseCacheContext, /) -> None:
        """Stores a server.

        Parameters
        ----------
        server: :class:`.Server`
            The server to store.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    @abstractmethod
    def delete_server(self, server_id: str, ctx: BaseCacheContext, /) -> None:
        """Deletes a server.

        Parameters
        ----------
        server_id: :class:`str`
            The server's ID.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    ##################
    # Server Members #
    ##################
    @abstractmethod
    def get_server_member(self, server_id: str, user_id: str, ctx: BaseCacheContext, /) -> Member | None:
        """Optional[:class:`.Member`]: Retrieves a member in server using server and user IDs.

        Parameters
        ----------
        server_id: :class:`str`
            The server's ID.
        user_id: :class:`str`
            The user's ID.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    def get_all_server_members_of(self, server_id: str, ctx: BaseCacheContext, /) -> Sequence[Member] | None:
        """Optional[Sequence[:class:`.Member`]]: Retrieves all members from a server.

        Parameters
        ----------
        server_id: :class:`str`
            The server's ID.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ms = self.get_server_members_mapping_of(server_id, ctx)
        if ms is None:
            return None
        return list(ms.values())

    @abstractmethod
    def get_server_members_mapping_of(self, server_id: str, ctx: BaseCacheContext, /) -> Mapping[str, Member] | None:
        """Optional[Mapping[:class:`str`, :class:`.Member`]]: Retrieves all members from a server as mapping.

        Parameters
        ----------
        server_id: :class:`str`
            The server's ID.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    @abstractmethod
    def bulk_store_server_members(
        self,
        server_id: str,
        members: dict[str, Member],
        ctx: BaseCacheContext,
        /,
    ) -> None:
        """Stores server members in bulk.

        Parameters
        ----------
        server_id: :class:`str`
            The server's ID to store members in.
        members: Dict[:class:`str`, :class:`.Member`]
            The members to store.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    @abstractmethod
    def overwrite_server_members(
        self,
        server_id: str,
        members: dict[str, Member],
        ctx: BaseCacheContext,
        /,
    ) -> None:
        """Overwrites members of a server.

        Parameters
        ----------
        server_id: :class:`str`
            The server's ID to overwrite members in.
        members: Dict[:class:`str`, :class:`.Member`]
            The member to store.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    @abstractmethod
    def store_server_member(self, member: Member, ctx: BaseCacheContext, /) -> None:
        """Stores a member.

        Parameters
        ----------
        member: :class:`.Member`
            The member to store.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    @abstractmethod
    def delete_server_member(self, server_id: str, user_id: str, ctx: BaseCacheContext, /) -> None:
        """Deletes a member from server.

        Parameters
        ----------
        channel_id: :class:`str`
            The channel's ID.
        member_id: :class:`str`
            The member user's ID.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    @abstractmethod
    def delete_server_members_of(self, server_id: str, ctx: BaseCacheContext, /) -> None:
        """Deletes all members from a server.

        Parameters
        ----------
        server_id: :class:`str`
            The server's ID.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    #########
    # Users #
    #########
    @abstractmethod
    def get_user(self, user_id: str, ctx: BaseCacheContext, /) -> User | None:
        """Optional[:class:`.User`]: Retrieves a user using ID.

        Parameters
        ----------
        user_id: :class:`str`
            The user's ID.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    def get_all_users(self, ctx: BaseCacheContext, /) -> Sequence[User]:
        """Sequence[:class:`.User`]: Retrieves all available users as sequence.

        Parameters
        ----------
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        return list(self.get_users_mapping().values())

    @abstractmethod
    def get_users_mapping(self) -> Mapping[str, User]:
        """Mapping[:class:`str`, :class:`.User`]: Retrieves all available users as mapping."""
        ...

    @abstractmethod
    def store_user(self, user: User, ctx: BaseCacheContext, /) -> None:
        """Stores an user.

        Parameters
        ----------
        user: :class:`.User`
            The user to store.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    @abstractmethod
    def bulk_store_users(self, users: dict[str, User], ctx: BaseCacheContext, /) -> None:
        """Stores users in bulk.

        Parameters
        ----------
        users: Dict[:class:`str`, :class:`.User`]
            The users to store.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    ############################
    # Private Channels by User #
    ############################
    @abstractmethod
    def get_private_channel_by_user(self, user_id: str, ctx: BaseCacheContext, /) -> str | None:
        """Optional[:class:`str`]: Retrieves a private channel ID using user ID.

        Parameters
        ----------
        user_id: :class:`str`
            The user's ID.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    def get_all_private_channels_by_users(self, ctx: BaseCacheContext, /) -> Sequence[str]:
        """Sequence[:class:`str`]: Retrieves all available DM channel IDs as sequence.

        Parameters
        ----------
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        return list(self.get_private_channels_by_users_mapping().values())

    @abstractmethod
    def get_private_channels_by_users_mapping(self) -> Mapping[str, str]:
        """Mapping[:class:`str`, :class:`str`]: Retrieves all available DM channel IDs as mapping of user IDs."""
        ...

    @abstractmethod
    def store_private_channel_by_user(self, channel: DMChannel, ctx: BaseCacheContext, /) -> None:
        """Stores a DM channel.

        Parameters
        ----------
        channel: :class:`.DMChannel`
            The channel to store.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    # Should be implemented in `delete_channel`, or in event
    @abstractmethod
    def delete_private_channel_by_user(self, user_id: str, ctx: BaseCacheContext, /) -> None:
        """Deletes a DM channel by user ID.

        Parameters
        ----------
        user_id: :class:`str`
            The user's ID.
        ctx: :class:`.BaseCacheContext`
            The context.
        """

        ...

    ########################
    # Channel Voice States #
    ########################
    @abstractmethod
    def get_channel_voice_state(
        self, channel_id: str, ctx: BaseCacheContext, /
    ) -> ChannelVoiceStateContainer | None: ...

    def get_all_channel_voice_states(self, ctx: BaseCacheContext, /) -> Sequence[ChannelVoiceStateContainer]:
        """Sequence[:class:`.ChannelVoiceStateContainer`]: Retrieves all available channel voice state containers as sequence.

        Parameters
        ----------
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        return list(self.get_channel_voice_states_mapping().values())

    @abstractmethod
    def get_channel_voice_states_mapping(self) -> Mapping[str, ChannelVoiceStateContainer]:
        """Mapping[:class:`str`, :class:`.ChannelVoiceStateContainer`]: Retrieves all available channel voice state containers as mapping of channel IDs."""
        ...

    @abstractmethod
    def store_channel_voice_state(self, container: ChannelVoiceStateContainer, ctx: BaseCacheContext, /) -> None:
        """Stores a channel voice state container.

        Parameters
        ----------
        container: :class:`.ChannelVoiceStateContainer`
            The container to store.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    @abstractmethod
    def bulk_store_channel_voice_states(
        self, containers: dict[str, ChannelVoiceStateContainer], ctx: BaseCacheContext, /
    ) -> None:
        """Stores channel voice state containers in bulk.

        Parameters
        ----------
        containers: Dict[:class:`str`, :class:`.ChannelVoiceStateContainer`]
            The containers to store.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...

    @abstractmethod
    def delete_channel_voice_state(self, channel_id: str, ctx: BaseCacheContext, /) -> None:
        """Deletes a channel voice state container by channel ID.

        Parameters
        ----------
        channel_id: :class:`str`
            The channel's ID.
        ctx: :class:`.BaseCacheContext`
            The context.
        """
        ...


class EmptyCache(Cache):
    """Implementation of cache which doesn't actually store anything."""

    __slots__ = ()

    ############
    # Channels #
    ############

    def get_channel(self, channel_id: str, ctx: BaseCacheContext, /) -> Channel | None:
        return None

    def get_channels_mapping(self) -> dict[str, Channel]:
        return {}

    def store_channel(self, channel: Channel, ctx: BaseCacheContext, /) -> None:
        pass

    def delete_channel(self, channel_id: str, ctx: BaseCacheContext, /) -> None:
        pass

    def get_private_channels_mapping(self) -> dict[str, DMChannel | GroupChannel]:
        return {}

    ####################
    # Channel Messages #
    ####################
    def get_message(self, channel_id: str, message_id: str, ctx: BaseCacheContext, /) -> Message | None:
        return None

    def get_messages_mapping_of(self, channel_id: str, ctx: BaseCacheContext, /) -> Mapping[str, Message] | None:
        return None

    def store_message(self, message: Message, ctx: BaseCacheContext, /) -> None:
        pass

    def delete_message(self, channel_id: str, message_id: str, ctx: BaseCacheContext, /) -> None:
        pass

    def delete_messages_of(self, channel_id: str, ctx: BaseCacheContext, /) -> None:
        pass

    ###############
    # Read States #
    ###############
    def get_read_state(self, channel_id: str, ctx: BaseCacheContext, /) -> ReadState | None:
        return None

    def get_read_states_mapping(self) -> dict[str, ReadState]:
        return {}

    def store_read_state(self, read_state: ReadState, ctx: BaseCacheContext, /) -> None:
        pass

    def delete_read_state(self, channel_id: str, ctx: BaseCacheContext, /) -> None:
        pass

    ##########
    # Emojis #
    ##########

    def get_emoji(self, emoji_id: str, ctx: BaseCacheContext, /) -> Emoji | None:
        return None

    def get_emojis_mapping(self) -> dict[str, Emoji]:
        return {}

    def get_server_emojis_mapping(
        self,
    ) -> dict[str, dict[str, ServerEmoji]]:
        return {}

    def get_server_emojis_mapping_of(self, server_id: str, ctx: BaseCacheContext, /) -> dict[str, ServerEmoji] | None:
        return None

    def delete_server_emojis_of(self, server_id: str, ctx: BaseCacheContext, /) -> None:
        pass

    def store_emoji(self, emoji: Emoji, ctx: BaseCacheContext, /) -> None:
        pass

    def delete_emoji(self, emoji_id: str, server_id: str | None, ctx: BaseCacheContext, /) -> None:
        pass

    ###########
    # Servers #
    ###########

    def get_server(self, server_id: str, ctx: BaseCacheContext, /) -> Server | None:
        return None

    def get_servers_mapping(self) -> dict[str, Server]:
        return {}

    def store_server(self, server: Server, ctx: BaseCacheContext, /) -> None:
        pass

    def delete_server(self, server_id: str, ctx: BaseCacheContext, /) -> None:
        pass

    ##################
    # Server Members #
    ##################
    def get_server_member(self, server_id: str, user_id: str, ctx: BaseCacheContext, /) -> Member | None:
        return None

    def get_server_members_mapping_of(self, server_id: str, ctx: BaseCacheContext, /) -> dict[str, Member] | None:
        return None

    def bulk_store_server_members(
        self,
        server_id: str,
        members: dict[str, Member],
        ctx: BaseCacheContext,
        /,
    ) -> None:
        pass

    def overwrite_server_members(
        self,
        server_id: str,
        members: dict[str, Member],
        ctx: BaseCacheContext,
        /,
    ) -> None:
        pass

    def store_server_member(self, member: Member, ctx: BaseCacheContext, /) -> None:
        pass

    def delete_server_member(self, server_id: str, user_id: str, ctx: BaseCacheContext, /) -> None:
        pass

    def delete_server_members_of(self, server_id: str, ctx: BaseCacheContext, /) -> None:
        pass

    #########
    # Users #
    #########

    def get_user(self, user_id: str, ctx: BaseCacheContext, /) -> User | None:
        return None

    def get_users_mapping(self) -> dict[str, User]:
        return {}

    def store_user(self, user: User, ctx: BaseCacheContext, /) -> None:
        return None

    def bulk_store_users(self, users: dict[str, User], ctx: BaseCacheContext, /) -> None:
        pass

    ############################
    # Private Channels by User #
    ############################
    def get_private_channel_by_user(self, user_id: str, ctx: BaseCacheContext, /) -> str | None:
        return None

    def get_private_channels_by_users_mapping(self) -> dict[str, str]:
        return {}

    def store_private_channel_by_user(self, channel: DMChannel, ctx: BaseCacheContext, /) -> None:
        pass

    def delete_private_channel_by_user(self, user_id: str, ctx: BaseCacheContext, /) -> None:
        pass

    ########################
    # Channel Voice States #
    ########################
    def get_channel_voice_state(self, channel_id: str, ctx: BaseCacheContext, /) -> ChannelVoiceStateContainer | None:
        return None

    def get_channel_voice_states_mapping(self) -> Mapping[str, ChannelVoiceStateContainer]:
        return {}

    def store_channel_voice_state(self, container: ChannelVoiceStateContainer, ctx: BaseCacheContext, /) -> None:
        pass

    def bulk_store_channel_voice_states(
        self, containers: dict[str, ChannelVoiceStateContainer], ctx: BaseCacheContext, /
    ) -> None:
        pass

    def delete_channel_voice_state(self, channel_id: str, ctx: BaseCacheContext, /) -> None:
        pass


V = typing.TypeVar('V')


def _put0(d: dict[str, V], k: str, max_size: int, required_keys: int = 1, /) -> bool:  # noqa: ARG001
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


def _put1(d: dict[str, V], k: str, v: V, max_size: int, /) -> None:
    if _put0(d, k, max_size):
        d[k] = v


class MapCache(Cache):
    """Implementation of :class:`.Cache` ABC based on :class:`dict`'s.

    Parameters of this class accept negative value to represent infinite count.

    Parameters
    ----------
    channels_max_size: :class:`int`
        How many channels can have cache. Defaults to ``-1``.
    emojis_max_size: :class:`int`
        How many emojis can have cache. Defaults to ``-1``.
    messages_max_size: :class:`int`
        How many messages can have cache per channel. Defaults to ``1000``.
    private_channels_by_user_max_size: :class:`int`
        How many DM channels by user can have cache. Defaults to ``-1``.
    private_channels_max_size: :class:`int`
        How many private channels can have cache. Defaults to ``-1``.
    read_states_max_size: :class:`int`
        How many read states can have cache. Defaults to ``-1``.
    server_emojis_max_size: :class:`int`
        How many server emojis can have cache. Defaults to ``-1``.
    server_members_max_size: :class:`int`
        How many server members can have cache. Defaults to ``-1``.
    servers_max_size: :class:`int`
        How many servers can have cache. Defaults to ``-1``.
    users_max_size: :class:`int`
        How many users can have cache. Defaults to ``-1``.
    channel_voice_states_max_size: :class:`int`
        How many channel voice state containers can have cache. Defaults to ``-1``.
    """

    __slots__ = (
        '_channels',
        '_channels_max_size',
        '_channel_voice_states',
        '_channel_voice_states_max_size',
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
        channel_voice_states_max_size: int = -1,
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
        self._channel_voice_states: dict[str, ChannelVoiceStateContainer] = {}
        self._channel_voice_states_max_size: int = channel_voice_states_max_size

    ############
    # Channels #
    ############
    def get_channel(self, channel_id: str, ctx: BaseCacheContext, /) -> Channel | None:
        return self._channels.get(channel_id)

    def get_channels_mapping(self) -> Mapping[str, Channel]:
        return self._channels

    def store_channel(self, channel: Channel, ctx: BaseCacheContext, /) -> None:
        _put1(self._channels, channel.id, channel, self._channels_max_size)

        from .channel import DMChannel, GroupChannel

        if isinstance(channel, (DMChannel, GroupChannel)):
            _put1(self._private_channels, channel.id, channel, self._private_channels_max_size)

    def delete_channel(self, channel_id: str, ctx: BaseCacheContext, /) -> None:
        self._channels.pop(channel_id, None)

    def get_private_channels_mapping(self) -> Mapping[str, DMChannel | GroupChannel]:
        return self._private_channels

    ####################
    # Channel Messages #
    ####################
    def get_message(self, channel_id: str, message_id: str, ctx: BaseCacheContext, /) -> Message | None:
        messages = self._messages.get(channel_id)
        if messages:
            return messages.get(message_id)
        return None

    def get_messages_mapping_of(self, channel_id: str, ctx: BaseCacheContext, /) -> Mapping[str, Message] | None:
        return self._messages.get(channel_id)

    def store_message(self, message: Message, ctx: BaseCacheContext, /) -> None:
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

    def delete_message(self, channel_id: str, message_id: str, ctx: BaseCacheContext, /) -> None:
        messages = self._messages.get(channel_id)
        if messages:
            messages.pop(message_id, None)

    def delete_messages_of(self, channel_id: str, ctx: BaseCacheContext, /) -> None:
        self._messages.pop(channel_id, None)

    ###############
    # Read States #
    ###############
    def get_read_state(self, channel_id: str, ctx: BaseCacheContext, /) -> ReadState | None:
        return self._read_states.get(channel_id)

    def get_read_states_mapping(self) -> Mapping[str, ReadState]:
        return self._read_states

    def store_read_state(self, read_state: ReadState, ctx: BaseCacheContext, /) -> None:
        _put1(
            self._read_states,
            read_state.channel_id,
            read_state,
            self._read_states_max_size,
        )

    def delete_read_state(self, channel_id: str, ctx: BaseCacheContext, /) -> None:
        self._read_states.pop(channel_id, None)

    ##########
    # Emojis #
    ##########

    def get_emoji(self, emoji_id: str, ctx: BaseCacheContext, /) -> Emoji | None:
        return self._emojis.get(emoji_id)

    def get_emojis_mapping(self) -> Mapping[str, Emoji]:
        return self._emojis

    def get_server_emojis_mapping(
        self,
    ) -> Mapping[str, Mapping[str, ServerEmoji]]:
        return self._server_emojis

    def get_server_emojis_mapping_of(
        self, server_id: str, ctx: BaseCacheContext, /
    ) -> Mapping[str, ServerEmoji] | None:
        return self._server_emojis.get(server_id)

    def delete_server_emojis_of(self, server_id: str, ctx: BaseCacheContext, /) -> None:
        self._server_emojis.pop(server_id, None)

    def store_emoji(self, emoji: Emoji, ctx: BaseCacheContext, /) -> None:
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

    def delete_emoji(self, emoji_id: str, server_id: str | None, ctx: BaseCacheContext, /) -> None:
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

    def get_server(self, server_id: str, ctx: BaseCacheContext, /) -> Server | None:
        return self._servers.get(server_id)

    def get_servers_mapping(self) -> Mapping[str, Server]:
        return self._servers

    def store_server(self, server: Server, ctx: BaseCacheContext, /) -> None:
        if server.id not in self._server_emojis:
            _put1(self._server_emojis, server.id, {}, self._server_emojis_max_size)

        if (
            _put0(self._server_members, server.id, self._server_members_max_size)
            and server.id not in self._server_members
        ):
            self._server_members[server.id] = {}
        _put1(self._servers, server.id, server, self._servers_max_size)

    def delete_server(self, server_id: str, ctx: BaseCacheContext, /) -> None:
        self._servers.pop(server_id, None)

    ##################
    # Server Members #
    ##################
    def get_server_member(self, server_id: str, user_id: str, ctx: BaseCacheContext, /) -> Member | None:
        d = self._server_members.get(server_id)
        if d is None:
            return None
        return d.get(user_id)

    def get_server_members_mapping_of(self, server_id: str, ctx: BaseCacheContext, /) -> Mapping[str, Member] | None:
        return self._server_members.get(server_id)

    def bulk_store_server_members(
        self,
        server_id: str,
        members: dict[str, Member],
        ctx: BaseCacheContext,
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
        ctx: BaseCacheContext,
        /,
    ) -> None:
        self._server_members[server_id] = members

    def store_server_member(self, member: Member, ctx: BaseCacheContext, /) -> None:
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

    def delete_server_member(self, server_id: str, user_id: str, ctx: BaseCacheContext, /) -> None:
        members = self._server_members.get(server_id)
        if members:
            members.pop(user_id, None)

    def delete_server_members_of(self, server_id: str, ctx: BaseCacheContext, /) -> None:
        self._server_members.pop(server_id, None)

    #########
    # Users #
    #########

    def get_user(self, user_id: str, ctx: BaseCacheContext, /) -> User | None:
        return self._users.get(user_id)

    def get_users_mapping(self) -> Mapping[str, User]:
        return self._users

    def store_user(self, user: User, ctx: BaseCacheContext, /) -> None:
        _put1(self._users, user.id, user, self._users_max_size)

    def bulk_store_users(self, users: Mapping[str, User], ctx: BaseCacheContext, /) -> None:
        self._users.update(users)

    ############################
    # Private Channels by User #
    ############################
    def get_private_channel_by_user(self, user_id: str, ctx: BaseCacheContext, /) -> str | None:
        return self._private_channels_by_user.get(user_id)

    def get_private_channels_by_users_mapping(self) -> Mapping[str, str]:
        return self._private_channels_by_user

    def store_private_channel_by_user(self, channel: DMChannel, ctx: BaseCacheContext, /) -> None:
        _put1(self._private_channels_by_user, channel.recipient_id, channel.id, self._private_channels_by_user_max_size)

    def delete_private_channel_by_user(self, user_id: str, ctx: BaseCacheContext, /) -> None:
        self._private_channels_by_user.pop(user_id, None)

    ########################
    # Channel Voice States #
    ########################
    def get_channel_voice_state(self, channel_id: str, ctx: BaseCacheContext, /) -> ChannelVoiceStateContainer | None:
        return self._channel_voice_states.get(channel_id)

    def get_channel_voice_states_mapping(self) -> Mapping[str, ChannelVoiceStateContainer]:
        return self._channel_voice_states

    def store_channel_voice_state(self, container: ChannelVoiceStateContainer, ctx: BaseCacheContext, /) -> None:
        _put1(self._channel_voice_states, container.channel_id, container, self._channel_voice_states_max_size)

    def bulk_store_channel_voice_states(
        self, containers: dict[str, ChannelVoiceStateContainer], ctx: BaseCacheContext, /
    ) -> None:
        self._channel_voice_states.update(containers)

    def delete_channel_voice_state(self, channel_id: str, ctx: BaseCacheContext, /) -> None:
        self._channel_voice_states.pop(channel_id, None)


# re-export internal functions as well for future usage
__all__ = (
    'CacheContextType',
    'BaseCacheContext',
    'DetachedEmojiCacheContext',
    'MessageCacheContext',
    'ServerCacheContext',
    'ServerEmojiCacheContext',
    'UserCacheContext',
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
    '_MESSAGE_CLEAR_REACTION',
    '_MESSAGE_DELETE_BULK',
    '_SERVER_CREATE',
    '_SERVER_UPDATE',
    '_SERVER_DELETE',
    '_SERVER_MEMBER_ADD',
    '_SERVER_MEMBER_UPDATE',
    '_SERVER_MEMBER_REMOVE',
    '_SERVER_ROLE_UPDATE',
    '_SERVER_ROLE_DELETE',
    '_USER_UPDATE',
    '_USER_RELATIONSHIP_UPDATE',
    '_USER_PLATFORM_WIPE',
    '_SERVER_EMOJI_CREATE',
    '_SERVER_EMOJI_DELETE',
    '_CHANNEL_CREATE',
    '_CHANNEL_UPDATE',
    '_CHANNEL_DELETE',
    '_GROUP_RECIPIENT_ADD',
    '_GROUP_RECIPIENT_REMOVE',
    '_VOICE_CHANNEL_JOIN',
    '_VOICE_CHANNEL_LEAVE',
    '_USER_VOICE_STATE_UPDATE',
    'ProvideCacheContextIn',
    'Cache',
    'EmptyCache',
    '_put0',
    '_put1',
    'MapCache',
)
