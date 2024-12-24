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

import contextlib
import typing


if typing.TYPE_CHECKING:
    from .abc import Messageable
    from .shard import Shard


class Typing(contextlib.AbstractAsyncContextManager):
    __slots__ = (
        'channel_id',
        'destination',
        'shard',
    )

    def __init__(self, *, destination: Messageable, shard: Shard) -> None:
        self.channel_id: str = ''
        self.destination: Messageable = destination
        self.shard: Shard = shard

    async def __aenter__(self) -> None:
        if not self.channel_id:
            self.channel_id = await self.destination.fetch_channel_id()

        await self.shard.begin_typing(self.channel_id)

    async def __aexit__(self, exc_type, exc_value, tb, /) -> None:
        del exc_type
        del exc_value
        del tb

        if not self.channel_id:
            self.channel_id = await self.destination.fetch_channel_id()

        await self.shard.end_typing(self.channel_id)
        return


__all__ = ('Typing',)
