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
from .core import (
    UNDEFINED,
    UndefinedOr,
    ULIDOr,
    resolve_id,
)
from .enums import ChannelType
from .errors import NoData
from .flags import (
    Permissions,
    UserPermissions,
    ALLOW_PERMISSIONS_IN_TIMEOUT,
    VIEW_ONLY_PERMISSIONS,
    DEFAULT_SAVED_MESSAGES_PERMISSIONS,
    DEFAULT_DM_PERMISSIONS,
)

if typing.TYPE_CHECKING:
    from collections.abc import Mapping

    from .bot import BaseBot
    from .cdn import StatelessAsset, Asset, ResolvableResource
    from .enums import MessageSort
    from .invite import Invite
    from .permissions import PermissionOverride
    from .message import (
        Reply,
        Interactions,
        Masquerade,
        SendableEmbed,
        BaseMessage,
        Message,
    )
    from .server import BaseRole, Role, Server, Member
    from .shard import Shard
    from .user import BaseUser, User


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
    """Represents channel on Revolt."""

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, BaseChannel) and self.id == other.id

    def message(self, message: ULIDOr[BaseMessage]) -> BaseMessage:
        """:class:`BaseMessage`: Returns a partial message with specified ID."""
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

    def permissions_for(self, _target: User | Member, /) -> Permissions:
        """Calculate permissions for given user.

        By default, this returns no permissions.

        Parameters
        ----------
        target: Union[:class:`User`, :class:`Member`]
            The member or user to calculate permissions for.

        Returns
        -------
        :class:`Permissions`
            The calculated permissions.
        """
        return Permissions.none()


@define(slots=True)
class PartialChannel(BaseChannel):
    """Partial representation of a channel on Revolt."""

    name: UndefinedOr[str] = field(repr=True, kw_only=True, eq=True)
    """The new channel name, if applicable. (only for :class:`GroupChannel`s and :class:`BaseServerChannel`'s)"""

    owner_id: UndefinedOr[str] = field(repr=True, kw_only=True, eq=True)
    """The ID of new group owner, if applicable. (only for :class:`GroupChannel`)"""

    description: UndefinedOr[str | None] = field(repr=True, kw_only=True, eq=True)
    """The new channel's description, if applicable. (only for :class:`GroupChannel`s and :class:`BaseServerChannel`'s)"""

    internal_icon: UndefinedOr[StatelessAsset | None] = field(repr=True, kw_only=True, eq=True)
    """The new channel's stateless icon, if applicable. (only for :class:`GroupChannel`s and :class:`BaseServerChannel`'s)"""

    nsfw: UndefinedOr[bool] = field(repr=True, kw_only=True, eq=True)
    """Whether the channel have been marked as NSFW, if applicable. (only for :class:`GroupChannel`s and :class:`BaseServerChannel`'s)"""

    active: UndefinedOr[bool] = field(repr=True, kw_only=True, eq=True)
    permissions: UndefinedOr[Permissions] = field(repr=True, kw_only=True, eq=True)
    role_permissions: UndefinedOr[dict[str, PermissionOverride]] = field(repr=True, kw_only=True, eq=True)
    default_permissions: UndefinedOr[PermissionOverride | None] = field(repr=True, kw_only=True, eq=True)
    last_message_id: UndefinedOr[str] = field(repr=True, kw_only=True, eq=True)


def calculate_saved_messages_channel_permissions(perspective_id: str, user_id: str, /) -> Permissions:
    """Calculates the permissions in :class:`SavedMessagesChannel` scope.

    Parameters
    ----------
    perspective_id: :class:`str`
        The ID of perspective user.
    user_id: :class:`str`
        The ID of channel owner (:attr:`SavedMessagesChannel.owner_id`).

    Returns
    -------
    :class:`Permissions`
        The calculated permissions.
    """
    if perspective_id == user_id:
        return DEFAULT_SAVED_MESSAGES_PERMISSIONS
    return Permissions.none()


def calculate_dm_channel_permissions(
    permissions: UserPermissions,
    /,
) -> Permissions:
    """Calculates the permissions in :class:`DMChannel` scope.

    Parameters
    ----------
    permissions: :class:`UserPermissions`
        The user permissions.

    Returns
    -------
    :class:`Permissions`
        The calculated permissions.
    """
    if permissions.send_messages:
        return DEFAULT_DM_PERMISSIONS
    return VIEW_ONLY_PERMISSIONS


def calculate_group_channel_permissions(
    perspective_id: str,
    /,
    *,
    group_owner_id: str,
    group_permissions: Permissions | None,
    group_recipients: list[str],
) -> Permissions:
    """Calculates the permissions in :class:`GroupChannel` scope.

    Parameters
    ----------
    perspective_id: :class:`str`
        The ID of perspective user.
    group_owner_id: :class:`str`
        The ID of group owner (:attr:`GroupChannel.owner_id`).
    group_permissions: Optional[:class:`Permissions`]
        The default group permissions (:attr:`GroupChannel.permissions`).
    group_recipients: List[:class:`str`]
        The IDs of group recipients (:attr:`GroupChannel.recipient_ids`).

    Returns
    -------
    :class:`Permissions`
        The calculated permissions.
    """
    if perspective_id == group_owner_id:
        return Permissions.all()
    elif perspective_id in group_recipients:
        if group_permissions is None:
            group_permissions = DEFAULT_DM_PERMISSIONS
        return VIEW_ONLY_PERMISSIONS | group_permissions
    return Permissions.none()


def calculate_server_channel_permissions(
    initial_permissions: Permissions,
    roles: list[Role],
    /,
    *,
    default_permissions: PermissionOverride | None,
    role_permissions: dict[str, PermissionOverride],
) -> Permissions:
    """Calculates the permissions in :class:`BaseServerChannel` scope.

    Parameters
    ----------
    initial_permissions: :class:`str`
        The initial permissions to use. Should be ``server.permissions_for(member)`` for members
        and :attr:`Server.default_permissions` for users.
    roles: List[:class:`Role`]
        The member's roles. Should be empty list if calculating for :class:`User`.
    default_permissions: :class:`str`
        The default channel permissions (:attr:`BaseServerChannel.default_permissions`).
    role_permissions: Dict[:class:`str`, :class:`Permissions`]
        The permissions overrides for roles in the channel (:attr:`BaseServerChannel.role_permissions`).

    Returns
    -------
    :class:`Permissions`
        The calculated permissions.
    """
    result = initial_permissions.value

    if default_permissions:
        result |= default_permissions.allow.value
        result &= ~default_permissions.deny.value

    for role in roles:
        override = role_permissions.get(role.id)
        if override:
            result |= override.allow.value
            result &= ~override.deny.value

    return Permissions(result)


@define(slots=True)
class TextChannel(BaseChannel):
    """A channel that can have messages."""

    def get_message(self, message_id: str, /) -> Message | None:
        """Retrieves a channel message from cache.

        Parameters
        ----------
        message_id: :class:`str`
            The message ID.

        Returns
        -------
        Optional[:class:`Message`]
            The message or ``None`` if not found.
        """
        cache = self.state.cache
        if not cache:
            return
        return cache.get_message(self.id, message_id, caching._USER_REQUEST)

    def _update(self, data: PartialChannel, /) -> None:
        # PartialChannel has no fields that are related to SavedMessages yet
        pass

    @property
    def messages(self) -> Mapping[str, Message]:
        """Mapping[:class:`str`, :class:`Message`]: Returns all messages in this channel."""
        cache = self.state.cache
        if cache:
            return cache.get_messages_mapping_of(self.id, caching._USER_REQUEST) or {}
        return {}

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
            Full-text search query. See `MongoDB documentation <https://docs.mongodb.com/manual/text-search/#-text-operator>`_ for more information.
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

    def typing(self) -> Typing:
        """:class:`Typing`: Returns an asynchronous context manager that allows you to send a typing indicator in channel for an indefinite period of time."""
        return Typing(self.state.shard, self.id)


@define(slots=True)
class SavedMessagesChannel(TextChannel):
    """Personal "Saved Notes" channel which allows users to save messages."""

    user_id: str = field(repr=True, kw_only=True)
    """The ID of the user this channel belongs to."""

    def _update(self, data: PartialChannel, /) -> None:
        # PartialChannel has no fields that are related to SavedMessages yet
        pass

    @property
    def type(self) -> typing.Literal[ChannelType.saved_messages]:
        """Literal[:attr:`ChannelType.saved_messages`]: The channel's type."""
        return ChannelType.saved_messages

    def permissions_for(self, target: User | Member, /) -> Permissions:
        """Calculate permissions for given member.

        Parameters
        ----------
        target: Union[:class:`User`, :class:`Member`]
            The user to calculate permissions for.

        Returns
        -------
        :class:`Permissions`
            The calculated permissions.
        """

        return calculate_saved_messages_channel_permissions(target.id, self.user_id)


@define(slots=True)
class DMChannel(TextChannel):
    """The PM channel between two users."""

    active: bool = field(repr=True, kw_only=True)
    """Whether this DM channel is currently open on both sides."""

    recipient_ids: tuple[str, str] = field(repr=True, kw_only=True)
    """The tuple of user IDs participating in DM."""

    last_message_id: str | None = field(repr=True, kw_only=True)
    """The ID of the last message sent in this channel."""

    @property
    def initiator_id(self) -> str:
        """:class:`str`: The user's ID that started this PM."""
        return self.recipient_ids[0]

    @property
    def recipient_id(self) -> str:
        """:class:`str`: The recipient's ID."""
        me = self.state.me

        if not me:
            return ''

        a = self.recipient_ids[0]
        b = self.recipient_ids[1]

        return a if me.id != a else b

    def _update(self, data: PartialChannel, /) -> None:
        if data.active is not UNDEFINED:
            self.active = data.active
        if data.last_message_id is not UNDEFINED:
            self.last_message_id = data.last_message_id

    @property
    def type(self) -> typing.Literal[ChannelType.dm]:
        """Literal[:attr:`ChannelType.dm`]: The channel's type."""
        return ChannelType.dm

    def permissions_for(self, target: User | Member, /) -> Permissions:
        """Calculate permissions for given user.

        Parameters
        ----------
        target: Union[:class:`User`, :class:`Member`]
            The member or user to calculate permissions for.

        Returns
        -------
        :class:`Permissions`
            The calculated permissions.
        """
        me = self.state.me
        if not me:
            raise TypeError('Missing own user')

        from .server import Member
        from .user import calculate_user_permissions

        if isinstance(target, Member):
            target = target.user

        return calculate_dm_channel_permissions(
            calculate_user_permissions(
                target.id,
                target.relationship,
                target.bot,
                perspective_id=me.id,
                perspective_bot=me.bot,
                perspective_privileged=me.privileged,
            )
        )


@define(slots=True)
class GroupChannel(TextChannel):
    """Represesnts Revolt group channel between 1 or more participants."""

    name: str = field(repr=True, kw_only=True)
    """The group's name."""

    owner_id: str = field(repr=True, kw_only=True)
    """The user's ID who owns this group."""

    description: str | None = field(repr=True, kw_only=True)
    """The group description."""

    _recipients: tuple[typing.Literal[True], list[str]] | tuple[typing.Literal[False], list[User]] = field(
        repr=True, kw_only=True, alias='internal_recipients'
    )

    internal_icon: StatelessAsset | None = field(repr=True, kw_only=True)
    """The stateless group icon."""

    last_message_id: str | None = field(repr=True, kw_only=True)
    """The ID of the last message sent in this channel."""

    permissions: Permissions | None = field(repr=True, kw_only=True)
    """The permissions assigned to members of this group. (does not apply to the owner of the group)"""

    nsfw: bool = field(repr=True, kw_only=True)
    """Whether this group is marked as not safe for work."""

    def _update(self, data: PartialChannel, /) -> None:
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

    @property
    def type(self) -> typing.Literal[ChannelType.group]:
        """Literal[:attr:`ChannelType.group`]: The channel's type."""
        return ChannelType.group

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

    def permissions_for(self, target: User | Member, /) -> Permissions:
        """Calculate permissions for given user.

        Parameters
        ----------
        target: Union[:class:`User`, :class:`Member`]
            The member or user to calculate permissions for.

        Returns
        -------
        :class:`Permissions`
            The calculated permissions.
        """
        me = self.state.me
        if not me:
            raise TypeError('Missing own user')

        from .server import Member
        from .user import calculate_user_permissions

        if isinstance(target, Member):
            target = target.user

        return calculate_dm_channel_permissions(
            calculate_user_permissions(
                target.id,
                target.relationship,
                target.bot,
                perspective_id=me.id,
                perspective_bot=me.bot,
                perspective_privileged=me.privileged,
            )
        )


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

    def _update(self, data: PartialChannel, /) -> None:
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
        result = await self.state.http.set_channel_permissions_for_role(self.id, role, allow=allow, deny=deny)
        return result

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

    def permissions_for(
        self, target: User | Member, /, *, safe: bool = True, with_ownership: bool = True, include_timeout: bool = True
    ) -> Permissions:
        """Calculate permissions for given user.

        Parameters
        ----------
        target: Union[:class:`User`, :class:`Member`]
            The member or user to calculate permissions for.
        safe: :class:`bool`
            Whether to raise exception or not if role is missing in cache.
        with_ownership: :class:`bool`
            Whether to account for ownership.
        include_timeout: :class:`bool`
            Whether to account for timeout.

        Raises
        ------
        NoData
            The server or role is not found in cache.

        Returns
        -------
        :class:`Permissions`
            The calculated permissions.
        """
        server = self.get_server()
        if server is None:
            raise NoData(self.server_id, 'server')

        if with_ownership and server.owner_id == target.id:
            return Permissions.all()

        from .server import sort_member_roles, calculate_server_permissions
        from .user import User

        if isinstance(target, User):
            initial_permissions = server.default_permissions

            # No point in providing roles since user doesn't have roles.
            return calculate_server_channel_permissions(
                server.default_permissions, [], default_permissions=self.default_permissions, role_permissions={}
            )

        initial_permissions = calculate_server_permissions([], None, default_permissions=server.default_permissions)
        roles = sort_member_roles(target.roles, safe=safe, server_roles=server.roles)
        result = calculate_server_channel_permissions(
            initial_permissions,
            roles,
            default_permissions=self.default_permissions,
            role_permissions=self.role_permissions,
        )
        if include_timeout and target.timed_out_until is not None:
            result &= ALLOW_PERMISSIONS_IN_TIMEOUT
        return result


@define(slots=True)
class ChannelVoiceMetadata:
    max_users: int = field(repr=True, kw_only=True)
    """The maximium amount of users allowed in the voice channel at once.
    
    Zero means a infinite amount of users can connect to voice channel.
    """


@define(slots=True)
class ServerTextChannel(BaseServerChannel, TextChannel):
    """Represents a text channel that belongs to a server on Revolt."""

    last_message_id: str | None = field(repr=True, kw_only=True)
    """The last's message ID sent in the channel."""

    voice: ChannelVoiceMetadata | None = field(repr=True, kw_only=True)
    """The voice's metadata in the channel."""

    def _update(self, data: PartialChannel, /) -> None:
        BaseServerChannel._update(self, data)
        if data.last_message_id is not UNDEFINED:
            self.last_message_id = data.last_message_id

    @property
    def type(self) -> typing.Literal[ChannelType.text]:
        """Literal[:attr:`ChannelType.text`]: The channel's type."""
        return ChannelType.text


@define(slots=True)
class VoiceChannel(BaseServerChannel):
    """Represents a voice channel that belongs to a server on Revolt.

    .. deprecated:: 0.7.0
        The voice channel type was deprecated in favour of :attr:`ServerTextChannel.voice`.
    """

    @property
    def type(self) -> typing.Literal[ChannelType.voice]:
        """Literal[:attr:`ChannelType.voice`]: The channel's type."""
        return ChannelType.voice


ServerChannel = ServerTextChannel | VoiceChannel

Channel = SavedMessagesChannel | DMChannel | GroupChannel | ServerTextChannel | VoiceChannel

__all__ = (
    'BaseChannel',
    'PartialChannel',
    'Typing',
    'calculate_saved_messages_channel_permissions',
    'calculate_dm_channel_permissions',
    'calculate_group_channel_permissions',
    'calculate_server_channel_permissions',
    'TextChannel',
    'SavedMessagesChannel',
    'DMChannel',
    'GroupChannel',
    'PrivateChannel',
    'BaseServerChannel',
    'ChannelVoiceMetadata',
    'ServerTextChannel',
    'VoiceChannel',
    'ServerChannel',
    'Channel',
)
