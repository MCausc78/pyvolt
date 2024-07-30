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

import abc
import aiohttp
import asyncio
import logging
import typing

from . import utils
from .core import ULIDOr, resolve_id, __version__ as version
from .enums import Enum
from .errors import PyvoltError, ShardError, AuthenticationError, ConnectError

if typing.TYPE_CHECKING:
    from . import raw
    from .channel import TextChannel
    from .server import BaseServer
    from .state import State

try:
    import msgpack
except ImportError:
    _HAS_MSGPACK = False
else:
    _HAS_MSGPACK = True

_L = logging.getLogger(__name__)


class Close(Exception):
    __slots__ = ()


class Reconnect(Exception):
    __slots__ = ()


class EventHandler(abc.ABC):
    @abc.abstractmethod
    async def handle_raw(self, shard: Shard, payload: raw.ClientEvent, /) -> None: ...


DEFAULT_SHARD_USER_AGENT = f'pyvolt Shard client (https://github.com/MCausc78/pyvolt, {version})'


class ShardFormat(Enum):
    json = 'json'
    msgpack = 'msgpack'


class Shard:
    """Implementation of Revolt WebSocket client."""

    _closing_future: asyncio.Future[None] | None
    _ws: aiohttp.ClientWebSocketResponse | None

    __slots__ = (
        '_closed',
        '_closing_future',
        '_heartbeat_sequence',
        '_last_close_code',
        '_sequence',
        '_session',
        '_ws',
        'base',
        'bot',
        'connect_delay',
        'format',
        'handler',
        'logged_out',
        'reconnect_on_timeout',
        'request_user_settings',
        'retries',
        'state',
        'token',
        'user_agent',
        'recv',
        'send',
    )

    def __init__(
        self,
        token: str,
        *,
        base: str | None = None,
        bot: bool = True,
        connect_delay: int | float | None = 2,
        format: ShardFormat = ShardFormat.json,
        handler: EventHandler | None = None,
        reconnect_on_timeout: bool = True,
        request_user_settings: list[str] | None = None,
        retries: int | None = None,
        session: utils.MaybeAwaitableFunc[[Shard], aiohttp.ClientSession] | aiohttp.ClientSession,
        state: State,
        user_agent: str | None = None,
    ) -> None:
        if format is ShardFormat.msgpack and not _HAS_MSGPACK:
            raise TypeError('Cannot use msgpack format without dependency')

        self._closed = False
        self._closing_future = None
        self._heartbeat_sequence = 1
        self._last_close_code = None
        self._sequence = 0
        self._ws = None
        self.base = base or 'wss://ws.revolt.chat/'
        self.bot = bot
        self.connect_delay = connect_delay
        self.format = format
        self.handler = handler
        self.logged_out = False
        self.reconnect_on_timeout = reconnect_on_timeout
        self.request_user_settings = request_user_settings
        self.retries = retries or 150
        self._session = session
        self.state = state
        self.token = token
        self.user_agent = user_agent or DEFAULT_SHARD_USER_AGENT

        self.recv = self._recv_json if format is ShardFormat.json else self._recv_msgpack
        self.send = self._send_json if format is ShardFormat.json else self._send_msgpack

    def is_closed(self) -> bool:
        return self._closed and not self._ws

    async def close(self) -> None:
        if self._ws:
            if self._closed:
                raise ShardError('Already closed')
            self._closing_future = None
            self._closed = True
            await self._ws.close(code=1000)

    @property
    def ws(self) -> aiohttp.ClientWebSocketResponse:
        if self._ws is None:
            raise TypeError('No websocket')
        return self._ws

    def with_credentials(self, token: str, *, bot: bool = True) -> None:
        """Modifies HTTP client credentials.

        Parameters
        ----------
        token: :class:`str`
            The authentication token.
        bot: :class:`bool`
            Whether the token belongs to bot account or not.
        """
        self.token = token
        self.bot = bot

    async def authenticate(self) -> None:
        """|coro|

        Authenticates the currently connected WebSocket. This is called right after successful WebSocket handshake.
        """
        payload: raw.ServerAuthenticateEvent = {
            'type': 'Authenticate',
            'token': self.token,
        }
        await self.send(payload)

    async def ping(self) -> None:
        """|coro|

        Pings the WebSocket.
        """
        self._heartbeat_sequence += 1
        payload: raw.ServerPingEvent = {
            'type': 'Ping',
            'data': self._heartbeat_sequence,
        }
        await self.send(payload)

    async def begin_typing(self, channel: ULIDOr[TextChannel]) -> None:
        """|coro|

        Begins typing in a channel.

        Parameters
        ----------
        channel: :class:`ULIDOr`[:class:`TextChannel`]
            The channel to begin typing in.
        """
        payload: raw.ServerBeginTypingEvent = {'type': 'BeginTyping', 'channel': resolve_id(channel)}
        await self.send(payload)

    async def end_typing(self, channel: ULIDOr[TextChannel]) -> None:
        """|coro|

        Ends typing in a channel.

        Parameters
        ----------
        channel: :class:`ULIDOr`[:class:`TextChannel`]
            The channel to end typing in.
        """
        payload: raw.ServerEndTypingEvent = {'type': 'EndTyping', 'channel': resolve_id(channel)}
        await self.send(payload)

    async def subscribe_to(self, server: ULIDOr[BaseServer]) -> None:
        """|coro|

        Subscribes to a server. After calling this method, you'll receive :class:`UserUpdateEvent`'s.

        Parameters
        ----------
        server: :class:`ULIDOr`[:class:`BaseServer`]
            The server to subscribe to.
        """
        payload: raw.ServerSubscribeEvent = {'type': 'Subscribe', 'server_id': resolve_id(server)}
        await self.send(payload)

    async def _send_json(self, d: raw.ServerEvent, /) -> None:
        _L.debug('sending %s', d)
        await self.ws.send_str(utils.to_json(d))

    async def _send_msgpack(self, d: raw.ServerEvent, /) -> None:
        _L.debug('sending %s', d)

        # Will never none according to stubs: https://github.com/sbdchd/msgpack-types/blob/a9ab1c861933fa11aff706b21c303ee52a2ee359/msgpack-stubs/__init__.pyi#L40-L49
        payload: bytes = msgpack.packb(d)  # type: ignore
        await self.ws.send_bytes(payload)

    async def _recv_json(self) -> raw.ClientEvent:
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
            _L.debug('Websocket closed: %s', data)
            if self._closed:
                raise Close
            else:
                await asyncio.sleep(0.5)
                raise Reconnect

        if message.type is aiohttp.WSMsgType.ERROR:
            _L.debug('Received invalid websocket payload. Reconnecting.')
            raise Reconnect

        if message.type is not aiohttp.WSMsgType.TEXT:
            _L.debug(
                'Received unknown message type: %s (expected TEXT). Reconnecting.',
                message.type,
            )
            raise Reconnect

        k = utils.from_json(message.data)
        if k['type'] != 'Ready':
            _L.debug('Received %s', k)
        return k

    async def _recv_msgpack(self) -> raw.ClientEvent:
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
            _L.debug('Websocket closed: %s', data)
            if self._closed:
                raise Close
            else:
                await asyncio.sleep(0.5)
                raise Reconnect
        if message.type is aiohttp.WSMsgType.ERROR:
            _L.debug('Received invalid websocket payload, reconnecting')
            raise Reconnect

        if message.type is not aiohttp.WSMsgType.BINARY:
            _L.debug(
                'Received unknown message type: %s (expected BINARY). Reconnecting.',
                message.type,
            )
            raise Reconnect

        # `msgpack` wont be unbound here
        k = msgpack.unpackb(message.data, use_list=True)  # type: ignore
        if k['type'] != 'Ready':
            _L.debug('received %s', k)
        return k

    def _headers(self) -> dict[str, str]:
        return {'user-agent': self.user_agent}

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
                raise TypeError(f'Expected aiohttp.ClientSession, not {type(session)!r}')
            # Do not call factory on future requests
            self._session = session

        params: raw.BonfireConnectionParameters = {
            'version': '1',
            'format': self.format.value,
        }
        if self.request_user_settings is not None:
            params['__user_settings_keys'] = ','.join(self.request_user_settings)

        errors = []
        for i in range(self.retries):
            try:
                _L.debug('Connecting to %s, format=%s, try=%i', self.base, self.format, i)
                return await session.ws_connect(
                    self.base,
                    headers=self._headers(),
                    params=params,  # type: ignore # Not true
                )
            except OSError as exc:
                # TODO: Handle 10053?
                if exc.errno in (54, 10054):  # Connection reset by peer
                    await asyncio.sleep(1.5)
                    continue
                errors.append(exc)
            except Exception as exc:
                errors.append(exc)
                _L.debug('connection failed on try=%i: %s', i, exc)
                if self.connect_delay is not None:
                    await asyncio.sleep(self.connect_delay)
        raise ConnectError(self.retries, errors)

    async def _connect(self) -> None:
        if self._ws:
            raise PyvoltError('The connection is already open.')
        self._closing_future = asyncio.Future()
        self._last_close_code = None
        while not self._closed:
            ws = await self._ws_connect()

            self._ws = ws
            await self.authenticate()

            message = await self.recv()
            if message is None or message['type'] != 'Authenticated':
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
                    try:
                        message = await self.recv()
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
                    except Exception:
                        pass
                    break
                else:
                    if not await self._handle(message):
                        if self.logged_out:
                            try:
                                await ws.close()
                            except Exception:  # Ignore close error
                                pass
                            return
                        exc = Reconnect()

            if not ws.closed:
                try:
                    await ws.close()
                except Exception as exc:
                    _L.warning('failed to close websocket', exc_info=exc)
        if self._closing_future:
            self._closing_future.set_result(None)
        self._last_close_code = None

    async def _handle(self, payload: raw.ClientEvent, /) -> bool:
        authenticated = True
        if payload['type'] == 'Pong':
            nonce = payload['data']
            if nonce != self._heartbeat_sequence:
                extra = ''
                if isinstance(nonce, int) and nonce < self._heartbeat_sequence:
                    extra = f'nonce is behind of {self._heartbeat_sequence - nonce} beats'
                if self.reconnect_on_timeout:
                    _L.error(
                        'missed Pong, expected %s, got %s (%s)',
                        self._heartbeat_sequence,
                        nonce,
                        extra,
                    )
                else:
                    _L.warn(
                        'missed Pong, expected %s, got %s (%s)',
                        self._heartbeat_sequence,
                        nonce,
                        extra,
                    )
                return not self.reconnect_on_timeout
        elif payload['type'] == 'Logout':
            authenticated = False

        if self.handler is not None:
            await self.handler.handle_raw(self, payload)
            self._sequence += 1
        return authenticated


__all__ = ('Close', 'Reconnect', 'EventHandler', 'DEFAULT_SHARD_USER_AGENT', 'Shard')
