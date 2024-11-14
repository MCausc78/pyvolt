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

from . import routes
from .abc import Messageable, Connectable
from .base import Base
from .cdn import StatelessAsset, Asset, ResolvableResource, resolve_resource
from .core import (
    UNDEFINED,
    UndefinedOr,
    ULIDOr,
)
from .flags import UserPermissions, UserBadges, UserFlags
from .enums import UserReportReason, Presence, RelationshipStatus


if typing.TYPE_CHECKING:
    from . import raw
    from .channel import SavedMessagesChannel, DMChannel
    from .message import BaseMessage
    from .state import State

_new_user_badges = UserBadges.__new__
_new_user_flags = UserFlags.__new__


@define(slots=True)
class UserStatus:
    """Represents user's active status."""

    text: str | None = field(repr=True, kw_only=True)
    """The custom status text."""

    presence: Presence | None = field(repr=True, kw_only=True)
    """The current presence option."""

    def locally_update(self, data: UserStatusEdit, /) -> None:
        """Locally updates user status with provided data.

        .. warn::
            This is called by library internally to keep cache up to date.
        """
        if data.text is not UNDEFINED:
            self.text = data.text
        if data.presence is not UNDEFINED:
            self.presence = data.presence


class UserStatusEdit:
    """Represents partial user's status.

    Attributes
    ----------
    text: :class:`UndefinedOr`[Optional[:class:`str`]]
        The new custom status text.
    presence: :class:`UndefinedOr`[Optional[:class:`Presence`]]
        The presence to use.
    """

    __slots__ = ('text', 'presence')

    def __init__(
        self,
        *,
        text: UndefinedOr[str | None] = UNDEFINED,
        presence: UndefinedOr[Presence | None] = UNDEFINED,
    ) -> None:
        self.text = text
        self.presence = presence

    @property
    def remove(self) -> list[raw.FieldsUser]:
        remove: list[raw.FieldsUser] = []
        if self.text is None:
            remove.append('StatusText')
        if self.presence is None:
            remove.append('StatusPresence')
        return remove

    def build(self) -> raw.UserStatus:
        payload: raw.UserStatus = {}
        if self.text not in (None, UNDEFINED):
            payload['text'] = self.text
        if self.presence not in (None, UNDEFINED):
            payload['presence'] = self.presence.value
        return payload


@define(slots=True)
class StatelessUserProfile:
    """The stateless user's profile."""

    content: str | None = field(repr=True, kw_only=True)
    """The user's profile content."""

    internal_background: StatelessAsset | None = field(repr=True, kw_only=True)
    """The stateless background visible on user's profile."""

    def _stateful(self, state: State, user_id: str) -> UserProfile:
        return UserProfile(
            content=self.content,
            internal_background=self.internal_background,
            state=state,
            user_id=user_id,
        )


@define(slots=True)
class UserProfile(StatelessUserProfile):
    """User's profile."""

    state: State = field(repr=False, kw_only=True)
    user_id: str = field(repr=True, kw_only=True)

    @property
    def background(self) -> Asset | None:
        """Background visible on user's profile."""
        return self.internal_background and self.internal_background._stateful(self.state, 'backgrounds')


@define(slots=True)
class PartialUserProfile:
    """The user's profile."""

    state: State = field(repr=False, kw_only=True)
    """The state."""

    content: UndefinedOr[str | None] = field(repr=True, kw_only=True)
    """The user's profile content."""

    internal_background: UndefinedOr[StatelessAsset | None] = field(repr=True, kw_only=True)
    """The stateless background visible on user's profile."""

    @property
    def background(self) -> UndefinedOr[Asset | None]:
        """:class:`UndefinedOr`[Optional[:class:`Asset`]]: The background visible on user's profile."""
        return self.internal_background and self.internal_background._stateful(self.state, 'backgrounds')


class UserProfileEdit:
    """Partially represents user's profile.

    Attributes
    ----------
    content: :class:`UndefinedOr`[Optional[:class:`str`]]
        The text to use in user profile description.
    background: :class:`UndefinedOr`[Optional[:class:`ResolvableResource`]]
        The background to use on user's profile.
    """

    __slots__ = ('content', 'background')

    def __init__(
        self,
        content: UndefinedOr[str | None] = UNDEFINED,
        *,
        background: UndefinedOr[ResolvableResource | None] = UNDEFINED,
    ) -> None:
        self.content = content
        self.background = background

    @property
    def remove(self) -> list[raw.FieldsUser]:
        remove: list[raw.FieldsUser] = []
        if self.content is None:
            remove.append('ProfileContent')
        if self.background is None:
            remove.append('ProfileBackground')
        return remove

    async def build(self, state: State, /) -> raw.DataUserProfile:
        payload: raw.DataUserProfile = {}
        if self.content:
            payload['content'] = self.content
        if self.background:
            payload['background'] = await resolve_resource(state, self.background, tag='backgrounds')
        return payload


@define(slots=True)
class Relationship:
    """Represents a relationship entry indicating current status with other user."""

    id: str = field(repr=True, kw_only=True)
    """The user's ID the relationship with."""

    status: RelationshipStatus = field(repr=True, kw_only=True)
    """The relationship status with them."""

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, Relationship) and self.id == other.id and self.status == other.status


@define(slots=True)
class Mutuals:
    """Mutual friends and servers response."""

    user_ids: list[str] = field(repr=True, kw_only=True)
    """Array of mutual user IDs that both users are friends with."""

    server_ids: list[str] = field(repr=True, kw_only=True)
    """Array of mutual server IDs that both users are in."""


class BaseUser(Base, Connectable, Messageable):
    """Represents a user on Revolt."""

    async def fetch_channel_id(self) -> str:
        channel_id = self.dm_channel_id
        if channel_id:
            return channel_id

        channel = await self.open_dm()
        return channel.id

    def get_channel_id(self) -> str:
        return self.dm_channel_id or ''

    def is_sentinel(self) -> bool:
        """:class:`bool`: Returns whether the user is sentinel (Revolt#0000)."""
        return self is self.state.system

    def __eq__(self, other: object, /) -> bool:
        from .server import BaseMember

        return self is other or isinstance(other, (BaseUser, BaseMember)) and self.id == other.id

    @property
    def mention(self) -> str:
        """:class:`str`: The user mention."""
        return f'<@{self.id}>'

    @property
    def default_avatar_url(self) -> str:
        """:class:`str`: The URL to user's default avatar."""
        return self.state.http.url_for(routes.USERS_GET_DEFAULT_AVATAR.compile(user_id=self.id))

    @property
    def dm_channel_id(self) -> str | None:
        """Optional[:class:`str`]: The ID of the private channel with this user."""
        cache = self.state.cache
        if cache:
            from .cache import _USER_REQUEST as USER_REQUEST

            return cache.get_private_channel_by_user(self.id, USER_REQUEST)

    pm_id = dm_channel_id

    @property
    def dm_channel(self) -> DMChannel | None:
        """Optional[:class:`DMChannel`]: The private channel with this user."""
        dm_channel_id = self.dm_channel_id

        cache = self.state.cache
        if cache and dm_channel_id:
            from .cache import _USER_REQUEST as USER_REQUEST

            channel = cache.get_channel(dm_channel_id, USER_REQUEST)
            if isinstance(channel, DMChannel):
                return channel

    pm = dm_channel

    async def accept_friend_request(self) -> User:
        """|coro|

        Accepts the incoming friend request.
        """
        return await self.state.http.accept_friend_request(self.id)

    async def block(self) -> User:
        """|coro|

        Blocks the user.
        """
        return await self.state.http.block_user(self.id)

    async def edit(
        self,
        *,
        display_name: UndefinedOr[str] = UNDEFINED,
        avatar: UndefinedOr[str | None] = UNDEFINED,
        status: UndefinedOr[UserStatusEdit] = UNDEFINED,
        profile: UndefinedOr[UserProfileEdit] = UNDEFINED,
        badges: UndefinedOr[UserBadges] = UNDEFINED,
        flags: UndefinedOr[UserFlags] = UNDEFINED,
    ) -> User:
        """|coro|

        Edits the user.

        Parameters
        ----------
        display_name: :class:`UndefinedOr`[Optional[:class:`str`]]
            New display name. Pass ``None`` to remove it.
        avatar: :class:`UndefinedOr`[Optional[:class:`ResolvableResource`]]
            New avatar. Pass ``None`` to remove it.
        status: :class:`UndefinedOr`[:class:`UserStatusEdit`]
            New user status.
        profile: :class:`UndefinedOr`[:class:`UserProfileEdit`]
            New user profile data. This is applied as a partial.
        badges: :class:`UndefinedOr`[:class:`UserBadges`]
            The new user badges.
        flags: :class:`UndefinedOr`[:class:`UserFlags`]
            The new user flags.

        Raises
        ------
        HTTPException
            Editing the user failed.

        Returns
        -------
        :class:`User`
            The newly updated user.
        """
        return await self.state.http.edit_user(
            self.id,
            display_name=display_name,
            avatar=avatar,
            status=status,
            profile=profile,
            badges=badges,
            flags=flags,
        )

    async def deny_friend_request(self) -> User:
        """|coro|

        Denies this user's friend request.
        """
        return await self.state.http.deny_friend_request(self.id)

    async def mutual_friend_ids(self) -> list[str]:
        """|coro|

        Retrieves a list of mutual friends with this user.
        """
        mutuals = await self.state.http.get_mutuals_with(self.id)
        return mutuals.user_ids

    async def mutual_server_ids(self) -> list[str]:
        """|coro|

        Retrieves a list of mutual servers with this user.
        """
        mutuals = await self.state.http.get_mutuals_with(self.id)
        return mutuals.server_ids

    async def mutuals(self) -> Mutuals:
        """|coro|

        Retrieve a list of mutual friends and servers with this user.
        """
        return await self.state.http.get_mutuals_with(self.id)

    async def open_dm(self) -> SavedMessagesChannel | DMChannel:
        """|coro|

        Open a DM with another user. If the target is oneself, a saved messages channel is returned.
        """
        return await self.state.http.open_dm(self.id)

    async def fetch_profile(self) -> UserProfile:
        """|coro|

        Retrives user profile.

        Returns
        -------
        :class`UserProfile`
            The user's profile page.
        """
        return await self.state.http.get_user_profile(self.id)

    async def remove_friend(self) -> User:
        """|coro|

        Removes the user as a friend.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        HTTPException
            Removing the user as a friend failed.
        """
        return await self.state.http.remove_friend(self.id)

    async def report(
        self,
        reason: UserReportReason,
        *,
        additional_context: str | None = None,
        message_context: ULIDOr[BaseMessage],
    ) -> None:
        """|coro|

        Report a piece of content to the moderation team.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        HTTPException
            You're trying to self-report, or reporting the user failed.
        """
        return await self.state.http.report_user(
            self.id,
            reason,
            additional_context=additional_context,
            message_context=message_context,
        )

    async def unblock(self) -> User:
        """|coro|

        Unblocks the user.
        """
        return await self.state.http.unblock_user(self.id)


@define(slots=True)
class PartialUser(BaseUser):
    """Represents a partial user on Revolt."""

    name: UndefinedOr[str] = field(repr=True, kw_only=True)
    """The new user's name."""

    discriminator: UndefinedOr[str] = field(repr=True, kw_only=True)
    """The new user's discriminator."""

    display_name: UndefinedOr[str | None] = field(repr=True, kw_only=True)
    """The new user's display name."""

    internal_avatar: UndefinedOr[StatelessAsset | None] = field(repr=True, kw_only=True)
    """The new user's stateless avatar."""

    raw_badges: UndefinedOr[int] = field(repr=True, kw_only=True)
    """The new user's badges raw value."""

    status: UndefinedOr[UserStatusEdit] = field(repr=True, kw_only=True)
    """The new user's status."""

    # internal_profile: UndefinedOr[PartialUserProfile] = field(repr=True, kw_only=True)
    # """The new user's profile page."""

    raw_flags: UndefinedOr[int] = field(repr=True, kw_only=True)
    """The user's flags raw value."""

    online: UndefinedOr[bool] = field(repr=True, kw_only=True)
    """Whether the user came online."""

    @property
    def avatar(self) -> UndefinedOr[Asset | None]:
        """:class:`UndefinedOr`[Optional[:class:`Asset`]]: The new user's avatar."""
        if self.internal_avatar in (None, UNDEFINED):
            return self.internal_avatar
        return self.internal_avatar._stateful(self.state, 'avatars')

    @property
    def badges(self) -> UndefinedOr[UserBadges]:
        """:class:`UndefinedOr`[:class:`UserBadges`]: The new user's badges."""
        if self.raw_badges is UNDEFINED:
            return self.raw_badges
        ret = _new_user_badges(UserBadges)
        ret.value = self.raw_badges
        return ret

    @property
    def flags(self) -> UndefinedOr[UserFlags]:
        """:class:`UndefinedOr`[:class:`UserFlags`]: The user's flags."""
        if self.raw_flags is UNDEFINED:
            return self.raw_flags
        ret = _new_user_flags(UserFlags)
        ret.value = self.raw_flags
        return ret


@define(slots=True)
class DisplayUser(BaseUser):
    """Represents a user on Revolt that can be easily displayed in UI."""

    name: str = field(repr=True, kw_only=True)
    """The username of the user."""

    discriminator: str = field(repr=True, kw_only=True)
    """The discriminator of the user."""

    internal_avatar: StatelessAsset | None = field(repr=True, kw_only=True)
    """The stateless avatar of the user."""

    def __str__(self) -> str:
        return self.name

    @property
    def avatar(self) -> Asset | None:
        """Optional[:class:`Asset`]: The avatar of the user."""
        return self.internal_avatar and self.internal_avatar._stateful(self.state, 'avatars')

    @property
    def tag(self) -> str:
        """:class:`str`: The tag of the user.

        Assuming that :attr:`User.name` is ``'vlf'`` and :attr:`User.discriminator` is ``'3510'``,
        example output would be ``'vlf#3510'``.
        """
        return f'{self.name}#{self.discriminator}'

    async def send_friend_request(self) -> User:
        """|coro|

        Sends the user a friend request.

        Raises
        ------
        Forbidden
            Not allowed to send a friend request to the user.
        HTTPException
            Sending the friend request failed.
        """
        return await self.state.http.send_friend_request(self.name, self.discriminator)


@define(slots=True)
class BotUserInfo:
    owner_id: str = field(repr=True, kw_only=True)
    """The ID of the owner of this bot."""

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, BotUserInfo) and self.owner_id == other.owner_id


def calculate_user_permissions(
    user_id: str,
    user_relationship: RelationshipStatus,
    user_bot: BotUserInfo | None,
    /,
    *,
    perspective_id: str,
    perspective_bot: BotUserInfo | None,
    perspective_privileged: bool,
) -> UserPermissions:
    """Calculates the permissions between two users.

    Parameters
    ----------
    user_id: :class:`str`
        The target ID.
    user_relationship: :class:`RelationshipStatus`
        The relationship between us and target user (:attr:`User.relationship`).
    user_bot: Optional[:class:`BotUserInfo`]
        The bot information about the user (:attr:`User.bot`), if applicable.
    perspective_id: :class:`str`
        The ID of the current user.
    perspective_bot: Optional[:class:`BotUserInfo`]
        The bot information about the current user (:attr:`User.bot`), if applicable.
    perspective_privileged: :class:`bool`
        Whether the current user is privileged (:attr:`User.privileged`).

    Returns
    -------
    :class:`UserPermissions`
        The calculated permissions.
    """
    if perspective_privileged or user_id == perspective_id or user_relationship is RelationshipStatus.friend:
        return UserPermissions.all()

    if user_relationship in (
        RelationshipStatus.blocked,
        RelationshipStatus.blocked_other,
    ):
        return UserPermissions(access=True)

    return UserPermissions(
        access=user_relationship in (RelationshipStatus.incoming, RelationshipStatus.outgoing),
        send_messages=bool(user_bot or perspective_bot),
    )


@define(slots=True)
class User(DisplayUser):
    """Represents a user on Revolt."""

    display_name: str | None = field(repr=True, kw_only=True)
    """The user's display name."""

    raw_badges: int = field(repr=True, kw_only=True)
    """The user's badges raw value."""

    status: UserStatus | None = field(repr=True, kw_only=True)
    """The current user's status."""

    raw_flags: int = field(repr=True, kw_only=True)
    """The user's flags raw value."""

    privileged: bool = field(repr=True, kw_only=True)
    """Whether the user is privileged."""

    bot: BotUserInfo | None = field(repr=True, kw_only=True)
    """The information about the bot."""

    relationship: RelationshipStatus = field(repr=True, kw_only=True)
    """The current session user's relationship with this user."""

    online: bool = field(repr=True, kw_only=True)
    """Whether the user is currently online."""

    def locally_update(self, data: PartialUser, /) -> None:
        """Locally updates user with provided data.

        .. warn::
            This is called by library internally to keep cache up to date.
        """
        if data.name is not UNDEFINED:
            self.name = data.name
        if data.discriminator is not UNDEFINED:
            self.discriminator = data.discriminator
        if data.display_name is not UNDEFINED:
            self.display_name = data.display_name
        if data.internal_avatar is not UNDEFINED:
            self.internal_avatar = data.internal_avatar
        if data.raw_badges is not UNDEFINED:
            self.raw_badges = data.raw_badges
        if data.status is not UNDEFINED:
            status = data.status
            if status.text is not UNDEFINED and status.presence is not UNDEFINED:
                self.status = UserStatus(
                    text=status.text,
                    presence=status.presence,
                )
            elif self.status:
                self.status.locally_update(status)
        if data.raw_flags is not UNDEFINED:
            self.raw_flags = data.raw_flags
        if data.online is not UNDEFINED:
            self.online = data.online

    @property
    def badges(self) -> UserBadges:
        """The user's badges."""
        ret = _new_user_badges(UserBadges)
        ret.value = self.raw_badges
        return ret

    @property
    def flags(self) -> UserFlags:
        """The user's badges."""
        ret = _new_user_flags(UserFlags)
        ret.value = self.raw_flags
        return ret

    # flags
    def is_suspended(self) -> bool:
        """:class:`bool`: Whether this user has been suspended from the platform."""
        return self.flags.suspended

    def is_deleted(self) -> bool:
        """:class:`bool`: Whether this user is deleted his account."""
        return self.flags.deleted

    def is_banned(self) -> bool:
        """:class:`bool`: Whether this user is banned off the platform."""
        return self.flags.banned

    def is_spammer(self) -> bool:
        """:class:`bool`: Whether this user was marked as spam and removed from platform."""
        return self.flags.spam

    # badges
    def is_developer(self) -> bool:
        """:class:`bool`: Whether this user is Revolt developer."""
        return self.badges.developer

    def is_translator(self) -> bool:
        """:class:`bool`: Whether this user helped translate Revolt."""
        return self.badges.translator

    def is_supporter(self) -> bool:
        """:class:`bool`: Whether this user monetarily supported Revolt."""
        return self.badges.supporter

    def is_responsible_disclosure(self) -> bool:
        """:class:`bool`: Whether this user responsibly disclosed a security issue."""
        return self.badges.responsible_disclosure

    def is_founder(self) -> bool:
        """:class:`bool`: Whether this user is Revolt founder."""
        return self.badges.founder

    def is_platform_moderator(self) -> bool:
        """:class:`bool`: Whether this user is platform moderator."""
        return self.badges.platform_moderation

    def is_active_supporter(self) -> bool:
        """:class:`bool`: Whether this user is active monetary supporter."""
        return self.badges.active_supporter

    def is_paw(self) -> bool:
        """:class:`bool`: Whether this user likes fox/raccoon (🦊🦝)."""
        return self.badges.paw

    def is_early_adopter(self) -> bool:
        """:class:`bool`: Whether this user have joined Revolt as one of the first 1000 users in 2021."""
        return self.badges.early_adopter

    def is_relevant_joke_1(self) -> bool:
        """:class:`bool`: Whether this user have given funny joke (Called "sus", displayed as Amogus in Revite)."""
        return self.badges.reserved_relevant_joke_badge_1

    def is_relevant_joke_2(self) -> bool:
        """:class:`bool`: Whether this user have given other funny joke (Called as "It's Morbin Time" in Revite)."""
        return self.badges.reserved_relevant_joke_badge_2


@define(slots=True)
class OwnUser(User):
    """Represents a current user on Revolt."""

    relations: dict[str, Relationship] = field(repr=True, kw_only=True)
    """The dictionary of relationships with other users."""

    async def edit(
        self,
        *,
        display_name: UndefinedOr[str] = UNDEFINED,
        avatar: UndefinedOr[str | None] = UNDEFINED,
        status: UndefinedOr[UserStatusEdit] = UNDEFINED,
        profile: UndefinedOr[UserProfileEdit] = UNDEFINED,
        badges: UndefinedOr[UserBadges] = UNDEFINED,
        flags: UndefinedOr[UserFlags] = UNDEFINED,
    ) -> User:
        """|coro|

        Edits the user.

        Parameters
        ----------
        display_name: :class:`UndefinedOr`[Optional[:class:`str`]]
            New display name. Pass ``None`` to remove it.
        avatar: :class:`UndefinedOr`[Optional[:class:`ResolvableResource`]]
            New avatar. Pass ``None`` to remove it.
        status: :class:`UndefinedOr`[:class:`UserStatusEdit`]
            New user status.
        profile: :class:`UndefinedOr`[:class:`UserProfileEdit`]
            New user profile data. This is applied as a partial.
        badges: :class:`UndefinedOr`[:class:`UserBadges`]
            The new user badges.
        flags: :class:`UndefinedOr`[:class:`UserFlags`]
            The new user flags.

        Raises
        ------
        HTTPException
            Editing the user failed.

        Returns
        -------
        :class:`OwnUser`
            The newly updated authenticated user.
        """
        return await self.state.http.edit_my_user(
            display_name=display_name,
            avatar=avatar,
            status=status,
            profile=profile,
            badges=badges,
            flags=flags,
        )


@define(slots=True)
class UserVoiceState:
    """Represents a voice state for the user."""

    user_id: str = field(repr=True, kw_only=True)
    """The user's ID this voice state belongs to."""

    can_publish: bool = field(repr=True, kw_only=True)
    """Whether the user can send voice data."""

    can_receive: bool = field(repr=True, kw_only=True)
    """Whether the user can receive voice data."""

    screensharing: bool = field(repr=True, kw_only=True)
    """Whether the user is sharing their screen."""

    camera: bool = field(repr=True, kw_only=True)
    """Whether the user is sharing their camera."""

    def locally_update(self, data: PartialUserVoiceState, /) -> None:
        """Locally updates voice state with provided data.

        .. warn::
            This is called by library internally to keep cache up to date.
        """

        if data.can_publish is not UNDEFINED:
            self.can_publish = data.can_publish

        if data.can_receive is not UNDEFINED:
            self.can_receive = data.can_receive

        if data.screensharing is not UNDEFINED:
            self.screensharing = data.screensharing

        if data.camera is not UNDEFINED:
            self.camera = data.camera


@define(slots=True)
class PartialUserVoiceState:
    """Represents a partial voice state for the user.

    Unmodified fields will have ``UNDEFINED`` value.
    """

    user_id: str = field(repr=True, kw_only=True)
    """The user's ID this voice state belongs to."""

    can_publish: UndefinedOr[bool] = field(repr=True, kw_only=True)
    """Whether the user can send voice data."""

    can_receive: UndefinedOr[bool] = field(repr=True, kw_only=True)
    """Whether the user can receive voice data."""

    screensharing: UndefinedOr[bool] = field(repr=True, kw_only=True)
    """Whether the user is sharing their screen."""

    camera: UndefinedOr[bool] = field(repr=True, kw_only=True)
    """Whether the user is sharing their camera."""


__all__ = (
    'UserStatus',
    'UserStatusEdit',
    'StatelessUserProfile',
    'UserProfile',
    'PartialUserProfile',
    'UserProfileEdit',
    'Relationship',
    'Mutuals',
    'BaseUser',
    'PartialUser',
    'DisplayUser',
    'BotUserInfo',
    'calculate_user_permissions',
    'User',
    'OwnUser',
    'UserVoiceState',
    'PartialUserVoiceState',
)
