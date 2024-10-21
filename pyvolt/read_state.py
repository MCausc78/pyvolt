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

if typing.TYPE_CHECKING:
    from .state import State


@define(slots=True)
class ReadState:
    """Represents the read state of a channel."""

    state: State = field(repr=False, hash=False, kw_only=True, eq=False)

    channel_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The channel's ID the read state for."""

    user_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The user's ID the read state belongs to."""

    last_acked_message_id: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The ID of the last acknowledged message. It *may* not point to an existing or valid message."""

    mentioned_in: list[str] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The message's IDs that mention the user."""

    def __hash__(self) -> int:
        return hash((self.channel_id, self.user_id))

    def __eq__(self, other: object, /) -> bool:
        return (
            self is other
            or isinstance(other, ReadState)
            and self.channel_id == other.channel_id
            and self.user_id == self.user_id
        )


__all__ = ('ReadState',)
