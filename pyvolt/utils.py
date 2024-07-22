# Thanks Danny:
# - https://github.com/Rapptz/discord.py/blob/041abf8b487038c2935da668405ba8b0686ff2f8/discord/utils.py#L77-L82
# - https://github.com/Rapptz/discord.py/blob/041abf8b487038c2935da668405ba8b0686ff2f8/discord/utils.py#L641-L653

from __future__ import annotations

import aiohttp
import datetime
import inspect
import json
import logging
import typing

try:
    import orjson
except ModuleNotFoundError:
    HAS_ORJSON = False
else:
    HAS_ORJSON = True

if typing.TYPE_CHECKING:
    from collections import abc as ca

    P = typing.ParamSpec('P')
    T = typing.TypeVar('T')

    MaybeAwaitable = T | ca.Awaitable[T]
    MaybeAwaitableFunc = ca.Callable[P, MaybeAwaitable[T]]


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


__all__ = (
    'to_json',
    'from_json',
    '_maybe_coroutine',
    '_bool',
    '_json_or_text',
    'utcnow',
)
