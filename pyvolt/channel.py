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
import contextlib
import typing

from . import cache as caching

from .base import Base
from .bot import BaseBot
from .cdn import StatelessAsset, Asset, ResolvableResource
from .core import (
    UNDEFINED,
    UndefinedOr,
    ULIDOr,
    resolve_id,
)
from .enums import Enum
from .errors import NoData
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
    text = 'Text'
    """Text channel."""

    voice = 'Voice'
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

    def message(self, message: ULIDOr[BaseMessage]) -> BaseMessage:
        from .message import BaseMessage

        return BaseMessage(state=self.state, id=resolve_id(message), channel_id=self.id)

    async def close(self, *, silent: bool | None = None) -> None:
        """|coro|

        Deletes a server channel, leaves a group or closes a group.

        Parameters
        ----------
        silent: Optional[:class:`bool`]
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
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str | None] = UNDEFINED,
        owner: UndefinedOr[ULIDOr[BaseUser]] = UNDEFINED,
        icon: UndefinedOr[str | None] = UNDEFINED,
        nsfw: UndefinedOr[bool] = UNDEFINED,
        archived: UndefinedOr[bool] = UNDEFINED,
        default_permissions: UndefinedOr[None] = UNDEFINED,
    ) -> Channel:
        """|coro|

        Edits the channel.

        Parameters
        ----------
        name: :class:`UndefinedOr`[:class:`str`]
            The new channel name. Only applicable when target channel is :class:`GroupChannel`, or :class:`ServerChannel`.
        description: :class:`UndefinedOr`[Optional[:class:`str`]]
            The new channel description. Only applicable when target channel is :class:`GroupChannel`, or :class:`ServerChannel`.
        owner: :class:`UndefinedOr`[:clsas:`ULIDOr`[:class:`BaseUser`]]
            The new channel owner. Only applicable when target channel is :class:`GroupChannel`.
        icon: :class:`UndefinedOr`[Optional[:class:`ResolvableResource`]]
            The new channel icon. Only applicable when target channel is :class:`GroupChannel`, or :class:`ServerChannel`.
        nsfw: :class:`UndefinedOr`[:class:`bool`]
            To mark the channel as NSFW or not. Only applicable when target channel is :class:`GroupChannel`, or :class:`ServerChannel`.
        archived: :class:`UndefinedOr`[:class:`bool`]
            To mark the channel as archived or not.
        default_permissions: :class:`UndefinedOr`[None]
            To remove default permissions or not. Only applicable when target channel is :class:`GroupChannel`, or :class:`ServerChannel`.

        Raises
        ------
        Forbidden
            You do not have permissions to edit the channel.
        HTTPException
            Editing the channel failed.

        Returns
        -------
        :class:`Channel`
            The newly updated channel.
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

    name: UndefinedOr[str] = field(repr=True, kw_only=True, eq=True)
    owner_id: UndefinedOr[str] = field(repr=True, kw_only=True, eq=True)
    description: UndefinedOr[str | None] = field(repr=True, kw_only=True, eq=True)
    internal_icon: UndefinedOr[StatelessAsset | None] = field(repr=True, kw_only=True, eq=True)
    nsfw: UndefinedOr[bool] = field(repr=True, kw_only=True, eq=True)
    active: UndefinedOr[bool] = field(repr=True, kw_only=True, eq=True)
    permissions: UndefinedOr[Permissions] = field(repr=True, kw_only=True, eq=True)
    role_permissions: UndefinedOr[dict[str, PermissionOverride]] = field(repr=True, kw_only=True, eq=True)
    default_permissions: UndefinedOr[PermissionOverride | None] = field(repr=True, kw_only=True, eq=True)
    last_message_id: UndefinedOr[str] = field(repr=True, kw_only=True, eq=True)


def _calculate_saved_messages_channel_permissions(perspective_id: str, user_id: str) -> Permissions:
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

    async def search(
        self,
        query: str | None = None,
        *,
        pinned: bool | None = None,
        limit: int | None = None,
        before: ULIDOr[BaseMessage] | None = None,
        after: ULIDOr[BaseMessage] | None = None,
        sort: MessageSort | None = None,
        populate_users: bool | None = None,
    ) -> list[Message]:
        """|coro|

        Searches for messages.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        query: Optional[:class:`str`]
            Full-text search query. See [MongoDB documentation](https://docs.mongodb.com/manual/text-search/#-text-operator) for more information.
        pinned: Optional[:class:`bool`]
            Whether to search for (un-)pinned messages or not.
        limit: Optional[:class:`int`]
            Maximum number of messages to fetch.
        before: Optional[:class:`ULIDOr`[:class:`BaseMessage`]]
            The message before which messages should be fetched.
        after: Optional[:class:`ULIDOr`[:class:`BaseMessage`]]
            The message after which messages should be fetched.
        sort: Optional[:class:`MessageSort`]
            Sort used for retrieving.
        populate_users: Optional[:class:`bool`]
            Whether to populate user (and member, if server channel) objects.

        Raises
        ------
        Forbidden
            You do not have permissions to search
        HTTPException
            Searching messages failed.

        Returns
        -------
        List[:class:`Message`]
            The messages matched.
        """
        return await self.state.http.search_for_messages(
            self.id,
            query=query,
            pinned=pinned,
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
        attachments: list[ResolvableResource] | None = None,
        replies: list[Reply | ULIDOr[BaseMessage]] | None = None,
        embeds: list[SendableEmbed] | None = None,
        masquerade: Masquerade | None = None,
        interactions: Interactions | None = None,
        silent: bool | None = None,
    ) -> Message:
        """|coro|

        Sends a message to the given channel.
        You must have `SendMessages` permission.

        Parameters
        ----------
        content: Optional[:class:`str`]
            The message content.
        nonce: Optional[:class:`str`]
            The message nonce.
        attachments: Optional[List[:class:`ResolvableResource`]]
            The message attachments.
        replies: Optional[List[Union[:class:`Reply`, :class:`ULIDOr`[:class:`BaseMessage`]]]]
            The message replies.
        embeds: Optional[List[:class:`SendableEmbed`]]
            The message embeds.
        masquearde: Optional[:class:`Masquerade`]
            The message masquerade.
        interactions: Optional[:class:`Interactions`]
            The message interactions.
        silent: Optional[:class:`bool`]
            Whether to suppress notifications or not.

        Raises
        ------
        Forbidden
            You do not have permissions to send
        HTTPException
            Sending the message failed.

        Returns
        -------
        :class:`Message`
            The message that was sent.
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

    user_id: str = field(repr=True, kw_only=True)
    """ID of the user this channel belongs to."""

    def __hash__(self) -> int:
        return hash((self.id, self.user_id))

    def __eq__(self, other: object) -> bool:
        return (
            self is other
            or isinstance(other, SavedMessagesChannel)
            and self.id == other.id
            and self.user_id == other.user_id
        )

    def _update(self, data: PartialChannel) -> None:
        # PartialChannel has no fields that are related to SavedMessages yet
        pass

    def permissions_for(self, perspective: User | Member, /) -> Permissions:
        return _calculate_saved_messages_channel_permissions(perspective.id, self.user_id)


@define(slots=True)
class DMChannel(TextChannel):
    """Direct message channel between two users."""

    active: bool = field(repr=True, kw_only=True)
    """Whether this DM channel is currently open on both sides."""

    recipient_ids: tuple[str, str] = field(repr=True, kw_only=True)
    """2-tuple of user IDs participating in DM."""

    last_message_id: str | None = field(repr=True, kw_only=True)
    """ID of the last message sent in this channel."""

    @property
    def initiator_id(self) -> str:
        me = self.state.me

        if not me:
            return ''

        a = self.recipient_ids[0]
        b = self.recipient_ids[1]

        return a if me.id == a else b

    @property
    def target_id(self) -> str:
        me = self.state.me

        if not me:
            return ''

        a = self.recipient_ids[0]
        b = self.recipient_ids[1]

        return a if me.id != a else b

    def _update(self, data: PartialChannel) -> None:
        if data.active is not UNDEFINED:
            self.active = data.active
        if data.last_message_id is not UNDEFINED:
            self.last_message_id = data.last_message_id


@define(slots=True)
class GroupChannel(TextChannel):
    """Group channel between 1 or more participants."""

    name: str = field(repr=True, kw_only=True)
    """Display name of the channel."""

    owner_id: str = field(repr=True, kw_only=True)
    """User ID of the owner of the group."""

    description: str | None = field(repr=True, kw_only=True)
    """Channel description."""

    _recipients: tuple[typing.Literal[True], list[str]] | tuple[typing.Literal[False], list[User]] = field(
        repr=True, alias='internal_recipients'
    )

    internal_icon: StatelessAsset | None = field(repr=True, kw_only=True)
    """The stateless group icon."""

    last_message_id: str | None = field(repr=True, kw_only=True)
    """ID of the last message sent in this channel."""

    permissions: Permissions | None = field(repr=True, kw_only=True)
    """Permissions assigned to members of this group. (does not apply to the owner of the group)"""

    nsfw: bool = field(repr=True, kw_only=True)
    """Whether this group is marked as not safe for work."""

    def _update(self, data: PartialChannel) -> None:
        if data.name is not UNDEFINED:
            self.name = data.name
        if data.owner_id is not UNDEFINED:
            self.owner_id = data.owner_id
        if data.description is not UNDEFINED:
            self.description = data.description
        if data.internal_icon is not UNDEFINED:
            self.internal_icon = data.internal_icon
        if data.last_message_id is not UNDEFINED:
            self.last_message_id = data.last_message_id
        if data.permissions is not UNDEFINED:
            self.permissions = data.permissions
        if data.nsfw is not UNDEFINED:
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
            self._recipients = (
                True,
                [u.id for u in self._recipients[1] if u.id != user_id],  # type: ignore
            )

    @property
    def icon(self) -> Asset | None:
        """Optional[:class:`Asset`]: The group icon."""
        return self.internal_icon and self.internal_icon._stateful(self.state, 'icons')

    @property
    def recipient_ids(self) -> list[str]:
        """List[:class:`str`]: The IDs of users participating in channel."""
        if self._recipients[0]:
            return self._recipients[1]  # type: ignore
        else:
            return [u.id for u in self._recipients[1]]  # type: ignore

    @property
    def recipients(self) -> list[User]:
        """List[:class:`User`]: The users participating in channel."""
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
        user: ULIDOr[BaseUser],
    ) -> None:
        """|coro|

        Adds another user to the group.

        Parameters
        ----------
        user: :class:`ULIDOr`[:class:`BaseUser`]
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
        bot: ULIDOr[BaseBot | BaseUser],
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

    async def set_default_permissions(self, permissions: Permissions, /) -> GroupChannel:
        """|coro|

        Sets default permissions in a channel.

        Parameters
        ----------
        permissions: :class:`Permissions`
            The new permissions. Should be :class:`Permissions` for groups and :class:`PermissionOverride` for server channels.

        Raises
        ------
        Forbidden
            You do not have permissions to set default permissions on the channel.
        HTTPException
            Setting permissions failed.

        Returns
        -------
        :class:`GroupChannel`
            The updated group with new permissions.
        """
        result = await self.state.http.set_default_channel_permissions(self.id, permissions)
        assert isinstance(result, GroupChannel)
        return result


PrivateChannel = SavedMessagesChannel | DMChannel | GroupChannel


@define(slots=True)
class BaseServerChannel(BaseChannel):
    server_id: str = field(repr=True, kw_only=True)
    """The server ID that channel belongs to."""

    name: str = field(repr=True, kw_only=True)
    """The display name of the channel."""

    description: str | None = field(repr=True, kw_only=True)
    """The channel description."""

    internal_icon: StatelessAsset | None = field(repr=True, kw_only=True)
    """The stateless custom channel icon."""

    default_permissions: PermissionOverride | None = field(repr=True, kw_only=True)
    """Default permissions assigned to users in this channel."""

    role_permissions: dict[str, PermissionOverride] = field(repr=True, kw_only=True)
    """Permissions assigned based on role to this channel."""

    nsfw: bool = field(repr=True, kw_only=True)
    """Whether this channel is marked as not safe for work."""

    def _update(self, data: PartialChannel) -> None:
        if data.name is not UNDEFINED:
            self.name = data.name
        if data.description is not UNDEFINED:
            self.description = data.description
        if data.internal_icon is not UNDEFINED:
            self.internal_icon = data.internal_icon
        if data.nsfw is not UNDEFINED:
            self.nsfw = data.nsfw
        if data.role_permissions is not UNDEFINED:
            self.role_permissions = data.role_permissions
        if data.default_permissions is not UNDEFINED:
            self.default_permissions = data.default_permissions

    @property
    def icon(self) -> Asset | None:
        """Optional[:class:`Asset`]: The custom channel icon."""
        return self.internal_icon and self.internal_icon._stateful(self.state, 'icons')

    @property
    def server(self) -> Server:
        """:class:`Server`: The server that channel belongs to."""
        server = self.get_server()
        if server:
            return server
        raise NoData(self.server_id, 'channel server')

    def get_server(self) -> Server | None:
        """Optional[:class:`Server`]: The server that channel belongs to."""
        if not self.state.cache:
            return None
        return self.state.cache.get_server(self.server_id, caching._USER_REQUEST)

    async def create_invite(self) -> Invite:
        """|coro|

        Creates an invite to channel. The destination channel must be a server channel.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        Forbidden
            You do not have permissions to create invite in that channel.
        HTTPException
            Creating invite failed.

        Returns
        -------
        :class:`Invite`
            The invite that was created.
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
        role: ULIDOr[BaseRole],
        *,
        allow: Permissions = Permissions.NONE,
        deny: Permissions = Permissions.NONE,
    ) -> ServerChannel:
        """|coro|

        Sets permissions for the specified role in this channel.
        Channel must be a `TextChannel` or `VoiceChannel`.

        Parameters
        ----------
        role: :class:`ULIDOr`[:class:`BaseRole`]
            The role.

        Raises
        ------
        Forbidden
            You do not have permissions to set role permissions on the channel.
        HTTPException
            Setting permissions failed.
        """
        return await self.state.http.set_role_channel_permissions(self.id, role, allow=allow, deny=deny)  # type: ignore

    async def set_default_permissions(self, permissions: PermissionOverride, /) -> ServerChannel:
        """|coro|

        Sets permissions for the default role in a channel.

        Parameters
        ----------
        permissions: :class:`PermissionOverride`
            The new permissions.

        Raises
        ------
        Forbidden
            You do not have permissions to set default permissions on the channel.
        HTTPException
            Setting permissions failed.

        Returns
        -------
        :class:`ServerChannel`
            The updated server channel with new permissions.
        """
        result = await self.state.http.set_default_channel_permissions(self.id, permissions)
        return result  # type: ignore


@define(slots=True)
class ServerTextChannel(BaseServerChannel, TextChannel):
    """Text channel belonging to a server."""

    last_message_id: str | None = field(repr=True, kw_only=True)
    """ID of the last message sent in this channel."""

    def _update(self, data: PartialChannel) -> None:
        BaseServerChannel._update(self, data)
        if data.last_message_id is not UNDEFINED:
            self.last_message_id = data.last_message_id


@define(slots=True)
class VoiceChannel(BaseServerChannel):
    """Voice channel belonging to a server."""


ServerChannel = ServerTextChannel | VoiceChannel

Channel = SavedMessagesChannel | DMChannel | GroupChannel | ServerTextChannel | VoiceChannel

__all__ = (
    'ChannelType',
    'BaseChannel',
    'PartialChannel',
    'Typing',
    '_calculate_saved_messages_channel_permissions',
    '_calculate_dm_channel_permissions',
    '_calculate_group_channel_permissions',
    '_calculate_server_channel_permissions',
    'TextChannel',
    'SavedMessagesChannel',
    'DMChannel',
    'GroupChannel',
    'PrivateChannel',
    'BaseServerChannel',
    'ServerTextChannel',
    'VoiceChannel',
    'ServerChannel',
    'Channel',
)
