from __future__ import annotations

from attrs import define, field
from enum import IntFlag
import typing as t

from . import cdn, core
from .base import Base
from .enums import Enum
from .permissions import UserPermissions
from .safety_reports import UserReportReason


if t.TYPE_CHECKING:
    from . import raw
    from .channel import SavedMessagesChannel, DMChannel
    from .message import BaseMessage
    from .state import State


class Presence(Enum):
    online = "Online"
    """User is online."""

    idle = "Idle"
    """User is not currently available."""

    focus = "Focus"
    """User is focusing / will only receive mentions."""

    busy = "Busy"
    """User is busy / will not receive any notifications."""

    invisible = "Invisible"
    """User appears to be offline."""


@define(slots=True)
class UserStatus:
    """User's active status."""

    text: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """Custom status text."""

    presence: Presence | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """Current presence option."""

    def _update(self, data: UserStatusEdit) -> None:
        if core.is_defined(data.text):
            self.text = data.text
        if core.is_defined(data.presence):
            self.presence = data.presence


class UserStatusEdit:
    """Patrial user's status."""

    text: core.UndefinedOr[str | None]
    """Custom status text."""

    presence: core.UndefinedOr[Presence | None]
    """Current presence option."""

    __slots__ = ("text", "presence")

    def __init__(
        self,
        *,
        text: core.UndefinedOr[str | None] = core.UNDEFINED,
        presence: core.UndefinedOr[Presence | None] = core.UNDEFINED,
    ) -> None:
        self.text = text
        self.presence = presence

    @property
    def remove(self) -> list[raw.FieldsUser]:
        r = []
        if self.text is None:
            r.append("StatusText")
        if self.presence is None:
            r.append("StatusPresence")
        return r

    def build(self) -> raw.UserStatus:
        j: raw.UserStatus = {}
        if self.text is not None and core.is_defined(self.text):
            j["text"] = self.text
        if self.presence is not None and core.is_defined(self.presence):
            j["presence"] = self.presence.value
        return j


@define(slots=True)
class StatelessUserProfile:
    """Stateless user's profile."""

    content: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The user's profile content."""

    internal_background: cdn.StatelessAsset | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
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

    state: State = field(repr=False, hash=False, kw_only=True, eq=False)
    user_id: str = field(repr=True, hash=True, kw_only=True, eq=True)

    @property
    def background(self) -> cdn.Asset | None:
        """Background visible on user's profile."""
        return self.internal_background and self.internal_background._stateful(
            self.state, "backgrounds"
        )


@define(slots=True)
class PartialUserProfile:
    """The user's profile."""

    state: State = field(repr=False, hash=False, kw_only=True, eq=False)
    """The state."""

    content: core.UndefinedOr[str | None] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The user's profile content."""

    internal_background: core.UndefinedOr[cdn.StatelessAsset | None] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The stateless background visible on user's profile."""

    @property
    def background(self) -> core.UndefinedOr[cdn.Asset | None]:
        """Background visible on user's profile."""
        return self.internal_background and self.internal_background._stateful(
            self.state, "backgrounds"
        )


class UserProfileEdit:
    """Partial user's profile."""

    content: core.UndefinedOr[str | None]
    """Text to set as user profile description."""

    background: core.UndefinedOr[cdn.ResolvableResource | None]
    """New background visible on user's profile."""

    __slots__ = ("content", "background")

    def __init__(
        self,
        content: core.UndefinedOr[str | None] = core.UNDEFINED,
        background: core.UndefinedOr[cdn.ResolvableResource | None] = core.UNDEFINED,
    ) -> None:
        self.content = content
        self.background = background

    @property
    def remove(self) -> list[raw.FieldsUser]:
        r = []
        if self.content is None:
            r.append("ProfileContent")
        if self.background is None:
            r.append("ProfileBackground")
        return r

    async def build(self, state: State) -> raw.DataUserProfile:
        j: raw.DataUserProfile = {}
        if self.content:
            j["content"] = self.content
        if self.background:
            j["background"] = await cdn.resolve_resource(
                state, self.background, tag="backgrounds"
            )
        return j


class UserBadges(IntFlag):
    """User badges bitfield."""

    NONE = 0
    """Zero badges bitfield."""

    DEVELOPER = 1 << 0
    """Revolt developer."""

    TRANSLATOR = 1 << 1
    """Helped translate Revolt."""

    SUPPORTER = 1 << 2
    """Monetarily supported Revolt."""

    RESPONSIBLE_DISCLOSURE = 1 << 3
    """Responsibly disclosed a security issue."""

    FOUNDER = 1 << 4
    """Revolt founder."""

    PLATFORM_MODERATION = 1 << 5
    """Platform moderator."""

    ACTIVE_SUPPORTER = 1 << 6
    """Active monetary supporter."""

    PAW = 1 << 7
    """🦊🦝"""

    EARLY_ADOPTER = 1 << 8
    """Joined as one of the first 1000 users in 2021."""

    RESERVED_RELEVANT_JOKE_BADGE_1 = 1 << 9
    """Amogus."""

    RESERVED_RELEVANT_JOKE_BADGE_2 = 1 << 10
    """Low resolution troll face."""


class UserFlags(IntFlag):
    """User flags bitfield."""

    NONE = 0
    """Zero badges bitfield."""

    SUSPENDED = 1 << 0
    """User has been suspended from the platform."""

    DELETED = 1 << 1
    """User has deleted their account."""

    BANNED = 1 << 2
    """User was banned off the platform."""

    SPAM = 1 << 3
    """User was marked as spam and removed from platform."""


class RelationshipStatus(Enum):
    """User's relationship with another user (or themselves)."""

    none = "None"
    """No relationship with other user."""

    user = "User"
    """Other user is us."""

    friend = "Friend"
    """Friends with the other user."""

    outgoing = "Outgoing"
    """Pending friend request to user."""

    incoming = "Incoming"
    """Incoming friend request from user."""

    blocked = "Blocked"
    """Blocked this user."""

    blocked_other = "BlockedOther"
    """Blocked by this user."""


@define(slots=True)
class Relationship:
    """Represents a relationship entry indicating current status with other user."""

    id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """Other user's ID."""

    status: RelationshipStatus = field(repr=True, hash=True, kw_only=True, eq=True)
    """Relationship status with them."""


@define(slots=True)
class Mutuals:
    """Mutual friends and servers response."""

    user_ids: list[str] = field(repr=True, hash=True, kw_only=True, eq=True)
    """Array of mutual user IDs that both users are friends with."""

    server_ids: list[str] = field(repr=True, hash=True, kw_only=True, eq=True)
    """Array of mutual server IDs that both users are in."""


class BaseUser(Base):
    """Represents a user on Revolt."""

    @property
    def mention(self) -> str:
        """The user mention."""
        return f"<@{self.id}>"

    async def accept_friend_request(self) -> User:
        """|coro|

        Accept another user's friend request.
        """
        return await self.state.http.accept_friend_request(self.id)

    async def block(self) -> User:
        """|coro|

        Block this user.
        """
        return await self.state.http.block_user(self.id)

    async def edit(
        self,
        *,
        display_name: core.UndefinedOr[str] = core.UNDEFINED,
        avatar: core.UndefinedOr[str | None] = core.UNDEFINED,
        status: core.UndefinedOr[UserStatusEdit] = core.UNDEFINED,
        profile: core.UndefinedOr[UserProfileEdit] = core.UNDEFINED,
        badges: core.UndefinedOr[UserBadges] = core.UNDEFINED,
        flags: core.UndefinedOr[UserFlags] = core.UNDEFINED,
    ) -> User:
        """|coro|

        Edits the user.

        Parameters
        ----------
        display_name: :class:`UndefinedOr`[:class:`str`] | `None`
            New display name. Set `None` to remove it.
        avatar: :class:`UndefinedOr`[:class:`str`] | `None`
            New avatar. Must be attachment ID. Set `None` to remove it.
        status: :class:`UndefinedOr`[:class:`UserStatusEdit`]
            New user status.
        profile: :class:`UndefinedOr`[:class:`UserProfileEdit`]
            New user profile data. This is applied as a partial.
        badges: :class:`UndefinedOr`[:class:`UserBadges`]
            New user badges.
        flags: :class:`UndefinedOr`[:class:`UserFlags`]
            New user flags.
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

        Retrieve a list of mutual friends with this user.
        """
        mutuals = await self.state.http.get_mutual_friends_and_servers(self.id)
        return mutuals.user_ids

    async def mutual_server_ids(self) -> list[str]:
        """|coro|

        Retrieve a list of mutual servers with this user.
        """
        mutuals = await self.state.http.get_mutual_friends_and_servers(self.id)
        return mutuals.server_ids

    async def mutuals(self) -> Mutuals:
        """|coro|

        Retrieve a list of mutual friends and servers with this user.
        """
        return await self.state.http.get_mutual_friends_and_servers(self.id)

    async def open_dm(self) -> SavedMessagesChannel | DMChannel:
        """|coro|

        Open a DM with another user. If the target is oneself, a saved messages channel is returned.
        """
        return await self.state.http.open_dm(self.id)

    async def remove_friend(self) -> User:
        """|coro|

        Denies this user's friend request or removes an existing friend.
        """
        return await self.state.http.remove_friend(self.id)

    async def report(
        self,
        reason: UserReportReason,
        *,
        additional_context: str | None = None,
        message_context: core.ULIDOr[BaseMessage],
    ) -> None:
        """|coro|

        Report a piece of content to the moderation team.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        APIError
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

        Unblock this user.
        """
        return await self.state.http.unblock_user(self.id)


@define(slots=True)
class PartialUser(BaseUser):
    """Partially represents a user on Revolt."""

    name: core.UndefinedOr[str] = field(repr=True, hash=True, kw_only=True, eq=True)
    """New username of the user."""

    discriminator: core.UndefinedOr[str] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """New discriminator of the user."""

    display_name: core.UndefinedOr[str | None] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """New display name of the user."""

    internal_avatar: core.UndefinedOr[cdn.StatelessAsset | None] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """New stateless avatar of the user."""

    badges: core.UndefinedOr[UserBadges] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """New user badges."""

    status: core.UndefinedOr[UserStatusEdit] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """New user's status."""

    profile: core.UndefinedOr[PartialUserProfile] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """New user's profile page."""

    flags: core.UndefinedOr[UserFlags] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The user flags."""

    online: core.UndefinedOr[bool] = field(repr=True, hash=True, kw_only=True, eq=True)
    """Whether this user came online."""

    @property
    def avatar(self) -> core.UndefinedOr[cdn.Asset | None]:
        """The avatar of the user."""
        return self.internal_avatar and self.internal_avatar._stateful(
            self.state, "avatars"
        )


@define(slots=True)
class DisplayUser(BaseUser):
    """Represents a user on Revolt that can be easily displayed in UI."""

    name: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The username of the user."""

    discriminator: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The discriminator of the user."""

    internal_avatar: cdn.StatelessAsset | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The stateless avatar of the user."""

    @property
    def avatar(self) -> cdn.Asset | None:
        """The avatar of the user."""
        return self.internal_avatar and self.internal_avatar._stateful(
            self.state, "avatars"
        )

    async def send_friend_request(self) -> User:
        """|coro|

        Send a friend request to this user.
        """
        return await self.state.http.send_friend_request(self.name, self.discriminator)


@define(slots=True)
class BotUserInfo:
    owner_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """ID of the owner of this bot."""


def _calculate_user_permissions(
    user_id: str,
    user_privileged: bool,
    user_relationship: RelationshipStatus,
    user_bot: BotUserInfo | None,
    *,
    perspective_id: str,
    perspective_bot: BotUserInfo | None,
) -> UserPermissions:
    if (
        user_privileged
        or user_id == perspective_id
        or user_relationship is RelationshipStatus.friend
    ):
        return UserPermissions.ALL

    if user_relationship in (
        RelationshipStatus.blocked,
        RelationshipStatus.blocked_other,
    ):
        return UserPermissions.ACCESS

    result = 0
    if user_relationship in (RelationshipStatus.incoming, RelationshipStatus.outgoing):
        result |= UserPermissions.ACCESS.value

    if user_bot or perspective_bot:
        result |= UserPermissions.SEND_MESSAGE.value

    return UserPermissions(result)


@define(slots=True)
class User(DisplayUser):
    """Represents a user on Revolt."""

    display_name: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The user display name."""

    badges: UserBadges = field(repr=True, hash=True, kw_only=True, eq=True)
    """The user badges."""

    status: UserStatus | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The current user's status."""

    flags: UserFlags = field(repr=True, hash=True, kw_only=True, eq=True)
    """The user flags."""

    privileged: bool = field(repr=True, hash=True, kw_only=True, eq=True)
    """Whether this user is privileged."""

    bot: BotUserInfo | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The information about the bot."""

    relationship: RelationshipStatus = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The current session user's relationship with this user."""

    online: bool = field(repr=True, hash=True, kw_only=True, eq=True)
    """Whether this user is currently online."""

    def _update(self, data: PartialUser) -> None:
        if core.is_defined(data.name):
            self.name = data.name
        if core.is_defined(data.discriminator):
            self.discriminator = data.discriminator
        if core.is_defined(data.display_name):
            self.display_name = data.display_name
        if core.is_defined(data.internal_avatar):
            self.internal_avatar = data.internal_avatar
        if core.is_defined(data.badges):
            self.badges = data.badges
        if core.is_defined(data.status):
            status = data.status
            if core.is_defined(status.text) and core.is_defined(status.presence):
                self.status = UserStatus(
                    text=status.text,
                    presence=status.presence,
                )
            elif self.status:
                self.status._update(status)
        if core.is_defined(data.flags):
            self.flags = data.flags
        if core.is_defined(data.online):
            self.online = data.online

    # flags
    def is_suspended(self) -> bool:
        """:class:`bool`: Whether this user has been suspended from the platform."""
        return UserFlags.SUSPENDED in self.flags

    def is_deleted(self) -> bool:
        """:class:`bool`: Whether this user is deleted his account."""
        return UserFlags.DELETED in self.flags

    def is_banned(self) -> bool:
        """:class:`bool`: Whether this user is banned off the platform."""
        return UserFlags.BANNED in self.flags

    def is_spammer(self) -> bool:
        """:class:`bool`: Whether this user was marked as spam and removed from platform."""
        return UserFlags.SPAM in self.flags

    # badges
    def is_developer(self) -> bool:
        """:class:`bool`: Whether this user is Revolt developer."""
        return UserBadges.DEVELOPER in self.badges

    def is_translator(self) -> bool:
        """:class:`bool`: Whether this user helped translate Revolt."""
        return UserBadges.TRANSLATOR in self.badges

    def is_supporter(self) -> bool:
        """:class:`bool`: Whether this user monetarily supported Revolt."""
        return UserBadges.SUPPORTER in self.badges

    def is_responsible_disclosure(self) -> bool:
        """:class:`bool`: Whether this user responsibly disclosed a security issue."""
        return UserBadges.RESPONSIBLE_DISCLOSURE in self.badges

    def is_founder(self) -> bool:
        """:class:`bool`: Whether this user is Revolt founder."""
        return UserBadges.FOUNDER in self.badges

    def is_platform_moderator(self) -> bool:
        """:class:`bool`: Whether this user is platform moderator."""
        return UserBadges.PLATFORM_MODERATION in self.badges

    def is_active_supporter(self) -> bool:
        """:class:`bool`: Whether this user is active monetary supporter."""
        return UserBadges.ACTIVE_SUPPORTER in self.badges

    def is_paw(self) -> bool:
        """:class:`bool`: Whether this user is fox/raccoon (🦊🦝)."""
        return UserBadges.PAW in self.badges

    def is_early_adopter(self) -> bool:
        """:class:`bool`: Whether this user have joined Revolt as one of the first 1000 users in 2021."""
        return UserBadges.EARLY_ADOPTER in self.badges

    def is_relevant_joke_1(self) -> bool:
        """:class:`bool`: Whether this user have given funny joke (Called "sus", displayed as Amogus in Revite)."""
        return UserBadges.RESERVED_RELEVANT_JOKE_BADGE_1 in self.badges

    def is_relevant_joke_2(self) -> bool:
        """:class:`bool`: Whether this user have given other funny joke (Called as "It's Morbin Time" in Revite)."""
        return UserBadges.RESERVED_RELEVANT_JOKE_BADGE_2 in self.badges

    async def profile(self) -> UserProfile:
        """|coro|

        Retrives user profile.

        Returns
        -------
        :class`UserProfile`
            The user's profile page.
        """
        return await self.state.http.get_user_profile(self.id)


@define(slots=True)
class SelfUser(User):
    """Representation of a user on Revolt."""

    relations: dict[str, Relationship] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The dictionary of relationships with other users."""

    async def edit(
        self,
        *,
        display_name: core.UndefinedOr[str] = core.UNDEFINED,
        avatar: core.UndefinedOr[str | None] = core.UNDEFINED,
        status: core.UndefinedOr[UserStatusEdit] = core.UNDEFINED,
        profile: core.UndefinedOr[UserProfileEdit] = core.UNDEFINED,
        badges: core.UndefinedOr[UserBadges] = core.UNDEFINED,
        flags: core.UndefinedOr[UserFlags] = core.UNDEFINED,
    ) -> User:
        """|coro|

        Edits the user.

        Parameters
        ----------
        display_name: :class:`UndefinedOr`[:class:`str`] | `None`
            New display name. Set `None` to remove it.
        avatar: :class:`UndefinedOr`[:class:`str`] | `None`
            New avatar. Must be attachment ID. Set `None` to remove it.
        status: :class:`UndefinedOr`[:class:`UserStatusEdit`]
            New user status.
        profile: :class:`UndefinedOr`[:class:`UserProfileEdit`]
            New user profile data. This is applied as a partial.
        badges: :class:`UndefinedOr`[:class:`UserBadges`]
            Bitfield of new user badges.
        flags: :class:`UndefinedOr`[:class:`UserFlags`]
            Bitfield of new user flags.
        """
        return await self.state.http.edit_self_user(
            display_name=display_name,
            avatar=avatar,
            status=status,
            profile=profile,
            badges=badges,
            flags=flags,
        )


__all__ = (
    "Presence",
    "UserStatus",
    "UserStatusEdit",
    "StatelessUserProfile",
    "UserProfile",
    "PartialUserProfile",
    "UserProfileEdit",
    "UserBadges",
    "UserFlags",
    "RelationshipStatus",
    "Relationship",
    "Mutuals",
    "BaseUser",
    "PartialUser",
    "DisplayUser",
    "BotUserInfo",
    "_calculate_user_permissions",
    "User",
    "SelfUser",
)
