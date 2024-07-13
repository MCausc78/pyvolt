from __future__ import annotations

from attrs import define, field
import typing as t


from . import cdn, core

from .server import ServerFlags, Server
from .state import State

if t.TYPE_CHECKING:
    from .channel import GroupChannel


@define(slots=True)
class BaseInvite:
    """Representation of a invite on Revolt."""

    state: State = field(repr=False, hash=True, eq=True)
    """State that controls this invite."""

    code: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The invite code."""

    async def accept(self) -> Server | GroupChannel:
        """|coro|

        Accept this invite.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        Forbidden
            You're banned.
        APIError
            Accepting the invite failed.
        """
        return await self.state.http.accept_invite(self.code)

    async def delete(self) -> None:
        """|coro|

        Delete an invite.

        Raises
        ------
        Forbidden
            You do not have permissions to delete invite or not creator of that invite.
        APIError
            Deleting the invite failed.
        """
        await self.state.http.delete_invite(self.code)

    async def revoke(self) -> None:
        """|coro|

        Alias to :meth:`BaseInvite.delete`.

        Raises
        ------
        Forbidden
            You do not have permissions to delete invite or not creator of that invite.
        APIError
            Deleting the invite failed.
        """
        return await self.delete()


@define(slots=True)
class ServerPublicInvite(BaseInvite):
    """Server channel invite."""

    server_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The ID of the server."""

    server_name: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The name of the server."""

    internal_server_icon: cdn.StatelessAsset | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The stateless icon of the server."""

    internal_server_banner: cdn.StatelessAsset | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The stateless banner of the server."""

    flags: ServerFlags | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The server flags."""

    channel_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The ID of destination channel."""

    channel_name: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The name of destination channel."""

    channel_description: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The description of destination channel."""

    user_name: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The name of inviter."""

    internal_user_avatar: cdn.StatelessAsset | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The stateless avatar of the inviter."""

    members_count: int = field(repr=True, hash=True, kw_only=True, eq=True)
    """The count of members in this server."""

    def server_icon(self) -> cdn.Asset | None:
        """The icon of the server."""
        return self.internal_server_icon and self.internal_server_icon._stateful(
            self.state, "icons"
        )

    def server_banner(self) -> cdn.Asset | None:
        """The banner of the server."""
        return self.internal_server_banner and self.internal_server_banner._stateful(
            self.state, "banners"
        )

    async def accept(self) -> Server:
        """|coro|

        Accept this invite.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        Forbidden
            You're banned.
        APIError
            Accepting the invite failed.
        """
        server = await super().accept()
        return server  # type: ignore


@define(slots=True)
class GroupPublicInvite(BaseInvite):
    """Group channel invite."""

    channel_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The ID of the destination channel."""

    channel_name: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The name of destination channel."""

    channel_description: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The description of destination channel."""

    user_name: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The name of inviter."""

    internal_user_avatar: cdn.StatelessAsset | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The stateless avatar of the inviter."""

    @property
    def user_avatar(self) -> cdn.Asset | None:
        """The avatar of the inviter."""
        return self.internal_user_avatar and self.internal_user_avatar._stateful(
            self.state, "avatars"
        )

    async def accept(self) -> GroupChannel:
        """|coro|

        Accept this invite.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        Forbidden
            You're banned.
        APIError
            Accepting the invite failed.
        """
        group = await super().accept()
        return group  # type: ignore


@define(slots=True)
class UnknownPublicInvite(BaseInvite):
    d: dict[str, t.Any] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The raw invite data."""


@define(slots=True)
class PrivateBaseInvite(BaseInvite):
    """Representation of a invite on Revolt."""

    creator_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The ID of the user who created this invite."""


@define(slots=True)
class GroupInvite(PrivateBaseInvite):
    """Representation of a group invite on Revolt."""

    channel_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """ID of the server/group channel this invite points to."""

    async def accept(self) -> GroupChannel:
        """|coro|

        Accept this invite.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        Forbidden
            You're banned.
        APIError
            Accepting the invite failed.
        """
        group = await super().accept()
        return group  # type: ignore


@define(slots=True)
class ServerInvite(PrivateBaseInvite):
    """Representation of a server invite on Revolt."""

    server_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """ID of the server this invite points to."""

    channel_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """ID of the server channel this invite points to."""

    async def accept(self) -> Server:
        """|coro|

        Accept this invite.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        Forbidden
            You're banned.
        APIError
            Accepting the invite failed.
        """
        server = await super().accept()
        return server  # type: ignore


Invite = GroupInvite | ServerInvite

__all__ = (
    "BaseInvite",
    "ServerPublicInvite",
    "GroupPublicInvite",
    "UnknownPublicInvite",
    "PrivateBaseInvite",
    "GroupInvite",
    "ServerInvite",
    "Invite",
)
