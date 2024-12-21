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
from datetime import datetime
import typing


from .core import ulid_time

if typing.TYPE_CHECKING:
    from .state import State


@define(slots=True)
class Base:
    state: State = field(repr=False, kw_only=True)
    """:class:`.State`: The state that controls this entity."""

    id: str = field(repr=True, kw_only=True)
    """:class:`str`: The ID of the entity."""

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, self.__class__) and self.id == other.id

    @property
    def created_at(self) -> datetime:
        return ulid_time(self.id)


__all__ = ('Base',)
