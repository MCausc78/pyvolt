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

# Thanks Danny:
# - https://github.com/Rapptz/discord.py/blob/041abf8b487038c2935da668405ba8b0686ff2f8/discord/utils.py#L77-L82
# - https://github.com/Rapptz/discord.py/blob/041abf8b487038c2935da668405ba8b0686ff2f8/discord/utils.py#L641-L653
# - https://github.com/Rapptz/discord.py/blob/ff638d393d0f5a83639ccc087bec9bf588b59a22/discord/utils.py#L1253-L1374

from __future__ import annotations

import aiohttp
import datetime
import inspect
import json
import logging
import os
import sys
import typing

try:
    import orjson
except ModuleNotFoundError:
    HAS_ORJSON = False
else:
    HAS_ORJSON = True

if typing.TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    P = typing.ParamSpec('P')
    T = typing.TypeVar('T')

    MaybeAwaitable = T | Awaitable[T]
    MaybeAwaitableFunc = Callable[P, MaybeAwaitable[T]]


from .core import UNDEFINED, UndefinedOr

_L = logging.getLogger(__name__)


if HAS_ORJSON:

    def to_json(obj: typing.Any) -> str:
        return orjson.dumps(obj).decode('utf-8')  # type: ignore

    from_json = orjson.loads  # type: ignore

else:

    def to_json(obj: typing.Any) -> str:
        return json.dumps(obj, separators=(',', ':'), ensure_ascii=True)

    from_json = json.loads


async def _maybe_coroutine(f: MaybeAwaitableFunc[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    value = f(*args, **kwargs)
    if inspect.isawaitable(value):
        return await value
    else:
        return value


_TRUE: typing.Literal['true'] = 'true'
_FALSE: typing.Literal['false'] = 'false'


def _bool(b: bool) -> typing.Literal['true', 'false']:
    return _TRUE if b else _FALSE


async def _json_or_text(response: aiohttp.ClientResponse) -> typing.Any:
    text = await response.text(encoding='utf-8')
    try:
        if response.headers['content-type'].startswith('application/json'):
            return from_json(text)
    except KeyError:
        # Thanks Cloudflare
        pass

    return text


def utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def is_docker() -> bool:
    path = '/proc/self/cgroup'
    return os.path.exists('/.dockerenv') or (os.path.isfile(path) and any('docker' in line for line in open(path)))


def stream_supports_colour(stream: typing.Any) -> bool:
    is_a_tty = hasattr(stream, 'isatty') and stream.isatty()

    # Pycharm and VSCode support colour in their inbuilt editors
    if 'PYCHARM_HOSTED' in os.environ or os.environ.get('TERM_PROGRAM') == 'vscode':
        return is_a_tty

    if sys.platform != 'win32':
        # Docker does not consistently have a tty attached to it
        return is_a_tty or is_docker()

    # ANSICON checks for things like ConEmu
    # WT_SESSION checks if this is Windows Terminal
    return is_a_tty and ('ANSICON' in os.environ or 'WT_SESSION' in os.environ)


class _ColourFormatter(logging.Formatter):
    # ANSI codes are a bit weird to decipher if you're unfamiliar with them, so here's a refresher
    # It starts off with a format like \x1b[XXXm where XXX is a semicolon separated list of commands
    # The important ones here relate to colour.
    # 30-37 are black, red, green, yellow, blue, magenta, cyan and white in that order
    # 40-47 are the same except for the background
    # 90-97 are the same but "bright" foreground
    # 100-107 are the same as the bright ones but for the background.
    # 1 means bold, 2 means dim, 0 means reset, and 4 means underline.

    LEVEL_COLOURS = [
        (logging.DEBUG, '\x1b[40;1m'),
        (logging.INFO, '\x1b[34;1m'),
        (logging.WARNING, '\x1b[33;1m'),
        (logging.ERROR, '\x1b[31m'),
        (logging.CRITICAL, '\x1b[41m'),
    ]

    FORMATS = {
        level: logging.Formatter(
            f'\x1b[30;1m%(asctime)s\x1b[0m {colour}%(levelname)-8s\x1b[0m \x1b[35m%(name)s\x1b[0m %(message)s',
            '%Y-%m-%d %H:%M:%S',
        )
        for level, colour in LEVEL_COLOURS
    }

    def format(self, record):
        formatter = self.FORMATS.get(record.levelno)
        if formatter is None:
            formatter = self.FORMATS[logging.DEBUG]

        # Override the traceback to always print in red
        if record.exc_info:
            text = formatter.formatException(record.exc_info)
            record.exc_text = f'\x1b[31m{text}\x1b[0m'

        output = formatter.format(record)

        # Remove the cache layer
        record.exc_text = None
        return output


def new_formatter(handler: logging.Handler) -> logging.Formatter:
    """A helper function to create logging formatter.

    Like :func:`.setup_logging`, this will use colors if they are supported
    on current stream.

    Parameters
    ----------
    handler: :class:`logging.Handler`
        The log handler.

    Returns
    -------
    :class:`logging.Formatter`
        The formatter.
    """
    if isinstance(handler, logging.StreamHandler) and stream_supports_colour(handler.stream):
        formatter = _ColourFormatter()
    else:
        dt_fmt = '%Y-%m-%d %H:%M:%S'
        formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
    return formatter


def setup_logging(
    *,
    handler: UndefinedOr[logging.Handler] = UNDEFINED,
    formatter: UndefinedOr[logging.Formatter] = UNDEFINED,
    level: UndefinedOr[int] = UNDEFINED,
    root: bool = True,
) -> None:
    """A helper function to setup logging.

    This is superficially similar to :func:`logging.basicConfig` but
    uses different defaults and a colour formatter if the stream can
    display colour.

    This is used by the :class:`~pyvolt.Client` to set up logging
    if ``log_handler`` is not ``None``.

    Parameters
    -----------
    handler: :class:`logging.Handler`
        The log handler to use for the library's logger.

        The default log handler if not provided is :class:`logging.StreamHandler`.
    formatter: :class:`logging.Formatter`
        The formatter to use with the given log handler. If not provided then it
        defaults to a colour based logging formatter (if available). If colour
        is not available then a simple logging formatter is provided.
    level: :class:`int`
        The default log level for the library's logger. Defaults to ``logging.INFO``.
    root: :class:`bool`
        Whether to set up the root logger rather than the library logger.
        Unlike the default for :class:`~pyvolt.Client`, this defaults to ``True``.
    """

    if level is UNDEFINED:
        level = logging.INFO

    if handler is UNDEFINED:
        handler = logging.StreamHandler()

    if formatter is UNDEFINED:
        formatter = new_formatter(handler)

    if root:
        logger = logging.getLogger()
    else:
        library, _, _ = __name__.partition('.')
        logger = logging.getLogger(library)

    handler.setFormatter(formatter)
    logger.setLevel(level)
    logger.addHandler(handler)


__all__ = (
    'to_json',
    'from_json',
    '_maybe_coroutine',
    '_bool',
    '_json_or_text',
    'utcnow',
    'is_docker',
    'stream_supports_colour',
    'new_formatter',
    'setup_logging',
)
