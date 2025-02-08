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
import asyncio
from datetime import datetime, timedelta
from inspect import isawaitable
import logging
import typing

import aiohttp
from multidict import CIMultiDict

from . import routes, utils
from .authentication import (
    PartialAccount,
    MFATicket,
    PartialSession,
    Session,
    MFAMethod,
    MFARequired,
    AccountDisabled,
    MFAStatus,
    MFAResponse,
    LoginResult,
)
from .channel import (
    BaseChannel,
    TextChannel,
    SavedMessagesChannel,
    DMChannel,
    GroupChannel,
    VoiceChannel,
    ServerChannel,
    Channel,
)
from .cdn import ResolvableResource, resolve_resource
from .core import (
    UNDEFINED,
    UndefinedOr,
    ULIDOr,
    resolve_id,
    __version__ as version,
)
from .emoji import BaseEmoji, ServerEmoji, Emoji, ResolvableEmoji, resolve_emoji
from .errors import (
    HTTPException,
    Unauthorized,
    Forbidden,
    NotFound,
    Conflict,
    Ratelimited,
    InternalServerError,
    BadGateway,
)
from .flags import MessageFlags, Permissions, ServerFlags, UserBadges, UserFlags
from .invite import BaseInvite, PublicInvite, ServerInvite, Invite
from .message import (
    Reply,
    MessageInteractions,
    Masquerade,
    SendableEmbed,
    BaseMessage,
    Message,
)
from .permissions import PermissionOverride
from .server import (
    Category,
    SystemMessageChannels,
    BaseRole,
    Role,
    BaseServer,
    Server,
    Ban,
    BaseMember,
    Member,
    MemberList,
)


if typing.TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from . import raw
    from .bot import BaseBot, Bot, PublicBot
    from .channel import TextableChannel
    from .enums import ChannelType, MessageSort, ContentReportReason, UserReportReason
    from .instance import Instance
    from .read_state import ReadState
    from .settings import UserSettings
    from .state import State
    from .user import (
        UserStatusEdit,
        UserProfile,
        UserProfileEdit,
        Mutuals,
        BaseUser,
        User,
        OwnUser,
    )
    from .webhook import BaseWebhook, Webhook


DEFAULT_HTTP_USER_AGENT = f'pyvolt (https://github.com/MCausc78/pyvolt, {version})'


_L = logging.getLogger(__name__)
_STATUS_TO_ERRORS = {
    401: Unauthorized,
    403: Forbidden,
    404: NotFound,
    409: Conflict,
    429: Ratelimited,
    500: InternalServerError,
}


class RateLimit(ABC):
    __slots__ = ()

    bucket: str
    remaining: int

    @abstractmethod
    async def block(self) -> None:
        """If necessary, this method must calculate delay and sleep."""
        ...

    @abstractmethod
    def is_expired(self) -> bool:
        """:class:`bool`: Whether the ratelimit is expired."""
        ...

    @abstractmethod
    def on_response(self, route: routes.CompiledRoute, response: aiohttp.ClientResponse, /) -> None:
        """Called when any response from Revolt API is received.

        This has same note as :meth:`RateLimiter.on_response`.

        This is called only if bucket was already present and ratelimiter wants
        to resync data.
        """
        ...


class RateLimitBlocker(ABC):
    __slots__ = ()

    async def increment(self) -> None:
        """Increments pending requests counter."""
        pass

    async def decrement(self) -> None:
        """Decrements pending requests counter."""
        pass


class RateLimiter(ABC):
    __slots__ = ()

    @abstractmethod
    def fetch_ratelimit_for(self, route: routes.CompiledRoute, path: str, /) -> typing.Optional[RateLimit]:
        """Optional[:class:`.RateLimit`]: Must return ratelimit information, if available."""
        ...

    @abstractmethod
    def fetch_blocker_for(self, route: routes.CompiledRoute, path: str, /) -> RateLimitBlocker:
        """:class:`.RateLimitBlocker`: Returns request blocker."""
        ...

    @abstractmethod
    async def on_response(self, route: routes.CompiledRoute, path: str, response: aiohttp.ClientResponse, /) -> None:
        """Called when any response from Revolt API is received.

        .. note::
            This is always called, even when request fails for other reasons like failed validation,
            invalid token, something not found, etc.
        """
        ...

    @abstractmethod
    def on_bucket_update(
        self, response: aiohttp.ClientResponse, route: routes.CompiledRoute, old_bucket: str, new_bucket: str, /
    ) -> None:
        """Called when route updates their bucket key.

        The :meth:`default implementation <DefaultRateLimiter.on_bucket_update>` will remove old
        bucket from internal mapping.

        Parameters
        ----------
        response: :class:`aiohttp.ClientResponse`
            The response.
        route: :class:`~routes.CompiledRoute`
            The route.
        old_bucket: :class:`str`
            The old bucket key.
        new_bucket: :class:`str`
            The new bucket key.
        """
        ...


class DefaultRateLimit(RateLimit):
    __slots__ = (
        '_rate_limiter',
        'bucket',
        'remaining',
        '_expires_at',
    )

    def __init__(self, rate_limiter: RateLimiter, bucket: str, /, *, remaining: int, reset_after: int) -> None:
        self._rate_limiter: RateLimiter = rate_limiter
        self.bucket: str = bucket
        self.remaining: int = remaining
        self._expires_at: datetime = utils.utcnow() + timedelta(milliseconds=reset_after)

    @utils.copy_doc(RateLimit.block)
    async def block(self) -> None:
        self.remaining -= 1
        if self.remaining <= 0:
            now = utils.utcnow()

            delay = (self._expires_at - now).total_seconds()
            if delay > 0:
                _L.info('Bucket %s is ratelimited locally for %.4f; sleeping', self.bucket, delay)
                await asyncio.sleep(delay)
            else:
                _L.debug('Bucket %s expired.', self.bucket)
                # Nothing to do here ┬─┬ノ( º _ ºノ)
                # The ratelimit expired. No 429 :)

    @utils.copy_doc(RateLimit.is_expired)
    def is_expired(self) -> bool:
        """:class:`bool`: Whether the ratelimit is expired."""
        return (self._expires_at - utils.utcnow()).total_seconds() <= 0

    @utils.copy_doc(RateLimit.on_response)
    def on_response(self, route: routes.CompiledRoute, response: aiohttp.ClientResponse, /) -> None:
        headers = response.headers
        bucket = headers['x-ratelimit-bucket']
        if self.bucket != bucket:
            _L.warning('%s changed ratelimit bucket key: %s -> %s.', response.url, self.bucket, bucket)
            self._rate_limiter.on_bucket_update(response, route, self.bucket, bucket)
            self.bucket = bucket

        # (bucket, limit, remaining, reset-after)
        self.remaining = int(headers['x-ratelimit-remaining'])
        self._expires_at = utils.utcnow() + timedelta(milliseconds=int(headers['x-ratelimit-reset-after']))


class DefaultRateLimitBlocker(RateLimitBlocker):
    __slots__ = ('_lock',)

    def __init__(self) -> None:
        self._lock: asyncio.Lock = asyncio.Lock()

    @utils.copy_doc(RateLimitBlocker.increment)
    async def increment(self) -> None:
        await self._lock.acquire()

    @utils.copy_doc(RateLimitBlocker.decrement)
    async def decrement(self) -> None:
        self._lock.release()


class _NoopRateLimitBlocker(RateLimitBlocker):
    __slots__ = ()

    def __init__(self) -> None:
        pass

    async def increment(self) -> None:
        pass

    async def decrement(self) -> None:
        pass


class DefaultRateLimiter(RateLimiter):
    __slots__ = (
        '_no_concurrent_block',
        '_no_expired_ratelimit_remove',
        '_noop_blocker',
        '_pending_requests',
        '_ratelimits',
        '_routes_to_bucket',
    )

    def __init__(
        self,
        *,
        no_concurrent_block: bool = False,
        no_expired_ratelimit_remove: bool = False,
    ) -> None:
        self._no_concurrent_block: bool = no_concurrent_block
        self._no_expired_ratelimit_remove: bool = no_expired_ratelimit_remove
        self._noop_blocker: RateLimitBlocker = _NoopRateLimitBlocker()
        self._pending_requests: dict[str, RateLimitBlocker] = {}
        self._ratelimits: dict[str, RateLimit] = {}
        self._routes_to_bucket: dict[str, str] = {}

    def get_ratelimit_key_for(self, route: routes.CompiledRoute, /) -> str:
        """Gets ratelimit key for this compiled route.

        By default this just calls :meth:`routes.CompiledRoute.build_ratelimit_key`.

        Parameters
        ----------
        route: :class:`~routes.CompiledRoute`
            The route to fetch ratelimit key for.

        Returns
        -------
        :class:`str`
            The ratelimit key.
        """
        return route.build_ratelimit_key()

    @utils.copy_doc(RateLimiter.fetch_ratelimit_for)
    def fetch_ratelimit_for(self, route: routes.CompiledRoute, path: str, /) -> typing.Optional[RateLimit]:
        if not self._no_expired_ratelimit_remove:
            self.try_remove_expired_ratelimits()

        key = self.get_ratelimit_key_for(route)
        try:
            bucket = self._routes_to_bucket[key]
        except KeyError:
            return None
        else:
            return self._ratelimits[bucket]

    @utils.copy_doc(RateLimiter.fetch_blocker_for)
    def fetch_blocker_for(self, route: routes.CompiledRoute, path: str, /) -> RateLimitBlocker:
        if self._no_concurrent_block:
            return self._noop_blocker

        key = self.get_ratelimit_key_for(route)
        try:
            return self._pending_requests[key]
        except KeyError:
            blocker = DefaultRateLimitBlocker()
            self._pending_requests[key] = blocker
            return blocker

    @utils.copy_doc(RateLimiter.on_response)
    async def on_response(self, route: routes.CompiledRoute, path: str, response: aiohttp.ClientResponse, /) -> None:
        headers = response.headers

        try:
            bucket = headers['x-ratelimit-bucket']
        except KeyError:
            # Thanks Cloudflare
            return

        remaining = int(headers['x-ratelimit-remaining'])
        reset_after = int(headers['x-ratelimit-reset-after'])

        try:
            ratelimit = self._ratelimits[bucket]
        except KeyError:
            _L.debug('%s %s found initial bucket key: %s.', route.route.method, path, bucket)

            ratelimit = DefaultRateLimit(
                self,
                bucket,
                remaining=remaining,
                reset_after=reset_after,
            )
            self._ratelimits[ratelimit.bucket] = ratelimit
            self._routes_to_bucket[self.get_ratelimit_key_for(route)] = bucket
        else:
            ratelimit.on_response(route, response)

    @utils.copy_doc(RateLimiter.on_bucket_update)
    def on_bucket_update(
        self, response: aiohttp.ClientResponse, route: routes.CompiledRoute, old_bucket: str, new_bucket: str, /
    ) -> None:
        self._ratelimits[new_bucket] = self._ratelimits.pop(old_bucket)
        self._routes_to_bucket[self.get_ratelimit_key_for(route)] = new_bucket

    def try_remove_expired_ratelimits(self) -> None:
        """Tries to remove expired ratelimits."""
        if not len(self._ratelimits) or not len(self._routes_to_bucket):
            return

        buckets = []

        ratelimits = self._ratelimits
        for s in ratelimits.values():
            if s.is_expired():
                buckets.append(s.bucket)

        if not buckets:
            return

        for bucket in buckets:
            ratelimits.pop(bucket, None)

        keys = [k for k, v in self._routes_to_bucket.items() if v in buckets or v not in ratelimits]
        for key in keys:
            del self._routes_to_bucket[key]


def _resolve_member_id(target: typing.Union[str, BaseUser, BaseMember], /) -> str:
    ret: str = getattr(target, 'id', target)  # type: ignore
    return ret


class HTTPClient:
    """Represents an HTTP client sending HTTP requests to the Revolt API.

    Attributes
    ----------
    bot: :class:`bool`
        Whether the token belongs to bot account.
    cookie: :class:`str`
        The cookie used to make requests. If ``cf_clearance`` cookie is present, then it's used to prevent HTML pages when service is down.
    max_retries: :class:`int`
        How many times to retry requests that received 429 or 502 HTTP status code.
    rate_limiter: Optional[:class:`RateLimiter`]
        The rate limiter in use.
    state: :class:`State`
        The state.
    token: :class:`str`
        The token in use. May be empty if not started.
    user_agent: :class:`str`
        The HTTP user agent used when making requests.
    """

    # To prevent unexpected 200's with HTML page the user must pass cookie with ``cf_clearance`` key.

    __slots__ = (
        '_base',
        '_session',
        'bot',
        'cookie',
        'max_retries',
        'rate_limiter',
        'state',
        'token',
        'user_agent',
    )

    def __init__(
        self,
        token: typing.Optional[str] = None,
        *,
        base: typing.Optional[str] = None,
        bot: bool = True,
        cookie: typing.Optional[str] = None,
        max_retries: typing.Optional[int] = None,
        rate_limiter: UndefinedOr[
            typing.Optional[typing.Union[Callable[[HTTPClient], typing.Optional[RateLimiter]], RateLimiter]]
        ] = UNDEFINED,
        state: State,
        session: typing.Union[utils.MaybeAwaitableFunc[[HTTPClient], aiohttp.ClientSession], aiohttp.ClientSession],
        user_agent: typing.Optional[str] = None,
    ) -> None:
        if base is None:
            base = 'https://api.revolt.chat/0.8'
        self._base: str = base.rstrip('/')
        self.bot: bool = bot
        self._session: typing.Union[
            utils.MaybeAwaitableFunc[[HTTPClient], aiohttp.ClientSession], aiohttp.ClientSession
        ] = session
        self.cookie: typing.Optional[str] = cookie
        self.max_retries: int = max_retries or 3

        if rate_limiter is UNDEFINED:
            self.rate_limiter: typing.Optional[RateLimiter] = DefaultRateLimiter()
        elif callable(rate_limiter):
            self.rate_limiter = rate_limiter(self)
        else:
            self.rate_limiter = rate_limiter

        self.state: State = state
        self.token: str = token or ''
        self.user_agent: str = user_agent or DEFAULT_HTTP_USER_AGENT

    @property
    def base(self) -> str:
        """:class:`str`: The base URL used for API requests."""
        return self._base

    def url_for(self, route: routes.CompiledRoute, /) -> str:
        """Returns a URL for route.

        Parameters
        ----------
        route: :class:`~routes.CompiledRoute`
            The route.

        Returns
        -------
        :class:`str`
            The URL for the route.
        """
        return self._base + route.build()

    def with_credentials(self, token: str, *, bot: bool = True) -> None:
        """Modifies HTTP client credentials.

        Parameters
        ----------
        token: :class:`str`
            The authentication token.
        bot: :class:`bool`
            Whether the token belongs to bot account or not. Defaults to ``True``.
        """
        self.token = token
        self.bot = bot

    def add_headers(
        self,
        headers: CIMultiDict[typing.Any],
        route: routes.CompiledRoute,
        /,
        *,
        accept_json: bool = True,
        bot: UndefinedOr[bool] = UNDEFINED,
        cookie: UndefinedOr[typing.Optional[str]] = UNDEFINED,
        json_body: bool = False,
        mfa_ticket: typing.Optional[str] = None,
        token: UndefinedOr[typing.Optional[str]] = UNDEFINED,
        user_agent: UndefinedOr[typing.Optional[str]] = UNDEFINED,
    ) -> utils.MaybeAwaitable[None]:
        if accept_json:
            headers['Accept'] = 'application/json'

        if json_body:
            headers['Content-type'] = 'application/json'

        # Allow users to set cookie if Revolt is under attack mode
        if cookie is UNDEFINED:
            if self.cookie:
                headers['Cookie'] = self.cookie
        elif cookie is not None:
            headers['Cookie'] = cookie

        if bot is UNDEFINED:
            bot = self.bot

        th = 'X-Bot-Token' if bot else 'X-Session-Token'

        if token is UNDEFINED:
            token = self.token

        if token:
            headers[th] = token

        if user_agent is UNDEFINED:
            user_agent = self.user_agent

        if user_agent is not None:
            headers['User-Agent'] = user_agent

        if mfa_ticket is not None:
            headers['X-Mfa-Ticket'] = mfa_ticket

    async def send_request(
        self,
        session: aiohttp.ClientSession,
        /,
        *,
        method: str,
        url: str,
        headers: CIMultiDict[typing.Any],
        **kwargs,
    ) -> aiohttp.ClientResponse:
        return await session.request(
            method,
            url,
            headers=headers,
            **kwargs,
        )

    async def raw_request(
        self,
        route: routes.CompiledRoute,
        *,
        accept_json: bool = True,
        bot: UndefinedOr[bool] = UNDEFINED,
        cookie: UndefinedOr[typing.Optional[str]] = UNDEFINED,
        json: UndefinedOr[typing.Any] = UNDEFINED,
        mfa_ticket: typing.Optional[str] = None,
        token: UndefinedOr[typing.Optional[str]] = UNDEFINED,
        user_agent: UndefinedOr[str] = UNDEFINED,
        **kwargs,
    ) -> aiohttp.ClientResponse:
        """|coro|

        Perform a HTTP request, with ratelimiting and errors handling.

        Parameters
        ----------
        route: :class:`~routes.CompiledRoute`
            The route.
        accept_json: :class:`bool`
            Whether to explicitly receive JSON or not. Defaults to ``True``.
        bot: UndefinedOr[:class:`bool`]
            Whether the authentication token belongs to bot account. Defaults to :attr:`.bot`.
        cookie: UndefinedOr[:class:`str`]
            The cookies to use when performing a request.
        json: UndefinedOr[typing.Any]
            The JSON payload to pass in.
        mfa_ticket: Optional[:class:`str`]
            The MFA ticket to pass in headers.
        token: UndefinedOr[Optional[:class:`str`]]
            The token to use when requesting the route.
        user_agent: UndefinedOr[:class:`str`]
            The user agent to use for HTTP request. Defaults to :attr:`.user_agent`.

        Raises
        ------
        :class:`HTTPException`
            Something went wrong during request.

        Returns
        -------
        :class:`aiohttp.ClientResponse`
            The aiohttp response.
        """
        headers: CIMultiDict[str]

        try:
            headers = CIMultiDict(kwargs.pop('headers'))
        except KeyError:
            headers = CIMultiDict()

        retries = 0

        tmp = self.add_headers(
            headers,
            route,
            accept_json=accept_json,
            bot=bot,
            cookie=cookie,
            json_body=json is not UNDEFINED,
            mfa_ticket=mfa_ticket,
            token=token,
            user_agent=user_agent,
        )
        if isawaitable(tmp):
            await tmp

        method = route.route.method
        path = route.build()
        url = self._base + path

        if json is not UNDEFINED:
            kwargs['data'] = utils.to_json(json)

        rate_limiter = self.rate_limiter

        while True:
            if rate_limiter:
                rate_limit = rate_limiter.fetch_ratelimit_for(route, path)
                if rate_limit:
                    blocker: typing.Optional[RateLimitBlocker] = None
                else:
                    blocker = rate_limiter.fetch_blocker_for(route, path)
                    await blocker.increment()

                    rate_limit = rate_limiter.fetch_ratelimit_for(route, path)

                if rate_limit:
                    await rate_limit.block()
            else:
                blocker = None

            _L.debug('Sending request to %s %s with %s', method, path, kwargs.get('data'))

            session = self._session
            if callable(session):
                session = await utils.maybe_coroutine(session, self)
                # detect recursion
                if callable(session):
                    raise TypeError(f'Expected aiohttp.ClientSession, not {type(session)!r}')
                # Do not call factory on future requests
                self._session = session

            try:
                response = await self.send_request(
                    session,
                    method=method,
                    url=url,
                    headers=headers,
                    **kwargs,
                )
            except OSError as exc:
                # TODO: Handle 10053?
                if exc.errno in (54, 10054):  # Connection reset by peer
                    await asyncio.sleep(1.5)
                    continue
                raise

            if rate_limiter:
                await rate_limiter.on_response(route, path, response)
                if blocker:
                    await blocker.decrement()

            if response.status >= 400:
                _L.debug('%s %s has returned %s', method, path, response.status)

                if response.status == 525:
                    await asyncio.sleep(1)
                    continue

                retries += 1

                if response.status == 502:
                    if retries >= self.max_retries:
                        data = await utils._json_or_text(response)
                        raise BadGateway(response, data)
                    continue

                elif response.status == 429:
                    if retries < self.max_retries:
                        data = await utils._json_or_text(response)

                        if isinstance(data, dict):
                            # Special case here
                            ignoring = data.get('type') == 'DiscriminatorChangeRatelimited'
                            retry_after: float = data.get('retry_after', 0) / 1000.0
                        else:
                            ignoring = False
                            retry_after = 1

                        if not ignoring:
                            _L.debug(
                                'Ratelimited on %s %s, retrying in %.3f seconds',
                                method,
                                url,
                                retry_after,
                            )
                            await asyncio.sleep(retry_after)
                            continue

                data = await utils._json_or_text(response)
                if isinstance(data, dict) and isinstance(data.get('error'), dict):
                    error = data['error']
                    code = error.get('code')
                    reason = error.get('reason')
                    description = error.get('description')
                    data['type'] = 'RocketError'
                    data['err'] = f'{code} {reason}: {description}'

                raise _STATUS_TO_ERRORS.get(response.status, HTTPException)(response, data)
            return response

    async def request(
        self,
        route: routes.CompiledRoute,
        *,
        accept_json: bool = True,
        bot: UndefinedOr[bool] = UNDEFINED,
        mfa_ticket: typing.Optional[str] = None,
        json: UndefinedOr[typing.Any] = UNDEFINED,
        log: bool = True,
        token: UndefinedOr[typing.Optional[str]] = UNDEFINED,
        user_agent: UndefinedOr[str] = UNDEFINED,
        **kwargs,
    ) -> typing.Any:
        """|coro|

        Perform a HTTP request, with ratelimiting and errors handling.

        Parameters
        ----------
        route: :class:`~routes.CompiledRoute`
            The route.
        accept_json: :class:`bool`
            Whether to explicitly receive JSON or not. Defaults to ``True``.
        bot: UndefinedOr[:class:`bool`]
            Whether the authentication token belongs to bot account. Defaults to :attr:`.bot`.
        json: UndefinedOr[typing.Any]
            The JSON payload to pass in.
        log: :class:`bool`
            Whether to log successful response or not. This option is intended to avoid console spam caused
            by routes like ``GET /servers/{server_id}/members``. Defaults to ``True``.
        mfa_ticket: Optional[:class:`str`]
            The MFA ticket to pass in headers.
        token: UndefinedOr[Optional[:class:`str`]]
            The token to use when requesting the route.
        user_agent: UndefinedOr[:class:`str`]
            The user agent to use for HTTP request. Defaults to :attr:`.user_agent`.

        Raises
        ------
        :class:`HTTPException`
            Something went wrong during request.

        Returns
        -------
        typing.Any
            The parsed JSON response.
        """
        response = await self.raw_request(
            route,
            accept_json=accept_json,
            bot=bot,
            json=json,
            mfa_ticket=mfa_ticket,
            token=token,
            user_agent=user_agent,
            **kwargs,
        )
        result = await utils._json_or_text(response)

        if log:
            method = response.request_info.method
            url = response.request_info.url

            _L.debug('%s %s has received %s %s', method, url, response.status, result)
        else:
            method = response.request_info.method
            url = response.request_info.url

            _L.debug('%s %s has received %s [too large response]', method, url, response.status)

        response.close()
        return result

    async def cleanup(self) -> None:
        """|coro|

        Closes the aiohttp session.
        """
        if not callable(self._session):
            await self._session.close()

    async def query_node(self) -> Instance:
        """|coro|

        Retrieves the instance information.

        Raises
        ------
        :class:`InternalServerError`
            The internal configuration is invalid.

        Returns
        -------
        :class:`.Instance`
            The instance.
        """
        resp: raw.RevoltConfig = await self.request(routes.ROOT.compile(), token=None)
        return self.state.parser.parse_instance(resp)

    # Bots control
    async def create_bot(self, name: str) -> Bot:
        """|coro|

        Creates a new Revolt bot.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        name: :class:`str`
            The bot name. Must be between 2 and 32 characters and not contain whitespace characters.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +------------------------+---------------------------------------------------------+
            | Value                  | Reason                                                  |
            +------------------------+---------------------------------------------------------+
            | ``FailedValidation``   | The bot's name exceeded length or contained whitespace. |
            +------------------------+---------------------------------------------------------+
            | ``InvalidUsername``    | The bot's name had forbidden characters/substrings.     |
            +------------------------+---------------------------------------------------------+
            | ``IsBot``              | The current token belongs to bot account.               |
            +------------------------+---------------------------------------------------------+
            | ``ReachedMaximumBots`` | The current user has too many bots.                     |
            +------------------------+---------------------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+-----------------------------------------+
            | Value              | Reason                                  |
            +--------------------+-----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid.  |
            +--------------------+-----------------------------------------+
        :class:`Conflict`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+--------------------------------------------------------------+
            | Value             | Reason                                                       |
            +-------------------+--------------------------------------------------------------+
            | ``UsernameTaken`` | The bot user name was taken.                                 |
            +-------------------+--------------------------------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`Bot`
            The created bot.
        """
        payload: raw.DataCreateBot = {'name': name}
        resp: raw.BotWithUserResponse = await self.request(routes.BOTS_CREATE.compile(), json=payload)

        # TODO: Remove when Revolt will fix this
        if resp['user']['relationship'] == 'User':
            resp['user']['relationship'] = 'None'
        return self.state.parser.parse_bot(resp, resp['user'])

    async def delete_bot(self, bot: ULIDOr[BaseBot], /) -> None:
        """|coro|

        Deletes the bot.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        bot: ULIDOr[:class:`.BaseBot`]
            The bot to delete.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +---------------------+----------------------------------------+
            | Value               | Reason                                 |
            +---------------------+----------------------------------------+
            | ``InvalidSession``  | The current bot/user token is invalid. |
            +---------------------+----------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+--------------------------------------------------------------+
            | Value        | Reason                                                       |
            +--------------+--------------------------------------------------------------+
            | ``NotFound`` | The bot was not found, or the current user does not own bot. |
            +--------------+--------------------------------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """
        await self.request(routes.BOTS_DELETE.compile(bot_id=resolve_id(bot)))

    async def edit_bot(
        self,
        bot: ULIDOr[BaseBot],
        *,
        name: UndefinedOr[str] = UNDEFINED,
        public: UndefinedOr[bool] = UNDEFINED,
        analytics: UndefinedOr[bool] = UNDEFINED,
        interactions_url: UndefinedOr[typing.Optional[str]] = UNDEFINED,
        reset_token: bool = False,
    ) -> Bot:
        """|coro|

        Edits the bot.

        Parameters
        ----------
        bot: ULIDOr[:class:`.BaseBot`]
            The bot to edit.
        name: UndefinedOr[:class:`str`]
            The new bot name. Must be between 2 and 32 characters and not contain whitespace characters.
        public: UndefinedOr[:class:`bool`]
            Whether the bot should be public (could be invited by anyone).
        analytics: UndefinedOr[:class:`bool`]
            Whether to allow Revolt collect analytics about the bot.
        interactions_url: UndefinedOr[Optional[:class:`str`]]
            The new bot interactions URL. For now, this parameter is reserved and does not do anything.
        reset_token: :class:`bool`
            Whether to reset bot token. The new token can be accessed via :attr:`Bot.token`.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------+---------------------------------------------------------+
            | Value                | Reason                                                  |
            +----------------------+---------------------------------------------------------+
            | ``FailedValidation`` | The bot's name exceeded length or contained whitespace. |
            +----------------------+---------------------------------------------------------+
            | ``InvalidUsername``  | The bot's name had forbidden characters/substrings.     |
            +----------------------+---------------------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+-----------------------------------------+
            | Value              | Reason                                  |
            +--------------------+-----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid.  |
            +--------------------+-----------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+--------------------------------------------------------------+
            | Value        | Reason                                                       |
            +--------------+--------------------------------------------------------------+
            | ``NotFound`` | The bot was not found, or the current user does not own bot. |
            +--------------+--------------------------------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`.Bot`
            The updated bot.
        """
        payload: raw.DataEditBot = {}
        remove: list[raw.FieldsBot] = []
        if name is not UNDEFINED:
            payload['name'] = name
        if public is not UNDEFINED:
            payload['public'] = public
        if analytics is not UNDEFINED:
            payload['analytics'] = analytics
        if interactions_url is not UNDEFINED:
            if interactions_url is None:
                remove.append('InteractionsURL')
            else:
                payload['interactions_url'] = interactions_url
        if reset_token:
            remove.append('Token')
        if len(remove) > 0:
            payload['remove'] = remove

        resp: raw.BotWithUserResponse = await self.request(
            routes.BOTS_EDIT.compile(bot_id=resolve_id(bot)), json=payload
        )

        # TODO: Remove when Revolt will fix this
        if resp['user']['relationship'] == 'User':
            resp['user']['relationship'] = 'None'

        return self.state.parser.parse_bot(
            resp,
            resp['user'],
        )

    async def get_bot(self, bot: ULIDOr[BaseBot], /) -> Bot:
        """|coro|

        Retrieves the bot with the given ID.

        The bot must be owned by you.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        bot: ULIDOr[:class:`.BaseBot`]
            The bot to fetch.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +-----------+-------------------------------------------+
            | Value     | Reason                                    |
            +-----------+-------------------------------------------+
            | ``IsBot`` | The current token belongs to bot account. |
            +-----------+-------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+-----------------------------------------+
            | Value              | Reason                                  |
            +--------------------+-----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid.  |
            +--------------------+-----------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------------------------+--------------------------------------------------------------+
            | Value                                | Reason                                                       |
            +--------------------------------------+--------------------------------------------------------------+
            | ``NotFound``                         | The bot was not found, or the current user does not own bot. |
            +--------------------------------------+--------------------------------------------------------------+

        Returns
        -------
        :class:`.Bot`
            The retrieved bot.
        """
        resp: raw.FetchBotResponse = await self.request(routes.BOTS_FETCH.compile(bot_id=resolve_id(bot)))
        return self.state.parser.parse_bot(resp['bot'], resp['user'])

    async def get_owned_bots(self) -> list[Bot]:
        """|coro|

        Retrieves all bots owned by you.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        List[:class:`.Bot`]
            The owned bots.
        """
        resp: raw.OwnedBotsResponse = await self.request(routes.BOTS_FETCH_OWNED.compile())
        return self.state.parser.parse_bots(resp)

    async def get_public_bot(self, bot: ULIDOr[BaseBot], /) -> PublicBot:
        """|coro|

        Retrieves the public bot with the given ID.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        bot: ULIDOr[:class:`.BaseBot`]
            The bot to fetch.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+--------------------------------------------------------------+
            | Value        | Reason                                                       |
            +--------------+--------------------------------------------------------------+
            | ``NotFound`` | The bot was not found, or the current user does not own bot. |
            +--------------+--------------------------------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`.PublicBot`
            The retrieved bot.
        """
        resp: raw.PublicBot = await self.request(routes.BOTS_FETCH_PUBLIC.compile(bot_id=resolve_id(bot)))
        return self.state.parser.parse_public_bot(resp)

    @typing.overload
    async def invite_bot(
        self,
        bot: ULIDOr[typing.Union[BaseBot, BaseUser]],
        *,
        server: ULIDOr[BaseServer],
    ) -> None: ...

    @typing.overload
    async def invite_bot(
        self,
        bot: ULIDOr[typing.Union[BaseBot, BaseUser]],
        *,
        group: ULIDOr[GroupChannel],
    ) -> None: ...

    async def invite_bot(
        self,
        bot: ULIDOr[typing.Union[BaseBot, BaseUser]],
        *,
        server: typing.Optional[ULIDOr[BaseServer]] = None,
        group: typing.Optional[ULIDOr[GroupChannel]] = None,
    ) -> None:
        """|coro|

        Invites a bot to a server or group.
        **Specifying both ``server`` and ``group`` parameters (or no parameters at all) will lead to an exception.**

        If destination is a server, you must have :attr:`~Permissions.manage_server` to do this, otherwise :attr:`~Permissions.invite_others` is required.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        bot: ULIDOr[Union[:class:`.BaseBot`, :class:`.BaseUser`]]
            The bot.
        server: Optional[ULIDOr[:class:`.BaseServer`]]
            The destination server.
        group: Optional[ULIDOr[:class:`.GroupChannel`]]
            The destination group.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------+------------------------------------------------------+
            | Value                | Reason                                               |
            +----------------------+------------------------------------------------------+
            | ``InvalidOperation`` | The target channel was not actually a group channel. |
            +----------------------+------------------------------------------------------+
            | ``IsBot``            | The current token belongs to bot account.            |
            +----------------------+------------------------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+-----------------------------------------------------+
            | Value                 | Reason                                              |
            +-----------------------+-----------------------------------------------------+
            | ``Banned``            | The bot was banned in target server.                |
            +-----------------------+-----------------------------------------------------+
            | ``BotIsPrivate``      | You do not own the bot to add it.                   |
            +-----------------------+-----------------------------------------------------+
            | ``GroupTooLarge``     | The group exceeded maximum count of recipients.     |
            +-----------------------+-----------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to add bots. |
            +-----------------------+-----------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+-------------------------------------+
            | Value        | Reason                              |
            +--------------+-------------------------------------+
            | ``NotFound`` | The bot/group/server was not found. |
            +--------------+-------------------------------------+
        :class:`Conflict`
            Possible values for :attr:`~HTTPException.type`:

            +---------------------+-------------------------------+
            | Value               | Reason                        |
            +---------------------+-------------------------------+
            | ``AlreadyInGroup``  | The bot is already in group.  |
            +---------------------+-------------------------------+
            | ``AlreadyInServer`` | The bot is already in server. |
            +---------------------+-------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        :class:`TypeError`
            You specified ``server`` and ``group`` parameters, or passed no parameters.
        """
        if server and group:
            raise TypeError('Cannot pass both server and group')
        if not server and not group:
            raise TypeError('Pass server or group')

        payload: raw.InviteBotDestination
        if server:
            payload = {'server': resolve_id(server)}
        elif group:
            payload = {'group': resolve_id(group)}
        else:
            raise RuntimeError('Unreachable')

        await self.request(routes.BOTS_INVITE.compile(bot_id=resolve_id(bot)), json=payload)

    # Channels control
    async def acknowledge_message(self, channel: ULIDOr[TextableChannel], message: ULIDOr[BaseMessage]) -> None:
        """|coro|

        Marks this message as read.

        You must have :attr:`~Permissions.view_channel` to do this.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        channel: ULIDOr[:class:`.TextableChannel`]
            The channel.
        message: ULIDOr[:class:`.BaseMessage`]
            The message.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+-----------------------------------------+
            | Value              | Reason                                  |
            +--------------------+-----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid.  |
            +--------------------+-----------------------------------------+
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +-----------+-------------------------------------------+
            | Value     | Reason                                    |
            +-----------+-------------------------------------------+
            | ``IsBot`` | The current token belongs to bot account. |
            +-----------+-------------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+-------------------------------------------------------------+
            | Value                 | Reason                                                      |
            +-----------------------+-------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to view the message. |
            +-----------------------+-------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+----------------------------+
            | Value        | Reason                     |
            +--------------+----------------------------+
            | ``NotFound`` | The channel was not found. |
            +--------------+----------------------------+
        """
        await self.request(
            routes.CHANNELS_CHANNEL_ACK.compile(
                channel_id=resolve_id(channel),
                message_id=resolve_id(message),
            )
        )

    async def close_channel(self, channel: ULIDOr[BaseChannel], silent: typing.Optional[bool] = None) -> None:
        """|coro|

        Deletes a server channel, leaves a group or closes a group.

        You must have :attr:`~Permissions.view_channel` to do this. If target channel is server channel, :attr:`~Permissions.manage_channels` is also required.

        Parameters
        ----------
        channel: ULIDOr[:class:`.BaseChannel`]
            The channel to close.
        silent: Optional[:class:`bool`]
            Whether to not send message when leaving.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+-----------------------------------------+
            | Value              | Reason                                  |
            +--------------------+-----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid.  |
            +--------------------+-----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+---------------------------------------------------------------------------+
            | Value                 | Reason                                                                    |
            +-----------------------+---------------------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to view and/or delete the channel. |
            +-----------------------+---------------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+----------------------------+
            | Value        | Reason                     |
            +--------------+----------------------------+
            | ``NotFound`` | The channel was not found. |
            +--------------+----------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """
        params: raw.OptionsChannelDelete = {}
        if silent is not None:
            params['leave_silently'] = utils._bool(silent)

        # this endpoint can return NoEffect and its 200 OK for some reason
        await self.request(
            routes.CHANNELS_CHANNEL_DELETE.compile(channel_id=resolve_id(channel)),
            params=params,
        )

    async def edit_channel(
        self,
        channel: ULIDOr[BaseChannel],
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[typing.Optional[str]] = UNDEFINED,
        owner: UndefinedOr[ULIDOr[BaseUser]] = UNDEFINED,
        icon: UndefinedOr[typing.Optional[ResolvableResource]] = UNDEFINED,
        nsfw: UndefinedOr[bool] = UNDEFINED,
        archived: UndefinedOr[bool] = UNDEFINED,
        default_permissions: UndefinedOr[None] = UNDEFINED,
    ) -> Channel:
        """|coro|

        Edits the channel.

        You must have :attr:`~Permissions.manage_channels` to do this.

        Parameters
        ----------
        channel: ULIDOr[:class:`.BaseChannel`]
            The channel.
        name: UndefinedOr[:class:`str`]
            The new channel name. Only applicable when target channel is :class:`.GroupChannel`, or :class:`.ServerChannel`.
        description: UndefinedOr[Optional[:class:`str`]]
            The new channel description. Only applicable when target channel is :class:`.GroupChannel`, or :class:`.ServerChannel`.
        owner: UndefinedOr[ULIDOr[:class:`.BaseUser`]]
            The new channel owner. Only applicable when target channel is :class:`.GroupChannel`.
        icon: UndefinedOr[Optional[:class:`.ResolvableResource`]]
            The new channel icon. Only applicable when target channel is :class:`.GroupChannel`, or :class:`.ServerChannel`.
        nsfw: UndefinedOr[:class:`bool`]
            To mark the channel as NSFW or not. Only applicable when target channel is :class:`.GroupChannel`, or :class:`.ServerChannel`.
        archived: UndefinedOr[:class:`bool`]
            To mark the channel as archived or not.
        default_permissions: UndefinedOr[None]
            To remove default permissions or not. Only applicable when target channel is :class:`.GroupChannel`, or :class:`.ServerChannel`.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------+------------------------------------------------------+
            | Value                | Reason                                               |
            +----------------------+------------------------------------------------------+
            | ``FailedValidation`` | The payload was invalid.                             |
            +----------------------+------------------------------------------------------+
            | ``InvalidOperation`` | The target channel was not group/text/voice channel. |
            +----------------------+------------------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+-------------------------------------------------------------+
            | Value                 | Reason                                                      |
            +-----------------------+-------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to edit the channel. |
            +-----------------------+-------------------------------------------------------------+
            | ``NotOwner``          | You do not own the group.                                   |
            +-----------------------+-------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +----------------+---------------------------------+
            | Value          | Reason                          |
            +----------------+---------------------------------+
            | ``NotFound``   | The channel was not found.      |
            +----------------+---------------------------------+
            | ``NotInGroup`` | The new owner was not in group. |
            +----------------+---------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`.Channel`
            The newly updated channel.
        """
        payload: raw.DataEditChannel = {}
        remove: list[raw.FieldsChannel] = []
        if name is not UNDEFINED:
            payload['name'] = name
        if description is not UNDEFINED:
            if description is None:
                remove.append('Description')
            else:
                payload['description'] = description
        if owner is not UNDEFINED:
            payload['owner'] = resolve_id(owner)
        if icon is not UNDEFINED:
            if icon is None:
                remove.append('Icon')
            else:
                payload['icon'] = await resolve_resource(self.state, icon, tag='icons')
        if nsfw is not UNDEFINED:
            payload['nsfw'] = nsfw
        if archived is not UNDEFINED:
            payload['archived'] = archived
        if default_permissions is not UNDEFINED:
            remove.append('DefaultPermissions')
        if len(remove) > 0:
            payload['remove'] = remove
        resp: raw.Channel = await self.request(
            routes.CHANNELS_CHANNEL_EDIT.compile(channel_id=resolve_id(channel)),
            json=payload,
        )
        return self.state.parser.parse_channel(resp)

    async def get_channel(self, channel: ULIDOr[BaseChannel], /) -> Channel:
        """|coro|

        Fetch a :class:`.Channel` with the specified ID.

        You must have :attr:`~Permissions.view_channel` to do this.

        Parameters
        ----------
        channel: ULIDOr[:class:`.BaseChannel`]
            The channel to fetch.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+-------------------------------------------------------------+
            | Value                 | Reason                                                      |
            +-----------------------+-------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to view the channel. |
            +-----------------------+-------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+----------------------------+
            | Value        | Reason                     |
            +--------------+----------------------------+
            | ``NotFound`` | The channel was not found. |
            +--------------+----------------------------+

        Returns
        -------
        :class:`.Channel`
            The retrieved channel.
        """
        resp: raw.Channel = await self.request(routes.CHANNELS_CHANNEL_FETCH.compile(channel_id=resolve_id(channel)))
        return self.state.parser.parse_channel(resp)

    async def add_group_recipient(
        self,
        channel: ULIDOr[GroupChannel],
        /,
        user: ULIDOr[BaseUser],
    ) -> None:
        """|coro|

        Adds another user to the group.

        You must have :attr:`~Permissions.create_invites` to do this.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        channel: ULIDOr[:class:`.GroupChannel`]
            The group.
        user: ULIDOr[:class:`.BaseUser`]
            The user to add.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------+-------------------------------------------+
            | Value                | Reason                                    |
            +----------------------+-------------------------------------------+
            | ``InvalidOperation`` | The target channel is not group.          |
            +----------------------+-------------------------------------------+
            | ``IsBot``            | The current token belongs to bot account. |
            +----------------------+-------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+--------------------------------------------------------------+
            | Value                 | Reason                                                       |
            +-----------------------+--------------------------------------------------------------+
            | ``GroupTooLarge``     | The group exceeded maximum count of recipients.              |
            +-----------------------+--------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to add the recipient. |
            +-----------------------+--------------------------------------------------------------+
            | ``NotFriends``        | You're not friends with the user you want to add.            |
            +-----------------------+--------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+-------------------------------------+
            | Value        | Reason                              |
            +--------------+-------------------------------------+
            | ``NotFound`` | The channel or user were not found. |
            +--------------+-------------------------------------+
        :class:`Conflict`
            Possible values for :attr:`~HTTPException.type`:

            +---------------------+-------------------------------+
            | Value               | Reason                        |
            +---------------------+-------------------------------+
            | ``AlreadyInGroup``  | The user is already in group. |
            +---------------------+-------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """
        await self.request(
            routes.CHANNELS_GROUP_ADD_MEMBER.compile(channel_id=resolve_id(channel), user_id=resolve_id(user))
        )

    async def create_group(
        self,
        name: str,
        *,
        description: typing.Optional[str] = None,
        icon: typing.Optional[ResolvableResource] = None,
        recipients: list[ULIDOr[BaseUser]] | None = None,
        nsfw: typing.Optional[bool] = None,
    ) -> GroupChannel:
        """|coro|

        Creates a new group.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        name: :class:`str`
            The group name. Must be between 1 and 32 characters long.
        description: Optional[:class:`str`]
            The group description. Can be only up to 1024 characters.
        icon: Optional[:class:`.ResolvableResource`]
            The group's icon.
        recipients: Optional[List[ULIDOr[:class:`.BaseUser`]]]
            The users to create the group with, only up to 49 users. You must be friends with these users.
        nsfw: Optional[:class:`bool`]
            To mark the group as NSFW or not.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------+-------------------------------------------+
            | Value                | Reason                                    |
            +----------------------+-------------------------------------------+
            | ``FailedValidation`` | The payload was invalid.                  |
            +----------------------+-------------------------------------------+
            | ``IsBot``            | The current token belongs to bot account. |
            +----------------------+-------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+------------------------------------------------------------------+
            | Value                 | Reason                                                           |
            +-----------------------+------------------------------------------------------------------+
            | ``GroupTooLarge``     | The group exceeded maximum count of recipients.                  |
            +-----------------------+------------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to add the recipient.     |
            +-----------------------+------------------------------------------------------------------+
            | ``NotFriends``        | You're not friends with the users you want to create group with. |
            +-----------------------+------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+----------------------------------+
            | Value        | Reason                           |
            +--------------+----------------------------------+
            | ``NotFound`` | One of recipients was not found. |
            +--------------+----------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`.GroupChannel`
            The new group.
        """
        payload: raw.DataCreateGroup = {'name': name}
        if description is not None:
            payload['description'] = description
        if icon is not None:
            payload['icon'] = await resolve_resource(self.state, icon, tag='icons')
        if recipients is not None:
            payload['users'] = list(map(resolve_id, recipients))
        if nsfw is not None:
            payload['nsfw'] = nsfw
        resp: raw.GroupChannel = await self.request(routes.CHANNELS_GROUP_CREATE.compile(), json=payload)
        return self.state.parser.parse_group_channel(
            resp,
            (True, []),
        )

    async def remove_group_recipient(
        self,
        channel: ULIDOr[GroupChannel],
        user: ULIDOr[BaseUser],
    ) -> None:
        """|coro|

        Removes a recipient from the group.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        channel: ULIDOr[:class:`.GroupChannel`]
            The group.
        user: ULIDOr[:class:`.BaseUser`]
            The user to remove.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------------+----------------------------------------------+
            | Value                    | Reason                                       |
            +--------------------------+----------------------------------------------+
            | ``CannotRemoveYourself`` | You tried to remove yourself from the group. |
            +--------------------------+----------------------------------------------+
            | ``IsBot``                | The current token belongs to bot account.    |
            +--------------------------+----------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+------------------------------------------------------------------+
            | Value                 | Reason                                                           |
            +-----------------------+------------------------------------------------------------------+
            | ``MissingPermission`` | You do not own the target group.                                 |
            +-----------------------+------------------------------------------------------------------+
            | ``NotFriends``        | You're not friends with the users you want to create group with. |
            +-----------------------+------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +----------------+------------------------------------------------------+
            | Value          | Reason                                               |
            +----------------+------------------------------------------------------+
            | ``NotFound``   | The target group was not found.                      |
            +----------------+------------------------------------------------------+
            | ``NotInGroup`` | The recipient you wanted to remove was not in group. |
            +----------------+------------------------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """
        await self.request(
            routes.CHANNELS_GROUP_REMOVE_MEMBER.compile(
                channel_id=resolve_id(channel),
                user_id=resolve_id(user),
            )
        )

    async def create_channel_invite(self, channel: ULIDOr[typing.Union[GroupChannel, ServerChannel]]) -> Invite:
        """|coro|

        Creates an invite to channel. The destination channel must be a group or server channel.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        channel: ULIDOr[Union[:class:`.GroupChannel`, :class:`.ServerChannel`]]
            The invite destination channel.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------+----------------------------------------------------+
            | Value                | Reason                                             |
            +----------------------+----------------------------------------------------+
            | ``InvalidOperation`` | The target channel is not group or server channel. |
            +----------------------+----------------------------------------------------+
            | ``IsBot``            | The current token belongs to bot account.          |
            +----------------------+----------------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+----------------------------------------------------------------------+
            | Value                 | Reason                                                               |
            +-----------------------+----------------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to create invites in channel. |
            +-----------------------+----------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +----------------+-----------------------------------+
            | Value          | Reason                            |
            +----------------+-----------------------------------+
            | ``NotFound``   | The target channel was not found. |
            +----------------+-----------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`.Invite`
            The invite that was created.
        """
        resp: raw.Invite = await self.request(routes.CHANNELS_INVITE_CREATE.compile(channel_id=resolve_id(channel)))
        return self.state.parser.parse_invite(resp)

    async def get_group_recipients(
        self,
        channel: ULIDOr[GroupChannel],
        /,
    ) -> list[User]:
        """|coro|

        Retrieves all recipients who are part of this group.

        Parameters
        ----------
        channel: ULIDOr[:class:`.GroupChannel`]
            The group channel.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------+----------------------------------+
            | Value                | Reason                           |
            +----------------------+----------------------------------+
            | ``InvalidOperation`` | The target channel is not group. |
            +----------------------+----------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+-----------------------------------------------------------+
            | Value                 | Reason                                                    |
            +-----------------------+-----------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to view the group. |
            +-----------------------+-----------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +----------------+-----------------------------------+
            | Value          | Reason                            |
            +----------------+-----------------------------------+
            | ``NotFound``   | The target channel was not found. |
            +----------------+-----------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        List[:class:`.User`]
            The group recipients.
        """
        resp: list[raw.User] = await self.request(
            routes.CHANNELS_MEMBERS_FETCH.compile(
                channel_id=resolve_id(channel),
            )
        )
        return list(map(self.state.parser.parse_user, resp))

    async def delete_messages(
        self, channel: ULIDOr[TextableChannel], messages: Sequence[ULIDOr[BaseMessage]], /
    ) -> None:
        """|coro|

        Delete multiple messages.

        You must have :attr:`~Permissions.manage_messages` to do this regardless whether you authored the message or not.

        Parameters
        ----------
        channel: ULIDOr[:class:`.TextableChannel`]
            The channel.
        messages: Sequence[ULIDOr[:class:`.BaseMessage`]]
            The messages to delete.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------+-----------------------------------------------------------------------------+
            | Value                | Reason                                                                      |
            +----------------------+-----------------------------------------------------------------------------+
            | ``InvalidOperation`` | One of provided message IDs was invalid or message was at least 1 week old. |
            +----------------------+-----------------------------------------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+------------------------------------------------------------+
            | Value                 | Reason                                                     |
            +-----------------------+------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to delete messages. |
            +-----------------------+------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +----------------+-----------------------------------+
            | Value          | Reason                            |
            +----------------+-----------------------------------+
            | ``NotFound``   | The target channel was not found. |
            +----------------+-----------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        """
        payload: raw.OptionsBulkDelete = {'ids': [resolve_id(message) for message in messages]}
        await self.request(
            routes.CHANNELS_MESSAGE_DELETE_BULK.compile(channel_id=resolve_id(channel)),
            json=payload,
        )

    async def clear_reactions(self, channel: ULIDOr[TextableChannel], message: ULIDOr[BaseMessage], /) -> None:
        """|coro|

        Removes all the reactions from the message.

        You must have :attr:`~Permissions.manage_messages` to do this.

        Parameters
        ----------
        channel: ULIDOr[:class:`.TextableChannel`]
            The channel.
        message: ULIDOr[:class:`.BaseMessage`]
            The message.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+-----------------------------------------+
            | Value              | Reason                                  |
            +--------------------+-----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid.  |
            +--------------------+-----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+---------------------------------------------------------------------+
            | Value                 | Reason                                                              |
            +-----------------------+---------------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to remove all the reactions. |
            +-----------------------+---------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+---------------------------------------+
            | Value        | Reason                                |
            +--------------+---------------------------------------+
            | ``NotFound`` | The channel or message was not found. |
            +--------------+---------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """
        await self.request(
            routes.CHANNELS_MESSAGE_CLEAR_REACTIONS.compile(
                channel_id=resolve_id(channel),
                message_id=resolve_id(message),
            )
        )

    async def delete_message(self, channel: ULIDOr[TextableChannel], message: ULIDOr[BaseMessage], /) -> None:
        """|coro|

        Deletes the message in a channel.

        You must have :attr:`~Permissions.manage_messages` to do this if message is not yours.

        Parameters
        ----------
        channel: ULIDOr[:class:`.TextableChannel`]
            The channel.
        message: ULIDOr[:class:`.BaseMessage`]
            The message.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+-----------------------------------------+
            | Value              | Reason                                  |
            +--------------------+-----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid.  |
            +--------------------+-----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+---------------------------------------------------------------+
            | Value                 | Reason                                                        |
            +-----------------------+---------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to delete the message. |
            +-----------------------+---------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+---------------------------------------+
            | Value        | Reason                                |
            +--------------+---------------------------------------+
            | ``NotFound`` | The channel or message was not found. |
            +--------------+---------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """
        await self.request(
            routes.CHANNELS_MESSAGE_DELETE.compile(
                channel_id=resolve_id(channel),
                message_id=resolve_id(message),
            )
        )

    async def edit_message(
        self,
        channel: ULIDOr[TextableChannel],
        message: ULIDOr[BaseMessage],
        *,
        content: UndefinedOr[str] = UNDEFINED,
        embeds: UndefinedOr[list[SendableEmbed]] = UNDEFINED,
    ) -> Message:
        """|coro|

        Edits a message in channel.

        Parameters
        ----------
        channel: ULIDOr[:class:`.TextableChannel`]
            The channel the message is in.
        message: ULIDOr[:class:`.BaseMessage`]
            The message to edit.
        content: UndefinedOr[:class:`str`]
            The new content to replace the message with. Must be between 1 and 2000 characters long.
        embeds: UndefinedOr[List[:class:`.SendableEmbed`]]
            The new embeds to replace the original with. Must be a maximum of 10. To remove all embeds ``[]`` should be passed.

            You must have :attr:`~Permissions.send_embeds` to provide this.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +------------------------+----------------------------+
            | Value                  | Reason                     |
            +------------------------+----------------------------+
            | ``FailedValidation``   | The payload was invalid.   |
            +------------------------+----------------------------+
            | ``PayloadTooLarge``    | The message was too large. |
            +------------------------+----------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+----------------------------------------------------------+
            | Value                 | Reason                                                   |
            +-----------------------+----------------------------------------------------------+
            | ``CannotEditMessage`` | The message you tried to edit isn't yours.               |
            +-----------------------+----------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to send messages. |
            +-----------------------+----------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+-----------------------------------------+
            | Value        | Reason                                  |
            +--------------+-----------------------------------------+
            | ``NotFound`` | The channel/message/file was not found. |
            +--------------+-----------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`Message`
            The newly edited message.
        """
        payload: raw.DataEditMessage = {}

        if content is not UNDEFINED:
            payload['content'] = content
        if embeds is not UNDEFINED:
            payload['embeds'] = [await embed.build(self.state) for embed in embeds]

        resp: raw.Message = await self.request(
            routes.CHANNELS_MESSAGE_EDIT.compile(
                channel_id=resolve_id(channel),
                message_id=resolve_id(message),
            ),
            json=payload,
        )
        return self.state.parser.parse_message(resp)

    async def get_message(self, channel: ULIDOr[TextableChannel], message: ULIDOr[BaseMessage]) -> Message:
        """|coro|

        Retrieves a message.

        Parameters
        ----------
        channel: ULIDOr[:class:`.TextableChannel`]
            The channel the message is in.
        message: ULIDOr[:class:`BaseMessage`]
            The message to retrieve.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+-------------------------------------------------------------+
            | Value                 | Reason                                                      |
            +-----------------------+-------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to view the channel. |
            +-----------------------+-------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+------------------------------------+
            | Value        | Reason                             |
            +--------------+------------------------------------+
            | ``NotFound`` | The channel/message was not found. |
            +--------------+------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`Message`
            The retrieved message.
        """
        resp: raw.Message = await self.request(
            routes.CHANNELS_MESSAGE_FETCH.compile(
                channel_id=resolve_id(channel),
                message_id=resolve_id(message),
            )
        )
        return self.state.parser.parse_message(resp)

    async def pin_message(self, channel: ULIDOr[TextableChannel], message: ULIDOr[BaseMessage]) -> None:
        """|coro|

        Pins a message.

        You must have :attr:`~Permissions.manage_messages` to do this.

        Parameters
        ----------
        channel: ULIDOr[:class:`.TextableChannel`]
            The channel the message is in.
        message: ULIDOr[:class:`BaseMessage`]
            The message to pin.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+---------------------------------+
            | Value             | Reason                          |
            +-------------------+---------------------------------+
            | ``AlreadyPinned`` | The message was already pinned. |
            +-------------------+---------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+------------------------------------------------------------+
            | Value                 | Reason                                                     |
            +-----------------------+------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to pin the message. |
            +-----------------------+------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+------------------------------------+
            | Value        | Reason                             |
            +--------------+------------------------------------+
            | ``NotFound`` | The channel/message was not found. |
            +--------------+------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """
        await self.request(
            routes.CHANNELS_MESSAGE_PIN.compile(
                channel_id=resolve_id(channel),
                message_id=resolve_id(message),
            )
        )

    async def get_messages(
        self,
        channel: ULIDOr[TextableChannel],
        *,
        limit: typing.Optional[int] = None,
        before: typing.Optional[ULIDOr[BaseMessage]] = None,
        after: typing.Optional[ULIDOr[BaseMessage]] = None,
        sort: typing.Optional[MessageSort] = None,
        nearby: typing.Optional[ULIDOr[BaseMessage]] = None,
        populate_users: typing.Optional[bool] = None,
    ) -> list[Message]:
        """|coro|

        Retrieve message history of a textable channel.

        You must have :attr:`~Permissions.read_message_history` to do this.

        Parameters
        ----------
        channel: ULIDOr[:class:`.TextableChannel`]
            The channel to retrieve messages from.
        limit: Optional[:class:`int`]
            The maximum number of messages to get. Must be between 1 and 100. Defaults to 50.

            If ``nearby`` is provided, then this is ``(limit + 1)``.
        before: Optional[ULIDOr[:class:`.BaseMessage`]]
            The message before which messages should be fetched.
        after: Optional[ULIDOr[:class:`.BaseMessage`]]
            The message after which messages should be fetched.
        sort: Optional[:class:`.MessageSort`]
            The message sort direction. Defaults to :attr:`.MessageSort.latest`
        nearby: Optional[ULIDOr[:class:`.BaseMessage`]]
            The message to search around.

            Providing this parameter will discrd ``before``, ``after`` and ``sort`` parameters.

            It will also take half of limit rounded as the limits to each side. It also fetches the message specified.
        populate_users: :class:`bool`
            Whether to populate user (and member, if server channel) objects.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+---------------------------------------------------------------------+
            | Value                 | Reason                                                              |
            +-----------------------+---------------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to read the message history. |
            +-----------------------+---------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+----------------------------+
            | Value        | Reason                     |
            +--------------+----------------------------+
            | ``NotFound`` | The channel was not found. |
            +--------------+----------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        List[:class:`.Message`]
            The messages retrieved.
        """
        params: raw.OptionsQueryMessages = {}

        if limit is not None:
            params['limit'] = limit
        if before is not None:
            params['before'] = resolve_id(before)
        if after is not None:
            params['after'] = resolve_id(after)
        if sort is not None:
            params['sort'] = sort.value
        if nearby is not None:
            params['nearby'] = resolve_id(nearby)
        if populate_users is not None:
            params['include_users'] = utils._bool(populate_users)

        resp: raw.BulkMessageResponse = await self.request(
            routes.CHANNELS_MESSAGE_QUERY.compile(channel_id=resolve_id(channel)),
            params=params,
        )
        return self.state.parser.parse_messages(resp)

    async def add_reaction_to_message(
        self,
        channel: ULIDOr[TextableChannel],
        message: ULIDOr[BaseMessage],
        emoji: ResolvableEmoji,
    ) -> None:
        """|coro|

        React to a given message.

        You must have :attr:`~Permissions.react` to do this.

        Parameters
        ----------
        channel: ULIDOr[:class:`.TextableChannel`]
            The channel the message was sent in.
        message: ULIDOr[:class:`.BaseMessage`]
            The message to react to.
        emoji: :class:`.ResolvableEmoji`
            The emoji to react with.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------+---------------------------------------------------------------------------------------------------------------+
            | Value                | Reason                                                                                                        |
            +----------------------+---------------------------------------------------------------------------------------------------------------+
            | ``InvalidOperation`` | One of these:                                                                                                 |
            |                      |                                                                                                               |
            |                      | - The message has too many reactions.                                                                         |
            |                      | - If :attr:`MessageInteractions.restrict_reactions` is ``True``, then the emoji provided was not whitelisted. |
            |                      | - The provided emoji was invalid.                                                                             |
            +----------------------+---------------------------------------------------------------------------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+--------------------------------------------------+
            | Value                 | Reason                                           |
            +-----------------------+--------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to react. |
            +-----------------------+--------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+-------------------------------------------------+
            | Value        | Reason                                          |
            +--------------+-------------------------------------------------+
            | ``NotFound`` | The channel/message/custom emoji was not found. |
            +--------------+-------------------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """
        await self.request(
            routes.CHANNELS_MESSAGE_REACT.compile(
                channel_id=resolve_id(channel),
                message_id=resolve_id(message),
                emoji=resolve_emoji(emoji),
            )
        )

    async def search_for_messages(
        self,
        channel: ULIDOr[TextableChannel],
        query: typing.Optional[str] = None,
        *,
        pinned: typing.Optional[bool] = None,
        limit: typing.Optional[int] = None,
        before: typing.Optional[ULIDOr[BaseMessage]] = None,
        after: typing.Optional[ULIDOr[BaseMessage]] = None,
        sort: typing.Optional[MessageSort] = None,
        populate_users: typing.Optional[bool] = None,
    ) -> list[Message]:
        """|coro|

        Searches for messages.

        For ``query`` and ``pinned``, only one parameter can be provided, otherwise a :class:`HTTPException` will
        be thrown with ``InvalidOperation`` type.

        You must have :attr:`~Permissions.read_message_history` to do this.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        channel: ULIDOr[:class:`.TextableChannel`]
            The channel to search in.
        query: Optional[:class:`str`]
            The full-text search query. See `MongoDB documentation <https://www.mongodb.com/docs/manual/text-search/>`_ for more information.
        pinned: Optional[:class:`bool`]
            Whether to search for (un-)pinned messages or not.
        limit: Optional[:class:`int`]
            The maximum number of messages to get. Must be between 1 and 100. Defaults to 50.

            If ``nearby`` is provided, then this is ``(limit + 1)``.
        before: Optional[ULIDOr[:class:`.BaseMessage`]]
            The message before which messages should be fetched.
        after: Optional[ULIDOr[:class:`.BaseMessage`]]
            The message after which messages should be fetched.
        sort: Optional[:class:`.MessageSort`]
            The message sort direction. Defaults to :attr:`.MessageSort.latest`
        nearby: Optional[ULIDOr[:class:`.BaseMessage`]]
            The message to search around.

            Providing this parameter will discard ``before``, ``after`` and ``sort`` parameters.

            It will also take half of limit rounded as the limits to each side. It also fetches the message specified.
        populate_users: :class:`bool`
            Whether to populate user (and member, if server channel) objects.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------+-------------------------------------------------------------------------+
            | Value                | Reason                                                                  |
            +----------------------+-------------------------------------------------------------------------+
            | ``FailedValidation`` | One of ``before``, ``after`` or ``nearby`` parameters were invalid IDs. |
            +----------------------+-------------------------------------------------------------------------+
            | ``InvalidOperation`` | You provided both ``query`` and ``pinned`` parameters.                  |
            +----------------------+-------------------------------------------------------------------------+
            | ``IsBot``            | The current token belongs to bot account.                               |
            +----------------------+-------------------------------------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+------------------------------------------------------------+
            | Value                 | Reason                                                     |
            +-----------------------+------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to search messages. |
            +-----------------------+------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+----------------------------+
            | Value        | Reason                     |
            +--------------+----------------------------+
            | ``NotFound`` | The channel was not found. |
            +--------------+----------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        List[:class:`.Message`]
            The messages matched.
        """
        payload: raw.DataMessageSearch = {}
        if query is not None:
            payload['query'] = query
        if pinned is not None:
            payload['pinned'] = pinned
        if limit is not None:
            payload['limit'] = limit
        if before is not None:
            payload['before'] = resolve_id(before)
        if after is not None:
            payload['after'] = resolve_id(after)
        if sort is not None:
            payload['sort'] = sort.value
        if populate_users is not None:
            payload['include_users'] = populate_users

        resp: raw.BulkMessageResponse = await self.request(
            routes.CHANNELS_MESSAGE_SEARCH.compile(channel_id=resolve_id(channel)),
            json=payload,
        )
        return self.state.parser.parse_messages(resp)

    async def send_message(
        self,
        channel: ULIDOr[TextableChannel],
        content: typing.Optional[str] = None,
        *,
        nonce: typing.Optional[str] = None,
        attachments: typing.Optional[list[ResolvableResource]] = None,
        replies: typing.Optional[list[typing.Union[Reply, ULIDOr[BaseMessage]]]] = None,
        embeds: typing.Optional[list[SendableEmbed]] = None,
        masquerade: typing.Optional[Masquerade] = None,
        interactions: typing.Optional[MessageInteractions] = None,
        silent: typing.Optional[bool] = None,
        mention_everyone: typing.Optional[bool] = None,
        mention_online: typing.Optional[bool] = None,
    ) -> Message:
        """|coro|

        Sends a message to the given channel.

        You must have :attr:`~Permissions.send_messages` to do this.

        If message mentions '@everyone' or '@here', you must have :attr:`~Permissions.mention_everyone` to do that.
        If message mentions any roles, you must :attr:`~Permission.mention_roles` to do that.

        Parameters
        ----------
        channel: ULIDOr[:class:`.TextableChannel`]
            The destination channel.
        content: Optional[:class:`str`]
            The message content.
        nonce: Optional[:class:`str`]
            The message nonce.
        attachments: Optional[List[:class:`.ResolvableResource`]]
            The attachments to send the message with.

            You must have :attr:`~Permissions.upload_files` to provide this.
        replies: Optional[List[Union[:class:`.Reply`, ULIDOr[:class:`.BaseMessage`]]]]
            The message replies.
        embeds: Optional[List[:class:`.SendableEmbed`]]
            The embeds to send the message with.

            You must have :attr:`~Permissions.send_embeds` to provide this.
        masquearde: Optional[:class:`.Masquerade`]
            The message masquerade.

            You must have :attr:`~Permissions.use_masquerade` to provide this.

            If :attr:`.Masquerade.color` is provided, :attr:`~Permissions.use_masquerade` is also required.
        interactions: Optional[:class:`.MessageInteractions`]
            The message interactions.

            If :attr:`.MessageInteractions.reactions` is provided, :attr:`~Permissions.react` is required.
        silent: Optional[:class:`bool`]
            Whether to suppress notifications or not.
        mention_everyone: Optional[:class:`bool`]
            Whether to mention all users who can see the channel. This cannot be mixed with ``mention_online`` parameter.

            .. note::

                User accounts cannot set this to ``True``.
        mention_online: Optional[:class:`bool`]
            Whether to mention all users who are online and can see the channel. This cannot be mixed with ``mention_everyone`` parameter.

            .. note::

                User accounts cannot set this to ``True``.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +------------------------+--------------------------------------------------------------------------------------------------------------------+
            | Value                  | Reason                                                                                                             |
            +------------------------+--------------------------------------------------------------------------------------------------------------------+
            | ``EmptyMessage``       | The message was empty.                                                                                             |
            +------------------------+--------------------------------------------------------------------------------------------------------------------+
            | ``FailedValidation``   | The payload was invalid.                                                                                           |
            +------------------------+--------------------------------------------------------------------------------------------------------------------+
            | ``InvalidFlagValue``   | Both ``mention_everyone`` and ``mention_online`` were ``True``.                                                    |
            +------------------------+--------------------------------------------------------------------------------------------------------------------+
            | ``InvalidOperation``   | The passed nonce was already used. One of :attr:`.MessageInteractions.reactions` elements was invalid.             |
            +------------------------+--------------------------------------------------------------------------------------------------------------------+
            | ``InvalidProperty``    | :attr:`.MessageInteractions.restrict_reactions` was ``True`` and :attr:`.MessageInteractions.reactions` was empty. |
            +------------------------+--------------------------------------------------------------------------------------------------------------------+
            | ``IsBot``              | The current token belongs to bot account.                                                                          |
            +------------------------+--------------------------------------------------------------------------------------------------------------------+
            | ``IsNotBot``           | The current token belongs to user account.                                                                         |
            +------------------------+--------------------------------------------------------------------------------------------------------------------+
            | ``PayloadTooLarge``    | The message was too large.                                                                                         |
            +------------------------+--------------------------------------------------------------------------------------------------------------------+
            | ``TooManyAttachments`` | You provided more attachments than allowed on this instance.                                                       |
            +------------------------+--------------------------------------------------------------------------------------------------------------------+
            | ``TooManyEmbeds``      | You provided more embeds than allowed on this instance.                                                            |
            +------------------------+--------------------------------------------------------------------------------------------------------------------+
            | ``TooManyReplies``     | You was replying to more messages than was allowed on this instance.                                               |
            +------------------------+--------------------------------------------------------------------------------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+----------------------------------------------------------+
            | Value                 | Reason                                                   |
            +-----------------------+----------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to send messages. |
            +-----------------------+----------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+---------------------------------------+
            | Value        | Reason                                |
            +--------------+---------------------------------------+
            | ``NotFound`` | The channel/file/reply was not found. |
            +--------------+---------------------------------------+
        :class:`Conflict`
            Possible values for :attr:`~HTTPException.type`:

            +---------------------+-------------------------------+
            | Value               | Reason                        |
            +---------------------+-------------------------------+
            | ``AlreadyInGroup``  | The bot is already in group.  |
            +---------------------+-------------------------------+
            | ``AlreadyInServer`` | The bot is already in server. |
            +---------------------+-------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+-------------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                                | Populated attributes                                                |
            +-------------------+-------------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database.        | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+-------------------------------------------------------+---------------------------------------------------------------------+
            | ``InternalError`` | Somehow something went wrong during message creation. |                                                                     |
            +-------------------+-------------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`Message`
            The message that was sent.
        """
        payload: raw.DataMessageSend = {}
        if content is not None:
            payload['content'] = content
        if attachments is not None:
            payload['attachments'] = [
                await resolve_resource(self.state, attachment, tag='attachments') for attachment in attachments
            ]
        if replies is not None:
            payload['replies'] = [
                (reply.build() if isinstance(reply, Reply) else {'id': resolve_id(reply), 'mention': False})
                for reply in replies
            ]
        if embeds is not None:
            payload['embeds'] = [await embed.build(self.state) for embed in embeds]
        if masquerade is not None:
            payload['masquerade'] = masquerade.build()
        if interactions is not None:
            payload['interactions'] = interactions.build()

        flags = None

        if silent is not None:
            if flags is None:
                flags = 0

            if silent:
                flags |= MessageFlags.suppress_notifications.value

        if mention_everyone is not None:
            if flags is None:
                flags = 0

            if mention_everyone:
                flags |= MessageFlags.mention_everyone.value

        if mention_online is not None:
            if flags is None:
                flags = 0

            if mention_online:
                flags |= MessageFlags.mention_online.value

        if flags is not None:
            payload['flags'] = flags

        headers = {}
        if nonce is not None:
            headers['Idempotency-Key'] = nonce

        resp: raw.Message = await self.request(
            routes.CHANNELS_MESSAGE_SEND.compile(channel_id=resolve_id(channel)),
            json=payload,
            headers=headers,
        )
        return self.state.parser.parse_message(resp)

    async def unpin_message(self, channel: ULIDOr[TextableChannel], message: ULIDOr[BaseMessage], /) -> None:
        """|coro|

        Unpins a message.
        You must have :attr:`~Permissions.manage_messages` to do this.

        Parameters
        ----------
        channel: ULIDOr[:class:`.TextableChannel`]
            The channel.
        message: ULIDOr[:class:`.BaseMessage`]
            The message.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +---------------+-----------------------------+
            | Value         | Reason                      |
            +---------------+-----------------------------+
            | ``NotPinned`` | The message was not pinned. |
            +---------------+-----------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+--------------------------------------------------------------+
            | Value                 | Reason                                                       |
            +-----------------------+--------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to unpin the message. |
            +-----------------------+--------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+------------------------------------+
            | Value        | Reason                             |
            +--------------+------------------------------------+
            | ``NotFound`` | The channel/message was not found. |
            +--------------+------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """
        await self.request(
            routes.CHANNELS_MESSAGE_PIN.compile(
                channel_id=resolve_id(channel),
                message_id=resolve_id(message),
            )
        )

    async def remove_reactions_from_message(
        self,
        channel: ULIDOr[TextableChannel],
        message: ULIDOr[BaseUser],
        emoji: ResolvableEmoji,
        *,
        user: typing.Optional[ULIDOr[BaseUser]] = None,
        remove_all: typing.Optional[bool] = None,
    ) -> None:
        """|coro|

        Remove your own, someone else's or all of a given reaction.

        You must have :attr:`~Permissions.react` to do this.

        Parameters
        ----------
        channel: ULIDOr[:class:`.TextableChannel`]
            The channel.
        message: ULIDOr[:class:`.BaseMessage`]
            The message.
        emoji: :class:`.ResolvableEmoji`
            The emoji to remove.
        user: Optional[ULIDOr[:class:`.BaseUser`]]
            The user to remove reactions from.

            You must have :attr:`~Permissions.manage_messages` to provide this.
        remove_all: Optional[:class:`bool`]
            Whether to remove all reactions.

            You must have :attr:`~Permissions.manage_messages` to provide this.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:
            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+------------------------------------------------------------+
            | Value                 | Reason                                                     |
            +-----------------------+------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to remove reaction. |
            +-----------------------+------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+------------------------------------+
            | Value        | Reason                             |
            +--------------+------------------------------------+
            | ``NotFound`` | One of these:                      |
            |              |                                    |
            |              | - The channel was not found.       |
            |              | - The message was not found.       |
            |              | - The user provided did not react. |
            +--------------+------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """
        params: raw.OptionsUnreact = {}
        if user is not None:
            params['user_id'] = resolve_id(user)
        if remove_all is not None:
            params['remove_all'] = utils._bool(remove_all)
        await self.request(
            routes.CHANNELS_MESSAGE_UNREACT.compile(
                channel_id=resolve_id(channel),
                message_id=resolve_id(message),
                emoji=resolve_emoji(emoji),
            ),
            params=params,
        )

    async def set_channel_permissions_for_role(
        self,
        channel: ULIDOr[ServerChannel],
        role: ULIDOr[BaseRole],
        *,
        allow: Permissions = Permissions.none(),
        deny: Permissions = Permissions.none(),
    ) -> ServerChannel:
        """|coro|

        Sets permissions for the specified role in a channel.

        You must have :attr:`~Permissions.manage_permissions` to do this.

        The provided channel must be a :class:`.ServerChannel`.

        Parameters
        ----------
        channel: ULIDOr[:class:`.ServerChannel`]
            The channel.
        role: ULIDOr[:class:`.BaseRole`]
            The role.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------+----------------------------------------------+
            | Value                | Reason                                       |
            +----------------------+----------------------------------------------+
            | ``InvalidOperation`` | The provided channel was not server channel. |
            +----------------------+----------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------------------+--------------------------------------------------------------------------------------+
            | Value                            | Reason                                                                               |
            +----------------------------------+--------------------------------------------------------------------------------------+
            | ``CannotGiveMissingPermissions`` | Your new provided permissions contained permissions you didn't have.                 |
            +----------------------------------+--------------------------------------------------------------------------------------+
            | ``NotElevated``                  | Rank of your top role is higher than rank of role you're trying to set override for. |
            +----------------------------------+--------------------------------------------------------------------------------------+
            | ``MissingPermission``            | You do not have the proper permissions to remove reaction.                           |
            +----------------------------------+--------------------------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+----------------------------------------+
            | Value        | Reason                                 |
            +--------------+----------------------------------------+
            | ``NotFound`` | The channel/server/role was not found. |
            +--------------+----------------------------------------+

        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`.ServerChannel`
            The updated server channel with new permissions.
        """
        payload: raw.DataSetRolePermissions = {'permissions': {'allow': allow.value, 'deny': deny.value}}
        resp: typing.Union[raw.TextChannel, raw.VoiceChannel] = await self.request(
            routes.CHANNELS_PERMISSIONS_SET.compile(
                channel_id=resolve_id(channel),
                role_id=resolve_id(role),
            ),
            json=payload,
        )
        ret = self.state.parser.parse_channel(resp)
        return ret

    @typing.overload
    async def set_default_channel_permissions(
        self,
        channel: ULIDOr[GroupChannel],
        permissions: Permissions,
    ) -> GroupChannel: ...

    @typing.overload
    async def set_default_channel_permissions(
        self,
        channel: ULIDOr[ServerChannel],
        permissions: PermissionOverride,
    ) -> ServerChannel: ...

    async def set_default_channel_permissions(
        self,
        channel: ULIDOr[typing.Union[GroupChannel, ServerChannel]],
        permissions: typing.Union[Permissions, PermissionOverride],
    ) -> typing.Union[GroupChannel, ServerChannel]:
        """|coro|

        Sets default permissions for everyone in a channel.

        You must have :attr:`~Permissions.manage_permissions` to do this.

        Channel must be a :class:`GroupChannel`, or :class:`.ServerChannel`.

        Parameters
        ----------
        channel: ULIDOr[Union[:class:`.GroupChannel`, :class:`.ServerChannel`]]
            The channel to set default permissions in.
        permissions: Union[:class:`.Permissions`, :class:`.PermissionOverride`]
            The new permissions. Must be :class:`.Permissions` for groups and :class:`.PermissionOverride` for server channels.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------+----------------------------------------------------------+
            | Value                | Reason                                                   |
            +----------------------+----------------------------------------------------------+
            | ``InvalidOperation`` | One of these:                                            |
            |                      |                                                          |
            |                      | - You provided :class:`.PermissionOverride` for group.   |
            |                      | - You provided :class:`.Permissions` for server channel. |
            |                      | - The provided channel was not group/server channel.     |
            +----------------------+----------------------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------------------+--------------------------------------------------------------------------------------+
            | Value                            | Reason                                                                               |
            +----------------------------------+--------------------------------------------------------------------------------------+
            | ``CannotGiveMissingPermissions`` | Your new provided permissions contained permissions you didn't have.                 |
            +----------------------------------+--------------------------------------------------------------------------------------+
            | ``NotElevated``                  | Rank of your top role is higher than rank of role you're trying to set override for. |
            +----------------------------------+--------------------------------------------------------------------------------------+
            | ``MissingPermission``            | You do not have the proper permissions to remove reaction.                           |
            +----------------------------------+--------------------------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+----------------------------+
            | Value        | Reason                     |
            +--------------+----------------------------+
            | ``NotFound`` | The channel was not found. |
            +--------------+----------------------------+

        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        Union[:class:`GroupChannel`, :class:`ServerChannel`]
            The updated group/server channel with new permissions.
        """
        payload: raw.DataDefaultChannelPermissions = {
            'permissions': (permissions.build() if isinstance(permissions, PermissionOverride) else permissions.value)
        }
        resp: raw.Channel = await self.request(
            routes.CHANNELS_PERMISSIONS_SET_DEFAULT.compile(channel_id=resolve_id(channel)),
            json=payload,
        )
        r = self.state.parser.parse_channel(resp)
        return r  # type: ignore

    async def join_call(self, channel: ULIDOr[typing.Union[DMChannel, GroupChannel, TextChannel, VoiceChannel]]) -> str:
        """|coro|

        Asks the voice server for a token to join the call.

        You must have :attr:`~Permissions.connect` to do this.

        Parameters
        ----------
        channel: ULIDOr[Union[:class:`.DMChannel`, :class:`.GroupChannel`, :class:`.TextChannel`, :class:`.VoiceChannel`]]
            The channel to join a call in.

            If current instance uses legacy voice server (determined by
            whether :attr:`InstanceFeaturesConfig.livekit_voice` is ``False``), then
            a channel with type of :attr:`~ChannelType.text` cannot be passed and
            will raise :class:`HTTPException` with ``CannotJoinCall`` type.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +---------------------------+-----------------------------------------------------------------------------------------------------------------------------------+
            | Value                     | Reason                                                                                                                            |
            +---------------------------+-----------------------------------------------------------------------------------------------------------------------------------+
            | ``AlreadyConnected``      | The current user was already connected to this voice channel.                                                                     |
            +---------------------------+-----------------------------------------------------------------------------------------------------------------------------------+
            | ``AlreadyInVoiceChannel`` | The current user was already connected to other voice channel.                                                                    |
            +---------------------------+-----------------------------------------------------------------------------------------------------------------------------------+
            | ``CannotJoinCall``        | The channel was type of :attr:`~ChannelType.saved_messages` (or if instance uses legacy voice server, :attr:`~ChannelType.text`). |
            +---------------------------+-----------------------------------------------------------------------------------------------------------------------------------+
            | ``InvalidOperation``      | The voice server is unavailable.                                                                                                  |
            +---------------------------+-----------------------------------------------------------------------------------------------------------------------------------+
            | ``NotAVoiceChannel``      | ???. Only applicable to instances using Livekit                                                                                   |
            +---------------------------+-----------------------------------------------------------------------------------------------------------------------------------+
            | ``VosoUnavailable``       | The voice server is unavailable.                                                                                                  |
            +---------------------------+-----------------------------------------------------------------------------------------------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------------------+--------------------------------------------------------+
            | Value                            | Reason                                                 |
            +----------------------------------+--------------------------------------------------------+
            | ``MissingPermission``            | You do not have the proper permissions to join a call. |
            +----------------------------------+--------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+----------------------------+
            | Value        | Reason                     |
            +--------------+----------------------------+
            | ``NotFound`` | The channel was not found. |
            +--------------+----------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+-------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                          | Populated attributes                                                |
            +-------------------+-------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database.  | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+-------------------------------------------------+---------------------------------------------------------------------+
            | ``InternalError`` | Somehow something went during retrieving token. |                                                                     |
            +-------------------+-------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`str`
            The token for authenticating with the voice server.
        """
        resp: raw.CreateVoiceUserResponse = await self.request(
            routes.CHANNELS_VOICE_JOIN.compile(channel_id=resolve_id(channel))
        )
        return resp['token']

    async def create_webhook(
        self,
        channel: ULIDOr[typing.Union[GroupChannel, TextChannel]],
        *,
        name: str,
        avatar: typing.Optional[ResolvableResource] = None,
    ) -> Webhook:
        """|coro|

        Creates a webhook which 3rd party platforms can use to send.

        You must have :attr:`~Permissions.manage_webhooks` permission to do this.

        Parameters
        ----------
        channel: ULIDOr[Union[:class:`.GroupChannel`, :class:`.TextChannel`]]
            The channel to create webhook in.
        name: :class:`str`
            The webhook name. Must be between 1 and 32 chars long.
        avatar: Optional[:class:`.ResolvableResource`]
            The webhook avatar.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +---------------------------+--------------------------------------------------------------------------------------+
            | Value                     | Reason                                                                               |
            +---------------------------+--------------------------------------------------------------------------------------+
            | ``InvalidOperation``      | The channel was not type of :attr:`~ChannelType.group` or :attr:`~ChannelType.text`. |
            +---------------------------+--------------------------------------------------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------------------+-------------------------------------------------------------+
            | Value                            | Reason                                                      |
            +----------------------------------+-------------------------------------------------------------+
            | ``MissingPermission``            | You do not have the proper permissions to create a webhook. |
            +----------------------------------+-------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+---------------------------------+
            | Value        | Reason                          |
            +--------------+---------------------------------+
            | ``NotFound`` | The channel/file was not found. |
            +--------------+---------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`.Webhook`
            The created webhook.
        """
        payload: raw.CreateWebhookBody = {'name': name}
        if avatar is not None:
            payload['avatar'] = await resolve_resource(self.state, avatar, tag='avatars')
        resp: raw.Webhook = await self.request(
            routes.CHANNELS_WEBHOOK_CREATE.compile(channel_id=resolve_id(channel)),
            json=payload,
        )
        return self.state.parser.parse_webhook(resp)

    async def get_channel_webhooks(self, channel: ULIDOr[ServerChannel]) -> list[Webhook]:
        """|coro|

        Retrieves all webhooks in a channel.

        You must have :attr:`~Permissions.manage_webhooks` permission to do this.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +---------------------------+--------------------------------------------------------------------------------------+
            | Value                     | Reason                                                                               |
            +---------------------------+--------------------------------------------------------------------------------------+
            | ``InvalidOperation``      | The channel was not type of :attr:`~ChannelType.group` or :attr:`~ChannelType.text`. |
            +---------------------------+--------------------------------------------------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------------------+--------------------------------------------------------------------------------------+
            | Value                            | Reason                                                                               |
            +----------------------------------+--------------------------------------------------------------------------------------+
            | ``MissingPermission``            | You do not have the proper permissions to view webhooks that belong to this channel. |
            +----------------------------------+--------------------------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+----------------------------+
            | Value        | Reason                     |
            +--------------+----------------------------+
            | ``NotFound`` | The channel was not found. |
            +--------------+----------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        List[:class:`.Webhook`]
            The webhooks for this channel.
        """
        resp: list[raw.Webhook] = await self.request(
            routes.CHANNELS_WEBHOOK_FETCH_ALL.compile(channel_id=resolve_id(channel))
        )
        return list(map(self.state.parser.parse_webhook, resp))

    # Customization control (emojis)
    async def create_server_emoji(
        self,
        server: ULIDOr[BaseServer],
        *,
        name: str,
        nsfw: typing.Optional[bool] = None,
        image: ResolvableResource,
    ) -> ServerEmoji:
        """|coro|

        Creates an emoji in server.

        You must have :attr:`~Permissions.manage_customization` to do this.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        server: ULIDOr[:class:`.BaseServer`]
            The server.
        name: :class:`str`
            The emoji name. Must be between 1 and 32 chars long. Can only contain ASCII digits, underscore and lowercase letters.
        nsfw: Optional[:class:`bool`]
            Whether the emoji is NSFW or not. Defaults to ``False``.
        image: :class:`.ResolvableResource`
            The emoji data.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------+---------------------------------------------------------+
            | Value                | Reason                                                  |
            +----------------------+---------------------------------------------------------+
            | ``FailedValidation`` | The payload was invalid.                                |
            +----------------------+---------------------------------------------------------+
            | ``IsBot``            | The current token belongs to bot account.               |
            +----------------------+---------------------------------------------------------+
            | ``TooManyEmoji``     | You provided more embeds than allowed on this instance. |
            +----------------------+---------------------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+-------------------------------------------------------------------+
            | Value                 | Reason                                                            |
            +-----------------------+-------------------------------------------------------------------+
            | ``MissingPermission`` | You do not have the proper permissions to create emoji in server. |
            +-----------------------+-------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+--------------------------------+
            | Value        | Reason                         |
            +--------------+--------------------------------+
            | ``NotFound`` | The server/file was not found. |
            +--------------+--------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`.ServerEmoji`
            The created emoji.
        """
        payload: raw.DataCreateEmoji = {
            'name': name,
            'parent': {
                'type': 'Server',
                'id': resolve_id(server),
            },
        }

        if nsfw is not None:
            payload['nsfw'] = nsfw

        attachment_id = await resolve_resource(self.state, image, tag='emojis')

        resp: raw.ServerEmoji = await self.request(
            routes.CUSTOMISATION_EMOJI_CREATE.compile(attachment_id=attachment_id),
            json=payload,
        )
        return self.state.parser.parse_server_emoji(resp)

    async def delete_emoji(self, emoji: ULIDOr[ServerEmoji]) -> None:
        """|coro|

        Deletes a emoji.

        You must have :attr:`~Permissions.manage_customization` to do this if you do not own
        the emoji, unless it was detached (already deleted).

        .. note::
            If deleting detached emoji, this will successfully return.

        Parameters
        ----------
        emoji: ULIDOr[:class:`.ServerEmoji`]
            The emoji to delete.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +-----------+---------------------------------------------------------+
            | Value     | Reason                                                  |
            +-----------+---------------------------------------------------------+
            | ``IsBot`` | The current token belongs to bot account.               |
            +-----------+---------------------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------------------+-----------------------------------------------------------+
            | Value                            | Reason                                                    |
            +----------------------------------+-----------------------------------------------------------+
            | ``MissingPermission``            | You do not have the proper permissions to delete a emoji. |
            +----------------------------------+-----------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+---------------------------------+
            | Value        | Reason                          |
            +--------------+---------------------------------+
            | ``NotFound`` | The emoji/server was not found. |
            +--------------+---------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """
        await self.request(routes.CUSTOMISATION_EMOJI_DELETE.compile(emoji_id=resolve_id(emoji)))

    async def get_emoji(self, emoji: ULIDOr[BaseEmoji]) -> Emoji:
        """|coro|

        Retrieves a custom emoji.

        Parameters
        ----------
        emoji: ULIDOr[:class:`.BaseEmoji`]
            The emoji to retrieve.

        Raises
        ------
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+--------------------------+
            | Value        | Reason                   |
            +--------------+--------------------------+
            | ``NotFound`` | The emoji was not found. |
            +--------------+--------------------------+

        Returns
        -------
        :class:`Emoji`
            The retrieved emoji.
        """
        resp: raw.Emoji = await self.request(
            routes.CUSTOMISATION_EMOJI_FETCH.compile(emoji_id=resolve_id(emoji)), token=None
        )
        return self.state.parser.parse_emoji(resp)

    # Invites control
    async def delete_invite(self, code: typing.Union[str, BaseInvite], /) -> None:
        """|coro|

        Deletes a invite.

        You must have :class:`~Permissions.manage_server` if deleting server invite.

        Parameters
        ----------
        code: Union[:class:`str`, :class:`.BaseInvite`]
            The invite code.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------------------+---------------------------------------------------------------+
            | Value                            | Reason                                                        |
            +----------------------------------+---------------------------------------------------------------+
            | ``MissingPermission``            | You do not have the proper permissions to delete this invite. |
            +----------------------------------+---------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+---------------------------+
            | Value        | Reason                    |
            +--------------+---------------------------+
            | ``NotFound`` | The invite was not found. |
            +--------------+---------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """
        invite_code = code.code if isinstance(code, BaseInvite) else code
        await self.request(routes.INVITES_INVITE_DELETE.compile(invite_code=invite_code))

    async def get_invite(self, code: typing.Union[str, BaseInvite], /) -> PublicInvite:
        """|coro|

        Retrieves an invite.

        Parameters
        ----------
        code: Union[:class:`str`, :class:`.BaseInvite`]
            The code to retrieve invite from.

        Raises
        ------
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+---------------------------------------+
            | Value        | Reason                                |
            +--------------+---------------------------------------+
            | ``NotFound`` | The invite/server/user was not found. |
            +--------------+---------------------------------------+

        Returns
        -------
        :class:`.PublicInvite`
            The invite retrieved.
        """
        invite_code = code.code if isinstance(code, BaseInvite) else code
        resp: raw.InviteResponse = await self.request(
            routes.INVITES_INVITE_FETCH.compile(invite_code=invite_code),
            token=None,
        )
        return self.state.parser.parse_public_invite(resp)

    async def accept_invite(self, code: typing.Union[str, BaseInvite], /) -> typing.Union[Server, GroupChannel]:
        """|coro|

        Accepts an invite.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        code: Union[:class:`str`, :class:`BaseInvite`]
            The invite code.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------+-------------------------------------------+
            | Value                | Reason                                    |
            +----------------------+-------------------------------------------+
            | ``IsBot``            | The current token belongs to bot account. |
            +----------------------+-------------------------------------------+
            | ``TooManyServers``   | You're participating in too many servers. |
            +----------------------+-------------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+-------------------------------------------------+
            | Value                 | Reason                                          |
            +-----------------------+-------------------------------------------------+
            | ``Banned``            | You're banned from server.                      |
            +-----------------------+-------------------------------------------------+
            | ``GroupTooLarge``     | The group exceeded maximum count of recipients. |
            +-----------------------+-------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+------------------------------------------+
            | Value        | Reason                                   |
            +--------------+------------------------------------------+
            | ``NotFound`` | The invite/channel/server was not found. |
            +--------------+------------------------------------------+
        :class:`Conflict`
            Possible values for :attr:`~HTTPException.type`:

            +---------------------+--------------------------------+
            | Value               | Reason                         |
            +---------------------+--------------------------------+
            | ``AlreadyInGroup``  | The user is already in group.  |
            +---------------------+--------------------------------+
            | ``AlreadyInServer`` | The user is already in server. |
            +---------------------+--------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        Union[:class:`.Server`, :class:`.GroupChannel`]
            The joined server or group.
        """
        invite_code = code.code if isinstance(code, BaseInvite) else code
        resp: raw.InviteJoinResponse = await self.request(routes.INVITES_INVITE_JOIN.compile(invite_code=invite_code))
        if resp['type'] == 'Server':
            return self.state.parser.parse_server(
                resp['server'],
                (False, resp['channels']),
            )
        elif resp['type'] == 'Group':
            recipients = list(map(self.state.parser.parse_user, resp['users']))

            return self.state.parser.parse_group_channel(
                resp['channel'],
                (False, recipients),
            )
        else:
            raise NotImplementedError(resp)

    # Onboarding control
    async def complete_onboarding(self, username: str, /) -> OwnUser:
        """|coro|

        Complete onboarding by setting up an username, and allow connections to WebSocket.

        Parameters
        ----------
        username: :class:`str`
            The username to use. Must be between 2 and 32 characters and not contain whitespace characters.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------+--------------------------+
            | Value                | Reason                   |
            +----------------------+--------------------------+
            | ``FailedValidation`` | The payload was invalid. |
            +----------------------+--------------------------+
            | ``InvalidUsername``  | The username is invalid. |
            +----------------------+--------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+------------------------------------+
            | Value              | Reason                             |
            +--------------------+------------------------------------+
            | ``InvalidSession`` | The current user token is invalid. |
            +--------------------+------------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+-------------------------------------------------+
            | Value                 | Reason                                          |
            +-----------------------+-------------------------------------------------+
            | ``AlreadyOnboarded``  | You already completed onboarding.
            +-----------------------+-------------------------------------------------+
        :class:`Conflict`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+-------------------------+
            | Value             | Reason                  |
            +-------------------+-------------------------+
            | ``UsernameTaken`` | The username was taken. |
            +-------------------+-------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        :class:`.OwnUser`
            The updated user.
        """
        payload: raw.DataOnboard = {'username': username}
        resp: raw.User = await self.request(routes.ONBOARD_COMPLETE.compile(), json=payload)
        return self.state.parser.parse_own_user(resp)

    async def onboarding_status(self) -> bool:
        """|coro|

        Determines whether the current session requires to complete onboarding.

        You may skip calling this if you're restoring from an existing session.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+------------------------------------+
            | Value              | Reason                             |
            +--------------------+------------------------------------+
            | ``InvalidSession`` | The current user token is invalid. |
            +--------------------+------------------------------------+

        Returns
        -------
        :class:`bool`
            Whether the onboarding is completed.
        """
        d: raw.DataHello = await self.request(routes.ONBOARD_HELLO.compile())
        return d['onboarding']

    # Web Push control
    async def push_subscribe(self, *, endpoint: str, p256dh: str, auth: str) -> None:
        """|coro|

        Create a new Web Push subscription. If an subscription already exists on this session, it will be removed.

        Parameters
        ----------
        endpoint: :class:`str`
            The HTTP `endpoint <https://developer.mozilla.org/en-US/docs/Web/API/PushSubscription/endpoint>`_ associated with push subscription.
        p256dh: :class:`str`
            The `Elliptic curve Diffie–Hellman public key on the P-256 curve <https://developer.mozilla.org/en-US/docs/Web/API/PushSubscription/getKey#p256dh>`_.
        auth: :class:`str`
            The `authentication secret <https://developer.mozilla.org/en-US/docs/Web/API/PushSubscription/getKey#auth>`_.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+------------------------------------+
            | Value              | Reason                             |
            +--------------------+------------------------------------+
            | ``InvalidSession`` | The current user token is invalid. |
            +--------------------+------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+----------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                           |
            +-------------------+------------------------------------------------+----------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.operation`, :attr:`~HTTPException.with_` |
            +-------------------+------------------------------------------------+----------------------------------------------------------------+
        """
        payload: raw.a.WebPushSubscription = {
            'endpoint': endpoint,
            'p256dh': p256dh,
            'auth': auth,
        }
        await self.request(
            routes.PUSH_SUBSCRIBE.compile(),
            json=payload,
        )

    async def unsubscribe(self) -> None:
        """|coro|

        Remove the Web Push subscription associated with the current session.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+------------------------------------+
            | Value              | Reason                             |
            +--------------------+------------------------------------+
            | ``InvalidSession`` | The current user token is invalid. |
            +--------------------+------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+----------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                           |
            +-------------------+------------------------------------------------+----------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.operation`, :attr:`~HTTPException.with_` |
            +-------------------+------------------------------------------------+----------------------------------------------------------------+
        """
        await self.request(routes.PUSH_UNSUBSCRIBE.compile())

    # Safety control
    async def _report_content(self, payload: raw.DataReportContent, /) -> None:
        await self.request(routes.SAFETY_REPORT_CONTENT.compile(), json=payload)

    async def report_message(
        self,
        message: ULIDOr[BaseMessage],
        reason: ContentReportReason,
        *,
        additional_context: typing.Optional[str] = None,
    ) -> None:
        """|coro|

        Report a message to the instance moderation team.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        message: ULIDOr[:class:`.BaseMessage`]
            The message to report.
        reason: :class:`.ContentReportReason`
            The reason for reporting.
        additional_context: Optional[:class:`str`]
            The additional context for moderation team. Can be only up to 1000 characters.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------------+---------------------------------------+
            | Value                    | Reason                                |
            +--------------------------+---------------------------------------+
            | ``CannotReportYourself`` | You tried to report your own message. |
            +--------------------------+---------------------------------------+
            | ``FailedValidation``     | The payload was invalid.              |
            +--------------------------+---------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+----------------------------+
            | Value        | Reason                     |
            +--------------+----------------------------+
            | ``NotFound`` | The message was not found. |
            +--------------+----------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """
        payload: raw.DataReportContent = {
            'content': {
                'type': 'Message',
                'id': resolve_id(message),
                'report_reason': reason.value,
            }
        }
        if additional_context is not None:
            payload['additional_context'] = additional_context
        await self._report_content(payload)

    async def report_server(
        self,
        server: ULIDOr[BaseServer],
        reason: ContentReportReason,
        *,
        additional_context: typing.Optional[str] = None,
    ) -> None:
        """|coro|

        Report a server to the instance moderation team.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        server: ULIDOr[:class:`.BaseServer`]
            The server to report.
        reason: :class:`.ContentReportReason`
            The reason for reporting.
        additional_context: Optional[:class:`str`]
            The additional context for moderation team. Can be only up to 1000 characters.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------------+---------------------------------------+
            | Value                    | Reason                                |
            +--------------------------+---------------------------------------+
            | ``CannotReportYourself`` | You tried to report your own server. |
            +--------------------------+--------------------------------------+
            | ``FailedValidation``     | The payload was invalid.             |
            +--------------------------+--------------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+---------------------------+
            | Value        | Reason                    |
            +--------------+---------------------------+
            | ``NotFound`` | The server was not found. |
            +--------------+---------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """
        payload: raw.DataReportContent = {
            'content': {
                'type': 'Server',
                'id': resolve_id(server),
                'report_reason': reason.value,
            }
        }
        if additional_context is not None:
            payload['additional_context'] = additional_context
        await self._report_content(payload)

    async def report_user(
        self,
        user: ULIDOr[BaseUser],
        reason: UserReportReason,
        *,
        additional_context: typing.Optional[str] = None,
        message_context: typing.Optional[ULIDOr[BaseMessage]] = None,
    ) -> None:
        """|coro|

        Report an user to the instance moderation team.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        server: ULIDOr[:class:`.BaseServer`]
            The server to report.
        reason: :class:`.UserReportReason`
            The reason for reporting user.
        additional_context: Optional[:class:`str`]
            The additional context for moderation team. Can be only up to 1000 characters.
        message_context: Optional[ULIDOr[:class:`.BaseMessage`]]
            The message context.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------------+-------------------------------+
            | Value                    | Reason                        |
            +--------------------------+-------------------------------+
            | ``CannotReportYourself`` | You tried to report yourself. |
            +--------------------------+-------------------------------+
            | ``FailedValidation``     | The payload was invalid.      |
            +--------------------------+-------------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+---------------------------------+
            | Value        | Reason                          |
            +--------------+---------------------------------+
            | ``NotFound`` | The user/message was not found. |
            +--------------+---------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """
        content: raw.UserReportedContent = {
            'type': 'User',
            'id': resolve_id(user),
            'report_reason': reason.value,
        }

        if message_context is not None:
            content['message_id'] = resolve_id(message_context)

        payload: raw.DataReportContent = {'content': content}
        if additional_context is not None:
            payload['additional_context'] = additional_context

        await self._report_content(payload)

    # Servers control
    async def ban(
        self,
        server: ULIDOr[BaseServer],
        user: str | BaseUser | BaseMember,
        /,
        *,
        reason: typing.Optional[str] = None,
    ) -> Ban:
        """|coro|

        Bans a user from the server.

        Parameters
        ----------
        server: ULIDOr[:class:`BaseServer`]
            The server.
        user: Union[:class:`str`, :class:`BaseUser`, :class:`BaseMember`]
            The user to ban from the server.
        reason: Optional[:class:`str`]
            The ban reason. Should be between 1 and 1024 chars long.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to ban the user.
        :class:`HTTPException`
            Banning the user failed.
        """
        payload: raw.DataBanCreate = {'reason': reason}
        response: raw.ServerBan = await self.request(
            routes.SERVERS_BAN_CREATE.compile(server_id=resolve_id(server), user_id=_resolve_member_id(user)),
            json=payload,
        )
        return self.state.parser.parse_ban(
            response,
            {},
        )

    async def get_bans(self, server: ULIDOr[BaseServer], /) -> list[Ban]:
        """|coro|

        Retrieves all bans on a server.

        Parameters
        ----------
        server: ULIDOr[:class:`BaseServer`]
            The server.

        Returns
        -------
        List[:class:`Ban`]
            The ban entries.
        """
        resp: raw.BanListResult = await self.request(routes.SERVERS_BAN_LIST.compile(server_id=resolve_id(server)))
        return self.state.parser.parse_bans(resp)

    async def unban(self, server: ULIDOr[BaseServer], user: ULIDOr[BaseUser]) -> None:
        """|coro|

        Unbans a user from the server.

        Parameters
        ----------
        server: ULIDOr[:class:`BaseServer`]
            The server.
        user: ULIDOr[:class:`BaseUser`]
            The user to unban from the server.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to unban the user.
        :class:`HTTPException`
            Unbanning the user failed.
        """
        await self.request(
            routes.SERVERS_BAN_REMOVE.compile(server_id=resolve_id(server), user_id=resolve_id(user)),
        )

    @typing.overload
    async def create_server_channel(
        self,
        server: ULIDOr[BaseServer],
        /,
        *,
        type: typing.Literal[ChannelType.text] = ...,
        name: str,
        description: typing.Optional[str] = ...,
        nsfw: typing.Optional[bool] = ...,
    ) -> TextChannel: ...

    @typing.overload
    async def create_server_channel(
        self,
        server: ULIDOr[BaseServer],
        /,
        *,
        type: None = ...,
        name: str,
        description: typing.Optional[str] = ...,
        nsfw: typing.Optional[bool] = ...,
    ) -> TextChannel: ...

    @typing.overload
    async def create_server_channel(
        self,
        server: ULIDOr[BaseServer],
        /,
        *,
        type: typing.Literal[ChannelType.voice] = ...,
        name: str,
        description: typing.Optional[str] = ...,
        nsfw: typing.Optional[bool] = ...,
    ) -> VoiceChannel: ...

    @typing.overload
    async def create_server_channel(
        self,
        server: ULIDOr[BaseServer],
        /,
        *,
        type: ChannelType = ...,
        name: str,
        description: typing.Optional[str] = ...,
        nsfw: typing.Optional[bool] = ...,
    ) -> typing.NoReturn: ...

    async def create_server_channel(
        self,
        server: ULIDOr[BaseServer],
        /,
        *,
        type: typing.Optional[ChannelType] = None,
        name: str,
        description: typing.Optional[str] = None,
        nsfw: typing.Optional[bool] = None,
    ) -> ServerChannel:
        """|coro|

        Create a new text or voice channel within server.

        Parameters
        ----------
        type: Optional[:class:`ChannelType`]
            The channel type. Defaults to :attr:`ChannelType.text` if not provided.
        name: :class:`str`
            The channel name.
        description: Optional[:class:`str`]
            The channel description.
        nsfw: Optional[:class:`bool`]
            To mark channel as NSFW or not.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to create the channel.
        :class:`HTTPException`
            Creating the channel failed.
        """

        if type not in (ChannelType.text, ChannelType.voice, None):
            raise TypeError('Cannot create non-text/voice channels')

        payload: raw.DataCreateServerChannel = {'name': name}
        if type is not None:
            payload['type'] = type.value
        if description is not None:
            payload['description'] = description
        if nsfw is not None:
            payload['nsfw'] = nsfw
        resp: raw.ServerChannel = await self.request(
            routes.SERVERS_CHANNEL_CREATE.compile(server_id=resolve_id(server)),
            json=payload,
        )
        return self.state.parser.parse_channel(resp)

    async def get_server_emojis(self, server: ULIDOr[BaseServer]) -> list[ServerEmoji]:
        """|coro|

        Retrieves all custom :class:`ServerEmoji`'s from the server.

        Parameters
        ----------
        server: ULIDOr[:class:`BaseServer`]
            The server.

        Returns
        -------
        List[:class:`ServerEmoji`]
            The retrieved emojis.
        """
        resp: list[raw.ServerEmoji] = await self.request(
            routes.SERVERS_EMOJI_LIST.compile(server_id=resolve_id(server))
        )
        return list(map(self.state.parser.parse_server_emoji, resp))

    async def get_server_invites(self, server: ULIDOr[BaseServer], /) -> list[ServerInvite]:
        """|coro|

        Returns a list of all invites from the server.

        Parameters
        ----------
        server: ULIDOr[:class:`BaseServer`]
            The server.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to manage the server.
        :class:`HTTPException`
            Getting the invites failed.

        Returns
        -------
        List[:class:`ServerInvite`]
            The retrieved invites.
        """
        resp: list[raw.ServerInvite] = await self.request(
            routes.SERVERS_INVITES_FETCH.compile(server_id=resolve_id(server))
        )
        return list(map(self.state.parser.parse_server_invite, resp))

    async def edit_member(
        self,
        server: ULIDOr[BaseServer],
        member: str | BaseUser | BaseMember,
        /,
        *,
        nick: UndefinedOr[typing.Optional[str]] = UNDEFINED,
        avatar: UndefinedOr[ResolvableResource | None] = UNDEFINED,
        roles: UndefinedOr[list[ULIDOr[BaseRole]] | None] = UNDEFINED,
        timeout: UndefinedOr[datetime | timedelta | float | int | None] = UNDEFINED,
        can_publish: UndefinedOr[bool | None] = UNDEFINED,
        can_receive: UndefinedOr[bool | None] = UNDEFINED,
        voice: UndefinedOr[ULIDOr[DMChannel | GroupChannel | TextChannel | VoiceChannel]] = UNDEFINED,
    ) -> Member:
        """|coro|

        Edits the member.

        Parameters
        ----------
        server: :class:`BaseServer`
            The server.
        member: Union[:class:`str`, :class:`BaseUser`, :class:`BaseMember`]
            The member.
        nick: UndefinedOr[Optional[:class:`str`]]
            The member's new nick. Use ``None`` to remove the nickname.
        avatar: UndefinedOr[Optional[:class:`.ResolvableResource`]]
            The member's new avatar. Use ``None`` to remove the avatar. You can only change your own server avatar.
        roles: UndefinedOr[Optional[List[ULIDOr[:class:`.BaseRole`]]]]
            The member's new list of roles. This *replaces* the roles.
        timeout: UndefinedOr[Optional[Union[:class:`datetime`, :class:`timedelta`, :class:`float`, :class:`int`]]]
            The duration/date the member's timeout should expire, or ``None`` to remove the timeout.
            This must be a timezone-aware datetime object. Consider using :func:`utils.utcnow()`.
        can_publish: UndefinedOr[Optional[:class:`bool`]]
            Whether the member should send voice data.
        can_receive: UndefinedOr[Optional[:class:`bool`]]
            Whether the member should receive voice data.
        voice: UndefinedOr[ULIDOr[Union[:class:`.DMChannel`, :class:`.GroupChannel`, :class:`.TextChannel`, :class:`.VoiceChannel`]]]
            The voice channel to move the member to.

        Returns
        -------
        :class:`Member`
            The newly updated member.
        """
        payload: raw.DataMemberEdit = {}
        remove: list[raw.FieldsMember] = []
        if nick is not UNDEFINED:
            if nick is None:
                remove.append('Nickname')
            else:
                payload['nickname'] = nick
        if avatar is not UNDEFINED:
            if avatar is not None:
                payload['avatar'] = await resolve_resource(self.state, avatar, tag='avatars')
            else:
                remove.append('Avatar')
        if roles is not UNDEFINED:
            if roles is not None:
                payload['roles'] = list(map(resolve_id, roles))
            else:
                remove.append('Roles')
        if timeout is not UNDEFINED:
            if timeout is None:
                remove.append('Timeout')
            elif isinstance(timeout, datetime):
                payload['timeout'] = timeout.isoformat()
            elif isinstance(timeout, timedelta):
                payload['timeout'] = (datetime.now() + timeout).isoformat()
            elif isinstance(timeout, (float, int)):
                payload['timeout'] = (datetime.now() + timedelta(seconds=timeout)).isoformat()
        if can_publish is not UNDEFINED:
            if can_publish is None:
                remove.append('CanPublish')
            else:
                payload['can_publish'] = can_publish
        if can_receive is not UNDEFINED:
            if can_receive is None:
                remove.append('CanReceive')
            else:
                payload['can_receive'] = can_receive
        if voice is not UNDEFINED:
            payload['voice_channel'] = resolve_id(voice)
        if len(remove) > 0:
            payload['remove'] = remove

        resp: raw.Member = await self.request(
            routes.SERVERS_MEMBER_EDIT.compile(
                server_id=resolve_id(server),
                member_id=_resolve_member_id(member),
            ),
            json=payload,
        )
        return self.state.parser.parse_member(resp)

    async def query_members_by_name(self, server: ULIDOr[BaseServer], query: str, /) -> list[Member]:
        """|coro|

        Query members by a given name, this API is not stable and will be removed in the future.

        Parameters
        ----------
        server: ULIDOr[:class:`BaseServer`]
            The server.
        query: :class:`str`
            The query to search members for.

        Returns
        -------
        List[:class:`Member`]
            The members matched.
        """
        resp: raw.AllMemberResponse = await self.request(
            routes.SERVERS_MEMBER_EXPERIMENTAL_QUERY.compile(server_id=resolve_id(server)),
            params={
                'query': query,
                'experimental_api': 'true',
            },
        )
        return self.state.parser.parse_members_with_users(resp)

    async def get_member(
        self,
        server: ULIDOr[BaseServer],
        member: str | BaseUser | BaseMember,
        /,
    ) -> Member:
        """|coro|

        Retrieves a Member from a server ID, and a user ID.

        Parameters
        ----------
        server: ULIDOr[:class:`BaseServer`]
            The server.
        member: Union[:class:`str`, :class:`BaseUser`, :class:`BaseMember`]
            The ID of the user.

        Returns
        -------
        :class:`Member`
            The retrieved member.
        """
        resp: raw.Member = await self.request(
            routes.SERVERS_MEMBER_FETCH.compile(
                server_id=resolve_id(server),
                member_id=_resolve_member_id(member),
            )
        )
        return self.state.parser.parse_member(resp)

    async def get_members(
        self, server: ULIDOr[BaseServer], /, *, exclude_offline: typing.Optional[bool] = None
    ) -> list[Member]:
        """|coro|

        Retrieves all server members.

        Parameters
        ----------
        server: ULIDOr[:class:`BaseServer`]
            The server.
        exclude_offline: Optional[:class:`bool`]
            Whether to exclude offline users.

        Returns
        -------
        List[:class:`Member`]
            The retrieved members.
        """
        params: raw.OptionsFetchAllMembers = {}
        if exclude_offline is not None:
            params['exclude_offline'] = utils._bool(exclude_offline)
        resp: raw.AllMemberResponse = await self.request(
            routes.SERVERS_MEMBER_FETCH_ALL.compile(server_id=resolve_id(server)),
            log=False,
            params=params,
        )
        return self.state.parser.parse_members_with_users(resp)

    async def get_member_list(
        self, server: ULIDOr[BaseServer], /, *, exclude_offline: typing.Optional[bool] = None
    ) -> MemberList:
        """|coro|

        Retrieves server members list.

        Parameters
        ----------
        server: ULIDOr[:class:`BaseServer`]
            The server.
        exclude_offline: Optional[:class:`bool`]
            Whether to exclude offline users.

        Returns
        -------
        :class:`MemberList`
            The member list.
        """
        params: raw.OptionsFetchAllMembers = {}
        if exclude_offline is not None:
            params['exclude_offline'] = utils._bool(exclude_offline)
        resp: raw.AllMemberResponse = await self.request(
            routes.SERVERS_MEMBER_FETCH_ALL.compile(server_id=resolve_id(server)),
            log=False,
            params=params,
        )
        return self.state.parser.parse_member_list(resp)

    async def kick_member(self, server: ULIDOr[BaseServer], member: str | BaseUser | BaseMember, /) -> None:
        """|coro|

        Removes a member from the server.

        Parameters
        ----------
        server: ULIDOr[:class:`.BaseServer`]
            The server.
        member: Union[:class:`str`, :class:`.BaseUser`, :class:`.BaseMember`]
            The member to kick.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to kick the member.
        :class:`HTTPException`
            Kicking the member failed.
        """
        await self.request(
            routes.SERVERS_MEMBER_REMOVE.compile(server_id=resolve_id(server), member_id=_resolve_member_id(member))
        )

    async def set_server_permissions_for_role(
        self,
        server: ULIDOr[BaseServer],
        role: ULIDOr[BaseRole],
        /,
        *,
        allow: Permissions = Permissions.none(),
        deny: Permissions = Permissions.none(),
    ) -> Server:
        """|coro|

        Sets permissions for the specified role in the server.

        Parameters
        ----------
        server: ULIDOr[:class:`BaseServer`]
            The server.
        role: ULIDOr[:class:`BaseRole`]
            The role.
        allow: :class:`Permissions`
            New allow flags.
        deny: :class:`Permissions`
            New deny flags.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to set role permissions on the server.
        :class:`HTTPException`
            Setting permissions failed.

        Returns
        -------
        :class:`Server`
            The newly updated server.
        """
        payload: raw.DataSetRolePermissions = {'permissions': {'allow': allow.value, 'deny': deny.value}}
        resp: raw.Server = await self.request(
            routes.SERVERS_PERMISSIONS_SET.compile(server_id=resolve_id(server), role_id=resolve_id(role)),
            json=payload,
        )

        return self.state.parser.parse_server(resp, (True, resp['channels']))

    async def set_default_server_permissions(
        self,
        server: ULIDOr[BaseServer],
        permissions: Permissions,
        /,
    ) -> Server:
        """|coro|

        Sets permissions for the default role in this server.

        Parameters
        ----------
        server: ULIDOr[:class:`BaseServer`]
            The server.
        permissions: :class:`Permissions`
            New default permissions.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to set default permissions on the server.
        :class:`HTTPException`
            Setting permissions failed.

        Returns
        -------
        :class:`Server`
            The newly updated server.
        """
        payload: raw.DataPermissionsValue = {'permissions': permissions.value}
        d: raw.Server = await self.request(
            routes.SERVERS_PERMISSIONS_SET_DEFAULT.compile(server_id=resolve_id(server)),
            json=payload,
        )
        return self.state.parser.parse_server(
            d,
            (True, d['channels']),
        )

    async def create_role(self, server: ULIDOr[BaseServer], /, *, name: str, rank: typing.Optional[int] = None) -> Role:
        """|coro|

        Creates a new server role.

        Parameters
        ----------
        name: :class:`str`
            The role name. Should be between 1 and 32 chars long.
        rank: Optional[:class:`int`]
            The ranking position. Smaller values take priority.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to create the role.
        :class:`HTTPException`
            Creating the role failed.
        """
        server_id = resolve_id(server)
        payload: raw.DataCreateRole = {'name': name, 'rank': rank}
        d: raw.NewRoleResponse = await self.request(
            routes.SERVERS_ROLES_CREATE.compile(server_id=server_id),
            json=payload,
        )
        return self.state.parser.parse_role(d['role'], d['id'], server_id)

    async def delete_role(self, server: ULIDOr[BaseServer], role: ULIDOr[BaseRole], /) -> None:
        """|coro|

        Deletes a server role.

        Parameters
        ----------
        server: ULIDOr[:class:`BaseServer`]
            The server.
        role: ULIDOr[:class:`BaseRole`]
            The role to delete.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to delete the role.
        :class:`HTTPException`
            Deleting the role failed.
        """
        await self.request(routes.SERVERS_ROLES_DELETE.compile(server_id=resolve_id(server), role_id=resolve_id(role)))

    async def edit_role(
        self,
        server: ULIDOr[BaseServer],
        role: ULIDOr[BaseRole],
        /,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        color: UndefinedOr[typing.Optional[str]] = UNDEFINED,
        hoist: UndefinedOr[bool] = UNDEFINED,
        rank: UndefinedOr[int] = UNDEFINED,
    ) -> Role:
        """|coro|

        Edits the role.

        Parameters
        ----------
        server: ULIDOr[:class:`BaseServer`]
            The server.
        role: ULIDOr[:class:`BaseRole`]
            The role to edit.
        name: UndefinedOr[:class:`str`]
            New role name. Should be between 1 and 32 chars long.
        color: UndefinedOr[Optional[:class:`str`]]
            New role color. This should be valid CSS color.
        hoist: UndefinedOr[:class:`bool`]
            Whether this role should be displayed separately.
        rank: UndefinedOr[:class:`int`]
            The new ranking position. Smaller values take priority.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to edit the role.
        :class:`HTTPException`
            Editing the role failed.

        Returns
        -------
        :class:`Role`
            The newly updated role.
        """
        payload: raw.DataEditRole = {}
        remove: list[raw.FieldsRole] = []
        if name is not UNDEFINED:
            payload['name'] = name
        if color is not UNDEFINED:
            if color is not None:
                payload['colour'] = color
            else:
                remove.append('Colour')
        if hoist is not UNDEFINED:
            payload['hoist'] = hoist
        if rank is not UNDEFINED:
            payload['rank'] = rank
        if len(remove) > 0:
            payload['remove'] = remove

        server_id = resolve_id(server)
        role_id = resolve_id(role)

        resp: raw.Role = await self.request(
            routes.SERVERS_ROLES_EDIT.compile(server_id=resolve_id(server), role_id=resolve_id(role)),
            json=payload,
        )
        return self.state.parser.parse_role(
            resp,
            role_id,
            server_id,
        )

    async def get_role(
        self,
        server: ULIDOr[BaseServer],
        role: ULIDOr[BaseRole],
        /,
    ) -> Role:
        """|coro|

        Retrieves a server role.

        Parameters
        ----------
        server: ULIDOr[:class:`BaseServer`]
            The server.
        role: ULIDOr[:class:`BaseRole`]
            The ID of the role to retrieve.

        Raises
        ------
        :class:`NotFound`
            The role does not exist.
        :class:`HTTPException`
            Getting the role failed.

        Returns
        -------
        :class:`Role`
            The retrieved role.
        """
        server_id = resolve_id(server)
        role_id = resolve_id(role)

        resp: raw.Role = await self.request(routes.SERVERS_ROLES_FETCH.compile(server_id=server_id, role_id=role_id))
        return self.state.parser.parse_role(
            resp,
            role_id,
            server_id,
        )

    async def mark_server_as_read(self, server: ULIDOr[BaseServer], /) -> None:
        """|coro|

        Mark all channels in a server as read.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        server: ULIDOr[:class:`BaseServer`]
            The server to mark as read.
        """
        await self.request(routes.SERVERS_SERVER_ACK.compile(server_id=resolve_id(server)))

    async def create_server(
        self, name: str, /, *, description: typing.Optional[str] = None, nsfw: typing.Optional[bool] = None
    ) -> Server:
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
        payload: raw.DataCreateServer = {'name': name}
        if description is not None:
            payload['description'] = description
        if nsfw is not None:
            payload['nsfw'] = nsfw
        d: raw.CreateServerLegacyResponse = await self.request(routes.SERVERS_SERVER_CREATE.compile(), json=payload)

        return self.state.parser.parse_server(
            d['server'],
            (False, d['channels']),
        )

    async def delete_server(self, server: ULIDOr[BaseServer], /) -> None:
        """|coro|

        Deletes a server if owner otherwise leaves.

        Parameters
        ----------
        server: ULIDOr[:class:`BaseServer`]
            The server to delete.
        """
        await self.request(routes.SERVERS_SERVER_DELETE.compile(server_id=resolve_id(server)))

    async def leave_server(self, server: ULIDOr[BaseServer], /, *, silent: typing.Optional[bool] = None) -> None:
        """|coro|

        Leaves the server if not owner otherwise deletes it.

        Parameters
        ----------
        server: ULIDOr[:class:`BaseServer`]
            The server to leave from.
        silent: Optional[:class:`bool`]
            Whether to not send a leave message.
        """
        p: raw.OptionsServerDelete = {}
        if silent is not None:
            p['leave_silently'] = utils._bool(silent)
        await self.request(
            routes.SERVERS_SERVER_DELETE.compile(server_id=resolve_id(server)),
            params=p,
        )

    async def edit_server(
        self,
        server: ULIDOr[BaseServer],
        /,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[typing.Optional[str]] = UNDEFINED,
        icon: UndefinedOr[ResolvableResource | None] = UNDEFINED,
        banner: UndefinedOr[ResolvableResource | None] = UNDEFINED,
        categories: UndefinedOr[list[Category] | None] = UNDEFINED,
        system_messages: UndefinedOr[SystemMessageChannels | None] = UNDEFINED,
        flags: UndefinedOr[ServerFlags] = UNDEFINED,
        discoverable: UndefinedOr[bool] = UNDEFINED,
        analytics: UndefinedOr[bool] = UNDEFINED,
    ) -> Server:
        """|coro|

        Edits the server.

        Parameters
        ----------
        server: ULIDOr[:class:`BaseServer`]
            The server to edit.
        name: UndefinedOr[:class:`str`]
            New server name. Should be between 1 and 32 chars long.
        description: UndefinedOr[Optional[:class:`str`]]
            New server description. Can be 1024 chars maximum long.
        icon: UndefinedOr[Optional[:class:`ResolvableResource`]]
            New server icon.
        banner: UndefinedOr[Optional[:class:`ResolvableResource`]]
            New server banner.
        categories: UndefinedOr[Optional[List[:class:`Category`]]]
            New category structure for this server.
        system_messsages: UndefinedOr[Optional[:class:`SystemMessageChannels`]]
            New system message channels configuration.
        flags: UndefinedOr[:class:`ServerFlags`]
            The new server flags. Can be passed only if you're privileged user.
        discoverable: UndefinedOr[:class:`bool`]
            Whether this server is public and should show up on `Revolt Discover <https://rvlt.gg>`_. Can be passed only if you're privileged user.
        analytics: UndefinedOr[:class:`bool`]
            Whether analytics should be collected for this server. Must be enabled in order to show up on `Revolt Discover <https://rvlt.gg>`_.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to edit the server.
        :class:`HTTPException`
            Editing the server failed.

        Returns
        -------
        :class:`Server`
            The newly updated server.
        """
        payload: raw.DataEditServer = {}
        remove: list[raw.FieldsServer] = []
        if name is not UNDEFINED:
            payload['name'] = name
        if description is not UNDEFINED:
            if description is not None:
                payload['description'] = description
            else:
                remove.append('Description')
        if icon is not UNDEFINED:
            if icon is not None:
                payload['icon'] = await resolve_resource(self.state, icon, tag='icons')
            else:
                remove.append('Icon')
        if banner is not UNDEFINED:
            if banner is not None:
                payload['banner'] = await resolve_resource(self.state, banner, tag='banners')
            else:
                remove.append('Banner')
        if categories is not UNDEFINED:
            if categories is not None:
                payload['categories'] = [e.build() for e in categories]
            else:
                remove.append('Categories')
        if system_messages is not UNDEFINED:
            if system_messages is not None:
                payload['system_messages'] = system_messages.build()
            else:
                remove.append('SystemMessages')
        if flags is not UNDEFINED:
            payload['flags'] = flags.value
        if discoverable is not UNDEFINED:
            payload['discoverable'] = discoverable
        if analytics is not UNDEFINED:
            payload['analytics'] = analytics
        if len(remove) > 0:
            payload['remove'] = remove

        d: raw.Server = await self.request(
            routes.SERVERS_SERVER_EDIT.compile(server_id=resolve_id(server)),
            json=payload,
        )
        return self.state.parser.parse_server(
            d,
            (True, d['channels']),
        )

    async def get_server(
        self,
        server: ULIDOr[BaseServer],
        /,
        *,
        populate_channels: typing.Optional[bool] = None,
    ) -> Server:
        """|coro|

        Retrieves a :class:`Server`.

        Parameters
        ----------
        server: ULIDOr[:class:`BaseServer`]
            The ID of the server.
        populate_channels: :class:`bool`
            Whether to populate channels.

        Returns
        -------
        :class:`Server`
            The retrieved server.
        """
        p: raw.OptionsFetchServer = {}
        if populate_channels is not None:
            p['include_channels'] = utils._bool(populate_channels)
        d: raw.FetchServerResponse = await self.request(
            routes.SERVERS_SERVER_FETCH.compile(server_id=resolve_id(server))
        )
        return self.state.parser.parse_server(
            d,  # type: ignore
            (not populate_channels, d['channels']),  # type: ignore
        )

    # Sync control
    async def get_user_settings(self, keys: typing.Optional[list[str]] = None) -> UserSettings:
        """|coro|

        Retrieve user settings.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        keys: Optional[List[:class:`str`]]
            The keys of user settings to retrieve. To retrieve all user settings, pass ``None`` or empty list.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """
        # Sync endpoints aren't meant to be used with bot accounts
        if keys is None:
            keys = []
        payload: raw.OptionsFetchSettings = {'keys': keys}
        resp: raw.UserSettings = await self.request(routes.SYNC_GET_SETTINGS.compile(), json=payload)
        return self.state.parser.parse_user_settings(
            resp,
            True,
        )

    async def get_read_states(self) -> list[ReadState]:
        """|coro|

        Retrieves read states for all channels the current user in.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+

        Returns
        -------
        List[:class:`.ReadState`]
            The channel read states.
        """
        resp: list[raw.ChannelUnread] = await self.request(routes.SYNC_GET_UNREADS.compile())
        return list(map(self.state.parser.parse_channel_unread, resp))

    async def edit_user_settings(
        self,
        partial: dict[str, str] = {},
        edited_at: typing.Optional[typing.Union[datetime, int]] = None,
    ) -> None:
        """|coro|

        Edits the current user settings.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        partial: Dict[:class:`str`, :class:`str`]
            The dict to merge into the current user settings.
        edited_at: Optional[Union[:class:`~datetime.datetime`, :class:`int`]]
            The revision.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """

        params: raw.OptionsSetSettings = {}

        if edited_at is not None:
            if isinstance(edited_at, datetime):
                edited_at = int(edited_at.timestamp())
            params['timestamp'] = edited_at

        payload: dict[str, str] = {}
        for k, v in partial.items():
            if isinstance(v, str):
                payload[k] = v
            else:
                payload[k] = utils.to_json(v)

        await self.request(routes.SYNC_SET_SETTINGS.compile(), json=payload, params=params)

    # Users control
    async def accept_friend_request(self, user: ULIDOr[BaseUser], /) -> User:
        """|coro|

        Accept another user's friend request.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        user: ULIDOr[:class:`BaseUser`]
            The user to friend with.

        Returns
        -------
        :class:`User`
            The friended user.
        """
        resp: raw.User = await self.request(routes.USERS_ADD_FRIEND.compile(user_id=resolve_id(user)))
        return self.state.parser.parse_user(resp)

    async def block_user(self, user: ULIDOr[BaseUser], /) -> User:
        """|coro|

        Block another user.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        user: ULIDOr[:class:`BaseUser`]
            The user to block.

        Returns
        -------
        :class:`User`
            The blocked user.
        """
        resp: raw.User = await self.request(routes.USERS_BLOCK_USER.compile(user_id=resolve_id(user)))
        return self.state.parser.parse_user(resp)

    async def change_username(self, username: str, /, *, current_password: str) -> OwnUser:
        """|coro|

        Change your username.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        username: :class:`str`
            The new username.
        current_password: :class:`str`
            The current account password.

        Returns
        -------
        :class:`OwnUser`
            The newly updated user.
        """
        payload: raw.DataChangeUsername = {'username': username, 'password': current_password}
        resp: raw.User = await self.request(
            routes.USERS_CHANGE_USERNAME.compile(),
            json=payload,
        )
        return self.state.parser.parse_own_user(resp)

    async def _edit_user(
        self,
        route: routes.CompiledRoute,
        /,
        *,
        display_name: UndefinedOr[typing.Optional[str]] = UNDEFINED,
        avatar: UndefinedOr[ResolvableResource | None] = UNDEFINED,
        status: UndefinedOr[UserStatusEdit] = UNDEFINED,
        profile: UndefinedOr[UserProfileEdit] = UNDEFINED,
        badges: UndefinedOr[UserBadges] = UNDEFINED,
        flags: UndefinedOr[UserFlags] = UNDEFINED,
    ) -> raw.User:
        payload: raw.DataEditUser = {}
        remove: list[raw.FieldsUser] = []
        if display_name is not UNDEFINED:
            if display_name is None:
                remove.append('DisplayName')
            else:
                payload['display_name'] = display_name
        if avatar is not UNDEFINED:
            if avatar is None:
                remove.append('Avatar')
            else:
                payload['avatar'] = await resolve_resource(self.state, avatar, tag='avatars')
        if status is not UNDEFINED:
            payload['status'] = status.build()
            remove.extend(status.remove)
        if profile is not UNDEFINED:
            payload['profile'] = await profile.build(self.state)
            remove.extend(profile.remove)
        if badges is not UNDEFINED:
            payload['badges'] = badges.value
        if flags is not UNDEFINED:
            payload['flags'] = flags.value
        if len(remove) > 0:
            payload['remove'] = remove
        return await self.request(route, json=payload)

    async def edit_my_user(
        self,
        *,
        display_name: UndefinedOr[typing.Optional[str]] = UNDEFINED,
        avatar: UndefinedOr[typing.Optional[ResolvableResource]] = UNDEFINED,
        status: UndefinedOr[UserStatusEdit] = UNDEFINED,
        profile: UndefinedOr[UserProfileEdit] = UNDEFINED,
        badges: UndefinedOr[UserBadges] = UNDEFINED,
        flags: UndefinedOr[UserFlags] = UNDEFINED,
    ) -> OwnUser:
        """|coro|

        Edits the user.

        Parameters
        ----------
        display_name: UndefinedOr[Optional[:class:`str`]]
            New display name. Pass ``None`` to remove it.
        avatar: UndefinedOr[Optional[:class:`ResolvableResource`]]
            New avatar. Pass ``None`` to remove it.
        status: UndefinedOr[:class:`UserStatusEdit`]
            New user status.
        profile: UndefinedOr[:class:`UserProfileEdit`]
            New user profile data. This is applied as a partial.
        badges: UndefinedOr[:class:`UserBadges`]
            The new user badges.
        flags: UndefinedOr[:class:`UserFlags`]
            The new user flags.

        Raises
        ------
        :class:`HTTPException`
            Editing the user failed.

        Returns
        -------
        :class:`OwnUser`
            The newly updated authenticated user.
        """
        resp = await self._edit_user(
            routes.USERS_EDIT_SELF_USER.compile(),
            display_name=display_name,
            avatar=avatar,
            status=status,
            profile=profile,
            badges=badges,
            flags=flags,
        )
        return self.state.parser.parse_own_user(resp)

    async def edit_user(
        self,
        user: ULIDOr[BaseUser],
        /,
        *,
        display_name: UndefinedOr[typing.Optional[str]] = UNDEFINED,
        avatar: UndefinedOr[ResolvableResource | None] = UNDEFINED,
        status: UndefinedOr[UserStatusEdit] = UNDEFINED,
        profile: UndefinedOr[UserProfileEdit] = UNDEFINED,
        badges: UndefinedOr[UserBadges] = UNDEFINED,
        flags: UndefinedOr[UserFlags] = UNDEFINED,
    ) -> User:
        """|coro|

        Edits the user.

        Parameters
        ----------
        user: ULIDOr[:class:`BaseUser`]
            The user to edit.
        display_name: UndefinedOr[Optional[:class:`str`]]
            New display name. Pass ``None`` to remove it.
        avatar: UndefinedOr[Optional[:class:`ResolvableULID`]]
            New avatar. Pass ``None`` to remove it.
        status: UndefinedOr[:class:`UserStatusEdit`]
            New user status.
        profile: UndefinedOr[:class:`UserProfileEdit`]
            New user profile data. This is applied as a partial.
        badges: UndefinedOr[:class:`UserBadges`]
            The new user badges.
        flags: UndefinedOr[:class:`UserFlags`]
            The new user flags.

        Raises
        ------
        :class:`HTTPException`
            Editing the user failed.

        Returns
        -------
        :class:`User`
            The newly updated user.
        """
        resp = await self._edit_user(
            routes.USERS_EDIT_USER.compile(user_id=resolve_id(user)),
            display_name=display_name,
            avatar=avatar,
            status=status,
            profile=profile,
            badges=badges,
            flags=flags,
        )
        return self.state.parser.parse_user(resp)

    async def get_private_channels(
        self,
    ) -> list[SavedMessagesChannel | DMChannel | GroupChannel]:
        """|coro|

        Get all DMs and groups conversations.

        Returns
        -------
        List[Union[:class:`SavedMessagesChannel`, :class:`DMChannel`, :class:`GroupChannel`]]
            The private channels.
        """
        resp: list[raw.SavedMessagesChannel | raw.DirectMessageChannel | raw.GroupChannel] = await self.request(
            routes.USERS_FETCH_DMS.compile()
        )
        return list(map(self.state.parser.parse_channel, resp))  # type: ignore[return-value]

    async def get_user_profile(self, user: ULIDOr[BaseUser], /) -> UserProfile:
        """|coro|

        Retrieve a user's profile data.

        Parameters
        ----------
        user: ULIDOr[:class:`BaseUser`]
            The user.

        Raises
        ------
        :class:`Forbidden`
            You do not have permission to access the user's profile.

        Returns
        -------
        :class:`UserProfile`
            The retrieved user profile.
        """
        user_id = resolve_id(user)
        resp: raw.UserProfile = await self.request(routes.USERS_FETCH_PROFILE.compile(user_id=user_id))
        return self.state.parser.parse_user_profile(resp).attach_state(self.state, user_id)

    async def get_me(self) -> OwnUser:
        """|coro|

        Retrieve your user information.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+

        Returns
        -------
        :class:`OwnUser`
            The retrieved user.
        """
        resp: raw.User = await self.request(routes.USERS_FETCH_SELF.compile())
        return self.state.parser.parse_own_user(resp)

    async def get_user(self, user: ULIDOr[BaseUser], /) -> User:
        """|coro|

        Retrieve a user's information.

        Parameters
        ----------
        user: ULIDOr[:class:`BaseUser`]
            The user.

        Raises
        ------
        :class:`Forbidden`
            You been blocked by that user.
        :class:`HTTPException`
            Getting the user failed.

        Returns
        -------
        :class:`User`
            The retrieved user.
        """
        resp: raw.User = await self.request(routes.USERS_FETCH_USER.compile(user_id=resolve_id(user)))
        return self.state.parser.parse_user(resp)

    async def get_user_flags(self, user: ULIDOr[BaseUser], /) -> UserFlags:
        """|coro|

        Retrieve a user's flags.
        """
        resp: raw.FlagResponse = await self.request(routes.USERS_FETCH_USER_FLAGS.compile(user_id=resolve_id(user)))
        return UserFlags(resp['flags'])

    async def get_mutuals_with(self, user: ULIDOr[BaseUser], /) -> Mutuals:
        """|coro|

        Retrieves a list of mutual friends and servers with another user.

        Raises
        ------
        :class:`HTTPException`
            Finding mutual friends/servers failed.

        Returns
        -------
        :class:`Mutuals`
            The found mutuals.
        """
        resp: raw.MutualResponse = await self.request(routes.USERS_FIND_MUTUAL.compile(user_id=resolve_id(user)))
        return self.state.parser.parse_mutuals(resp)

    async def get_default_avatar(self, user: ULIDOr[BaseUser], /) -> bytes:
        """|coro|

        Returns a default avatar based on the given ID.
        """
        response = await self.raw_request(
            routes.USERS_GET_DEFAULT_AVATAR.compile(user_id=resolve_id(user)[-1]),
            token=None,
            accept_json=False,
        )
        avatar = await response.read()
        if not response.closed:
            response.close()
        return avatar

    async def open_dm(self, user: ULIDOr[BaseUser], /) -> SavedMessagesChannel | DMChannel:
        """|coro|

        Open a DM with another user. If the target is oneself, a :class:`SavedMessagesChannel` is returned.

        Raises
        ------
        :class:`HTTPException`
            Opening DM failed.
        """
        resp: raw.SavedMessagesChannel | raw.DirectMessageChannel = await self.request(
            routes.USERS_OPEN_DM.compile(user_id=resolve_id(user))
        )
        channel = self.state.parser.parse_channel(resp)
        assert isinstance(channel, (SavedMessagesChannel, DMChannel))
        return channel

    async def deny_friend_request(self, user: ULIDOr[BaseUser], /) -> User:
        """|coro|

        Denies another user's friend request.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        :class:`HTTPException`
            Denying the friend request failed.
        """
        resp: raw.User = await self.request(routes.USERS_REMOVE_FRIEND.compile(user_id=resolve_id(user)))
        return self.state.parser.parse_user(resp)

    async def remove_friend(self, user: ULIDOr[BaseUser], /) -> User:
        """|coro|

        Removes the user as a friend.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        :class:`HTTPException`
            Removing the user as a friend failed.
        """
        resp: raw.User = await self.request(routes.USERS_REMOVE_FRIEND.compile(user_id=resolve_id(user)))
        return self.state.parser.parse_user(resp)

    async def send_friend_request(self, username: str, discriminator: typing.Optional[str] = None, /) -> User:
        """|coro|

        Send a friend request to another user.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        username: :class:`str`
            Username and discriminator combo separated by `#`.
        discriminator: Optional[:class:`str`]
            The user's discriminator.

        Raises
        ------
        :class:`Forbidden`
            Target user have blocked you.
        :class:`HTTPException`
            Sending the friend request failed.
        """
        if discriminator is not None:
            username += '#' + discriminator
        payload: raw.DataSendFriendRequest = {'username': username}

        resp: raw.User = await self.request(
            routes.USERS_SEND_FRIEND_REQUEST.compile(),
            json=payload,
        )
        return self.state.parser.parse_user(resp)

    async def unblock_user(self, user: ULIDOr[BaseUser], /) -> User:
        """|coro|

        Unblock a user.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        user: ULIDOr[:class:`BaseUser`]
            The user to unblock.
        """
        resp: raw.User = await self.request(routes.USERS_UNBLOCK_USER.compile(user_id=resolve_id(user)))
        return self.state.parser.parse_user(resp)

    # Webhooks control
    async def delete_webhook(self, webhook: ULIDOr[BaseWebhook], /, *, token: typing.Optional[str] = None) -> None:
        """|coro|

        Deletes a webhook. If webhook token wasn't given, the library will attempt delete webhook with current bot/user token.

        Parameters
        ----------
        webhook: ULIDOr[:class:`BaseWebhook`]
            The webhook to delete.
        token: Optional[:class:`str`]
            The webhook token.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to delete the webhook.
        :class:`HTTPException`
            Deleting the webhook failed.
        """
        if token is None:
            await self.request(routes.WEBHOOKS_WEBHOOK_DELETE.compile(webhook_id=resolve_id(webhook)))
        else:
            await self.request(
                routes.WEBHOOKS_WEBHOOK_DELETE_TOKEN.compile(webhook_id=resolve_id(webhook), webhook_token=token),
                token=None,
            )

    async def edit_webhook(
        self,
        webhook: ULIDOr[BaseWebhook],
        /,
        *,
        token: typing.Optional[str] = None,
        name: UndefinedOr[str] = UNDEFINED,
        avatar: UndefinedOr[ResolvableResource | None] = UNDEFINED,
        permissions: UndefinedOr[Permissions] = UNDEFINED,
    ) -> Webhook:
        """|coro|

        Edits a webhook. If webhook token wasn't given, the library will attempt edit webhook with current bot/user token.

        Parameters
        ----------
        webhook: ULIDOr[:class:`BaseWebhook`]
            The webhook to edit.
        token: Optional[:class:`str`]
            The webhook token.
        name: UndefinedOr[:class:`str`]
            New webhook name. Should be between 1 and 32 chars long.
        avatar: UndefinedOr[Optional[:class:`ResolvableResource`]]
            New webhook avatar.
        permissions: UndefinedOr[:class:`Permissions`]
            New webhook permissions.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to edit the webhook.
        :class:`HTTPException`
            Editing the webhook failed.

        Returns
        -------
        :class:`Webhook`
            The newly updated webhook.
        """
        payload: raw.DataEditWebhook = {}
        remove: list[raw.FieldsWebhook] = []
        if name is not UNDEFINED:
            payload['name'] = name
        if avatar is not UNDEFINED:
            if avatar is None:
                remove.append('Avatar')
            else:
                payload['avatar'] = await resolve_resource(self.state, avatar, tag='avatars')
        if permissions is not UNDEFINED:
            payload['permissions'] = permissions.value
        if len(remove) > 0:
            payload['remove'] = remove

        if token is None:
            resp: raw.Webhook = await self.request(
                routes.WEBHOOKS_WEBHOOK_EDIT.compile(webhook_id=resolve_id(webhook)),
                json=payload,
            )
        else:
            resp = await self.request(
                routes.WEBHOOKS_WEBHOOK_EDIT_TOKEN.compile(webhook_id=resolve_id(webhook), webhook_token=token),
                json=payload,
                token=None,
            )
        return self.state.parser.parse_webhook(resp)

    async def execute_webhook(
        self,
        webhook: ULIDOr[BaseWebhook],
        token: str,
        /,
        content: typing.Optional[str] = None,
        *,
        nonce: typing.Optional[str] = None,
        attachments: list[ResolvableResource] | None = None,
        replies: list[Reply | ULIDOr[BaseMessage]] | None = None,
        embeds: list[SendableEmbed] | None = None,
        masquerade: typing.Optional[Masquerade] = None,
        interactions: typing.Optional[MessageInteractions] = None,
        silent: typing.Optional[bool] = None,
        mention_everyone: typing.Optional[bool] = None,
        mention_online: typing.Optional[bool] = None,
    ) -> Message:
        """|coro|

        Executes a webhook and returns a message.

        Parameters
        ----------
        webhook: ULIDOr[:class:`.BaseWebhook`]
            The ID of the webhook.
        token: :class:`str`
            The webhook token.
        content: Optional[:class:`str`]
            The message content.
        nonce: Optional[:class:`str`]
            The message nonce.
        attachments: Optional[List[:class:`.ResolvableResource`]]
            The attachments to send the message with.

            To provide this, the webhook must have :attr:`~Permissions.upload_files`.
        replies: Optional[List[Union[:class:`Reply`, ULIDOr[:class:`BaseMessage`]]]]
            The message replies.
        embeds: Optional[List[:class:`SendableEmbed`]]
            The embeds to send the message with.

            To provide non-null or non-empty value, the webhook must have :attr:`~Permissions.send_embeds`.
        masquearde: Optional[:class:`Masquerade`]
            The message masquerade.

            To provide this, the webhook must have :attr:`~Permissions.use_masquerade`.

            If :attr:`.Masquerade.color` is provided, :attr:`~Permissions.use_masquerade` is also required.
        interactions: Optional[:class:`MessageInteractions`]
            The message interactions.

            If :attr:`.MessageInteractions.reactions` is provided, :attr:`~Permissions.react` is required.
        silent: Optional[:class:`bool`]
            Whether to suppress notifications or not.
        mention_everyone: Optional[:class:`bool`]
            Whether to mention all users who can see the channel. This cannot be mixed with ``mention_online`` parameter.
        mention_online: Optional[:class:`bool`]
            Whether to mention all users who are online and can see the channel. This cannot be mixed with ``mention_everyone`` parameter.

        Returns
        -------
        :class:`.Message`
            The message sent.
        """
        payload: raw.DataMessageSend = {}
        if content is not None:
            payload['content'] = content
        if attachments is not None:
            payload['attachments'] = [
                await resolve_resource(self.state, attachment, tag='attachments') for attachment in attachments
            ]
        if replies is not None:
            payload['replies'] = [
                (reply.build() if isinstance(reply, Reply) else {'id': resolve_id(reply), 'mention': False})
                for reply in replies
            ]
        if embeds is not None:
            payload['embeds'] = [await embed.build(self.state) for embed in embeds]
        if masquerade is not None:
            payload['masquerade'] = masquerade.build()
        if interactions is not None:
            payload['interactions'] = interactions.build()

        flags = None

        if silent is not None:
            if flags is None:
                flags = 0

            if silent:
                flags |= MessageFlags.suppress_notifications.value

        if mention_everyone is not None:
            if flags is None:
                flags = 0

            if mention_everyone:
                flags |= MessageFlags.mention_everyone.value

        if mention_online is not None:
            if flags is None:
                flags = 0

            if mention_online:
                flags |= MessageFlags.mention_online.value

        if flags is not None:
            payload['flags'] = flags

        headers = {}
        if nonce is not None:
            headers['Idempotency-Key'] = nonce
        resp: raw.Message = await self.request(
            routes.WEBHOOKS_WEBHOOK_EXECUTE.compile(webhook_id=resolve_id(webhook), webhook_token=token),
            json=payload,
            headers=headers,
            token=None,
        )
        return self.state.parser.parse_message(resp)

    async def get_webhook(
        self,
        webhook: ULIDOr[BaseWebhook],
        /,
        *,
        token: typing.Optional[str] = None,
    ) -> Webhook:
        """|coro|

        Retrieves a webhook. If webhook token wasn't given, the library will attempt get webhook with bot/user token.

        .. note::
            Due to Revolt limitation, the webhook avatar information will be partial if no token is provided.
            Fields are guaranteed to be non-zero/non-empty are ``id`` and ``user_id``.

        Parameters
        ----------
        webhook: ULIDOr[:class:`BaseWebhook`]
            The ID of the webhook.
        token: Optional[:class:`str`]
            The webhook token.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to get the webhook.
        :class:`HTTPException`
            Getting the webhook failed.

        Returns
        -------
        :class:`Webhook`
            The retrieved webhook.
        """

        if token is None:
            r1: raw.ResponseWebhook = await self.request(
                routes.WEBHOOKS_WEBHOOK_FETCH.compile(webhook_id=resolve_id(webhook))
            )
            return self.state.parser.parse_response_webhook(r1)
        else:
            r2: raw.Webhook = await self.request(
                routes.WEBHOOKS_WEBHOOK_FETCH_TOKEN.compile(webhook_id=resolve_id(webhook), webhook_token=token),
                token=None,
            )
            return self.state.parser.parse_webhook(r2)

    # Account authentication control
    async def change_email(
        self,
        *,
        email: str,
        current_password: str,
    ) -> None:
        """|coro|

        Change the current account password.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        email: :class:`str`
            New email for this account.
        current_password: :class:`str`
            The current account password.

        Raises
        ------
        :class:`HTTPException`
            Changing the account password failed.
        """
        payload: raw.a.DataChangeEmail = {
            'email': email,
            'current_password': current_password,
        }
        await self.request(
            routes.AUTH_ACCOUNT_CHANGE_EMAIL.compile(),
            json=payload,
        )

    async def change_password(
        self,
        *,
        new_password: str,
        current_password: str,
    ) -> None:
        """|coro|

        Change the current account password.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        new_password: :class:`str`
            New password for this account.
        current_password: :class:`str`
            The current account password.

        Raises
        ------
        :class:`HTTPException`
            Changing the account password failed.
        """
        payload: raw.a.DataChangePassword = {
            'password': new_password,
            'current_password': current_password,
        }
        await self.request(
            routes.AUTH_ACCOUNT_CHANGE_PASSWORD.compile(),
            json=payload,
        )

    async def confirm_account_deletion(
        self,
        *,
        token: str,
    ) -> None:
        """|coro|

        Schedule an account for deletion by confirming the received token.

        Parameters
        ----------
        token: :class:`str`
            The deletion token received.

        Raises
        ------
        :class:`HTTPException`
            Confirming the account deletion failed.
        """
        payload: raw.a.DataAccountDeletion = {'token': token}
        await self.request(
            routes.AUTH_ACCOUNT_CONFIRM_DELETION.compile(),
            token=None,
            json=payload,
        )

    async def register(
        self,
        email: str,
        password: str,
        /,
        *,
        invite: typing.Optional[str] = None,
        captcha: typing.Optional[str] = None,
    ) -> None:
        """|coro|

        Register a new account.

        Parameters
        ----------
        email: :class:`str`
            The account email.
        password: :class:`str`
            The account password.
        invite: Optional[:class:`str`]
            The instance invite code.
        captcha: Optional[:class:`str`]
            The CAPTCHA verification code.

        Raises
        ------
        :class:`HTTPException`
            Registering the account failed.
        """
        payload: raw.a.DataCreateAccount = {
            'email': email,
            'password': password,
            'invite': invite,
            'captcha': captcha,
        }
        await self.request(
            routes.AUTH_ACCOUNT_CREATE_ACCOUNT.compile(),
            token=None,
            json=payload,
        )

    async def delete_account(
        self,
        *,
        mfa: str,
    ) -> None:
        """|coro|

        Request to have an account deleted.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        mfa: :class:`str`
            The MFA ticket code.

        Raises
        ------
        :class:`HTTPException`
            Requesting the account to be deleted failed.
        """
        await self.request(routes.AUTH_ACCOUNT_DELETE_ACCOUNT.compile(), mfa_ticket=mfa)

    async def disable_account(
        self,
        *,
        mfa: str,
    ) -> None:
        """|coro|

        Disable an account.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        mfa: :class:`str`
            The MFA ticket code.

        Raises
        ------
        :class:`HTTPException`
            Disabling the account failed.
        """
        await self.request(routes.AUTH_ACCOUNT_DISABLE_ACCOUNT.compile(), mfa_ticket=mfa)

    async def get_account(self) -> PartialAccount:
        """|coro|

        Get account information from the current session.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        :class:`HTTPException`
            Getting the account data failed.
        """
        resp: raw.a.AccountInfo = await self.request(routes.AUTH_ACCOUNT_FETCH_ACCOUNT.compile())
        return self.state.parser.parse_partial_account(resp)

    async def confirm_password_reset(
        self, token: str, /, *, new_password: str, remove_sessions: typing.Optional[bool] = None
    ) -> None:
        """|coro|

        Confirm password reset and change the password.

        Parameters
        ----------
        token: :class:`str`
            The password reset token.
        new_password: :class:`str`
            New password for the account.
        remove_sessions: Optional[:class:`bool`]
            Whether to logout all sessions.

        Raises
        ------
        :class:`HTTPException`
            Sending the email failed.
        """
        payload: raw.a.DataPasswordReset = {
            'token': token,
            'password': new_password,
            'remove_sessions': remove_sessions,
        }
        await self.request(
            routes.AUTH_ACCOUNT_PASSWORD_RESET.compile(),
            token=None,
            json=payload,
        )

    async def resend_verification(
        self,
        *,
        email: str,
        captcha: typing.Optional[str] = None,
    ) -> None:
        """|coro|

        Resend account creation verification email.

        Parameters
        ----------
        email: :class:`str`
            The email associated with the account.
        captcha: Optional[:class:`str`]
            The CAPTCHA verification code.

        Raises
        ------
        :class:`HTTPException`
            Resending the verification mail failed.
        """
        payload: raw.a.DataResendVerification = {'email': email, 'captcha': captcha}
        await self.request(
            routes.AUTH_ACCOUNT_RESEND_VERIFICATION.compile(),
            token=None,
            json=payload,
        )

    async def send_password_reset(self, *, email: str, captcha: typing.Optional[str] = None) -> None:
        """|coro|

        Send an email to reset account password.

        Parameters
        ----------
        email: :class:`str`
            The email associated with the account.
        captcha: Optional[:class:`str`]
            The CAPTCHA verification code.

        Raises
        ------
        :class:`HTTPException`
            Sending the email failed.
        """
        payload: raw.a.DataSendPasswordReset = {'email': email, 'captcha': captcha}
        await self.request(
            routes.AUTH_ACCOUNT_SEND_PASSWORD_RESET.compile(),
            token=None,
            json=payload,
        )

    async def verify_email(self, code: str, /) -> MFATicket | None:
        """|coro|

        Verify an email address.

        Parameters
        ----------
        code: :class:`str`
            The code from mail body.

        Raises
        ------
        :class:`HTTPException`
            Verifying the email address failed.
        """
        response = await self.request(routes.AUTH_ACCOUNT_VERIFY_EMAIL.compile(code=code), token=None)
        if response is not None and isinstance(response, dict) and 'ticket' in response:
            return self.state.parser.parse_mfa_ticket(response['ticket'])
        else:
            return None

    # MFA authentication control
    async def _create_mfa_ticket(self, payload: raw.a.MFAResponse, /) -> MFATicket:
        resp: raw.a.MFATicket = await self.request(routes.AUTH_MFA_CREATE_TICKET.compile(), json=payload)
        return self.state.parser.parse_mfa_ticket(resp)

    async def create_password_ticket(self, password: str, /) -> MFATicket:
        """|coro|

        Create a new MFA ticket or validate an existing one.
        """
        payload: raw.a.PasswordMFAResponse = {'password': password}
        return await self._create_mfa_ticket(payload)

    async def create_recovery_code_ticket(self, recovery_code: str, /) -> MFATicket:
        """|coro|

        Create a new MFA ticket or validate an existing one.
        """
        payload: raw.a.RecoveryMFAResponse = {'recovery_code': recovery_code}
        return await self._create_mfa_ticket(payload)

    async def create_totp_ticket(self, totp_code: str, /) -> MFATicket:
        """|coro|

        Create a new MFA ticket or validate an existing one.
        """
        payload: raw.a.TotpMFAResponse = {'totp_code': totp_code}
        return await self._create_mfa_ticket(payload)

    async def get_recovery_codes(self) -> list[str]:
        """|coro|

        Gets recovery codes for an account.
        """
        return await self.request(routes.AUTH_MFA_GENERATE_RECOVERY.compile())

    async def mfa_status(self) -> MFAStatus:
        """|coro|

        Gets MFA status of an account.
        """
        resp: raw.a.MultiFactorStatus = await self.request(routes.AUTH_MFA_FETCH_STATUS.compile())
        return self.state.parser.parse_multi_factor_status(resp)

    async def generate_recovery_codes(self, *, mfa_ticket: str) -> list[str]:
        """|coro|

        Regenerates recovery codes for an account.
        """
        resp: list[str] = await self.request(routes.AUTH_MFA_GENERATE_RECOVERY.compile(), mfa_ticket=mfa_ticket)
        return resp

    async def get_mfa_methods(self) -> list[MFAMethod]:
        """|coro|

        Gets available MFA methods.
        """
        resp: list[raw.a.MFAMethod] = await self.request(routes.AUTH_MFA_GET_MFA_METHODS.compile())
        return [MFAMethod(mm) for mm in resp]

    async def disable_totp_2fa(self, *, mfa_ticket: str) -> None:
        """|coro|

        Disables TOTP 2FA for an account.
        """
        await self.request(
            routes.AUTH_MFA_TOTP_DISABLE.compile(),
            mfa_ticket=mfa_ticket,
        )

    async def enable_totp_2fa(self, response: MFAResponse, /) -> None:
        """|coro|

        Enables TOTP 2FA for an account.
        """
        await self.request(
            routes.AUTH_MFA_TOTP_ENABLE.compile(),
            json=response.build(),
        )

    async def generate_totp_secret(self, *, mfa_ticket: str) -> str:
        """|coro|

        Generates a new secret for TOTP.
        """
        resp: raw.a.ResponseTotpSecret = await self.request(
            routes.AUTH_MFA_TOTP_GENERATE_SECRET.compile(),
            mfa_ticket=mfa_ticket,
        )
        return resp['secret']

    async def edit_session(self, session: ULIDOr[PartialSession], *, friendly_name: str) -> PartialSession:
        """|coro|

        Edits the session information.

        Parameters
        ----------
        session: ULIDOr[:class:`PartialSession`]
            The session to edit.
        friendly_name: :class:`str`
            The new device name. Because of Authifier limitation, this is not :class:`UndefinedOr`.

        """
        payload: raw.a.DataEditSession = {'friendly_name': friendly_name}
        resp: raw.a.SessionInfo = await self.request(
            routes.AUTH_SESSION_EDIT.compile(session_id=resolve_id(session)), json=payload
        )
        return self.state.parser.parse_partial_session(resp)

    async def get_sessions(self) -> list[PartialSession]:
        """|coro|

        Retrieves all sessions associated with this account.

        Returns
        -------
        List[:class:`PartialSession`]
            The sessions.
        """
        resp: list[raw.a.SessionInfo] = await self.request(routes.AUTH_SESSION_FETCH_ALL.compile())
        return list(map(self.state.parser.parse_partial_session, resp))

    async def login_with_email(
        self, email: str, password: str, /, *, friendly_name: typing.Optional[str] = None
    ) -> LoginResult:
        """|coro|

        Logs in to an account using email and password.

        Parameters
        ----------
        email: :class:`str`
            The email.
        password: :class:`str`
            The password.
        friendly_name: Optional[:class:`str`]
            The device name.

        Returns
        -------
        :class:`LoginResult`
            The login response.
        """
        payload: raw.a.EmailDataLogin = {
            'email': email,
            'password': password,
            'friendly_name': friendly_name,
        }
        resp: raw.a.ResponseLogin = await self.request(routes.AUTH_SESSION_LOGIN.compile(), token=None, json=payload)
        return self.state.parser.parse_response_login(resp, friendly_name)

    async def login_with_mfa(
        self,
        ticket: str,
        by: MFAResponse | None,
        /,
        *,
        friendly_name: typing.Optional[str] = None,
    ) -> Session | AccountDisabled:
        """|coro|

        Logs in to an account.

        Parameters
        ----------
        ticket: :class:`str`
            The MFA ticket.
        by: Optional[:class:`MFAResponse`]
            The :class:`ByPassword`, :class:`ByRecoveryCode`, or :class:`ByTOTP` object.
        friendly_name: Optional[:class:`str`]
            The device name.

        Returns
        -------
        Union[:class:`Session`, :class:`AccountDisabled`]
            The session if successfully logged in, or :class:`AccountDisabled` containing user ID associated with the account.
        """
        payload: raw.a.MFADataLogin = {
            'mfa_ticket': ticket,
            'mfa_response': by.build() if by else None,
            'friendly_name': friendly_name,
        }
        resp: raw.a.ResponseLogin = await self.request(routes.AUTH_SESSION_LOGIN.compile(), token=None, json=payload)
        ret = self.state.parser.parse_response_login(resp, friendly_name)
        assert not isinstance(ret, MFARequired), 'Recursion detected'
        return ret

    async def logout(self) -> None:
        """|coro|

        Deletes current session.
        """
        await self.request(routes.AUTH_SESSION_LOGOUT.compile())

    async def revoke_session(self, session_id: ULIDOr[PartialSession], /) -> None:
        """|coro|

        Deletes a specific active session.
        """
        await self.request(routes.AUTH_SESSION_REVOKE.compile(session_id=resolve_id(session_id)))

    async def revoke_all_sessions(self, *, revoke_self: typing.Optional[bool] = None) -> None:
        """|coro|

        Deletes all active sessions, optionally including current one.

        Parameters
        ----------
        revoke_self: Optional[:class:`bool`]
            Whether to revoke current session or not.
        """
        params = {}
        if revoke_self is not None:
            params['revoke_self'] = utils._bool(revoke_self)
        await self.request(routes.AUTH_SESSION_REVOKE_ALL.compile(), params=params)


__all__ = (
    'DEFAULT_HTTP_USER_AGENT',
    '_STATUS_TO_ERRORS',
    'RateLimit',
    'RateLimitBlocker',
    'RateLimiter',
    'DefaultRateLimit',
    'DefaultRateLimitBlocker',
    '_NoopRateLimitBlocker',
    'DefaultRateLimiter',
    'HTTPClient',
)
