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

from inspect import cleandoc, isawaitable
from pyvolt import Client, Message, MessageCreateEvent, Shard, utils
import typing

from .context import Context
from .errors import CommandNotFound
from .events import CommandErrorEvent, CommandEvent, CommandCompletionEvent
from .view import StringView

if typing.TYPE_CHECKING:
    from typing_extensions import Self

    from ._types import ContextT
    from .core import Command


class Bot(Client):
    __slots__ = (
        'all_commands',
        'command_prefix',
        'description',
        'owner_id',
        'owner_ids',
        'skip_check',
        'strip_after_prefix',
    )

    def __init__(
        self,
        command_prefix: utils.MaybeAwaitableFunc[[Context[Self]], list[str]] | str | list[str],
        *,
        description: str | None = None,
        self_bot: bool = False,
        strip_after_prefix: bool = False,
        user_bot: bool = False,
        **options,
    ) -> None:
        skip_check = options.pop('skip_check', self.traditional_bot_skip_check)

        if self_bot:
            if user_bot:
                raise TypeError('Both self_bot and user_bot are set')
            skip_check = self.self_bot_skip_check
        elif user_bot:
            skip_check = self.user_bot_skip_check

        self.all_commands: dict[str, Command] = {}
        self.command_prefix: utils.MaybeAwaitableFunc[[Context[Self]], list[str]] | str | list[str] = command_prefix
        self.description: str = cleandoc(description) if description else ''
        self.owner_id: str | None = options.get('owner_id')
        self.owner_ids: set[str] = options.pop('owner_ids', set())
        self.skip_check: utils.MaybeAwaitableFunc[[Context[Self]], bool] = skip_check
        self.strip_after_prefix: bool = strip_after_prefix

        super().__init__(**options)

    async def get_prefix(self, ctx: Context[Self], /) -> list[str]:
        """List[:class:`str`]: Return prefixes possible in this context."""
        tmp = self.command_prefix
        if callable(tmp):
            tmp = tmp(ctx)
            if isawaitable(tmp):
                tmp = await tmp
        if isinstance(tmp, str):
            tmp = [tmp]
        return tmp

    async def get_context(self, origin: Message, shard: Shard, /, *, cls: type[ContextT] = Context) -> ContextT:
        view = StringView(origin.content)
        ctx = cls(
            bot=self,
            command=None,
            message=origin,
            shard=shard,
            view=view,
        )

        prefixes = await self.get_prefix(ctx)
        invoked_prefix = None
        for prefix in prefixes:
            if view.skip_string(prefix):
                invoked_prefix = prefix
                break

        if invoked_prefix:
            if self.strip_after_prefix:
                view.skip_ws()

            label = view.get_word()

            ctx.label = label
            ctx.prefix = invoked_prefix
            ctx.command = self.all_commands.get(label)

        return ctx

    def self_bot_skip_check(self, ctx: Context[Self], /) -> bool:
        return ctx.author.bot is not None or ctx.message.webhook is not None or ctx.author_id != ctx.me.id

    def traditional_bot_skip_check(self, ctx: Context[Self], /) -> bool:
        return ctx.author.bot is not None or ctx.message.webhook is not None or ctx.author_id == ctx.me.id

    def user_bot_skip_check(self, ctx: Context[Self], /) -> bool:
        return ctx.author.bot is not None or ctx.message.webhook is not None

    @property
    def self_bot(self) -> bool:
        """:class:`bool`: Whether the bot is a self-bot (responds only to :attr:`.me`)."""
        return self.skip_check is self.self_bot_skip_check

    @property
    def traditional_bot(self) -> bool:
        """:class:`bool`: Whether the bot is a traditional bot (does not respond to :attr:`.me`)."""
        return self.skip_check is self.traditional_bot_skip_check

    @property
    def user_bot(self) -> bool:
        """:class:`bool`: Whether the bot is a userbot (responds to everyone)."""
        return self.skip_check is self.user_bot_skip_check

    async def invoke(self, ctx: Context[Self], /) -> None:
        if ctx.command is not None:
            self.dispatch(CommandEvent(shard=ctx.shard, context=ctx))

            self.dispatch(CommandCompletionEvent(shard=ctx.shard, context=ctx))
        elif ctx.label:
            exc = CommandNotFound(f'Command "{ctx.label}" is not found')
            self.dispatch(CommandErrorEvent(shard=ctx.shard, context=ctx, error=exc))

    async def process_commands(self, message: Message, shard: Shard, /) -> None:
        ctx = await self.get_context(message, shard)

        tmp = self.skip_check(ctx)
        if isawaitable(tmp):
            tmp = await tmp

        if tmp:
            return

        # TODO

    async def on_message_create(self, event: MessageCreateEvent, /) -> None:
        await self.process_commands(event.message, event.shard)


__all__ = ('Bot',)
