from __future__ import annotations

import abc
import aiohttp
import asyncio
from enum import StrEnum
import logging
import typing as t

from . import core, utils
from .errors import PyvoltError, ShardError, AuthenticationError, ConnectError

if t.TYPE_CHECKING:
    from . import raw
    from .state import State

try:
    import msgpack
except ImportError:
    _HAS_MSGPACK = False
else:
    _HAS_MSGPACK = True

_L = logging.getLogger(__name__)


class Close(BaseException):
    pass


class Reconnect(BaseException):
    pass


class EventHandler(abc.ABC):
    @abc.abstractmethod
    async def handle_raw(self, shard: Shard, d: raw.ClientEvent) -> None: ...


DEFAULT_SHARD_USER_AGENT = (
    f"pyvolt Shard client (https://github.com/MCausc78/pyvolt, {core.__version__})"
)


class ShardFormat(StrEnum):
    JSON = "json"
    MSGPACK = "msgpack"


class Shard:
    _closing_future: asyncio.Future[None] | None
    _ws: aiohttp.ClientWebSocketResponse | None

    __slots__ = (
        "_closed",
        "_closing_future",
        "_heartbeat_sequence",
        "_last_close_code",
        "_sequence",
        "_ws",
        "base",
        "bot",
        "connect_delay",
        "format",
        "handler",
        "logged_out",
        "reconnect_on_timeout",
        "retries",
        "_session",
        "state",
        "token",
        "user_agent",
        "recv",
        "send",
    )

    def __init__(
        self,
        token: str,
        *,
        base: str | None = None,
        bot: bool = True,
        connect_delay: int | float | None = 2,
        format: ShardFormat = ShardFormat.JSON,
        handler: EventHandler | None = None,
        reconnect_on_timeout: bool = True,
        retries: int | None = None,
        session: (
            utils.MaybeAwaitableFunc[[Shard], aiohttp.ClientSession]
            | aiohttp.ClientSession
        ),
        state: State,
        user_agent: str | None = None,
    ) -> None:
        if format is ShardFormat.MSGPACK and not _HAS_MSGPACK:
            raise TypeError("Cannot use msgpack format without dependency")

        self._closed = False
        self._closing_future = None
        self._heartbeat_sequence = 1
        self._last_close_code = None
        self._sequence = 0
        self._ws = None
        self.base = base or "wss://ws.revolt.chat/"
        self.bot = bot
        self.connect_delay = connect_delay
        self.format = format
        self.handler = handler
        self.logged_out = False
        self.reconnect_on_timeout = reconnect_on_timeout
        self.retries = retries or 150
        self._session = session
        self.state = state
        self.token = token
        self.user_agent = user_agent or DEFAULT_SHARD_USER_AGENT

        self.recv = (
            self._recv_json if format is ShardFormat.JSON else self._recv_msgpack
        )
        self.send = (
            self._send_json if format is ShardFormat.JSON else self._send_msgpack
        )

    def is_closed(self) -> bool:
        return self._closed and not self._ws

    async def close(self) -> None:
        if self._ws:
            if self._closed:
                raise ShardError("Already closed")
            self._closing_future = None
            self._closed = True
            await self._ws.close(code=1000)

    @property
    def ws(self) -> aiohttp.ClientWebSocketResponse:
        if self._ws is None:
            raise TypeError("No websocket")
        return self._ws

    async def begin_typing(self, channel: core.ResolvableULID) -> None:
        await self.send({"type": "BeginTyping", "channel": core.resolve_ulid(channel)})

    async def end_typing(self, channel: core.ResolvableULID) -> None:
        await self.send({"type": "EndTyping", "channel": core.resolve_ulid(channel)})

    async def subscribe_to(self, server: core.ResolvableULID) -> None:
        await self.send({"type": "Subscribe", "server_id": core.resolve_ulid(server)})

    async def _send_json(self, d: raw.ServerEvent) -> None:
        _L.debug("sending %s", d)
        await self.ws.send_str(utils.to_json(d))

    async def _send_msgpack(self, d: raw.ServerEvent) -> None:
        _L.debug("sending %s", d)

        # Will never none according to stubs: https://github.com/sbdchd/msgpack-types/blob/a9ab1c861933fa11aff706b21c303ee52a2ee359/msgpack-stubs/__init__.pyi#L40-L49
        payload: bytes = msgpack.packb(d)  # type: ignore
        await self.ws.send_bytes(payload)

    async def _recv_json(self) -> raw.ClientEvent | None:
        try:
            message = await self.ws.receive()
        except (KeyboardInterrupt, asyncio.CancelledError):
            raise Close
        if message.type in (
            aiohttp.WSMsgType.CLOSE,
            aiohttp.WSMsgType.CLOSED,
            aiohttp.WSMsgType.CLOSING,
        ):
            data = message.data
            self._last_close_code = data
            _L.debug("websocket closed: %s", data)
            if self._closed:
                raise Close
            else:
                await asyncio.sleep(1)
                raise Reconnect
        if message.type is aiohttp.WSMsgType.ERROR:
            _L.debug("received invalid websocket payload, reconnecting")
            raise Reconnect

        if message.type is not aiohttp.WSMsgType.TEXT:
            return None
        k = utils.from_json(message.data)
        if k["type"] != "Ready":
            _L.debug("received %s", k)
        return k

    async def _recv_msgpack(self) -> raw.ClientEvent | None:
        try:
            message = await self.ws.receive()
        except (KeyboardInterrupt, asyncio.CancelledError):
            raise Close
        if message.type in (
            aiohttp.WSMsgType.CLOSE,
            aiohttp.WSMsgType.CLOSED,
            aiohttp.WSMsgType.CLOSING,
        ):
            data = message.data
            self._last_close_code = data
            _L.debug("websocket closed: %s", data)
            if self._closed:
                raise Close
            else:
                await asyncio.sleep(1)
                raise Reconnect
        if message.type is aiohttp.WSMsgType.ERROR:
            _L.debug("received invalid websocket payload, reconnecting")
            raise Reconnect

        if message.type is not aiohttp.WSMsgType.BINARY:
            return None
        # `msgpack` wont be unbound here
        k = msgpack.unpackb(message.data, use_list=True)  # type: ignore
        if k["type"] != "Ready":
            _L.debug("received %s", k)
        return k

    async def ping(self) -> None:
        self._heartbeat_sequence += 1
        d: raw.ServerPingEvent = {
            "type": "Ping",
            "data": self._heartbeat_sequence,
        }
        await self.send(d)

    def _headers(self) -> dict[str, str]:
        return {"user-agent": self.user_agent}

    async def _heartbeat(self) -> None:
        while True:
            await asyncio.sleep(30.0)
            await self.ping()

    async def connect(self) -> None:
        await self._connect()

    async def _ws_connect(self) -> aiohttp.ClientWebSocketResponse:
        session = self._session
        if callable(session):
            session = await utils._maybe_coroutine(session, self)
            # detect recursion
            if callable(session):
                raise TypeError(
                    f"Expected aiohttp.ClientSession, not {type(session)!r}"
                )
            # Do not call factory on future requests
            self._session = session

        es = []
        for i in range(self.retries):
            try:
                _L.debug("connecting to %s, format=json, try=%i", self.base, i)
                return await session.ws_connect(
                    self.base,
                    headers=self._headers(),
                    params={
                        "version": "1",
                        "format": "json",
                    },
                )
            except OSError as exc:
                # TODO: 10053
                if exc.errno in (54, 10054):  # Connection reset by peer
                    await asyncio.sleep(1.5)
                    continue
            except Exception as exc:
                es.append(exc)
                _L.debug("connection failed on try=%i: %s", i, exc)
                if self.connect_delay is not None:
                    await asyncio.sleep(self.connect_delay)
        raise ConnectError(self.retries, es)

    async def _connect(self) -> None:
        if self._ws:
            raise PyvoltError("The connection is already open.")
        self._closing_future = asyncio.Future()
        self._last_close_code = None
        while not self._closed:
            ws = await self._ws_connect()

            self._ws = ws
            await self.send({"type": "Authenticate", "token": self.token})

            message = await self.recv()
            if message is None or message["type"] != "Authenticated":
                raise AuthenticationError(message)
            self.logged_out = False
            await self._handle(message)
            message = None

            heartbeat_task = asyncio.create_task(self._heartbeat())
            exc: BaseException | None = None
            while not self._closed:
                try:
                    if exc:
                        tmp = exc
                        exc = None
                        raise tmp
                    while True:
                        try:
                            message = await self.recv()
                            if message:
                                break
                        except (asyncio.CancelledError, KeyboardInterrupt):
                            raise Close
                except Close:
                    heartbeat_task.cancel()
                    await ws.close()
                    return
                except Reconnect:
                    await asyncio.sleep(3)
                    heartbeat_task.cancel()
                    _ws = self.ws
                    self._ws = None
                    try:
                        await _ws.close()
                    except:
                        pass
                    break
                else:
                    if not await self._handle(message):
                        if self.logged_out:
                            try:
                                await ws.close()
                            except:  # Ignore close
                                pass
                            return
                        exc = Reconnect()

            if not ws.closed:
                try:
                    await ws.close()
                except Exception as exc:
                    _L.warning("failed to close websocket", exc_info=exc)
        if self._closing_future:
            self._closing_future.set_result(None)
        self._last_close_code = None

    async def _handle(self, d: raw.ClientEvent) -> bool:
        authenticated = True
        if d["type"] == "Pong":
            nonce = d["data"]
            if nonce != self._heartbeat_sequence:
                extra = ""
                if isinstance(nonce, int) and nonce < self._heartbeat_sequence:
                    extra = (
                        f"nonce is behind of {self._heartbeat_sequence - nonce} beats"
                    )
                if self.reconnect_on_timeout:
                    _L.error(
                        "missed Pong, expected %s, got %s (%s)",
                        self._heartbeat_sequence,
                        nonce,
                        extra,
                    )
                else:
                    _L.warn(
                        "missed Pong, expected %s, got %s (%s)",
                        self._heartbeat_sequence,
                        nonce,
                        extra,
                    )
                return not self.reconnect_on_timeout
        elif d["type"] == "Logout":
            authenticated = False

        if self.handler is not None:
            # asyncio.create_task(self.handler.handle_raw(self, d), name=f"pyvolt-eht-{self._sequence}")
            try:
                await self.handler.handle_raw(self, d)
            except Exception as exc:
                _L.exception("error occured on seq=%s", self._sequence, exc_info=exc)
            self._sequence += 1
        return authenticated


__all__ = ("Close", "Reconnect", "EventHandler", "DEFAULT_SHARD_USER_AGENT", "Shard")
