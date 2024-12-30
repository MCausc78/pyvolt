from __future__ import annotations

import pyvolt
import typing

if typing.TYPE_CHECKING:
    from collections.abc import Callable

    from .context import Context


class Parameter:
    __slots__ = (
        'type',
        'name',
        'description',
        'displayed_name',
    )

    def __init__(
        self,
        *,
        type: type,
        name: str,
        description: str | None = None,
        displayed_name: str | None = None,
    ) -> None:
        self.type: type = type
        self.name: str = name
        self.description: str | None = description
        self.displayed_name: str | None = displayed_name


class Command:
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
    checks: List[:class:`.Check`]
        A list of checks that verify if the command could be executed
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
        'aliases',
        'callback',
        'checks',
        'children',
        'description',
        'example',
        'gear',
        'hidden',
        'name',
        'parameters',
    )

    def __init__(
        self,
        *,
        aliases: list[str] | None = None,
        # args: str,  # TODO
        callback: Callable[[Context], pyvolt.utils.MaybeAwaitable[typing.Any]],
        # checks: list[Check],
        description: str | None = None,
        name: str,
        # children: list[SubCommand],
        example: str = '',
        hidden: bool = False,
    ) -> None:
        self.aliases: list[str] = aliases or []
        # self.args: str = args
        # self.callback: Callable[[E, Context], pyvolt.utils.MaybeAwaitable[typing.Any]] = callback
        # self.checks: list[Check] = checks
        self.description: str | None = description
        self.gear: Gear = None  # type: ignore # set up later
        self.name: str = name
        # self.children: list[SubCommand] = children
        self.example: str = example
        self.hidden: bool = hidden
