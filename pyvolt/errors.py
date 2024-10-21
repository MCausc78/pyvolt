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

import aiohttp
import typing

Response = aiohttp.ClientResponse


class PyvoltError(Exception):
    __slots__ = ()


class HTTPException(PyvoltError):
    response: Response
    type: str
    retry_after: float | None
    error: str | None
    max: int | None
    permission: str | None
    operation: str | None
    collection: str | None
    location: str | None
    with_: str | None

    __slots__ = (
        'response',
        'data',
        'type',
        'retry_after',
        'err',
        'max',
        'permission',
        'operation',
        'collection',
        'location',
        'with_',
    )

    def __init__(
        self,
        response: Response,
        data: dict[str, typing.Any] | str,
        /,
        *,
        message: str | None = None,
    ) -> None:
        self.response = response
        self.data = data
        errors = []
        if message is not None:
            errors.append(message)
        if isinstance(data, str):
            self.type = 'NonJSON'
            self.retry_after = None
            self.err = data
            errors.append(data)
            self.max = None
            self.permission = None
            self.operation = None
            self.collection = None
            self.location = None
            self.with_ = None
        else:
            self.type = data.get('type', 'Unknown')
            self.retry_after = data.get('retry_after')
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
        super().__init__(self.type if len(errors) == 0 else f"{self.type}: {' '.join(errors)} (raw={data})\n")


class Unauthorized(HTTPException):
    __slots__ = ()


class Forbidden(HTTPException):
    __slots__ = ()


class NotFound(HTTPException):
    __slots__ = ()


class Ratelimited(HTTPException):
    __slots__ = ()


class InternalServerError(HTTPException):
    __slots__ = ()


class BadGateway(HTTPException):
    __slots__ = ()


class ShardError(PyvoltError):
    __slots__ = ()


class AuthenticationError(ShardError):
    __slots__ = ()

    def __init__(self, a: typing.Any, /) -> None:
        self.message: typing.Any = a
        super().__init__('Failed to connect shard', a)


class ConnectError(ShardError):
    __slots__ = ('errors',)

    def __init__(self, tries: int, errors: list[Exception], /) -> None:
        self.errors = errors
        super().__init__(f'Giving up, after {tries} tries, last 3 errors:', errors[-3:])


class DiscoverError(PyvoltError):
    __slots__ = ('response', 'status', 'data')

    def __init__(
        self,
        response: aiohttp.ClientResponse,
        status: int,
        data: str,
        /,
    ) -> None:
        self.response: aiohttp.ClientResponse = response
        self.status: int = status
        self.data: str = data
        super().__init__(status, data)


# Thanks Danny for docs
class InvalidData(PyvoltError):
    """Exception that's raised when the library encounters unknown
    or invalid data from Revolt.
    """

    __slots__ = ('reason',)

    def __init__(self, reason: str, /) -> None:
        self.reason: str = reason
        super().__init__(reason)


class NoData(PyvoltError):
    __slots__ = ('what', 'type')

    def __init__(self, what: str, type: str) -> None:
        self.what = what
        self.type = type
        super().__init__(f'Unable to find {type} {what} in cache')


__all__ = (
    'PyvoltError',
    'HTTPException',
    'Unauthorized',
    'Forbidden',
    'NotFound',
    'Ratelimited',
    'InternalServerError',
    'BadGateway',
    'ShardError',
    'AuthenticationError',
    'ConnectError',
    'DiscoverError',
    'InvalidData',
    'NoData',
)
