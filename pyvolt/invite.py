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

from .cdn import StatelessAsset, Asset

if typing.TYPE_CHECKING:
    from .channel import GroupChannel
    from .server import ServerFlags, Server
    from .state import State


@define(slots=True)
class BaseInvite:
    """Representation of a invite on Revolt."""

    state: State = field(repr=False, kw_only=True)
    """State that controls this invite."""

    code: str = field(repr=True, kw_only=True)
    """The invite code."""

    def __hash__(self) -> int:
        return hash(self.code)

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, BaseInvite) and self.code == other.code

    async def accept(self) -> Server | GroupChannel:
        """|coro|

        Accept this invite.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        Forbidden
            You're banned.
        HTTPException
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
        HTTPException
            Deleting the invite failed.
        """
        return await self.state.http.delete_invite(self.code)

    async def revoke(self) -> None:
        """|coro|

        Alias to :meth:`.delete`.

        Raises
        ------
        Forbidden
            You do not have permissions to delete invite or not creator of that invite.
        HTTPException
            Deleting the invite failed.
        """
        return await self.state.http.delete_invite(self.code)


@define(slots=True)
class ServerPublicInvite(BaseInvite):
    """Server channel invite."""

    server_id: str = field(repr=True, kw_only=True)
    """The ID of the server."""

    server_name: str = field(repr=True, kw_only=True)
    """The name of the server."""

    internal_server_icon: StatelessAsset | None = field(repr=True, kw_only=True)
    """The stateless icon of the server."""

    internal_server_banner: StatelessAsset | None = field(repr=True, kw_only=True)
    """The stateless banner of the server."""

    flags: ServerFlags | None = field(repr=True, kw_only=True)
    """The server flags."""

    channel_id: str = field(repr=True, kw_only=True)
    """The ID of destination channel."""

    channel_name: str = field(repr=True, kw_only=True)
    """The name of destination channel."""

    channel_description: str | None = field(repr=True, kw_only=True)
    """The description of destination channel."""

    user_name: str = field(repr=True, kw_only=True)
    """The name of inviter."""

    internal_user_avatar: StatelessAsset | None = field(repr=True, kw_only=True)
    """The stateless avatar of the inviter."""

    members_count: int = field(repr=True, kw_only=True)
    """The count of members in this server."""

    def server_icon(self) -> Asset | None:
        """Optional[:class:`Asset`]: The icon of the server."""
        return self.internal_server_icon and self.internal_server_icon._stateful(self.state, 'icons')

    def server_banner(self) -> Asset | None:
        """Optional[:class:`Asset`]: The banner of the server."""
        return self.internal_server_banner and self.internal_server_banner._stateful(self.state, 'banners')

    async def accept(self) -> Server:
        """|coro|

        Accept this invite.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        Forbidden
            You're banned.
        HTTPException
            Accepting the invite failed.
        """
        server = await super().accept()
        return server  # type: ignore


@define(slots=True)
class GroupPublicInvite(BaseInvite):
    """Group channel invite."""

    channel_id: str = field(repr=True, kw_only=True)
    """The ID of the destination channel."""

    channel_name: str = field(repr=True, kw_only=True)
    """The name of destination channel."""

    channel_description: str | None = field(repr=True, kw_only=True)
    """The description of destination channel."""

    user_name: str = field(repr=True, kw_only=True)
    """The name of inviter."""

    internal_user_avatar: StatelessAsset | None = field(repr=True, kw_only=True)
    """The stateless avatar of the inviter."""

    @property
    def user_avatar(self) -> Asset | None:
        """Optional[:class:`Asset`]: The avatar of the inviter."""
        return self.internal_user_avatar and self.internal_user_avatar._stateful(self.state, 'avatars')

    async def accept(self) -> GroupChannel:
        """|coro|

        Accept this invite.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        Forbidden
            You're banned.
        HTTPException
            Accepting the invite failed.
        """
        group = await super().accept()
        return group  # type: ignore


@define(slots=True)
class UnknownPublicInvite(BaseInvite):
    payload: dict[str, typing.Any] = field(repr=True, kw_only=True)
    """The raw invite data."""


@define(slots=True)
class PrivateBaseInvite(BaseInvite):
    """Representation of a invite on Revolt."""

    creator_id: str = field(repr=True, kw_only=True)
    """The ID of the user who created this invite."""


@define(slots=True)
class GroupInvite(PrivateBaseInvite):
    """Representation of a group invite on Revolt."""

    channel_id: str = field(repr=True, kw_only=True)
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
        HTTPException
            Accepting the invite failed.
        """
        group = await super().accept()
        return group  # type: ignore


@define(slots=True)
class ServerInvite(PrivateBaseInvite):
    """Representation of a server invite on Revolt."""

    server_id: str = field(repr=True, kw_only=True)
    """ID of the server this invite points to."""

    channel_id: str = field(repr=True, kw_only=True)
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
        HTTPException
            Accepting the invite failed.
        """
        server = await super().accept()
        return server  # type: ignore


Invite = GroupInvite | ServerInvite

__all__ = (
    'BaseInvite',
    'ServerPublicInvite',
    'GroupPublicInvite',
    'UnknownPublicInvite',
    'PrivateBaseInvite',
    'GroupInvite',
    'ServerInvite',
    'Invite',
)
