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
from datetime import datetime, timedelta
import typing

from . import (
    cache as caching,
    utils,
)
from .base import Base
from .bot import BaseBot
from .cdn import StatelessAsset, Asset, ResolvableResource
from .core import (
    UNDEFINED,
    UndefinedOr,
    ULIDOr,
    resolve_id,
)
from .emoji import ServerEmoji
from .enums import ChannelType, ContentReportReason, RelationshipStatus
from .errors import NoData
from .flags import Permissions, ServerFlags, UserBadges, UserFlags
from .permissions import Permissions, PermissionOverride
from .user import (
    UserStatus,
    BaseUser,
    DisplayUser,
    BotUserMetadata,
    User,
)


if typing.TYPE_CHECKING:
    from collections.abc import Mapping

    from . import raw
    from .channel import (
        TextChannel,
        VoiceChannel,
        ServerChannel,
        TextableChannel,
        PartialMessageable,
    )
    from .state import State

_new_permissions = Permissions.__new__
_new_server_flags = ServerFlags.__new__


class Category:
    """Represents a category containing channels in Revolt server.

    Parameters
    ----------
    id: :class:`str`
        The category's ID. Must be between 1 and 32 characters long.
    title: :class:`str`
        The category's title. Must be between 1 and 32 characters long.

    Attributes
    ----------
    id: :class:`str`
        The category's ID.
    title: :class:`str`
        The category's title.
    channels: List[:class:`str`]
        The channel's IDs inside this category.
    """

    __slots__ = ('id', 'title', 'channels')

    def __init__(
        self,
        id: ULIDOr[Category],
        title: str,
        channels: list[ULIDOr[ServerChannel]],
    ) -> None:
        self.id: str = resolve_id(id)
        self.title: str = title
        self.channels: list[str] = list(map(resolve_id, channels))

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, Category) and self.id == other.id

    def build(self) -> raw.Category:
        return {
            'id': self.id,
            'title': self.title,
            'channels': self.channels,
        }


class SystemMessageChannels:
    """Represents system message channel assignments in a Revolt server.

    Attributes
    ----------
    user_joined: Optional[:class:`str`]
        The channel's ID to send user join messages in.
    user_left: Optional[:class:`str`]
        The channel's ID to send user left messages in.
    user_kicked: Optional[:class:`str`]
        The channel's ID to send user kicked messages in.
    user_banned: Optional[:class:`str`]
        The channel's ID to send user banned messages in.
    """

    __slots__ = ('user_joined', 'user_left', 'user_kicked', 'user_banned')

    def __init__(
        self,
        *,
        user_joined: typing.Optional[ULIDOr[typing.Union[TextableChannel, PartialMessageable]]] = None,
        user_left: typing.Optional[ULIDOr[typing.Union[TextableChannel, PartialMessageable]]] = None,
        user_kicked: typing.Optional[ULIDOr[typing.Union[TextableChannel, PartialMessageable]]] = None,
        user_banned: typing.Optional[ULIDOr[typing.Union[TextableChannel, PartialMessageable]]] = None,
    ) -> None:
        self.user_joined: typing.Optional[str] = None if user_joined is None else resolve_id(user_joined)
        self.user_left: typing.Optional[str] = None if user_left is None else resolve_id(user_left)
        self.user_kicked: typing.Optional[str] = None if user_kicked is None else resolve_id(user_kicked)
        self.user_banned: typing.Optional[str] = None if user_banned is None else resolve_id(user_banned)

    def __eq__(self, other: object, /) -> bool:
        return (
            self is other
            or isinstance(other, SystemMessageChannels)
            and (
                self.user_joined == other.user_joined
                and self.user_left == other.user_left
                and self.user_kicked == other.user_kicked
                and self.user_banned == other.user_banned
            )
        )

    def build(self) -> raw.SystemMessageChannels:
        payload: raw.SystemMessageChannels = {}
        if self.user_joined is not None:
            payload['user_joined'] = self.user_joined
        if self.user_left is not None:
            payload['user_left'] = self.user_left
        if self.user_kicked is not None:
            payload['user_kicked'] = self.user_kicked
        if self.user_banned is not None:
            payload['user_banned'] = self.user_banned
        return payload


@define(slots=True)
class BaseRole(Base):
    """Represents a base role in Revolt server."""

    server_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The server's ID the role belongs to."""

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, BaseRole) and self.id == other.id

    async def delete(self) -> None:
        """|coro|

        Deletes a server role.

        You must have :attr:`~Permissions.manage_roles` to do this.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+----------------------------------------------------------------------------+
            | Value                 | Reason                                                                     |
            +-----------------------+----------------------------------------------------------------------------+
            | ``NotElevated``       | Rank of your top role is higher than rank of role you're trying to delete. |
            +-----------------------+----------------------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to delete role.                     |
            +-----------------------+----------------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+--------------------------------+
            | Value        | Reason                         |
            +--------------+--------------------------------+
            | ``NotFound`` | The server/role was not found. |
            +--------------+--------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """

        return await self.state.http.delete_role(self.server_id, self.id)

    async def edit(
        self,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        color: UndefinedOr[typing.Optional[str]] = UNDEFINED,
        hoist: UndefinedOr[bool] = UNDEFINED,
        rank: UndefinedOr[int] = UNDEFINED,
    ) -> Role:
        """|coro|

        Edits a role.

        You must have :attr:`~Permissions.manage_roles` to do this.

        Parameters
        ----------
        server: ULIDOr[:class:`.BaseServer`]
            The server the role in.
        role: ULIDOr[:class:`.BaseRole`]
            The role to edit.
        name: UndefinedOr[:class:`str`]
            The new role name. Must be between 1 and 32 characters long.
        color: UndefinedOr[Optional[:class:`str`]]
            The new role color. Must be a valid CSS color.
        hoist: UndefinedOr[:class:`bool`]
            Whether this role should be displayed separately.
        rank: UndefinedOr[:class:`int`]
            The new ranking position. The smaller value is, the more role takes priority.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+---------------------------------------------------------------------------------+
            | Value                 | Reason                                                                          |
            +-----------------------+---------------------------------------------------------------------------------+
            | ``NotElevated``       | One of these:                                                                   |
            |                       |                                                                                 |
            |                       | - Rank of your top role is higher than rank of role you're trying to edit.      |
            |                       | - Rank of your top role is higher than rank you're trying to set for this role. |
            +-----------------------+---------------------------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to edit role.                            |
            +-----------------------+---------------------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+--------------------------------+
            | Value        | Reason                         |
            +--------------+--------------------------------+
            | ``NotFound`` | The server/role was not found. |
            +--------------+--------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`.Role`
            The newly updated role.
        """
        return await self.state.http.edit_role(
            self.server_id,
            self.id,
            name=name,
            color=color,
            hoist=hoist,
            rank=rank,
        )

    async def set_permissions(
        self,
        *,
        allow: Permissions = Permissions.none(),
        deny: Permissions = Permissions.none(),
    ) -> Server:
        """|coro|

        Sets permissions for this role.

        You must have :attr:`~Permissions.manage_permissions` to do this.

        Parameters
        ----------
        allow: :class:`.Permissions`
            The permissions to allow.
        deny: :class:`.Permissions`
            The permissions to deny.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------------------+--------------------------------------------------------------------------------------+
            | Value                            | Reason                                                                               |
            +----------------------------------+--------------------------------------------------------------------------------------+
            | ``CannotGiveMissingPermissions`` | Your new provided permissions contained permissions you didn't have.                 |
            +----------------------------------+--------------------------------------------------------------------------------------+
            | ``NotElevated``                  | Rank of your top role is higher than rank of role you're trying to set override for. |
            +----------------------------------+--------------------------------------------------------------------------------------+
            | ``MissingPermission``            | You do not have the proper permissions to edit permissions for this role.            |
            +----------------------------------+--------------------------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+--------------------------------+
            | Value        | Reason                         |
            +--------------+--------------------------------+
            | ``NotFound`` | The server/role was not found. |
            +--------------+--------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`.Server`
            The updated server with new permissions.
        """

        return await self.state.http.set_server_permissions_for_role(self.server_id, self.id, allow=allow, deny=deny)


@define(slots=True)
class PartialRole(BaseRole):
    """Represents a partial role for the server.

    Unmodified fields will have :data:`.UNDEFINED` value.
    """

    name: UndefinedOr[str] = field(repr=True, kw_only=True)
    """UndefinedOr[:class:`str`]: The new role's name."""

    permissions: UndefinedOr[PermissionOverride] = field(repr=True, kw_only=True)
    """UndefinedOr[:class:`.PermissionOverride`]: The new role's permissions."""

    color: UndefinedOr[typing.Optional[str]] = field(repr=True, kw_only=True)
    """UndefinedOr[Optional[:class:`str`]]: The new role's color. This can be any valid CSS color."""

    hoist: UndefinedOr[bool] = field(repr=True, kw_only=True)
    """UndefinedOr[:class:`bool`]: Whether this role should be shown separately on the member sidebar."""

    rank: UndefinedOr[int] = field(repr=True, kw_only=True)
    """UndefinedOr[:class:`int`]: The new role's rank."""

    def into_full(self) -> typing.Optional[Role]:
        """Optional[:class:`.Role`]: Tries transform this partial role into full object. This is useful when caching role."""
        if (
            self.name is not UNDEFINED
            and self.permissions is not UNDEFINED
            and self.hoist is not UNDEFINED
            and self.rank is not UNDEFINED
        ):
            color = None if not self.color is not UNDEFINED else self.color
            return Role(
                state=self.state,
                id=self.id,
                server_id=self.server_id,
                name=self.name,
                permissions=self.permissions,
                color=color,
                hoist=self.hoist,
                rank=self.rank,
            )


@define(slots=True)
class Role(BaseRole):
    """Represents a role in Revolt server."""

    name: str = field(repr=True, kw_only=True)
    """:class:`str`: The role's name."""

    permissions: PermissionOverride = field(repr=True, kw_only=True)
    """:class:`.PermissionOverride`: Permissions available to this role."""

    color: typing.Optional[str] = field(repr=True, kw_only=True)
    """Optional[:class:`str`]: The role's color. This is valid CSS color."""

    hoist: bool = field(repr=True, kw_only=True)
    """:class:`bool`: Whether this role should be shown separately on the member sidebar."""

    rank: int = field(repr=True, kw_only=True)
    """:class:`int`: The role's rank."""

    def locally_update(self, data: PartialRole, /) -> None:
        """Locally updates role with provided data.

        .. warning::
            This is called by library internally to keep cache up to date.
        """
        if data.name is not UNDEFINED:
            self.name = data.name
        if data.permissions is not UNDEFINED:
            self.permissions = data.permissions
        if data.color is not UNDEFINED:
            self.color = data.color
        if data.hoist is not UNDEFINED:
            self.hoist = data.hoist
        if data.rank is not UNDEFINED:
            self.rank = data.rank


@define(slots=True)
class BaseServer(Base):
    """Represents a server on Revolt."""

    def get_emoji(self, emoji_id: str, /) -> typing.Optional[ServerEmoji]:
        """Retrieves a server emoji from cache.

        Parameters
        ----------
        emoji_id: :class:`str`
            The emoji ID.

        Returns
        -------
        Optional[:class:`.ServerEmoji`]
            The emoji or ``None`` if not found.
        """
        cache = self.state.cache
        if not cache:
            return
        emoji = cache.get_emoji(emoji_id, caching._USER_REQUEST)
        if emoji and isinstance(emoji, ServerEmoji) and emoji.server_id == self.id:
            return emoji

    def get_member(self, user_id: str, /) -> typing.Optional[Member]:
        """Retrieves a server member from cache.

        Parameters
        ----------
        user_id: :class:`str`
            The user ID.

        Returns
        -------
        Optional[:class:`.Member`]
            The member or ``None`` if not found.
        """
        cache = self.state.cache
        if not cache:
            return
        return cache.get_server_member(self.id, user_id, caching._USER_REQUEST)

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, BaseServer) and self.id == other.id

    @property
    def emojis(self) -> Mapping[str, ServerEmoji]:
        """Mapping[:class:`str`, :class:`.ServerEmoji`]: Returns all emojis of this server."""
        cache = self.state.cache
        if cache:
            return cache.get_server_emojis_mapping_of(self.id, caching._USER_REQUEST) or {}
        return {}

    @property
    def members(self) -> Mapping[str, Member]:
        """Mapping[:class:`str`, :class:`.Member`]: Returns all members of this server."""
        cache = self.state.cache
        if cache:
            return cache.get_server_members_mapping_of(self.id, caching._USER_REQUEST) or {}
        return {}

    async def add_bot(
        self,
        bot: ULIDOr[typing.Union[BaseBot, BaseUser]],
    ) -> None:
        """|coro|

        Invites a bot to a server or group.

        You must have :attr:`~Permissions.manage_server` to do this.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        bot: ULIDOr[Union[:class:`.BaseBot`, :class:`.BaseUser`]]
            The bot.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +-----------+-------------------------------------------+
            | Value     | Reason                                    |
            +-----------+-------------------------------------------+
            | ``IsBot`` | The current token belongs to bot account. |
            +-----------+-------------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+-----------------------------------------------------+
            | Value                 | Reason                                              |
            +-----------------------+-----------------------------------------------------+
            | ``Banned``            | The bot was banned in target server.                |
            +-----------------------+-----------------------------------------------------+
            | ``BotIsPrivate``      | You do not own the bot to add it.                   |
            +-----------------------+-----------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to add bots. |
            +-----------------------+-----------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+-------------------------------+
            | Value        | Reason                        |
            +--------------+-------------------------------+
            | ``NotFound`` | The bot/server was not found. |
            +--------------+-------------------------------+
        :class:`Conflict`
            Possible values for :attr:`~HTTPException.type`:

            +---------------------+-------------------------------+
            | Value               | Reason                        |
            +---------------------+-------------------------------+
            | ``AlreadyInServer`` | The bot is already in server. |
            +---------------------+-------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """

        return await self.state.http.invite_bot(bot, server=self.id)

    async def ban(self, user: typing.Union[str, BaseUser, BaseMember], *, reason: typing.Optional[str] = None) -> Ban:
        """|coro|

        Bans a user from the server.

        You must have :attr:`~Permissions.ban_members` to do this.

        Parameters
        ----------
        user: Union[:class:`str`, :class:`.BaseUser`, :class:`.BaseMember`]
            The user to ban from the server.
        reason: Optional[:class:`str`]
            The ban reason. Can be only up to 1024 characters long.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------------+--------------------------------+
            | Value                    | Reason                         |
            +--------------------------+--------------------------------+
            | ``CannotRemoveYourself`` | You tried to ban yourself.     |
            +--------------------------+--------------------------------+
            | ``FailedValidation``     | The payload was invalid.       |
            +--------------------------+--------------------------------+
            | ``InvalidOperation``     | You tried to ban server owner. |
            +--------------------------+--------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------------------+-------------------------------------------------------------------------------------+
            | Value                            | Reason                                                                              |
            +----------------------------------+-------------------------------------------------------------------------------------+
            | ``NotElevated``                  | Rank of your top role is higher than rank of top role of user you're trying to ban. |
            +----------------------------------+-------------------------------------------------------------------------------------+
            | ``MissingPermission``            | You do not have the proper permissions to ban members.                              |
            +----------------------------------+-------------------------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+--------------------------------+
            | Value        | Reason                         |
            +--------------+--------------------------------+
            | ``NotFound`` | The server/user was not found. |
            +--------------+--------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`.Ban`
            The created ban.
        """
        return await self.state.http.ban(self.id, user, reason=reason)

    @typing.overload
    async def create_channel(
        self,
        *,
        type: None = ...,
        name: str,
        description: typing.Optional[str] = ...,
        nsfw: typing.Optional[bool] = ...,
    ) -> TextChannel: ...

    @typing.overload
    async def create_channel(
        self,
        *,
        type: typing.Literal[ChannelType.text] = ...,
        name: str,
        description: typing.Optional[str] = ...,
        nsfw: typing.Optional[bool] = ...,
    ) -> TextChannel: ...

    @typing.overload
    async def create_channel(
        self,
        *,
        type: typing.Literal[ChannelType.voice] = ...,
        name: str,
        description: typing.Optional[str] = ...,
        nsfw: typing.Optional[bool] = ...,
    ) -> VoiceChannel: ...

    async def create_channel(
        self,
        *,
        type: typing.Optional[ChannelType] = None,
        name: str,
        description: typing.Optional[str] = None,
        nsfw: typing.Optional[bool] = None,
    ) -> ServerChannel:
        """|coro|

        Create a new text or voice channel within server.

        You must have :attr:`~Permissions.manage_channels` to do this.

        Parameters
        ----------
        type: Optional[:class:`.ChannelType`]
            The channel type. Defaults to :attr:`.ChannelType.text` if not provided.
        name: :class:`str`
            The channel name. Must be between 1 and 32 characters.
        description: Optional[:class:`str`]
            The channel description. Can be only up to 1024 characters.
        nsfw: Optional[:class:`bool`]
            To mark channel as NSFW or not.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +---------------------+-----------------------------------------------------------------+
            | Value               | Reason                                                          |
            +---------------------+-----------------------------------------------------------------+
            | ``TooManyChannels`` | The server has too many channels than allowed on this instance. |
            +---------------------+-----------------------------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+-----------------------------------------+
            | Value              | Reason                                  |
            +--------------------+-----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid.  |
            +--------------------+-----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+----------------------------------------------------------------------+
            | Value                 | Reason                                                               |
            +-----------------------+----------------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to create channels in server. |
            +-----------------------+----------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+---------------------------+
            | Value        | Reason                    |
            +--------------+---------------------------+
            | ``NotFound`` | The server was not found. |
            +--------------+---------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`.ServerChannel`
            The channel created in server.
        """

        return await self.state.http.create_server_channel(
            self.id, type=type, name=name, description=description, nsfw=nsfw
        )

    async def create_text_channel(
        self, name: str, *, description: typing.Optional[str] = None, nsfw: typing.Optional[bool] = None
    ) -> TextChannel:
        """|coro|

        Create a new text channel within server.

        You must have :attr:`~Permissions.manage_channels` to do this.

        Parameters
        ----------
        name: :class:`str`
            The channel name. Must be between 1 and 32 characters.
        description: Optional[:class:`str`]
            The channel description. Can be only up to 1024 characters.
        nsfw: Optional[:class:`bool`]
            To mark channel as NSFW or not.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +---------------------+-----------------------------------------------------------------+
            | Value               | Reason                                                          |
            +---------------------+-----------------------------------------------------------------+
            | ``TooManyChannels`` | The server has too many channels than allowed on this instance. |
            +---------------------+-----------------------------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+-----------------------------------------+
            | Value              | Reason                                  |
            +--------------------+-----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid.  |
            +--------------------+-----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+----------------------------------------------------------------------+
            | Value                 | Reason                                                               |
            +-----------------------+----------------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to create channels in server. |
            +-----------------------+----------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+---------------------------+
            | Value        | Reason                    |
            +--------------+---------------------------+
            | ``NotFound`` | The server was not found. |
            +--------------+---------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`.TextChannel`
            The channel created in server.
        """
        channel = await self.create_channel(type=ChannelType.text, name=name, description=description, nsfw=nsfw)
        return channel

    async def create_voice_channel(
        self, name: str, *, description: typing.Optional[str] = None, nsfw: typing.Optional[bool] = None
    ) -> VoiceChannel:
        """|coro|

        Create a new voice channel within server.

        You must have :attr:`~Permissions.manage_channels` to do this.

        Parameters
        ----------
        name: :class:`str`
            The channel name. Must be between 1 and 32 characters.
        description: Optional[:class:`str`]
            The channel description. Can be only up to 1024 characters.
        nsfw: Optional[:class:`bool`]
            To mark channel as NSFW or not.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +---------------------+-----------------------------------------------------------------+
            | Value               | Reason                                                          |
            +---------------------+-----------------------------------------------------------------+
            | ``TooManyChannels`` | The server has too many channels than allowed on this instance. |
            +---------------------+-----------------------------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+-----------------------------------------+
            | Value              | Reason                                  |
            +--------------------+-----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid.  |
            +--------------------+-----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+----------------------------------------------------------------------+
            | Value                 | Reason                                                               |
            +-----------------------+----------------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to create channels in server. |
            +-----------------------+----------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+---------------------------+
            | Value        | Reason                    |
            +--------------+---------------------------+
            | ``NotFound`` | The server was not found. |
            +--------------+---------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`.VoiceChannel`
            The channel created in server.
        """
        channel = await self.create_channel(type=ChannelType.voice, name=name, description=description, nsfw=nsfw)
        return channel

    async def create_role(self, *, name: str, rank: typing.Optional[int] = None) -> Role:
        """|coro|

        Creates a new server role.

        You must have :attr:`~Permissions.manage_roles` to do this.

        Parameters
        ----------
        name: :class:`str`
            The role name. Must be between 1 and 32 characters long.
        rank: Optional[:class:`int`]
            The ranking position. The smaller value is, the more role takes priority.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------+--------------------------------------------------------------+
            | Value                | Reason                                                       |
            +----------------------+--------------------------------------------------------------+
            | ``FailedValidation`` | The payload was invalid.                                     |
            +----------------------+--------------------------------------------------------------+
            | ``TooManyRoles``     | The server has too many roles than allowed on this instance. |
            +----------------------+--------------------------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+----------------------------------------------------------------------------+
            | Value                 | Reason                                                                     |
            +-----------------------+----------------------------------------------------------------------------+
            | ``NotElevated``       | Rank of your top role is higher than rank of role you're trying to create. |
            +-----------------------+----------------------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to create role in this server.      |
            +-----------------------+----------------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+--------------------------------+
            | Value        | Reason                         |
            +--------------+--------------------------------+
            | ``NotFound`` | The server/role was not found. |
            +--------------+--------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`.Role`
            The role created in server.
        """

        return await self.state.http.create_role(self.id, name=name, rank=rank)

    async def delete(self) -> None:
        """|coro|

        Deletes a server if owner, or leaves otherwise.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+-----------------------------------------+
            | Value              | Reason                                  |
            +--------------------+-----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid.  |
            +--------------------+-----------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+---------------------------+
            | Value        | Reason                    |
            +--------------+---------------------------+
            | ``NotFound`` | The server was not found. |
            +--------------+---------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """
        return await self.state.http.delete_server(self.id)

    async def edit(
        self,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[typing.Optional[str]] = UNDEFINED,
        icon: UndefinedOr[typing.Optional[ResolvableResource]] = UNDEFINED,
        banner: UndefinedOr[typing.Optional[ResolvableResource]] = UNDEFINED,
        categories: UndefinedOr[typing.Optional[list[Category]]] = UNDEFINED,
        system_messages: UndefinedOr[typing.Optional[SystemMessageChannels]] = UNDEFINED,
        flags: UndefinedOr[ServerFlags] = UNDEFINED,
        discoverable: UndefinedOr[bool] = UNDEFINED,
        analytics: UndefinedOr[bool] = UNDEFINED,
    ) -> Server:
        """|coro|

        Edits a server.

        To provide any of parameters below (except for ``categories``, ``discoverable`` and ``flags``), you must have :attr:`~Permissions.manage_server`.

        Parameters
        ----------
        server: ULIDOr[:class:`.BaseServer`]
            The server to edit.
        name: UndefinedOr[:class:`str`]
            The new server name. Must be between 1 and 32 characters long.
        description: UndefinedOr[Optional[:class:`str`]]
            The new server description. Can be only up to 1024 characters.
        icon: UndefinedOr[Optional[:class:`.ResolvableResource`]]
            The new server icon.
        banner: UndefinedOr[Optional[:class:`.ResolvableResource`]]
            The new server banner.
        categories: UndefinedOr[Optional[List[:class:`.Category`]]]
            The new server categories structure.

            You must have :attr:`~Permissions.manage_channels`.
        system_messsages: UndefinedOr[Optional[:class:`.SystemMessageChannels`]]
            The new system message channels configuration.
        flags: UndefinedOr[:class:`.ServerFlags`]
            The new server flags. You must be a privileged user to provide this.
        discoverable: UndefinedOr[:class:`bool`]
            Whether this server is public and should show up on `Revolt Discover <https://rvlt.gg>`_.

            The new server flags. You must be a privileged user to provide this.
        analytics: UndefinedOr[:class:`bool`]
            Whether analytics should be collected for this server. Must be enabled in order to show up on `Revolt Discover <https://rvlt.gg>`_.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------+-------------------------------------------+
            | Value                | Reason                                    |
            +----------------------+-------------------------------------------+
            | ``FailedValidation`` | The payload was invalid.                  |
            +----------------------+-------------------------------------------+
            | ``InvalidOperation`` | More than 2 categories had same channel.  |
            +----------------------+-------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+---------------------------------------------------------------------------------------+
            | Value                 | Reason                                                                                |
            +-----------------------+---------------------------------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to edit server details.                        |
            +-----------------------+---------------------------------------------------------------------------------------+
            | ``NotPrivileged``     | You provided ``discoverable`` or ``flags`` parameters and you wasn't privileged user. |
            +-----------------------+---------------------------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+----------------------------------------------------------------+
            | Value        | Reason                                                         |
            +--------------+----------------------------------------------------------------+
            | ``NotFound`` | One of these:                                                  |
            |              |                                                                |
            |              | - The server was not found.                                    |
            |              | - One of channels in one of provided categories was not found. |
            +--------------+----------------------------------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`.Server`
            The newly updated server.
        """
        return await self.state.http.edit_server(
            self.id,
            name=name,
            description=description,
            icon=icon,
            banner=banner,
            categories=categories,
            system_messages=system_messages,
            flags=flags,
            discoverable=discoverable,
            analytics=analytics,
        )

    async def join(self) -> Server:
        """|coro|

        Joins the server.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+-------------------------------------------+
            | Value              | Reason                                    |
            +--------------------+-------------------------------------------+
            | ``IsBot``          | The current token belongs to bot account. |
            +--------------------+-------------------------------------------+
            | ``TooManyServers`` | You're participating in too many servers. |
            +--------------------+-------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +------------+----------------------------+
            | Value      | Reason                     |
            +------------+----------------------------+
            | ``Banned`` | You're banned from server. |
            +------------+----------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+------------------------------------------+
            | Value        | Reason                                   |
            +--------------+------------------------------------------+
            | ``NotFound`` | The invite/channel/server was not found. |
            +--------------+------------------------------------------+
        :class:`Conflict`
            Possible values for :attr:`~HTTPException.type`:

            +---------------------+--------------------------------+
            | Value               | Reason                         |
            +---------------------+--------------------------------+
            | ``AlreadyInServer`` | The user is already in server. |
            +---------------------+--------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`.Server`
            The server you just joined.
        """
        server = await self.state.http.accept_invite(self.id)
        return server  # type: ignore

    async def leave(self, *, silent: typing.Optional[bool] = None) -> None:
        """|coro|

        Leaves a server if not owner, or deletes otherwise.

        Parameters
        ----------
        silent: Optional[:class:`bool`]
            Whether to silently leave server or not.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+-----------------------------------------+
            | Value              | Reason                                  |
            +--------------------+-----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid.  |
            +--------------------+-----------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+---------------------------+
            | Value        | Reason                    |
            +--------------+---------------------------+
            | ``NotFound`` | The server was not found. |
            +--------------+---------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """
        return await self.state.http.leave_server(self.id, silent=silent)

    async def mark_server_as_read(self) -> None:
        """|coro|

        Marks all channels in a server as read.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +-----------+-------------------------------------------+
            | Value     | Reason                                    |
            +-----------+-------------------------------------------+
            | ``IsBot`` | The current token belongs to bot account. |
            +-----------+-------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+-----------------------------------------+
            | Value              | Reason                                  |
            +--------------------+-----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid.  |
            +--------------------+-----------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+---------------------------+
            | Value        | Reason                    |
            +--------------+---------------------------+
            | ``NotFound`` | The server was not found. |
            +--------------+---------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """

        return await self.state.http.mark_server_as_read(self.id)

    async def report(
        self,
        reason: ContentReportReason,
        *,
        additional_context: typing.Optional[str] = None,
    ) -> None:
        """|coro|

        Report a server to the instance moderation team.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        reason: :class:`.ContentReportReason`
            The reason for reporting.
        additional_context: Optional[:class:`str`]
            The additional context for moderation team. Can be only up to 1000 characters.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------------+---------------------------------------+
            | Value                    | Reason                                |
            +--------------------------+---------------------------------------+
            | ``CannotReportYourself`` | You tried to report your own server. |
            +--------------------------+--------------------------------------+
            | ``FailedValidation``     | The payload was invalid.             |
            +--------------------------+--------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+---------------------------+
            | Value        | Reason                    |
            +--------------+---------------------------+
            | ``NotFound`` | The server was not found. |
            +--------------+---------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """

        return await self.state.http.report_server(self.id, reason, additional_context=additional_context)

    async def set_role_permissions(
        self,
        role: ULIDOr[BaseRole],
        *,
        allow: Permissions = Permissions.none(),
        deny: Permissions = Permissions.none(),
    ) -> Server:
        """|coro|

        Sets permissions for the specified server role.

        You must have :attr:`~Permissions.manage_permissions` to do this.

        Parameters
        ----------
        role: ULIDOr[:class:`.BaseRole`]
            The role.
        allow: :class:`.Permissions`
            The permissions to allow for the specified role.
        deny: :class:`.Permissions`
            The permissions to deny for the specified role.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------------------+--------------------------------------------------------------------------------------+
            | Value                            | Reason                                                                               |
            +----------------------------------+--------------------------------------------------------------------------------------+
            | ``CannotGiveMissingPermissions`` | Your new provided permissions contained permissions you didn't have.                 |
            +----------------------------------+--------------------------------------------------------------------------------------+
            | ``NotElevated``                  | Rank of your top role is higher than rank of role you're trying to set override for. |
            +----------------------------------+--------------------------------------------------------------------------------------+
            | ``MissingPermission``            | You do not have the proper permissions to edit permissions for this role.            |
            +----------------------------------+--------------------------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+--------------------------------+
            | Value        | Reason                         |
            +--------------+--------------------------------+
            | ``NotFound`` | The server/role was not found. |
            +--------------+--------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`.Server`
            The updated server with new permissions.
        """
        return await self.state.http.set_server_permissions_for_role(self.id, role, allow=allow, deny=deny)

    async def set_default_permissions(self, permissions: Permissions) -> Server:
        """|coro|

        Sets default permissions for everyone in a server.

        You must have :attr:`~Permissions.manage_permissions` to do this.

        Parameters
        ----------
        permissions: :class:`.Permissions`
            The new permissions.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------------------+-------------------------------------------------------------------------------------+
            | Value                            | Reason                                                                              |
            +----------------------------------+-------------------------------------------------------------------------------------+
            | ``CannotGiveMissingPermissions`` | Your new provided permissions contained permissions you didn't have.                |
            +----------------------------------+-------------------------------------------------------------------------------------+
            | ``MissingPermission``            | You do not have the proper permissions to edit default permissions for this server. |
            +----------------------------------+-------------------------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+----------------------------+
            | Value        | Reason                     |
            +--------------+----------------------------+
            | ``NotFound`` | The channel was not found. |
            +--------------+----------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`.Server`
            The newly updated server.
        """

        return await self.state.http.set_default_server_permissions(self.id, permissions)

    async def subscribe(self) -> None:
        """|coro|

        Subscribes to this server.
        """
        await self.state.shard.subscribe_to(self.id)

    async def unban(self, user: ULIDOr[BaseUser]) -> None:
        """|coro|

        Unbans a user from the server.

        You must have :attr:`~Permissions.ban_members` to do this.

        Parameters
        ----------
        user: ULIDOr[:class:`.BaseUser`]
            The user to unban from the server.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+-----------------------------------------+
            | Value              | Reason                                  |
            +--------------------+-----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid.  |
            +--------------------+-----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+----------------------------------------------------------+
            | Value                 | Reason                                                   |
            +-----------------------+----------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to unban members. |
            +-----------------------+----------------------------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """

        return await self.state.http.unban(self.id, user)


@define(slots=True)
class PartialServer(BaseServer):
    """Represents a partial server on Revolt.

    Unmodified fields will have ``UNDEFINED`` value.
    """

    name: UndefinedOr[str] = field(repr=True, kw_only=True)
    """UndefinedOr[:class:`str`]: The new server's name."""

    owner_id: UndefinedOr[str] = field(repr=True, kw_only=True)
    """UndefinedOr[:class:`str`]: The new user's ID who owns this server."""

    description: UndefinedOr[typing.Optional[str]] = field(repr=True, kw_only=True)
    """UndefinedOr[Optional[:class:`str`]]: The new server's description."""

    channel_ids: UndefinedOr[list[str]] = field(repr=True, kw_only=True)
    """UndefinedOr[List[:class:`str`]]: The server's channels now."""

    categories: UndefinedOr[typing.Optional[list[Category]]] = field(repr=True, kw_only=True)
    """UndefinedOr[Optional[List[:class:`.Category`]]]: The server's categories now."""

    system_messages: UndefinedOr[typing.Optional[SystemMessageChannels]] = field(repr=True, kw_only=True)
    """UndefinedOr[Optional[:class:`.SystemMessageChannels`]]: The new server's system message assignments."""

    raw_default_permissions: UndefinedOr[int] = field(repr=True, kw_only=True)
    """UndefinedOr[:class:`int`]: The raw value of new default permissions for everyone."""

    internal_icon: UndefinedOr[typing.Optional[StatelessAsset]] = field(repr=True, kw_only=True)
    """UndefinedOr[Optional[:class:`.StatelessAsset`]]: The new server's icon, if any."""

    internal_banner: UndefinedOr[typing.Optional[StatelessAsset]] = field(repr=True, kw_only=True)
    """UndefinedOr[Optional[:class:`.StatelessAsset`]]: The new server's banner, if any."""

    raw_flags: UndefinedOr[int] = field(repr=True, kw_only=True)
    """UndefinedOr[:class:`int`]: The new server's flags raw value."""

    discoverable: UndefinedOr[bool] = field(repr=True, kw_only=True)
    """UndefinedOr[:class:`bool`]: Whether the server is publicly discoverable."""

    analytics: UndefinedOr[bool] = field(repr=True, kw_only=True)
    """UndefinedOr[:class:`bool`]: Whether the server activity is being analyzed in real-time."""

    @property
    def default_permissions(self) -> UndefinedOr[Permissions]:
        """UndefinedOr[:class:`.Permissions`]: The new default permissions for everyone."""
        if self.raw_default_permissions is UNDEFINED:
            return self.raw_default_permissions
        ret = _new_permissions(Permissions)
        ret.value = self.raw_default_permissions
        return ret

    @property
    def flags(self) -> UndefinedOr[ServerFlags]:
        """UndefinedOr[:class:`.ServerFlags`]: The new server's flags."""
        if self.raw_flags is UNDEFINED:
            return self.raw_flags
        ret = _new_server_flags(ServerFlags)
        ret.value = self.raw_flags
        return ret

    @property
    def icon(self) -> UndefinedOr[typing.Optional[Asset]]:
        """UndefinedOr[Optional[:class:`.Asset`]]: The stateful server icon."""
        return self.internal_icon and self.internal_icon.attach_state(self.state, 'icons')

    @property
    def banner(self) -> UndefinedOr[typing.Optional[Asset]]:
        """UndefinedOr[Optional[:class:`.Asset`]]: The stateful server banner."""
        return self.internal_banner and self.internal_banner.attach_state(self.state, 'banners')


def sort_member_roles(
    target_roles: list[str],
    /,
    *,
    safe: bool = True,
    server_roles: dict[str, Role],
) -> list[Role]:
    """Sorts the member roles.

    Parameters
    ----------
    target_roles: List[:class:`str`]
        The IDs of roles to sort (:attr:`.Member.roles`).
    safe: :class:`bool`
        Whether to raise exception or not if role is missing in cache.
    server_roles: Dict[:class:`str`, :class:`.Role`]
        The mapping of role IDs to role objects (:attr:`.Server.roles`).

    Raises
    ------
    NoData
        The role is not found in cache.

    Returns
    -------
    List[:class:`.Role`]
        The sorted result.
    """
    if not safe:
        return sorted(
            (server_roles[tr] for tr in target_roles if tr in server_roles),
            key=lambda role: role.rank,
            reverse=True,
        )
    try:
        return sorted(
            (server_roles[tr] for tr in target_roles),
            key=lambda role: role.rank,
            reverse=True,
        )
    except KeyError as ke:
        raise NoData(ke.args[0], 'role')


def calculate_server_permissions(
    target_roles: list[Role],
    target_timeout: typing.Optional[datetime],
    /,
    *,
    default_permissions: Permissions,
    can_publish: bool = True,
    can_receive: bool = True,
) -> Permissions:
    """Calculates the permissions in :class:`.Server` scope.

    Parameters
    ----------
    target_roles: List[:class:`.Role`]
        The target member's roles. Should be empty list if calculating against :class:`.User`,
        and ``pyvolt.sort_member_roles(member.roles, server_roles=server.roles)``
        for member.
    target_timeout: Optional[:class:`~datetime.datetime`]
        The target timeout, if applicable (:attr:`.Member.timed_out_until`).
    default_permissions: :class:`Permissions`
        The default channel permissions (:attr:`.Server.default_permissions`).
    can_publish: :class:`bool`
        Whether the member can send voice data. Defaults to ``True``.
    can_receive: :class:`bool`
        Whether the member can receive voice data. Defaults to ``True``.

    Returns
    -------
    :class:`.Permissions`
        The calculated permissions.
    """
    result = default_permissions.copy()

    for role in target_roles:
        result |= role.permissions.allow
        result &= ~role.permissions.deny

    if target_timeout is not None and target_timeout <= utils.utcnow():
        result.send_messages = False

    if not can_publish:
        result.speak = False

    if not can_receive:
        result.listen = False

    return result


@define(slots=True)
class Server(BaseServer):
    """Represents a server on Revolt."""

    owner_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The user's ID who owns this server."""

    name: str = field(repr=True, kw_only=True)
    """:class:`str`: The server's name."""

    description: typing.Optional[str] = field(repr=True, kw_only=True)
    """Optional[:class:`str`]: The server's description."""

    internal_channels: tuple[typing.Literal[True], list[str]] | tuple[typing.Literal[False], list[ServerChannel]] = (
        field(repr=True, kw_only=True)
    )

    categories: typing.Optional[list[Category]] = field(repr=True, kw_only=True)
    """Optional[List[:class:`.Category`]]: The server's categories."""

    system_messages: typing.Optional[SystemMessageChannels] = field(repr=True, kw_only=True)
    """Optional[:class:`.SystemMessageChannels`]: The configuration for sending system event messages."""

    roles: dict[str, Role] = field(repr=True, kw_only=True)
    """Dict[:class:`str`, :class:`.Role`]: The server's roles."""

    raw_default_permissions: int = field(repr=True, kw_only=True)
    """:class:`int`: The raw value of default permissions for everyone."""

    internal_icon: typing.Optional[StatelessAsset] = field(repr=True, kw_only=True)
    """Optional[:class:`.StatelessAsset`]: The stateless server's icon."""

    internal_banner: typing.Optional[StatelessAsset] = field(repr=True, kw_only=True)
    """Optional[:class:`.StatelessAsset`]: The stateless server's banner."""

    raw_flags: int = field(repr=True, kw_only=True)
    """:class:`int`: The server's flags raw value."""

    nsfw: bool = field(repr=True, kw_only=True)
    """:class:`bool`: Whether the server is flagged as not safe for work."""

    analytics: bool = field(repr=True, kw_only=True)
    """:class:`bool`: Whether the server activity is being analyzed in real-time."""

    discoverable: bool = field(repr=True, kw_only=True)
    """:class:`bool`: Whether the server is publicly discoverable."""

    def get_channel(self, channel_id: str, /) -> typing.Optional[ServerChannel]:
        """Retrieves a server channel from cache.

        Parameters
        ----------
        channel_id: :class:`str`
            The channel ID.

        Returns
        -------
        Optional[:class:`.ServerChannel`]
            The channel or ``None`` if not found.
        """
        cache = self.state.cache
        if not cache:
            return

        from .channel import ServerChannel

        channel = cache.get_channel(channel_id, caching._USER_REQUEST)
        if channel and isinstance(channel, ServerChannel) and (channel.server_id == self.id or channel.server_id == ''):
            return channel

        if not self.internal_channels[0]:
            for ch in self.internal_channels[1]:
                t: ServerChannel = ch  # type: ignore
                if t.id == channel_id:
                    return t

    @property
    def icon(self) -> typing.Optional[Asset]:
        """Optional[:class:`.Asset`]: The server icon."""
        return self.internal_icon and self.internal_icon.attach_state(self.state, 'icons')

    @property
    def banner(self) -> typing.Optional[Asset]:
        """Optional[:class:`.Asset`]: The server banner."""
        return self.internal_banner and self.internal_banner.attach_state(self.state, 'banners')

    @property
    def channel_ids(self) -> list[str]:
        """List[:class:`str`]: The IDs of channels within this server."""
        if self.internal_channels[0]:
            return self.internal_channels[1]  # type: ignore
        else:
            return [channel.id for channel in self.internal_channels[1]]  # type: ignore

    @property
    def channels(self) -> list[ServerChannel]:
        """List[:class:`ServerChannel`]: The channels within this server."""

        if not self.internal_channels[0]:
            return self.internal_channels[1]  # type: ignore

        cache = self.state.cache
        if cache is None:
            return []

        from .channel import TextChannel, VoiceChannel

        channels = []
        for channel_id in self.internal_channels[1]:
            id: str = channel_id  # type: ignore
            channel = cache.get_channel(id, caching._USER_REQUEST)

            if channel:
                if channel.__class__ not in (
                    TextChannel,
                    VoiceChannel,
                ) or not isinstance(channel, (TextChannel, VoiceChannel)):
                    raise TypeError(f'Cache have given us incorrect channel type: {channel.__class__!r}')
                channels.append(channel)
        return channels

    @property
    def default_permissions(self) -> Permissions:
        """:class:`.Permissions`: The default permissions for everyone."""
        ret = _new_permissions(Permissions)
        ret.value = self.raw_default_permissions
        return ret

    @property
    def flags(self) -> ServerFlags:
        """:class:`.ServerFlags`: The server's flags."""
        ret = _new_server_flags(ServerFlags)
        ret.value = self.raw_flags
        return ret

    def is_verified(self) -> bool:
        """:class:`bool`: Whether the server is verified."""
        return self.flags.verified

    def is_official(self) -> bool:
        """:class:`bool`: Whether the server is ran by Revolt team."""
        return self.flags.official

    def locally_update(self, data: PartialServer, /) -> None:
        """Locally updates server with provided data.

        .. warning::
            This is called by library internally to keep cache up to date.
            You likely want to use :meth:`.BaseServer.edit` method instead.
        """
        if data.owner_id is not UNDEFINED:
            self.owner_id = data.owner_id
        if data.name is not UNDEFINED:
            self.name = data.name
        if data.description is not UNDEFINED:
            self.description = data.description
        if data.channel_ids is not UNDEFINED:
            self.internal_channels = (True, data.channel_ids)
        if data.categories is not UNDEFINED:
            self.categories = data.categories or []
        if data.system_messages is not UNDEFINED:
            self.system_messages = data.system_messages
        if data.raw_default_permissions is not UNDEFINED:
            self.raw_default_permissions = data.raw_default_permissions
        if data.internal_icon is not UNDEFINED:
            self.internal_icon = data.internal_icon
        if data.internal_banner is not UNDEFINED:
            self.internal_banner = data.internal_banner
        if data.raw_flags is not UNDEFINED:
            self.raw_flags = data.raw_flags
        if data.discoverable is not UNDEFINED:
            self.discoverable = data.discoverable
        if data.analytics is not UNDEFINED:
            self.analytics = data.analytics

    def permissions_for(
        self,
        member: typing.Union[Member, User],
        /,
        *,
        safe: bool = True,
        with_ownership: bool = True,
        include_timeout: bool = True,
    ) -> Permissions:
        """Calculate permissions for given member.

        Parameters
        ----------
        member: Union[:class:`.Member`, :class:`.User`]
            The member to calculate permissions for.
        safe: :class:`bool`
            Whether to raise exception or not if role is missing in cache.
        with_ownership: :class:`bool`
            Whether to account for ownership.
        include_timeout: :class:`bool`
            Whether to account for timeout.

        Raises
        ------
        NoData
            The role is not found in cache.

        Returns
        -------
        :class:`Permissions`
            The calculated permissions.
        """

        if with_ownership and member.id == self.owner_id:
            return Permissions.all()

        if isinstance(member, User):
            return calculate_server_permissions([], None, default_permissions=self.default_permissions)

        return calculate_server_permissions(
            sort_member_roles(member.roles, safe=safe, server_roles=self.roles),
            member.timed_out_until if include_timeout else None,
            default_permissions=self.default_permissions,
            can_publish=member.can_publish,
            can_receive=member.can_receive,
        )

    def prepare_cached(self) -> list[ServerChannel]:
        """List[:class:`.ServerChannel`]: Prepares the server to be cached."""
        if not self.internal_channels[0]:
            channels = self.internal_channels[1]
            self.internal_channels = (True, self.channel_ids)
            return channels  # type: ignore
        return []

    def upsert_role(self, role: typing.Union[PartialRole, Role], /) -> None:
        """Locally upserts role into :attr:`Server.roles` mapping.

        .. warning::
            This is called by library internally to keep cache up to date.
            You likely want to use :meth:`BaseServer.create_role` or :meth:`BaseRole.edit` instead.

        Parameters
        ----------
        role: Union[:class:`.PartialRole`, :class:`.Role`]
            The role to upsert.
        """
        if isinstance(role, PartialRole):
            self.roles[role.id].locally_update(role)
        else:
            self.roles[role.id] = role


@define(slots=True)
class Ban:
    """Represents a server ban on Revolt."""

    server_id: str = field(repr=False, kw_only=True)
    """:class:`str`: The server's ID."""

    user_id: str = field(repr=False, kw_only=True)
    """:class:`str`: The user's ID that was banned."""

    reason: typing.Optional[str] = field(repr=False, kw_only=True)
    """Optional[:class:`str`]: The ban's reason."""

    user: typing.Optional[DisplayUser] = field(repr=False, kw_only=True)
    """Optional[:class:`.DisplayUser`]: The user that was banned."""

    def __hash__(self) -> int:
        return hash((self.server_id, self.user_id))

    def __eq__(self, other: object, /) -> bool:
        return (
            self is other
            or isinstance(other, Ban)
            and (self.server_id == other.server_id and self.user_id == other.user_id)
        )


@define(slots=True)
class BaseMember:
    """Represents a Revolt base member to a :class:`Server`."""

    state: State = field(repr=False, kw_only=True)
    """:class:`.State`: State that controls this member."""

    server_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The server's ID the member in."""

    _user: typing.Union[User, str] = field(repr=True, kw_only=True, alias='_user')

    def get_user(self) -> typing.Optional[User]:
        """Optional[:class:`.User`]: Grabs the user from cache."""
        if isinstance(self._user, User):
            return self._user
        cache = self.state.cache
        if not cache:
            return None
        return cache.get_user(self._user, caching._USER_REQUEST)

    def __eq__(self, other: object, /) -> bool:
        return (
            self is other
            or (isinstance(other, BaseMember) and self.id == other.id and self.server_id == other.server_id)
            or isinstance(other, BaseUser)
            and self.id == other.id
        )

    def __hash__(self) -> int:
        return hash((self.server_id, self.id))

    def __str__(self) -> str:
        user = self.get_user()
        return str(user) if user else ''

    @property
    def id(self) -> str:
        """:class:`str`: The member's user ID."""
        return self._user.id if isinstance(self._user, User) else self._user

    @property
    def user(self) -> User:
        """:class:`.User`: The member user."""
        user = self.get_user()
        if user is None:
            raise NoData(self.id, 'member user')
        return user

    @property
    def display_name(self) -> typing.Optional[str]:
        """Optional[:class:`str`]: The user display name."""
        user = self.get_user()
        if user is not None:
            return user.display_name

    @property
    def badges(self) -> UserBadges:
        """:class:`.UserBadges`: The user badges."""
        user = self.get_user()
        if user is None:
            return UserBadges.none()
        return user.badges

    @property
    def status(self) -> typing.Optional[UserStatus]:
        """Optional[:class:`.UserStatus`]: The current user's status."""
        user = self.get_user()
        if user is not None:
            return user.status

    @property
    def flags(self) -> UserFlags:
        """:class:`.UserFlags`: The user flags."""
        user = self.get_user()
        if user is None:
            return UserFlags.none()
        return user.flags

    @property
    def privileged(self) -> bool:
        """:class:`bool`: Whether this user is privileged."""
        user = self.get_user()
        if user is None:
            return False
        return user.privileged

    @property
    def bot(self) -> typing.Optional[BotUserMetadata]:
        """Optional[:class:`.BotUserMetadata`]: The information about the bot."""
        user = self.get_user()
        if user is not None:
            return user.bot

    @property
    def relationship(self) -> RelationshipStatus:
        """:class:`.RelationshipStatus`: The current session user's relationship with this user."""
        user = self.get_user()
        if user is None:
            return RelationshipStatus.none
        return user.relationship

    @property
    def online(self) -> bool:
        """:class:`bool`: Whether this user is currently online."""
        user = self.get_user()
        if user is None:
            return False
        return user.online

    async def ban(self, *, reason: typing.Optional[str] = None) -> Ban:
        """|coro|

        Bans a user from the server.

        You must have :attr:`~Permissions.ban_members` to do this.

        Parameters
        ----------
        reason: Optional[:class:`str`]
            The ban reason. Can be only up to 1024 characters long.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------------+--------------------------------+
            | Value                    | Reason                         |
            +--------------------------+--------------------------------+
            | ``CannotRemoveYourself`` | You tried to ban yourself.     |
            +--------------------------+--------------------------------+
            | ``FailedValidation``     | The payload was invalid.       |
            +--------------------------+--------------------------------+
            | ``InvalidOperation``     | You tried to ban server owner. |
            +--------------------------+--------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------------------+-------------------------------------------------------------------------------------+
            | Value                            | Reason                                                                              |
            +----------------------------------+-------------------------------------------------------------------------------------+
            | ``NotElevated``                  | Rank of your top role is higher than rank of top role of user you're trying to ban. |
            +----------------------------------+-------------------------------------------------------------------------------------+
            | ``MissingPermission``            | You do not have the proper permissions to ban members.                              |
            +----------------------------------+-------------------------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+--------------------------------+
            | Value        | Reason                         |
            +--------------+--------------------------------+
            | ``NotFound`` | The server/user was not found. |
            +--------------+--------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`.Ban`
            The created ban.
        """

        return await self.state.http.ban(self.server_id, self.id, reason=reason)

    async def edit(
        self,
        *,
        nick: UndefinedOr[typing.Optional[str]] = UNDEFINED,
        avatar: UndefinedOr[typing.Optional[ResolvableResource]] = UNDEFINED,
        roles: UndefinedOr[typing.Optional[list[ULIDOr[BaseRole]]]] = UNDEFINED,
        timeout: UndefinedOr[typing.Optional[typing.Union[datetime, timedelta, float, int]]] = UNDEFINED,
        can_publish: UndefinedOr[typing.Optional[bool]] = UNDEFINED,
        can_receive: UndefinedOr[typing.Optional[bool]] = UNDEFINED,
        voice: UndefinedOr[ULIDOr[typing.Union[TextChannel, VoiceChannel]]] = UNDEFINED,
    ) -> Member:
        """|coro|

        Edits the member.

        Parameters
        ----------
        nick: UndefinedOr[Optional[:class:`str`]]
            The member's new nick. Use ``None`` to remove the nickname.
        avatar: UndefinedOr[Optional[:class:`ResolvableResource`]]
            The member's new avatar. Use ``None`` to remove the avatar. You can only change your own server avatar.
        roles: UndefinedOr[Optional[List[:class:`BaseRole`]]]
            The member's new list of roles. This *replaces* the roles.
        timeout: UndefinedOr[Optional[Union[:class:`datetime`, :class:`timedelta`, :class:`float`, :class:`int`]]]
            The duration/date the member's timeout should expire, or ``None`` to remove the timeout.
            This must be a timezone-aware datetime object. Consider using :func:`utils.utcnow()`.
        can_publish: UndefinedOr[Optional[:class:`bool`]]
            Whether the member should send voice data.
        can_receive: UndefinedOr[Optional[:class:`bool`]]
            Whether the member should receive voice data.
        voice: UndefinedOr[ULIDOr[Union[:class:`DMChannel`, :class:`GroupChannel`, :class:`TextChannel`, :class:`VoiceChannel`]]]
            The voice channel to move the member to.

        Returns
        -------
        :class:`.Member`
            The newly updated member.
        """
        return await self.state.http.edit_member(
            self.server_id,
            self.id,
            nick=nick,
            avatar=avatar,
            roles=roles,
            timeout=timeout,
            can_publish=can_publish,
            can_receive=can_receive,
            voice=voice,
        )

    async def kick(self) -> None:
        """|coro|

        Kicks a member from the server.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------------+---------------------------------+
            | Value                    | Reason                          |
            +--------------------------+---------------------------------+
            | ``CannotRemoveYourself`` | You tried to kick yourself.     |
            +--------------------------+---------------------------------+
            | ``InvalidOperation``     | You tried to kick server owner. |
            +--------------------------+---------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------------------+-------------------------------------------------------------------------------------+
            | Value                            | Reason                                                                              |
            +----------------------------------+-------------------------------------------------------------------------------------+
            | ``NotElevated``                  | Rank of your top role is higher than rank of top role of user you're trying to ban. |
            +----------------------------------+-------------------------------------------------------------------------------------+
            | ``MissingPermission``            | You do not have the proper permissions to ban members.                              |
            +----------------------------------+-------------------------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+--------------------------------+
            | Value        | Reason                         |
            +--------------+--------------------------------+
            | ``NotFound`` | The server/user was not found. |
            +--------------+--------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """
        return await self.state.http.kick_member(self.server_id, self.id)


@define(slots=True)
class PartialMember(BaseMember):
    """Represents a partial Revolt member to a :class:`Server`.

    Unmodified fields will have :data:`.UNDEFINED` value.
    """

    nick: UndefinedOr[typing.Optional[str]] = field(repr=True, kw_only=True)
    """UndefinedOr[Optional[:class:`str`]]: The new member's nick."""

    internal_server_avatar: UndefinedOr[typing.Optional[StatelessAsset]] = field(repr=True, kw_only=True)
    """UndefinedOr[Optional[:class:`.StatelessAsset`]]: The new member's avatar."""

    roles: UndefinedOr[list[str]] = field(repr=True, kw_only=True)
    """UndefinedOr[List[:class:`str`]]: The new member's roles."""

    timed_out_until: UndefinedOr[typing.Optional[datetime]] = field(repr=True, kw_only=True)
    """UndefinedOr[Optional[:class:`~datetime.datetime`]]: When member's time out expires now."""

    can_publish: UndefinedOr[typing.Optional[bool]] = field(repr=True, kw_only=True)
    """UndefinedOr[Optional[:class:`bool`]]: Whether the member can send voice data now."""

    can_receive: UndefinedOr[typing.Optional[bool]] = field(repr=True, kw_only=True)
    """UndefinedOr[Optional[:class:`bool`]]: Whether the member can receive voice data now."""

    @property
    def server_avatar(self) -> UndefinedOr[typing.Optional[Asset]]:
        """UndefinedOr[Optional[:class:`.Asset`]]: The member's avatar on server."""
        return self.internal_server_avatar and self.internal_server_avatar.attach_state(self.state, 'avatars')


@define(slots=True)
class Member(BaseMember):
    """Represents a Revolt member to a :class:`.Server`."""

    joined_at: datetime = field(repr=True, kw_only=True)
    """:class:`~datetime.datetime`: When the member joined the server."""

    nick: typing.Optional[str] = field(repr=True, kw_only=True)
    """Optional[:class:`str`]: The member's nick."""

    internal_server_avatar: typing.Optional[StatelessAsset] = field(repr=True, kw_only=True)
    """Optional[:class:`.StatelessAsset`]: The member's avatar on server."""

    roles: list[str] = field(repr=True, kw_only=True)
    """List[:class:`str`]: The member's roles."""

    timed_out_until: typing.Optional[datetime] = field(repr=True, kw_only=True)
    """Optional[:class:`~datetime.datetime`]: The timestamp this member is timed out until."""

    can_publish: bool = field(repr=True, kw_only=True)
    """:class:`bool`: Whether the member can send voice data."""

    can_receive: bool = field(repr=True, kw_only=True)
    """:class:`bool`: Whether the member can receive voice data."""

    def locally_update(self, data: PartialMember, /) -> None:
        """Locally updates member with provided data.

        .. warning::
            This is called by library internally to keep cache up to date.

        Parameters
        ----------
        data: :class:`.PartialMember`
            The data to update member with.
        """
        if data.nick is not UNDEFINED:
            self.nick = data.nick
        if data.internal_server_avatar is not UNDEFINED:
            self.internal_server_avatar = data.internal_server_avatar
        if data.roles is not UNDEFINED:
            self.roles = data.roles or []
        if data.can_publish is not UNDEFINED:
            self.can_publish = True if data.can_publish is None else data.can_publish
        if data.can_receive is not UNDEFINED:
            self.can_receive = True if data.can_receive is None else data.can_receive

    @property
    def server_avatar(self) -> typing.Optional[Asset]:
        """Optional[:class:`.Asset`]: The member's avatar on server."""
        return self.internal_server_avatar and self.internal_server_avatar.attach_state(self.state, 'avatars')


@define(slots=True)
class MemberList:
    """A member list of a server."""

    members: list[Member] = field(repr=True, kw_only=True)
    """List[:class:`.Member`]: The members in server."""

    users: list[User] = field(repr=True, kw_only=True)
    """List[:class:`.User`]: The users."""


__all__ = (
    'Category',
    'SystemMessageChannels',
    'BaseRole',
    'PartialRole',
    'Role',
    'BaseServer',
    'PartialServer',
    'sort_member_roles',
    'calculate_server_permissions',
    'Server',
    'Ban',
    'BaseMember',
    'PartialMember',
    'Member',
    'MemberList',
)
