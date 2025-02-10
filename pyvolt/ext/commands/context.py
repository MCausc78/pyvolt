from __future__ import annotations

import pyvolt
import typing

from ._types import BotT

if typing.TYPE_CHECKING:
    from .core import Command
    from .gear import Gear
    from .parameters import Parameter
    from .view import StringView


class Context(typing.Generic[BotT], pyvolt.abc.Messageable):
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
        'event',
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
        args: typing.Optional[list[typing.Any]] = None,
        bot: BotT,
        command: typing.Optional[Command[typing.Any, ..., typing.Any]] = None,
        command_failed: bool = False,
        current_argument: typing.Optional[str] = None,
        current_parameter: typing.Optional[Parameter] = None,
        event: typing.Optional[pyvolt.MessageCreateEvent] = None,
        kwargs: typing.Optional[dict[str, typing.Any]] = None,
        invoked_parents: typing.Optional[list[str]] = None,
        invoked_subcommand: typing.Optional[Command[typing.Any, ..., typing.Any]] = None,
        label: str = '',
        message: pyvolt.Message,
        shard: pyvolt.Shard,
        subcommand_passed: typing.Optional[str] = None,
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
        self._author: typing.Optional[typing.Union[pyvolt.Member, pyvolt.User]] = message.get_author()
        self.author_id: str = message.author_id
        self.bot: BotT = bot
        self.channel: typing.Union[pyvolt.TextableChannel, pyvolt.PartialMessageable] = channel
        self.command: typing.Optional[Command[typing.Any, ..., typing.Any]] = command
        self.command_failed: bool = command_failed
        self.current_argument: typing.Optional[str] = current_argument
        self.current_parameter: typing.Optional[Parameter] = current_parameter
        self.event: typing.Optional[pyvolt.MessageCreateEvent] = event
        self.invoked_parents: list[str] = invoked_parents
        self.invoked_subcommand: typing.Optional[Command[typing.Any, ..., typing.Any]] = invoked_subcommand
        self.label: str = label
        self.me: typing.Union[pyvolt.Member, pyvolt.OwnUser] = server.get_member(me.id) or me if server else me
        self.message: pyvolt.Message = message
        self.prefix: str = ''
        self.server: typing.Optional[pyvolt.Server] = server
        self.shard: pyvolt.Shard = shard
        self.subcommand_passed: typing.Optional[str] = subcommand_passed
        self.view: StringView = view

    def _get_state(self) -> pyvolt.State:
        return self.bot.state

    @property
    def author(self) -> typing.Union[pyvolt.Member, pyvolt.User]:
        if self._author is None:
            raise pyvolt.NoData(self.author_id, 'message author')
        return self._author

    @property
    def channel_id(self) -> str:
        return self.channel.id

    @property
    def gear(self) -> typing.Optional[Gear]:
        """Optional[:class:`.Gear`]: Returns the gear associated with this context's command. None if it does not exist."""

        if self.command is None:
            return None
        return self.command.gear

    def get_author(self) -> typing.Optional[typing.Union[pyvolt.Member, pyvolt.User]]:
        return self._author

    def get_channel_id(self) -> str:
        return self.channel.id


__all__ = ('Context',)
