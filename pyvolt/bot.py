from __future__ import annotations

from attrs import define, field
from enum import IntFlag


from . import base, core, user as users


class BotFlags(IntFlag):
    """Flags that may be attributed to a bot."""

    NONE = 0
    VERIFIED = 1 << 0
    OFFICIAL = 1 << 1


@define(slots=True)
class BaseBot(base.Base):
    """Base representation of a bot on Revolt."""

    async def delete(self) -> None:
        """|coro|

        Deletes the bot.
        """
        return await self.state.http.delete_bot(self.id)

    async def edit(
        self,
        *,
        name: core.UndefinedOr[str] = core.UNDEFINED,
        public: core.UndefinedOr[bool] = core.UNDEFINED,
        analytics: core.UndefinedOr[bool] = core.UNDEFINED,
        interactions_url: core.UndefinedOr[str | None] = core.UNDEFINED,
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
class Bot(base.Base):
    """Partial representation of a bot on Revolt."""

    owner_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    """The user ID of the bot owner."""

    token: str = field(repr=False, hash=True, eq=True)
    """Token used to authenticate requests for this bot."""

    public: bool = field(repr=True, hash=True, kw_only=True, eq=True)
    """Whether the bot is public (may be invited by anyone)."""

    analytics: bool = field(repr=True, hash=True, kw_only=True, eq=True)
    """Whether to enable analytics."""

    discoverable: bool = field(repr=True, hash=True, kw_only=True, eq=True)
    """Whether this bot should be publicly discoverable."""

    interactions_url: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """Reserved; URL for handling interactions."""

    terms_of_service_url: str | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """URL for terms of service."""

    privacy_policy_url: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """URL for privacy policy."""

    flags: BotFlags = field(repr=True, hash=True, kw_only=True, eq=True)
    """Enum of bot flags."""

    user: users.User = field(repr=True, hash=True, kw_only=True, eq=True)
    """The user associated with this bot."""


@define(slots=True)
class PublicBot(BaseBot):
    """Representation of a public bot on Revolt."""

    username: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The bot username."""

    internal_avatar_id: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The bot avatar ID."""

    description: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The bot description."""


__all__ = ("BotFlags", "BaseBot", "Bot", "PublicBot")
