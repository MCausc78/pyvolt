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

import aiohttp
import asyncio
import builtins
from inspect import isawaitable
import logging
import typing

from . import cache as caching, utils
from .cache import Cache, MapCache
from .cdn import CDNClient
from .channel import SavedMessagesChannel, DMChannel, GroupChannel, Channel
from .core import (
    UNDEFINED,
    UndefinedOr,
    ULIDOr,
)
from .emoji import Emoji
from .events import BaseEvent
from .http import HTTPClient
from .parser import Parser
from .server import Server
from .shard import EventHandler, Shard
from .state import State
from .user import BaseUser, User, OwnUser


if typing.TYPE_CHECKING:
    from collections.abc import Callable, Coroutine, Generator, Mapping
    from types import TracebackType
    from typing_extensions import Self

    from . import raw
    from .events import (
        AuthenticatedEvent,
        AuthifierEvent,
        BaseChannelCreateEvent,
        BaseEvent,
        BulkMessageDeleteEvent,
        ChannelDeleteEvent,
        ChannelStartTypingEvent,
        ChannelStopTypingEvent,
        ChannelUpdateEvent,
        GroupRecipientAddEvent,
        GroupRecipientRemoveEvent,
        LogoutEvent,
        MessageAckEvent,
        MessageAppendEvent,
        MessageClearReactionEvent,
        MessageCreateEvent,
        MessageDeleteEvent,
        MessageReactEvent,
        MessageUnreactEvent,
        MessageUpdateEvent,
        PrivateChannelCreateEvent,
        RawServerRoleUpdateEvent,
        ReadyEvent,
        ServerChannelCreateEvent,
        ServerCreateEvent,
        ServerDeleteEvent,
        ServerEmojiCreateEvent,
        ServerEmojiDeleteEvent,
        ServerMemberJoinEvent,
        ServerMemberRemoveEvent,
        ServerMemberUpdateEvent,
        ServerRoleDeleteEvent,
        ServerUpdateEvent,
        SessionCreateEvent,
        SessionDeleteAllEvent,
        SessionDeleteEvent,
        UserPlatformWipeEvent,
        UserRelationshipUpdateEvent,
        UserSettingsUpdateEvent,
        UserUpdateEvent,
        WebhookCreateEvent,
        WebhookDeleteEvent,
        WebhookUpdateEvent,
        BeforeConnectEvent,
        AfterConnectEvent,
    )
    from .message import Message
    from .read_state import ReadState
    from .user_settings import UserSettings


_L = logging.getLogger(__name__)


def _session_factory(_) -> aiohttp.ClientSession:
    return aiohttp.ClientSession()


class ClientEventHandler(EventHandler):
    """The default event handler for the client."""

    __slots__ = ('_client', '_state', 'dispatch', '_handlers')

    def __init__(self, client: Client) -> None:
        self._client = client
        self._state = client._state
        self.dispatch = client.dispatch

        self._handlers = {
            'Bulk': self.handle_bulk,
            'Authenticated': self.handle_authenticated,
            'Logout': self.handle_logout,
            'Ready': self.handle_ready,
            'Pong': self.handle_pong,
            'Message': self.handle_message,
            'MessageUpdate': self.handle_message_update,
            'MessageAppend': self.handle_message_append,
            'MessageDelete': self.handle_message_delete,
            'MessageReact': self.handle_message_react,
            'MessageUnreact': self.handle_message_unreact,
            'MessageRemoveReaction': self.handle_message_remove_reaction,
            'BulkMessageDelete': self.handle_bulk_message_delete,
            'ServerCreate': self.handle_server_create,
            'ServerUpdate': self.handle_server_update,
            'ServerDelete': self.handle_server_delete,
            'ServerMemberJoin': self.handle_server_member_join,
            'ServerMemberUpdate': self.handle_server_member_update,
            'ServerMemberLeave': self.handle_server_member_leave,
            'ServerRoleUpdate': self.handle_server_role_update,
            'ServerRoleDelete': self.handle_server_role_delete,
            'UserUpdate': self.handle_user_update,
            'UserRelationship': self.handle_user_relationship,
            'UserSettingsUpdate': self.handle_user_settings_update,
            'UserPlatformWipe': self.handle_user_platform_wipe,
            'EmojiCreate': self.handle_emoji_create,
            'EmojiDelete': self.handle_emoji_delete,
            'ChannelCreate': self.handle_channel_create,
            'ChannelUpdate': self.handle_channel_update,
            'ChannelDelete': self.handle_channel_delete,
            'ChannelGroupJoin': self.handle_channel_group_join,
            'ChannelGroupLeave': self.handle_channel_group_leave,
            'ChannelStartTyping': self.handle_channel_start_typing,
            'ChannelStopTyping': self.handle_channel_stop_typing,
            'ChannelAck': self.handle_channel_ack,
            'WebhookCreate': self.handle_webhook_create,
            'WebhookUpdate': self.handle_webhook_update,
            'WebhookDelete': self.handle_webhook_delete,
            'Auth': self.handle_auth,
        }

    async def handle_bulk(self, shard: Shard, payload: raw.ClientBulkEvent, /) -> None:
        for v in payload['v']:
            await self._handle(shard, v)

    def handle_authenticated(self, shard: Shard, payload: raw.ClientAuthenticatedEvent, /) -> None:
        self.dispatch(self._state.parser.parse_authenticated_event(shard, payload))

    def handle_logout(self, shard: Shard, payload: raw.ClientLogoutEvent, /) -> None:
        self.dispatch(self._state.parser.parse_logout_event(shard, payload))

    def handle_ready(self, shard: Shard, payload: raw.ClientReadyEvent, /) -> None:
        event = self._state.parser.parse_ready_event(shard, payload)
        self.dispatch(event)

    def handle_pong(self, shard: Shard, payload: raw.ClientPongEvent, /) -> None:
        pass

    def handle_message(self, shard: Shard, payload: raw.ClientMessageEvent, /) -> None:
        event = self._state.parser.parse_message_event(shard, payload)
        self.dispatch(event)

    def handle_message_update(self, shard: Shard, payload: raw.ClientMessageUpdateEvent, /) -> None:
        event = self._state.parser.parse_message_update_event(shard, payload)
        self.dispatch(event)

    def handle_message_append(self, shard: Shard, payload: raw.ClientMessageAppendEvent, /) -> None:
        event = self._state.parser.parse_message_append_event(shard, payload)
        self.dispatch(event)

    def handle_message_delete(self, shard: Shard, payload: raw.ClientMessageDeleteEvent, /) -> None:
        event = self._state.parser.parse_message_delete_event(shard, payload)
        self.dispatch(event)

    def handle_message_react(self, shard: Shard, payload: raw.ClientMessageReactEvent, /) -> None:
        event = self._state.parser.parse_message_react_event(shard, payload)
        self.dispatch(event)

    def handle_message_unreact(self, shard: Shard, payload: raw.ClientMessageUnreactEvent, /) -> None:
        event = self._state.parser.parse_message_unreact_event(shard, payload)
        self.dispatch(event)

    def handle_message_remove_reaction(self, shard: Shard, payload: raw.ClientMessageRemoveReactionEvent, /) -> None:
        event = self._state.parser.parse_message_remove_reaction_event(shard, payload)
        self.dispatch(event)

    def handle_bulk_message_delete(self, shard: Shard, payload: raw.ClientBulkMessageDeleteEvent, /) -> None:
        event = self._state.parser.parse_bulk_message_delete_event(shard, payload)
        self.dispatch(event)

    def handle_server_create(self, shard: Shard, payload: raw.ClientServerCreateEvent, /) -> None:
        joined_at = utils.utcnow()
        event = self._state.parser.parse_server_create_event(shard, payload, joined_at)
        self.dispatch(event)

    def handle_server_update(self, shard: Shard, payload: raw.ClientServerUpdateEvent, /) -> None:
        event = self._state.parser.parse_server_update_event(shard, payload)
        self.dispatch(event)

    def handle_server_delete(self, shard: Shard, payload: raw.ClientServerDeleteEvent, /) -> None:
        event = self._state.parser.parse_server_delete_event(shard, payload)
        self.dispatch(event)

    def handle_server_member_join(self, shard: Shard, payload: raw.ClientServerMemberJoinEvent, /) -> None:
        joined_at = utils.utcnow()
        event = self._state.parser.parse_server_member_join_event(shard, payload, joined_at)
        self.dispatch(event)

    def handle_server_member_update(self, shard: Shard, payload: raw.ClientServerMemberUpdateEvent, /) -> None:
        event = self._state.parser.parse_server_member_update_event(shard, payload)
        self.dispatch(event)

    def handle_server_member_leave(self, shard: Shard, payload: raw.ClientServerMemberLeaveEvent, /) -> None:
        event = self._state.parser.parse_server_member_leave_event(shard, payload)
        self.dispatch(event)

    def handle_server_role_update(self, shard: Shard, payload: raw.ClientServerRoleUpdateEvent, /) -> None:
        event = self._state.parser.parse_server_role_update_event(shard, payload)
        self.dispatch(event)

    def handle_server_role_delete(self, shard: Shard, payload: raw.ClientServerRoleDeleteEvent, /) -> None:
        event = self._state.parser.parse_server_role_delete_event(shard, payload)
        self.dispatch(event)

    def handle_user_update(self, shard: Shard, payload: raw.ClientUserUpdateEvent, /) -> None:
        event = self._state.parser.parse_user_update_event(shard, payload)
        self.dispatch(event)

    def handle_user_relationship(self, shard: Shard, payload: raw.ClientUserRelationshipEvent, /) -> None:
        event = self._state.parser.parse_user_relationship_event(shard, payload)
        self.dispatch(event)

    def handle_user_settings_update(self, shard: Shard, payload: raw.ClientUserSettingsUpdateEvent, /) -> None:
        event = self._state.parser.parse_user_settings_update_event(shard, payload)
        self.dispatch(event)

    def handle_user_platform_wipe(self, shard: Shard, payload: raw.ClientUserPlatformWipeEvent, /) -> None:
        event = self._state.parser.parse_user_platform_wipe_event(shard, payload)
        self.dispatch(event)

    def handle_emoji_create(self, shard: Shard, payload: raw.ClientEmojiCreateEvent, /) -> None:
        event = self._state.parser.parse_emoji_create_event(shard, payload)
        self.dispatch(event)

    def handle_emoji_delete(self, shard: Shard, payload: raw.ClientEmojiDeleteEvent, /) -> None:
        event = self._state.parser.parse_emoji_delete_event(shard, payload)
        self.dispatch(event)

    def handle_channel_create(self, shard: Shard, payload: raw.ClientChannelCreateEvent, /) -> None:
        event = self._state.parser.parse_channel_create_event(shard, payload)
        self.dispatch(event)

    def handle_channel_update(self, shard: Shard, payload: raw.ClientChannelUpdateEvent, /) -> None:
        event = self._state.parser.parse_channel_update_event(shard, payload)
        self.dispatch(event)

    def handle_channel_delete(self, shard: Shard, payload: raw.ClientChannelDeleteEvent, /) -> None:
        event = self._state.parser.parse_channel_delete_event(shard, payload)
        self.dispatch(event)

    def handle_channel_group_join(self, shard: Shard, payload: raw.ClientChannelGroupJoinEvent, /) -> None:
        event = self._state.parser.parse_channel_group_join_event(shard, payload)
        self.dispatch(event)

    def handle_channel_group_leave(self, shard: Shard, payload: raw.ClientChannelGroupLeaveEvent, /) -> None:
        event = self._state.parser.parse_channel_group_leave_event(shard, payload)
        self.dispatch(event)

    def handle_channel_start_typing(self, shard: Shard, payload: raw.ClientChannelStartTypingEvent, /) -> None:
        event = self._state.parser.parse_channel_start_typing_event(shard, payload)
        self.dispatch(event)

    def handle_channel_stop_typing(self, shard: Shard, payload: raw.ClientChannelStopTypingEvent, /) -> None:
        event = self._state.parser.parse_channel_stop_typing_event(shard, payload)
        self.dispatch(event)

    def handle_channel_ack(self, shard: Shard, payload: raw.ClientChannelAckEvent, /) -> None:
        event = self._state.parser.parse_channel_ack_event(shard, payload)
        self.dispatch(event)

    def handle_webhook_create(self, shard: Shard, payload: raw.ClientWebhookCreateEvent, /) -> None:
        event = self._state.parser.parse_webhook_create_event(shard, payload)
        self.dispatch(event)

    def handle_webhook_update(self, shard: Shard, payload: raw.ClientWebhookUpdateEvent, /) -> None:
        event = self._state.parser.parse_webhook_update_event(shard, payload)
        self.dispatch(event)

    def handle_webhook_delete(self, shard: Shard, payload: raw.ClientWebhookDeleteEvent, /) -> None:
        event = self._state.parser.parse_webhook_delete_event(shard, payload)
        self.dispatch(event)

    def handle_auth(self, shard: Shard, payload: raw.ClientAuthEvent, /) -> None:
        event = self._state.parser.parse_auth_event(shard, payload)
        self.dispatch(event)

    async def _handle_library_error(self, shard: Shard, payload: raw.ClientEvent, exc: Exception, name: str, /) -> None:
        try:
            r = self._client.on_library_error(shard, payload, exc)
            if isawaitable(r):
                await r
        except Exception:
            _L.exception('on_library_error (task: %s) raised an exception', name)

    async def _handle(self, shard: Shard, payload: raw.ClientEvent, /) -> None:
        type = payload['type']
        try:
            handler = self._handlers[type]
        except KeyError:
            _L.debug('Received unknown event: %s. Discarding.', type)
        else:
            _L.debug('Handling %s', type)
            try:
                r = handler(shard, payload)
                if isawaitable(r):
                    await r
            except Exception as exc:
                if type == 'Ready':
                    # This is fatal
                    raise

                _L.exception('%s handler raised an exception', type)

                name = f'pyvolt-dispatch-{self._client._get_i()}'
                asyncio.create_task(self._handle_library_error(shard, payload, exc, name), name=name)

    def handle_raw(self, shard: Shard, payload: raw.ClientEvent, /) -> utils.MaybeAwaitable[None]:
        return self._handle(shard, payload)

    def before_connect(self, shard: Shard, /) -> utils.MaybeAwaitable[None]:
        from .events import BeforeConnectEvent

        return self.dispatch(BeforeConnectEvent(shard=shard))

    def after_connect(self, shard: Shard, socket: aiohttp.ClientWebSocketResponse, /) -> utils.MaybeAwaitable[None]:
        from .events import AfterConnectEvent

        return self.dispatch(AfterConnectEvent(shard=shard, socket=socket))


# OOP in Python sucks.
ClientT = typing.TypeVar('ClientT', bound='Client')
EventT = typing.TypeVar('EventT', bound='BaseEvent')


def _parents_of(type: type[BaseEvent]) -> tuple[type[BaseEvent], ...]:
    """Returns parents of BaseEvent, including BaseEvent itself."""
    if type is BaseEvent:
        return (BaseEvent,)
    tmp: typing.Any = type.__mro__[:-1]
    return tmp


class EventSubscription(typing.Generic[EventT]):
    """Represents a event subscription.

    Attributes
    ----------
    client: :class:`Client`
        The client that this subscription is tied to.
    id: :class:`int`
        The ID of the subscription.
    callback
        The callback.
    """

    __slots__ = (
        'client',
        'id',
        'callback',
        'event',
    )

    def __init__(
        self,
        *,
        client: Client,
        id: int,
        callback: utils.MaybeAwaitableFunc[[EventT], None],
        event: type[EventT],
    ) -> None:
        self.client: Client = client
        self.id: int = id
        self.callback: utils.MaybeAwaitableFunc[[EventT], None] = callback
        self.event: type[EventT] = event

    def __call__(self, arg: EventT, /) -> utils.MaybeAwaitable[None]:
        return self.callback(arg)

    async def _handle(self, arg: EventT, name: str, /) -> None:
        await self.client._run_callback(self.callback, arg, name)

    def remove(self) -> None:
        """Removes the event subscription."""
        self.client._handlers[self.event][0].pop(self.id, None)


class TemporarySubscription(typing.Generic[EventT]):
    """Represents a temporary event subscription."""

    __slots__ = (
        'client',
        'id',
        'event',
        'future',
        'check',
        'coro',
    )

    def __init__(
        self,
        *,
        client: Client,
        id: int,
        event: type[EventT],
        future: asyncio.Future[EventT],
        check: Callable[[EventT], utils.MaybeAwaitable[bool]],
        coro: Coroutine[typing.Any, typing.Any, EventT],
    ) -> None:
        self.client: Client = client
        self.id: int = id
        self.event: type[EventT] = event
        self.future: asyncio.Future[EventT] = future
        self.check: Callable[[EventT], utils.MaybeAwaitable[bool]] = check
        self.coro: Coroutine[typing.Any, typing.Any, EventT] = coro

    def __await__(self) -> Generator[typing.Any, typing.Any, EventT]:
        return self.coro.__await__()

    async def _handle(self, arg: EventT, name: str, /) -> bool:
        try:
            can = self.check(arg)
            if isawaitable(can):
                can = await can

            if can:
                self.future.set_result(arg)
            return can
        except Exception as exc:
            try:
                self.future.set_exception(exc)
            except Exception:
                _L.exception('Checker function (task: %s) raised an exception', name)
            return True

    def cancel(self) -> None:
        """Cancels the subscription."""
        self.future.cancel()
        self.client._handlers[self.event][1].pop(self.id, None)


_DEFAULT_HANDLERS = ({}, {})


def _private_channel_sort_old(channel: DMChannel | GroupChannel) -> str:
    return channel.last_message_id or '0'


def _private_channel_sort_new(channel: DMChannel | GroupChannel) -> str:
    return channel.last_message_id or channel.id


class Client:
    """A Revolt client."""

    __slots__ = (
        '_handlers',
        '_i',
        '_state',
        '_token',
        '_types',
        'bot',
        'closed',
        'extra',
    )

    @typing.overload
    def __init__(
        self,
        *,
        token: str = '',
        bot: bool = True,
        state: Callable[[Client], State] | State | None = None,
    ) -> None: ...

    @typing.overload
    def __init__(
        self,
        *,
        token: str = '',
        bot: bool = True,
        cache: Callable[[Client, State], UndefinedOr[Cache | None]] | UndefinedOr[Cache | None] = UNDEFINED,
        cdn_base: str | None = None,
        cdn_client: Callable[[Client, State], CDNClient] | None = None,
        http_base: str | None = None,
        http: Callable[[Client, State], HTTPClient] | None = None,
        parser: Callable[[Client, State], Parser] | None = None,
        shard: Callable[[Client, State], Shard] | None = None,
        request_user_settings: list[str] | None = None,
        websocket_base: str | None = None,
    ) -> None: ...

    def __init__(
        self,
        *,
        token: str = '',
        bot: bool = True,
        cache: Callable[[Client, State], UndefinedOr[Cache | None]] | UndefinedOr[Cache | None] = UNDEFINED,
        cdn_base: str | None = None,
        cdn_client: Callable[[Client, State], CDNClient] | None = None,
        http_base: str | None = None,
        http: Callable[[Client, State], HTTPClient] | None = None,
        parser: Callable[[Client, State], Parser] | None = None,
        shard: Callable[[Client, State], Shard] | None = None,
        state: Callable[[Client], State] | State | None = None,
        request_user_settings: list[str] | None = None,
        websocket_base: str | None = None,
    ) -> None:
        self.closed: bool = True
        # {Type[BaseEvent]: List[utils.MaybeAwaitableFunc[[BaseEvent], None]]}
        self._handlers: dict[
            type[BaseEvent],
            tuple[
                dict[int, EventSubscription[BaseEvent]],
                dict[int, TemporarySubscription[BaseEvent]],
            ],
        ] = {}
        # {Type[BaseEvent]: Tuple[Type[BaseEvent], ...]}
        self._types: dict[type[BaseEvent], tuple[type[BaseEvent], ...]] = {}
        self._i = 0

        self.extra = {}
        if state:
            if callable(state):
                self._state: State = state(self)
            else:
                self._state = state
        else:  # elif any(x is not None for x in (cache, cdn_client, http, parser, shard)):
            state = State()

            c = None
            if callable(cache):
                cr = cache(self, state)
            else:
                cr = cache
            c = cr if cr is not UNDEFINED else MapCache()

            if parser:
                state.setup(parser=parser(self, state))
            state.setup(
                cache=c,
                cdn_client=(
                    cdn_client(self, state)
                    if cdn_client
                    else CDNClient(
                        base=cdn_base,
                        session=_session_factory,
                        state=state,
                    )
                ),
                http=(
                    http(self, state)
                    if http
                    else HTTPClient(
                        token,
                        base=http_base,
                        bot=bot,
                        session=_session_factory,
                        state=state,
                    )
                ),
            )
            self._state = state
            state.setup(
                shard=(
                    shard(self, state)
                    if shard
                    else Shard(
                        token,
                        base=websocket_base,
                        handler=ClientEventHandler(self),
                        request_user_settings=request_user_settings,
                        session=_session_factory,
                        state=state,
                    )
                )
            )
        self._token = token
        self.bot = bot
        # self._subscribe_methods()

    def _get_i(self) -> int:
        self._i += 1
        return self._i

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException | None,
        traceback: TracebackType | None,
        /,
    ) -> None:
        await self.close()

    async def on_user_error(self, event: BaseEvent) -> None:
        """Handles user errors that came from handlers.
        You can get current exception being raised via :func:`sys.exc_info`.

        By default, this logs exception.
        """
        _L.exception(
            'One of %s handlers raised an exception',
            event.__class__.__name__,
        )

    async def on_library_error(self, _shard: Shard, payload: raw.ClientEvent, exc: Exception, /) -> None:
        """Handles library errors. By default, this logs exception.

        .. note::
            This won't be called if handling `Ready` will raise a exception as it is fatal.
        """

        type = payload['type']

        _L.exception('%s handler raised an exception', type, exc_info=exc)

    async def _run_callback(
        self, callback: Callable[[EventT], utils.MaybeAwaitable[None]], arg: EventT, name: str, /
    ) -> None:
        try:
            r = callback(arg)
            if isawaitable(r):
                await r
        except Exception:
            try:
                r = self.on_user_error(arg)
                if isawaitable(r):
                    await r
            except Exception:
                _L.exception('on_user_error (task: %s) raised an exception', name)

    async def _dispatch(self, types: list[type[BaseEvent]], event: BaseEvent, name: str, /) -> None:
        event.before_dispatch()
        await event.abefore_dispatch()

        for i, type in enumerate(types):
            handlers, temporary_handlers = self._handlers.get(type, _DEFAULT_HANDLERS)
            if _L.isEnabledFor(logging.DEBUG):
                _L.debug(
                    'Dispatching %s (%i handlers, originating from %s)',
                    type.__name__,
                    len(handlers),
                    event.__class__.__name__,
                )

            remove = None
            for handler in temporary_handlers.values():
                r = handler._handle(event, name)
                if isawaitable(r):
                    r = await r

                if r:
                    remove = handler.id
                    break

            if remove is not None:
                del temporary_handlers[remove]
                break

            for handler in handlers.values():
                r = handler._handle(event, name)
                if isawaitable(r):
                    await r

            event_name: str | None = getattr(type, 'event_name', None)
            if event_name:
                handler = getattr(self, 'on_' + event_name, None)
                if handler:
                    r = self._run_callback(handler, event, name)
                    if isawaitable(r):
                        await r

        handler = getattr(self, 'on_event', None)
        if handler:
            await self._run_callback(handler, event, name)

        if event.is_cancelled:
            _L.debug('%s processing was cancelled', event.__class__.__name__)
        else:
            _L.debug('Processing %s', event.__class__.__name__)
            event.process()
            await event.aprocess()

        hook = getattr(event, 'call_object_handlers_hook', None)
        if not hook:
            return
        try:
            r = hook(self)
            if isawaitable(r):
                await r
        except Exception:
            try:
                r = self.on_user_error(event)
                if isawaitable(r):
                    await r
            except Exception:
                _L.exception('on_user_error (task: %s) raised an exception', name)

    def dispatch(self, event: BaseEvent) -> asyncio.Task[None]:
        """Dispatches a event.

        Parameters
        ----------
        event: :class:`BaseEvent`
            The event to dispatch.

        Returns
        -------
        :class:`asyncio.Task`[None]
            The asyncio task.
        """

        et = builtins.type(event)
        try:
            types = self._types[et]
        except KeyError:
            types = self._types[et] = _parents_of(et)

        name = f'pyvolt-dispatch-{self._get_i()}'
        return asyncio.create_task(self._dispatch(types, event, name), name=name)  # type: ignore

    def subscribe(
        self,
        event: type[EventT],
        callback: utils.MaybeAwaitableFunc[[EventT], None],
    ) -> EventSubscription[EventT]:
        """Subscribes to event.

        Parameters
        ----------
        event: Type[EventT]
            The type of the event.
        callback
            The callback for the event.
        """
        sub: EventSubscription[EventT] = EventSubscription(
            client=self,
            id=self._get_i(),
            callback=callback,
            event=event,
        )

        # The actual generic of value type is same as key
        try:
            self._handlers[event][0][sub.id] = sub  # type: ignore
        except KeyError:
            self._handlers[event] = ({sub.id: sub}, {})  # type: ignore
        return sub

    def on(
        self, event: type[EventT]
    ) -> Callable[
        [utils.MaybeAwaitableFunc[[EventT], None]],
        EventSubscription[EventT],
    ]:
        def decorator(
            handler: utils.MaybeAwaitableFunc[[EventT], None],
        ) -> EventSubscription[EventT]:
            return self.subscribe(event, handler)

        return decorator

    def wait_for(
        self,
        event: type[EventT],
        /,
        *,
        check: Callable[[EventT], bool] | None = None,
        timeout: float | None = None,
    ) -> TemporarySubscription[EventT]:
        """|coro|

        Waits for a WebSocket event to be dispatched.

        This could be used to wait for a user to reply to a message,
        or to react to a message, or to edit a message in a self-contained
        way.

        The ``timeout`` parameter is passed onto :func:`asyncio.wait_for`. By default,
        it does not timeout. Note that this does propagate the
        :exc:`asyncio.TimeoutError` for you in case of timeout and is provided for
        ease of use.

        This function returns the **first event that meets the requirements**.

        Examples
        ---------

        Waiting for a user reply: ::

            @client.on(pyvolt.MessageCreateEvent)
            async def on_message_create(event):
                message = event.message
                if message.content.startswith('$greet'):
                    channel = message.channel
                    await channel.send('Say hello!')

                    def check(event):
                        return event.message.content == 'hello' and event.message.channel.id == channel.id

                    msg = await client.wait_for(pyvolt.MessageCreateEvent, check=check)
                    await channel.send(f'Hello {msg.author}!')

        Waiting for a thumbs up reaction from the message author: ::

            @client.on(pyvolt.MessageCreateEvent)
            async def on_message_create(event):
                message = event.message
                if message.content.startswith('$thumb'):
                    channel = message.channel
                    await channel.send('Send me that \N{THUMBS UP SIGN} reaction, mate')

                    def check(event):
                        return event.user_id == message.author.id and event.emoji == '\N{THUMBS UP SIGN}'

                    try:
                        await client.wait_for(pyvolt.MessageReactEvent, timeout=60.0, check=check)
                    except asyncio.TimeoutError:
                        await channel.send('\N{THUMBS DOWN SIGN}')
                    else:
                        await channel.send('\N{THUMBS UP SIGN}')

        Parameters
        ------------
        event: Type[EventT]
            The event to wait for.
        check: Optional[Callable[[EventT], :class:`bool`]]
            A predicate to check what to wait for.
        timeout: Optional[:class:`float`]
            The number of seconds to wait before timing out and raising
            :exc:`asyncio.TimeoutError`.

        Raises
        -------
        asyncio.TimeoutError
            If a timeout is provided and it was reached.

        Returns
        --------
        :class:`TemporarySubscription`[EventT]
            The subscription. This can be ``await``'ed.
        """

        if not check:
            check = lambda _: True

        future = asyncio.get_running_loop().create_future()

        coro = asyncio.wait_for(future, timeout=timeout)
        sub = TemporarySubscription(
            client=self,
            id=self._get_i(),
            event=event,
            future=future,
            check=check,
            coro=coro,
        )

        try:
            self._handlers[event][1][sub.id] = sub  # type: ignore
        except KeyError:
            self._handlers[event] = ({sub.id: sub}, {})  # type: ignore
        return sub

    @property
    def me(self) -> OwnUser | None:
        """Optional[:class:`OwnUser`]: The currently logged in user. ``None`` if not logged in."""
        return self._state._me

    @property
    def saved_notes(self) -> SavedMessagesChannel | None:
        """Optional[:class:`SavedMessagesChannel`]: The Saved Notes channel."""
        return self._state._saved_notes

    @property
    def http(self) -> HTTPClient:
        """:class:`HTTPClient`: The HTTP client."""
        return self._state.http

    @property
    def shard(self) -> Shard:
        """:class:`Shard`: The Revolt WebSocket client."""
        return self._state.shard

    @property
    def state(self) -> State:
        """:class:`State`: The controller for all entities and components."""
        return self._state

    @property
    def channels(self) -> Mapping[str, Channel]:
        """Mapping[:class:`str`, :class:`Channel`]: Mapping of cached channels."""
        cache = self._state.cache
        if cache:
            return cache.get_channels_mapping()
        return {}

    @property
    def emojis(self) -> Mapping[str, Emoji]:
        """Mapping[:class:`str`, :class:`Emoji`]: Mapping of cached emojis."""
        cache = self._state.cache
        if cache:
            return cache.get_emojis_mapping()
        return {}

    @property
    def servers(self) -> Mapping[str, Server]:
        """Mapping[:class:`str`, :class:`Server`]: Mapping of cached servers."""
        cache = self._state.cache
        if cache:
            return cache.get_servers_mapping()
        return {}

    @property
    def users(self) -> Mapping[str, User]:
        """Mapping[:class:`str`, :class:`User`]: Mapping of cached users."""
        cache = self._state.cache
        if cache:
            return cache.get_users_mapping()
        return {}

    @property
    def dm_channel_ids(self) -> Mapping[str, str]:
        """Mapping[:class:`str`, :class:`str`]: Mapping of user IDs to cached DM channel IDs."""
        cache = self._state.cache
        if cache:
            return cache.get_private_channels_by_users_mapping()
        return {}

    @property
    def dm_channels(self) -> Mapping[str, DMChannel]:
        """Mapping[:class:`str`, :class:`DMChannel`]: Mapping of user IDs to cached DM channels."""

        cache = self._state.cache
        if not cache:
            return {}

        result: dict[str, DMChannel] = {}
        for k, v in self.dm_channel_ids.items():
            channel = cache.get_channel(v, caching._USER_REQUEST)
            if channel and isinstance(channel, DMChannel):
                result[k] = channel
        return result

    @property
    def private_channels(self) -> Mapping[str, DMChannel | GroupChannel]:
        """Mapping[:class:`str`, Union[:class:`DMChannel`, :class:`GroupChannel`]]: Mapping of channel IDs to private channels.
        Useful when developing Revolt client."""
        cache = self._state.cache
        if not cache:
            return {}
        return cache.get_private_channels_mapping()

    @property
    def ordered_private_channels_old(self) -> list[DMChannel | GroupChannel]:
        """List[Union[:class:`DMChannel`, :class:`GroupChannel`]]: The list of private channels in Revite order.
        Useful when developing Revolt client."""
        return sorted(self.private_channels.values(), key=_private_channel_sort_old, reverse=True)

    @property
    def ordered_private_channels(self) -> list[DMChannel | GroupChannel]:
        """List[Union[:class:`DMChannel`, :class:`GroupChannel`]]: The list of private channels in new client's order.
        Useful when developing Revolt client."""
        return sorted(self.private_channels.values(), key=_private_channel_sort_new, reverse=True)

    def get_channel(self, channel_id: str, /) -> Channel | None:
        """Retrieves a channel from cache.

        Parameters
        ----------
        channel_id: :class:`str`
            The channel ID.

        Returns
        -------
        Optional[:class:`Channel`]
            The channel or ``None`` if not found.
        """
        cache = self._state.cache
        if cache:
            return cache.get_channel(channel_id, caching._USER_REQUEST)

    async def fetch_channel(self, channel_id: str, /) -> Channel:
        """|coro|

        Retrieves a channel from API. This is shortcut to :meth:`HTTPClient.get_channel`.

        Parameters
        ----------
        channel_id: :class:`str`
            The channel ID.

        Returns
        -------
        :class:`Channel`
            The retrieved channel.
        """
        return await self.http.get_channel(channel_id)

    def get_emoji(self, emoji_id: str, /) -> Emoji | None:
        """Retrieves a emoji from cache.

        Parameters
        ----------
        emoji_id: :class:`str`
            The emoji ID.

        Returns
        -------
        Optional[:class:`Emoji`]
            The emoji or ``None`` if not found.
        """
        cache = self._state.cache
        if cache:
            return cache.get_emoji(emoji_id, caching._USER_REQUEST)

    async def fetch_emoji(self, emoji_id: str, /) -> Emoji:
        """|coro|

        Retrieves a emoji from API. This is shortcut to :meth:`HTTPClient.get_emoji`.

        Parameters
        ----------
        emoji_id: :class:`str`
            The emoji ID.

        Returns
        -------
        :class:`Emoji`
            The retrieved emoji.
        """
        return await self.http.get_emoji(emoji_id)

    def get_read_state(self, channel_id: str, /) -> ReadState | None:
        """Retrieves a read state from cache.

        Parameters
        ----------
        channel_id: :class:`str`
            The channel ID of read state.

        Returns
        -------
        Optional[:class:`ReadState`]
            The read state or ``None`` if not found.
        """
        cache = self._state.cache
        if cache:
            return cache.get_read_state(channel_id, caching._USER_REQUEST)

    def get_server(self, server_id: str, /) -> Server | None:
        """Retrieves a server from cache.

        Parameters
        ----------
        server_id: :class:`str`
            The server ID.

        Returns
        -------
        Optional[:class:`Server`]
            The server or ``None`` if not found.
        """
        cache = self._state.cache
        if cache:
            return cache.get_server(server_id, caching._USER_REQUEST)

    async def fetch_server(self, server_id: str, /) -> Server:
        """|coro|

        Retrieves a server from API. This is shortcut to :meth:`HTTPClient.get_server`.

        Parameters
        ----------
        server_id: :class:`str`
            The server ID.

        Returns
        -------
        :class:`Server`
            The server.
        """
        return await self.http.get_server(server_id)

    def get_user(self, user_id: str, /) -> User | None:
        """Retrieves a user from cache.

        Parameters
        ----------
        user_id: :class:`str`
            The user ID.

        Returns
        -------
        Optional[:class:`User`]
            The user or ``None`` if not found.
        """
        cache = self._state.cache
        if cache:
            return cache.get_user(user_id, caching._USER_REQUEST)

    async def fetch_user(self, user_id: str, /) -> User:
        """|coro|

        Retrieves a user from API. This is shortcut to :meth:`HTTPClient.get_user`.

        Parameters
        ----------
        user_id: :class:`str`
            The user ID.

        Returns
        -------
        :class:`User`
            The user.
        """
        return await self.http.get_user(user_id)

    @property
    def settings(self) -> UserSettings:
        """:class:`UserSettings`: The current user settings."""
        return self._state.settings

    @property
    def system(self) -> User:
        """:class:`User`: The Revolt sentinel user."""
        return self._state.system

    async def start(self) -> None:
        """|coro|

        Starts up the client.
        """
        self.closed = False
        await self._state.shard.connect()

    async def close(self, *, http: bool = True, cleanup_websocket: bool = True) -> None:
        """|coro|

        Closes all HTTP sessions, and websocket connections.
        """

        self.closed = True

        await self.shard.close()
        if cleanup_websocket:
            await self.shard.cleanup()

        if http:
            await self.http.cleanup()

    def run(
        self,
        token: str = '',
        *,
        bot: UndefinedOr[bool] = UNDEFINED,
        log_handler: UndefinedOr[logging.Handler | None] = UNDEFINED,
        log_formatter: UndefinedOr[logging.Formatter] = UNDEFINED,
        log_level: UndefinedOr[int] = UNDEFINED,
        root_logger: bool = False,
        asyncio_debug: bool = False,
        cleanup: bool = True,
    ) -> None:
        """A blocking call that abstracts away the event loop
        initialisation from you.

        If you want more control over the event loop then this
        function should not be used. Use :meth:`.start` coroutine.

        This function also sets up the logging library to make it easier
        for beginners to know what is going on with the library. For more
        advanced users, this can be disabled by passing ``None`` to
        the ``log_handler`` parameter.

        .. warning::

            This function must be the last function to call due to the fact that it
            is blocking. That means that registration of events or anything being
            called after this function call will not execute until it returns.

        Parameters
        -----------
        log_handler: Optional[:class:`logging.Handler`]
            The log handler to use for the library's logger. If this is ``None``
            then the library will not set up anything logging related. Logging
            will still work if ``None`` is passed, though it is your responsibility
            to set it up.

            The default log handler if not provided is :class:`logging.StreamHandler`.
        log_formatter: :class:`logging.Formatter`
            The formatter to use with the given log handler. If not provided then it
            defaults to a colour based logging formatter (if available).
        log_level: :class:`int`
            The default log level for the library's logger. This is only applied if the
            ``log_handler`` parameter is not ``None``. Defaults to ``logging.INFO``.
        root_logger: :class:`bool`
            Whether to set up the root logger rather than the library logger.
            By default, only the library logger (``'pyvolt'``) is set up. If this
            is set to ``True`` then the root logger is set up as well.

            Defaults to ``False``.
        asyncio_debug: :class:`bool`
            Whether to run with asyncio debug mode enabled or not.

            Defaults to ``False``.
        cleanup: :class:`bool`
            Whether to close aiohttp sessions or not.

            Defaults to ``True``.
        """

        if token:
            bot = self.bot if bot is UNDEFINED else bot

            self.http.with_credentials(token, bot=bot)
            self.shard.with_credentials(token, bot=bot)
        elif not self._token:
            raise TypeError('No token was provided')

        async def runner():
            await self.start()
            if cleanup and not self.closed:
                await self.close()
            self.closed = True

        if log_handler is not None:
            utils.setup_logging(
                handler=log_handler,
                formatter=log_formatter,
                level=log_level,
                root=root_logger,
            )

        try:
            asyncio.run(runner(), debug=asyncio_debug)
        except KeyboardInterrupt:
            # nothing to do here
            # `asyncio.run` handles the loop cleanup
            # NOTE: not true
            # > and `self.start` closes all sockets and the HTTPClient instance.
            return

    if typing.TYPE_CHECKING:

        def on_event(self, arg: BaseEvent, /) -> utils.MaybeAwaitable[None]: ...

        def on_authenticated(self, arg: AuthenticatedEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_authifier(self, arg: AuthifierEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_channel_create(self, arg: BaseChannelCreateEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_bulk_message_delete(self, arg: BulkMessageDeleteEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_channel_delete(self, arg: ChannelDeleteEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_channel_start_typing(self, arg: ChannelStartTypingEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_channel_stop_typing(self, arg: ChannelStopTypingEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_channel_update(self, arg: ChannelUpdateEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_recipient_add(self, arg: GroupRecipientAddEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_recipient_remove(self, arg: GroupRecipientRemoveEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_logout(self, arg: LogoutEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_message_ack(self, arg: MessageAckEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_message_append(self, arg: MessageAppendEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_message_clear_reaction(self, arg: MessageClearReactionEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_message_create(self, arg: MessageCreateEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_message_delete(self, arg: MessageDeleteEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_message_react(self, arg: MessageReactEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_message_unreact(self, arg: MessageUnreactEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_message_update(self, arg: MessageUpdateEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_message(self, arg: Message, /) -> utils.MaybeAwaitable[None]: ...
        def on_private_channel_create(self, arg: PrivateChannelCreateEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_raw_server_role_update(self, arg: RawServerRoleUpdateEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_ready(self, arg: ReadyEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_server_channel_create(self, arg: ServerChannelCreateEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_server_create(self, arg: ServerCreateEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_server_delete(self, arg: ServerDeleteEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_server_emoji_create(self, arg: ServerEmojiCreateEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_server_emoji_delete(self, arg: ServerEmojiDeleteEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_server_member_join(self, arg: ServerMemberJoinEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_server_member_remove(self, arg: ServerMemberRemoveEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_server_member_update(self, arg: ServerMemberUpdateEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_server_role_delete(self, arg: ServerRoleDeleteEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_server_update(self, arg: ServerUpdateEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_session_create(self, arg: SessionCreateEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_session_delete_all(self, arg: SessionDeleteAllEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_session_delete(self, arg: SessionDeleteEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_user_platform_wipe(self, arg: UserPlatformWipeEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_user_relationship_update(self, arg: UserRelationshipUpdateEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_user_settings_update(self, arg: UserSettingsUpdateEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_user_update(self, arg: UserUpdateEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_webhook_create(self, arg: WebhookCreateEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_webhook_delete(self, arg: WebhookDeleteEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_webhook_update(self, arg: WebhookUpdateEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_before_connect(self, arg: BeforeConnectEvent, /) -> utils.MaybeAwaitable[None]: ...
        def on_after_connect(self, arg: AfterConnectEvent, /) -> utils.MaybeAwaitable[None]: ...

    async def create_group(
        self,
        name: str,
        *,
        description: str | None = None,
        recipients: list[ULIDOr[BaseUser]] | None = None,
        nsfw: bool | None = None,
    ) -> GroupChannel:
        """|coro|

        Creates the new group channel.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        name: :class:`str`
            The group name.
        description: Optional[:class:`str`]
            The group description.
        recipients: Optional[List[:class:`ULIDOr`[:class:`BaseUser`]]]
            The list of recipients to add to the group. You must be friends with these users.
        nsfw: Optional[:class:`bool`]
            Whether this group should be age-restricted.

        Raises
        ------
        HTTPException
            Creating the group failed.

        Returns
        -------
        :class:`GroupChannel`
            The new group.
        """
        return await self.http.create_group(name, description=description, recipients=recipients, nsfw=nsfw)

    async def create_server(self, name: str, /, *, description: str | None = None, nsfw: bool | None = None) -> Server:
        """|coro|

        Create a new server.

        Parameters
        ----------
        name: :class:`str`
            The server name.
        description: Optional[:class:`str`]
            The server description.
        nsfw: Optional[:class:`bool`]
            Whether this server is age-restricted.

        Returns
        -------
        :class:`Server`
            The created server.
        """
        return await self.http.create_server(name, description=description, nsfw=nsfw)


__all__ = (
    'EventSubscription',
    'TemporarySubscription',
    'ClientEventHandler',
    '_private_channel_sort_old',
    '_private_channel_sort_new',
    'Client',
)
