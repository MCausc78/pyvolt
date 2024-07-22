from __future__ import annotations

from attrs import define, field
import typing

if typing.TYPE_CHECKING:
    from .state import State


@define(slots=True)
class ReadState:
    """The channel read state."""

    state: State = field(repr=False, hash=False, kw_only=True, eq=False)

    channel_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The state channel ID."""

    user_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The current user ID."""

    last_message_id: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The ID of the last message read in this channel by current user."""

    mentioned_in: list[str] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The list of message IDs that mention the user."""


__all__ = ('ReadState',)
