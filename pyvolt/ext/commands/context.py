from __future__ import annotations

import pyvolt
import typing

if typing.TYPE_CHECKING:
    from ._types import BotT
    from .core import Command
    from .view import StringView


class Context(typing.Generic['BotT']):
    r"""A class that implements the protocol for a bot text command.

    These are not created manually, instead they are created via the decorator or functional interface.

    Attributes
    -----------
    name: :class:`str`
        The name of the command.
    callback: :ref:`coroutine <coroutine>`
        The coroutine that is executed when the command is called.
    aliases: Union[List[:class:`str`], Tuple[:class:`str`]]
        The list of aliases the command can be invoked under.
    enabled: :class:`bool`
        A boolean that indicates if the command is currently enabled.
        If the command is invoked while it is disabled, then
        :exc:`.DisabledCommand` is raised to the :func:`.on_command_error`
        event. Defaults to ``True``.
    checks: List[Callable[[:class:`.Context`], :class:`bool`]]
        A list of predicates that verifies if the command could be executed
        with the given :class:`.Context` as the sole parameter. If an exception
        is necessary to be thrown to signal failure, then one inherited from
        :exc:`.CommandError` should be used. Note that if the checks fail then
        :exc:`.CheckFailure` exception is raised to the :func:`.on_command_error`
        event.
    description: :class:`str`
        The message prefixed into the default help command.
    hidden: :class:`bool`
        If ``True``\, the default help command does not show this in the
        help output.
    rest_is_raw: :class:`bool`
        If ``False`` and a keyword-only argument is provided then the keyword
        only argument is stripped and handled as if it was a regular argument
        that handles :exc:`.MissingRequiredArgument` and default values in a
        regular matter rather than passing the rest completely raw. If ``True``
        then the keyword-only argument will pass in the rest of the arguments
        in a completely raw matter. Defaults to ``False``.
    invoked_subcommand: Optional[:class:`.Command`]
        The subcommand that was invoked, if any.
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
