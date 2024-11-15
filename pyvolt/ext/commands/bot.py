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

from pyvolt import Client, Message
import typing

if typing.TYPE_CHECKING:
    from collections.abc import Callable


class Bot(Client):
    __slots__ = ()

    def __init__(
        self,
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

        self.skip_check: Callable[[Message], bool] = skip_check
        super().__init__(**options)

    def self_bot_check(self, message: Message, /) -> bool:
        if message.author.bot is not None or message.webhook is not None:
            return False
        me = self.me
        return me is not None and message.author_id == me.id

    def traditional_bot_check(self, message: Message, /) -> bool:
        if message.author.bot is not None or message.webhook is not None:
            return False
        me = self.me
        return me is not None and message.author_id != me.id

    def user_bot_check(self, message: Message, /) -> bool:
        return message.author.bot is not None or message.webhook is not None


__all__ = ('Bot',)
