from __future__ import annotations

import abc
from attrs import define, field
import contextlib
import typing

from . import (
    cache as caching,
    cdn,
    core,
)

from .base import Base
from .bot import BaseBot
from .enums import Enum
from .invite import Invite
from .permissions import (
    Permissions,
    PermissionOverride,
    UserPermissions,
    VIEW_ONLY_PERMISSIONS,
    DEFAULT_SAVED_MESSAGES_PERMISSIONS,
    DEFAULT_DM_PERMISSIONS,
)
from .server import BaseRole, Role, Server, Member
from .user import BaseUser, User

if typing.TYPE_CHECKING:
    from .message import (
        Reply,
        Interactions,
        Masquerade,
        SendableEmbed,
        MessageSort,
        BaseMessage,
        Message,
    )
    from .shard import Shard


class ChannelType(Enum):
    text = "Text"
    """Text channel."""

    voice = "Voice"
    """Voice channel."""


class Typing(contextlib.AbstractAsyncContextManager):
    shard: Shard
    channel_id: str

    def __init__(self, shard: Shard, channel_id: str) -> None:
        self.shard = shard
        self.channel_id = channel_id

    async def __aenter__(self) -> None:
        await self.shard.begin_typing(self.channel_id)

    async def __aexit__(self, exc_type, exc_value, tb) -> None:
        del exc_type
        del exc_value
        del tb
        await self.shard.end_typing(self.channel_id)
        return


class BaseChannel(Base, abc.ABC):
    """Representation of channel on Revolt."""

    def message(self, message: core.ULIDOr[BaseMessage]) -> BaseMessage:
        from .message import BaseMessage

        return BaseMessage(
            state=self.state, id=core.resolve_id(message), channel_id=self.id
        )

    async def close(self, *, silent: bool | None = None) -> None:
        """|coro|

        Deletes a server channel, leaves a group or closes a group.

        Parameters
        ----------
        silent: :class:`bool`
            Whether to not send message when leaving group.

        Raises
        ------
        Forbidden
            You do not have permissions to close the channel.
        HTTPException
            Closing the channel failed.
        """
        return await self.state.http.close_channel(self.id, silent=silent)

    async def edit(
        self,
        *,
        name: core.UndefinedOr[str] = core.UNDEFINED,
        description: core.UndefinedOr[str | None] = core.UNDEFINED,
        owner: core.UndefinedOr[core.ULIDOr[BaseUser]] = core.UNDEFINED,
        icon: core.UndefinedOr[str | None] = core.UNDEFINED,
        nsfw: core.UndefinedOr[bool] = core.UNDEFINED,
        archived: core.UndefinedOr[bool] = core.UNDEFINED,
        default_permissions: core.UndefinedOr[None] = core.UNDEFINED,
    ) -> Channel:
        """|coro|

        Edits the channel.

        Raises
        ------
        Forbidden
            You do not have permissions to edit the channel.
        HTTPException
            Editing the channel failed.
        """
        return await self.state.http.edit_channel(
            self.id,
            name=name,
            description=description,
            owner=owner,
            icon=icon,
            nsfw=nsfw,
            archived=archived,
            default_permissions=default_permissions,
        )

    async def join_call(self) -> str:
        """|coro|

        Asks the voice server for a token to join the call.

        Returns
        -------
        :class:`str`
            Token for authenticating with the voice server.

        Raises
        ------
        HTTPException
            Asking the token failed.
        """
        return await self.state.http.join_call(self.id)


@define(slots=True)
class PartialChannel(BaseChannel):
    """Partial representation of a channel on Revolt."""

    name: core.UndefinedOr[str] = field(repr=True, hash=True, kw_only=True, eq=True)
    owner_id: core.UndefinedOr[str] = field(repr=True, hash=True, kw_only=True, eq=True)
    description: core.UndefinedOr[str | None] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    internal_icon: core.UndefinedOr[cdn.StatelessAsset | None] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    nsfw: core.UndefinedOr[bool] = field(repr=True, hash=True, kw_only=True, eq=True)
    active: core.UndefinedOr[bool] = field(repr=True, hash=True, kw_only=True, eq=True)
    permissions: core.UndefinedOr[Permissions] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    role_permissions: core.UndefinedOr[dict[str, PermissionOverride]] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    default_permissions: core.UndefinedOr[PermissionOverride | None] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    last_message_id: core.UndefinedOr[str] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )


def _calculate_saved_messages_channel_permissions(
    perspective_id: str, user_id: str
) -> Permissions:
    if perspective_id == user_id:
        return DEFAULT_SAVED_MESSAGES_PERMISSIONS
    return Permissions.NONE


def _calculate_dm_channel_permissions(
    user_permissions: UserPermissions,
) -> Permissions:
    if user_permissions & UserPermissions.SEND_MESSAGE:
        return DEFAULT_DM_PERMISSIONS
    return VIEW_ONLY_PERMISSIONS


def _calculate_group_channel_permissions(
    perspective_id: str,
    *,
    group_owner_id: str,
    group_permissions: Permissions,
    group_recipients: list[str],
) -> Permissions:
    if perspective_id == group_owner_id:
        return Permissions.ALL
    elif perspective_id in group_recipients:
        return VIEW_ONLY_PERMISSIONS | group_permissions
    return Permissions.NONE


def _calculate_server_channel_permissions(
    initial_permissions: Permissions,
    roles: list[Role],
    /,
    *,
    default_permissions: PermissionOverride | None,
    role_permissions: dict[str, PermissionOverride],
) -> Permissions:
    result = initial_permissions.value

    if default_permissions:
        result |= default_permissions.allow.value
        result &= ~default_permissions.deny.value

    for role in roles:
        try:
            override = role_permissions[role.id]
            result |= override.allow.value
            result &= ~override.deny.value
        except KeyError:
            pass

    return Permissions(result)


@define(slots=True)
class TextChannel(BaseChannel):
    """A channel that can have messages."""

    def _update(self, data: PartialChannel) -> None:
        # PartialChannel has no fields that are related to SavedMessages yet
        pass

    def typing(self) -> Typing:
        """Returns an asynchronous context manager that allows you to send a typing indicator in channel for an indefinite period of time."""
        return Typing(self.state.shard, self.id)

    async def begin_typing(self) -> None:
        """Begins typing in channel, until `end_typing` is called."""
        return await self.state.shard.begin_typing(self.id)

    async def end_typing(self) -> None:
        """Ends typing in channel."""
        await self.state.shard.end_typing(self.id)

    async def pins(self) -> list[Message]:
        """|coro|

        Retrieves all messages that are currently pinned in the channel.

        Raises
        ------
        HTTPException
            Getting channel pins failed.
        """
        return await self.state.http.get_channel_pins(self.id)

    async def search(
        self,
        query: str,
        *,
        limit: int | None = None,
        before: core.ULIDOr[BaseMessage] | None = None,
        after: core.ULIDOr[BaseMessage] | None = None,
        sort: MessageSort | None = None,
        populate_users: bool | None = None,
    ) -> list[Message]:
        """|coro|

        Searches for messages within the given parameters.

        Parameters
        ----------
        query: :class:`str`
            Full-text search query. See [MongoDB documentation](https://docs.mongodb.com/manual/text-search/#-text-operator) for more information.
        limit: :class:`int`
            Maximum number of messages to fetch.
        before: :class:`core.ResolvableULID`
            Message ID before which messages should be fetched.
        after: :class:`core.ResolvableULID`
            Message ID after which messages should be fetched.
        sort: :class:`messages.MessageSort`
            Sort used for retrieving messages.
        populate_users: :class:`bool`
            Whether to populate user (and member, if server channel) objects.

        Returns
        -------
        :class:`list`[:class:`messages.Message`]
            The messages matched.

        Raises
        ------
        Forbidden
            You do not have permissions to search messages.
        HTTPException
            Searching messages failed.
        """
        return await self.state.http.search_for_messages(
            self.id,
            query,
            limit=limit,
            before=before,
            after=after,
            sort=sort,
            populate_users=populate_users,
        )

    async def send(
        self,
        content: str | None = None,
        *,
        nonce: str | None = None,
        attachments: list[cdn.ResolvableResource] | None = None,
        replies: list[Reply | core.ULIDOr[BaseMessage]] | None = None,
        embeds: list[SendableEmbed] | None = None,
        masquerade: Masquerade | None = None,
        interactions: Interactions | None = None,
        silent: bool | None = None,
    ) -> Message:
        """|coro|

        Sends a message to the given channel.
        You must have `SendMessages` permission.

        Returns
        -------
        :class:`Message`
            The message sent.

        Forbidden
            You do not have permissions to send messages.
        HTTPException
            Sending the message failed.
        """
        return await self.state.http.send_message(
            self.id,
            content,
            nonce=nonce,
            attachments=attachments,
            replies=replies,
            embeds=embeds,
            masquerade=masquerade,
            interactions=interactions,
            silent=silent,
        )


@define(slots=True)
class SavedMessagesChannel(TextChannel):
    """Personal "Saved Notes" channel which allows users to save messages."""

    user_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """ID of the user this channel belongs to."""

    def _update(self, data: PartialChannel) -> None:
        # PartialChannel has no fields that are related to SavedMessages yet
        pass

    def permissions_for(self, perspective: User | Member, /) -> Permissions:
        return _calculate_saved_messages_channel_permissions(
            perspective.id, self.user_id
        )


@define(slots=True)
class DMChannel(TextChannel):
    """Direct message channel between two users."""

    active: bool = field(repr=True, hash=True, kw_only=True, eq=True)
    """Whether this DM channel is currently open on both sides."""

    recipient_ids: tuple[str, str] = field(repr=True, hash=True, kw_only=True, eq=True)
    """2-tuple of user IDs participating in DM."""

    last_message_id: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """ID of the last message sent in this channel."""

    def _update(self, data: PartialChannel) -> None:
        if core.is_defined(data.active):
            self.active = data.active
        if core.is_defined(data.last_message_id):
            self.last_message_id = data.last_message_id


@define(slots=True)
class GroupChannel(TextChannel):
    """Group channel between 1 or more participants."""

    name: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """Display name of the channel."""

    owner_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """User ID of the owner of the group."""

    description: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """Channel description."""

    _recipients: (
        tuple[typing.Literal[True], list[str]]
        | tuple[typing.Literal[False], list[User]]
    ) = field(repr=True, hash=True, eq=True, alias="internal_recipients")

    internal_icon: cdn.StatelessAsset | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The stateless group icon."""

    last_message_id: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """ID of the last message sent in this channel."""

    permissions: Permissions | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """Permissions assigned to members of this group. (does not apply to the owner of the group)"""

    nsfw: bool = field(repr=True, hash=True, kw_only=True, eq=True)
    """Whether this group is marked as not safe for work."""

    def _update(self, data: PartialChannel) -> None:
        if core.is_defined(data.name):
            self.name = data.name
        if core.is_defined(data.owner_id):
            self.owner_id = data.owner_id
        if core.is_defined(data.description):
            self.description = data.description
        if core.is_defined(data.internal_icon):
            self.internal_icon = data.internal_icon
        if core.is_defined(data.last_message_id):
            self.last_message_id = data.last_message_id
        if core.is_defined(data.permissions):
            self.permissions = data.permissions
        if core.is_defined(data.nsfw):
            self.nsfw = data.nsfw

    def _join(self, user_id: str) -> None:
        if self._recipients[0]:
            self._recipients[1].append(user_id)  # type: ignore # Pyright doesn't understand `if`
        else:
            self._recipients = (True, [u.id for u in self._recipients[1]])  # type: ignore
            self._recipients[1].append(user_id)

    def _leave(self, user_id: str) -> None:
        if self._recipients[0]:
            try:
                self._recipients[1].remove(user_id)  # type: ignore
            except ValueError:
                pass
        else:
            self._recipients = (True, [u.id for u in self._recipients[1] if u.id != user_id])  # type: ignore

    @property
    def icon(self) -> cdn.Asset | None:
        """The group icon."""
        return self.internal_icon and self.internal_icon._stateful(self.state, "icons")

    @property
    def recipient_ids(self) -> list[str]:
        """The IDs of users participating in channel."""
        if self._recipients[0]:
            return self._recipients[1]  # type: ignore
        else:
            return [u.id for u in self._recipients[1]]  # type: ignore

    @property
    def recipients(self) -> list[User]:
        """The users participating in channel."""
        if self._recipients[0]:
            cache = self.state.cache
            if not cache:
                return []
            recipient_ids: list[str] = self._recipients[1]  # type: ignore
            recipients = []
            for recipient_id in recipient_ids:
                user = cache.get_user(recipient_id, caching._USER_REQUEST)
                if user:
                    recipients.append(user)
            return recipients
        else:
            return self._recipients[1]  # type: ignore

    async def add(
        self,
        user: core.ULIDOr[BaseUser],
    ) -> None:
        """|coro|

        Adds another user to the group.

        Parameters
        ----------
        user: :class:`ResolvableULID`
            The user to add.

        Raises
        ------
        Forbidden
            You're bot, lacking `InviteOthers` permission, or not friends with this user.
        HTTPException
            Adding user to the group failed.
        """
        return await self.state.http.add_recipient_to_group(self.id, user)

    async def add_bot(
        self,
        bot: core.ULIDOr[BaseBot | BaseUser],
    ) -> None:
        """|coro|

        Adds a bot to a group.

        Raises
        ------
        Forbidden
            You're bot, or lacking `InviteOthers` permission.
        HTTPException
            Adding bot to the group failed.
        """
        return await self.state.http.invite_bot(bot, group=self.id)

    async def create_invite(self) -> Invite:
        """|coro|

        Creates an invite to this channel.

        Raises
        ------
        Forbidden
            You do not have permissions to create invite in that channel.
        HTTPException
            Creating invite failed.
        """
        return await self.state.http.create_invite(self.id)

    async def leave(self, *, silent: bool | None = None) -> None:
        """|coro|

        Leaves a group.

        Parameters
        ----------
        silent: :class:`bool`
            Whether to not send message when leaving.

        Raises
        ------
        HTTPException
            Leaving the group failed.
        """
        return await self.close(silent=silent)


PrivateChannel = SavedMessagesChannel | DMChannel | GroupChannel


@define(slots=True)
class BaseServerChannel(BaseChannel):
    server_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The server ID that channel belongs to."""

    name: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The display name of the channel."""

    description: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The channel description."""

    internal_icon: cdn.StatelessAsset | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The stateless custom channel icon."""

    default_permissions: PermissionOverride | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """Default permissions assigned to users in this channel."""

    role_permissions: dict[str, PermissionOverride] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """Permissions assigned based on role to this channel."""

    nsfw: bool = field(repr=True, hash=True, kw_only=True, eq=True)
    """Whether this channel is marked as not safe for work."""

    def _update(self, data: PartialChannel) -> None:
        if core.is_defined(data.name):
            self.name = data.name
        if core.is_defined(data.description):
            self.description = data.description
        if core.is_defined(data.internal_icon):
            self.internal_icon = data.internal_icon
        if core.is_defined(data.nsfw):
            self.nsfw = data.nsfw
        if core.is_defined(data.role_permissions):
            self.role_permissions = data.role_permissions
        if core.is_defined(data.default_permissions):
            self.default_permissions = data.default_permissions

    @property
    def icon(self) -> cdn.Asset | None:
        """The custom channel icon."""
        return self.internal_icon and self.internal_icon._stateful(self.state, "icons")

    @property
    def server(self) -> Server:
        """The server that channel belongs to."""
        server = self.get_server()
        if server:
            return server
        raise TypeError("Server is not in cache")

    def get_server(self) -> Server | None:
        """The server that channel belongs to."""
        if not self.state.cache:
            return None
        return self.state.cache.get_server(self.server_id, caching._USER_REQUEST)

    async def create_invite(self) -> Invite:
        """|coro|

        Creates an invite to this channel.
        Channel must be a `TextChannel`.

        Raises
        ------
        Forbidden
            You do not have permissions to create invite in that channel.
        HTTPException
            Creating invite failed.
        """
        return await self.state.http.create_invite(self.id)

    async def delete(self) -> None:
        """|coro|

        Deletes the server channel.

        Raises
        ------
        Forbidden
            You do not have permissions to delete the channel.
        HTTPException
            Deleting the channel failed.
        """
        return await self.close()

    async def set_role_permissions(
        self,
        role: core.ULIDOr[BaseRole],
        *,
        allow: Permissions = Permissions.NONE,
        deny: Permissions = Permissions.NONE,
    ) -> ServerChannel:
        """|coro|

        Sets permissions for the specified role in this channel.
        Channel must be a `TextChannel` or `VoiceChannel`.

        Parameters
        ----------
        role: :class:`core.ResolvableULID`
            The role.

        Raises
        ------
        Forbidden
            You do not have permissions to set role permissions on the channel.
        HTTPException
            Setting permissions failed.
        """
        return await self.state.http.set_role_channel_permissions(
            self.id, role, allow=allow, deny=deny
        )  # type: ignore

    async def set_default_permissions(
        self,
        permissions: "Permissions | PermissionOverride",
    ) -> ServerChannel:
        """|coro|

        Sets permissions for the default role in this channel.
        Channel must be a `Group`, `TextChannel` or `VoiceChannel`.

        Raises
        ------
        Forbidden
            You do not have permissions to set default permissions on the channel.
        HTTPException
            Setting permissions failed.
        """
        return await self.state.http.set_default_channel_permissions(
            self.id, permissions
        )  # type: ignore


@define(slots=True)
class ServerTextChannel(BaseServerChannel, TextChannel):
    """Text channel belonging to a server."""

    last_message_id: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """ID of the last message sent in this channel."""

    def _update(self, data: PartialChannel) -> None:
        BaseServerChannel._update(self, data)
        if core.is_defined(data.last_message_id):
            self.last_message_id = data.last_message_id


@define(slots=True)
class VoiceChannel(BaseServerChannel):
    """Voice channel belonging to a server."""


ServerChannel = ServerTextChannel | VoiceChannel

Channel = (
    SavedMessagesChannel | DMChannel | GroupChannel | ServerTextChannel | VoiceChannel
)

__all__ = (
    "ChannelType",
    "BaseChannel",
    "PartialChannel",
    "Typing",
    "_calculate_saved_messages_channel_permissions",
    "_calculate_dm_channel_permissions",
    "_calculate_group_channel_permissions",
    "_calculate_server_channel_permissions",
    "TextChannel",
    "SavedMessagesChannel",
    "DMChannel",
    "GroupChannel",
    "PrivateChannel",
    "BaseServerChannel",
    "ServerTextChannel",
    "VoiceChannel",
    "ServerChannel",
    "Channel",
)
