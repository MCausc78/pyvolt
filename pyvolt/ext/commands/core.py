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
    )

    def __init__(
        self,
        *,
        type: type,
        name: str,
        description: str | None = None,
    ) -> None:
        self.type: type = type
        self.name: str = name
        self.description: str | None = description


class Command:
    __slots__ = (
        'aliases',
        'args',
        'callback',
        'checks',
        'children',
        'description',
        'example',
        'extension',
        'hidden',
        'name',
        'parameters',
    )

    def __init__(
        self,
        *,
        aliases: list[str],
        args: str,
        callback: Callable[[Context], pyvolt.utils.MaybeAwaitable[typing.Any]],
        # checks: list[Check],
        description: str | None,
        name: str,
        # children: list[SubCommand],
        alias_to_child: dict[str, str],
        example: str,
        hidden: bool,
    ) -> None:
        self.aliases: list[str] = aliases
        self.args: str = args
        # self.callback: Callable[[E, Context], pyvolt.utils.MaybeAwaitable[typing.Any]] = callback
        # self.checks: list[Check] = checks
        self.description: str | None = description
        self.extension: E = None  # type: ignore # set up later
        self.name: str = name
        # self.children: list[SubCommand] = children
        self.example: str = example
        self.hidden: bool = hidden
