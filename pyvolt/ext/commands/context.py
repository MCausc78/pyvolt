from __future__ import annotations

import pyvolt
import typing

if typing.TYPE_CHECKING:
    from .bot import Bot


class Context:
    __slots__ = (
        'author',
        'author_id',
        'bot',
        'channel',
        'me',
        'message',
        'server',
    )

    def __init__(
        self,
        *,
        bot: Bot,
        message: pyvolt.Message,
    ) -> None:
        channel = message.channel
        me: pyvolt.OwnUser = bot.me  # type: ignore
        server = getattr(channel, 'server', None)

        self.author: pyvolt.Member | pyvolt.User = message.author
        self.author_id: str = message.author_id
        self.bot: Bot = bot
        self.channel: pyvolt.TextableChannel | pyvolt.PartialMessageable = channel
        self.me: pyvolt.Member | pyvolt.OwnUser = server.get_member(me.id) or me if server else me
        self.message: pyvolt.Message = message
        self.server: pyvolt.Server | None = server


__all__ = ('Context',)
