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
from .flags import ServerFlags

if typing.TYPE_CHECKING:
    from .channel import GroupChannel
    from .server import Server
    from .state import State

_new_server_flags = ServerFlags.__new__


@define(slots=True)
class BaseInvite:
    """Represents a invite on Revolt."""

    state: State = field(repr=False, kw_only=True)
    """:class:`.State`: State that controls this invite."""

    code: str = field(repr=True, kw_only=True)
    """:class:`str`: The invite's code."""

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
    """Represents a public invite to server channel."""

    server_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The server's ID this invite points to."""

    server_name: str = field(repr=True, kw_only=True)
    """:class:`str`: The server's name."""

    internal_server_icon: StatelessAsset | None = field(repr=True, kw_only=True)
    """Optional[:class:`.StatelessAsset`]: The server's stateless icon."""

    internal_server_banner: StatelessAsset | None = field(repr=True, kw_only=True)
    """Optional[:class:`.StatelessAsset`]: The server's stateless banner.."""

    raw_server_flags: int = field(repr=True, kw_only=True)
    """:class:`int`: The server's flags raw value."""

    channel_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The destination channel's ID."""

    channel_name: str = field(repr=True, kw_only=True)
    """:class:`str`: The destination channel's name."""

    channel_description: str | None = field(repr=True, kw_only=True)
    """Optional[:class:`str`]: The destination channel's description."""

    user_name: str = field(repr=True, kw_only=True)
    """:class:`str`: The user's name who created this invite."""

    internal_user_avatar: StatelessAsset | None = field(repr=True, kw_only=True)
    """Optional[:class:`.StatelessAsset`]: The user's stateless avatar who created this invite."""

    member_count: int = field(repr=True, kw_only=True)
    """:class:`int`: The count of members in target server."""

    @property
    def server_flags(self) -> ServerFlags:
        """:class:`.ServerFlags`: The server's flags."""
        ret = _new_server_flags(ServerFlags)
        ret.value = self.raw_server_flags
        return ret

    @property
    def server_icon(self) -> Asset | None:
        """Optional[:class:`.Asset`]: The icon of the server."""
        return self.internal_server_icon and self.internal_server_icon._stateful(self.state, 'icons')

    @property
    def server_banner(self) -> Asset | None:
        """Optional[:class:`.Asset`]: The banner of the server."""
        return self.internal_server_banner and self.internal_server_banner._stateful(self.state, 'banners')

    @property
    def user_avatar(self) -> Asset | None:
        """Optional[:class:`.Asset`]: The user's avatar who created this invite."""
        return self.internal_user_avatar and self.internal_user_avatar._stateful(self.state, 'avatars')

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
    """Represents a public invite to group channel."""

    channel_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The destination channel's ID."""

    channel_name: str = field(repr=True, kw_only=True)
    """:class:`str`: The destination channel's name."""

    channel_description: str | None = field(repr=True, kw_only=True)
    """Optional[:class:`str`]: The destination channel's description."""

    user_name: str = field(repr=True, kw_only=True)
    """:class:`str`: The user's name who created this invite."""

    internal_user_avatar: StatelessAsset | None = field(repr=True, kw_only=True)
    """Optional[:class:`.StatelessAsset`]: The user's stateless avatar who created this invite."""

    @property
    def user_avatar(self) -> Asset | None:
        """Optional[:class:`Asset`]: The user's avatar who created this invite."""
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
    """Represents a public invite that is not recognized by library yet."""

    payload: dict[str, typing.Any] = field(repr=True, kw_only=True)
    """Dict[:class:`str`, Any]: The raw invite data."""


@define(slots=True)
class PrivateBaseInvite(BaseInvite):
    """Represents a private invite on Revolt."""

    creator_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The user's ID who created this invite."""


@define(slots=True)
class GroupInvite(PrivateBaseInvite):
    """Represents a group invite on Revolt."""

    channel_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The group's ID this invite points to."""

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
    """Represents a server invite on Revolt."""

    server_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The server's ID this invite points to."""

    channel_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The channel's ID this invite points to."""

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
