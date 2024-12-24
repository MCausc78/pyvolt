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

import typing

from attrs import define, field
from pyvolt import BaseEvent

if typing.TYPE_CHECKING:
    from .bot import Bot
    from .context import Context
    from .errors import CommandError


@define(slots=True)
class CommandErrorEvent(BaseEvent):
    """Dispatched when an error is raised inside a command either through user input error, check failure, or an error in your own code."""

    event_name: typing.ClassVar[typing.Literal['command_error']] = 'command_error'

    context: Context[Bot] = field(repr=True, kw_only=True)
    """:class:`.Context`: The invocation context."""

    error: CommandError = field(repr=True, kw_only=True)
    """:class:`.CommandError`: The error that was raised."""


@define(slots=True)
class CommandEvent(BaseEvent):
    """Dispatched when a command is found and about to be invoked."""

    event_name: typing.ClassVar[typing.Literal['command']] = 'command'

    context: Context[Bot] = field(repr=True, kw_only=True)
    """:class:`.Context`: The invocation context."""


@define(slots=True)
class CommandCompletionEvent(BaseEvent):
    """Dispatched when a command has completed its invocation.

    This event is dispatched only if the command succeeded, i.e. all checks have passed and the user input it correctly.
    """

    event_name: typing.ClassVar[typing.Literal['command_completion']] = 'command_completion'

    context: Context[Bot] = field(repr=True, kw_only=True)
    """:class:`.Context`: The invocation context."""


__all__ = (
    'CommandErrorEvent',
    'CommandEvent',
    'CommandCompletionEvent',
)
