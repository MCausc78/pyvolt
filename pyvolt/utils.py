# Thanks Rapptz:
# - https://github.com/Rapptz/discord.py/blob/041abf8b487038c2935da668405ba8b0686ff2f8/discord/utils.py#L77-L82
# - https://github.com/Rapptz/discord.py/blob/041abf8b487038c2935da668405ba8b0686ff2f8/discord/utils.py#L641-L653

from __future__ import annotations

import aiohttp
import datetime
import inspect
import json
import logging
import typing as t

try:
    import orjson
except ModuleNotFoundError:
    HAS_ORJSON = False
else:
    HAS_ORJSON = True

if t.TYPE_CHECKING:
    from collections import abc as ca

    from . import raw

    P = t.ParamSpec("P")
    T = t.TypeVar("T")

    MaybeAwaitable = T | ca.Awaitable[T]
    MaybeAwaitableFunc = ca.Callable[P, MaybeAwaitable[T]]


_L = logging.getLogger(__name__)


if HAS_ORJSON:

    def to_json(obj: t.Any) -> str:
        return orjson.dumps(obj).decode("utf-8")  # type: ignore

    from_json = orjson.loads  # type: ignore

else:

    def to_json(obj: t.Any) -> str:
        return json.dumps(obj, separators=(",", ":"), ensure_ascii=True)

    from_json = json.loads


async def _maybe_coroutine(
    f: MaybeAwaitableFunc[P, T], *args: P.args, **kwargs: P.kwargs
) -> T:
    value = f(*args, **kwargs)
    if inspect.isawaitable(value):
        return await value
    else:
        return value


_TRUE: t.Literal["true"] = "true"
_FALSE: t.Literal["false"] = "false"


def _bool(b: bool) -> "raw.Bool":
    return _TRUE if b else _FALSE


async def _json_or_text(response: aiohttp.ClientResponse) -> t.Any:
    text = await response.text(encoding="utf-8")
    try:
        if response.headers["content-type"] == "application/json":
            if len(text) < 2000:
                _L.debug("Decoding %s", text)
            return from_json(text)
    except KeyError:
        # Thanks Cloudflare
        pass

    return text


def utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


__all__ = (
    "to_json",
    "from_json",
    "_maybe_coroutine",
    "_bool",
    "_json_or_text",
    "utcnow",
)
