from __future__ import annotations

from attrs import define, field
import typing as t

from . import core

if t.TYPE_CHECKING:
    from .state import State


@define(slots=True)
class ReadState:
    """The channel read state."""

    state: State = field(repr=False, hash=False, kw_only=True, eq=False)

    channel_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    """The state channel ID."""

    user_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    """The current user ID."""

    last_message_id: core.ULID | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The ID of the last message read in this channel by current user."""

    mentioned_in: list[core.ULID] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The list of message IDs that mention the user."""


__all__ = ("ReadState",)
