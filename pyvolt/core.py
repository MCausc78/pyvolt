from collections.abc import MutableMapping
import datetime
import typing as t
import ulid


class Undefined:
    """Undefined sentinel"""

    __slots__ = ()

    def __init__(self) -> None:
        pass

    def __bool__(self) -> t.Literal[False]:
        return False


UNDEFINED = Undefined()


T = t.TypeVar("T")
UndefinedOr = Undefined | T


def is_defined(x: UndefinedOr[T]) -> t.TypeGuard[T]:
    return x is not UNDEFINED and not isinstance(x, Undefined)


class ULID(str):
    EPOCH: int = 1420070400000

    @property
    def timestamp(self) -> float:
        return ulid.parse(self).timestamp().timestamp

    @property
    def created_at(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self.timestamp)


class HasID(t.Protocol):
    id: ULID


ResolvableULID = ULID | HasID | str


def resolve_ulid(resolvable: ResolvableULID) -> ULID:
    if isinstance(resolvable, ULID):
        return resolvable
    if isinstance(resolvable, str):
        return ULID(resolvable)
    return resolvable.id


__version__: str = "1.0.0"

__all__ = (
    "Undefined",
    "UNDEFINED",
    "T",
    "UndefinedOr",
    "is_defined",
    "ULID",
    "HasID",
    "ResolvableULID",
    "resolve_ulid",
    "__version__",
)
