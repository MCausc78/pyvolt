from __future__ import annotations

from datetime import datetime, timezone
import typing

from .enums import Enum
from .ulid import _ulid_timestamp


class _Sentinel(Enum):
    """The library sentinels."""

    _undefined = 'UNDEFINED'

    def __bool__(self) -> typing.Literal[False]:
        return False

    def __repr__(self) -> typing.Literal['UNDEFINED']:
        return self.value


Undefined: typing.TypeAlias = typing.Literal[_Sentinel._undefined]
UNDEFINED: Undefined = _Sentinel._undefined


T = typing.TypeVar('T')
UndefinedOr = Undefined | T


def ulid_timestamp(val: str) -> float:
    return _ulid_timestamp(val.encode('ascii'))


def ulid_time(val: str) -> datetime:
    return datetime.fromtimestamp(ulid_timestamp(val), timezone.utc)


class HasID(typing.Protocol):
    id: str


U = typing.TypeVar('U', bound='HasID')
ULIDOr = str | U


def resolve_id(resolvable: ULIDOr) -> str:
    if isinstance(resolvable, str):
        return resolvable
    return resolvable.id


# zero ID
ZID = '00000000000000000000000000'

__version__: str = '0.7.0'

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
