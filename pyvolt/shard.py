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

from abc import ABC, abstractmethod
import aiohttp
import asyncio
from inspect import isawaitable
import logging
import typing

from . import utils
from .core import ULIDOr, resolve_id, __version__ as version
from .enums import ShardFormat
from .errors import PyvoltError, ShardClosedError, AuthenticationError, ConnectError

if typing.TYPE_CHECKING:
    from datetime import datetime

    from . import raw
    from .channel import TextChannel
    from .server import BaseServer
    from .state import State

try:
    import msgpack  # type: ignore
except ImportError:
    _HAS_MSGPACK = False
else:
    _HAS_MSGPACK = True

_L = logging.getLogger(__name__)


class Close(Exception):
    __slots__ = ()


class Reconnect(Exception):
    __slots__ = ()


class EventHandler(ABC):
    """A handler for shard events."""

    __slots__ = ()

    @abstractmethod
    def handle_raw(self, shard: Shard, payload: raw.ClientEvent, /) -> utils.MaybeAwaitable[None]:
        """Handles dispatched event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard that received the event.
        payload: Dict[:class:`str`, Any]
            The received event payload.
        """
        ...

    def before_connect(self, shard: Shard, /) -> utils.MaybeAwaitable[None]:
        """Called before connecting to Revolt."""
        ...

    def after_connect(self, shard: Shard, socket: aiohttp.ClientWebSocketResponse, /) -> utils.MaybeAwaitable[None]:
        """Called when successfully connected to Revolt WebSocket.

        Parameters
        ----------
        socket: :class:`aiohttp.ClientWebSocketResponse`
            The connected WebSocket.
        """
        ...


DEFAULT_SHARD_USER_AGENT = f'pyvolt Shard client (https://github.com/MCausc78/pyvolt, {version})'


class Shard:
    """Implements Revolt WebSocket client.

    Attributes
    ----------
    base: :class:`str`
        The base WebSocket URL.
    bot: :class:`bool`
        Whether the token belongs to bot account. Defaults to ``True``.
    connect_delay: Optional[:class:`float`]
        The duration in seconds to sleep when reconnecting to WebSocket due to aiohttp errors. Defaults to 2.
    format: :class:`ShardFormat`
        The message format to use when communicating with Revolt WebSocket.
    handler: Optional[:class:`.EventHandler`]
        The handler that receives events. Defaults to ``None`` if not provided.
    last_ping_at: Optional[:class:`~datetime.datetime`]
        When the shard sent ping.
    last_pong_at: Optional[:class:`~datetime.datetime`]
        When the shard received response to ping.
    logged_out: :class:`bool`
        Whether the shard got logged out.
    reconnect_on_timeout: :class:`bool`
        Whether to reconnect when received pong nonce is not equal to current ping nonce. Defaults to ``True``.
    request_user_settings: Optional[List[:class:`str`]]
        The list of user setting keys to request.
    state: :class:`State`
        The state.
    token: :class:`str`
        The shard token. May be empty if not started.
    user_agent: :class:`str`
        The HTTP user agent used when connecting to WebSocket.
    """

    _socket: aiohttp.ClientWebSocketResponse | None

    __slots__ = (
        '_closed',
        '_heartbeat_sequence',
        '_last_close_code',
        '_sequence',
        '_session',
        '_socket',
        'base',
        'bot',
        'connect_delay',
        'format',
        'handler',
        'last_ping_at',
        'last_pong_at',
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
        connect_delay: float | None = 2,
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

        self._closed: bool = False
        self._heartbeat_sequence: int = 1
        self._last_close_code: int | None = None
        self._sequence: int = 0
        self._session = session
        self._socket: aiohttp.ClientWebSocketResponse | None = None
        self.base: str = base or 'wss://ws.revolt.chat/'
        self.bot: bool = bot
        self.connect_delay: int | float | None = connect_delay
        self.format: ShardFormat = format
        self.handler: EventHandler | None = handler
        self.last_ping_at: datetime | None = None
        self.last_pong_at: datetime | None = None
        self.logged_out: bool = False
        self.reconnect_on_timeout: bool = reconnect_on_timeout
        self.request_user_settings = request_user_settings
        self.retries: int = retries or 150
        self.state: State = state
        self.token: str = token
        self.user_agent: str = user_agent or DEFAULT_SHARD_USER_AGENT

        self.recv = self._recv_json if format is ShardFormat.json else self._recv_msgpack
        self.send = self._send_json if format is ShardFormat.json else self._send_msgpack

    def is_closed(self) -> bool:
        return self._closed and not self._socket

    async def cleanup(self) -> None:
        """|coro|

        Closes the aiohttp session.
        """
        if not callable(self._session):
            await self._session.close()

    async def close(self) -> None:
        """|coro|

        Closes the connection to Revolt.
        """
        if self._socket:
            if self._closed:
                raise ShardClosedError('Already closed')
            self._closed = True
            await self._socket.close(code=1000)

    @property
    def socket(self) -> aiohttp.ClientWebSocketResponse:
        """:class:`aiohttp.ClientWebSocketResponse`: The current WebSocket connection."""
        if self._socket is None:
            raise TypeError('No websocket')
        return self._socket

    def with_credentials(self, token: str, *, bot: bool = True) -> None:
        """Modifies HTTP request credentials.

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
        self.last_ping_at = utils.utcnow()

    async def begin_typing(self, channel: ULIDOr[TextChannel], /) -> None:
        """|coro|

        Begins typing in a channel.

        Parameters
        ----------
        channel: ULIDOr[:class:`TextChannel`]
            The channel to begin typing in.
        """
        payload: raw.ServerBeginTypingEvent = {'type': 'BeginTyping', 'channel': resolve_id(channel)}
        await self.send(payload)

    async def end_typing(self, channel: ULIDOr[TextChannel], /) -> None:
        """|coro|

        Ends typing in a channel.

        Parameters
        ----------
        channel: ULIDOr[:class:`TextChannel`]
            The channel to end typing in.
        """
        payload: raw.ServerEndTypingEvent = {'type': 'EndTyping', 'channel': resolve_id(channel)}
        await self.send(payload)

    async def subscribe_to(self, server: ULIDOr[BaseServer], /) -> None:
        """|coro|

        Subscribes to a server. After calling this method, you'll receive :class:`UserUpdateEvent`'s.

        Parameters
        ----------
        server: ULIDOr[:class:`BaseServer`]
            The server to subscribe to.
        """
        payload: raw.ServerSubscribeEvent = {'type': 'Subscribe', 'server_id': resolve_id(server)}
        await self.send(payload)

    async def _send_json(self, d: raw.ServerEvent, /) -> None:
        _L.debug('sending %s', d)
        await self.socket.send_str(utils.to_json(d))

    async def _send_msgpack(self, d: raw.ServerEvent, /) -> None:
        _L.debug('sending %s', d)

        # Will never none according to stubs: https://github.com/sbdchd/msgpack-types/blob/a9ab1c861933fa11aff706b21c303ee52a2ee359/msgpack-stubs/__init__.pyi#L40-L49
        payload: bytes = msgpack.packb(d)  # type: ignore
        await self.socket.send_bytes(payload)

    async def _recv_json(self) -> raw.ClientEvent:
        try:
            message = await self.socket.receive()
        except (KeyboardInterrupt, asyncio.CancelledError):
            raise Close

        if message.type in (
            aiohttp.WSMsgType.CLOSE,
            aiohttp.WSMsgType.CLOSED,
            aiohttp.WSMsgType.CLOSING,
        ):
            self._last_close_code = data = self.socket.close_code
            _L.debug('WebSocket closed with %s (closed: %s)', data, self._closed)
            if self._closed:
                raise Close
            await asyncio.sleep(0.5)
            raise Reconnect

        if message.type is aiohttp.WSMsgType.ERROR:
            _L.debug('Received invalid WebSocket payload. Reconnecting.')
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
            message = await self.socket.receive()
        except (KeyboardInterrupt, asyncio.CancelledError):
            raise Close

        if message.type in (
            aiohttp.WSMsgType.CLOSE,
            aiohttp.WSMsgType.CLOSED,
            aiohttp.WSMsgType.CLOSING,
        ):
            self._last_close_code = data = self.socket.close_code
            _L.debug('WebSocket closed with %s (was closed: %s)', data, self._closed)
            if self._closed:
                raise Close
            await asyncio.sleep(0.2)
            raise Reconnect

        if message.type is aiohttp.WSMsgType.ERROR:
            _L.debug('Received invalid WebSocket payload. Reconnecting.')
            raise Reconnect

        if message.type is not aiohttp.WSMsgType.BINARY:
            _L.debug(
                'Received unknown message type: %s (expected BINARY). Reconnecting.',
                message.type,
            )
            raise Reconnect

        # `msgpack` wont be unbound here
        k: raw.ClientEvent = msgpack.unpackb(message.data, use_list=True)  # type: ignore
        if k['type'] != 'Ready':
            _L.debug('Received %s', k)
        return k

    def get_headers(self) -> dict[str, str]:
        """Dict[:class:`str`, :class:`str`]: The headers to use when connecting to WebSocket."""
        return {'User-Agent': self.user_agent}

    async def _heartbeat(self) -> None:
        while True:
            await asyncio.sleep(30.0)
            await self.ping()

    async def ws_connect(
        self, session: aiohttp.ClientSession, url: str, /, *, headers: dict[str, str], params: dict[str, str]
    ) -> aiohttp.ClientWebSocketResponse:
        """|coro|

        Start a WebSocket connection.

        Parameters
        ----------
        session: :class:`aiohttp.ClientSession`
            The session to use when connecting.
        url: :class:`str`
            The URL to connect to.
        headers: Dict[:class:`str`, :class:`str`]
            The HTTP headers.
        params: Dict[:class:`str`, :class:`str`]
            The HTTP query string parameters.

        Returns
        -------
        :class:`aiohttp.ClientWebSocketResponse`
            The WebSocket connection.
        """
        return await session.ws_connect(
            url,
            headers=headers,
            params=params,
        )

    async def _socket_connect(self) -> aiohttp.ClientWebSocketResponse:
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

        i = 0
        _L.debug('Connecting to %s, format=%s', self.base, self.format)

        headers = self.get_headers()
        while True:
            if i >= self.retries:
                break
            try:
                return await self.ws_connect(
                    session,
                    self.base,
                    headers=headers,
                    params=params,  # type: ignore # Not true
                )
            except OSError as exc:
                if i == 0:
                    _L.warning('Connection failed (code: %i)', exc.errno)
                if exc.errno == 11001:
                    await asyncio.sleep(1)
                i += 1
            except aiohttp.WSServerHandshakeError as exc:
                _L.debug('Server replied with %i', exc.code)
                if exc.code in (502, 525):
                    await asyncio.sleep(1.5)
                    continue
                raise exc from None
            except Exception as exc:
                i += 1
                errors.append(exc)
                _L.exception('Connection failed on %i attempt', i)
                if self.connect_delay is not None:
                    await asyncio.sleep(self.connect_delay)
        raise ConnectError(self.retries, errors)

    async def connect(self) -> None:
        """|coro|

        Starts the WebSocket lifecycle.
        """
        if self._socket:
            raise PyvoltError('The connection is already open.')
        while not self._closed:
            if self.handler:
                r = self.handler.before_connect(self)
                if isawaitable(r):
                    await r

            socket = await self._socket_connect()
            if self.handler:
                r = self.handler.after_connect(self, socket)
                if isawaitable(r):
                    await r

            self._closed = False
            self._last_close_code = None

            self._socket = socket
            heartbeat_task = asyncio.create_task(self._heartbeat())

            try:
                await self.authenticate()

                message = await self.recv()
                if message['type'] != 'Authenticated':
                    raise AuthenticationError(message)  # type: ignore

                self.logged_out = False
                await self._handle(message)
                message = None
            except:
                heartbeat_task.cancel()
                raise
            else:
                heartbeat_task.cancel()
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
                    await socket.close()
                    return
                except Reconnect:
                    await asyncio.sleep(1)
                    heartbeat_task.cancel()
                    _socket = self.socket
                    self._socket = None
                    try:
                        await _socket.close()
                    except Exception:
                        pass
                    break
                else:
                    r = self._handle(message)
                    if isawaitable(r):
                        r = await r
                    if not r:
                        if self.logged_out:
                            try:
                                await socket.close()
                            except Exception:  # Ignore close error
                                pass
                            return
                        exc = Reconnect()

            if not socket.closed:
                try:
                    await socket.close()
                except Exception as exc:
                    _L.warning('failed to close websocket', exc_info=exc)
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
                    _L.warning(
                        'missed Pong, expected %s, got %s (%s)',
                        self._heartbeat_sequence,
                        nonce,
                        extra,
                    )
                return not self.reconnect_on_timeout
            self.last_pong_at = utils.utcnow()
        elif payload['type'] == 'Logout':
            authenticated = False

        if self.handler is not None:
            r = self.handler.handle_raw(self, payload)
            if isawaitable(r):
                await r
            self._sequence += 1
        return authenticated


__all__ = ('Close', 'Reconnect', 'EventHandler', 'DEFAULT_SHARD_USER_AGENT', 'Shard')
