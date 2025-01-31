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
# - setup_logging, copy_doc
# - https://github.com/Rapptz/discord.py/blob/041abf8b487038c2935da668405ba8b0686ff2f8/discord/utils.py#L77-L82
# - https://github.com/Rapptz/discord.py/blob/041abf8b487038c2935da668405ba8b0686ff2f8/discord/utils.py#L641-L653
# - https://github.com/Rapptz/discord.py/blob/ff638d393d0f5a83639ccc087bec9bf588b59a22/discord/utils.py#L1253-L1374

from __future__ import annotations

import datetime
from functools import partial
import inspect
import json
import logging
import os
import re
import sys
import types
import typing

import aiohttp

try:
    import orjson  # type: ignore
except ModuleNotFoundError:
    HAS_ORJSON = False
else:
    HAS_ORJSON = True

if typing.TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable, Sequence

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


async def maybe_coroutine(f: MaybeAwaitableFunc[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    value = f(*args, **kwargs)
    if inspect.isawaitable(value):
        return await value
    else:
        return value


def copy_doc(original: Callable[..., typing.Any]) -> Callable[[T], T]:
    """A decorator that copies documentation.

    Parameters
    ----------
    original: Callable[..., typing.Any]
        The function to copy documentation from.

    Returns
    -------
    Callable[[T], T]
        The decorated function with copied documentation.
    """

    def decorator(overridden: T) -> T:
        overridden.__doc__ = original.__doc__
        overridden.__signature__ = inspect.signature(original)  # type: ignore
        return overridden

    return decorator


_TRUE: typing.Literal['true'] = 'true'
_FALSE: typing.Literal['false'] = 'false'


def _bool(b: bool, /) -> typing.Literal['true', 'false']:
    return _TRUE if b else _FALSE


_BOOL_FALSE_VALUES: typing.Final[tuple[str, ...]] = (
    '0',
    'f',
    'false',
    'falsy',
    'n',
    'na',
    'nah',
    'no',
    'nop',
)

_BOOL_TRUE_VALUES: typing.Final[tuple[str, ...]] = (
    '1',
    't',
    'true',
    'trut',
    'truth',
    'y',
    'ye',
    'yep',
    'yeah',
    'yeh',
    'yop',
    'yuh',
    'yes',
)


def decode_bool(
    b: str,
    /,
) -> bool | None:
    v = b.casefold()
    if v in _BOOL_TRUE_VALUES:
        return True
    elif v in _BOOL_FALSE_VALUES:
        return False
    return None


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


def stream_supports_color(stream: typing.Any, /) -> bool:
    is_a_tty = hasattr(stream, 'isatty') and stream.isatty()

    # Pycharm and VSCode support colou in their inbuilt editors
    if 'PYCHARM_HOSTED' in os.environ or os.environ.get('TERM_PROGRAM') == 'vscode':
        return is_a_tty

    if sys.platform != 'win32':
        # Docker does not consistently have a tty attached to it
        return is_a_tty or is_docker()

    # ANSICON checks for things like ConEmu
    # WT_SESSION checks if this is Windows Terminal
    return is_a_tty and ('ANSICON' in os.environ or 'WT_SESSION' in os.environ)


class _ColorFormatter(logging.Formatter):
    # ANSI codes are a bit weird to decipher if you're unfamiliar with them, so here's a refresher
    # It starts off with a format like \x1b[XXXm where XXX is a semicolon separated list of commands
    # The important ones here relate to color.
    # 30-37 are black, red, green, yellow, blue, magenta, cyan and white in that order
    # 40-47 are the same except for the background
    # 90-97 are the same but "bright" foreground
    # 100-107 are the same as the bright ones but for the background.
    # 1 means bold, 2 means dim, 0 means reset, and 4 means underline.

    LEVEL_COLORS = [
        (logging.DEBUG, '\x1b[40;1m'),
        (logging.INFO, '\x1b[34;1m'),
        (logging.WARNING, '\x1b[33;1m'),
        (logging.ERROR, '\x1b[31m'),
        (logging.CRITICAL, '\x1b[41m'),
    ]

    FORMATS = {
        level: logging.Formatter(
            f'\x1b[30;1m%(asctime)s\x1b[0m {color}%(levelname)-8s\x1b[0m \x1b[35m%(name)s\x1b[0m %(message)s',
            '%Y-%m-%d %H:%M:%S',
        )
        for level, color in LEVEL_COLORS
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
    if isinstance(handler, logging.StreamHandler) and stream_supports_color(handler.stream):
        formatter = _ColorFormatter()
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
    uses different defaults and a color formatter if the stream can
    display color.

    This is used by the :class:`~pyvolt.Client` to set up logging
    if ``log_handler`` is not ``None``.

    Parameters
    -----------
    handler: :class:`logging.Handler`
        The log handler to use for the library's logger.

        The default log handler if not provided is :class:`logging.StreamHandler`.
    formatter: :class:`logging.Formatter`
        The formatter to use with the given log handler. If not provided then it
        defaults to a color based logging formatter (if available). If color
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


_UTC: datetime.timezone = datetime.timezone.utc

PY_310: bool = sys.version_info >= (3, 10)
PY_312: bool = sys.version_info >= (3, 12)


def flatten_literal_params(parameters: Iterable[typing.Any], /) -> tuple[typing.Any, ...]:
    params = []
    literal_cls = type(typing.Literal[0])
    for p in parameters:
        if isinstance(p, literal_cls):
            params.extend(typing.get_args(p))
        else:
            params.append(p)
    return tuple(params)


def normalise_optional_params(parameters: Iterable[typing.Any], /) -> tuple[typing.Any, ...]:
    none_cls = type(None)
    return tuple(p for p in parameters if p is not none_cls) + (none_cls,)


def evaluate_annotation(
    tp: typing.Any,
    globals: dict[str, typing.Any],
    locals: dict[str, typing.Any],
    cache: dict[str, typing.Any],
    /,
    *,
    implicit_str: bool = True,
) -> typing.Any:
    if isinstance(tp, typing.ForwardRef):
        tp = tp.__forward_arg__
        # ForwardRefs always evaluate their internals
        implicit_str = True

    if implicit_str and isinstance(tp, str):
        if tp in cache:
            return cache[tp]
        evaluated = evaluate_annotation(eval(tp, globals, locals), globals, locals, cache)
        cache[tp] = evaluated
        return evaluated

    if PY_312 and getattr(tp.__repr__, '__objclass__', None) is typing.TypeAliasType:  # type: ignore
        temp_locals = dict(**locals, **{t.__name__: t for t in tp.__type_params__})
        annotation = evaluate_annotation(tp.__value__, globals, temp_locals, cache.copy())
        if hasattr(tp, '__args__'):
            annotation = annotation[tp.__args__]
        return annotation

    if hasattr(tp, '__supertype__'):
        return evaluate_annotation(tp.__supertype__, globals, locals, cache)

    if hasattr(tp, '__metadata__'):
        # Annotated[X, Y] can access Y via __metadata__
        metadata = tp.__metadata__[0]
        return evaluate_annotation(metadata, globals, locals, cache)

    if hasattr(tp, '__args__'):
        implicit_str = True
        is_literal = False
        args = tp.__args__
        if not hasattr(tp, '__origin__'):
            if PY_310 and tp.__class__ is types.UnionType:  # type: ignore
                converted = Union[args]  # type: ignore
                return evaluate_annotation(converted, globals, locals, cache)

            return tp
        if tp.__origin__ is typing.Union:
            try:
                if args.index(type(None)) != len(args) - 1:
                    args = normalise_optional_params(tp.__args__)
            except ValueError:
                pass
        if tp.__origin__ is typing.Literal:
            if not PY_310:
                args = flatten_literal_params(tp.__args__)
            implicit_str = False
            is_literal = True

        evaluated_args = tuple(
            evaluate_annotation(arg, globals, locals, cache, implicit_str=implicit_str) for arg in args
        )

        if is_literal and not all(isinstance(x, (str, int, bool, type(None))) for x in evaluated_args):
            raise TypeError('Literal arguments must be of type str, int, bool, or NoneType.')

        try:
            return tp.copy_with(evaluated_args)
        except AttributeError:
            return tp.__origin__[evaluated_args]

    return tp


def resolve_annotation(
    annotation: typing.Any,
    globalns: dict[str, typing.Any],
    localns: dict[str, typing.Any] | None,
    cache: dict[str, typing.Any] | None,
    /,
) -> typing.Any:
    if annotation is None:
        return type(None)
    if isinstance(annotation, str):
        annotation = typing.ForwardRef(annotation)

    locals = globalns if localns is None else localns
    if cache is None:
        cache = {}
    return evaluate_annotation(annotation, globalns, locals, cache)


def is_inside_class(func: Callable[..., typing.Any], /) -> bool:
    # For methods defined in a class, the qualname has a dotted path
    # denoting which class it belongs to. So, e.g. for A.foo the qualname
    # would be A.foo while a global foo() would just be foo.
    #
    # Unfortunately, for nested functions this breaks. So inside an outer
    # function named outer, those two would end up having a qualname with
    # outer.<locals>.A.foo and outer.<locals>.foo

    return func.__qualname__ != func.__name__ and not func.__qualname__.rpartition('.')[0].endswith('<locals>')


def unwrap_function(function: Callable[..., typing.Any], /) -> Callable[..., typing.Any]:
    while True:
        if hasattr(function, '__wrapped__'):
            function = function.__wrapped__  # type: ignore
        elif isinstance(function, partial):
            function = function.func
        else:
            return function


ARG_NAME_SUBREGEX: typing.Final[str] = r'(?:\\?\*){0,2}(?P<name>\w+)'
ARG_DESCRIPTION_SUBREGEX: typing.Final[str] = r'(?P<description>(?:.|\n)+?(?:\Z|\r?\n(?=[\S\r\n])))'
ARG_TYPE_SUBREGEX: typing.Final[str] = r'(?:.+)'
GOOGLE_DOCSTRING_ARG_REGEX: typing.Final[re.Pattern[str]] = re.compile(
    rf'^{ARG_NAME_SUBREGEX}[ \t]*(?:\({ARG_TYPE_SUBREGEX}\))?[ \t]*:[ \t]*{ARG_DESCRIPTION_SUBREGEX}',
    re.MULTILINE,
)
NUMPY_DOCSTRING_ARG_REGEX: typing.Final[re.Pattern[str]] = re.compile(
    rf'^{ARG_NAME_SUBREGEX}(?:[ \t]*:)?(?:[ \t]+{ARG_TYPE_SUBREGEX})?[ \t]*\r?\n[ \t]+{ARG_DESCRIPTION_SUBREGEX}',
    re.MULTILINE,
)
PARAMETER_HEADING_REGEX: typing.Final[re.Pattern[str]] = re.compile(r'Parameters?\n---+\n', re.I)
SPHINX_DOCSTRING_ARG_REGEX: typing.Final[re.Pattern[str]] = re.compile(
    rf'^:param {ARG_NAME_SUBREGEX}:[ \t]+{ARG_DESCRIPTION_SUBREGEX}',
    re.MULTILINE,
)


def _is_submodule(parent: str, child: str) -> bool:
    return parent == child or child.startswith(parent + '.')


def human_join(seq: Sequence[str], /, *, delimiter: str = ', ', final: str = 'or') -> str:
    size = len(seq)
    if size == 0:
        return ''

    if size == 1:
        return seq[0]

    if size == 2:
        return f'{seq[0]} {final} {seq[1]}'

    return delimiter.join(seq[:-1]) + f' {final} {seq[-1]}'


class _MissingSentinel:
    __slots__ = ()

    def __bool__(self) -> typing.Literal[False]:
        return False

    def __repr__(self) -> typing.Literal['...']:
        return '...'


MISSING: typing.Any = _MissingSentinel()

__all__ = (
    'to_json',
    'from_json',
    'maybe_coroutine',
    'copy_doc',
    '_bool',
    '_BOOL_FALSE_VALUES',
    '_BOOL_TRUE_VALUES',
    'decode_bool',
    '_json_or_text',
    'utcnow',
    'is_docker',
    'stream_supports_color',
    'new_formatter',
    'setup_logging',
    '_UTC',
    'PY_310',
    'PY_312',
    'flatten_literal_params',
    'normalise_optional_params',
    'evaluate_annotation',
    'resolve_annotation',
    'is_inside_class',
    'ARG_NAME_SUBREGEX',
    'ARG_DESCRIPTION_SUBREGEX',
    'ARG_TYPE_SUBREGEX',
    'GOOGLE_DOCSTRING_ARG_REGEX',
    'NUMPY_DOCSTRING_ARG_REGEX',
    'PARAMETER_HEADING_REGEX',
    'SPHINX_DOCSTRING_ARG_REGEX',
    '_is_submodule',
    'human_join',
    '_MissingSentinel',
    'MISSING',
)
