from __future__ import annotations

import pyvolt
import typing

from ._types import BotT

if typing.TYPE_CHECKING:
    from .core import Command
    from .gear import Gear
    from .parameters import Parameter
    from .view import StringView


class Context(typing.Generic[BotT]):
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
    command_failed: :class:`bool`
        Whether invoking the command failed.
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
        'args',
        '_author',
        'author_id',
        'bot',
        'channel',
        'command',
        'command_failed',
        'current_argument',
        'current_parameter',
        'kwargs',
        'invoked_parents',
        'invoked_subcommand',
        'label',
        'me',
        'message',
        'prefix',
        'server',
        'shard',
        'subcommand_passed',
        'view',
    )

    def __init__(
        self,
        *,
        args: list[typing.Any] | None = None,
        bot: BotT,
        command: Command[typing.Any, ..., typing.Any] | None = None,
        command_failed: bool = False,
        current_argument: str | None = None,
        current_parameter: Parameter | None = None,
        kwargs: dict[str, typing.Any] | None = None,
        invoked_parents: list[str] | None = None,
        invoked_subcommand: Command[typing.Any, ..., typing.Any] | None = None,
        label: str = '',
        message: pyvolt.Message,
        shard: pyvolt.Shard,
        subcommand_passed: str | None = None,
        view: StringView,
    ) -> None:
        channel = message.channel
        me: pyvolt.OwnUser = bot.me  # type: ignore
        server = getattr(channel, 'server', None)

        if args is None:
            args = []

        if kwargs is None:
            kwargs = {}

        if invoked_parents is None:
            invoked_parents = []

        self.args: list[typing.Any] = args
        self._author: pyvolt.Member | pyvolt.User | None = message.get_author()
        self.author_id: str = message.author_id
        self.bot: BotT = bot
        self.channel: pyvolt.TextableChannel | pyvolt.PartialMessageable = channel
        self.command: Command | None = command
        self.command_failed: bool = command_failed
        self.current_argument: str | None = current_argument
        self.current_parameter: Parameter | None = current_parameter
        self.invoked_parents: list[str] = invoked_parents
        self.invoked_subcommand: Command[typing.Any, ..., typing.Any] | None = invoked_subcommand
        self.label: str = label
        self.me: pyvolt.Member | pyvolt.OwnUser = server.get_member(me.id) or me if server else me
        self.message: pyvolt.Message = message
        self.prefix: str = ''
        self.server: pyvolt.Server | None = server
        self.shard: pyvolt.Shard = shard
        self.subcommand_passed: str | None = subcommand_passed
        self.view: StringView = view

    @property
    def author(self) -> pyvolt.Member | pyvolt.User:
        if self._author is None:
            raise pyvolt.NoData(self.author_id, 'message author')
        return self._author

    @property
    def channel_id(self) -> str:
        return self.channel.id

    @property
    def gear(self) -> Gear | None:
        """Optional[:class:`.Gear`]: Returns the gear associated with this context's command. None if it does not exist."""

        if self.command is None:
            return None
        return self.command.gear

    def get_author(self) -> pyvolt.Member | pyvolt.User | None:
        return self._author


__all__ = ('Context',)
