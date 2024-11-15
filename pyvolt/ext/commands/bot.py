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

from pyvolt import Client
import sys
import typing

if typing.TYPE_CHECKING:
    from collections.abc import Callable

    from .context import Context

if sys.version_info >= (3, 13):
    C = typing.TypeVar('C', bound='Context', default='Context')
else:
    C = typing.TypeVar('C', bound='Context')


class Bot(Client, typing.Generic[C]):
    __slots__ = (
        'command_prefix',
        'skip_check',
    )

    def __init__(
        self,
        command_prefix: Callable[[C], list[str]] | str | list[str],
        **options,
    ) -> None:
        self_bot = options.pop('self_bot', False)
        user_bot = options.pop('user_bot', False)
        skip_check = options.pop('skip_check', self.traditional_bot_check)

        if self_bot:
            if user_bot:
                raise TypeError('Both self_bot and user_bot set.')
            skip_check = self.self_bot_check
        elif user_bot:
            skip_check = self.user_bot_check

        self.command_prefix: Callable[[C], list[str]] | str | list[str] = command_prefix
        self.skip_check: Callable[[C], bool] = skip_check

        super().__init__(**options)

    def self_bot_check(self, ctx: C, /) -> bool:
        if ctx.author.bot is not None or ctx.message.webhook is not None:
            return False
        return ctx.author_id == ctx.me.id

    def traditional_bot_check(self, ctx: C, /) -> bool:
        if ctx.author.bot is not None or ctx.message.webhook is not None:
            return False
        return ctx.author_id != ctx.me.id

    def user_bot_check(self, ctx: C, /) -> bool:
        return ctx.author.bot is not None or ctx.message.webhook is not None


__all__ = ('Bot',)
