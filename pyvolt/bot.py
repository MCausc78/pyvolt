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

from .base import Base
from .core import UNDEFINED, UndefinedOr
from .flags import BotFlags

if typing.TYPE_CHECKING:
    from .user import User

_new_bot_flags = BotFlags.__new__


@define(slots=True)
class BaseBot(Base):
    """Represents a base bot on Revolt."""

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, BaseBot) and self.id == other.id

    async def delete(self) -> None:
        """|coro|

        Deletes the bot.

        Raises
        ------
        NotFound
            +--------------------------------------+--------------------------------------------------------------+
            | Possible :attr:`NotFound.type` value | Reason                                                       |
            +--------------------------------------+--------------------------------------------------------------+
            | ``NotFound``                         | The bot was not found, or the current user does not own bot. |
            +--------------------------------------+--------------------------------------------------------------+
        InternalServerError
            +-------------------------------------------------+------------------------------------------------+-------------------------------------------------------------------------------|
            | Possible :attr:`InternalServerError.type` value | Reason                                         | Populated attributes                                                          |
            +-------------------------------------------------+------------------------------------------------+-------------------------------------------------------------------------------|
            | ``DatabaseError``                               | Something went wrong during querying database. | :attr:`InternalServerError.collection`, :attr:`InternalServerError.operation` |
            +-------------------------------------------------+------------------------------------------------+-------------------------------------------------------------------------------|
        """
        return await self.state.http.delete_bot(self.id)

    async def edit(
        self,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        public: UndefinedOr[bool] = UNDEFINED,
        analytics: UndefinedOr[bool] = UNDEFINED,
        interactions_url: UndefinedOr[typing.Optional[str]] = UNDEFINED,
        reset_token: bool = False,
    ) -> Bot:
        """|coro|

        Edits the bot.

        Parameters
        ----------
        name: UndefinedOr[:class:`str`]
            The new bot name. Must be between 2 and 32 characters and not contain whitespace characters.
        public: UndefinedOr[:class:`bool`]
            Whether the bot should be public (could be invited by anyone).
        analytics: UndefinedOr[:class:`bool`]
            Whether to allow Revolt collect analytics about the bot.
        interactions_url: UndefinedOr[Optional[:class:`str`]]
            The new bot interactions URL. For now, this parameter is reserved and does not do anything.
        reset_token: :class:`bool`
            Whether to reset bot token. The new token can be accessed via ``bot.token``.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------+---------------------------------------------------------+
            | Value                | Reason                                                  |
            +----------------------+---------------------------------------------------------+
            | ``FailedValidation`` | The bot's name exceeded length or contained whitespace. |
            +----------------------+---------------------------------------------------------+
            | ``InvalidUsername``  | The bot's name had forbidden characters/substrings.     |
            +----------------------+---------------------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+-----------------------------------------+
            | Value              | Reason                                  |
            +--------------------+-----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid.  |
            +--------------------+-----------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+--------------------------------------------------------------+
            | Value        | Reason                                                       |
            +--------------+--------------------------------------------------------------+
            | ``NotFound`` | The bot was not found, or the current user does not own bot. |
            +--------------+--------------------------------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`.Bot`
            The updated bot.
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
    """Represents a bot on Revolt."""

    owner_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The user's ID who owns this bot."""

    token: str = field(repr=False)
    """:class:`str`: The bot's token used to authenticate requests."""

    public: bool = field(repr=True, kw_only=True)
    """:class:`bool`: Whether the bot is public (may be invited by anyone)."""

    analytics: bool = field(repr=True, kw_only=True)
    """:class:`bool`: Whether to enable analytics."""

    discoverable: bool = field(repr=True, kw_only=True)
    """:class:`bool`: Whether the bot is publicly discoverable."""

    interactions_url: typing.Optional[str] = field(repr=True, kw_only=True)
    """Optional[:class:`str`]: The URL to send interactions to.
    
    .. note::
        This attribute is reserved.
    """

    terms_of_service_url: typing.Optional[str] = field(repr=True, kw_only=True)
    """Optional[:class:`str`]: The Terms of Service's URL."""

    privacy_policy_url: typing.Optional[str] = field(repr=True, kw_only=True)
    """Optional[:class:`str`]: The privacy policy URL."""

    raw_flags: int = field(repr=True, kw_only=True)
    """:class:`int`: The bot's flags raw value."""

    user: User = field(repr=True, kw_only=True)
    """:class:`.User`: The user associated with this bot."""

    @property
    def flags(self) -> BotFlags:
        """:class:`.BotFlags`: The bot's flags."""
        ret = _new_bot_flags(BotFlags)
        ret.value = self.raw_flags
        return ret


@define(slots=True)
class PublicBot(BaseBot):
    """Represents public bot on Revolt."""

    name: str = field(repr=True, kw_only=True)
    """:class:`str`: The bot's name."""

    internal_avatar_id: typing.Optional[str] = field(repr=True, kw_only=True)
    """Optional[:class:`str`]: The bot's avatar ID."""

    description: str = field(repr=True, kw_only=True)
    """:class:`str`: The bot's description."""


__all__ = ('BaseBot', 'Bot', 'PublicBot')
