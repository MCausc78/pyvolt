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

from datetime import datetime, timezone
from enum import Enum
import typing

from .ulid import _ulid_timestamp


class _Sentinel(Enum):
    """The library sentinels."""

    undefined = 'UNDEFINED'

    def __bool__(self) -> typing.Literal[False]:
        return False

    def __repr__(self) -> typing.Literal['UNDEFINED']:
        return self.value

    def __eq__(self, other: object, /) -> bool:
        return self is other


Undefined: typing.TypeAlias = typing.Literal[_Sentinel.undefined]
UNDEFINED: Undefined = _Sentinel.undefined


T = typing.TypeVar('T')
UndefinedOr = Undefined | T


def ulid_timestamp(val: str, /) -> float:
    return _ulid_timestamp(val.encode('ascii'))


def ulid_time(val: str, /) -> datetime:
    return datetime.fromtimestamp(ulid_timestamp(val), timezone.utc)


class HasID(typing.Protocol):
    id: str


U = typing.TypeVar('U', bound='HasID')
ULIDOr = str | U


def resolve_id(resolvable: ULIDOr[U], /) -> str:
    if isinstance(resolvable, str):
        return resolvable
    return resolvable.id


# zero ID
ZID = '00000000000000000000000000'

__version__: str = '0.8.0'

__all__ = (
    'Undefined',
    'UNDEFINED',
    'T',
    'UndefinedOr',
    'ulid_timestamp',
    'ulid_time',
    'HasID',
    'ULIDOr',
    'resolve_id',
    '__version__',
    'ZID',
)
