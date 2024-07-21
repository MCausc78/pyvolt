from __future__ import annotations

import abc
from attrs import define, field
from enum import Enum, auto
import logging
import typing

from .emoji import ServerEmoji, Emoji
from .user import User

if typing.TYPE_CHECKING:
    from .channel import ServerChannel, Channel
    from .message import Message
    from .read_state import ReadState
    from .server import Server, Member

_L = logging.getLogger(__name__)


class ContextType(Enum):
    UNDEFINED = auto()
    """Context is not provided."""

    USER_REQUEST = auto()
    """The end user is asking for object."""

    LIBRARY_REQUEST = auto()
    """Library needs the object for internal purposes."""

    READY = auto()
    """Populated data from Ready event."""

    MESSAGE_ACK = auto()
    MESSAGE_CREATE = auto()
    MESSAGE_UPDATE = auto()
    MESSAGE_APPEND = auto()
    MESSAGE_DELETE = auto()
    MESSAGE_REACT = auto()
    MESSAGE_UNREACT = auto()
    MESSAGE_REMOVE_REACTION = auto()
    MESSAGE_BULK_DELETE = auto()

    SERVER_CREATE = auto()
    SERVER_UPDATE = auto()
    SERVER_DELETE = auto()

    SERVER_MEMBER_CREATE = auto()
    SERVER_MEMBER_UPDATE = auto()
    SERVER_MEMBER_DELETE = auto()

    SERVER_ROLE_UPDATE = auto()
    SERVER_ROLE_DELETE = auto()

    USER_UPDATE = auto()
    USER_RELATIONSHIP_UPDATE = auto()
    USER_PLATFORM_WIPE = auto()

    EMOJI_CREATE = auto()
    EMOJI_DELETE = auto()

    CHANNEL_CREATE = auto()
    CHANNEL_UPDATE = auto()
    CHANNEL_DELETE = auto()

    CHANNEL_GROUP_JOIN = auto()
    CHANNEL_GROUP_LEAVE = auto()
    """Data from websocket event."""

    MESSAGE = auto()
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
_MESSAGE_ACK = BaseContext(type=ContextType.MESSAGE_ACK)
_MESSAGE_CREATE = BaseContext(type=ContextType.MESSAGE_CREATE)
_MESSAGE_UPDATE = BaseContext(type=ContextType.MESSAGE_UPDATE)
_MESSAGE_APPEND = BaseContext(type=ContextType.MESSAGE_APPEND)
_MESSAGE_DELETE = BaseContext(type=ContextType.MESSAGE_DELETE)
_MESSAGE_REACT = BaseContext(type=ContextType.MESSAGE_REACT)
_MESSAGE_UNREACT = BaseContext(type=ContextType.MESSAGE_UNREACT)
_MESSAGE_REMOVE_REACTION = BaseContext(type=ContextType.MESSAGE_REMOVE_REACTION)
_MESSAGE_BULK_DELETE = BaseContext(type=ContextType.MESSAGE_BULK_DELETE)
_SERVER_CREATE = BaseContext(type=ContextType.SERVER_CREATE)
_SERVER_UPDATE = BaseContext(type=ContextType.SERVER_UPDATE)
_SERVER_DELETE = BaseContext(type=ContextType.SERVER_DELETE)
_SERVER_MEMBER_CREATE = BaseContext(type=ContextType.SERVER_MEMBER_CREATE)
_SERVER_MEMBER_UPDATE = BaseContext(type=ContextType.SERVER_MEMBER_UPDATE)
_SERVER_MEMBER_DELETE = BaseContext(type=ContextType.SERVER_MEMBER_DELETE)
_SERVER_ROLE_UPDATE = BaseContext(type=ContextType.SERVER_ROLE_UPDATE)
_SERVER_ROLE_DELETE = BaseContext(type=ContextType.SERVER_ROLE_DELETE)
_USER_UPDATE = BaseContext(type=ContextType.USER_UPDATE)
_USER_RELATIONSHIP_UPDATE = BaseContext(type=ContextType.USER_RELATIONSHIP_UPDATE)
_USER_PLATFORM_WIPE = BaseContext(type=ContextType.USER_PLATFORM_WIPE)
_EMOJI_CREATE = BaseContext(type=ContextType.EMOJI_CREATE)
_EMOJI_DELETE = BaseContext(type=ContextType.EMOJI_DELETE)
_CHANNEL_CREATE = BaseContext(type=ContextType.CHANNEL_CREATE)
_CHANNEL_UPDATE = BaseContext(type=ContextType.CHANNEL_UPDATE)
_CHANNEL_DELETE = BaseContext(type=ContextType.CHANNEL_DELETE)
_CHANNEL_GROUP_JOIN = BaseContext(type=ContextType.CHANNEL_GROUP_JOIN)
_CHANNEL_GROUP_LEAVE = BaseContext(type=ContextType.CHANNEL_GROUP_LEAVE)


class Cache(abc.ABC):
    ############
    # Channels #
    ############

    @abc.abstractmethod
    def get_channel(self, channel_id: str, ctx: BaseContext, /) -> Channel | None: ...

    def get_all_channels(self, ctx: BaseContext, /) -> list[Channel]:
        return list(self.get_channels_mapping().values())

    @abc.abstractmethod
    def get_channels_mapping(self) -> dict[str, Channel]: ...

    @abc.abstractmethod
    def store_channel(self, channel: Channel, ctx: BaseContext, /) -> None: ...

    @abc.abstractmethod
    def delete_channel(self, channel_id: str, ctx: BaseContext, /) -> None: ...

    ###############
    # Read States #
    ###############
    @abc.abstractmethod
    def get_read_state(self, channel_id: str, ctx: BaseContext, /) -> ReadState | None: ...

    def get_all_read_states(self, ctx: BaseContext, /) -> list[ReadState]:
        return list(self.get_read_states_mapping().values())

    @abc.abstractmethod
    def get_read_states_mapping(self) -> dict[str, ReadState]: ...

    @abc.abstractmethod
    def store_read_state(self, read_state: ReadState, ctx: BaseContext, /) -> None: ...

    @abc.abstractmethod
    def delete_read_state(self, channel_id: str, ctx: BaseContext, /) -> None: ...

    ##########
    # Emojis #
    ##########

    @abc.abstractmethod
    def get_emoji(self, emoji_id: str, ctx: BaseContext, /) -> Emoji | None: ...

    def get_all_emojis(self, ctx: BaseContext, /) -> list[Emoji]:
        return list(self.get_emojis_mapping().values())

    @abc.abstractmethod
    def get_emojis_mapping(self) -> dict[str, Emoji]: ...

    @abc.abstractmethod
    def get_server_emojis_mapping(
        self,
    ) -> dict[str, dict[str, ServerEmoji]]: ...

    @abc.abstractmethod
    def get_server_emojis_mapping_of(self, server_id: str, ctx: BaseContext, /) -> dict[str, ServerEmoji] | None: ...

    @abc.abstractmethod
    def store_emoji(self, emoji: Emoji, ctx: BaseContext, /) -> None: ...

    @abc.abstractmethod
    def delete_emoji(self, emoji_id: str, server_id: str | None, ctx: BaseContext, /) -> None: ...

    ###########
    # Servers #
    ###########

    @abc.abstractmethod
    def get_server(self, server_id: str, ctx: BaseContext, /) -> Server | None: ...

    def get_all_servers(self, ctx: BaseContext, /) -> list[Server]:
        return list(self.get_servers_mapping().values())

    @abc.abstractmethod
    def get_servers_mapping(self) -> dict[str, Server]: ...

    @abc.abstractmethod
    def store_server(self, server: Server, ctx: BaseContext, /) -> None: ...

    @abc.abstractmethod
    def delete_server(self, server_id: str, ctx: BaseContext, /) -> None: ...

    ##################
    # Server Members #
    ##################
    @abc.abstractmethod
    def get_server_member(self, server_id: str, user_id: str, ctx: BaseContext, /) -> Member | None: ...

    def get_all_server_members_of(self, server_id: str, ctx: BaseContext, /) -> list[Member] | None:
        ms = self.get_server_members_mapping_of(server_id, ctx)
        if ms is None:
            return None
        return list(ms.values())

    @abc.abstractmethod
    def get_server_members_mapping_of(self, server_id: str, ctx: BaseContext, /) -> dict[str, Member] | None: ...

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

    #########
    # Users #
    #########

    @abc.abstractmethod
    def get_user(self, user_id: str, ctx: BaseContext, /) -> User | None: ...

    def get_all_users(self, ctx: BaseContext, /) -> list[User]:
        return list(self.get_users_mapping().values())

    @abc.abstractmethod
    def get_users_mapping(self) -> dict[str, User]: ...

    @abc.abstractmethod
    def store_user(self, user: User, ctx: BaseContext, /) -> None: ...

    @abc.abstractmethod
    def bulk_store_users(self, users: dict[str, User], ctx: BaseContext, /) -> None: ...


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


V = typing.TypeVar('V')


def _put0(d: dict[str, V], k: str, max_size: int, required_keys: int = 1) -> bool:
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
    _channels: dict[str, Channel]
    _channels_max_size: int
    _read_states: dict[str, ReadState]
    _read_states_max_size: int
    _emojis: dict[str, Emoji]
    _emojis_max_size: int
    _server_emojis: dict[str, dict[str, ServerEmoji]]
    _server_emojis_max_size: int
    _servers: dict[str, Server]
    _servers_max_size: int
    _server_members: dict[str, dict[str, Member]]
    _server_members_max_size: int
    _users: dict[str, User]
    _users_max_size: int

    __slots__ = (
        '_channels',
        '_channels_max_size',
        '_read_states',
        '_read_states_max_size',
        '_emojis',
        '_emojis_max_size',
        '_server_emojis',
        '_server_emojis_max_size',
        '_servers',
        '_servers_max_size',
        '_server_members',
        '_server_members_max_size',
        '_users',
        '_users_max_size',
    )

    def __init__(
        self,
        *,
        channels_max_size: int = -1,
        read_states_max_size: int = -1,
        emojis_max_size: int = -1,
        server_emojis_max_size: int = -1,
        servers_max_size: int = -1,
        server_members_max_size: int = -1,
        users_max_size: int = -1,
    ) -> None:
        self._channels = {}
        self._channels_max_size = channels_max_size
        self._read_states = {}
        self._read_states_max_size = read_states_max_size
        self._emojis = {}
        self._emojis_max_size = emojis_max_size
        self._server_emojis = {}
        self._server_emojis_max_size = server_emojis_max_size
        self._servers = {}
        self._servers_max_size = servers_max_size
        self._server_members = {}
        self._server_members_max_size = server_members_max_size
        self._users = {}
        self._users_max_size = users_max_size

    ############
    # Channels #
    ############

    def get_channel(self, channel_id: str, ctx: BaseContext, /) -> Channel | None:
        return self._channels.get(channel_id)

    def get_channels_mapping(self) -> dict[str, Channel]:
        return self._channels

    def store_channel(self, channel: Channel, ctx: BaseContext, /) -> None:
        _put1(self._channels, channel.id, channel, self._channels_max_size)

    def delete_channel(self, channel_id: str, ctx: BaseContext, /) -> None:
        try:
            del self._channels[channel_id]
        except KeyError:
            pass

    ###############
    # Read States #
    ###############
    def get_read_state(self, channel_id: str, ctx: BaseContext, /) -> ReadState | None:
        return self._read_states.get(channel_id)

    def get_read_states_mapping(self) -> dict[str, ReadState]:
        return self._read_states

    def store_read_state(self, read_state: ReadState, ctx: BaseContext, /) -> None:
        _put1(
            self._read_states,
            read_state.channel_id,
            read_state,
            self._read_states_max_size,
        )

    def delete_read_state(self, channel_id: str, ctx: BaseContext, /) -> None:
        del self._read_states[channel_id]

    ##########
    # Emojis #
    ##########

    def get_emoji(self, emoji_id: str, ctx: BaseContext, /) -> Emoji | None:
        return self._emojis.get(emoji_id)

    def get_emojis_mapping(self) -> dict[str, Emoji]:
        return self._emojis

    def get_server_emojis_mapping(
        self,
    ) -> dict[str, dict[str, ServerEmoji]]:
        return self._server_emojis

    def get_server_emojis_mapping_of(self, server_id: str, ctx: BaseContext, /) -> dict[str, ServerEmoji] | None:
        return self._server_emojis.get(server_id)

    def store_emoji(self, emoji: Emoji, ctx: BaseContext, /) -> None:
        if isinstance(emoji, ServerEmoji):
            server_id = emoji.server_id
            if _put0(self._server_emojis, server_id, self._server_emojis_max_size):
                self._server_emojis[server_id] = {
                    **self._server_emojis.get(server_id, {}),
                    emoji.id: emoji,
                }
        _put1(self._emojis, emoji.id, emoji, self._emojis_max_size)

    def delete_emoji(self, emoji_id: str, server_id: str | None, ctx: BaseContext, /) -> None:
        emoji = self._emojis.get(emoji_id)

        try:
            del self._emojis[emoji_id]
        except KeyError:
            pass

        server_ids: tuple[str, ...] = ()
        if isinstance(emoji, ServerEmoji):
            if server_id:
                server_ids = (server_id, emoji.server_id)
            else:
                server_ids = (emoji.server_id,)

        for server_id in server_ids:
            server_emojis = self._server_emojis.get(server_id, {})
            try:
                del server_emojis[emoji_id]
            except KeyError:
                pass

    ###########
    # Servers #
    ###########

    def get_server(self, server_id: str, ctx: BaseContext, /) -> Server | None:
        return self._servers.get(server_id)

    def get_servers_mapping(self) -> dict[str, Server]:
        return self._servers

    def store_server(self, server: Server, ctx: BaseContext, /) -> None:
        _put1(self._server_emojis, server.id, {}, self._server_emojis_max_size)
        if (
            _put0(self._server_members, server.id, self._server_members_max_size)
            and server.id not in self._server_members
        ):
            self._server_members[server.id] = {}
        server._ensure_cached()
        _put1(self._servers, server.id, server, self._servers_max_size)

    def delete_server(self, server_id: str, ctx: BaseContext, /) -> None:
        try:
            del self._servers[server_id]
        except KeyError:
            pass

    ##################
    # Server Members #
    ##################
    def get_server_member(self, server_id: str, user_id: str, ctx: BaseContext, /) -> Member | None:
        d = self._server_members.get(server_id)
        if d is None:
            return None
        return d.get(user_id)

    def get_server_members_mapping_of(self, server_id: str, ctx: BaseContext, /) -> dict[str, Member] | None:
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
            self._server_members[member.server_id] = {member.id: member}
        else:
            d[member.id] = member

    def delete_server_member(self, server_id: str, user_id: str, ctx: BaseContext, /) -> None:
        members = self._server_members.get(server_id)
        if members:
            try:
                del members[user_id]
            except KeyError:
                pass

    #########
    # Users #
    #########

    def get_user(self, user_id: str, ctx: BaseContext, /) -> User | None:
        return self._users.get(user_id)

    def get_users_mapping(self) -> dict[str, User]:
        return self._users

    def store_user(self, user: User, ctx: BaseContext, /) -> None:
        _put1(self._users, user.id, user, self._users_max_size)

    def bulk_store_users(self, users: dict[str, User], ctx: BaseContext, /) -> None:
        self._users.update(users)


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
    'Cache',
    'EmptyCache',
    '_put0',
    '_put1',
    'MapCache',
)
