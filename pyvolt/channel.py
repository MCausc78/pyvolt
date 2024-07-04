from __future__ import annotations

import abc
import contextlib
import typing as t
from enum import StrEnum

from attrs import define, field

from . import (
    base,
    cache as caching,
    cdn,
    core,
    permissions as permissions_,
    user as users,
)

if t.TYPE_CHECKING:
    from . import invite as invites, message as messages, server as servers
    from .shard import Shard


class ChannelType(StrEnum):
    TEXT = "Text"
    """Text channel."""

    VOICE = "Voice"
    """Voice channel."""


class Typing(contextlib.AbstractAsyncContextManager):
    shard: Shard
    channel_id: core.ULID

    def __init__(self, shard: Shard, channel_id: core.ULID) -> None:
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


class BaseChannel(base.Base, abc.ABC):
    """Representation of channel on Revolt."""

    def message(self, message: core.ResolvableULID) -> messages.BaseMessage:
        from . import messages

        return messages.BaseMessage(
            state=self.state, id=core.resolve_ulid(message), channel_id=self.id
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
        :class:`Forbidden`
            You do not have permissions to close the channel.
        :class:`APIError`
            Closing the channel failed.
        """
        return await self.state.http.close_channel(
            self.id, silent=silent
        )

    async def edit(
        self,
        *,
        name: core.UndefinedOr[str] = core.UNDEFINED,
        description: core.UndefinedOr[str | None] = core.UNDEFINED,
        owner: core.UndefinedOr[core.ResolvableULID] = core.UNDEFINED,
        icon: core.UndefinedOr[str | None] = core.UNDEFINED,
        nsfw: core.UndefinedOr[bool] = core.UNDEFINED,
        archived: core.UndefinedOr[bool] = core.UNDEFINED,
        default_permissions: core.UndefinedOr[None] = core.UNDEFINED,
    ) -> "Channel":
        """|coro|

        Edits the channel.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to edit the channel.
        :class:`APIError`
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
        :class:`APIError`
            Asking the token failed.
        """
        return await self.state.http.join_call(self.id)


@define(slots=True)
class PartialChannel(BaseChannel):
    """Partial representation of a channel on Revolt."""

    name: core.UndefinedOr[str] = field(repr=True, hash=True, kw_only=True, eq=True)
    owner_id: core.UndefinedOr[core.ULID] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    description: core.UndefinedOr[str | None] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    internal_icon: core.UndefinedOr[cdn.StatelessAsset | None] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    nsfw: core.UndefinedOr[bool] = field(repr=True, hash=True, kw_only=True, eq=True)
    active: core.UndefinedOr[bool] = field(repr=True, hash=True, kw_only=True, eq=True)
    permissions: core.UndefinedOr[permissions_.Permissions] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    role_permissions: core.UndefinedOr[
        dict[core.ULID, permissions_.PermissionOverride]
    ] = field(repr=True, hash=True, kw_only=True, eq=True)
    default_permissions: core.UndefinedOr[permissions_.PermissionOverride | None] = (
        field(repr=True, hash=True, kw_only=True, eq=True)
    )
    last_message_id: core.UndefinedOr[core.ULID] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )


def _calculate_saved_messages_channel_permissions(
    perspective_id: core.ULID, user_id: core.ULID
) -> permissions_.Permissions:
    if perspective_id == user_id:
        return permissions_.DEFAULT_SAVED_MESSAGES_PERMISSIONS
    return permissions_.Permissions.NONE


def _calculate_dm_channel_permissions(
    user_permissions: permissions_.UserPermissions,
) -> permissions_.Permissions:
    if user_permissions & permissions_.UserPermissions.SEND_MESSAGE:
        return permissions_.DEFAULT_DM_PERMISSIONS
    return permissions_.VIEW_ONLY_PERMISSIONS


def _calculate_group_channel_permissions(
    perspective_id: core.ULID,
    *,
    group_owner_id: core.ULID,
    group_permissions: permissions_.Permissions,
    group_recipients: list[core.ULID],
) -> permissions_.Permissions:
    if perspective_id == group_owner_id:
        return permissions_.Permissions.ALL
    elif perspective_id in group_recipients:
        return permissions_.VIEW_ONLY_PERMISSIONS | group_permissions
    return permissions_.Permissions.NONE


def _calculate_server_channel_permissions(
    initial_permissions: permissions_.Permissions,
    roles: list[servers.Role],
    /,
    *,
    default_permissions: permissions_.PermissionOverride | None,
    role_permissions: dict[core.ULID, permissions_.PermissionOverride],
) -> permissions_.Permissions:
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

    return permissions_.Permissions(result)


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

    async def pins(self) -> list[messages.Message]:
        """|coro|

        Retrieves all messages that are currently pinned in the channel.

        Raises
        ------
        :class:`APIError`
            Getting channel pins failed.
        """
        return await self.state.http.get_channel_pins(self.id)

    async def search(
        self,
        query: str,
        *,
        limit: int | None = None,
        before: core.ResolvableULID | None = None,
        after: core.ResolvableULID | None = None,
        sort: "messages.MessageSort | None" = None,
        populate_users: bool | None = None,
    ) -> list["messages.Message"]:
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
        :class:`Forbidden`
            You do not have permissions to search messages.
        :class:`APIError`
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
        replies: list[messages.Reply | core.ResolvableULID] | None = None,
        embeds: list[messages.SendableEmbed] | None = None,
        masquerade: messages.Masquerade | None = None,
        interactions: messages.Interactions | None = None,
        silent: bool | None = None,
    ) -> "messages.Message":
        """|coro|

        Sends a message to the given channel.
        You must have `SendMessages` permission.

        Returns
        -------
        :class:`Message`
            The message sent.

        :class:`Forbidden`
            You do not have permissions to send messages.
        :class:`APIError`
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

    user_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    """ID of the user this channel belongs to."""

    def _update(self, data: PartialChannel) -> None:
        # PartialChannel has no fields that are related to SavedMessages yet
        pass

    def permissions_for(
        self, perspective: users.User | servers.Member, /
    ) -> permissions_.Permissions:
        return _calculate_saved_messages_channel_permissions(
            perspective.id, self.user_id
        )


@define(slots=True)
class DMChannel(TextChannel):
    """Direct message channel between two users."""

    active: bool = field(repr=True, hash=True, kw_only=True, eq=True)
    """Whether this DM channel is currently open on both sides."""

    recipient_ids: tuple[core.ULID, core.ULID] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """2-tuple of user IDs participating in DM."""

    last_message_id: core.ULID | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
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

    owner_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    """User ID of the owner of the group."""

    description: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """Channel description."""

    _recipients: (
        tuple[t.Literal[True], list[core.ULID]]
        | tuple[t.Literal[False], list[users.User]]
    ) = field(repr=True, hash=True, eq=True, alias="internal_recipients")

    internal_icon: cdn.StatelessAsset | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The stateless group icon."""

    last_message_id: core.ULID | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """ID of the last message sent in this channel."""

    permissions: permissions_.Permissions | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
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

    def _join(self, user_id: core.ULID) -> None:
        if self._recipients[0]:
            self._recipients[1].append(user_id)  # type: ignore # Pyright doesn't understand `if`
        else:
            self._recipients = (True, [u.id for u in self._recipients[1]])  # type: ignore
            self._recipients[1].append(user_id)

    def _leave(self, user_id: core.ULID) -> None:
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
    def recipient_ids(self) -> list[core.ULID]:
        """The IDs of users participating in channel."""
        if self._recipients[0]:
            return self._recipients[1]  # type: ignore
        else:
            return [u.id for u in self._recipients[1]]  # type: ignore

    @property
    def recipients(self) -> list[users.User]:
        """The users participating in channel."""
        if self._recipients[0]:
            cache = self.state.cache
            if not cache:
                return []
            recipient_ids = t.cast("list[core.ULID]", self._recipients[1])
            recipients = []
            for recipient_id in recipient_ids:
                user = cache.get_user(recipient_id, caching._USER_REQUEST)
                if user:
                    recipients.append(user)
            return recipients
        else:
            return t.cast("list[users.User]", self._recipients[1])

    async def add(
        self,
        user: core.ResolvableULID,
    ) -> None:
        """|coro|

        Adds another user to the group.

        Parameters
        ----------
        user: :class:`ResolvableULID`
            The user to add.

        Raises
        ------
        :class:`Forbidden`
            You're bot, lacking `InviteOthers` permission, or not friends with this user.
        :class:`APIError`
            Adding user to the group failed.
        """
        return await self.state.http.add_member_to_group(self.id, user)

    async def add_bot(
        self,
        bot: core.ResolvableULID,
    ) -> None:
        """|coro|

        Adds a bot to a group.

        Raises
        ------
        :class:`Forbidden`
            You're bot, or lacking `InviteOthers` permission.
        :class:`APIError`
            Adding bot to the group failed.
        """
        return await self.state.http.invite_bot(bot, group=self.id)

    async def create_invite(self) -> "invites.Invite":
        """|coro|

        Creates an invite to this channel.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to create invite in that channel.
        :class:`APIError`
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
        :class:`APIError`
            Leaving the group failed.
        """
        return await self.close(silent=silent)


PrivateChannel = SavedMessagesChannel | DMChannel | GroupChannel


@define(slots=True)
class BaseServerChannel(BaseChannel):
    server_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    """The server ID that channel belongs to."""

    name: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The display name of the channel."""

    description: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The channel description."""

    internal_icon: cdn.StatelessAsset | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The stateless custom channel icon."""

    default_permissions: permissions_.PermissionOverride | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """Default permissions assigned to users in this channel."""

    role_permissions: dict[core.ULID, permissions_.PermissionOverride] = field(
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
    def server(self) -> servers.Server:
        """The server that channel belongs to."""
        server = self.get_server()
        if server:
            return server
        raise TypeError("Server is not in cache")

    def get_server(self) -> servers.Server | None:
        """The server that channel belongs to."""
        if not self.state.cache:
            return None
        return self.state.cache.get_server(self.server_id, caching._USER_REQUEST)

    async def create_invite(self) -> invites.Invite:
        """|coro|

        Creates an invite to this channel.
        Channel must be a `TextChannel`.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to create invite in that channel.
        :class:`APIError`
            Creating invite failed.
        """
        return await self.state.http.create_invite(self.id)

    async def delete(self) -> None:
        """|coro|

        Deletes the server channel.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to delete the channel.
        :class:`APIError`
            Deleting the channel failed.
        """
        return await self.close()

    async def set_role_permissions(
        self,
        role: core.ResolvableULID,
        *,
        allow: permissions_.Permissions = permissions_.Permissions.NONE,
        deny: permissions_.Permissions = permissions_.Permissions.NONE,
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
        :class:`Forbidden`
            You do not have permissions to set role permissions on the channel.
        :class:`APIError`
            Setting permissions failed.
        """
        return await self.state.http.set_role_channel_permissions(
            self.id, role, allow=allow, deny=deny
        )  # type: ignore

    async def set_default_permissions(
        self,
        permissions: "permissions_.Permissions | permissions_.PermissionOverride",
    ) -> ServerChannel:
        """|coro|

        Sets permissions for the default role in this channel.
        Channel must be a `Group`, `TextChannel` or `VoiceChannel`.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to set default permissions on the channel.
        :class:`APIError`
            Setting permissions failed.
        """
        return await self.state.http.set_default_channel_permissions(
            self.id, permissions
        )  # type: ignore


@define(slots=True)
class ServerTextChannel(BaseServerChannel, TextChannel):
    """Text channel belonging to a server."""

    last_message_id: core.ULID | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
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
