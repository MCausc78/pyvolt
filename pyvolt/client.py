from __future__ import annotations

import aiohttp
import asyncio
import builtins
from collections import abc as ca
import inspect
from functools import wraps
import logging
import sys
import typing

from . import cache as caching, utils
from .cache import Cache, MapCache
from .cdn import CDNClient
from .channel import SavedMessagesChannel, GroupChannel, Channel
from .core import (
    UNDEFINED,
    UndefinedOr,
    is_defined,
    ULIDOr,
)
from .emoji import Emoji
from .events import BaseEvent, MessageCreateEvent
from .http import HTTPClient
from .message import Message
from .parser import Parser
from .read_state import ReadState
from .server import Server
from .shard import EventHandler, Shard
from .state import State
from .user_settings import UserSettings
from .user import BaseUser, User, SelfUser


if typing.TYPE_CHECKING:
    from . import raw


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
        event = self._state.parser.parse_server_create_event(shard, payload)
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

    async def _handle(self, shard: Shard, payload: raw.ClientEvent, /) -> None:
        type = payload['type']
        try:
            handler = self._handlers[type]
        except KeyError:
            _L.debug('Received unknown event: %s. Discarding.', type)
        else:
            _L.debug('Handling %s', type)
            try:
                await utils._maybe_coroutine(handler, shard, payload)
            except Exception as exc:
                _L.exception('%s handler raised an exception', type, exc_info=exc)

    async def handle_raw(self, shard: Shard, d: raw.ClientEvent) -> None:
        return await self._handle(shard, d)


# OOP in Python sucks.
ClientT = typing.TypeVar('ClientT', bound='Client')
EventT = typing.TypeVar('EventT', bound='BaseEvent')


def _parents_of(type: type[BaseEvent]) -> tuple[type[BaseEvent], ...]:
    """Returns parents of BaseEvent, including BaseEvent itself."""
    if type is BaseEvent:
        return (BaseEvent,)
    tmp: typing.Any = type.__mro__[:-1]
    return tmp


EventToModel = Message
_COMMON_CONVERTERS: dict[type[EventToModel], ca.Callable] = {
    Message: (lambda callback: (MessageCreateEvent, lambda event: callback(event.message)))
}


class Client:
    """A Revolt client."""

    __slots__ = ('_handlers', '_types', '_i', '_state', 'extra')

    @typing.overload
    def __init__(
        self,
        *,
        token: str,
        bot: bool = True,
        state: ca.Callable[[Client], State] | State | None = None,
    ) -> None: ...

    @typing.overload
    def __init__(
        self,
        *,
        token: str,
        bot: bool = True,
        cache: ca.Callable[[Client, State], UndefinedOr[Cache | None]] | None = None,
        cdn_base: str | None = None,
        cdn_client: ca.Callable[[Client, State], CDNClient] | None = None,
        http_base: str | None = None,
        http: ca.Callable[[Client, State], HTTPClient] | None = None,
        parser: ca.Callable[[Client, State], Parser] | None = None,
        shard: ca.Callable[[Client, State], Shard] | None = None,
        websocket_base: str | None = None,
    ) -> None: ...

    def __init__(
        self,
        *,
        token: str,
        bot: bool = True,
        cache: (ca.Callable[[Client, State], UndefinedOr[Cache | None]] | UndefinedOr[Cache | None]) = UNDEFINED,
        cdn_base: str | None = None,
        cdn_client: ca.Callable[[Client, State], CDNClient] | None = None,
        http_base: str | None = None,
        http: ca.Callable[[Client, State], HTTPClient] | None = None,
        parser: ca.Callable[[Client, State], Parser] | None = None,
        shard: ca.Callable[[Client, State], Shard] | None = None,
        websocket_base: str | None = None,
        state: ca.Callable[[Client], State] | State | None = None,
    ) -> None:
        # {Type[BaseEvent]: List[utils.MaybeAwaitableFunc[[BaseEvent], None]]}
        self._handlers: dict[
            type[BaseEvent],
            list[utils.MaybeAwaitableFunc[[BaseEvent], None]],
        ] = {}
        # {Type[BaseEvent]: Tuple[Type[BaseEvent], ...]}
        self._types: dict[type[BaseEvent], tuple[type[BaseEvent], ...]] = {}
        self._i = 0

        self.extra = {}
        if state:
            if callable(state):
                self._state = state(self)
            else:
                self._state = state
        else:  # elif any(x is not None for x in (cache, cdn_client, http, parser, shard)):
            state = State()

            c = None
            if callable(cache):
                cr = cache(self, state)
            else:
                cr = cache
            c = cr if is_defined(cr) else MapCache()

            state.setup(
                cache=c,
                cdn_client=(
                    cdn_client(self, state) if cdn_client else CDNClient(state, session=_session_factory, base=cdn_base)
                ),
                http=(
                    http(self, state)
                    if http
                    else HTTPClient(
                        token,
                        base=http_base,
                        bot=bot,
                        state=state,
                        session=_session_factory,
                    )
                ),
                parser=parser(self, state) if parser else Parser(state),
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
                        session=_session_factory,
                        state=state,
                    )
                )
            )
        self._subscribe_methods()

    def _get_i(self) -> int:
        self._i += 1
        return self._i

    async def on_error(self, event: BaseEvent) -> None:
        _, exc, _ = sys.exc_info()
        _L.exception(
            'one of %s handlers raised an exception',
            event.__class__.__name__,
            exc_info=exc,
        )

    async def _dispatch(
        self,
        handlers: list[utils.MaybeAwaitableFunc[[EventT], None]],
        event: EventT,
        name: str,
        first: bool,
        /,
    ) -> None:
        if first:
            event.before_dispatch()
            await event.abefore_dispatch()

        for handler in handlers:
            try:
                await utils._maybe_coroutine(handler, event)
            except Exception:
                try:
                    await utils._maybe_coroutine(self.on_error, event)
                except Exception as exc:
                    _L.exception('on_error (task: %s) raised an exception', name, exc_info=exc)
        # Prevent double-processing
        if first:
            if not event.is_cancelled:
                _L.debug('Processing %s', event.__class__.__name__)

                event.process()
                await event.aprocess()
            else:
                _L.debug('%s processing was cancelled', event.__class__.__name__)

    def dispatch(self, event: BaseEvent) -> None:
        """Dispatches a event."""

        et = builtins.type(event)
        try:
            types = self._types[et]
        except KeyError:
            types = self._types[et] = _parents_of(et)

        for i, type in enumerate(types):
            handlers = self._handlers.get(type, [])
            if _L.isEnabledFor(logging.DEBUG):
                _L.debug(
                    'Dispatching %s (%i handlers, originating from %s)',
                    type.__name__,
                    len(handlers),
                    event.__class__.__name__,
                )

            name = name = f'pyvolt-dispatch-{self._get_i()}'
            asyncio.create_task(self._dispatch(handlers, event, name, i == 0), name=name)

    def subscribe(
        self,
        event: type[EventT | EventToModel],
        callback: utils.MaybeAwaitableFunc[[EventT], None],
    ) -> None:
        """Subscribes to event."""
        ev: typing.Any = event
        try:
            ev, converter = _COMMON_CONVERTERS[event](callback)  # type: ignore
            tmp: typing.Any = converter
        except KeyError:
            tmp: typing.Any = callback

        try:
            self._handlers[ev].append(tmp)
        except KeyError:
            self._handlers[ev] = [tmp]

    def on(
        self, event: type[EventT | EventToModel]
    ) -> ca.Callable[
        [utils.MaybeAwaitableFunc[[EventT], None]],
        utils.MaybeAwaitableFunc[[EventT], None],
    ]:
        def decorator(
            handler: utils.MaybeAwaitableFunc[[EventT], None],
        ) -> utils.MaybeAwaitableFunc[[EventT], None]:
            self.subscribe(event, handler)
            return handler

        return decorator

    @staticmethod
    def listens_on(
        event: type[EventT | EventToModel],
    ) -> ca.Callable[
        [utils.MaybeAwaitableFunc[[ClientT, EventT], None]],
        utils.MaybeAwaitableFunc[[ClientT, EventT], None],
    ]:
        def decorator(
            handler: utils.MaybeAwaitableFunc[[ClientT, EventT], None],
        ) -> utils.MaybeAwaitableFunc[[ClientT, EventT], None]:
            @wraps(handler)
            def callback(*args, **kwargs) -> utils.MaybeAwaitable[None]:
                return handler(*args, **kwargs)

            callback.__pyvolt_handles__ = event  # type: ignore
            return callback

        return decorator

    def _subscribe_methods(self) -> None:
        for _, callback in inspect.getmembers(self, lambda func: hasattr(func, '__pyvolt_handles__')):
            self.subscribe(callback.__pyvolt_handles__, callback)

    @property
    def me(self) -> SelfUser | None:
        """:class:`SelfUser` | None: The currently logged in user. ``None`` if not logged in."""
        return self._state._me

    @property
    def saved_notes(self) -> SavedMessagesChannel | None:
        """:class:`SavedMessagesChannel` | None: The Saved Notes channel."""
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
        """:class:`State`: The controller for all entities and managers."""
        return self._state

    @property
    def channels(self) -> ca.Mapping[str, Channel]:
        """:class:`ca.Mapping`[:class:`str`, :class:`Channel`]: Retrieves all cached channels."""
        cache = self._state.cache
        if cache:
            return cache.get_channels_mapping()
        return {}

    @property
    def emojis(self) -> ca.Mapping[str, Emoji]:
        """:class:`ca.Mapping`[:class:`str`, :class:`Emoji`]: Retrieves all cached emojis."""
        cache = self._state.cache
        if cache:
            return cache.get_emojis_mapping()
        return {}

    @property
    def servers(self) -> ca.Mapping[str, Server]:
        """:class:`ca.Mapping`[:class:`str`, :class:`Server`]: Retrieves all cached servers."""
        cache = self._state.cache
        if cache:
            return cache.get_servers_mapping()
        return {}

    @property
    def users(self) -> ca.Mapping[str, User]:
        """:class:`ca.Mapping`[:class:`str`, :class:`User`]: Retrieves all cached users."""
        cache = self._state.cache
        if cache:
            return cache.get_users_mapping()
        return {}

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
        await self._state.shard.connect()

    async def close(self) -> None:
        """|coro|

        Closes all HTTP sessions, and websocket connections.
        """
        try:
            await self._state.shard.close()
        except:
            pass

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
    'ClientEventHandler',
    'Client',
)
