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
    """Represents a partial Revolt account."""

    id: str = field(repr=True, kw_only=True, eq=True)
    """:class:`str`: The unique account ID."""

    email: str = field(repr=True, kw_only=True)
    """:class:`str`: The email associated with this account."""

    def __hash__(self) -> int:
        return hash(self.id)


@define(slots=True, eq=True)
class MFATicket:
    """The MFA ticket."""

    id: str = field(repr=True, kw_only=True, eq=True)
    """:class:`str`: The unique ticket ID."""

    account_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The associated account ID."""

    token: str = field(repr=True, kw_only=True)
    """:class:`str`: The unique token."""

    validated: bool = field(repr=True, kw_only=True)
    """:class:`bool`: Whether this ticket has been validated (can be used for account actions)."""

    authorized: bool = field(repr=True, kw_only=True)
    """:class:`bool`: Whether this ticket is authorized (can be used to log a user in)."""

    last_totp_code: typing.Optional[str] = field(repr=True, kw_only=True)
    """Optional[:class:`str`]: The TOTP code at time of ticket creation."""

    def __hash__(self) -> int:
        return hash(self.id)


@define(slots=True)
class WebPushSubscription:
    """Represents WebPush subscription."""

    endpoint: str = field(repr=True, kw_only=True)
    """:class:`str`: The HTTP `endpoint <https://developer.mozilla.org/en-US/docs/Web/API/PushSubscription/endpoint>`_ associated with push subscription."""

    p256dh: str = field(repr=True, kw_only=True)
    """:class:`str`: The `Elliptic curve Diffie–Hellman public key on the P-256 curve <https://developer.mozilla.org/en-US/docs/Web/API/PushSubscription/getKey#p256dh>`_."""

    auth: str = field(repr=True, kw_only=True)
    """:class:`str`: The `authentication secret <https://developer.mozilla.org/en-US/docs/Web/API/PushSubscription/getKey#auth>`_."""


@define(slots=True)
class PartialSession(Base):
    """Represents partial Revolt authentication session."""

    name: str = field(repr=True, kw_only=True)
    """:class:`str`: The user-friendly client name."""

    async def edit(self, *, friendly_name: UndefinedOr[str] = UNDEFINED) -> PartialSession:
        """|coro|

        Edits the session.

        Parameters
        ----------
        friendly_name: UndefinedOr[:class:`str`]
            The new user-friendly client name.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------------------------------+
            | Value              | Reason                                                         |
            +--------------------+----------------------------------------------------------------+
            | ``InvalidSession`` | One of these:                                                  |
            |                    |                                                                |
            |                    | - The current user token is invalid.                           |
            |                    | - The session you tried to edit didn't belong to your account. |
            +--------------------+----------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------+----------------------------+
            | Value           | Reason                     |
            +-----------------+----------------------------+
            | ``UnknownUser`` | The session was not found. |
            +-----------------+----------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+----------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                           |
            +-------------------+------------------------------------------------+----------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.operation`, :attr:`~HTTPException.with_` |
            +-------------------+------------------------------------------------+----------------------------------------------------------------+

        Returns
        -------
        :class:`.PartialSession`
            The newly updated session.
        """

        if friendly_name is UNDEFINED:
            return PartialSession(
                state=self.state,
                id=self.id,
                name=self.name,
            )
        return await self.state.http.edit_session(
            self.id,
            friendly_name=friendly_name,
        )

    async def revoke(self) -> None:
        """|coro|

        Deletes the session.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+------------------------------------------------------+
            | Value              | Reason                                               |
            +--------------------+------------------------------------------------------+
            | ``InvalidSession`` | The current user token is invalid.                   |
            +--------------------+------------------------------------------------------+
            | ``InvalidToken``   | The provided session did not belong to your account. |
            +--------------------+------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------+-------------------------------------+
            | Value           | Reason                              |
            +-----------------+-------------------------------------+
            | ``UnknownUser`` | The provided session was not found. |
            +-----------------+-------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+----------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                           |
            +-------------------+------------------------------------------------+----------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.operation`, :attr:`~HTTPException.with_` |
            +-------------------+------------------------------------------------+----------------------------------------------------------------+
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
    friendly_name: typing.Optional[str] = field(repr=True, kw_only=True)

    async def use_recovery_code(
        self, code: str, *, friendly_name: UndefinedOr[typing.Optional[str]] = UNDEFINED
    ) -> typing.Union[Session, AccountDisabled]:
        """|coro|

        Complete MFA login flow.

        Parameters
        ----------
        code: :class:`str`
            The valid recovery code.
        friendly_name: UndefinedOr[Optional[:class:`str`]]
            The user-friendly client name. If set to :data:`.UNDEFINED`, this defaults to :attr:`.friendly_name`.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------------+------------------------------------------------------+
            | Value                   | Reason                                               |
            +-------------------------+------------------------------------------------------+
            | ``DisallowedMFAMethod`` | You tried to use disallowed MFA verification method. |
            +-------------------------+------------------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +------------------+----------------------------------------+
            | Value            | Reason                                 |
            +------------------+----------------------------------------+
            | ``InvalidToken`` | The provided recovery code is invalid. |
            +------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+------------------------------------------------------------+
            | Value                 | Reason                                                     |
            +-----------------------+------------------------------------------------------------+
            | ``LockedOut``         | The account was locked out.                                |
            +-----------------------+------------------------------------------------------------+
            | ``UnverifiedAccount`` | The account you tried to log into is currently unverified. |
            +-----------------------+------------------------------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+----------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                           |
            +-------------------+------------------------------------------------+----------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.operation`, :attr:`~HTTPException.with_` |
            +-------------------+------------------------------------------------+----------------------------------------------------------------+

        Returns
        -------
        Union[:class:`.Session`, :class:`.AccountDisabled`]
            The session if successfully logged in, or :class:`.AccountDisabled` containing user ID associated with the account.
        """

        if friendly_name is UNDEFINED:
            friendly_name = self.friendly_name

        return await self.state.http.login_with_mfa(
            self.ticket,
            ByRecoveryCode(code),
            friendly_name=friendly_name,
        )

    async def use_totp(
        self, code: str, *, friendly_name: UndefinedOr[typing.Optional[str]] = UNDEFINED
    ) -> typing.Union[Session, AccountDisabled]:
        """|coro|

        Complete MFA login flow.

        Parameters
        ----------
        code: :class:`str`
            The valid TOTP code.
        friendly_name: UndefinedOr[Optional[:class:`str`]]
            The user-friendly client name. If set to :data:`.UNDEFINED`, this defaults to :attr:`.friendly_name`.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------------+------------------------------------------------------+
            | Value                   | Reason                                               |
            +-------------------------+------------------------------------------------------+
            | ``DisallowedMFAMethod`` | You tried to use disallowed MFA verification method. |
            +-------------------------+------------------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +------------------+------------------------------------+
            | Value            | Reason                             |
            +------------------+------------------------------------+
            | ``InvalidToken`` | The provided TOTP code is invalid. |
            +------------------+------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+------------------------------------------------------------+
            | Value                 | Reason                                                     |
            +-----------------------+------------------------------------------------------------+
            | ``LockedOut``         | The account was locked out.                                |
            +-----------------------+------------------------------------------------------------+
            | ``UnverifiedAccount`` | The account you tried to log into is currently unverified. |
            +-----------------------+------------------------------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+----------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                           |
            +-------------------+------------------------------------------------+----------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.operation`, :attr:`~HTTPException.with_` |
            +-------------------+------------------------------------------------+----------------------------------------------------------------+

        Returns
        -------
        Union[:class:`.Session`, :class:`.AccountDisabled`]
            The session if successfully logged in, or :class:`.AccountDisabled` containing user ID associated with the account.
        """

        if friendly_name is UNDEFINED:
            friendly_name = self.friendly_name

        return await self.state.http.login_with_mfa(self.ticket, ByTOTP(code), friendly_name=self.friendly_name)


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
    """Represents a MFA verification way."""

    __slots__ = ()


class ByPassword(BaseMFAResponse):
    """Represents MFA verification by password.

    Attributes
    ----------
    password: :class:`str`
        The password.
    """

    __slots__ = ('password',)

    def __init__(self, password: str) -> None:
        self.password = password

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, ByPassword) and self.password == other.password

    def to_dict(self) -> raw.a.PasswordMFAResponse:
        return {'password': self.password}


class ByRecoveryCode(BaseMFAResponse):
    """Represents MFA verification by recovery code.

    Attributes
    ----------
    code: :class:`str`
        The recovery code.
    """

    __slots__ = ('code',)

    def __init__(self, code: str, /) -> None:
        self.code = code

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, ByRecoveryCode) and self.code == other.code

    def to_dict(self) -> raw.a.RecoveryMFAResponse:
        return {'recovery_code': self.code}


class ByTOTP(BaseMFAResponse):
    """Represents MFA verification by TOTP code.

    Attributes
    ----------
    code: :class:`str`
        The TOTP code.
    """

    __slots__ = ('code',)

    def __init__(self, code: str, /) -> None:
        self.code = code

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, ByTOTP) and self.code == other.code

    def to_dict(self) -> raw.a.TotpMFAResponse:
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
