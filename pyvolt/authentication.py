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

from .base import Base
from .core import UNDEFINED, UndefinedOr
from .enums import MFAMethod

if typing.TYPE_CHECKING:
    from .state import State
    from . import raw


@define(slots=True, eq=True)
class PartialAccount:
    id: str = field(repr=True, kw_only=True, eq=True)
    """:class:`str`: The unique account ID."""

    email: str = field(repr=True, kw_only=True)
    """:class:`str`: The email associated with this account."""

    def __hash__(self) -> int:
        return hash(self.id)


@define(slots=True, eq=True)
class MFATicket:
    """The Multi-factor authentication ticket."""

    id: str = field(repr=True, kw_only=True, eq=True)
    """:class:`str`: The unique ticket ID."""

    account_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The associated account ID."""

    token: str = field(repr=True, kw_only=True)
    """:class:`str`: The unique token."""

    validated: bool = field(repr=True, kw_only=True)
    """:class:`bool`: Whether this ticket has been validated (can be used for account actions)."""

    authorised: bool = field(repr=True, kw_only=True)
    """:class:`bool`: Whether this ticket is authorised (can be used to log a user in)."""

    last_totp_code: typing.Optional[str] = field(repr=True, kw_only=True)
    """Optional[:class:`str`]: The TOTP code at time of ticket creation."""

    def __hash__(self) -> int:
        return hash(self.id)


@define(slots=True)
class WebPushSubscription:
    """Represents WebPush subscription."""

    endpoint: str = field(repr=True, kw_only=True)
    p256dh: str = field(repr=True, kw_only=True)
    auth: str = field(repr=True, kw_only=True)


@define(slots=True)
class PartialSession(Base):
    """Represents partial Revolt auth session."""

    name: str = field(repr=True, kw_only=True)
    """:class:`str`: The session friendly name."""

    async def edit(self, *, friendly_name: UndefinedOr[str]) -> PartialSession:
        """|coro|

        Edits the session.
        """
        return await self.state.http.edit_session(
            self.id,
            friendly_name=friendly_name if friendly_name is not UNDEFINED else self.name,
        )

    async def revoke(self) -> None:
        """|coro|

        Deletes this session.
        """
        return await self.state.http.revoke_session(self.id)


@define(slots=True)
class Session(PartialSession):
    """The session information."""

    user_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The ID of associated user."""

    token: str = field(repr=True, kw_only=True)
    """:class:`str`: The session token."""

    subscription: typing.Optional[WebPushSubscription] = field(repr=True, kw_only=True)
    """Optional[:class:`.WebPushSubscription`]: The Web Push subscription associated with this session."""


@define(slots=True)
class MFARequired:
    """The password is valid, but MFA is required."""

    ticket: str = field(repr=True, kw_only=True)
    """:class:`str`: The MFA ticket."""

    allowed_methods: list[MFAMethod] = field(repr=True, kw_only=True)
    """List[:class:`.MFAMethod`]: The allowed methods."""

    # internals
    state: State = field(repr=True, kw_only=True)
    internal_friendly_name: typing.Optional[str] = field(repr=True, kw_only=True)

    async def use_recovery_code(self, code: str, /) -> typing.Union[Session, AccountDisabled]:
        """|coro|

        Login to an account.
        """
        return await self.state.http.login_with_mfa(
            self.ticket, ByRecoveryCode(code), friendly_name=self.internal_friendly_name
        )

    async def use_totp(self, code: str, /) -> typing.Union[Session, AccountDisabled]:
        """|coro|

        Login to an account.
        """
        return await self.state.http.login_with_mfa(
            self.ticket, ByTOTP(code), friendly_name=self.internal_friendly_name
        )


@define(slots=True)
class AccountDisabled:
    """The password/MFA are valid, but account is disabled."""

    user_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The ID of the disabled user account."""


@define(slots=True, eq=True)
class MFAStatus:
    totp_mfa: bool = field(repr=True, kw_only=True, eq=True)
    """:class:`bool`: Whether the account has MFA TOTP enabled."""

    recovery_active: bool = field(repr=True, kw_only=True, eq=True)
    """:class:`bool`: Whether the account has recovery codes."""


class BaseMFAResponse:
    __slots__ = ()


class ByPassword(BaseMFAResponse):
    __slots__ = ('password',)

    def __init__(self, password: str, /) -> None:
        self.password = password

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, ByPassword) and self.password == other.password

    def build(self) -> raw.a.PasswordMFAResponse:
        return {'password': self.password}


class ByRecoveryCode(BaseMFAResponse):
    __slots__ = ('code',)

    def __init__(self, code: str, /) -> None:
        self.code = code

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, ByRecoveryCode) and self.code == other.code

    def build(self) -> raw.a.RecoveryMFAResponse:
        return {'recovery_code': self.code}


class ByTOTP(BaseMFAResponse):
    __slots__ = ('code',)

    def __init__(self, code: str, /) -> None:
        self.code = code

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, ByTOTP) and self.code == other.code

    def build(self) -> raw.a.TotpMFAResponse:
        return {'totp_code': self.code}


MFAResponse = typing.Union[ByPassword, ByRecoveryCode, ByTOTP]
LoginResult = typing.Union[Session, MFARequired, AccountDisabled]

__all__ = (
    'PartialAccount',
    'MFATicket',
    'WebPushSubscription',
    'PartialSession',
    'Session',
    'MFARequired',
    'AccountDisabled',
    'MFAStatus',
    'BaseMFAResponse',
    'ByPassword',
    'ByRecoveryCode',
    'ByTOTP',
    'MFAResponse',
    'LoginResult',
)
