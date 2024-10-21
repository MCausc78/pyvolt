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
    BotUserInfo,
    User,
)


if typing.TYPE_CHECKING:
    from collections.abc import Mapping

    from . import raw
    from .channel import (
        TextChannel,
        DMChannel,
        GroupChannel,
        ServerTextChannel,
        VoiceChannel,
        ServerChannel,
    )
    from .state import State


class Category:
    """Represents a category containing channels in Revolt server.

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
        self.channels: list[str] = [resolve_id(channel) for channel in channels]

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
        user_joined: ULIDOr[TextChannel] | None = None,
        user_left: ULIDOr[TextChannel] | None = None,
        user_kicked: ULIDOr[TextChannel] | None = None,
        user_banned: ULIDOr[TextChannel] | None = None,
    ) -> None:
        self.user_joined: str | None = None if user_joined is None else resolve_id(user_joined)
        self.user_left: str | None = None if user_left is None else resolve_id(user_left)
        self.user_kicked: str | None = None if user_kicked is None else resolve_id(user_kicked)
        self.user_banned: str | None = None if user_banned is None else resolve_id(user_banned)

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

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, BaseRole) and self.id == other.id

    async def delete(self) -> None:
        """|coro|

        Deletes the role.

        Raises
        ------
        Forbidden
            You do not have permissions to delete the role.
        HTTPException
            Deleting the role failed.
        """
        return await self.state.http.delete_role(self.server_id, self.id)

    async def edit(
        self,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        colour: UndefinedOr[str | None] = UNDEFINED,
        hoist: UndefinedOr[bool] = UNDEFINED,
        rank: UndefinedOr[int] = UNDEFINED,
    ) -> Role:
        """|coro|

        Edits the role.

        Parameters
        ----------
        name: :class:`UndefinedOr`[:class:`str`]
            New role name. Should be between 1 and 32 chars long.
        colour: :class:`UndefinedOr`[Optional[:class:`str`]]
            New role colour. This should be valid CSS colour.
        hoist: :class:`UndefinedOr`[:class:`bool`]
            Whether this role should be displayed separately.
        rank: :class:`UndefinedOr`[:class:`int`]
            The new ranking position. Smaller values take priority.

        Raises
        ------
        Forbidden
            You do not have permissions to edit the role.
        HTTPException
            Editing the role failed.

        Returns
        -------
        :class:`Role`
            The newly updated role.
        """
        return await self.state.http.edit_role(
            self.server_id,
            self.id,
            name=name,
            colour=colour,
            hoist=hoist,
            rank=rank,
        )

    async def set_permissions(
        self,
        *,
        allow: Permissions = Permissions.NONE,
        deny: Permissions = Permissions.NONE,
    ) -> Server:
        """|coro|

        Sets permissions for the specified role in the server.

        Parameters
        ----------
        allow: :class:`Permissions`
            New allow bit flags.
        deny: :class:`Permissions`
            New disallow bit flags.

        Raises
        ------
        Forbidden
            You do not have permissions to set role permissions on the server.
        HTTPException
            Setting permissions failed.
        """
        return await self.state.http.set_server_permissions_for_role(self.server_id, self.id, allow=allow, deny=deny)


@define(slots=True)
class PartialRole(BaseRole):
    """Represents a partial role for the server.

    Unmodified fields will have ``UNDEFINED`` value.
    """

    name: UndefinedOr[str] = field(repr=True, kw_only=True)
    """The new role's name."""

    permissions: UndefinedOr[PermissionOverride] = field(repr=True, kw_only=True)
    """The permissions available to this role."""

    color: UndefinedOr[str | None] = field(repr=True, kw_only=True)
    """New color used for this. This can be any valid CSS colour."""

    hoist: UndefinedOr[bool] = field(repr=True, kw_only=True)
    """Whether this role should be shown separately on the member sidebar."""

    rank: UndefinedOr[int] = field(repr=True, kw_only=True)
    """New ranking of this role."""

    def into_full(self) -> Role | None:
        """Optional[:class:`Role`]: Tries transform this partial role into full object. This is useful when caching role."""
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
    """The role's name."""

    permissions: PermissionOverride = field(repr=True, kw_only=True)
    """Permissions available to this role."""

    color: str | None = field(repr=True, kw_only=True)
    """The role's color. This is valid CSS color."""

    hoist: bool = field(repr=True, kw_only=True)
    """Whether this role should be shown separately on the member sidebar."""

    rank: int = field(repr=True, kw_only=True)
    """The role's rank."""

    def locally_update(self, data: PartialRole, /) -> None:
        """Locally updates role with provided data.

        .. warn::
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
    """Base representation of a server on Revolt."""

    def get_emoji(self, emoji_id: str, /) -> ServerEmoji | None:
        """Retrieves a server emoji from cache.

        Parameters
        ----------
        emoji_id: :class:`str`
            The emoji ID.

        Returns
        -------
        Optional[:class:`ServerEmoji`]
            The emoji or ``None`` if not found.
        """
        cache = self.state.cache
        if not cache:
            return
        emoji = cache.get_emoji(emoji_id, caching._USER_REQUEST)
        if emoji and isinstance(emoji, ServerEmoji) and emoji.server_id == self.id:
            return emoji

    def get_member(self, user_id: str, /) -> Member | None:
        """Retrieves a server member from cache.

        Parameters
        ----------
        user_id: :class:`str`
            The user ID.

        Returns
        -------
        Optional[:class:`Member`]
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
        """Mapping[:class:`str`, :class:`ServerEmoji`]: Returns all emojis of this server."""
        cache = self.state.cache
        if cache:
            return cache.get_server_emojis_mapping_of(self.id, caching._USER_REQUEST) or {}
        return {}

    @property
    def members(self) -> Mapping[str, Member]:
        """Mapping[:class:`str`, :class:`Member`]: Returns all members of this server."""
        cache = self.state.cache
        if cache:
            return cache.get_server_members_mapping_of(self.id, caching._USER_REQUEST) or {}
        return {}

    async def add_bot(
        self,
        bot: ULIDOr[BaseBot | BaseUser],
    ) -> None:
        """|coro|

        Adds a bot to a server.
        """
        return await self.state.http.invite_bot(bot, server=self.id)

    async def ban(self, user: str | BaseUser | BaseMember, *, reason: str | None = None) -> Ban:
        """|coro|

        Ban a user.

        Parameters
        ----------
        user: Union[:class:`str`, :class:`BaseUser`, :class:`BaseMember`]
            The user to ban.
        reason: Optional[:class:`str`]
            The ban reason. Should be between 1 and 1024 chars long.

        Raises
        ------
        Forbidden
            You do not have permissions to ban the user.
        HTTPException
            Banning the user failed.
        """
        return await self.state.http.ban(self.id, user, reason=reason)

    @typing.overload
    async def create_channel(
        self,
        *,
        type: None = ...,
        name: str,
        description: str | None = ...,
        nsfw: bool | None = ...,
    ) -> ServerTextChannel: ...

    @typing.overload
    async def create_channel(
        self,
        *,
        type: typing.Literal[ChannelType.text] = ...,
        name: str,
        description: str | None = ...,
        nsfw: bool | None = ...,
    ) -> ServerTextChannel: ...

    @typing.overload
    async def create_channel(
        self,
        *,
        type: typing.Literal[ChannelType.voice] = ...,
        name: str,
        description: str | None = ...,
        nsfw: bool | None = ...,
    ) -> VoiceChannel: ...

    async def create_channel(
        self,
        *,
        type: ChannelType | None = None,
        name: str,
        description: str | None = None,
        nsfw: bool | None = None,
    ) -> ServerChannel:
        """|coro|

        Create a new text or voice channel within this server.

        Raises
        ------
        Forbidden
            You do not have permissions to create the channel.
        HTTPException
            Creating the channel failed.
        """
        return await self.state.http.create_server_channel(
            self.id, type=type, name=name, description=description, nsfw=nsfw
        )

    async def create_text_channel(
        self, name: str, *, description: str | None = None, nsfw: bool | None = None
    ) -> ServerTextChannel:
        """|coro|

        Create a new text channel within this server.

        Raises
        ------
        Forbidden
            You do not have permissions to create the channel.
        HTTPException
            Creating the channel failed.
        """
        channel = await self.create_channel(type=ChannelType.text, name=name, description=description, nsfw=nsfw)
        return channel

    async def create_voice_channel(
        self, name: str, *, description: str | None = None, nsfw: bool | None = None
    ) -> VoiceChannel:
        """|coro|

        Create a new voice channel within this server.

        Raises
        ------
        Forbidden
            You do not have permissions to create the channel.
        HTTPException
            Creating the channel failed.
        """
        channel = await self.create_channel(type=ChannelType.voice, name=name, description=description, nsfw=nsfw)
        return channel

    async def create_role(self, *, name: str, rank: int | None = None) -> Role:
        """|coro|

        Creates a new server role.

        Parameters
        ----------
        name: :class:`str`
            The role name. Should be between 1 and 32 chars long.
        rank: Optional[:class:`int`]
            The ranking position. Smaller values take priority.

        Raises
        ------
        Forbidden
            You do not have permissions to create the role.
        HTTPException
            Creating the role failed.
        """
        return await self.state.http.create_role(self.id, name=name, rank=rank)

    async def delete(self) -> None:
        """|coro|

        Deletes the server if owner otherwise leaves.
        """
        return await self.state.http.delete_server(self.id)

    async def edit(
        self,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str | None] = UNDEFINED,
        icon: UndefinedOr[str | None] = UNDEFINED,
        banner: UndefinedOr[str | None] = UNDEFINED,
        categories: UndefinedOr[list[Category] | None] = UNDEFINED,
        system_messages: UndefinedOr[SystemMessageChannels | None] = UNDEFINED,
        flags: UndefinedOr[ServerFlags] = UNDEFINED,
        discoverable: UndefinedOr[bool] = UNDEFINED,
        analytics: UndefinedOr[bool] = UNDEFINED,
    ) -> Server:
        """|coro|

        Edits the server.

        Parameters
        ----------
        name: :class:`UndefinedOr`[:class:`str`]
            New server name. Should be between 1 and 32 chars long.
        description: :class:`UndefinedOr`[Optional[:class:`str`]]
            New server description. Can be 1024 chars maximum long.
        icon: :class:`UndefinedOr`[Optional[:class:`ResolvableResource`]]
            New server icon.
        banner: :class:`UndefinedOr`[Optional[:class:`ResolvableResource`]]
            New server banner.
        categories: :class:`UndefinedOr`[Optional[List[:class:`Category`]]]
            New category structure for this server.
        system_messsages: :class:`UndefinedOr`[Optional[:class:`SystemMessageChannels`]]
            New system message channels configuration.
        flags: :class:`UndefinedOr`[:class:`ServerFlags`]
            The new server flags. Can be passed only if you're privileged user.
        discoverable: :class:`UndefinedOr`[:class:`bool`]
            Whether this server is public and should show up on `Revolt Discover <https://rvlt.gg>`_. Can be passed only if you're privileged user.
        analytics: :class:`UndefinedOr`[:class:`bool`]
            Whether analytics should be collected for this server. Must be enabled in order to show up on `Revolt Discover <https://rvlt.gg>`_.

        Raises
        ------
        Forbidden
            You do not have permissions to edit the server.
        HTTPException
            Editing the server failed.

        Returns
        -------
        :class:`Server`
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

        Raises
        ------
        Forbidden
            You're banned.
        NotFound
            Either server is not discoverable, or it does not exist at all.
        HTTPException
            Accepting the invite failed.
        """
        server = await self.state.http.accept_invite(self.id)
        return server  # type: ignore

    async def leave(self, *, silent: bool | None = None) -> None:
        """|coro|

        Leaves a server if not owner otherwise deletes it.

        Parameters
        ----------
        silent: :class:`bool`
            Whether to not send a leave message.
        """
        return await self.state.http.leave_server(self.id, silent=silent)

    async def mark_server_as_read(self) -> None:
        """|coro|

        Mark all channels in a server as read.
        """
        return await self.state.http.mark_server_as_read(self.id)

    async def report(
        self,
        reason: ContentReportReason,
        *,
        additional_context: str | None = None,
    ) -> None:
        """|coro|

        Report a piece of content to the moderation team.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        HTTPException
            You're trying to self-report, or reporting the server failed.
        """
        return await self.state.http.report_server(self.id, reason, additional_context=additional_context)

    async def set_role_permissions(
        self,
        role: ULIDOr[BaseRole],
        *,
        allow: Permissions = Permissions.NONE,
        deny: Permissions = Permissions.NONE,
    ) -> Server:
        """|coro|

        Sets permissions for the specified role in the server.

        Parameters
        ----------
        allow: :class:`Permissions`
            New allow bit flags.
        deny: :class:`Permissions`
            New deny bit flags.

        Raises
        ------
        Forbidden
            You do not have permissions to set role permissions on the server.
        HTTPException
            Setting permissions failed.
        """
        return await self.state.http.set_server_permissions_for_role(self.id, role, allow=allow, deny=deny)

    async def set_default_permissions(self, permissions: Permissions, /) -> Server:
        """|coro|

        Sets permissions for the default role in this server.

        Raises
        ------
        Forbidden
            You do not have permissions to set default permissions on the server.
        HTTPException
            Setting permissions failed.
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

        Parameters
        ----------
        user: :class:`ULIDOr`[:class:`BaseUser`]
            The user to unban from the server.

        Raises
        ------
        Forbidden
            You do not have permissions to unban the user.
        HTTPException
            Unbanning the user failed.
        """
        return await self.state.http.unban(self.id, user)


@define(slots=True)
class PartialServer(BaseServer):
    """Represents a server on Revolt.

    Unmodified fields will have ``UNDEFINED`` value.
    """

    name: UndefinedOr[str] = field(repr=True, kw_only=True)
    owner_id: UndefinedOr[str] = field(repr=True, kw_only=True)
    description: UndefinedOr[str | None] = field(repr=True, kw_only=True)
    channel_ids: UndefinedOr[list[str]] = field(repr=True, kw_only=True)
    categories: UndefinedOr[list[Category] | None] = field(repr=True, kw_only=True)
    system_messages: UndefinedOr[SystemMessageChannels | None] = field(repr=True, kw_only=True)
    default_permissions: UndefinedOr[Permissions] = field(repr=True, kw_only=True)
    internal_icon: UndefinedOr[StatelessAsset | None] = field(repr=True, kw_only=True)
    internal_banner: UndefinedOr[StatelessAsset | None] = field(repr=True, kw_only=True)
    flags: UndefinedOr[ServerFlags] = field(repr=True, kw_only=True)
    discoverable: UndefinedOr[bool] = field(repr=True, kw_only=True)
    analytics: UndefinedOr[bool] = field(repr=True, kw_only=True)

    @property
    def icon(self) -> UndefinedOr[Asset | None]:
        """:class:`UndefinedOr`[Optional[:class:`Asset`]]: The stateful server icon."""
        return self.internal_icon and self.internal_icon._stateful(self.state, 'icons')

    @property
    def banner(self) -> UndefinedOr[Asset | None]:
        """:class:`UndefinedOr`[Optional[:class:`Asset`]]: The stateful server banner."""
        return self.internal_banner and self.internal_banner._stateful(self.state, 'banners')


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
        The IDs of roles to sort (:attr:`Member.roles`).
    safe: :class:`bool`
        Whether to raise exception or not if role is missing in cache.
    server_roles: Dict[:class:`str`, :class:`Role`]
        The mapping of role IDs to role objects (:attr:`Server.roles`).

    Raises
    ------
    NoData
        The role is not found in cache.

    Returns
    -------
    List[:class:`Role`]
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
    target_timeout: datetime | None,
    /,
    *,
    default_permissions: Permissions,
    can_publish: bool = True,
    can_receive: bool = True,
) -> Permissions:
    """Calculates the permissions in :class:`Server` scope.

    Parameters
    ----------
    target_roles: List[:class:`Role`]
        The target member's roles. Should be empty list if calculating against :class:`User`,
        and ``pyvolt.sort_member_roles(member.roles, server_roles=server.roles)``
        for member.
    target_timeout: Optional[:class:`~datetime.datetime`]
        The target timeout, if applicable (:attr:`Member.timed_out_until`).
    default_permissions: :class:`Permissions`
        The default channel permissions (:attr:`Server.default_permissions`).
    can_publish: :class:`bool`
        Whether the member can send voice data. Defaults to ``True``.
    can_receive: :class:`bool`
        Whether the member can receive voice data. Defaults to ``True``.

    Returns
    -------
    :class:`Permissions`
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
    """The user ID of the owner."""

    name: str = field(repr=True, kw_only=True)
    """The name of the server."""

    description: str | None = field(repr=True, kw_only=True)
    """The description for the server."""

    internal_channels: tuple[typing.Literal[True], list[str]] | tuple[typing.Literal[False], list[ServerChannel]] = (
        field(repr=True, kw_only=True)
    )

    categories: list[Category] | None = field(repr=True, kw_only=True)
    """The categories for this server."""

    system_messages: SystemMessageChannels | None = field(repr=True, kw_only=True)
    """The configuration for sending system event messages."""

    roles: dict[str, Role] = field(repr=True, kw_only=True)
    """The roles for this server."""

    default_permissions: Permissions = field(repr=True, kw_only=True)
    """The default set of server and channel permissions."""

    internal_icon: StatelessAsset | None = field(repr=True, kw_only=True)
    """The stateless server icon."""

    internal_banner: StatelessAsset | None = field(repr=True, kw_only=True)
    """The stateless server banner."""

    flags: ServerFlags = field(repr=True, kw_only=True)
    """The server flags."""

    nsfw: bool = field(repr=True, kw_only=True)
    """Whether this server is flagged as not safe for work."""

    analytics: bool = field(repr=True, kw_only=True)
    """Whether to enable analytics."""

    discoverable: bool = field(repr=True, kw_only=True)
    """Whether this server should be publicly discoverable."""

    def get_channel(self, channel_id: str, /) -> ServerChannel | None:
        """Retrieves a server channel from cache.

        Parameters
        ----------
        channel_id: :class:`str`
            The channel ID.

        Returns
        -------
        Optional[:class:`ServerChannel`]
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
    def icon(self) -> Asset | None:
        """Optional[:class:`Asset`]: The server icon."""
        return self.internal_icon and self.internal_icon._stateful(self.state, 'icons')

    @property
    def banner(self) -> Asset | None:
        """Optional[:class:`Asset`]: The server banner."""
        return self.internal_banner and self.internal_banner._stateful(self.state, 'banners')

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
        if not cache:
            return []
        from .channel import ServerTextChannel, VoiceChannel

        channels = []
        for channel_id in self.internal_channels[1]:
            id: str = channel_id  # type: ignore
            channel = cache.get_channel(id, caching._USER_REQUEST)

            if channel:
                if channel.__class__ not in (
                    ServerTextChannel,
                    VoiceChannel,
                ) or not isinstance(channel, (ServerTextChannel, VoiceChannel)):
                    raise TypeError(f'Cache have given us incorrect channel type: {channel.__class__!r}')
                channels.append(channel)
        return channels

    def is_verified(self) -> bool:
        """:class:`bool`: Whether the server is verified."""
        return self.flags.verified

    def is_official(self) -> bool:
        """:class:`bool`: Whether the server is ran by Revolt team."""
        return self.flags.official

    def locally_update(self, data: PartialServer, /) -> None:
        """Locally updates server with provided data.

        .. warn::
            This is called by library internally to keep cache up to date.
            You likely want to use :meth:`.edit` instead.
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
        if data.default_permissions is not UNDEFINED:
            self.default_permissions = data.default_permissions
        if data.internal_icon is not UNDEFINED:
            self.internal_icon = data.internal_icon
        if data.internal_banner is not UNDEFINED:
            self.internal_banner = data.internal_banner
        if data.flags is not UNDEFINED:
            self.flags = data.flags
        if data.discoverable is not UNDEFINED:
            self.discoverable = data.discoverable
        if data.analytics is not UNDEFINED:
            self.analytics = data.analytics

    def permissions_for(
        self,
        member: Member,
        /,
        *,
        safe: bool = True,
        with_ownership: bool = True,
        include_timeout: bool = True,
    ) -> Permissions:
        """Calculate permissions for given member.

        Parameters
        ----------
        member: :class:`Member`
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

        return calculate_server_permissions(
            sort_member_roles(member.roles, safe=safe, server_roles=self.roles),
            member.timed_out_until if include_timeout else None,
            default_permissions=self.default_permissions,
            can_publish=member.can_publish,
            can_receive=member.can_receive,
        )

    def prepare_cached(self) -> list[ServerChannel]:
        """List[:class:`ServerChannel`]: Prepares the server to be cached."""
        if not self.internal_channels[0]:
            channels = self.internal_channels[1]
            self.internal_channels = (True, self.channel_ids)
            return channels  # type: ignore
        return []

    def upsert_role(self, data: PartialRole | Role, /) -> None:
        """Locally upserts role into :attr:`Server.roles` mapping.

        .. warn::
            This is called by library internally to keep cache up to date.
            You likely want to use :meth:`.create_role` or :meth:`BaseRole.edit` instead.

        Parameters
        ----------
        data: Union[:class:`PartialRole`, :class:`Role`]
            The role to upsert.
        """
        if isinstance(data, PartialRole):
            self.roles[data.id].locally_update(data)
        else:
            self.roles[data.id] = data


@define(slots=True)
class Ban:
    """Represents a server ban on Revolt."""

    server_id: str = field(repr=False, kw_only=True)
    """The server's ID."""

    user_id: str = field(repr=False, kw_only=True)
    """The user's ID that was banned."""

    reason: str | None = field(repr=False, kw_only=True)
    """The ban's reason."""

    user: DisplayUser | None = field(repr=False, kw_only=True)
    """The user that was banned."""

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
    """State that controls this member."""

    server_id: str = field(repr=True, kw_only=True)
    """The server's ID the member in."""

    _user: User | str = field(repr=True, kw_only=True, alias='_user')

    def get_user(self) -> User | None:
        """Optional[:class:`User`]: Grabs the user from cache."""
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
        """:class:`User`: The member user."""
        user = self.get_user()
        if not user:
            raise NoData(self.id, 'member user')
        return user

    @property
    def display_name(self) -> str | None:
        """Optional[:class:`str`]: The user display name."""
        user = self.get_user()
        if user:
            return user.display_name

    @property
    def badges(self) -> UserBadges:
        """:class:`UserBadges`: The user badges."""
        user = self.get_user()
        if user:
            return user.badges
        return UserBadges.NONE

    @property
    def status(self) -> UserStatus | None:
        """Optional[:class:`UserStatus`]: The current user's status."""
        user = self.get_user()
        if user:
            return user.status

    @property
    def flags(self) -> UserFlags:
        """Optional[:class:`UserFlags`]: The user flags."""
        user = self.get_user()
        if user:
            return user.flags
        return UserFlags.NONE

    @property
    def privileged(self) -> bool:
        """:class:`bool`: Whether this user is privileged."""
        user = self.get_user()
        if user:
            return user.privileged
        return False

    @property
    def bot(self) -> BotUserInfo | None:
        """Optional[:class:`BotUserInfo`]: The information about the bot."""
        user = self.get_user()
        if user:
            return user.bot

    @property
    def relationship(self) -> RelationshipStatus:
        """:class:`RelationshipStatus`: The current session user's relationship with this user."""
        user = self.get_user()
        if user:
            return user.relationship
        return RelationshipStatus.none

    @property
    def online(self) -> bool:
        """:class:`bool`: Whether this user is currently online."""
        user = self.get_user()
        if user:
            return user.online
        return False

    async def ban(self, *, reason: str | None = None) -> Ban:
        """|coro|

        Ban a user.

        Parameters
        ----------
        reason: Optional[:class:`str`]
            The ban reason. Must be between 1 and 1024 chars long.

        Raises
        ------
        Forbidden
            You do not have permissions to ban the user.
        HTTPException
            Banning the user failed.
        """
        return await self.state.http.ban(self.server_id, self.id, reason=reason)

    async def edit(
        self,
        *,
        nick: UndefinedOr[str | None] = UNDEFINED,
        avatar: UndefinedOr[ResolvableResource | None] = UNDEFINED,
        roles: UndefinedOr[list[ULIDOr[BaseRole]] | None] = UNDEFINED,
        timeout: UndefinedOr[datetime | timedelta | float | int | None] = UNDEFINED,
        can_publish: UndefinedOr[bool | None] = UNDEFINED,
        can_receive: UndefinedOr[bool | None] = UNDEFINED,
        voice: UndefinedOr[ULIDOr[DMChannel | GroupChannel | ServerTextChannel | VoiceChannel]] = UNDEFINED,
    ) -> Member:
        """|coro|

        Edits the member.

        Parameters
        ----------
        nick: :class:`UndefinedOr`[Optional[:class:`str`]]
            The member's new nick. Use ``None`` to remove the nickname.
        avatar: :class:`UndefinedOr`[Optional[:class:`ResolvableResource`]]
            The member's new avatar. Use ``None`` to remove the avatar. You can only change your own server avatar.
        roles: :class:`UndefinedOr`[Optional[List[:class:`BaseRole`]]]
            The member's new list of roles. This *replaces* the roles.
        timeout: :class:`UndefinedOr`[Optional[Union[:class:`datetime`, :class:`timedelta`, :class:`float`, :class:`int`]]]
            The duration/date the member's timeout should expire, or ``None`` to remove the timeout.
            This must be a timezone-aware datetime object. Consider using :func:`utils.utcnow()`.
        can_publish: :class:`UndefinedOr`[Optional[:class:`bool`]]
            Whether the member should send voice data.
        can_receive: :class:`UndefinedOr`[Optional[:class:`bool`]]
            Whether the member should receive voice data.
        voice: :class:`UndefinedOr`[ULIDOr[Union[:class:`DMChannel`, :class:`GroupChannel`, :class:`ServerTextChannel`, :class:`VoiceChannel`]]]
            The voice channel to move the member to.

        Returns
        -------
        :class:`Member`
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

        Removes a member from the server.

        Raises
        ------
        Forbidden
            You do not have permissions to kick the member.
        HTTPException
            Kicking the member failed.
        """
        return await self.state.http.kick_member(self.server_id, self.id)


@define(slots=True)
class PartialMember(BaseMember):
    """Represents a Revolt member to a :class:`Server`.

    Unmodified fields will have ``UNDEFINED`` value.
    """

    nick: UndefinedOr[str | None] = field(repr=True, kw_only=True)
    internal_server_avatar: UndefinedOr[StatelessAsset | None] = field(repr=True, kw_only=True)
    roles: UndefinedOr[list[str]] = field(repr=True, kw_only=True)
    timed_out_until: UndefinedOr[datetime | None] = field(repr=True, kw_only=True)
    can_publish: UndefinedOr[bool | None] = field(repr=True, kw_only=True)
    can_receive: UndefinedOr[bool | None] = field(repr=True, kw_only=True)

    def server_avatar(self) -> UndefinedOr[Asset | None]:
        """:class:`UndefinedOr`[Optional[:class:`Asset`]]: The member's avatar on server."""
        return self.internal_server_avatar and self.internal_server_avatar._stateful(self.state, 'avatars')


@define(slots=True)
class Member(BaseMember):
    """Represents a Revolt member to a :class:`Server`."""

    joined_at: datetime = field(repr=True, kw_only=True)
    """Time at which this user joined the server."""

    nick: str | None = field(repr=True, kw_only=True)
    """The member's nick."""

    internal_server_avatar: StatelessAsset | None = field(repr=True, kw_only=True)
    """The member's avatar on server."""

    roles: list[str] = field(repr=True, kw_only=True)
    """The member's roles."""

    timed_out_until: datetime | None = field(repr=True, kw_only=True)
    """The timestamp this member is timed out until."""

    can_publish: bool = field(repr=True, kw_only=True)
    """Whether the member can send voice data."""

    can_receive: bool = field(repr=True, kw_only=True)
    """Whether the member can receive voice data."""

    def locally_update(self, data: PartialMember) -> None:
        """Locally updates member with provided data.

        .. warn::
            This is called by library internally to keep cache up to date.

        Parameters
        ----------
        data: :class:`PartialMember`
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
    def server_avatar(self) -> Asset | None:
        """Optional[:class:`Asset`]: The member's avatar on server."""
        return self.internal_server_avatar and self.internal_server_avatar._stateful(self.state, 'avatars')


@define(slots=True)
class MemberList:
    """A member list of a server."""

    members: list[Member] = field(repr=True, kw_only=True)
    users: list[User] = field(repr=True, kw_only=True)


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
