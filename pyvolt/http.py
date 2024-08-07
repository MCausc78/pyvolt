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
from datetime import datetime, timedelta
import logging
import multidict
import typing

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
from .bot import BaseBot, Bot, PublicBot
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
from .enums import ChannelType, MessageSort, ContentReportReason, UserReportReason
from .errors import (
    HTTPException,
    Unauthorized,
    Forbidden,
    NotFound,
    Ratelimited,
    InternalServerError,
    BadGateway,
)
from .flags import MessageFlags, Permissions, ServerFlags, UserBadges, UserFlags
from .invite import BaseInvite, ServerInvite, Invite
from .message import (
    Reply,
    Interactions,
    Masquerade,
    SendableEmbed,
    BaseMessage,
    Message,
)
from .permissions import PermissionOverride
from .read_state import ReadState
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
from .user_settings import UserSettings
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

_L = logging.getLogger(__name__)


if typing.TYPE_CHECKING:
    from . import raw
    from .instance import Instance
    from .state import State


DEFAULT_HTTP_USER_AGENT = f'pyvolt API client (https://github.com/MCausc78/pyvolt, {version})'


_L = logging.getLogger(__name__)
_STATUS_TO_ERRORS = {
    401: Unauthorized,
    403: Forbidden,
    404: NotFound,
    429: Ratelimited,
    500: InternalServerError,
}


class HTTPClient:
    """The Revolt HTTP API client."""

    # To prevent unexpected 200's with HTML page the user must pass cookie with ``cf_clearance`` key.

    __slots__ = (
        'token',
        'bot',
        'state',
        '_session',
        'base',
        'cookie',
        'max_retries',
        'user_agent',
    )

    def __init__(
        self,
        token: str | None = None,
        *,
        base: str | None = None,
        bot: bool = True,
        cookie: str | None = None,
        max_retries: int | None = None,
        state: State,
        session: utils.MaybeAwaitableFunc[[HTTPClient], aiohttp.ClientSession] | aiohttp.ClientSession,
        user_agent: str | None = None,
    ) -> None:
        self.token = token
        self.bot = bot

        self.state = state
        if base is None:
            base = 'https://api.revolt.chat'
        self._session = session
        self.base = base
        self.cookie = cookie
        self.max_retries = max_retries or 3
        self.user_agent = user_agent or DEFAULT_HTTP_USER_AGENT

    def url_for(self, route: routes.CompiledRoute) -> str:
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
        return self.base.rstrip('/') + route.build()

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

    async def raw_request(
        self,
        route: routes.CompiledRoute,
        *,
        authenticated: bool = True,
        accept_json: bool = True,
        user_agent: str = '',
        mfa_ticket: str | None = None,
        json: UndefinedOr[typing.Any] = UNDEFINED,
        **kwargs,
    ) -> aiohttp.ClientResponse:
        """|coro|

        Perform a HTTP request, with ratelimiting and errors handling.

        Parameters
        ----------
        route: :class:`~routes.CompiledRoute`
            The route.
        authenticated: :class:`bool`
            Whether this route should have provided authentication or not. Defaults to ``True``.
        accept_json: :class:`bool`
            Whether to explicitly receive JSON or not. Defaults to ``True``.
        user_agent: :class:`str`
            The user agent to use for HTTP request. This is reserved field.
        mfa_ticket: Optional[:class:`str`]
            The MFA ticket to pass in headers.
        json: :class:`UndefinedOr`[typing.Any]
            The JSON payload to pass in.

        Raises
        ------
        HTTPException
            Something went wrong during request.

        Returns
        -------
        :class:`aiohttp.ClientResponse`
            The aiohttp response.
        """
        headers: multidict.CIMultiDict[typing.Any] = multidict.CIMultiDict(kwargs.pop('headers', {}))

        # Allow users to set cookie if Revolt is under attack mode
        cookie = kwargs.pop('cookie', self.cookie)
        if cookie:
            headers['cookie'] = cookie

        if self.token is not None and authenticated:
            headers['x-bot-token' if self.bot else 'x-session-token'] = self.token
        if accept_json:
            headers['accept'] = 'application/json'
        headers['user-agent'] = user_agent or self.user_agent
        if mfa_ticket is not None:
            headers['x-mfa-ticket'] = mfa_ticket
        retries = 0

        if json is not UNDEFINED:
            headers['content-type'] = 'application/json'
            kwargs['data'] = utils.to_json(json)

        method = route.route.method
        url = self.url_for(route)

        while True:
            _L.debug('sending request to %s %s with %s', method, url, kwargs.get('data'))

            session = self._session
            if callable(session):
                session = await utils._maybe_coroutine(session, self)
                # detect recursion
                if callable(session):
                    raise TypeError(f'Expected aiohttp.ClientSession, not {type(session)!r}')
                # Do not call factory on future requests
                self._session = session

            try:
                response = await session.request(
                    method,
                    url,
                    headers=headers,
                    **kwargs,
                )
            except OSError as exc:
                # TODO: Handle 10053?
                if exc.errno in (54, 10054):  # Connection reset by peer
                    await asyncio.sleep(1.5)
                    continue
                raise

            if response.status >= 400:
                _L.debug('%s %s has returned %s', method, url, kwargs.get('data'), response.status)

                if response.status == 502:
                    if retries >= self.max_retries:
                        raise BadGateway(response, await utils._json_or_text(response))
                    continue
                if response.status == 429:
                    if retries < self.max_retries:
                        j = await utils._json_or_text(response)
                        if isinstance(j, dict):
                            retry_after: float = j['retry_after'] / 1000.0
                        else:
                            retry_after = 1
                        _L.debug(
                            'ratelimited on %s %s, retrying in %.3f seconds',
                            method,
                            url,
                            retry_after,
                        )
                        await asyncio.sleep(retry_after)
                        continue
                j = await utils._json_or_text(response)
                if isinstance(j, dict) and isinstance(j.get('error'), dict):
                    error = j['error']
                    code = error.get('code')
                    reason = error.get('reason')
                    description = error.get('description')
                    j['type'] = 'RocketError'
                    j['err'] = f'{code} {reason}: {description}'
                raise _STATUS_TO_ERRORS.get(response.status, HTTPException)(response, j)
            return response

    async def request(
        self,
        route: routes.CompiledRoute,
        *,
        authenticated: bool = True,
        accept_json: bool = True,
        user_agent: str = '',
        mfa_ticket: str | None = None,
        json: UndefinedOr[typing.Any] = UNDEFINED,
        log: bool = True,
        **kwargs,
    ) -> typing.Any:
        """|coro|

        Perform a HTTP request, with ratelimiting and errors handling.

        Parameters
        ----------
        route: :class:`~routes.CompiledRoute`
            The route.
        authenticated: :class:`bool`
            Whether this route should have provided authentication or not. Defaults to ``True``.
        accept_json: :class:`bool`
            Whether to explicitly receive JSON or not. Defaults to ``True``.
        user_agent: :class:`str`
            The user agent to use for HTTP request. This is reserved field.
        mfa_ticket: Optional[:class:`str`]
            The MFA ticket to pass in headers.
        json: :class:`UndefinedOr`[typing.Any]
            The JSON payload to pass in.
        log: :class:`bool`
            Whether to log successful response or not. This option is intended to avoid catastrophic spam.

        Raises
        ------
        HTTPException
            Something went wrong during request.

        Returns
        -------
        Any
            The parsed JSON response.
        """
        response = await self.raw_request(
            route,
            authenticated=authenticated,
            accept_json=accept_json,
            user_agent=user_agent,
            mfa_ticket=mfa_ticket,
            json=json,
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

        Returns
        -------
        :class:`Instance`
            The instance.
        """
        resp: raw.RevoltConfig = await self.request(routes.ROOT.compile(), authenticated=False)
        return self.state.parser.parse_instance(resp)

    # Bots control
    async def create_bot(self, name: str) -> Bot:
        """|coro|

        Create a new Revolt bot.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        name: :class:`str`
            The bot name.

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

    async def delete_bot(self, bot: ULIDOr[BaseBot]) -> None:
        """|coro|

        Deletes the bot.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        bot: :class:`ULIDOr`[:class:`BaseBot`]
            The bot to delete.
        """
        await self.request(routes.BOTS_DELETE.compile(bot_id=resolve_id(bot)))

    async def edit_bot(
        self,
        bot: ULIDOr[BaseBot],
        *,
        name: UndefinedOr[str] = UNDEFINED,
        public: UndefinedOr[bool] = UNDEFINED,
        analytics: UndefinedOr[bool] = UNDEFINED,
        interactions_url: UndefinedOr[str | None] = UNDEFINED,
        reset_token: bool = False,
    ) -> Bot:
        """|coro|

        Edits the bot.

        Parameters
        ----------
        bot: :class:`ULIDOr`[:class:`BaseBot`]
            The bot to edit.
        name: :class:`UndefinedOr`[:class:`str`]
            The new bot name.
        public: :class:`UndefinedOr`[:class:`bool`]
            Whether the bot should be public (could be invited by anyone).
        analytics: :class:`UndefinedOr`[:class:`bool`]
            Whether to allow Revolt collect analytics about the bot.
        interactions_url: :class:`UndefinedOr`[Optional[:class:`str`]]
            The new bot interactions URL. For now, this parameter is reserved and does not do anything.
        reset_token: :class:`bool`
            Whether to reset bot token. The new token can be accessed via ``bot.token``.

        Returns
        -------
        :class:`Bot`
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

    async def get_bot(self, bot: ULIDOr[BaseBot]) -> Bot:
        """|coro|

        Retrieves the bot with the given ID.

        The bot must be owned by you.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        bot: :class:`ULIDOr`[:class:`BaseBot`]
            The ID of the bot.

        Returns
        -------
        :class:`Bot`
            The retrieved bot.
        """
        resp: raw.FetchBotResponse = await self.request(routes.BOTS_FETCH.compile(bot_id=resolve_id(bot)))
        return self.state.parser.parse_bot(resp['bot'], resp['user'])

    async def get_owned_bots(self) -> list[Bot]:
        """|coro|

        Retrieves all bots owned by you.

        .. note::
            This can only be used by non-bot accounts.

        Returns
        -------
        List[:class:`Bot`]
            The owned bots.
        """
        return self.state.parser.parse_bots(await self.request(routes.BOTS_FETCH_OWNED.compile()))

    async def get_public_bot(self, bot: ULIDOr[BaseBot]) -> PublicBot:
        """|coro|

        Retrieves the public bot with the given ID.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        bot: :class:`ULIDOr`[:class:`BaseBot`]
            The ID of the bot.

        Returns
        -------
        :class:`PublicBot`
            The retrieved bot.
        """
        return self.state.parser.parse_public_bot(
            await self.request(routes.BOTS_FETCH_PUBLIC.compile(bot_id=resolve_id(bot)))
        )

    @typing.overload
    async def invite_bot(
        self,
        bot: ULIDOr[BaseBot | BaseUser],
        *,
        server: ULIDOr[BaseServer],
    ) -> None: ...

    @typing.overload
    async def invite_bot(
        self,
        bot: ULIDOr[BaseBot | BaseUser],
        *,
        group: ULIDOr[GroupChannel],
    ) -> None: ...

    async def invite_bot(
        self,
        bot: ULIDOr[BaseBot | BaseUser],
        *,
        server: ULIDOr[BaseServer] | None = None,
        group: ULIDOr[GroupChannel] | None = None,
    ) -> None:
        """|coro|

        Invites a bot to a server or group.
        **Specifying both ``server`` and ``group`` parameters (or no parameters at all) will lead to an exception.**

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        bot: :class:`ULIDOr`[Union[:class:`BaseBot`, :class:`BaseUser`]]
            The bot.
        server: Optional[:class:`ULIDOr`[:class:`BaseServer`]]
            The destination server.
        group: Optional[:class:`ULIDOr`[:class:`GroupChannel`]]
            The destination group.

        Raises
        ------
        TypeError
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
    async def acknowledge_message(self, channel: ULIDOr[TextChannel], message: ULIDOr[BaseMessage]) -> None:
        """|coro|

        Marks this message as read.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        channel: :class:`ULIDOr`[:class:`TextChannel`]
            The channel.
        message: :class:`ULIDOr`[:class:`BaseMessage`]
            The message.

        Raises
        ------
        Forbidden
            You do not have permissions to see that message.
        HTTPException
            Acking message failed.
        """
        await self.request(
            routes.CHANNELS_CHANNEL_ACK.compile(
                channel_id=resolve_id(channel),
                message_id=resolve_id(message),
            )
        )

    async def close_channel(self, channel: ULIDOr[BaseChannel], silent: bool | None = None) -> None:
        """|coro|

        Deletes a server channel, leaves a group or closes a group.

        Parameters
        ----------
        channel: :class:`ULIDOr`[:class:`BaseChannel`]
            The channel.
        silent: Optional[:class:`bool`]
            Whether to not send message when leaving.

        Raises
        ------
        Forbidden
            You do not have permissions to close the channel.
        HTTPException
            Closing the channel failed.
        """
        p: raw.OptionsChannelDelete = {}
        if silent is not None:
            p['leave_silently'] = utils._bool(silent)
        await self.request(
            routes.CHANNELS_CHANNEL_DELETE.compile(channel_id=resolve_id(channel)),
            params=p,
        )

    async def edit_channel(
        self,
        channel: ULIDOr[BaseChannel],
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str | None] = UNDEFINED,
        owner: UndefinedOr[ULIDOr[BaseUser]] = UNDEFINED,
        icon: UndefinedOr[ResolvableResource | None] = UNDEFINED,
        nsfw: UndefinedOr[bool] = UNDEFINED,
        archived: UndefinedOr[bool] = UNDEFINED,
        default_permissions: UndefinedOr[None] = UNDEFINED,
    ) -> Channel:
        """|coro|

        Edits the channel.

        Parameters
        ----------
        channel: :class:`ULIDOr`[:class:`BaseChannel`]
            The channel.
        name: :class:`UndefinedOr`[:class:`str`]
            The new channel name. Only applicable when target channel is :class:`GroupChannel`, or :class:`ServerChannel`.
        description: :class:`UndefinedOr`[Optional[:class:`str`]]
            The new channel description. Only applicable when target channel is :class:`GroupChannel`, or :class:`ServerChannel`.
        owner: :class:`UndefinedOr`[:clsas:`ULIDOr`[:class:`BaseUser`]]
            The new channel owner. Only applicable when target channel is :class:`GroupChannel`.
        icon: :class:`UndefinedOr`[Optional[:class:`ResolvableResource`]]
            The new channel icon. Only applicable when target channel is :class:`GroupChannel`, or :class:`ServerChannel`.
        nsfw: :class:`UndefinedOr`[:class:`bool`]
            To mark the channel as NSFW or not. Only applicable when target channel is :class:`GroupChannel`, or :class:`ServerChannel`.
        archived: :class:`UndefinedOr`[:class:`bool`]
            To mark the channel as archived or not.
        default_permissions: :class:`UndefinedOr`[None]
            To remove default permissions or not. Only applicable when target channel is :class:`GroupChannel`, or :class:`ServerChannel`.

        Raises
        ------
        Forbidden
            You do not have permissions to edit the channel.
        HTTPException
            Editing the channel failed.

        Returns
        -------
        :class:`Channel`
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
        return self.state.parser.parse_channel(
            await self.request(
                routes.CHANNELS_CHANNEL_EDIT.compile(channel_id=resolve_id(channel)),
                json=payload,
            )
        )

    async def get_channel(self, channel: ULIDOr[BaseChannel]) -> Channel:
        """|coro|

        Retrieves a :class:`Channel` with the specified ID.

        Parameters
        ----------
        channel: :class:`ULIDOr`[:class:`BaseChannel`]
            The ID of the channel.

        Raises
        ------
        NotFound
            The channel does not exist.
        HTTPException
            Getting the channel failed.

        Returns
        -------
        :class:`Channel`
            The retrieved channel.
        """
        return self.state.parser.parse_channel(
            await self.request(routes.CHANNELS_CHANNEL_FETCH.compile(channel_id=resolve_id(channel)))
        )

    async def add_recipient_to_group(
        self,
        channel: ULIDOr[GroupChannel],
        user: ULIDOr[BaseUser],
    ) -> None:
        """|coro|

        Adds another user to the group.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        channel: :class:`ULIDOr`[:class:`GroupChannel`]
            The group.
        user: :class:`ULIDOr`[:class:`BaseUser`]
            The user to add.

        Raises
        ------
        Forbidden
            You're bot, lacking `InviteOthers` permission, or not friends with this user.
        HTTPException
            Adding user to the group failed.
        """
        await self.request(
            routes.CHANNELS_GROUP_ADD_MEMBER.compile(channel_id=resolve_id(channel), user_id=resolve_id(user))
        )

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
        payload: raw.DataCreateGroup = {'name': name}
        if description is not None:
            payload['description'] = description
        if recipients is not None:
            payload['users'] = [resolve_id(recipient) for recipient in recipients]
        if nsfw is not None:
            payload['nsfw'] = nsfw
        return self.state.parser.parse_group_channel(
            await self.request(routes.CHANNELS_GROUP_CREATE.compile(), json=payload),
            recipients=(True, []),
        )

    async def remove_recipient_from_group(
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
        channel: :class:`ULIDOr`[:class:`GroupChannel`]
            The group.
        user: :class:`ULID`[:class:`BaseUser`]
            The user to remove.

        Raises
        ------
        Forbidden
            You're not owner of group.
        HTTPException
            Removing the member from group failed.
        """
        await self.request(
            routes.CHANNELS_GROUP_REMOVE_MEMBER.compile(
                channel_id=resolve_id(channel),
                user_id=resolve_id(user),
            )
        )

    async def create_invite(self, channel: ULIDOr[GroupChannel | ServerChannel]) -> Invite:
        """|coro|

        Creates an invite to channel. The destination channel must be a group or server channel.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        channel: :class:`ULIDOr`[Union[:class:`GroupChannel`, :class:`ServerChannel`]]
            The invite destination channel.

        Raises
        ------
        Forbidden
            You do not have permissions to create invite in that channel.
        HTTPException
            Creating invite failed.

        Returns
        -------
        :class:`Invite`
            The invite that was created.
        """
        return self.state.parser.parse_invite(
            await self.request(routes.CHANNELS_INVITE_CREATE.compile(channel_id=resolve_id(channel)))
        )

    async def get_group_recipients(
        self,
        channel: ULIDOr[GroupChannel],
    ) -> list[User]:
        """|coro|

        Retrieves all recipients who are part of this group.

        Parameters
        ----------
        channel: :class:`ULIDOr`[:class:`GroupChannel`]
            The group channel.

        Raises
        ------
        HTTPException
            Getting group recipients failed.

        Returns
        -------
        List[:class:`User`]
            The group recipients.
        """
        return [
            self.state.parser.parse_user(user)
            for user in await self.request(
                routes.CHANNELS_MEMBERS_FETCH.compile(
                    channel_id=resolve_id(channel),
                )
            )
        ]

    async def bulk_delete_messages(
        self,
        channel: ULIDOr[TextChannel],
        messages: typing.Sequence[ULIDOr[BaseMessage]],
    ) -> None:
        """|coro|

        Delete multiple messages you've sent or one you have permission to delete.
        This will always require `ManageMessages` permission regardless of whether you own the message or not.
        Messages must have been sent within the past 1 week.

        Parameters
        ----------
        channel: :class:`ULIDOr`[:class:`TextChannel`]
            The channel.
        messages: :class:`typing.Sequence`[:class:`ULIDOr`[:class:`BaseMessage`]]
            The messages to delete.

        Raises
        ------
        Forbidden
            You do not have permissions to delete
        HTTPException
            Deleting messages failed.
        """
        payload: raw.OptionsBulkDelete = {'ids': [resolve_id(message) for message in messages]}
        await self.request(
            routes.CHANNELS_MESSAGE_BULK_DELETE.compile(channel_id=resolve_id(channel)),
            json=payload,
        )

    async def remove_all_reactions_from_message(
        self,
        channel: ULIDOr[TextChannel],
        message: ULIDOr[BaseMessage],
    ) -> None:
        """|coro|

        Removes your own, someone else's or all of a given reaction.
        Requires `ManageMessages` permission.

        Parameters
        ----------
        channel: :class:`ULIDOr`[:class:`TextChannel`]
            The channel.
        message: :class:`ULIDOr`[:class:`BaseMessage`]
            The message.

        Raises
        ------
        Forbidden
            You do not have permissions to remove all reactions from message.
        HTTPException
            Removing reactions from message failed.
        """
        await self.request(
            routes.CHANNELS_MESSAGE_CLEAR_REACTIONS.compile(
                channel_id=resolve_id(channel),
                message_id=resolve_id(message),
            )
        )

    async def delete_message(self, channel: ULIDOr[TextChannel], message: ULIDOr[BaseMessage]) -> None:
        """|coro|

        Deletes a message you've sent or one you have permission to delete.

        Parameters
        ----------
        channel: :class:`ULIDOr`[:class:`TextChannel`]
            The channel.
        message: :class:`ULIDOr`[:class:`BaseMessage`]
            The message.

        Raises
        ------
        Forbidden
            You do not have permissions to delete message.
        HTTPException
            Deleting the message failed.
        """
        await self.request(
            routes.CHANNELS_MESSAGE_DELETE.compile(
                channel_id=resolve_id(channel),
                message_id=resolve_id(message),
            )
        )

    async def edit_message(
        self,
        channel: ULIDOr[TextChannel],
        message: ULIDOr[BaseMessage],
        *,
        content: UndefinedOr[str] = UNDEFINED,
        embeds: UndefinedOr[list[SendableEmbed]] = UNDEFINED,
    ) -> Message:
        """|coro|

        Edits the message that you've previously sent.

        Parameters
        ----------
        channel: :class:`ULIDOr`[:class:`TextChannel`]
            The channel.
        message: :class:`ULIDOr`[:class:`BaseMessage`]
            The message.
        content: :class:`UndefinedOr`[:class:`str`]
            The new content to replace the message with.
        embeds: :class:`UndefinedOr`[List[:class:`SendableEmbed`]]
            The new embeds to replace the original with. Must be a maximum of 10. To remove all embeds ``[]`` should be passed.

        Raises
        ------
        Forbidden
            Tried to suppress a message without permissions or edited a message's content or embed that isn't yours.
        HTTPException
            Editing the message failed.

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
        return self.state.parser.parse_message(
            await self.request(
                routes.CHANNELS_MESSAGE_EDIT.compile(
                    channel_id=resolve_id(channel),
                    message_id=resolve_id(message),
                ),
                json=payload,
            )
        )

    async def get_message(self, channel: ULIDOr[TextChannel], message: ULIDOr[BaseMessage]) -> Message:
        """|coro|

        Retrieves a message.

        Parameters
        ----------
        channel: :class:`ULIDOr`[:class:`TextChannel`]
            The channel.
        message: :class:`ULIDOr`[:class:`BaseMessage`]
            The message.

        Raises
        ------
        Forbidden
            You do not have permissions to get message.
        HTTPException
            Getting the message failed.

        Returns
        -------
        :class:`Message`
            The retrieved message.
        """
        return self.state.parser.parse_message(
            await self.request(
                routes.CHANNELS_MESSAGE_FETCH.compile(
                    channel_id=resolve_id(channel),
                    message_id=resolve_id(message),
                )
            )
        )

    async def get_messages(
        self,
        channel: ULIDOr[TextChannel],
        *,
        limit: int | None = None,
        before: ULIDOr[BaseMessage] | None = None,
        after: ULIDOr[BaseMessage] | None = None,
        sort: MessageSort | None = None,
        nearby: ULIDOr[BaseMessage] | None = None,
        populate_users: bool | None = None,
    ) -> list[Message]:
        """|coro|

        Get multiple messages from the channel.

        Parameters
        ----------
        channel: :class:`ULIDOr`[:class:`TextChannel`]
            The channel.
        limit: Optional[:class:`int`]
            Maximum number of messages to get. For getting nearby messages, this is ``(limit + 1)``.
        before: Optional[:class:`ULIDOr`[:class:`BaseMessage`]]
            The message before which messages should be fetched.
        after: Optional[:class:`ULIDOr`[:class:`BaseMessage`]]
            The message after which messages should be fetched.
        sort: Optional[:class:`MessageSort`]
            The message sort direction.
        nearby: Optional[:class:`ULIDOr`[:class:`BaseMessage`]]
            The message to search around. Specifying ``nearby`` ignores ``before``, ``after`` and ``sort``. It will also take half of limit rounded as the limits to each side. It also fetches the message ID specified.
        populate_users: :class:`bool`
            Whether to populate user (and member, if server channel) objects.

        Raises
        ------
        Forbidden
            You do not have permissions to get channel message history.
        HTTPException
            Getting messages failed.

        Returns
        -------
        List[:class:`Message`]
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
        channel: ULIDOr[TextChannel],
        message: ULIDOr[BaseMessage],
        emoji: ResolvableEmoji,
    ) -> None:
        """|coro|

        React to a given message.

        Parameters
        ----------
        channel: :class:`ULIDOr`[:class:`TextChannel`]
            The channel.
        message: :class:`ULIDOr`[:class:`BaseMessage`]
            The message.
        emoji: :class:`ResolvableEmoji`
            The emoji to react with.

        Raises
        ------
        Forbidden
            You do not have permissions to react to message.
        HTTPException
            Reacting to message failed.
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
        channel: ULIDOr[TextChannel],
        query: str | None = None,
        *,
        pinned: bool | None = None,
        limit: int | None = None,
        before: ULIDOr[BaseMessage] | None = None,
        after: ULIDOr[BaseMessage] | None = None,
        sort: MessageSort | None = None,
        populate_users: bool | None = None,
    ) -> list[Message]:
        """|coro|

        Searches for messages.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        channel: :class:`ULIDOr`[:class:`TextChannel`]
            The channel to search in.
        query: Optional[:class:`str`]
            Full-text search query. See [MongoDB documentation](https://docs.mongodb.com/manual/text-search/#-text-operator) for more information.
        pinned: Optional[:class:`bool`]
            Whether to search for (un-)pinned messages or not.
        limit: Optional[:class:`int`]
            Maximum number of messages to fetch.
        before: Optional[:class:`ULIDOr`[:class:`BaseMessage`]]
            The message before which messages should be fetched.
        after: Optional[:class:`ULIDOr`[:class:`BaseMessage`]]
            The message after which messages should be fetched.
        sort: Optional[:class:`MessageSort`]
            Sort used for retrieving.
        populate_users: Optional[:class:`bool`]
            Whether to populate user (and member, if server channel) objects.

        Raises
        ------
        Forbidden
            You do not have permissions to search
        HTTPException
            Searching messages failed.

        Returns
        -------
        List[:class:`Message`]
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

        return self.state.parser.parse_messages(
            await self.request(
                routes.CHANNELS_MESSAGE_SEARCH.compile(channel_id=resolve_id(channel)),
                json=payload,
            )
        )

    async def pin_message(self, channel: ULIDOr[TextChannel], message: ULIDOr[BaseMessage], /) -> None:
        """|coro|

        Pins a message.
        You must have `ManageMessages` permission.

        Parameters
        ----------
        channel: :class:`ULIDOr`[:class:`TextChannel`]
            The channel.
        message: :class:`ULIDOr`[:class:`BaseMessage`]
            The message.

        Raises
        ------
        Forbidden
            You do not have permissions to pin message.
        HTTPException
            Pinning the message failed.
        """
        await self.request(
            routes.CHANNELS_MESSAGE_PIN.compile(
                channel_id=resolve_id(channel),
                message_id=resolve_id(message),
            )
        )

    async def send_message(
        self,
        channel: ULIDOr[TextChannel],
        content: str | None = None,
        *,
        nonce: str | None = None,
        attachments: list[ResolvableResource] | None = None,
        replies: list[Reply | ULIDOr[BaseMessage]] | None = None,
        embeds: list[SendableEmbed] | None = None,
        masquerade: Masquerade | None = None,
        interactions: Interactions | None = None,
        silent: bool | None = None,
    ) -> Message:
        """|coro|

        Sends a message to the given channel.
        You must have `SendMessages` permission.

        Parameters
        ----------
        channel: :class:`ULIDOr`[:class:`TextChannel`]
            The channel.
        content: Optional[:class:`str`]
            The message content.
        nonce: Optional[:class:`str`]
            The message nonce.
        attachments: Optional[List[:class:`ResolvableResource`]]
            The message attachments.
        replies: Optional[List[Union[:class:`Reply`, :class:`ULIDOr`[:class:`BaseMessage`]]]]
            The message replies.
        embeds: Optional[List[:class:`SendableEmbed`]]
            The message embeds.
        masquearde: Optional[:class:`Masquerade`]
            The message masquerade.
        interactions: Optional[:class:`Interactions`]
            The message interactions.
        silent: Optional[:class:`bool`]
            Whether to suppress notifications or not.

        Raises
        ------
        Forbidden
            You do not have permissions to send
        HTTPException
            Sending the message failed.

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
            flags = 0
            if silent:
                flags |= MessageFlags.SUPPRESS_NOTIFICATIONS

        if flags is not None:
            payload['flags'] = flags

        headers = {}
        if nonce is not None:
            headers['Idempotency-Key'] = nonce
        return self.state.parser.parse_message(
            await self.request(
                routes.CHANNELS_MESSAGE_SEND.compile(channel_id=resolve_id(channel)),
                json=payload,
                headers=headers,
            )
        )

    async def unpin_message(self, channel: ULIDOr[TextChannel], message: ULIDOr[BaseMessage], /) -> None:
        """|coro|

        Unpins a message.
        You must have `ManageMessages` permission.

        Parameters
        ----------
        channel: :class:`ULIDOr`[:class:`TextChannel`]
            The channel.
        message: :class:`ULIDOr`[:class:`BaseMessage`]
            The message.

        Raises
        ------
        Forbidden
            You do not have permissions to unpin messages.
        HTTPException
            Unpinning the message failed.
        """
        await self.request(
            routes.CHANNELS_MESSAGE_PIN.compile(
                channel_id=resolve_id(channel),
                message_id=resolve_id(message),
            )
        )

    async def remove_reactions_from_message(
        self,
        channel: ULIDOr[TextChannel],
        message: ULIDOr[BaseUser],
        emoji: ResolvableEmoji,
        /,
        *,
        user: ULIDOr[BaseUser] | None = None,
        remove_all: bool | None = None,
    ) -> None:
        """|coro|

        Remove your own, someone else's or all of a given reaction.
        Requires `ManageMessages` permission if changing other's reactions.

        Parameters
        ----------
        channel: :class:`ULIDOr`[:class:`TextChannel`]
            The channel.
        message: :class:`ULIDOr`[:class:`BaseMessage`]
            The message.
        emoji: :class:`ResolvableEmoji`
            The emoji to remove.
        user: Optional[:class:`ULIDOr`[:class:`BaseUser`]]
            Remove reactions from this user. Requires `ManageMessages` permission if provided.
        remove_all: Optional[:class:`bool`]
            Whether to remove all reactions. Requires `ManageMessages` permission if provided.

        Raises
        ------
        Forbidden
            You do not have permissions to remove reactions from message.
        HTTPException
            Removing reactions from message failed.
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
        /,
        *,
        allow: Permissions = Permissions.NONE,
        deny: Permissions = Permissions.NONE,
    ) -> ServerChannel:
        """|coro|

        Sets permissions for the specified role in a channel. Channel must be a :class:`ServerChannel`.

        Parameters
        ----------
        channel: :class:`ULIDOr`[:class:`ServerChannel`]
            The channel.
        role: :class:`ULIDOr`[:class:`BaseRole`]
            The role.

        Raises
        ------
        Forbidden
            You do not have permissions to set role permissions on the channel.
        HTTPException
            Setting permissions failed.

        Returns
        -------
        :class:`ServerChannel`
            The updated server channel with new permissions.
        """
        payload: raw.DataSetRolePermissions = {'permissions': {'allow': allow.value, 'deny': deny.value}}
        r = self.state.parser.parse_channel(
            await self.request(
                routes.CHANNELS_PERMISSIONS_SET.compile(
                    channel_id=resolve_id(channel),
                    role_id=resolve_id(role),
                ),
                json=payload,
            )
        )
        return r  # type: ignore

    async def set_default_channel_permissions(
        self,
        channel: ULIDOr[GroupChannel | ServerChannel],
        permissions: Permissions | PermissionOverride,
        /,
    ) -> GroupChannel | ServerChannel:
        """|coro|

        Sets permissions for the default role in a channel.
        Channel must be a :class:`GroupChannel`, or :class:`ServerChannel`.

        Parameters
        ----------
        channel: :class:`ULIDOr`[Union[:class:`GroupChannel`, :class:`ServerChannel`]]
            The channel.
        permissions: Union[:class:`Permissions`, :class:`PermissionOverride`]
            The new permissions. Should be :class:`Permissions` for groups and :class:`PermissionOverride` for server channels.

        Raises
        ------
        Forbidden
            You do not have permissions to set default permissions on the channel.
        HTTPException
            Setting permissions failed.

        Returns
        -------
        Union[:class:`GroupChannel`, :class:`ServerChannel`]
            The updated group/server channel with new permissions.
        """
        payload: raw.DataDefaultChannelPermissions = {
            'permissions': (permissions.build() if isinstance(permissions, PermissionOverride) else permissions.value)
        }
        r = self.state.parser.parse_channel(
            await self.request(
                routes.CHANNELS_PERMISSIONS_SET_DEFAULT.compile(channel_id=resolve_id(channel)),
                json=payload,
            )
        )
        return r  # type: ignore

    async def join_call(self, channel: ULIDOr[DMChannel | GroupChannel | VoiceChannel]) -> str:
        """|coro|

        Asks the voice server for a token to join the call.

        Parameters
        ----------
        channel: :class:`ULIDOr`[Union[:class:`DMChannel`, :class:`GroupChannel`, :class:`VoiceChannel`]]
            The channel.

        Raises
        ------
        HTTPException
            Asking for the token failed.

        Returns
        -------
        :class:`str`
            Token for authenticating with the voice server.
        """
        d: raw.LegacyCreateVoiceUserResponse = await self.request(
            routes.CHANNELS_VOICE_JOIN.compile(channel_id=resolve_id(channel))
        )
        return d['token']

    async def create_webhook(
        self,
        channel: ULIDOr[GroupChannel | TextChannel],
        /,
        *,
        name: str,
        avatar: ResolvableResource | None = None,
    ) -> Webhook:
        """|coro|

        Creates a webhook which 3rd party platforms can use to send.

        Parameters
        ----------
        channel: :class:`ULIDOr`[Union[:class:`GroupChannel`, :class:`TextChannel`]]
            The channel to create webhook in.
        name: :class:`str`
            The webhook name. Must be between 1 and 32 chars long.
        avatar: Optional[:class:`ResolvableResource`]
            The webhook avatar.

        Raises
        ------
        Forbidden
            You do not have permissions to create the webhook.
        HTTPException
            Creating the webhook failed.

        Returns
        -------
        :class:`Webhook`
            The created webhook.
        """
        payload: raw.CreateWebhookBody = {'name': name}
        if avatar is not None:
            payload['avatar'] = await resolve_resource(self.state, avatar, tag='avatars')
        return self.state.parser.parse_webhook(
            await self.request(
                routes.CHANNELS_WEBHOOK_CREATE.compile(channel_id=resolve_id(channel)),
                json=payload,
            )
        )

    async def get_channel_webhooks(self, channel: ULIDOr[ServerChannel], /) -> list[Webhook]:
        """|coro|

        Gets the list of webhooks from this channel.

        Raises
        ------
        Forbidden
            You don't have permissions to get the webhooks.
        HTTPException
            Getting channel webhooks failed.

        Returns
        -------
        List[:class:`Webhook`]
            The webhooks for this channel.
        """
        return [
            self.state.parser.parse_webhook(e)
            for e in await self.request(routes.CHANNELS_WEBHOOK_FETCH_ALL.compile(channel_id=resolve_id(channel)))
        ]

    # Customization control (emojis)
    async def create_emoji(
        self,
        server: ULIDOr[BaseServer],
        data: ResolvableResource,
        /,
        *,
        name: str,
        nsfw: bool | None = None,
    ) -> ServerEmoji:
        """|coro|

        Create an emoji on the server.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        server: :class:`ULIDOr`[:class:`BaseServer`]
            The server.
        data: :class:`ResolvableResource`
            The emoji data.
        name: :class:`str`
            The emoji name. Must be at least 2 characters.
        nsfw: Optional[:class:`bool`]
            To mark the emoji as NSFW or not.

        Raises
        ------
        Forbidden
            You do not have permissions to create emoji.
        HTTPException
            Creating the emoji failed.

        Returns
        -------
        :class:`ServerEmoji`
            The created emoji.
        """
        payload: raw.DataCreateEmoji = {
            'name': name,
            'parent': {'type': 'Server', 'id': resolve_id(server)},
        }
        if nsfw is not None:
            payload['nsfw'] = nsfw
        return self.state.parser.parse_server_emoji(
            await self.request(
                routes.CUSTOMISATION_EMOJI_CREATE.compile(
                    attachment_id=await resolve_resource(self.state, data, tag='emojis')
                ),
                json=payload,
            )
        )

    async def delete_emoji(self, emoji: ULIDOr[ServerEmoji], /) -> None:
        """|coro|

        Deletes a emoji.

        Parameters
        ----------
        emoji: :class:`ULIDOr`[:class:`ServerEmoji`]
            The emoji to delete.

        Raises
        ------
        Forbidden
            You do not have permissions to delete emojis.
        HTTPException
            Deleting the emoji failed.
        """
        await self.request(routes.CUSTOMISATION_EMOJI_DELETE.compile(emoji_id=resolve_id(emoji)))

    async def get_emoji(self, emoji: ULIDOr[BaseEmoji], /) -> Emoji:
        """|coro|

        Retrieves a custom emoji.

        Parameters
        ----------
        emoji: :class:`ULIDOr`[:class:`BaseEmoji`]
            The emoji.

        Raises
        ------
        HTTPException
            An error occurred fetching the emoji.

        Returns
        -------
        :class:`Emoji`
            The retrieved emoji.
        """

        return self.state.parser.parse_emoji(
            await self.request(routes.CUSTOMISATION_EMOJI_FETCH.compile(emoji_id=resolve_id(emoji)))
        )

    # Invites control
    async def delete_invite(self, code: str | BaseInvite, /) -> None:
        """|coro|

        Deletes a invite.

        Parameters
        ----------
        code: Union[:class:`str`, :class:`BaseInvite`]
            The invite code.

        Raises
        ------
        Forbidden
            You do not have permissions to delete invite or not creator of that invite.
        HTTPException
            Deleting the invite failed.
        """
        invite_code = code.code if isinstance(code, BaseInvite) else code
        await self.request(routes.INVITES_INVITE_DELETE.compile(invite_code=invite_code))

    async def get_invite(self, code: str | BaseInvite, /) -> BaseInvite:
        """|coro|

        Gets an invite.

        Parameters
        ----------
        code: Union[:class:`str`, :class:`BaseInvite`]
            The invite code.

        Raises
        ------
        NotFound
            The invite is invalid.
        HTTPException
            Getting the invite failed.
        """
        invite_code = code.code if isinstance(code, BaseInvite) else code
        return self.state.parser.parse_public_invite(
            await self.request(
                routes.INVITES_INVITE_FETCH.compile(invite_code=invite_code),
                authenticated=False,
            )
        )

    async def accept_invite(self, code: str | BaseInvite, /) -> Server | GroupChannel:
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
        Forbidden
            You're banned.
        HTTPException
            Accepting the invite failed.

        Returns
        -------
        Union[:class:`Server`, :class:`GroupChannel`]
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
            return self.state.parser.parse_group_channel(
                resp['channel'],
                (False, [self.state.parser.parse_user(u) for u in resp['users']]),
            )
        else:
            raise NotImplementedError(resp)

    # Onboarding control
    async def complete_onboarding(self, username: str, /) -> OwnUser:
        """|coro|

        Set a new username, complete onboarding and allow a user to start using Revolt.

        Parameters
        ----------
        username: :class:`str`
            The username to use.

        Returns
        -------
        :class:`OwnUser`
            The updated user.
        """
        payload: raw.DataOnboard = {'username': username}
        return self.state.parser.parse_own_user(await self.request(routes.ONBOARD_COMPLETE.compile(), json=payload))

    async def onboarding_status(self) -> bool:
        """|coro|

        Whether the current account requires onboarding or whether you can continue to send requests as usual.
        You may skip calling this if you're restoring an existing session.
        """
        d: raw.DataHello = await self.request(routes.ONBOARD_HELLO.compile())
        return d['onboarding']

    # Web Push control
    async def push_subscribe(self, *, endpoint: str, p256dh: str, auth: str) -> None:
        """|coro|

        Create a new Web Push subscription. If an subscription already exists on this session, it will be removed.
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
        additional_context: str | None = None,
    ) -> None:
        """|coro|

        Report a piece of content to the moderation team.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        HTTPException
            Trying to self-report, or reporting the message failed.
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
        /,
        *,
        additional_context: str | None = None,
    ) -> None:
        """|coro|

        Report a piece of content to the moderation team.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        HTTPException
            You're trying to self-report, or reporting the server failed.
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
        /,
        *,
        additional_context: str | None = None,
        message_context: ULIDOr[BaseMessage],
    ) -> None:
        """|coro|

        Report a piece of content to the moderation team.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        HTTPException
            You're trying to self-report, or reporting the user failed.
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
        reason: str | None = None,
    ) -> Ban:
        """|coro|

        Bans a user from the server.

        Parameters
        ----------
        server: :class:`ULIDOr`[:class:`BaseServer`]
            The server.
        user: Union[:class:`str`, :class:`BaseUser`, :class:`BaseMember`]
            The user to ban from the server.
        reason: Optional[:class:`str`]
            The ban reason. Should be between 1 and 1024 chars long.

        Raises
        ------
        Forbidden
            You do not have permissions to ban the user.
        HTTPException
            Banning the user failed.
        """
        payload: raw.DataBanCreate = {'reason': reason}
        return self.state.parser.parse_ban(
            await self.request(
                routes.SERVERS_BAN_CREATE.compile(server_id=resolve_id(server), user_id=resolve_id(user)),
                json=payload,
            ),
            {},
        )

    async def get_bans(self, server: ULIDOr[BaseServer], /) -> list[Ban]:
        """|coro|

        Retrieves all bans on a server.

        Parameters
        ----------
        server: :class:`ULIDOr`[:class:`BaseServer`]
            The server.

        Returns
        -------
        List[:class:`Ban`]
            The ban entries.
        """
        return self.state.parser.parse_bans(
            await self.request(routes.SERVERS_BAN_LIST.compile(server_id=resolve_id(server)))
        )

    async def unban(self, server: ULIDOr[BaseServer], user: ULIDOr[BaseUser]) -> None:
        """|coro|

        Unbans a user from the server.

        Parameters
        ----------
        server: :class:`ULIDOr`[:class:`BaseServer`]
            The server.
        user: :class:`ULIDOr`[:class:`BaseUser`]
            The user to unban from the server.

        Raises
        ------
        Forbidden
            You do not have permissions to unban the user.
        HTTPException
            Unbanning the user failed.
        """
        await self.request(
            routes.SERVERS_BAN_REMOVE.compile(server_id=resolve_id(server), user_id=resolve_id(user)),
        )

    async def create_server_channel(
        self,
        server: ULIDOr[BaseServer],
        /,
        *,
        type: ChannelType | None = None,
        name: str,
        description: str | None = None,
        nsfw: bool | None = None,
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
        Forbidden
            You do not have permissions to create the channel.
        HTTPException
            Creating the channel failed.
        """
        payload: raw.DataCreateServerChannel = {'name': name}
        if type is not None:
            payload['type'] = type.value
        if description is not None:
            payload['description'] = description
        if nsfw is not None:
            payload['nsfw'] = nsfw
        channel = self.state.parser.parse_channel(
            await self.request(
                routes.SERVERS_CHANNEL_CREATE.compile(server_id=resolve_id(server)),
                json=payload,
            )
        )
        assert isinstance(channel, ServerChannel)
        return channel

    async def get_server_emojis(self, server: ULIDOr[BaseServer]) -> list[ServerEmoji]:
        """|coro|

        Retrieves all custom :class:`ServerEmoji`s from the server.

        Parameters
        ----------
        server: :class:`ULIDOr`[:class:`BaseServer`]
            The server.

        Returns
        -------
        List[:class:`ServerEmoji`]
            The retrieved emojis.
        """
        return [
            self.state.parser.parse_server_emoji(e)
            for e in await self.request(routes.SERVERS_EMOJI_LIST.compile(server_id=resolve_id(server)))
        ]

    async def get_server_invites(self, server: ULIDOr[BaseServer], /) -> list[ServerInvite]:
        """|coro|

        Returns a list of all invites from the server.

        Parameters
        ----------
        server: :class:`ULIDOr`[:class:`BaseServer`]
            The server.

        Raises
        ------
        Forbidden
            You do not have permissions to manage the server.
        HTTPException
            Getting the invites failed.

        Returns
        -------
        List[:class:`ServerInvite`]
            The retrieved invites.
        """
        return [
            self.state.parser.parse_server_invite(i)
            for i in await self.request(routes.SERVERS_INVITES_FETCH.compile(server_id=resolve_id(server)))
        ]

    async def edit_member(
        self,
        server: ULIDOr[BaseServer],
        member: str | BaseUser | BaseMember,
        /,
        *,
        nick: UndefinedOr[str | None] = UNDEFINED,
        avatar: UndefinedOr[ResolvableResource | None] = UNDEFINED,
        roles: UndefinedOr[list[ULIDOr[BaseRole]] | None] = UNDEFINED,
        timeout: UndefinedOr[datetime | timedelta | float | int | None] = UNDEFINED,
    ) -> Member:
        """|coro|

        Edits the member.

        Parameters
        ----------
        server: :class:`BaseServer`
            The server.
        member: Union[:class:`str`, :class:`BaseUser`, :class:`BaseMember`]
            The member.
        nick: :class:`UndefinedOr`[Optional[:class:`str`]]
            The member's new nick. Use ``None`` to remove the nickname.
        avatar: :class:`UndefinedOr`[Optional[:class:`ResolvableResource`]]
            The member's new avatar. Use ``None`` to remove the avatar. You can only change your own server avatar.
        roles: :class:`UndefinedOr`[Optional[List[:class:`BaseRole`]]]
            The member's new list of roles. This *replaces* the roles.
        timeout: :class:`UndefinedOr`[Optional[Union[:class:`datetime`, :class:`timedelta`, :class:`float`, :class:`int`]]]
            The duration/date the member's timeout should expire, or ``None`` to remove the timeout.
            This must be a timezone-aware datetime object. Consider using :func:`utils.utcnow()`.

        Returns
        -------
        :class:`Member`
            The newly updated member.
        """
        payload: raw.DataMemberEdit = {}
        remove: list[raw.FieldsMember] = []
        if nick is not UNDEFINED:
            if nick is not None:
                payload['nickname'] = nick
            else:
                remove.append('Nickname')
        if avatar is not UNDEFINED:
            if avatar is not None:
                payload['avatar'] = await resolve_resource(self.state, avatar, tag='avatars')
            else:
                remove.append('Avatar')
        if roles is not UNDEFINED:
            if roles is not None:
                payload['roles'] = [resolve_id(e) for e in roles]
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
        if len(remove) > 0:
            payload['remove'] = remove

        resp: raw.Member = await self.request(
            routes.SERVERS_MEMBER_EDIT.compile(
                server_id=resolve_id(server),
                member_id=resolve_id(member),
            ),
            json=payload,
        )
        return self.state.parser.parse_member(resp)

    async def query_members_by_name(self, server: ULIDOr[BaseServer], query: str, /) -> list[Member]:
        """|coro|

        Query members by a given name, this API is not stable and will be removed in the future.

        Parameters
        ----------
        server: :class:`ULIDOr`[:class:`BaseServer`]
            The server.
        query: :class:`str`
            The query to search members for.

        Returns
        -------
        List[:class:`Member`]
            The members matched.
        """
        return self.state.parser.parse_members_with_users(
            await self.request(
                routes.SERVERS_MEMBER_EXPERIMENTAL_QUERY.compile(server_id=resolve_id(server)),
                params={
                    'query': query,
                    'experimental_api': 'true',
                },
            )
        )

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
        server: :class:`ULIDOr`[:class:`BaseServer`]
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
                member_id=resolve_id(member),
            )
        )
        return self.state.parser.parse_member(resp)

    async def get_members(self, server: ULIDOr[BaseServer], /, *, exclude_offline: bool | None = None) -> list[Member]:
        """|coro|

        Retrieves all server members.

        Parameters
        ----------
        server: :class:`ULIDOr`[:class:`BaseServer`]
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
        self, server: ULIDOr[BaseServer], /, *, exclude_offline: bool | None = None
    ) -> MemberList:
        """|coro|

        Retrieves server members list.

        Parameters
        ----------
        server: :class:`ULIDOr`[:class:`BaseServer`]
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
        server: :class:`ULIDOr`[:class:`BaseServer`]
            The server.
        member: :class:`Union`[:class:`str`, :class:`BaseUser`, :class:`BaseMember`]
            The member to kick.

        Raises
        ------
        Forbidden
            You do not have permissions to kick the member.
        HTTPException
            Kicking the member failed.
        """
        await self.request(
            routes.SERVERS_MEMBER_REMOVE.compile(server_id=resolve_id(server), member_id=resolve_id(member))
        )

    async def set_server_permissions_for_role(
        self,
        server: ULIDOr[BaseServer],
        role: ULIDOr[BaseRole],
        /,
        *,
        allow: Permissions = Permissions.NONE,
        deny: Permissions = Permissions.NONE,
    ) -> Server:
        """|coro|

        Sets permissions for the specified role in the server.

        Parameters
        ----------
        server: :class:`ULIDOr`[:class:`BaseServer`]
            The server.
        role: :class:`ULIDOr`[:class:`BaseRole`]
            The role.
        allow: :class:`Permissions`
            New allow flags.
        deny: :class:`Permissions`
            New deny flags.

        Raises
        ------
        Forbidden
            You do not have permissions to set role permissions on the server.
        HTTPException
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
        server: :class:`ULIDOr`[:class:`BaseServer`]
            The server.
        permissions: :class:`Permissions`
            New default permissions.

        Raises
        ------
        Forbidden
            You do not have permissions to set default permissions on the server.
        HTTPException
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

    async def create_role(self, server: ULIDOr[BaseServer], /, *, name: str, rank: int | None = None) -> Role:
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
        Forbidden
            You do not have permissions to create the role.
        HTTPException
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
        server: :class:`ULIDOr`[:class:`BaseServer`]
            The server.
        role: :class:`ULIDOr`[:class:`BaseRole`]
            The role to delete.

        Raises
        ------
        Forbidden
            You do not have permissions to delete the role.
        HTTPException
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
        colour: UndefinedOr[str | None] = UNDEFINED,
        hoist: UndefinedOr[bool] = UNDEFINED,
        rank: UndefinedOr[int] = UNDEFINED,
    ) -> Role:
        """|coro|

        Edits the role.

        Parameters
        ----------
        server: :class:`ULIDOr`[:class:`BaseServer`]
            The server.
        role: :class:`ULIDOr`[:class:`BaseRole`]
            The role to edit.
        name: :class:`UndefinedOr`[:class:`str`]
            New role name. Should be between 1 and 32 chars long.
        colour: :class:`UndefinedOr`[Optional[:class:`str`]]
            New role colour. This should be valid CSS colour.
        hoist: :class:`UndefinedOr`[:class:`bool`]
            Whether this role should be displayed separately.
        rank: :class:`UndefinedOr`[:class:`int`]
            The new ranking position. Smaller values take priority.

        Raises
        ------
        Forbidden
            You do not have permissions to edit the role.
        HTTPException
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
        if colour is not UNDEFINED:
            if colour is not None:
                payload['colour'] = colour
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

        return self.state.parser.parse_role(
            await self.request(
                routes.SERVERS_ROLES_EDIT.compile(server_id=resolve_id(server), role_id=resolve_id(role)),
                json=payload,
            ),
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
        server: :class:`ULIDOr`[:class:`BaseServer`]
            The server.
        role: :class:`ULIDOr`[:class:`BaseRole`]
            The ID of the role to retrieve.

        Raises
        ------
        NotFound
            The role does not exist.
        HTTPException
            Getting the role failed.

        Returns
        -------
        :class:`Role`
            The retrieved role.
        """
        server_id = resolve_id(server)
        role_id = resolve_id(role)

        return self.state.parser.parse_role(
            await self.request(routes.SERVERS_ROLES_FETCH.compile(server_id=server_id, role_id=role_id)),
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
        server: :class:`ULIDOr`[:class:`BaseServer`]
            The server to mark as read.
        """
        await self.request(routes.SERVERS_SERVER_ACK.compile(server_id=resolve_id(server)))

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
        server: :class:`ULIDOr`[:class:`BaseServer`]
            The server to delete.
        """
        await self.request(routes.SERVERS_SERVER_DELETE.compile(server_id=resolve_id(server)))

    async def leave_server(self, server: ULIDOr[BaseServer], /, *, silent: bool | None = None) -> None:
        """|coro|

        Leaves the server if not owner otherwise deletes it.

        Parameters
        ----------
        server: :class:`ULIDOr`[:class:`BaseServer`]
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
        description: UndefinedOr[str | None] = UNDEFINED,
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
        server: :class:`ULIDOr`[:class:`BaseServer`]
            The server to edit.
        name: :class:`UndefinedOr`[:class:`str`]
            New server name. Should be between 1 and 32 chars long.
        description: :class:`UndefinedOr`[Optional[:class:`str`]]
            New server description. Can be 1024 chars maximum long.
        icon: :class:`UndefinedOr`[Optional[:class:`ResolvableResource`]]
            New server icon.
        banner: :class:`UndefinedOr`[Optional[:class:`ResolvableResource`]]
            New server banner.
        categories: :class:`UndefinedOr`[Optional[List[:class:`Category`]]]
            New category structure for this server.
        system_messsages: :class:`UndefinedOr`[Optional[:class:`SystemMessageChannels`]]
            New system message channels configuration.
        flags: :class:`UndefinedOr`[:class:`ServerFlags`]
            The new server flags. Can be passed only if you're privileged user.
        discoverable: :class:`UndefinedOr`[:class:`bool`]
            Whether this server is public and should show up on [Revolt Discover](https://rvlt.gg). Can be passed only if you're privileged user.
        analytics: :class:`UndefinedOr`[:class:`bool`]
            Whether analytics should be collected for this server. Must be enabled in order to show up on [Revolt Discover](https://rvlt.gg).

        Raises
        ------
        Forbidden
            You do not have permissions to edit the server.
        HTTPException
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
        populate_channels: bool | None = None,
    ) -> Server:
        """|coro|

        Retrieves a :class:`Server`.

        Parameters
        ----------
        server: :class:`ULIDOr`[:class:`BaseServer`]
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
    async def get_user_settings(self, keys: list[str] = [], /) -> UserSettings:
        """|coro|

        Get user settings from server filtered by keys.

        .. note::
            This can only be used by non-bot accounts.
        """
        # Sync endpoints aren't meant to be used with bot accounts
        payload: raw.OptionsFetchSettings = {'keys': keys}
        return self.state.parser.parse_user_settings(
            await self.request(routes.SYNC_GET_SETTINGS.compile(), json=payload),
            partial=True,
        )

    async def get_read_states(self) -> list[ReadState]:
        """|coro|

        Get information about unread state on channels.

        .. note::
            This can only be used by non-bot accounts.

        Returns
        -------
        List[:class:`ReadState`]
            The channel read states.
        """
        return [self.state.parser.parse_read_state(rs) for rs in await self.request(routes.SYNC_GET_UNREADS.compile())]

    async def edit_user_settings(
        self,
        dict_settings: dict[str, str] = {},
        edited_at: datetime | int | None = None,
        /,
        **kwargs: str,
    ) -> None:
        """|coro|

        Modify current user settings.

        .. note::
            This can only be used by non-bot accounts.
        """

        params: raw.OptionsSetSettings = {}

        if edited_at is not None:
            if isinstance(edited_at, datetime):
                edited_at = int(edited_at.timestamp())
            params['timestamp'] = edited_at

        payload: dict[str, str] = {}
        for k, v in (dict_settings | kwargs).items():
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
        user: :class:`ULIDOr`[:class:`BaseUser`]
            The user to friend with.

        Returns
        -------
        :class:`User`
            The friended user.
        """
        return self.state.parser.parse_user(
            await self.request(routes.USERS_ADD_FRIEND.compile(user_id=resolve_id(user)))
        )

    async def block_user(self, user: ULIDOr[BaseUser], /) -> User:
        """|coro|

        Block another user.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        user: :class:`ULIDOr`[:class:`BaseUser`]
            The user to block.

        Returns
        -------
        :class:`User`
            The blocked user.
        """
        return self.state.parser.parse_user(
            await self.request(routes.USERS_BLOCK_USER.compile(user_id=resolve_id(user)))
        )

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
        return self.state.parser.parse_own_user(
            await self.request(
                routes.USERS_CHANGE_USERNAME.compile(),
                json=payload,
            )
        )

    async def _edit_user(
        self,
        route: routes.CompiledRoute,
        /,
        *,
        display_name: UndefinedOr[str | None] = UNDEFINED,
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
        display_name: UndefinedOr[str] = UNDEFINED,
        avatar: UndefinedOr[ResolvableResource | None] = UNDEFINED,
        status: UndefinedOr[UserStatusEdit] = UNDEFINED,
        profile: UndefinedOr[UserProfileEdit] = UNDEFINED,
        badges: UndefinedOr[UserBadges] = UNDEFINED,
        flags: UndefinedOr[UserFlags] = UNDEFINED,
    ) -> OwnUser:
        """|coro|

        Edits the user.

        Parameters
        ----------
        display_name: :class:`UndefinedOr`[Optional[:class:`str`]]
            New display name. Pass ``None`` to remove it.
        avatar: :class:`UndefinedOr`[Optional[:class:`ResolvableResource`]]
            New avatar. Pass ``None`` to remove it.
        status: :class:`UndefinedOr`[:class:`UserStatusEdit`]
            New user status.
        profile: :class:`UndefinedOr`[:class:`UserProfileEdit`]
            New user profile data. This is applied as a partial.
        badges: :class:`UndefinedOr`[:class:`UserBadges`]
            The new user badges.
        flags: :class:`UndefinedOr`[:class:`UserFlags`]
            The new user flags.

        Raises
        ------
        HTTPException
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
        display_name: UndefinedOr[str] = UNDEFINED,
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
        user: :class:`ULIDOr`[:class:`BaseUser`]
            The user to edit.
        display_name: :class:`UndefinedOr`[Optional[:class:`str`]]
            New display name. Pass ``None`` to remove it.
        avatar: :class:`UndefinedOr`[Optional[:class:`ResolvableULID`]]
            New avatar. Pass ``None`` to remove it.
        status: :class:`UndefinedOr`[:class:`UserStatusEdit`]
            New user status.
        profile: :class:`UndefinedOr`[:class:`UserProfileEdit`]
            New user profile data. This is applied as a partial.
        badges: :class:`UndefinedOr`[:class:`UserBadges`]
            The new user badges.
        flags: :class:`UndefinedOr`[:class:`UserFlags`]
            The new user flags.

        Raises
        ------
        HTTPException
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
        result = [self.state.parser.parse_channel(e) for e in await self.request(routes.USERS_FETCH_DMS.compile())]
        return result  # type: ignore # The returned channels are always DM/Groups

    async def get_user_profile(self, user: ULIDOr[BaseUser], /) -> UserProfile:
        """|coro|

        Retrieve a user's profile data.

        Parameters
        ----------
        user: :class:`ULIDOr`[:class:`BaseUser`]
            The user.

        Raises
        ------
        Forbidden
            You do not have permission to access the user's profile.

        Returns
        -------
        :class:`UserProfile`
            The retrieved user profile.
        """
        user_id = resolve_id(user)
        return self.state.parser.parse_user_profile(
            await self.request(routes.USERS_FETCH_PROFILE.compile(user_id=user_id))
        )._stateful(self.state, user_id)

    async def get_me(self) -> User:
        """|coro|

        Retrieve your user information.

        Raises
        ------
        Unauthorized
            Invalid token.
        """
        return self.state.parser.parse_user(await self.request(routes.USERS_FETCH_SELF.compile()))

    async def get_user(self, user: ULIDOr[BaseUser], /) -> User:
        """|coro|

        Retrieve a user's information.

        Parameters
        ----------
        user: :class:`ULIDOr`[:class:`BaseUser`]
            The user.

        Raises
        ------
        Forbidden
            You been blocked by that user.
        HTTPException
            Getting the user failed.

        Returns
        -------
        :class:`User`
            The retrieved user.
        """
        return self.state.parser.parse_user(
            await self.request(routes.USERS_FETCH_USER.compile(user_id=resolve_id(user)))
        )

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
        HTTPException
            Finding mutual friends/servers failed.

        Returns
        -------
        :class:`Mutuals`
            The found mutuals.
        """
        return self.state.parser.parse_mutuals(
            await self.request(routes.USERS_FIND_MUTUAL.compile(user_id=resolve_id(user)))
        )

    async def get_default_avatar(self, user: ULIDOr[BaseUser], /) -> bytes:
        """|coro|

        Returns a default avatar based on the given ID.
        """
        response = await self.raw_request(
            routes.USERS_GET_DEFAULT_AVATAR.compile(user_id=resolve_id(user)[-1]),
            authenticated=False,
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
        HTTPException
            Opening DM failed.
        """
        channel = self.state.parser.parse_channel(
            await self.request(routes.USERS_OPEN_DM.compile(user_id=resolve_id(user)))
        )
        assert isinstance(channel, (SavedMessagesChannel, DMChannel))
        return channel

    async def deny_friend_request(self, user: ULIDOr[BaseUser], /) -> User:
        """|coro|

        Denies another user's friend request.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        HTTPException
            Denying the friend request failed.
        """
        return self.state.parser.parse_user(
            await self.request(routes.USERS_REMOVE_FRIEND.compile(user_id=resolve_id(user)))
        )

    async def remove_friend(self, user: ULIDOr[BaseUser], /) -> User:
        """|coro|

        Removes the user as a friend.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        HTTPException
            Removing the user as a friend failed.
        """
        return self.state.parser.parse_user(
            await self.request(routes.USERS_REMOVE_FRIEND.compile(user_id=resolve_id(user)))
        )

    async def send_friend_request(self, username: str, discriminator: str | None = None, /) -> User:
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
        Forbidden
            Target user have blocked you.
        HTTPException
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
        user: :class:`ULIDOr`[:class:`BaseUser`]
            The user to unblock.
        """
        return self.state.parser.parse_user(
            await self.request(routes.USERS_UNBLOCK_USER.compile(user_id=resolve_id(user)))
        )

    # Webhooks control
    async def delete_webhook(self, webhook: ULIDOr[BaseWebhook], /, *, token: str | None = None) -> None:
        """|coro|

        Deletes a webhook. If webhook token wasn't given, the library will attempt delete webhook with current bot/user token.

        Parameters
        ----------
        webhook: :class:`ULIDOr`[:class:`BaseWebhook`]
            The webhook to delete.
        token: Optional[:class:`str`]
            The webhook token.

        Raises
        ------
        Forbidden
            You do not have permissions to delete the webhook.
        HTTPException
            Deleting the webhook failed.
        """
        if token is None:
            await self.request(routes.WEBHOOKS_WEBHOOK_DELETE.compile(webhook_id=resolve_id(webhook)))
        else:
            await self.request(
                routes.WEBHOOKS_WEBHOOK_DELETE_TOKEN.compile(webhook_id=resolve_id(webhook), webhook_token=token),
                authenticated=False,
            )

    async def edit_webhook(
        self,
        webhook: ULIDOr[BaseWebhook],
        /,
        *,
        token: str | None = None,
        name: UndefinedOr[str] = UNDEFINED,
        avatar: UndefinedOr[ResolvableResource | None] = UNDEFINED,
        permissions: UndefinedOr[Permissions] = UNDEFINED,
    ) -> Webhook:
        """|coro|

        Edits a webhook. If webhook token wasn't given, the library will attempt edit webhook with current bot/user token.

        Parameters
        ----------
        webhook: :class:`ULIDOr`[:class:`BaseWebhook`]
            The webhook to edit.
        token: Optional[:class:`str`]
            The webhook token.
        name: :class:`UndefinedOr`[:class:`str`]
            New webhook name. Should be between 1 and 32 chars long.
        avatar: :class:`UndefinedOr`[Optional[:class:`ResolvableResource`]]
            New webhook avatar.
        permissions: :class:`UndefinedOr`[:class:`Permissions`]
            New webhook permissions.

        Raises
        ------
        Forbidden
            You do not have permissions to edit the webhook.
        HTTPException
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
                authenticated=False,
            )
        return self.state.parser.parse_webhook(resp)

    async def execute_webhook(
        self,
        webhook: ULIDOr[BaseWebhook],
        token: str,
        /,
        content: str | None = None,
        *,
        nonce: str | None = None,
        attachments: list[ResolvableResource] | None = None,
        replies: list[Reply | ULIDOr[BaseMessage]] | None = None,
        embeds: list[SendableEmbed] | None = None,
        masquerade: Masquerade | None = None,
        interactions: Interactions | None = None,
        silent: bool | None = None,
    ) -> Message:
        """|coro|

        Executes a webhook and returns a message.

        Parameters
        ----------
        webhook: :class:`ULIDOr`[:class:`BaseWebhook`]
            The ID of the webhook.
        token: :class:`str`
            The webhook token.
        content: Optional[:class:`str`]
            The message content.
        nonce: Optional[:class:`str`]
            The message nonce.
        attachments: Optional[List[:class:`ResolvableResource`]]
            The message attachments.
        replies: Optional[List[Union[:class:`Reply`, :class:`ULIDOr`[:class:`BaseMessage`]]]]
            The message replies.
        embeds: Optional[List[:class:`SendableEmbed`]]
            The message embeds.
        masquearde: Optional[:class:`Masquerade`]
            The message masquerade.
        interactions: Optional[:class:`Interactions`]
            The message interactions.
        silent: Optional[:class:`bool`]
            Whether to suppress notifications or not.

        Returns
        -------
        :class:`Message`
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
            flags = 0
            if silent:
                flags |= MessageFlags.SUPPRESS_NOTIFICATIONS

        if flags is not None:
            payload['flags'] = flags

        headers = {}
        if nonce is not None:
            headers['Idempotency-Key'] = nonce
        return self.state.parser.parse_message(
            await self.request(
                routes.WEBHOOKS_WEBHOOK_EXECUTE.compile(webhook_id=resolve_id(webhook), webhook_token=token),
                json=payload,
                headers=headers,
                authenticated=False,
            )
        )

    async def get_webhook(
        self,
        webhook: ULIDOr[BaseWebhook],
        /,
        *,
        token: str | None = None,
    ) -> Webhook:
        """|coro|

        Retrieves a webhook. If webhook token wasn't given, the library will attempt get webhook with bot/user token.

        .. note::
            Due to Revolt limitation, the webhook avatar information will be partial if no token is provided. Fields are guaranteed to be non-zero/non-empty: `id` and `user_id`.

        Parameters
        ----------
        webhook: :class:`ULIDOr`[:class:`BaseWebhook`]
            The ID of the webhook.
        token: Optional[:class:`str`]
            The webhook token.

        Raises
        ------
        Forbidden
            You do not have permissions to get the webhook.
        HTTPException
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
                authenticated=False,
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
        HTTPException
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
        HTTPException
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
        HTTPException
            Confirming the account deletion failed.
        """
        payload: raw.a.DataAccountDeletion = {'token': token}
        await self.request(
            routes.AUTH_ACCOUNT_CONFIRM_DELETION.compile(),
            authenticated=False,
            json=payload,
        )

    async def register(
        self,
        email: str,
        password: str,
        /,
        *,
        invite: str | None = None,
        captcha: str | None = None,
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
        HTTPException
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
            authenticated=False,
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
        HTTPException
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
        HTTPException
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
        HTTPException
            Getting the account data failed.
        """
        return self.state.parser.parse_partial_account(await self.request(routes.AUTH_ACCOUNT_FETCH_ACCOUNT.compile()))

    async def confirm_password_reset(
        self, token: str, /, *, new_password: str, remove_sessions: bool | None = None
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
        HTTPException
            Sending the email failed.
        """
        payload: raw.a.DataPasswordReset = {
            'token': token,
            'password': new_password,
            'remove_sessions': remove_sessions,
        }
        await self.request(
            routes.AUTH_ACCOUNT_PASSWORD_RESET.compile(),
            authenticated=False,
            json=payload,
        )

    async def resend_verification(
        self,
        *,
        email: str,
        captcha: str | None = None,
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
        HTTPException
            Resending the verification mail failed.
        """
        payload: raw.a.DataResendVerification = {'email': email, 'captcha': captcha}
        await self.request(
            routes.AUTH_ACCOUNT_RESEND_VERIFICATION.compile(),
            authenticated=False,
            json=payload,
        )

    async def send_password_reset(self, *, email: str, captcha: str | None = None) -> None:
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
        HTTPException
            Sending the email failed.
        """
        payload: raw.a.DataSendPasswordReset = {'email': email, 'captcha': captcha}
        await self.request(
            routes.AUTH_ACCOUNT_SEND_PASSWORD_RESET.compile(),
            authenticated=False,
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
        HTTPException
            Verifying the email address failed.
        """
        response = await self.request(routes.AUTH_ACCOUNT_VERIFY_EMAIL.compile(code=code), authenticated=False)
        if response is not None and isinstance(response, dict) and 'ticket' in response:
            return self.state.parser.parse_mfa_ticket(response['ticket'])
        else:
            return None

    # MFA authentication control
    async def _create_mfa_ticket(self, payload: raw.a.MFAResponse, /) -> MFATicket:
        return self.state.parser.parse_mfa_ticket(
            await self.request(routes.AUTH_MFA_CREATE_TICKET.compile(), json=payload)
        )

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
        return [MFAMethod(mm) for mm in await self.request(routes.AUTH_MFA_GET_MFA_METHODS.compile())]

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
        session: :class:`ULIDOr`[:class:`PartialSession`]
            The session to edit.
        friendly_name: :class:`str`
            The new device name. Because of Authifier limitation, this is not :class:`UndefinedOr`.

        """
        payload: raw.a.DataEditSession = {'friendly_name': friendly_name}
        return self.state.parser.parse_partial_session(
            await self.request(routes.AUTH_SESSION_EDIT.compile(session_id=resolve_id(session)), json=payload)
        )

    async def get_sessions(self) -> list[PartialSession]:
        """|coro|

        Retrieves all sessions associated with this account.

        Returns
        -------
        List[:class:`PartialSession`]
            The sessions.
        """
        sessions: list[raw.a.SessionInfo] = await self.request(routes.AUTH_SESSION_FETCH_ALL.compile())
        return [self.state.parser.parse_partial_session(e) for e in sessions]

    async def login_with_email(self, email: str, password: str, /, *, friendly_name: str | None = None) -> LoginResult:
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
        d: raw.a.ResponseLogin = await self.request(
            routes.AUTH_SESSION_LOGIN.compile(), authenticated=False, json=payload
        )
        return self.state.parser.parse_response_login(d, friendly_name)

    async def login_with_mfa(
        self,
        ticket: str,
        by: MFAResponse | None,
        /,
        *,
        friendly_name: str | None = None,
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
        d: raw.a.ResponseLogin = await self.request(
            routes.AUTH_SESSION_LOGIN.compile(), authenticated=False, json=payload
        )
        p = self.state.parser.parse_response_login(d, friendly_name)
        assert not isinstance(p, MFARequired), 'Recursion detected'
        return p

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

    async def revoke_all_sessions(self, *, revoke_self: bool | None = None) -> None:
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


__all__ = ('DEFAULT_HTTP_USER_AGENT', '_STATUS_TO_ERRORS', 'HTTPClient')
