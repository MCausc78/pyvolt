from __future__ import annotations

from attrs import define, field
from datetime import datetime
import typing as t


from . import core

if t.TYPE_CHECKING:
    from .state import State


@define(slots=True)
class Base:
    state: State = field(repr=False, hash=True, eq=True)
    """State that controls this entity."""

    id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The unique ID of the entity."""

    @property
    def created_at(self) -> datetime:
        return core.ulid_time(self.id)


__all__ = ("Base",)
