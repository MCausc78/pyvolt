from __future__ import annotations

import pyvolt
import typing

if typing.TYPE_CHECKING:
    from ._types import BotT
    from .core import Command
    from .view import StringView


class Context(typing.Generic['BotT']):
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
