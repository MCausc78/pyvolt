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
import typing

from . import cache as caching

from .abc import Messageable, Connectable
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
    from .bot import BaseBot
    from .cdn import StatelessAsset, Asset, ResolvableResource
    from .invite import Invite
    from .message import BaseMessage
    from .permissions import PermissionOverride
    from .server import BaseRole, Role, Server, Member
    from .state import State
    from .user import BaseUser, User, UserVoiceState

_new_permissions = Permissions.__new__


@define(slots=True)
class BaseChannel(Base):
    """Represents channel on Revolt."""

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, BaseChannel) and self.id == other.id

    def message(self, message: ULIDOr[BaseMessage], /) -> BaseMessage:
        """:class:`BaseMessage`: Returns a partial message with specified ID."""
        from .message import BaseMessage

        return BaseMessage(state=self.state, id=resolve_id(message), channel_id=self.id)

    @property
    def mention(self) -> str:
        """:class:`str`: Returns the channel's mention."""

        return f'<#{self.id}>'

    async def close(self, *, silent: typing.Optional[bool] = None) -> None:
        """|coro|

        Deletes a server channel, leaves a group or closes a group.

        You must have :attr:`~Permissions.view_channel` to do this. If target channel is server channel, :attr:`~Permissions.manage_channels` is also required.

        Parameters
        ----------
        silent: Optional[:class:`bool`]
            Whether to not send message when leaving.

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

            +-----------------------+---------------------------------------------------------------------------+
            | Value                 | Reason                                                                    |
            +-----------------------+---------------------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to view and/or delete the channel. |
            +-----------------------+---------------------------------------------------------------------------+
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
        """

        return await self.state.http.close_channel(self.id, silent=silent)

    async def edit(
        self,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[typing.Optional[str]] = UNDEFINED,
        owner: UndefinedOr[ULIDOr[BaseUser]] = UNDEFINED,
        icon: UndefinedOr[typing.Optional[ResolvableResource]] = UNDEFINED,
        nsfw: UndefinedOr[bool] = UNDEFINED,
        archived: UndefinedOr[bool] = UNDEFINED,
        default_permissions: UndefinedOr[None] = UNDEFINED,
    ) -> Channel:
        """|coro|

        Edits the channel.

        You must have :attr:`~Permissions.manage_channels` to do this.

        Parameters
        ----------
        name: UndefinedOr[:class:`str`]
            The new channel name. Only applicable when target channel is :class:`.GroupChannel`, or :class:`.ServerChannel`.
        description: UndefinedOr[Optional[:class:`str`]]
            The new channel description. Only applicable when target channel is :class:`.GroupChannel`, or :class:`.ServerChannel`.
        owner: UndefinedOr[ULIDOr[:class:`.BaseUser`]]
            The new channel owner. Only applicable when target channel is :class:`.GroupChannel`.
        icon: UndefinedOr[Optional[:class:`.ResolvableResource`]]
            The new channel icon. Only applicable when target channel is :class:`.GroupChannel`, or :class:`.ServerChannel`.
        nsfw: UndefinedOr[:class:`bool`]
            To mark the channel as NSFW or not. Only applicable when target channel is :class:`.GroupChannel`, or :class:`.ServerChannel`.
        archived: UndefinedOr[:class:`bool`]
            To mark the channel as archived or not.
        default_permissions: UndefinedOr[None]
            To remove default permissions or not. Only applicable when target channel is :class:`.GroupChannel`, or :class:`.ServerChannel`.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------+------------------------------------------------------+
            | Value                | Reason                                               |
            +----------------------+------------------------------------------------------+
            | ``FailedValidation`` | The payload was invalid.                             |
            +----------------------+------------------------------------------------------+
            | ``InvalidOperation`` | The target channel was not group/text/voice channel. |
            +----------------------+------------------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+-------------------------------------------------------------+
            | Value                 | Reason                                                      |
            +-----------------------+-------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to edit the channel. |
            +-----------------------+-------------------------------------------------------------+
            | ``NotOwner``          | You do not own the group.                                   |
            +-----------------------+-------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +----------------+---------------------------------+
            | Value          | Reason                          |
            +----------------+---------------------------------+
            | ``NotFound``   | The channel was not found.      |
            +----------------+---------------------------------+
            | ``NotInGroup`` | The new owner was not in group. |
            +----------------+---------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`.Channel`
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

        You must have :attr:`~Permissions.connect` to do this.

        If current instance uses legacy voice server (determined by whether :attr:`InstanceFeaturesConfig.livekit_voice` is ``False``),
        then you cannot connect to channel with type of :attr:`~ChannelType.text` and if you do,
        it will raise :class:`HTTPException` with ``CannotJoinCall`` type.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +---------------------------+-----------------------------------------------------------------------------------------------------------------------------------+
            | Value                     | Reason                                                                                                                            |
            +---------------------------+-----------------------------------------------------------------------------------------------------------------------------------+
            | ``AlreadyConnected``      | The current user was already connected to this voice channel.                                                                     |
            +---------------------------+-----------------------------------------------------------------------------------------------------------------------------------+
            | ``AlreadyInVoiceChannel`` | The current user was already connected to other voice channel.                                                                    |
            +---------------------------+-----------------------------------------------------------------------------------------------------------------------------------+
            | ``CannotJoinCall``        | The channel was type of :attr:`~ChannelType.saved_messages` (or if instance uses legacy voice server, :attr:`~ChannelType.text`). |
            +---------------------------+-----------------------------------------------------------------------------------------------------------------------------------+
            | ``InvalidOperation``      | The voice server is unavailable.                                                                                                  |
            +---------------------------+-----------------------------------------------------------------------------------------------------------------------------------+
            | ``NotAVoiceChannel``      | ???. Only applicable to instances using Livekit                                                                                   |
            +---------------------------+-----------------------------------------------------------------------------------------------------------------------------------+
            | ``VosoUnavailable``       | The voice server is unavailable.                                                                                                  |
            +---------------------------+-----------------------------------------------------------------------------------------------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------------------+--------------------------------------------------------+
            | Value                            | Reason                                                 |
            +----------------------------------+--------------------------------------------------------+
            | ``MissingPermission``            | You do not have the proper permissions to join a call. |
            +----------------------------------+--------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+----------------------------+
            | Value        | Reason                     |
            +--------------+----------------------------+
            | ``NotFound`` | The channel was not found. |
            +--------------+----------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+-------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                          | Populated attributes                                                |
            +-------------------+-------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database.  | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+-------------------------------------------------+---------------------------------------------------------------------+
            | ``InternalError`` | Somehow something went during retrieving token. |                                                                     |
            +-------------------+-------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`str`
            The token for authenticating with the voice server.
        """
        return await self.state.http.join_call(self.id)

    def permissions_for(self, _target: typing.Union[User, Member], /) -> Permissions:
        """Calculate permissions for given user.

        By default, this returns no permissions.

        Parameters
        ----------
        target: Union[:class:`.User`, :class:`.Member`]
            The member or user to calculate permissions for.

        Returns
        -------
        :class:`.Permissions`
            The calculated permissions.
        """
        return Permissions.none()


@define(slots=True)
class PartialChannel(BaseChannel):
    """Represents a partial channel on Revolt."""

    name: UndefinedOr[str] = field(repr=True, kw_only=True, eq=True)
    """UndefinedOr[:class:`str`]: The new channel name, if applicable. Only for :class:`GroupChannel` and :class:`BaseServerChannel`'s."""

    owner_id: UndefinedOr[str] = field(repr=True, kw_only=True, eq=True)
    """UndefinedOr[:class:`str`]: The ID of new group owner, if applicable. Only for :class:`GroupChannel`."""

    description: UndefinedOr[typing.Optional[str]] = field(repr=True, kw_only=True, eq=True)
    """UndefinedOr[Optional[:class:`str`]]: The new channel's description, if applicable. Only for :class:`GroupChannel` and :class:`BaseServerChannel`'s."""

    internal_icon: UndefinedOr[typing.Optional[StatelessAsset]] = field(repr=True, kw_only=True, eq=True)
    """UndefinedOr[Optional[:class:`.StatelessAsset`]]: The new channel's stateless icon, if applicable. Only for :class:`GroupChannel` and :class:`BaseServerChannel`'s."""

    nsfw: UndefinedOr[bool] = field(repr=True, kw_only=True, eq=True)
    """UndefinedOr[:class:`bool`]: Whether the channel have been marked as NSFW, if applicable. Only for :class:`GroupChannel` and :class:`BaseServerChannel`'s."""

    active: UndefinedOr[bool] = field(repr=True, kw_only=True, eq=True)
    """UndefinedOr[:class:`bool`]: Whether the DM channel is active now, if applicable. Only for :class:`DMChannel`'s."""

    raw_permissions: UndefinedOr[int] = field(repr=True, kw_only=True, eq=True)
    """UndefinedOr[:class:`int`]: The new channel's permissions raw value, if applicable. Only for :class:`GroupChannel`'s."""

    role_permissions: UndefinedOr[dict[str, PermissionOverride]] = field(repr=True, kw_only=True, eq=True)
    """UndefinedOr[Dict[:class:`str`, :class:`.PermissionOverride`]]: The new channel's permission overrides for roles, if applicable. Only for :class:`BaseServerChannel`'s."""

    default_permissions: UndefinedOr[typing.Optional[PermissionOverride]] = field(repr=True, kw_only=True, eq=True)
    """UndefinedOr[Optional[:class:`.PermissionOverride`]]: The new channel's permission overrides for everyone, if applicable. Only for :class:`BaseServerChannel`'s."""

    last_message_id: UndefinedOr[str] = field(repr=True, kw_only=True, eq=True)
    """UndefinedOr[:class:`str`]: The last message ID sent in the channel."""

    @property
    def icon(self) -> UndefinedOr[typing.Optional[Asset]]:
        r"""UndefinedOr[Optional[:class:`Asset`]]: The new channel's icon, if applicable. Only for :class:`.GroupChannel` and :class:`.BaseServerChannel`\'s."""
        if self.internal_icon in (None, UNDEFINED):
            return self.internal_icon
        return self.internal_icon.attach_state(self.state, 'icons')

    @property
    def permissions(self) -> UndefinedOr[Permissions]:
        r"""UndefinedOr[:class:`.Permissions`]: The new channel's permissions, if applicable. Only for :class:`.GroupChannel`\'s."""
        if self.raw_permissions is UNDEFINED:
            return self.raw_permissions
        ret = _new_permissions(Permissions)
        ret.value = self.raw_permissions
        return ret


def calculate_saved_messages_channel_permissions(perspective_id: str, user_id: str, /) -> Permissions:
    """Calculates the permissions in :class:`.SavedMessagesChannel` scope.

    Parameters
    ----------
    perspective_id: :class:`str`
        The ID of perspective user.
    user_id: :class:`str`
        The ID of channel owner (:attr:`.SavedMessagesChannel.owner_id`).

    Returns
    -------
    :class:`.Permissions`
        The calculated permissions.
    """
    if perspective_id == user_id:
        return DEFAULT_SAVED_MESSAGES_PERMISSIONS
    return Permissions.none()


def calculate_dm_channel_permissions(
    permissions: UserPermissions,
    /,
) -> Permissions:
    """Calculates the permissions in :class:`.DMChannel` scope.

    Parameters
    ----------
    permissions: :class:`.UserPermissions`
        The user permissions.

    Returns
    -------
    :class:`.Permissions`
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
    group_permissions: typing.Optional[Permissions],
    group_recipients: list[str],
) -> Permissions:
    """Calculates the permissions in :class:`.GroupChannel` scope.

    Parameters
    ----------
    perspective_id: :class:`str`
        The ID of perspective user.
    group_owner_id: :class:`str`
        The ID of group owner (:attr:`.GroupChannel.owner_id`).
    group_permissions: Optional[:class:`.Permissions`]
        The default group permissions (:attr:`.GroupChannel.permissions`).
    group_recipients: List[:class:`str`]
        The IDs of group recipients (:attr:`.GroupChannel.recipient_ids`).

    Returns
    -------
    :class:`.Permissions`
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
    *,
    default_permissions: typing.Optional[PermissionOverride],
    role_permissions: dict[str, PermissionOverride],
) -> Permissions:
    """Calculates the permissions in :class:`.BaseServerChannel` scope.

    Parameters
    ----------
    initial_permissions: :class:`str`
        The initial permissions to use. Should be ``server.permissions_for(member)`` for members
        and :attr:`Server.default_permissions` for users.
    roles: List[:class:`.Role`]
        The member's roles. Should be empty list if calculating for :class:`.User`.
    default_permissions: :class:`str`
        The default channel permissions (:attr:`.BaseServerChannel.default_permissions`).
    role_permissions: Dict[:class:`str`, :class:`.Permissions`]
        The permissions overrides for roles in the channel (:attr:`.BaseServerChannel.role_permissions`).

    Returns
    -------
    :class:`.Permissions`
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
class SavedMessagesChannel(BaseChannel, Messageable):
    """Represents a personal "Saved Notes" channel which allows users to save messages."""

    user_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The ID of the user this channel belongs to."""

    def get_channel_id(self) -> str:
        return self.id

    def locally_update(self, data: PartialChannel, /) -> None:
        """Locally updates channel with provided data.

        .. warning::
            This is called by library internally to keep cache up to date.

        Parameters
        ----------
        data: :class:`.PartialChannel`
            The data to update channel with.
        """
        # PartialChannel has no fields that are related to SavedMessages yet
        pass

    @property
    def type(self) -> typing.Literal[ChannelType.saved_messages]:
        """Literal[:attr:`ChannelType.saved_messages`]: The channel's type."""
        return ChannelType.saved_messages

    def permissions_for(self, target: typing.Union[User, Member], /) -> Permissions:
        """Calculate permissions for given member.

        Parameters
        ----------
        target: Union[:class:`.User`, :class:`.Member`]
            The user to calculate permissions for.

        Returns
        -------
        :class:`Permissions`
            The calculated permissions.
        """

        return calculate_saved_messages_channel_permissions(target.id, self.user_id)


@define(slots=True)
class DMChannel(BaseChannel, Messageable):
    """Represents a private channel between two users."""

    active: bool = field(repr=True, kw_only=True)
    """:class:`bool`: Whether the DM channel is currently open on both sides."""

    recipient_ids: tuple[str, str] = field(repr=True, kw_only=True)
    """Tuple[:class:`str`, :class:`str`]: The tuple of user IDs participating in DM."""

    last_message_id: typing.Optional[str] = field(repr=True, kw_only=True)
    """Optional[:class:`str`]: The last message ID sent in the channel."""

    def get_channel_id(self) -> str:
        return self.id

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

    def locally_update(self, data: PartialChannel, /) -> None:
        """Locally updates channel with provided data.

        .. warning::
            This is called by library internally to keep cache up to date.

        Parameters
        ----------
        data: :class:`.PartialChannel`
            The data to update channel with.
        """
        if data.active is not UNDEFINED:
            self.active = data.active
        if data.last_message_id is not UNDEFINED:
            self.last_message_id = data.last_message_id

    @property
    def type(self) -> typing.Literal[ChannelType.private]:
        """Literal[:attr:`.ChannelType.private`]: The channel's type."""
        return ChannelType.private

    def permissions_for(self, target: typing.Union[User, Member], /) -> Permissions:
        """Calculate permissions for given user.

        Parameters
        ----------
        target: Union[:class:`.User`, :class:`.Member`]
            The member or user to calculate permissions for.

        Returns
        -------
        :class:`.Permissions`
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
class GroupChannel(BaseChannel, Messageable):
    """Represesnts Revolt group channel between 1 or more participants."""

    name: str = field(repr=True, kw_only=True)
    """:class:`str`: The group's name."""

    owner_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The user's ID who owns this group."""

    description: typing.Optional[str] = field(repr=True, kw_only=True)
    """Optional[:class:`str`]: The group description."""

    _recipients: typing.Union[
        tuple[typing.Literal[True], list[str]],
        tuple[typing.Literal[False], list[User]],
    ] = field(repr=True, kw_only=True, alias='internal_recipients')

    internal_icon: typing.Optional[StatelessAsset] = field(repr=True, kw_only=True)
    """Optional[:class:`.StatelessAsset`]: The stateless group icon."""

    last_message_id: typing.Optional[str] = field(repr=True, kw_only=True)
    """Optional[:class:`str`]: The last message ID sent in the channel."""

    raw_permissions: typing.Optional[int] = field(repr=True, kw_only=True)
    """Optional[:class:`int`]: The permissions assigned to members of this group.
    
    .. note::
        This attribute does not apply to the owner of the group.
    """

    nsfw: bool = field(repr=True, kw_only=True)
    """:class:`bool`: Whether this group is marked as not safe for work."""

    def get_channel_id(self) -> str:
        return self.id

    def locally_update(self, data: PartialChannel, /) -> None:
        """Locally updates channel with provided data.

        .. warning::
            This is called by library internally to keep cache up to date.

        Parameters
        ----------
        data: :class:`.PartialChannel`
            The data to update channel with.
        """
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
        if data.raw_permissions is not UNDEFINED:
            self.raw_permissions = data.raw_permissions
        if data.nsfw is not UNDEFINED:
            self.nsfw = data.nsfw

    def _join(self, user_id: str, /) -> None:
        if self._recipients[0]:
            self._recipients[1].append(user_id)  # type: ignore # Pyright doesn't understand `if`
        else:
            self._recipients = (True, [u.id for u in self._recipients[1]])  # type: ignore
            self._recipients[1].append(user_id)

    def _leave(self, user_id: str, /) -> None:
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
    def icon(self) -> typing.Optional[Asset]:
        """Optional[:class:`.Asset`]: The group icon."""
        return self.internal_icon and self.internal_icon.attach_state(self.state, 'icons')

    @property
    def permissions(self) -> typing.Optional[Permissions]:
        """Optional[:class:`.Permissions`]: The permissions assigned to members of this group.

        .. note::
            This attribute does not apply to the owner of the group.
        """
        if self.raw_permissions is None:
            return None
        ret = _new_permissions(Permissions)
        ret.value = self.raw_permissions
        return ret

    @property
    def recipient_ids(self) -> list[str]:
        """List[:class:`str`]: The IDs of users participating in channel."""
        if self._recipients[0]:
            return self._recipients[1]  # type: ignore
        else:
            return [u.id for u in self._recipients[1]]  # type: ignore

    @property
    def recipients(self) -> list[User]:
        """List[:class:`.User`]: The users participating in channel."""
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
        """Literal[:attr:`.ChannelType.group`]: The channel's type."""
        return ChannelType.group

    async def add(
        self,
        user: ULIDOr[BaseUser],
    ) -> None:
        """|coro|

        Adds another user to the group.

        You must have :attr:`~Permissions.create_invites` to do this.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        user: ULIDOr[:class:`.BaseUser`]
            The user to add.

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

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+--------------------------------------------------------------+
            | Value                 | Reason                                                       |
            +-----------------------+--------------------------------------------------------------+
            | ``GroupTooLarge``     | The group exceeded maximum count of recipients.              |
            +-----------------------+--------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to add the recipient. |
            +-----------------------+--------------------------------------------------------------+
            | ``NotFriends``        | You're not friends with the user you want to add.            |
            +-----------------------+--------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+-------------------------------------+
            | Value        | Reason                              |
            +--------------+-------------------------------------+
            | ``NotFound`` | The channel or user were not found. |
            +--------------+-------------------------------------+
        :class:`Conflict`
            Possible values for :attr:`~HTTPException.type`:

            +---------------------+-------------------------------+
            | Value               | Reason                        |
            +---------------------+-------------------------------+
            | ``AlreadyInGroup``  | The user is already in group. |
            +---------------------+-------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """
        return await self.state.http.add_group_recipient(self.id, user)

    async def add_bot(
        self,
        bot: ULIDOr[typing.Union[BaseBot, BaseUser]],
    ) -> None:
        """|coro|

        Invites a bot to a group.

        You must have :attr:`~Permissions.create_invites` to do this.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        bot: ULIDOr[Union[:class:`.BaseBot`, :class:`.BaseUser`]]
            The bot.
        server: Optional[ULIDOr[:class:`.BaseServer`]]
            The destination server.
        group: Optional[ULIDOr[:class:`.GroupChannel`]]
            The destination group.

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

            +----------------------+------------------------------------------------------+
            | Value                | Reason                                               |
            +----------------------+------------------------------------------------------+
            | ``IsBot``            | The current token belongs to bot account.            |
            +----------------------+------------------------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+-----------------------------------------------------+
            | Value                 | Reason                                              |
            +-----------------------+-----------------------------------------------------+
            | ``BotIsPrivate``      | You do not own the bot to add it.                   |
            +-----------------------+-----------------------------------------------------+
            | ``GroupTooLarge``     | The group exceeded maximum count of recipients.     |
            +-----------------------+-----------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to add bots. |
            +-----------------------+-----------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+-------------------------------------+
            | Value        | Reason                              |
            +--------------+-------------------------------------+
            | ``NotFound`` | The bot/group/server was not found. |
            +--------------+-------------------------------------+
        :class:`Conflict`
            Possible values for :attr:`~HTTPException.type`:

            +---------------------+-------------------------------+
            | Value               | Reason                        |
            +---------------------+-------------------------------+
            | ``AlreadyInGroup``  | The bot is already in group.  |
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
        :class:`TypeError`
            You specified ``server`` and ``group`` parameters, or passed no parameters.
        """
        return await self.state.http.invite_bot(bot, group=self.id)

    async def create_invite(self) -> Invite:
        """|coro|

        Creates an invite to channel. The destination channel must be a group or server channel.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------+----------------------------------------------------+
            | Value                | Reason                                             |
            +----------------------+----------------------------------------------------+
            | ``InvalidOperation`` | The target channel is not group or server channel. |
            +----------------------+----------------------------------------------------+
            | ``IsBot``            | The current token belongs to bot account.          |
            +----------------------+----------------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+----------------------------------------------------------------------+
            | Value                 | Reason                                                               |
            +-----------------------+----------------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to create invites in channel. |
            +-----------------------+----------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +----------------+-----------------------------------+
            | Value          | Reason                            |
            +----------------+-----------------------------------+
            | ``NotFound``   | The target channel was not found. |
            +----------------+-----------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`.Invite`
            The invite that was created.
        """

        return await self.state.http.create_channel_invite(self.id)

    async def leave(self, *, silent: typing.Optional[bool] = None) -> None:
        """|coro|

        Leaves a group or closes a group.

        You must have :attr:`~Permissions.view_channel` to do this.

        Parameters
        ----------
        silent: Optional[:class:`bool`]
            Whether to not send message when leaving.

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

            +-----------------------+---------------------------------------------------------------------------+
            | Value                 | Reason                                                                    |
            +-----------------------+---------------------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to view and/or delete the channel. |
            +-----------------------+---------------------------------------------------------------------------+
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
        """

        return await self.close(silent=silent)

    async def set_default_permissions(self, permissions: Permissions) -> GroupChannel:
        """|coro|

        Sets default permissions for everyone in a channel.

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

            +----------------------------------+--------------------------------------------------------------------------------------+
            | Value                            | Reason                                                                               |
            +----------------------------------+--------------------------------------------------------------------------------------+
            | ``CannotGiveMissingPermissions`` | Your new provided permissions contained permissions you didn't have.                 |
            +----------------------------------+--------------------------------------------------------------------------------------+
            | ``MissingPermission``            | You do not have the proper permissions to edit default permissions for this channel. |
            +----------------------------------+--------------------------------------------------------------------------------------+
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
        :class:`.GroupChannel`
            The updated group with new permissions.
        """

        result = await self.state.http.set_default_channel_permissions(self.id, permissions)
        assert isinstance(result, GroupChannel)
        return result

    def permissions_for(self, target: typing.Union[User, Member], /) -> Permissions:
        """Calculate permissions for given user.

        Parameters
        ----------
        target: Union[:class:`.User`, :class:`.Member`]
            The member or user to calculate permissions for.

        Returns
        -------
        :class:`.Permissions`
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


PrivateChannel = typing.Union[SavedMessagesChannel, DMChannel, GroupChannel]


@define(slots=True)
class BaseServerChannel(BaseChannel):
    server_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The server ID that channel belongs to."""

    name: str = field(repr=True, kw_only=True)
    """:class:`str`: The display name of the channel."""

    description: typing.Optional[str] = field(repr=True, kw_only=True)
    """Optional[:class:`str`]: The channel description."""

    internal_icon: typing.Optional[StatelessAsset] = field(repr=True, kw_only=True)
    """Optional[:class:`.StatelessAsset`]: The stateless custom channel icon."""

    default_permissions: typing.Optional[PermissionOverride] = field(repr=True, kw_only=True)
    """Optional[:class:`.PermissionOverride`]: Default permissions assigned to users in this channel."""

    role_permissions: dict[str, PermissionOverride] = field(repr=True, kw_only=True)
    """Dict[:class:`str`, :class:`.PermissionOverride`]: The permissions assigned based on role to this channel."""

    nsfw: bool = field(repr=True, kw_only=True)
    """:class:`bool`: Whether this channel is marked as not safe for work."""

    def locally_update(self, data: PartialChannel, /) -> None:
        """Locally updates channel with provided data.

        .. warning::
            This is called by library internally to keep cache up to date.

        Parameters
        ----------
        data: :class:`.PartialChannel`
            The data to update channel with.
        """
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
    def icon(self) -> typing.Optional[Asset]:
        """Optional[:class:`.Asset`]: The custom channel icon."""
        return self.internal_icon and self.internal_icon.attach_state(self.state, 'icons')

    @property
    def server(self) -> Server:
        """:class:`.Server`: The server that channel belongs to."""
        server = self.get_server()
        if server is None:
            raise NoData(self.server_id, 'channel server')
        return server

    def get_server(self) -> typing.Optional[Server]:
        """Optional[:class:`.Server`]: The server that channel belongs to."""
        cache = self.state.cache
        if cache is None:
            return None
        return cache.get_server(self.server_id, caching._USER_REQUEST)

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
        :class:`.Invite`
            The invite that was created.
        """
        return await self.state.http.create_channel_invite(self.id)

    async def delete(self) -> None:
        """|coro|

        Deletes a server channel.

        You must have :attr:`~Permissions.view_channel` and :attr:`~Permissions.manage_channels` to do this.

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

            +-----------------------+---------------------------------------------------------------------------+
            | Value                 | Reason                                                                    |
            +-----------------------+---------------------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to view and/or delete the channel. |
            +-----------------------+---------------------------------------------------------------------------+
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
        """

        return await self.close()

    async def set_role_permissions(
        self,
        role: ULIDOr[BaseRole],
        *,
        allow: Permissions = Permissions.none(),
        deny: Permissions = Permissions.none(),
    ) -> ServerChannel:
        """|coro|

        Sets permissions for the specified role in a channel.

        You must have :attr:`~Permissions.manage_permissions` to do this.

        Parameters
        ----------
        role: ULIDOr[:class:`.BaseRole`]
            The role.

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
            | ``MissingPermission``            | You do not have the proper permissions to edit overrides for this channel.           |
            +----------------------------------+--------------------------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+----------------------------------------+
            | Value        | Reason                                 |
            +--------------+----------------------------------------+
            | ``NotFound`` | The channel/server/role was not found. |
            +--------------+----------------------------------------+
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
            The updated server channel with new permissions.
        """
        result = await self.state.http.set_channel_permissions_for_role(self.id, role, allow=allow, deny=deny)
        return result

    async def set_default_permissions(self, permissions: PermissionOverride) -> ServerChannel:
        """|coro|

        Sets default permissions for everyone in a channel.

        You must have :attr:`~Permissions.manage_permissions` to do this.

        Parameters
        ----------
        permissions: :class:`.PermissionOverride`
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

            +----------------------------------+--------------------------------------------------------------------------------------+
            | Value                            | Reason                                                                               |
            +----------------------------------+--------------------------------------------------------------------------------------+
            | ``CannotGiveMissingPermissions`` | Your new provided permissions contained permissions you didn't have.                 |
            +----------------------------------+--------------------------------------------------------------------------------------+
            | ``MissingPermission``            | You do not have the proper permissions to edit default permissions for this channel. |
            +----------------------------------+--------------------------------------------------------------------------------------+
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
        :class:`.ServerChannel`
            The updated server channel with new permissions.
        """

        result = await self.state.http.set_default_channel_permissions(self.id, permissions)
        return result  # type: ignore

    def permissions_for(
        self,
        target: typing.Union[User, Member],
        /,
        *,
        safe: bool = True,
        with_ownership: bool = True,
        include_timeout: bool = True,
    ) -> Permissions:
        """Calculate permissions for given user.

        Parameters
        ----------
        target: Union[:class:`.User`, :class:`.Member`]
            The member or user to calculate permissions for.
        safe: :class:`bool`
            Whether to raise exception or not if role is missing in cache.
        with_ownership: :class:`bool`
            Whether to account for ownership.
        include_timeout: :class:`bool`
            Whether to account for timeout.

        Raises
        ------
        :class:`NoData`
            The server or role is not found in cache.

        Returns
        -------
        :class:`.Permissions`
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

        initial_permissions = calculate_server_permissions(
            [],
            None,
            default_permissions=server.default_permissions,
            can_publish=True,
            can_receive=True,
        )
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
    """Represents some voice-specific metadata for text channel."""

    max_users: int = field(repr=True, kw_only=True)
    """:class:`int`: The maximium amount of users allowed in the voice channel at once.
    
    Zero means a infinite amount of users can connect to voice channel.
    """


@define(slots=True)
class TextChannel(BaseServerChannel, Connectable, Messageable):
    """Represents a text channel that belongs to a server on Revolt."""

    last_message_id: typing.Optional[str] = field(repr=True, kw_only=True)
    """Optional[:class:`str`]: The last message ID sent in the channel."""

    voice: typing.Optional[ChannelVoiceMetadata] = field(repr=True, kw_only=True)
    """Optional[:class:`.ChannelVoiceMetadata`]: The voice's metadata in the channel."""

    def get_channel_id(self) -> str:
        return self.id

    def locally_update(self, data: PartialChannel, /) -> None:
        """Locally updates channel with provided data.

        .. warning::
            This is called by library internally to keep cache up to date.

        Parameters
        ----------
        data: :class:`.PartialChannel`
            The data to update channel with.
        """
        BaseServerChannel.locally_update(self, data)
        if data.last_message_id is not UNDEFINED:
            self.last_message_id = data.last_message_id

    @property
    def type(self) -> typing.Literal[ChannelType.text]:
        """Literal[:attr:`.ChannelType.text`]: The channel's type."""
        return ChannelType.text

    @property
    def voice_states(self) -> ChannelVoiceStateContainer:
        """:class:`.ChannelVoiceStateContainer`: Returns all voice states in the channel."""
        cache = self.state.cache
        if cache:
            res = cache.get_channel_voice_state(
                self.id,
                caching._USER_REQUEST,
            )
        else:
            res = None
        return res or ChannelVoiceStateContainer(channel_id=self.id, participants={})


@define(slots=True)
class VoiceChannel(BaseServerChannel, Connectable, Messageable):
    """Represents a voice channel that belongs to a server on Revolt.

    .. deprecated:: 0.7.0
        The voice channel type was deprecated in favour of :attr:`TextChannel.voice`.
    """

    def get_channel_id(self) -> str:
        return self.id

    @property
    def type(self) -> typing.Literal[ChannelType.voice]:
        """Literal[:attr:`.ChannelType.voice`]: The channel's type."""
        return ChannelType.voice

    @property
    def voice_states(self) -> ChannelVoiceStateContainer:
        """:class:`.ChannelVoiceStateContainer`: Returns all voice states in the channel."""
        cache = self.state.cache
        if cache is None:
            res = None
        else:
            res = cache.get_channel_voice_state(
                self.id,
                caching._USER_REQUEST,
            )
        return res or ChannelVoiceStateContainer(channel_id=self.id, participants={})


ServerChannel = typing.Union[TextChannel, VoiceChannel]
TextableChannel = typing.Union[SavedMessagesChannel, DMChannel, GroupChannel, TextChannel, VoiceChannel]
Channel = typing.Union[SavedMessagesChannel, DMChannel, GroupChannel, TextChannel, VoiceChannel]


@define(slots=True)
class ChannelVoiceStateContainer:
    """Represents voice state container for the channel."""

    channel_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The channel's ID."""

    participants: dict[str, UserVoiceState] = field(repr=True, kw_only=True)
    """Dict[:class:`str`, :class:`.UserVoiceState`]: The channel's participants."""

    def locally_add(self, state: UserVoiceState, /) -> None:
        """Locally adds user's voice state into this container.

        Parameters
        ----------
        state: :class:`.UserVoiceState`
            The state to add.
        """
        self.participants[state.user_id] = state

    def locally_remove(self, user_id: str, /) -> typing.Optional[UserVoiceState]:
        """Locally removes user's voice state from this container.

        Parameters
        ----------
        user_id: :class:`str`
            The user's ID to remove state from.

        Returns
        -------
        Optional[:class:`.UserVoiceState`]
            The removed user's voice state.
        """
        return self.participants.pop(user_id, None)


@define(slots=True)
class PartialMessageable(Messageable):
    """Represents a partial messageable to aid with working messageable channels when only a channel ID is present."""

    state: State = field(repr=False, kw_only=True)
    """:class:`.State`: The state."""

    id: str = field(repr=True, kw_only=True)
    """:class:`str`: The channel's ID."""

    def get_channel_id(self) -> str:
        return self.id


__all__ = (
    'BaseChannel',
    'PartialChannel',
    'calculate_saved_messages_channel_permissions',
    'calculate_dm_channel_permissions',
    'calculate_group_channel_permissions',
    'calculate_server_channel_permissions',
    'SavedMessagesChannel',
    'DMChannel',
    'GroupChannel',
    'PrivateChannel',
    'BaseServerChannel',
    'ChannelVoiceMetadata',
    'TextChannel',
    'VoiceChannel',
    'ServerChannel',
    'TextableChannel',
    'Channel',
    'ChannelVoiceStateContainer',
    'PartialMessageable',
)
