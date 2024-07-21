from __future__ import annotations

from datetime import datetime, timezone
import typing
from .ulid import _ulid_timestamp


class Undefined:
    """Undefined sentinel"""

    __slots__ = ()

    def __init__(self) -> None:
        pass

    def __bool__(self) -> typing.Literal[False]:
        return False


UNDEFINED = Undefined()


T = typing.TypeVar('T')
UndefinedOr = Undefined | T


def is_defined(x: UndefinedOr[T]) -> typing.TypeGuard[T]:
    return x is not UNDEFINED and not isinstance(x, Undefined)


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
Z = '00000000000000000000000000'

__version__: str = '1.0.0'

__all__ = (
    'Undefined',
    'UNDEFINED',
    'T',
    'UndefinedOr',
    'is_defined',
    'ulid_timestamp',
    'ulid_time',
    'HasID',
    'ULIDOr',
    'resolve_id',
    '__version__',
    'Z',
)
