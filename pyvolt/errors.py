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

import typing

if typing.TYPE_CHECKING:
    from aiohttp import ClientResponse as Response


# Thanks Rapptz/discord.py for docs


class PyvoltException(Exception):
    """Base exception class for pyvolt

    Ideally speaking, this could be caught to handle any exceptions raised from this library.
    """

    __slots__ = ()


class HTTPException(PyvoltException):
    """Exception that's raised when an HTTP request operation fails.

    Attributes
    ------------
    response: :class:`aiohttp.ClientResponse`
        The response of the failed HTTP request. This is an
        instance of :class:`aiohttp.ClientResponse`.
    data: Union[Dict[:class:`str`, Any], Any]
        The data of the error. Could be an empty string.
    status: :class:`int`
        The status code of the HTTP request.
    type: :class:`str`
        The Revolt specific error type for the failure.
    retry_after: Optional[:class:`float`]
        The duration in seconds to wait until ratelimit expires.
    error: Optional[:class:`str`]
        The validation error details.
        Only applicable when :attr:`~.type` is ``'FaliedValidation'``.
    max: Optional[:class:`int`]
        The maximum count of entities.
        Only applicable when :attr:`~.type` one of following values:

        - ``'FileTooLarge'``
        - ``'GroupTooLarge'``
        - ``'TooManyAttachments'``
        - ``'TooManyChannels'``
        - ``'TooManyEmbeds'``
        - ``'TooManyEmoji'``
        - ``'TooManyPendingFriendRequests'``
        - ``'TooManyReplies'``
        - ``'TooManyRoles'``
        - ``'TooManyServers'``
    permission: Optional[:class:`str`]
        The permission required to perform request.
        Only applicable when :attr:`~.type` one of following values:
        - ``'MissingPermission'``
        - ``'MissingUserPermission'``
    operation: Optional[:class:`str`]
        The database operation that failed.
        Only applicable when :attr:`~.type` is ``'DatabaseError'``.
    collection: Optional[:class:`str`]
        The collection's name the operation was on.
        Not always available when :attr:`~.type` is ``'DatabaseError'``.
    location: Optional[:class:`str`]
        The path to Rust location where error occured.
    with_: Optional[:class:`str`]
        The collection's name the operation was on.
        Only applicable when :attr:`~.type` one of following values:
        - ``'IncorrectData'``

        Not always available when :attr:`~.type` is ``'DatabaseError'``.
    feature: Optional[:class:`str`]
        The feature that was disabled.
        Only applicable when :attr:`~.type` is ``'FeatureDisabled'``.

        Possible values:

        - ``'features.mass_mentions_enabled'``
    """

    # response: Response
    # type: str
    # retry_after: typing.Optional[float]
    # error: typing.Optional[str]
    # max: typing.Optional[int]
    # permission: typing.Optional[str]
    # operation: typing.Optional[str]
    # collection: typing.Optional[str]
    # location: typing.Optional[str]
    # with_: typing.Optional[str]

    __slots__ = (
        'response',
        'data',
        'type',
        'retry_after',
        'error',
        'max',
        'permission',
        'operation',
        'collection',
        'location',
        'with_',
        'feature',
    )

    def __init__(
        self,
        response: Response,
        data: typing.Union[dict[str, typing.Any], str],
        /,
    ) -> None:
        self.response: Response = response
        self.data: typing.Union[dict[str, typing.Any], str] = data
        self.status: int = response.status

        errors = []

        if isinstance(data, str):
            self.type: str = 'NonJSON'
            self.retry_after: typing.Optional[float] = None
            self.error: typing.Optional[str] = data
            errors.append(data)
            self.max: typing.Optional[int] = None
            self.permission: typing.Optional[str] = None
            self.operation: typing.Optional[str] = None
            self.collection: typing.Optional[str] = None
            self.location: typing.Optional[str] = None
            self.with_: typing.Optional[str] = None
            self.feature: typing.Optional[str] = None
        else:
            self.type = data.get('type', 'Unknown')

            self.retry_after = data.get('retry_after', 0)
            if self.retry_after is not None:
                errors.append(f'retry_after={self.retry_after}')

            self.error = data.get('error')
            if self.error is not None:
                errors.append(f'error={self.error}')

            self.max = data.get('max')
            if self.max is not None:
                errors.append(f'max={self.max}')

            self.permission = data.get('permission')
            if self.permission is not None:
                errors.append(f'permission={self.permission}')

            self.operation = data.get('operation')
            if self.operation is not None:
                errors.append(f'operation={self.operation}')

            self.collection = data.get('collection')
            if self.collection is not None:
                errors.append(f'collection={self.collection}')

            self.location = data.get('location')
            if self.location is not None:
                errors.append(f'location={self.location}')

            self.with_ = data.get('with')
            if self.with_ is not None:
                errors.append(f'with={self.with_}')

            self.feature = data.get('feature')
            if self.feature is not None:
                errors.append(f'feature={self.feature}')

        super().__init__(
            f'{self.type} (raw={data})' if len(errors) == 0 else f"{self.type}: {' '.join(errors)} (raw={data})\n"
        )


class NoEffect(PyvoltException):
    """HTTP exception that corresponds to HTTP 200 status code.

    This exists because Revolt API returns 200 with error body for some reason.
    """

    __slots__ = ('data',)

    def __init__(
        self,
        data: dict[str, typing.Any],
        /,
    ) -> None:
        self.data: dict[str, typing.Any] = data


class Unauthorized(HTTPException):
    """HTTP exception that corresponds to HTTP 401 status code."""

    __slots__ = ()


class Forbidden(HTTPException):
    """HTTP exception that corresponds to HTTP 403 status code."""

    __slots__ = ()


class NotFound(HTTPException):
    """HTTP exception that corresponds to HTTP 404 status code."""

    __slots__ = ()


class Conflict(HTTPException):
    """HTTP exception that corresponds to HTTP 409 status code."""

    __slots__ = ()


class Ratelimited(HTTPException):
    """HTTP exception that corresponds to HTTP 429 status code."""

    __slots__ = ()


class InternalServerError(HTTPException):
    """HTTP exception that corresponds to HTTP 5xx status code."""

    __slots__ = ()


class BadGateway(HTTPException):
    """HTTP exception that corresponds to HTTP 502 status code."""

    __slots__ = ()


class ShardError(PyvoltException):
    """Exception that's raised when any shard-related
    error happens.
    """

    __slots__ = ()


class ShardClosedError(ShardError):
    """Exception that's raised when shard
    was already closed.
    """

    __slots__ = ()


class AuthenticationError(ShardError):
    """Exception that's raised when WebSocket
    authentication fails.

    Attributes
    ----------
    payload: Optional[Dict[:class:`str`, Any]]
        The WebSocket payload.
    """

    __slots__ = ()

    def __init__(self, payload: dict[str, typing.Any], /) -> None:
        self.payload: dict[str, typing.Any] = payload
        super().__init__(f'Failed to connect shard: {payload}')


class ConnectError(ShardError):
    """Exception that's raised when the library fails
    to connect to Revolt WebSocket.

    Attributes
    ----------
    errors: List[:exc:`Exception`]
        The errors.
    """

    __slots__ = ('errors',)

    def __init__(self, tries: int, errors: list[Exception], /) -> None:
        self.errors: list[Exception] = errors
        super().__init__(f'Giving up, after {tries} tries, last 3 errors: {errors[-3:]}')


class DiscoverError(PyvoltException):
    __slots__ = ('response', 'status', 'data')

    def __init__(
        self,
        response: Response,
        status: int,
        data: str,
        /,
    ) -> None:
        self.response: Response = response
        self.status: int = status
        self.data: str = data
        super().__init__(status, data)


class InvalidData(PyvoltException):
    """Exception that's raised when the library encounters unknown
    or invalid data from Revolt.
    """

    __slots__ = ('reason',)

    def __init__(self, reason: str, /) -> None:
        self.reason: str = reason
        super().__init__(reason)


class NoData(PyvoltException):
    """Exception that's raised when the library did not found
    data requested from cache.

    This is different from :exc:`.NotFound`.
    """

    __slots__ = ('what', 'type')

    def __init__(self, what: str, type: str) -> None:
        self.what = what
        self.type = type
        super().__init__(f'Unable to find {type} {what} in cache')


__all__ = (
    'PyvoltException',
    'HTTPException',
    'NoEffect',
    'Unauthorized',
    'Forbidden',
    'NotFound',
    'Conflict',
    'Ratelimited',
    'InternalServerError',
    'BadGateway',
    'ShardError',
    'ShardClosedError',
    'AuthenticationError',
    'ConnectError',
    'DiscoverError',
    'InvalidData',
    'NoData',
)
