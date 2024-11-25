"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

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

import re
import typing

import pyvolt

from .errors import BadArgument, ServerNotFound

if typing.TYPE_CHECKING:
    from ._types import BotT
    from .context import Context

T = typing.TypeVar('T')
T_co = typing.TypeVar('T_co', covariant=True)


@typing.runtime_checkable
class Converter(typing.Protocol[T_co]):
    """The base class of custom converters that require the :class:`.Context`
    to be passed to be useful.

    This allows you to implement converters that function similar to the
    special cased ``pyvolt`` classes.

    Classes that derive from this should override the :meth:`~.Converter.convert`
    method to do its conversion logic. This method must be a :ref:`coroutine <coroutine>`.
    """

    async def convert(self, ctx: Context[BotT], argument: str, /) -> T_co:
        """|coro|

        The method to override to do conversion logic.

        If an error is found while converting, it is recommended to
        raise a :exc:`.CommandError` derived exception as it will
        properly propagate to the error handlers.

        Note that if this method is called manually, :exc:`Exception`
        should be caught to handle the cases where a subclass does
        not explicitly inherit from :exc:`.CommandError`.

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context that the argument is being used in.
        argument: :class:`str`
            The argument that is being converted.

        Raises
        -------
        CommandError
            A generic exception occurred when converting the argument.
        BadArgument
            The converter failed to convert the argument.
        """
        raise NotImplementedError('Derived classes need to implement this.')


_ID_REGEX: re.Pattern[str] = re.compile(r'([0-9A-Z]{26})$')


class IDConverter(Converter[T_co]):
    @staticmethod
    def _get_id_match(argument: str, /) -> re.Match[str] | None:
        return _ID_REGEX.match(argument)


class BaseConverter(IDConverter[pyvolt.Base]):
    """Converts to a :class:`~pyvolt.Base`.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    """

    async def convert(self, ctx: Context[BotT], argument: str, /) -> pyvolt.Base:
        match = self._get_id_match(argument)

        if match is None:
            raise BadArgument(argument)

        return pyvolt.Base(
            state=ctx.shard.state,
            id=match.group(1),
        )


class ServerConverter(IDConverter[pyvolt.Server]):
    """Converts to a :class:`~pyvolt.Server`.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by name. (There is no disambiguation for Servers with multiple matching names).
    """

    async def convert(self, ctx: Context[BotT], argument: str, /) -> pyvolt.Server:
        match = self._get_id_match(argument)
        result = None

        if match is None:
            for server in ctx.bot.servers.values():
                if server.name == argument:
                    result = server
        else:
            server_id = match.group(1)
            result = ctx.bot.get_server(server_id)

        if result is None:
            raise ServerNotFound(argument=argument)

        return result


__all__ = (
    'Converter',
    '_ID_REGEX',
    'IDConverter',
    'BaseConverter',
    'ServerConverter',
)
