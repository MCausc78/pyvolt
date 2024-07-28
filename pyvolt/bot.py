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
from enum import IntFlag

from .base import Base
from .core import UNDEFINED, UndefinedOr
from .user import User


class BotFlags(IntFlag):
    """Flags that may be attributed to a bot."""

    NONE = 0
    VERIFIED = 1 << 0
    OFFICIAL = 1 << 1


@define(slots=True)
class BaseBot(Base):
    """Base representation of a bot on Revolt."""

    async def delete(self) -> None:
        """|coro|

        Deletes the bot.
        """
        return await self.state.http.delete_bot(self.id)

    async def edit(
        self,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        public: UndefinedOr[bool] = UNDEFINED,
        analytics: UndefinedOr[bool] = UNDEFINED,
        interactions_url: UndefinedOr[str | None] = UNDEFINED,
        reset_token: bool = False,
    ) -> Bot:
        """|coro|

        Edits the bot.
        """
        return await self.state.http.edit_bot(
            self.id,
            name=name,
            public=public,
            analytics=analytics,
            interactions_url=interactions_url,
            reset_token=reset_token,
        )


@define(slots=True)
class Bot(BaseBot):
    """Partial representation of a bot on Revolt."""

    owner_id: str = field(repr=True, kw_only=True)
    """The user ID of the bot owner."""

    token: str = field(repr=False)
    """Token used to authenticate requests for this bot."""

    public: bool = field(repr=True, kw_only=True)
    """Whether the bot is public (may be invited by anyone)."""

    analytics: bool = field(repr=True, kw_only=True)
    """Whether to enable analytics."""

    discoverable: bool = field(repr=True, kw_only=True)
    """Whether this bot should be publicly discoverable."""

    interactions_url: str | None = field(repr=True, kw_only=True)
    """Reserved; URL for handling interactions."""

    terms_of_service_url: str | None = field(repr=True, kw_only=True)
    """URL for terms of service."""

    privacy_policy_url: str | None = field(repr=True, kw_only=True)
    """URL for privacy policy."""

    flags: BotFlags = field(repr=True, kw_only=True)
    """Enum of bot flags."""

    user: User = field(repr=True, kw_only=True)
    """The user associated with this bot."""


@define(slots=True)
class PublicBot(BaseBot):
    """Representation of a public bot on Revolt."""

    username: str = field(repr=True, kw_only=True)
    """The bot username."""

    internal_avatar_id: str | None = field(repr=True, kw_only=True)
    """The bot avatar ID."""

    description: str = field(repr=True, kw_only=True)
    """The bot description."""


__all__ = ('BotFlags', 'BaseBot', 'Bot', 'PublicBot')
