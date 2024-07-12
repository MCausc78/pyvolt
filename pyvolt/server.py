from __future__ import annotations

from attrs import define, field
from datetime import datetime
from enum import IntFlag, StrEnum
import typing as t

from . import (
    cache as caching,
    cdn,
    core,
    utils,
)
from .base import Base
from .errors import NoData
from .permissions import Permissions, PermissionOverride
from .safety_reports import ContentReportReason
from .state import State
from .user import DisplayUser, User

if t.TYPE_CHECKING:
    from . import raw
    from .channel import ChannelType, ServerTextChannel, VoiceChannel, ServerChannel


class ServerFlags(IntFlag):
    NONE = 0

    VERIFIED = 1 << 0
    """Whether the server is verified."""

    OFFICIAL = 1 << 1
    """Whether the server is ran by Revolt team."""


class Category:
    """Representation of channel category on Revolt server."""

    id: core.ULID
    """Unique ID for this category."""

    title: str
    """Title for this category."""

    channels: list[core.ULID]
    """Channel in this category."""

    __slots__ = ("id", "title", "channels")

    def __init__(
        self,
        id: core.ResolvableULID,
        title: str,
        channels: list[core.ResolvableULID],
    ) -> None:
        self.id = core.resolve_ulid(id)
        self.title = title
        self.channels = [core.resolve_ulid(channel) for channel in channels]

    def build(self) -> raw.Category:
        return {
            "id": self.id,
            "title": self.title,
            "channels": t.cast("list[str]", self.channels),
        }


class SystemMessageChannels:
    """System message channel assignments."""

    user_joined: core.ULID | None
    """ID of channel to send user join messages in."""

    user_left: core.ULID | None
    """ID of channel to send user left messages in."""

    user_kicked: core.ULID | None
    """ID of channel to send user kicked messages in."""

    user_banned: core.ULID | None
    """ID of channel to send user banned messages in."""

    __slots__ = ("user_joined", "user_left", "user_kicked", "user_banned")

    def __init__(
        self,
        *,
        user_joined: core.ResolvableULID | None = None,
        user_left: core.ResolvableULID | None = None,
        user_kicked: core.ResolvableULID | None = None,
        user_banned: core.ResolvableULID | None = None,
    ) -> None:
        self.user_joined = (
            None if user_joined is None else core.resolve_ulid(user_joined)
        )
        self.user_left = None if user_left is None else core.resolve_ulid(user_left)
        self.user_kicked = (
            None if user_kicked is None else core.resolve_ulid(user_kicked)
        )
        self.user_banned = (
            None if user_banned is None else core.resolve_ulid(user_banned)
        )

    def build(self) -> raw.SystemMessageChannels:
        d: raw.SystemMessageChannels = {}
        if self.user_joined is not None:
            d["user_joined"] = self.user_joined
        if self.user_left is not None:
            d["user_left"] = self.user_left
        if self.user_kicked is not None:
            d["user_kicked"] = self.user_kicked
        if self.user_banned is not None:
            d["user_banned"] = self.user_banned
        return d


@define()
class BaseRole(Base):
    """Base representation of a server role."""

    server_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)

    async def delete(self) -> None:
        """|coro|

        Delete a server role.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to delete the role.
        :class:`APIError`
            Deleting the role failed.
        """
        return await self.state.http.delete_role(self.server_id, self.id)

    async def edit(
        self,
        *,
        name: core.UndefinedOr[str] = core.UNDEFINED,
        colour: core.UndefinedOr[str | None] = core.UNDEFINED,
        hoist: core.UndefinedOr[bool] = core.UNDEFINED,
        rank: core.UndefinedOr[int] = core.UNDEFINED,
    ) -> Role:
        """|coro|

        Edit a role.

        Parameters
        ----------
        name: :class:`UndefinedOr`[:class:`str`]
            New role name. Should be between 1 and 32 chars long.
        colour: :class:`UndefinedOr`[:class:`str` | `None`]
            New role colour.
        hoist: :class:`UndefinedOr`[:class:`bool`]
            Whether this role should be displayed separately.
        rank: :class:`UndefinedOr`[:class:`int`]
            Ranking position. Smaller values take priority.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to edit the role.
        :class:`APIError`
            Editing the role failed.
        """
        return await self.state.http.edit_role(
            self.server_id, self.id, name=name, colour=colour, hoist=hoist, rank=rank
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
        :class:`Forbidden`
            You do not have permissions to set role permissions on the server.
        :class:`APIError`
            Setting permissions failed.
        """
        return await self.state.http.set_role_server_permissions(
            self.server_id, self.id, allow=allow, deny=deny
        )


@define(slots=True)
class PartialRole(BaseRole):
    """Partial representation of a server role."""

    name: core.UndefinedOr[str] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The new role name."""

    permissions: core.UndefinedOr[PermissionOverride] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The permissions available to this role."""

    colour: core.UndefinedOr[str | None] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """New colour used for this. This can be any valid CSS colour."""

    hoist: core.UndefinedOr[bool] = field(repr=True, hash=True, kw_only=True, eq=True)
    """Whether this role should be shown separately on the member sidebar."""

    rank: core.UndefinedOr[int] = field(repr=True, hash=True, kw_only=True, eq=True)
    """New ranking of this role."""

    def into_full(self) -> Role | None:
        """Tries transform this partial role into full object. This is useful when caching role."""
        if (
            core.is_defined(self.name)
            and core.is_defined(self.permissions)
            and core.is_defined(self.hoist)
            and core.is_defined(self.rank)
        ):
            colour = None if not core.is_defined(self.colour) else self.colour
            return Role(
                state=self.state,
                id=self.id,
                server_id=self.server_id,
                name=self.name,
                permissions=self.permissions,
                colour=colour,
                hoist=self.hoist,
                rank=self.rank,
            )


@define(slots=True)
class Role(BaseRole):
    """Representation of a server role."""

    name: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """Role name."""

    permissions: PermissionOverride = field(repr=True, hash=True, kw_only=True, eq=True)
    """Permissions available to this role."""

    colour: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """Colour used for this. This can be any valid CSS colour."""

    hoist: bool = field(repr=True, hash=True, kw_only=True, eq=True)
    """Whether this role should be shown separately on the member sidebar."""

    rank: int = field(repr=True, hash=True, kw_only=True, eq=True)
    """Ranking of this role."""

    def _update(self, data: PartialRole) -> None:
        if core.is_defined(data.name):
            self.name = data.name
        if core.is_defined(data.permissions):
            self.permissions = data.permissions
        if core.is_defined(data.colour):
            self.colour = data.colour
        if core.is_defined(data.hoist):
            self.hoist = data.hoist
        if core.is_defined(data.rank):
            self.rank = data.rank


@define(slots=True)
class BaseServer(Base):
    """Base representation of a server on Revolt."""

    async def add_bot(
        self,
        bot: core.ResolvableULID,
    ) -> None:
        """|coro|

        Adds a bot to a server.
        """
        return await self.state.http.invite_bot(bot, server=self.id)

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
        :class:`Forbidden`
            You do not have permissions to create the channel.
        :class:`APIError`
            Creating the channel failed.
        """
        return await self.state.http.create_channel(
            self.id, type=type, name=name, description=description, nsfw=nsfw
        )

    async def create_text_channel(
        self, name: str, *, description: str | None = None, nsfw: bool | None = None
    ) -> ServerTextChannel:
        """|coro|

        Create a new text channel within this server.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to create the channel.
        :class:`APIError`
            Creating the channel failed.
        """
        from .channel import ChannelType

        type = ChannelType.TEXT
        channel = await self.create_channel(
            type=type, name=name, description=description, nsfw=nsfw
        )
        return channel  # type: ignore

    async def create_voice_channel(
        self, name: str, *, description: str | None = None, nsfw: bool | None = None
    ) -> VoiceChannel:
        """|coro|

        Create a new voice channel within this server.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to create the channel.
        :class:`APIError`
            Creating the channel failed.
        """
        from .channel import ChannelType

        type = ChannelType.VOICE
        channel = await self.create_channel(
            type=type, name=name, description=description, nsfw=nsfw
        )
        return channel  # type: ignore

    async def create_role(self, *, name: str, rank: int | None = None) -> Role:
        """|coro|

        Creates a new server role.

        Parameters
        ----------
        name: :class:`str` | `None`
            Role name. Should be between 1 and 32 chars long.
        rank: :class:`int` | `None`
            Ranking position. Smaller values take priority.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to create the role.
        :class:`APIError`
            Creating the role failed.
        """
        return await self.state.http.create_role(self.id, name=name, rank=rank)

    async def delete(self) -> None:
        """|coro|

        Deletes a server if owner otherwise leaves.
        """
        return await self.state.http.delete_server(self.id)

    async def edit(
        self,
        *,
        name: core.UndefinedOr[str] = core.UNDEFINED,
        description: core.UndefinedOr[str | None] = core.UNDEFINED,
        icon: core.UndefinedOr[str | None] = core.UNDEFINED,
        banner: core.UndefinedOr[str | None] = core.UNDEFINED,
        categories: core.UndefinedOr[list[Category] | None] = core.UNDEFINED,
        system_messages: core.UndefinedOr[
            SystemMessageChannels | None
        ] = core.UNDEFINED,
        flags: core.UndefinedOr[ServerFlags] = core.UNDEFINED,
        discoverable: core.UndefinedOr[bool] = core.UNDEFINED,
        analytics: core.UndefinedOr[bool] = core.UNDEFINED,
    ) -> Server:
        """|coro|

        Edit a server.

        Parameters
        ----------
        name: :class:`UndefinedOr`[:class:`str`]
            New server name. Should be between 1 and 32 chars long.
        description: :class:`UndefinedOr`[:class:`str` | `None`]
            New server description. Can be 1024 chars maximum long.
        icon: :class:`UndefinedOr`[:class:`str` | `None`]
            New server icon. Pass attachment ID given by Autumn.
        banner: :class:`UndefinedOr`[:class:`str` | `None`]
            New server banner. Pass attachment ID given by Autumn.
        categories: :class:`UndefinedOr`[:class:`list`[:class:`Category`] | `None`]
            New category structure for this server.
        system_messsages: :class:`UndefinedOr`[:class:`SystemMessageChannels` | `None`]
            New system message channels configuration.
        flags: :class:`UndefinedOr`[:class:`ServerFlags`]
            Bitfield of server flags. Can be passed only if you're privileged user.
        discoverable: :class:`UndefinedOr`[:class:`bool`]
            Whether this server is public and should show up on [Revolt Discover](https://rvlt.gg). Can be passed only if you're privileged user.
        analytics: :class:`UndefinedOr`[:class:`bool`]
            Whether analytics should be collected for this server. Must be enabled in order to show up on [Revolt Discover](https://rvlt.gg).

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to edit the server.
        :class:`APIError`
            Editing the server failed.
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
        APIError
            Accepting the invite failed.
        """
        server = await self.state.http.accept_invite(self.id)
        return server  # type: ignore

    async def leave(self, *, leave_silently: bool | None = None) -> None:
        """|coro|

        Deletes a server if owner otherwise leaves.

        Parameters
        ----------
        leave_silently: :class:`bool`
            Whether to not send a leave message.
        """
        return await self.state.http.leave_server(
            self.id, leave_silently=leave_silently
        )

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
        :class:`APIError`
            You're trying to self-report, or reporting the server failed.
        """
        return await self.state.http.report_server(
            self.id, reason, additional_context=additional_context
        )

    async def set_role_permissions(
        self,
        role: core.ResolvableULID,
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
        :class:`Forbidden`
            You do not have permissions to set role permissions on the server.
        :class:`APIError`
            Setting permissions failed.
        """
        return await self.state.http.set_role_server_permissions(
            self.id, role, allow=allow, deny=deny
        )

    async def set_default_permissions(
        self, permissions: Permissions | PermissionOverride, /
    ) -> Server:
        """|coro|

        Sets permissions for the default role in this server.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to set default permissions on the server.
        :class:`APIError`
            Setting permissions failed.
        """
        return await self.state.http.set_default_role_permissions(self.id, permissions)

    async def subscribe(self) -> None:
        """|coro|

        Subscribes to this server.
        """
        await self.state.shard.subscribe_to(self.id)


@define(slots=True)
class PartialServer(BaseServer):
    """Partial representation of a server on Revolt."""

    name: core.UndefinedOr[str] = field(repr=True, hash=True, kw_only=True, eq=True)
    owner_id: core.UndefinedOr[core.ULID] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    description: core.UndefinedOr[str | None] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    channel_ids: core.UndefinedOr[list[core.ULID]] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    categories: core.UndefinedOr[list[Category] | None] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    system_messages: core.UndefinedOr[SystemMessageChannels | None] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    default_permissions: core.UndefinedOr[Permissions] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    internal_icon: core.UndefinedOr[cdn.StatelessAsset | None] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    internal_banner: core.UndefinedOr[cdn.StatelessAsset | None] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    flags: core.UndefinedOr[ServerFlags] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    discoverable: core.UndefinedOr[bool] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    analytics: core.UndefinedOr[bool] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )

    @property
    def icon(self) -> core.UndefinedOr[cdn.Asset | None]:
        return self.internal_icon and self.internal_icon._stateful(self.state, "icons")

    @property
    def banner(self) -> core.UndefinedOr[cdn.Asset | None]:
        return self.internal_banner and self.internal_banner._stateful(
            self.state, "banners"
        )


def _sort_roles(
    target_roles: list[core.ULID],
    /,
    *,
    safe: bool,
    server_roles: dict[core.ULID, Role],
) -> list[Role]:
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
        raise NoData(ke.args[0], "role")


def _calculate_server_permissions(
    roles: list[Role],
    target_timeout: datetime | None,
    *,
    default_permissions: Permissions,
) -> Permissions:
    result = default_permissions.value

    for role in roles:
        result |= role.permissions.allow.value
        result &= ~role.permissions.deny.value

    if target_timeout is not None and target_timeout > utils.utcnow():
        result &= ~Permissions.SEND_MESSAGE.value

    return Permissions(result)


@define(slots=True)
class Server(BaseServer):
    """Representation of a server on Revolt."""

    owner_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    """The user ID of the owner."""

    name: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The name of the server."""

    description: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The description for the server."""

    internal_channels: (
        tuple[t.Literal[True], list[core.ULID]]
        | tuple[t.Literal[False], list[ServerChannel]]
    ) = field(repr=True, hash=True, kw_only=True, eq=True)

    categories: list[Category] | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The categories for this server."""

    system_messages: SystemMessageChannels | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The configuration for sending system event messages."""

    roles: dict[core.ULID, Role] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The roles for this server."""

    default_permissions: Permissions = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The default set of server and channel permissions."""

    internal_icon: cdn.StatelessAsset | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The stateless server icon."""

    internal_banner: cdn.StatelessAsset | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The stateless server banner."""

    flags: ServerFlags = field(repr=True, hash=True, kw_only=True, eq=True)
    """The server flags."""

    nsfw: bool = field(repr=True, hash=True, kw_only=True, eq=True)
    """Whether this server is flagged as not safe for work."""

    analytics: bool = field(repr=True, hash=True, kw_only=True, eq=True)
    """Whether to enable analytics."""

    discoverable: bool = field(repr=True, hash=True, kw_only=True, eq=True)
    """Whether this server should be publicly discoverable."""

    def _update(self, data: PartialServer) -> None:
        if core.is_defined(data.owner_id):
            self.owner_id = data.owner_id
        if core.is_defined(data.name):
            self.name = data.name
        if core.is_defined(data.description):
            self.description = data.description
        if core.is_defined(data.channel_ids):
            self.internal_channels = (True, data.channel_ids)
        if core.is_defined(data.categories):
            self.categories = data.categories or []
        if core.is_defined(data.system_messages):
            self.system_messages = data.system_messages
        if core.is_defined(data.default_permissions):
            self.default_permissions = data.default_permissions
        if core.is_defined(data.internal_icon):
            self.internal_icon = data.internal_icon
        if core.is_defined(data.internal_banner):
            self.internal_banner = data.internal_banner
        if core.is_defined(data.flags):
            self.flags = data.flags
        if core.is_defined(data.discoverable):
            self.discoverable = data.discoverable
        if core.is_defined(data.analytics):
            self.analytics = data.analytics

    def _role_update_full(self, data: PartialRole | Role) -> None:
        if isinstance(data, PartialRole):
            self.roles[data.id]._update(data)
        else:
            self.roles[data.id] = data

    def _role_update(self, data: PartialRole) -> None:
        try:
            role = self.roles[data.id]
        except KeyError:
            role = data.into_full()
            if role:
                self.roles[role.id] = role
        else:
            role._update(data)

    @property
    def icon(self) -> cdn.Asset | None:
        """The server icon."""
        return self.internal_icon and self.internal_icon._stateful(self.state, "icons")

    @property
    def banner(self) -> cdn.Asset | None:
        """The server banner."""
        return self.internal_banner and self.internal_banner._stateful(
            self.state, "banners"
        )

    @property
    def channel_ids(self) -> list[core.ULID]:
        """IDs of channels within this server."""
        if self.internal_channels[0]:
            return self.internal_channels[1]  # type: ignore
        else:
            return [channel.id for channel in self.internal_channels[1]]  # type: ignore

    @property
    def channels(self) -> list[ServerChannel]:
        """The channels within this server."""

        if not self.internal_channels[0]:
            return self.internal_channels[1]  # type: ignore
        cache = self.state.cache
        if not cache:
            return []
        channels = []
        for channel_id in self.internal_channels[1]:
            id: core.ULID = channel_id  # type: ignore
            channel = cache.get_channel(id, caching._USER_REQUEST)

            if channel:
                if channel.__class__ not in (
                    ServerTextChannel,
                    VoiceChannel,
                ) or not isinstance(channel, (ServerTextChannel, VoiceChannel)):
                    raise TypeError(
                        f"Cache have given us incorrect channel type: {channel.__class__!r}"
                    )
                channels.append(channel)
        return channels

    @property
    def members(self) -> list[Member]:
        """The members list of this server."""
        cache = self.state.cache
        if not cache:
            return []
        return cache.get_all_server_members_of(self.id, caching._USER_REQUEST) or []

    @property
    def members_mapping(self) -> dict[core.ULID, Member]:
        """The members mapping of this server."""
        cache = self.state.cache
        if not cache:
            return {}
        return cache.get_server_members_mapping_of(self.id, caching._USER_REQUEST) or {}

    def is_verified(self) -> bool:
        """:class:`bool`: Whether the server is verified."""
        return ServerFlags.VERIFIED in self.flags

    def is_official(self) -> bool:
        """:class:`bool`: Whether the server is ran by Revolt team."""
        return ServerFlags.OFFICIAL in self.flags

    def permissions_for(
        self,
        member: Member,
        /,
        *,
        safe: bool = True,
    ) -> Permissions:
        """Calculate permissions for given member."""

        if member.id == self.owner_id:
            return Permissions.ALL

        return _calculate_server_permissions(
            _sort_roles(member.roles, safe=safe, server_roles=self.roles),
            member.timeout,
            default_permissions=self.default_permissions,
        )

    def _ensure_cached(self) -> None:
        if not self.internal_channels[0]:
            self.internal_channels = (True, self.channel_ids)


@define(slots=True)
class Ban:
    """Representation of a server ban on Revolt."""

    server_id: core.ULID = field(repr=False, hash=False, kw_only=True, eq=False)
    """The server ID."""

    user_id: core.ULID = field(repr=False, hash=False, kw_only=True, eq=False)
    """The user ID that was banned."""

    reason: str | None = field(repr=False, hash=False, kw_only=True, eq=False)
    """Reason for ban creation."""

    user: DisplayUser | None = field(repr=False, hash=False, kw_only=True, eq=False)
    """The user that was banned."""


@define(slots=True)
class BaseMember:
    """Base representation of a member of a server on Revolt."""

    state: State = field(repr=False, hash=False, kw_only=True, eq=False)
    """State that controls this member."""

    server_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    """ID of the server that member is on."""

    _user: User | core.ULID = field(
        repr=True, hash=True, kw_only=True, eq=True, alias="_user"
    )

    @property
    def id(self) -> core.ULID:
        """The member's user ID."""
        return self._user.id if isinstance(self._user, User) else self._user


@define(slots=True)
class PartialMember(BaseMember):
    """Partial representation of a member of a server on Revolt."""

    nick: core.UndefinedOr[str | None] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    internal_avatar: core.UndefinedOr[cdn.StatelessAsset | None] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    roles: core.UndefinedOr[list[core.ULID]] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    timeout: core.UndefinedOr[datetime | None] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )

    def avatar(self) -> core.UndefinedOr[cdn.Asset | None]:
        return self.internal_avatar and self.internal_avatar._stateful(
            self.state, "avatars"
        )


@define(slots=True)
class Member(BaseMember):
    """Representation of a member of a server on Revolt."""

    joined_at: datetime = field(repr=True, hash=True, kw_only=True, eq=True)
    """Time at which this user joined the server."""

    nick: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The member's nick."""

    internal_avatar: cdn.StatelessAsset | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The member's avatar on server."""

    roles: list[core.ULID] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The member's roles."""

    timeout: datetime | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The timestamp this member is timed out until."""

    def _update(self, data: PartialMember) -> None:
        if core.is_defined(data.nick):
            self.nick = data.nick
        if core.is_defined(data.internal_avatar):
            self.internal_avatar = data.internal_avatar
        if core.is_defined(data.roles):
            self.roles = data.roles or []
        if core.is_defined(data.timeout):
            self.timeout = data.timeout

    @property
    def avatar(self) -> cdn.Asset | None:
        """The member's avatar on server."""
        return self.internal_avatar and self.internal_avatar._stateful(
            self.state, "avatars"
        )

    async def ban(self, *, reason: str | None = None) -> Ban:
        """|coro|

        Ban a user.

        Parameters
        ----------
        reason: :class:`str` | `None`
            Ban reason. Should be between 1 and 1024 chars long.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to ban the user.
        :class:`APIError`
            Banning the user failed.
        """
        return await self.state.http.ban_user(self.server_id, self.id, reason=reason)

    async def kick(self) -> None:
        """|coro|

        Removes a member from the server.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to kick the member.
        :class:`APIError`
            Kicking the member failed.
        """
        return await self.state.http.kick_member(self.server_id, self.id)


@define(slots=True)
class MemberList:
    """A member list of a server."""

    members: list[Member] = field(repr=True, hash=True, kw_only=True, eq=True)
    users: list[User] = field(repr=True, hash=True, kw_only=True, eq=True)


class MemberRemovalIntention(StrEnum):
    LEAVE = "Leave"
    KICK = "Kick"
    BAN = "Ban"


__all__ = (
    "ServerFlags",
    "Category",
    "SystemMessageChannels",
    "BaseRole",
    "PartialRole",
    "Role",
    "BaseServer",
    "PartialServer",
    "_sort_roles",
    "_calculate_server_permissions",
    "Server",
    "Ban",
    "BaseMember",
    "PartialMember",
    "Member",
    "MemberList",
    "MemberRemovalIntention",
)
