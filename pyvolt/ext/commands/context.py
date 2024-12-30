from __future__ import annotations

import pyvolt
import typing

if typing.TYPE_CHECKING:
    from ._types import BotT
    from .core import Command
    from .view import StringView


class Context(typing.Generic['BotT']):
    r"""A invoking context for commands.

    These are not created manually, instead they are created via :meth:`Bot.get_context` method.

    Attributes
    -----------
    author: Union[:class:`pyvolt.Member`, :class:`pyvolt.User`]
        The user who created this context.
    author_id: :class:`str`
        The user's ID who created this context.
    bot: :class:`Bot`
        The bot in this context.
    channel: Union[:class:`pyvolt.TextableChannel`, :class:`pyvolt.PartialMessageable`]
        The channel the context was created in.
    command: Optional[:class:`.Command`]
        The command used in this context.
    label: :class:`str`
        The substring used to invoke the command. May be empty sometimes.
    me: Union[:class:`pyvolt.Member`, :class:`pyvolt.OwnUser`]
        The bot user in this context.
    message: :class:`pyvolt.Message`
        The message that caused this context to be created.
    prefix: :class:`str`
        The prefix used to invoke command. May be empty sometimes.
    server: Optional[:class:`pyvolt.Server`]
        The server this command happened in.
    shard: :class:`pyvolt.Shard`
        The shard the context was created on.
    view: :class:`.StringView`
        The string view, used to parse command parameters.
    """

    __slots__ = (
        'author',
        'author_id',
        'bot',
        'channel',
        'command',
        'label',
        'me',
        'message',
        'prefix',
        'server',
        'shard',
        'view',
    )

    def __init__(
        self,
        *,
        bot: BotT,
        command: Command | None,
        message: pyvolt.Message,
        shard: pyvolt.Shard,
        view: StringView,
    ) -> None:
        channel = message.channel
        me: pyvolt.OwnUser = bot.me  # type: ignore
        server = getattr(channel, 'server', None)

        self.author: pyvolt.Member | pyvolt.User = message.author
        self.author_id: str = message.author_id
        self.bot: BotT = bot
        self.channel: pyvolt.TextableChannel | pyvolt.PartialMessageable = channel
        self.command: Command | None = command
        self.label: str = ''
        self.me: pyvolt.Member | pyvolt.OwnUser = server.get_member(me.id) or me if server else me
        self.message: pyvolt.Message = message
        self.prefix: str = ''
        self.server: pyvolt.Server | None = server
        self.shard: pyvolt.Shard = shard
        self.view: StringView = view


__all__ = ('Context',)
