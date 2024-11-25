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
    __slots__ = (
        'aliases',
        'args',
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
        args: str,  # TODO
        callback: Callable[[Context], pyvolt.utils.MaybeAwaitable[typing.Any]],
        # checks: list[Check],
        description: str | None = None,
        name: str,
        # children: list[SubCommand],
        example: str = '',
        hidden: bool = False,
    ) -> None:
        self.aliases: list[str] = aliases
        self.args: str = args
        # self.callback: Callable[[E, Context], pyvolt.utils.MaybeAwaitable[typing.Any]] = callback
        # self.checks: list[Check] = checks
        self.description: str | None = description
        self.gear: Gear = None  # type: ignore # set up later
        self.name: str = name
        # self.children: list[SubCommand] = children
        self.example: str = example
        self.hidden: bool = hidden
