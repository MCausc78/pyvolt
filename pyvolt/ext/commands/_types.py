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

from collections.abc import Callable, Coroutine
import sys
import typing

if typing.TYPE_CHECKING:
    from .bot import Bot
    from .context import Context
    from .errors import CommandError
    from .gear import Gear

T = typing.TypeVar('T')

if sys.version_info >= (3, 13):
    BotT = typing.TypeVar('BotT', bound='Bot', default='Bot', covariant=True)
else:
    BotT = typing.TypeVar('BotT', bound='Bot', covariant=True)

if sys.version_info >= (3, 13):
    ContextT = typing.TypeVar('ContextT', bound='Context[typing.Any]', default='Context[typing.Any]')
    ContextT_co = typing.TypeVar(
        'ContextT_co', bound='Context[typing.Any]', default='Context[typing.Any]', covariant=True
    )
else:
    ContextT = typing.TypeVar('ContextT', bound='Context[typing.Any]')
    ContextT_co = typing.TypeVar('ContextT_co', bound='Context[typing.Any]', covariant=True)


# This is merely a tag type to avoid circular import issues.
# Yes, this is a terrible solution but ultimately it is the only solution.
class _BaseCommand:
    __slots__ = ()


GearT = typing.TypeVar('GearT', bound='typing.Optional[Gear]')


Error = typing.Union[
    Callable[['GearT', 'ContextT', 'CommandError'], Coroutine[typing.Any, typing.Any, typing.Any]],
    Callable[['ContextT', 'CommandError'], Coroutine[typing.Any, typing.Any, typing.Any]],
]
Hook = typing.Union[
    Callable[['GearT', 'ContextT'], Coroutine[typing.Any, typing.Any, typing.Any]],
    Callable[['ContextT'], Coroutine[typing.Any, typing.Any, typing.Any]],
]
UserCheck = Callable[['ContextT'], typing.Union[bool, Coroutine[typing.Any, typing.Any, bool]]]


class Check(typing.Protocol[ContextT_co]):  # type: ignore # TypeVar is expected to be invariant
    predicate: Callable[[ContextT_co], Coroutine[typing.Any, typing.Any, bool]]

    def __call__(self, coro_or_commands: T, /) -> T: ...


__all__ = (
    'BotT',
    'ContextT',
    'ContextT_co',
    '_BaseCommand',
    'GearT',
    'Error',
    'Hook',
    'UserCheck',
    'Check',
)
