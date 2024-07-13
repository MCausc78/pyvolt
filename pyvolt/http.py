from __future__ import annotations

import aiohttp
import asyncio
from datetime import datetime, timedelta
import logging
import multidict
import typing as t


from .auth import (
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
    ChannelType,
    BaseChannel,
    TextChannel,
    SavedMessagesChannel,
    DMChannel,
    GroupChannel,
    VoiceChannel,
    ServerChannel,
    Channel,
)
from .emoji import BaseEmoji, ServerEmoji, Emoji, ResolvableEmoji, resolve_emoji
from .errors import (
    APIError,
    Unauthorized,
    Forbidden,
    NotFound,
    Ratelimited,
    InternalServerError,
    BadGateway,
)
from .invite import BaseInvite, ServerInvite, Invite
from .message import (
    Reply,
    Interactions,
    Masquerade,
    SendableEmbed,
    MessageSort,
    BaseMessage,
    MessageFlags,
    Message,
)
from .permissions import Permissions, PermissionOverride
from .read_state import ReadState
from .safety_reports import ContentReportReason, UserReportReason
from .server import (
    ServerFlags,
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
    UserBadges,
    UserFlags,
    Mutuals,
    BaseUser,
    User,
    SelfUser,
)
from .webhook import BaseWebhook, Webhook

_L = logging.getLogger(__name__)


from . import cdn, core, routes, utils

if t.TYPE_CHECKING:
    from . import raw
    from .state import State


DEFAULT_HTTP_USER_AGENT = (
    f"pyvolt API client (https://github.com/MCausc78/pyvolt, {core.__version__})"
)


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

    __slots__ = (
        "token",
        "bot",
        "state",
        "_session",
        "base",
        "cf_clearance",
        "max_retries",
        "user_agent",
    )

    def __init__(
        self,
        token: str | None = None,
        *,
        base: str | None = None,
        bot: bool = True,
        cf_clearance: str | None = None,
        max_retries: int | None = None,
        state: State,
        session: (
            utils.MaybeAwaitableFunc[[HTTPClient], aiohttp.ClientSession]
            | aiohttp.ClientSession
        ),
        user_agent: str | None = None,
    ) -> None:
        self.token = token
        self.bot = bot

        self.state = state
        if base is None:
            base = "https://api.revolt.chat"
        self._session = session
        self.base = base
        self.cf_clearance = cf_clearance
        self.max_retries = max_retries or 3
        self.user_agent = user_agent or DEFAULT_HTTP_USER_AGENT

    async def _request(
        self,
        route: routes.CompiledRoute,
        *,
        authenticated: bool = True,
        manual_accept: bool = False,
        user_agent: str = "",
        mfa_ticket: str | None = None,
        **kwargs,
    ) -> aiohttp.ClientResponse:
        headers: multidict.CIMultiDict[t.Any] = multidict.CIMultiDict(
            kwargs.pop("headers", {})
        )

        # Prevent UnderAttackMode error
        cf_clearance = kwargs.pop("cf_clearance", self.cf_clearance)
        if cf_clearance:
            if "cookie" not in headers:
                headers["cookie"] = f"cf_clearance={cf_clearance}"
            else:

                pass

        if self.token is not None and authenticated:
            headers["x-bot-token" if self.bot else "x-session-token"] = self.token
        if not manual_accept:
            headers["accept"] = "application/json"
        headers["user-agent"] = user_agent or self.user_agent
        if mfa_ticket is not None:
            headers["x-mfa-ticket"] = mfa_ticket
        retries = 0

        method = route.route.method
        url = self.base.rstrip("/") + route.build()

        while True:
            _L.debug("sending request to %s, body=%s", route, kwargs.get("json"))

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
                if response.status == 502:
                    if retries >= self.max_retries:
                        raise BadGateway(response, await utils._json_or_text(response))
                    continue
                if response.status == 429:
                    if retries < self.max_retries:
                        j = await utils._json_or_text(response)
                        if isinstance(j, dict):
                            retry_after: float = j["retry_after"] / 1000.0
                        else:
                            retry_after = float("nan")
                        _L.debug(
                            "ratelimited on %s %s, retrying in %.3f seconds",
                            method,
                            url,
                            retry_after,
                        )
                        await asyncio.sleep(retry_after)
                        continue
                j = await utils._json_or_text(response)
                if isinstance(j.get("error"), dict):
                    error = j["error"]
                    code = error.get("code")
                    reason = error.get("reason")
                    description = error.get("description")
                    j["type"] = "RocketError"
                    j["err"] = f"{code} {reason}: {description}"
                raise _STATUS_TO_ERRORS.get(response.status, APIError)(response, j)
            return response

    async def request(
        self,
        route: routes.CompiledRoute,
        *,
        authenticated: bool = True,
        manual_accept: bool = False,
        user_agent: str = "",
        mfa_ticket: str | None = None,
        **kwargs,
    ) -> t.Any:
        response = await self._request(
            route,
            authenticated=authenticated,
            manual_accept=manual_accept,
            user_agent=user_agent,
            mfa_ticket=mfa_ticket,
            **kwargs,
        )
        result = await utils._json_or_text(response)
        if not response.closed:
            response.close()
        return result

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
        :class:`bots.Bot`
            The created bot.
        """
        j: raw.DataCreateBot = {"name": name}
        d: raw.BotWithUserResponse = await self.request(
            routes.BOTS_CREATE.compile(), json=j
        )
        return self.state.parser.parse_bot(d, d["user"])

    async def delete_bot(self, bot: core.ULIDOr[BaseBot]) -> None:
        """|coro|

        Delete a bot.
        https://developers.revolt.chat/api/#tag/Bots/operation/delete_delete_bot

        .. note::
            This can only be used by non-bot accounts.
        """
        await self.request(routes.BOTS_DELETE.compile(bot_id=core.resolve_id(bot)))

    async def edit_bot(
        self,
        bot: core.ULIDOr[BaseBot],
        *,
        name: core.UndefinedOr[str] = core.UNDEFINED,
        public: core.UndefinedOr[bool] = core.UNDEFINED,
        analytics: core.UndefinedOr[bool] = core.UNDEFINED,
        interactions_url: core.UndefinedOr[str | None] = core.UNDEFINED,
        reset_token: bool = False,
    ) -> Bot:
        """|coro|

        Edits the bot.
        """
        j: raw.DataEditBot = {}
        r: list[raw.FieldsBot] = []
        if core.is_defined(name):
            j["name"] = name
        if core.is_defined(public):
            j["public"] = public
        if core.is_defined(analytics):
            j["analytics"] = analytics
        if core.is_defined(interactions_url):
            if interactions_url is None:
                r.append("InteractionsURL")
            else:
                j["interactions_url"] = interactions_url
        if reset_token:
            r.append("Token")
        if len(r) > 0:
            j["remove"] = r

        d: raw.BotWithUserResponse = await self.request(
            routes.BOTS_EDIT.compile(bot_id=core.resolve_id(bot)), json=j
        )
        return self.state.parser.parse_bot(
            d,
            d["user"],
        )

    async def get_bot(self, bot: core.ULIDOr[BaseBot]) -> Bot:
        """|coro|

        Get details of a bot you own.
        https://developers.revolt.chat/api/#tag/Bots/operation/fetch_fetch_bot

        .. note::
            This can only be used by non-bot accounts.
        """
        d: raw.FetchBotResponse = await self.request(
            routes.BOTS_FETCH.compile(bot_id=core.resolve_id(bot))
        )
        return self.state.parser.parse_bot(d["bot"], d["user"])

    async def get_owned_bots(self) -> list[Bot]:
        """|coro|

        Get  all of the bots that you have control over.
        https://developers.revolt.chat/api/#tag/Bots/operation/fetch_owned_fetch_owned_bots

        .. note::
            This can only be used by non-bot accounts.
        """
        return self.state.parser.parse_bots(
            await self.request(routes.BOTS_FETCH_OWNED.compile())
        )

    async def get_public_bot(self, bot: core.ULIDOr[BaseBot]) -> PublicBot:
        """|coro|

        Get details of a public (or owned) bot.
        https://developers.revolt.chat/api/#tag/Bots/operation/fetch_public_fetch_public_bot

        .. note::
            This can only be used by non-bot accounts.
        """
        return self.state.parser.parse_public_bot(
            await self.request(
                routes.BOTS_FETCH_PUBLIC.compile(bot_id=core.resolve_id(bot))
            )
        )

    async def invite_bot(
        self,
        bot: core.ULIDOr[BaseBot | BaseUser],
        *,
        server: core.ULIDOr[BaseServer] | None = None,
        group: core.ULIDOr[GroupChannel] | None = None,
    ) -> None:
        """|coro|

        Invite a bot to a server or group.
        https://developers.revolt.chat/api/#tag/Bots/operation/invite_invite_bot

        .. note::
            This can only be used by non-bot accounts.

        """
        if server and group:
            raise TypeError("Cannot pass both server and group")
        if not server and not group:
            raise TypeError("Pass server or group")

        j: raw.InviteBotDestination
        if server:
            j = {"server": core.resolve_id(server)}
        elif group:
            j = {"group": core.resolve_id(group)}
        else:
            raise RuntimeError("Unreachable")

        await self.request(
            routes.BOTS_INVITE.compile(bot_id=core.resolve_id(bot)), json=j
        )

    # Channels control
    async def acknowledge_message(
        self, channel: core.ULIDOr[TextChannel], message: core.ULIDOr[BaseMessage]
    ) -> None:
        """|coro|

        Lets the server and all other clients know that we've seen this message in this channel.
        https://developers.revolt.chat/api/#tag/Messaging/operation/channel_ack_req

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        channel: :class:`core.ResolvableULID`
            Channel message was sent to.
        message: :class:`core.ResolvableULID`
            Message to ack.

        Raises
        ------
        Forbidden
            You do not have permissions to see that message.
        APIError
            Acknowledging message failed.
        """
        await self.request(
            routes.CHANNELS_CHANNEL_ACK.compile(
                channel_id=core.resolve_id(channel),
                message_id=core.resolve_id(message),
            )
        )

    async def close_channel(
        self, channel: core.ULIDOr[BaseChannel], silent: bool | None = None
    ) -> None:
        """|coro|

        Deletes a server channel, leaves a group or closes a group.
        https://developers.revolt.chat/api/#tag/Channel-Information/operation/channel_delete_req

        Parameters
        ----------
        channel: :class:`core.ResolvableULID`
            Channel to close.
        silent: :class:`bool`
            Whether to not send message when leaving.

        Raises
        ------
        Forbidden
            You do not have permissions to close the channel.
        APIError
            Closing the channel failed.
        """
        p: raw.OptionsChannelDelete = {}
        if silent is not None:
            p["leave_silently"] = utils._bool(silent)
        await self.request(
            routes.CHANNELS_CHANNEL_DELETE.compile(channel_id=core.resolve_id(channel)),
            params=p,
        )

    async def edit_channel(
        self,
        channel: core.ULIDOr[BaseChannel],
        *,
        name: core.UndefinedOr[str] = core.UNDEFINED,
        description: core.UndefinedOr[str | None] = core.UNDEFINED,
        owner: core.UndefinedOr[core.ULIDOr[BaseUser]] = core.UNDEFINED,
        icon: core.UndefinedOr[str | None] = core.UNDEFINED,
        nsfw: core.UndefinedOr[bool] = core.UNDEFINED,
        archived: core.UndefinedOr[bool] = core.UNDEFINED,
        default_permissions: core.UndefinedOr[None] = core.UNDEFINED,
    ) -> Channel:
        """|coro|

        Edits the channel.
        https://developers.revolt.chat/api/#tag/Channel-Information/operation/channel_edit_req

        Parameters
        ----------
        channel: :class:`core.ResolvableULID`
            Channel to edit.

        Raises
        ------
        Forbidden
            You do not have permissions to edit the channel.
        APIError
            Editing the channel failed.
        """
        j: raw.DataEditChannel = {}
        r: list[raw.FieldsChannel] = []
        if core.is_defined(name):
            j["name"] = name
        if core.is_defined(description):
            if description is None:
                r.append("Description")
            else:
                j["description"] = description
        if core.is_defined(owner):
            j["owner"] = core.resolve_id(owner)
        if core.is_defined(icon):
            if icon is None:
                r.append("Icon")
            else:
                j["icon"] = icon
        if core.is_defined(nsfw):
            j["nsfw"] = nsfw
        if core.is_defined(archived):
            j["archived"] = archived
        if core.is_defined(default_permissions):
            r.append("DefaultPermissions")
        if len(r) > 0:
            j["remove"] = r
        return self.state.parser.parse_channel(
            await self.request(
                routes.CHANNELS_CHANNEL_EDIT.compile(
                    channel_id=core.resolve_id(channel)
                ),
                json=j,
            )
        )

    async def get_channel(self, channel: core.ULIDOr[BaseChannel]) -> Channel:
        """|coro|

        Gets the channel.
        https://developers.revolt.chat/api/#tag/Channel-Information/operation/channel_fetch_req

        Raises
        ------
        NotFound
            Invalid Channel ID.
        APIError
            Getting the channel failed.
        """
        return self.state.parser.parse_channel(
            await self.request(
                routes.CHANNELS_CHANNEL_FETCH.compile(
                    channel_id=core.resolve_id(channel)
                )
            )
        )

    async def get_channel_pins(
        self, channel: core.ULIDOr[TextChannel]
    ) -> list[Message]:
        """|coro|

        Retrieves all messages that are currently pinned in the channel.

        Raises
        ------
        APIError
            Getting channel pins failed.

        Returns
        -------
        :class:`list`[:class:`Message`]
            The pinned
        """
        return [
            self.state.parser.parse_message(m)
            for m in await self.request(
                routes.CHANNELS_CHANNEL_PINS.compile(
                    channel_id=core.resolve_id(channel)
                )
            )
        ]

    async def add_recipient_to_group(
        self,
        channel: core.ULIDOr[GroupChannel],
        user: core.ULIDOr[BaseUser],
    ) -> None:
        """|coro|

        Adds another user to the group.
        https://developers.revolt.chat/api/#tag/Groups/operation/group_add_member_req

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        channel: :class:`core.ULIDOr`[:class:`GroupChannel`]
            The group.
        user: :class:`core.ULIDOr`[:class:`BaseUser`]
            The user to add.

        Raises
        ------
        Forbidden
            You're bot, lacking `InviteOthers` permission, or not friends with this user.
        APIError
            Adding user to the group failed.
        """
        await self.request(
            routes.CHANNELS_GROUP_ADD_MEMBER.compile(
                channel_id=core.resolve_id(channel), user_id=core.resolve_id(user)
            )
        )

    async def create_group(
        self,
        name: str,
        *,
        description: str | None = None,
        users: list[core.ULIDOr[BaseUser]] | None = None,
        nsfw: bool | None = None,
    ) -> GroupChannel:
        """|coro|

        Creates the new group channel.
        https://developers.revolt.chat/api/#tag/Groups/operation/group_create_req

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        name: :class:`str`
            Group name.
        description: :class:`str` | None
            Group description.
        users: :class:`list`[`:class:`core.ULIDOr`[:class:`BaseUser`]] | None
            List of users to add to the group. Must be friends with these users.
        nsfw: :class:`bool` | None
            Whether this group should be age-restricted.

        Raises
        ------
        APIError
            Creating the group failed.
        """
        j: raw.DataCreateGroup = {"name": name}
        if description is not None:
            j["description"] = description
        if users is not None:
            j["users"] = [core.resolve_id(user) for user in users]
        if nsfw is not None:
            j["nsfw"] = nsfw
        return self.state.parser.parse_group_channel(
            await self.request(routes.CHANNELS_GROUP_CREATE.compile(), json=j),
            recipients=(True, []),
        )

    async def remove_member_from_group(
        self,
        channel: core.ULIDOr[GroupChannel],
        member: core.ULIDOr[BaseUser],
    ) -> None:
        """|coro|

        Removes a user from the group.
        https://developers.revolt.chat/api/#tag/Groups/operation/group_remove_member_req

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        channel: :class:`core.ResolvableULID`
            The group.
        member: :class:`core.ResolvableULID`
            User to remove.

        Raises
        ------
        Forbidden
            You're not owner of group.
        APIError
            Removing the member from group failed.
        """
        await self.request(
            routes.CHANNELS_GROUP_REMOVE_MEMBER.compile(
                channel_id=core.resolve_id(channel),
                member_id=core.resolve_id(member),
            )
        )

    async def create_invite(
        self, channel: core.ULIDOr[GroupChannel | ServerChannel]
    ) -> Invite:
        """|coro|

        Creates an invite to channel.
        Channel must be a group or server text channel.
        https://developers.revolt.chat/api/#tag/Channel-Invites/operation/invite_create_req

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        channel: :class:`core.ULIDOr`[:class:`GroupChannel` | :class:`ServerChannel`]
            The invite destination channel.

        Raises
        ------
        Forbidden
            You do not have permissions to create invite in that channel.
        APIError
            Creating invite failed.
        """
        return self.state.parser.parse_invite(
            await self.request(
                routes.CHANNELS_INVITE_CREATE.compile(
                    channel_id=core.resolve_id(channel)
                )
            )
        )

    async def get_group_recipients(
        self,
        channel: core.ULIDOr[GroupChannel],
    ) -> list[User]:
        """|coro|

        Retrieves all users who are part of this group.
        https://developers.revolt.chat/api/#tag/Groups/operation/members_fetch_req

        Parameters
        ----------
        channel: :class:`core.ULIDOr`[:class:`GroupChannel`]
            The group channel.

        Raises
        ------
        APIError
            Getting group recipients failed.
        """
        return [
            self.state.parser.parse_user(user)
            for user in await self.request(
                routes.CHANNELS_MEMBERS_FETCH.compile(
                    channel_id=core.resolve_id(channel),
                )
            )
        ]

    async def bulk_delete_messages(
        self,
        channel: core.ULIDOr[TextChannel],
        messages: t.Sequence[core.ULIDOr[BaseMessage]],
    ) -> None:
        """|coro|

        Delete multiple messages you've sent or one you have permission to delete.
        This will always require `ManageMessages` permission regardless of whether you own the message or not.
        Messages must have been sent within the past 1 week.
        https://developers.revolt.chat/api/#tag/Messaging/operation/message_bulk_delete_req

        Parameters
        ----------
        channel: :class:`core.ULIDOr`[:class:`TextChannel`]
            The channel.
        messages: :class:`t.Sequence`[:class:`core.ULIDOr`[:class:`BaseMessage`]]
            The messages to delete.

        Forbidden
            You do not have permissions to delete
        APIError
            Deleting messages failed.
        """
        j: raw.OptionsBulkDelete = {
            "ids": [core.resolve_id(message) for message in messages]
        }
        await self.request(
            routes.CHANNELS_MESSAGE_BULK_DELETE.compile(
                channel_id=core.resolve_id(channel)
            ),
            json=j,
        )

    async def remove_all_reactions_from_message(
        self,
        channel: core.ULIDOr[TextChannel],
        message: core.ULIDOr[BaseMessage],
    ) -> None:
        """|coro|

        Remove your own, someone else's or all of a given reaction.
        Requires `ManageMessages` permission.
        https://developers.revolt.chat/api/#tag/Interactions/operation/message_clear_reactions_clear_reactions

        Parameters
        ----------
        channel: :class:`core.ResolvableULID`
            The channel.
        message: :class:`core.ResolvableULID`
            The message.

        Raises
        ------
        Forbidden
            You do not have permissions to remove all reactions from message.
        APIError
            Removing reactions from message failed.
        """
        await self.request(
            routes.CHANNELS_MESSAGE_CLEAR_REACTIONS.compile(
                channel_id=core.resolve_id(channel),
                message_id=core.resolve_id(message),
            )
        )

    async def delete_message(
        self, channel: core.ULIDOr[TextChannel], message: core.ULIDOr[BaseMessage]
    ) -> None:
        """|coro|

        Delete a message you've sent or one you have permission to delete.
        https://developers.revolt.chat/api/#tag/Messaging/operation/message_delete_req

        Parameters
        ----------
        channel: :class:`core.ResolvableULID`
            The channel.
        message: :class:`core.ResolvableULID`
            The message.

        Raises
        ------
        Forbidden
            You do not have permissions to delete message.
        APIError
            Deleting the message failed.
        """
        await self.request(
            routes.CHANNELS_MESSAGE_DELETE.compile(
                channel_id=core.resolve_id(channel),
                message_id=core.resolve_id(message),
            )
        )

    async def edit_message(
        self,
        channel: core.ULIDOr[TextChannel],
        message: core.ULIDOr[BaseMessage],
        *,
        content: core.UndefinedOr[str] = core.UNDEFINED,
        embeds: core.UndefinedOr[list[SendableEmbed]] = core.UNDEFINED,
    ) -> Message:
        """|coro|

        Edits the message that you've previously sent.
        https://developers.revolt.chat/api/#tag/Messaging/operation/message_edit_req

        Parameters
        ----------
        channel: :class:`core.ResolvableULID`
            The channel.
        message: :class:`core.ResolvableULID`
            The message.
        content: :class:`str` | None
            New content.
        embeds: :class:`list`[:class:`SendableEmbed`] | None
            New embeds.
        """
        j: raw.DataEditMessage = {}
        if core.is_defined(content):
            j["content"] = content
        if core.is_defined(embeds):
            j["embeds"] = [await embed.build(self.state) for embed in embeds]
        return self.state.parser.parse_message(
            await self.request(
                routes.CHANNELS_MESSAGE_EDIT.compile(
                    channel_id=core.resolve_id(channel),
                    message_id=core.resolve_id(message),
                ),
                json=j,
            )
        )

    async def get_message(
        self, channel: core.ULIDOr[TextChannel], message: core.ULIDOr[BaseMessage]
    ) -> Message:
        """|coro|

        Retrieves a message.
        https://developers.revolt.chat/api/#tag/Messaging/operation/message_fetch_req

        Parameters
        ----------
        channel: :class:`core.ResolvableULID`
            The channel.
        message: :class:`core.ResolvableULID`
            The message.

        Raises
        ------
        Forbidden
            You do not have permissions to get message.
        APIError
            Getting the message failed.

        Returns
        -------
        :class:`Message`
            The retrieved message.
        """
        return self.state.parser.parse_message(
            await self.request(
                routes.CHANNELS_MESSAGE_FETCH.compile(
                    channel_id=core.resolve_id(channel),
                    message_id=core.resolve_id(message),
                )
            )
        )

    async def get_messages(
        self,
        channel: core.ULIDOr[TextChannel],
        *,
        limit: int | None = None,
        before: core.ULIDOr[BaseMessage] | None = None,
        after: core.ULIDOr[BaseMessage] | None = None,
        sort: MessageSort | None = None,
        nearby: core.ULIDOr[BaseMessage] | None = None,
        populate_users: bool | None = None,
    ) -> list[Message]:
        """|coro|

        Get multiple
        https://developers.revolt.chat/api/#tag/Messaging/operation/message_query_req

        Parameters
        ----------
        channel: :class:`core.ResolvableULID`
            The channel.
        limit: :class:`int` | None
            Maximum number of messages to get. For getting nearby messages, this is `(limit + 1)`.
        before: :class:`core.ResolvableULID` | None
            Message id before which messages should be fetched.
        after: :class:`core.ResolvableULID` | None
            Message after which messages should be fetched.
        sort: :class:`MessageSort` | None
            Message sort direction.
        nearby: :class:`core.ResolvableULID`
            Message id to search around. Specifying 'nearby' ignores 'before', 'after' and 'sort'. It will also take half of limit rounded as the limits to each side. It also fetches the message ID specified.
        populate_users: :class:`bool`
            Whether to populate user (and member, if server channel) objects.

        Returns
        -------
        :class:`list`[:class:`Message`]
            The messages retrieved.

        Raises
        ------
        Forbidden
            You do not have permissions to get
        APIError
            Getting messages failed.
        """
        p: raw.OptionsQueryMessages = {}
        if limit is not None:
            p["limit"] = limit
        if before is not None:
            p["before"] = core.resolve_id(before)
        if after is not None:
            p["after"] = core.resolve_id(after)
        if sort is not None:
            p["sort"] = sort.value
        if nearby is not None:
            p["nearby"] = core.resolve_id(nearby)
        if populate_users is not None:
            p["include_users"] = utils._bool(populate_users)
        return self.state.parser.parse_messages(
            await self.request(
                routes.CHANNELS_MESSAGE_QUERY.compile(
                    channel_id=core.resolve_id(channel)
                ),
                params=p,
            )
        )

    async def add_reaction_to_message(
        self,
        channel: core.ULIDOr[TextChannel],
        message: core.ULIDOr[BaseMessage],
        emoji: ResolvableEmoji,
    ) -> None:
        """|coro|

        React to a given message.
        https://developers.revolt.chat/api/#tag/Interactions/operation/message_react_react_message

        Parameters
        ----------
        channel: :class:`core.ResolvableULID`
            The channel.
        message: :class:`core.ResolvableULID`
            The message.
        emoji: :class:`emojis.ResolvableEmoji`
            The emoji to react with.

        Raises
        ------
        Forbidden
            You do not have permissions to react to message.
        APIError
            Reacting to message failed.
        """
        await self.request(
            routes.CHANNELS_MESSAGE_REACT.compile(
                channel_id=core.resolve_id(channel),
                message_id=core.resolve_id(message),
                emoji=resolve_emoji(emoji),
            )
        )

    async def search_for_messages(
        self,
        channel: core.ULIDOr[TextChannel],
        query: str,
        *,
        limit: int | None = None,
        before: core.ULIDOr[BaseMessage] | None = None,
        after: core.ULIDOr[BaseMessage] | None = None,
        sort: MessageSort | None = None,
        populate_users: bool | None = None,
    ) -> list[Message]:
        """|coro|

        Searches for messages within the given parameters.
        https://developers.revolt.chat/api/#tag/Messaging/operation/message_search_req

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        channel: :class:`core.ResolvableULID`
            The channel to search in.
        query: :class:`str`
            Full-text search query. See [MongoDB documentation](https://docs.mongodb.com/manual/text-search/#-text-operator) for more information.
        limit: :class:`int`
            Maximum number of messages to fetch.
        before: :class:`core.ResolvableULID`
            Message ID before which messages should be fetched.
        after: :class:`core.ResolvableULID`
            Message ID after which messages should be fetched.
        sort: :class:`MessageSort`
            Sort used for retrieving
        populate_users: :class:`bool`
            Whether to populate user (and member, if server channel) objects.

        Returns
        -------
        :class:`list`[:class:`Message`]
            The messages matched.

        Raises
        ------
        Forbidden
            You do not have permissions to search
        APIError
            Searching messages failed.
        """
        j: raw.DataMessageSearch = {"query": query}
        if limit is not None:
            j["limit"] = limit
        if before is not None:
            j["before"] = core.resolve_id(before)
        if after is not None:
            j["after"] = core.resolve_id(after)
        if sort is not None:
            j["sort"] = sort.value
        if populate_users is not None:
            j["include_users"] = utils._bool(populate_users)

        return self.state.parser.parse_messages(
            await self.request(
                routes.CHANNELS_MESSAGE_SEARCH.compile(
                    channel_id=core.resolve_id(channel)
                ),
                json=j,
            )
        )

    async def pin_message(
        self, channel: core.ULIDOr[TextChannel], message: core.ULIDOr[BaseMessage], /
    ) -> None:
        """|coro|

        Pins a message.
        You must have `ManageMessages` permission.

        Parameters
        ----------
        channel: :class:`core.ResolvableULID`
            The channel.
        message: :class:`core.ResolvableULID`
            The message.

        Raises
        ------
        Forbidden
            You do not have permissions to pin
        APIError
            Pinning the message failed.
        """
        await self.request(
            routes.CHANNELS_MESSAGE_PIN.compile(
                channel_id=core.resolve_id(channel),
                message_id=core.resolve_id(message),
            )
        )

    async def send_message(
        self,
        channel: core.ULIDOr[TextChannel],
        content: str | None = None,
        *,
        nonce: str | None = None,
        attachments: list[cdn.ResolvableResource] | None = None,
        replies: list[Reply | core.ULIDOr[BaseMessage]] | None = None,
        embeds: list[SendableEmbed] | None = None,
        masquerade: Masquerade | None = None,
        interactions: Interactions | None = None,
        silent: bool | None = None,
    ) -> Message:
        """|coro|

        Sends a message to the given channel.
        You must have `SendMessages` permission.
        https://developers.revolt.chat/api/#tag/Messaging/operation/message_send_message_send

        Parameters
        ----------
        channel: :class:`~ResolvableULID`
            The channel.
        content: :class:`str` | None
            The message content.
        nonce: :class:`str` | None
            The message nonce.
        attachments: :class:`list`[:class:`~ResolvableResource`] | None
            The message attachments.
        replies: :class:`list`[:class:`~Reply` | :class:`~ResolvableULID`] | None
            The message replies.
        embeds: :class:`list`[:class:`~SendableEmbed`] | None
            The message embeds.
        masquearde: :class:`~Masquerade` | None
            The message masquerade.
        interactions: :class:`~Interactions` | None
            The message interactions.
        silent: :class:`bool` | None
            Whether to suppress notifications when fanning out event.

        Returns
        -------
        :class:`~Message`
            The message that was sent.

        Raises
        ------
        Forbidden
            You do not have permissions to send
        APIError
            Sending the message failed.
        """
        j: raw.DataMessageSend = {}
        if content is not None:
            j["content"] = content
        if attachments is not None:
            j["attachments"] = [
                await cdn.resolve_resource(self.state, attachment, tag="attachments")
                for attachment in attachments
            ]
        if replies is not None:
            j["replies"] = [
                (
                    reply.build()
                    if isinstance(reply, Reply)
                    else {"id": core.resolve_id(reply), "mention": False}
                )
                for reply in replies
            ]
        if embeds is not None:
            j["embeds"] = [await embed.build(self.state) for embed in embeds]
        if masquerade is not None:
            j["masquerade"] = masquerade.build()
        if interactions is not None:
            j["interactions"] = interactions.build()

        flags = None
        if silent is not None:
            flags = 0
            if silent:
                flags |= MessageFlags.SUPPRESS_NOTIFICATIONS.value

        if flags is not None:
            j["flags"] = flags

        headers = {}
        if nonce is not None:
            headers["Idempotency-Key"] = nonce
        return self.state.parser.parse_message(
            await self.request(
                routes.CHANNELS_MESSAGE_SEND.compile(
                    channel_id=core.resolve_id(channel)
                ),
                json=j,
                headers=headers,
            )
        )

    async def unpin_message(
        self, channel: core.ULIDOr[TextChannel], message: core.ULIDOr[BaseMessage], /
    ) -> None:
        """|coro|

        Unpins a message.
        You must have `ManageMessages` permission.

        Parameters
        ----------
        channel: :class:`core.ResolvableULID`
            The channel.
        message: :class:`core.ResolvableULID`
            The message.

        Raises
        ------
        Forbidden
            You do not have permissions to unpin
        APIError
            Unpinning the message failed.
        """
        await self.request(
            routes.CHANNELS_MESSAGE_PIN.compile(
                channel_id=core.resolve_id(channel),
                message_id=core.resolve_id(message),
            )
        )

    async def remove_reactions_from_message(
        self,
        channel: core.ULIDOr[TextChannel],
        message: core.ULIDOr[BaseUser],
        emoji: ResolvableEmoji,
        /,
        *,
        user: core.ULIDOr[BaseUser] | None = None,
        remove_all: bool | None = None,
    ) -> None:
        """|coro|

        Remove your own, someone else's or all of a given reaction.
        Requires `ManageMessages` permission if changing other's reactions.
        https://developers.revolt.chat/api/#tag/Interactions/operation/message_unreact_unreact_message


        Parameters
        ----------
        channel: :class:`core.ResolvableULID`
            The channel.
        message: :class:`core.ResolvableULID`
            The message.
        emoji: :class:`ResolvableEmoji`
            Emoji to remove.
        user: :class:`core.ResolvableULID` | None
            Remove reactions from this user. Requires `ManageMessages` permission if provided.
        remove_all: :class:`bool` | None
            Whether to remove all reactions. Requires `ManageMessages` permission if provided.

        Raises
        ------
        Forbidden
            You do not have permissions to remove reactions from message.
        APIError
            Removing reactions from message failed.
        """
        p: raw.OptionsUnreact = {}
        if user is not None:
            p["user_id"] = core.resolve_id(user)
        if remove_all is not None:
            p["remove_all"] = utils._bool(remove_all)
        await self.request(
            routes.CHANNELS_MESSAGE_UNREACT.compile(
                channel_id=core.resolve_id(channel),
                message_id=core.resolve_id(message),
                emoji=resolve_emoji(emoji),
            ),
            params=p,
        )

    async def set_role_channel_permissions(
        self,
        channel: core.ULIDOr[ServerChannel],
        role: core.ULIDOr[BaseRole],
        /,
        *,
        allow: Permissions = Permissions.NONE,
        deny: Permissions = Permissions.NONE,
    ) -> Channel:
        """|coro|

        Sets permissions for the specified role in this channel.
        Channel must be a `TextChannel` or `VoiceChannel`.
        https://developers.revolt.chat/api/#tag/Channel-Permissions/operation/permissions_set_req

        Parameters
        ----------
        channel: :class:`core.ResolvableULID`
            The channel.
        role: :class:`core.ResolvableULID`
            The role.

        Raises
        ------
        Forbidden
            You do not have permissions to set role permissions on the channel.
        APIError
            Setting permissions failed.
        """
        j: raw.DataSetRolePermissions = {
            "permissions": {"allow": int(allow), "deny": int(deny)}
        }
        return self.state.parser.parse_channel(
            await self.request(
                routes.CHANNELS_PERMISSIONS_SET.compile(
                    channel_id=core.resolve_id(channel),
                    role_id=core.resolve_id(role),
                ),
                json=j,
            )
        )

    async def set_default_channel_permissions(
        self,
        channel: core.ULIDOr[GroupChannel | ServerChannel],
        permissions: Permissions | PermissionOverride,
        /,
    ) -> Channel:
        """|coro|

        Sets permissions for the default role in this channel.
        Channel must be a `Group`, `TextChannel` or `VoiceChannel`.
        https://developers.revolt.chat/api/#tag/Channel-Permissions/operation/permissions_set_default_req

        Raises
        ------
        Forbidden
            You do not have permissions to set default permissions on the channel.
        APIError
            Setting permissions failed.
        """
        j: raw.DataDefaultChannelPermissions = {
            "permissions": (
                permissions.build()
                if isinstance(permissions, PermissionOverride)
                else int(permissions)
            )
        }
        return self.state.parser.parse_channel(
            await self.request(
                routes.CHANNELS_PERMISSIONS_SET_DEFAULT.compile(
                    channel_id=core.resolve_id(channel)
                ),
                json=j,
            )
        )

    async def join_call(
        self, channel: core.ULIDOr[DMChannel | GroupChannel | VoiceChannel]
    ) -> str:
        """|coro|

        Asks the voice server for a token to join the call.
        https://developers.revolt.chat/api/#tag/Voice/operation/voice_join_req

        Parameters
        ----------
        channel: :class:`core.ResolvableULID`
            The channel.

        Returns
        -------
        :class:`str`
            Token for authenticating with the voice server.

        Raises
        ------
        APIError
            Asking for the token failed.
        """
        return (
            await self.request(
                routes.CHANNELS_VOICE_JOIN.compile(channel_id=core.resolve_id(channel))
            )
        )["token"]

    async def create_webhook(
        self,
        channel: core.ULIDOr[ServerChannel],
        /,
        *,
        name: str,
        avatar: cdn.ResolvableResource | None = None,
    ) -> Webhook:
        """|coro|

        Creates a webhook which 3rd party platforms can use to send
        https://developers.revolt.chat/api/#tag/Webhooks/operation/webhook_create_req

        Parameters
        ----------
        name: :class:`str`
            The webhook name. Must be between 1 and 32 chars long.
        avatar: :class:`cdn.ResolvableResource` | None`
            The webhook avatar.

        Raises
        ------
        Forbidden
            You do not have permissions to create the webhook.
        APIError
            Creating the webhook failed.
        """
        j: raw.CreateWebhookBody = {"name": name}
        if avatar is not None:
            j["avatar"] = await cdn.resolve_resource(self.state, avatar, tag="avatars")
        return self.state.parser.parse_webhook(
            await self.request(
                routes.CHANNELS_WEBHOOK_CREATE.compile(
                    channel_id=core.resolve_id(channel)
                ),
                json=j,
            )
        )

    async def get_channel_webhooks(
        self, channel: core.ULIDOr[ServerChannel], /
    ) -> list[Webhook]:
        """|coro|

        Gets all webhooks inside the channel.
        https://developers.revolt.chat/api/#tag/Webhooks/operation/webhook_fetch_all_req

        Raises
        ------
        Forbidden
            You do not have permissions to get channel webhooks.
        APIError
            Getting channel webhooks failed.
        """
        return [
            self.state.parser.parse_webhook(e)
            for e in await self.request(
                routes.CHANNELS_WEBHOOK_FETCH_ALL.compile(
                    channel_id=core.resolve_id(channel)
                )
            )
        ]

    # Customization control (emojis)
    async def create_emoji(
        self,
        server_id: core.ULIDOr[BaseServer],
        data: cdn.ResolvableResource,
        /,
        *,
        name: str,
        nsfw: bool | None = None,
    ) -> ServerEmoji:
        """|coro|

        Create an emoji on the server.
        https://developers.revolt.chat/api/#tag/Emojis/operation/emoji_create_create_emoji

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        Forbidden
            You do not have permissions to create emoji.
        APIError
            Creating the emoji failed.
        """
        j: raw.DataCreateEmoji = {
            "name": name,
            "parent": {"type": "Server", "id": core.resolve_id(server_id)},
        }
        if nsfw is not None:
            j["nsfw"] = nsfw
        return self.state.parser.parse_server_emoji(
            await self.request(
                routes.CUSTOMISATION_EMOJI_CREATE.compile(
                    attachment_id=await cdn.resolve_resource(
                        self.state, data, tag="emojis"
                    )
                ),
                json=j,
            )
        )

    async def delete_emoji(self, emoji: core.ULIDOr[ServerEmoji], /) -> None:
        """|coro|

        Delete an emoji.
        https://developers.revolt.chat/api/#tag/Emojis/operation/emoji_delete_delete_emoji

        Raises
        ------
        Forbidden
            You do not have permissions to delete emojis.
        APIError
            Deleting the emoji failed.
        """
        await self.request(
            routes.CUSTOMISATION_EMOJI_DELETE.compile(emoji_id=core.resolve_id(emoji))
        )

    async def get_emoji(self, emoji: core.ULIDOr[BaseEmoji], /) -> Emoji:
        """|coro|

        Get an emoji.
        https://developers.revolt.chat/api/#tag/Emojis/operation/emoji_fetch_fetch_emoji

        Raises
        ------
        APIError
            Getting the emoji failed.
        """

        return self.state.parser.parse_emoji(
            await self.request(
                routes.CUSTOMISATION_EMOJI_FETCH.compile(
                    emoji_id=core.resolve_id(emoji)
                )
            )
        )

    # Invites control
    async def delete_invite(self, invite_code: str, /) -> None:
        """|coro|

        Delete an invite.
        https://developers.revolt.chat/api/#tag/Invites/operation/invite_delete_req

        Raises
        ------
        Forbidden
            You do not have permissions to delete invite or not creator of that invite.
        APIError
            Deleting the invite failed.
        """
        await self.request(
            routes.INVITES_INVITE_DELETE.compile(invite_code=invite_code)
        )

    async def get_invite(self, invite_code: str, /) -> BaseInvite:
        """|coro|

        Get an invite.
        https://developers.revolt.chat/api/#tag/Invites/operation/invite_fetch_req


        Raises
        ------
        NotFound
            Invalid invite code.
        APIError
            Getting the invite failed.
        """
        return self.state.parser.parse_public_invite(
            await self.request(
                routes.INVITES_INVITE_FETCH.compile(invite_code=invite_code),
                authenticated=False,
            )
        )

    async def accept_invite(self, invite_code: str, /) -> Server | GroupChannel:
        """|coro|

        Accept an invite.
        https://developers.revolt.chat/api/#tag/Invites/operation/invite_join_req

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        Forbidden
            You're banned.
        APIError
            Accepting the invite failed.
        """
        d: raw.InviteJoinResponse = await self.request(
            routes.INVITES_INVITE_JOIN.compile(invite_code=invite_code)
        )
        if d["type"] == "Server":
            return self.state.parser.parse_server(
                d["server"],
                (False, d["channels"]),
            )
        elif d["type"] == "Group":
            return self.state.parser.parse_group_channel(
                d["channel"],
                (False, [self.state.parser.parse_user(u) for u in d["users"]]),
            )
        else:
            _L.error("Invalid payload: %s", d)
            raise NotImplemented

    # Onboarding control
    async def complete_onboarding(self, username: str, /) -> User:
        """|coro|

        Set a new username, complete onboarding and allow a user to start using Revolt.
        """
        j: raw.DataOnboard = {"username": username}
        return self.state.parser.parse_user(
            await self.request(routes.ONBOARD_COMPLETE.compile(), json=j)
        )

    async def onboarding_status(self) -> bool:
        """|coro|

        Whether the current account requires onboarding or whether you can continue to send requests as usual.
        You may skip calling this if you're restoring an existing session.
        """
        d: raw.DataHello = await self.request(routes.ONBOARD_HELLO.compile())
        return d["onboarding"]

    # Web Push control
    async def push_subscribe(self, *, endpoint: str, p256dh: str, auth: str) -> None:
        """|coro|

        Create a new Web Push subscription. If an subscription already exists on this session, it will be removed.
        """
        j: raw.a.WebPushSubscription = {
            "endpoint": endpoint,
            "p256dh": p256dh,
            "auth": auth,
        }
        await self.request(
            routes.PUSH_SUBSCRIBE.compile(),
            json=j,
        )

    async def unsubscribe(self) -> None:
        """|coro|

        Remove the Web Push subscription associated with the current session.
        """
        await self.request(routes.PUSH_UNSUBSCRIBE.compile())

    # Safety control
    async def _report_content(self, j: raw.DataReportContent, /) -> None:
        await self.request(routes.SAFETY_REPORT_CONTENT.compile(), json=j)

    async def report_message(
        self,
        message: core.ULIDOr[BaseMessage],
        reason: ContentReportReason,
        *,
        additional_context: str | None = None,
    ) -> None:
        """|coro|

        Report a piece of content to the moderation team.
        https://developers.revolt.chat/developers/api/reference.html#tag/user-safety/post/safety/report

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        APIError
            Trying to self-report, or reporting the message failed.
        """
        j: raw.DataReportContent = {
            "content": {
                "type": "Message",
                "id": core.resolve_id(message),
                "report_reason": reason.value,
            }
        }
        if additional_context is not None:
            j["additional_context"] = additional_context
        await self._report_content(j)

    async def report_server(
        self,
        server: core.ULIDOr[BaseServer],
        reason: ContentReportReason,
        /,
        *,
        additional_context: str | None = None,
    ) -> None:
        """|coro|

        Report a piece of content to the moderation team.
        https://developers.revolt.chat/developers/api/reference.html#tag/user-safety/post/safety/report

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        APIError
            You're trying to self-report, or reporting the server failed.
        """
        j: raw.DataReportContent = {
            "content": {
                "type": "Server",
                "id": core.resolve_id(server),
                "report_reason": reason.value,
            }
        }
        if additional_context is not None:
            j["additional_context"] = additional_context
        await self._report_content(j)

    async def report_user(
        self,
        user: core.ULIDOr[BaseUser],
        reason: UserReportReason,
        /,
        *,
        additional_context: str | None = None,
        message_context: core.ULIDOr[BaseMessage],
    ) -> None:
        """|coro|

        Report a piece of content to the moderation team.
        https://developers.revolt.chat/developers/api/reference.html#tag/user-safety/post/safety/report

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        APIError
            You're trying to self-report, or reporting the user failed.
        """
        content: raw.UserReportedContent = {
            "type": "User",
            "id": core.resolve_id(user),
            "report_reason": reason.value,
        }

        if message_context is not None:
            content["message_id"] = core.resolve_id(message_context)

        j: raw.DataReportContent = {"content": content}
        if additional_context is not None:
            j["additional_context"] = additional_context

        await self._report_content(j)

    # Servers control
    async def ban_user(
        self,
        server: core.ULIDOr[BaseServer],
        user: str | BaseUser | BaseMember,
        /,
        *,
        reason: str | None = None,
    ) -> Ban:
        """|coro|

        Ban a user by their ID.
        https://developers.revolt.chat/api/#tag/Server-Members/operation/ban_create_req

        Parameters
        ----------
        reason: :class:`str` | None
            Ban reason. Should be between 1 and 1024 chars long.

        Raises
        ------
        Forbidden
            You do not have permissions to ban the user.
        APIError
            Banning the user failed.
        """
        j: raw.DataBanCreate = {"reason": reason}
        return self.state.parser.parse_ban(
            await self.request(
                routes.SERVERS_BAN_CREATE.compile(
                    server_id=core.resolve_id(server), user_id=core.resolve_id(user)
                ),
                json=j,
            ),
            {},
        )

    async def get_bans(self, server: core.ULIDOr[BaseServer], /) -> list[Ban]:
        """|coro|

        Get all bans on a server.
        https://developers.revolt.chat/api/#tag/Server-Members/operation/ban_list_req
        """
        return self.state.parser.parse_bans(
            await self.request(
                routes.SERVERS_BAN_LIST.compile(server_id=core.resolve_id(server))
            )
        )

    async def unban_user(
        self, server: core.ULIDOr[BaseServer], user: core.ULIDOr[BaseUser]
    ) -> None:
        """|coro|

        Remove a user's ban.
        https://developers.revolt.chat/api/#tag/Server-Members/operation/ban_remove_req

        Raises
        ------
        Forbidden
            You do not have permissions to unban the user.
        APIError
            Unbanning the user failed.
        """
        await self.request(
            routes.SERVERS_BAN_REMOVE.compile(
                server_id=core.resolve_id(server), user_id=core.resolve_id(user)
            ),
        )

    async def create_channel(
        self,
        server: core.ULIDOr[BaseServer],
        /,
        *,
        type: ChannelType | None = None,
        name: str,
        description: str | None = None,
        nsfw: bool | None = None,
    ) -> ServerChannel:
        """|coro|

        Create a new text or voice channel within server.
        https://developers.revolt.chat/api/#tag/Server-Information/operation/channel_create_req

        Raises
        ------
        Forbidden
            You do not have permissions to create the channel.
        APIError
            Creating the channel failed.
        """
        j: raw.DataCreateServerChannel = {"name": name}
        if type is not None:
            j["type"] = type.value
        if description is not None:
            j["description"] = description
        if nsfw is not None:
            j["nsfw"] = nsfw
        channel = self.state.parser.parse_channel(
            await self.request(
                routes.SERVERS_CHANNEL_CREATE.compile(
                    server_id=core.resolve_id(server)
                ),
                json=j,
            )
        )
        assert isinstance(channel, ServerChannel)
        return channel

    async def get_server_emojis(
        self, server: core.ULIDOr[BaseServer]
    ) -> list[ServerEmoji]:
        """|coro|

        Get all emojis on a server.
        """
        return [
            self.state.parser.parse_server_emoji(e)
            for e in await self.request(
                routes.SERVERS_EMOJI_LIST.compile(server_id=core.resolve_id(server))
            )
        ]

    async def get_server_invites(
        self, server: core.ULIDOr[ServerChannel], /
    ) -> list[ServerInvite]:
        """|coro|

        Get all server invites.

        Raises
        ------
        Forbidden
            You do not have permissions to manage the server.
        APIError
            Getting the invites failed.
        """
        return [
            self.state.parser.parse_server_invite(i)
            for i in await self.request(
                routes.SERVERS_INVITES_FETCH.compile(server_id=core.resolve_id(server))
            )
        ]

    async def edit_member(
        self,
        server: core.ULIDOr[BaseServer],
        member: str | BaseUser | BaseMember,
        /,
        *,
        nickname: core.UndefinedOr[str | None] = core.UNDEFINED,
        avatar: core.UndefinedOr[str | None] = core.UNDEFINED,
        roles: core.UndefinedOr[list[core.ULIDOr[BaseRole]] | None] = core.UNDEFINED,
        timeout: core.UndefinedOr[
            datetime | timedelta | float | int | None
        ] = core.UNDEFINED,
    ) -> Member:
        """|coro|

        Edits the member.

        Returns
        -------
        :class:`Member`
            The updated member.
        """
        j: raw.DataMemberEdit = {}
        r: list[raw.FieldsMember] = []
        if core.is_defined(nickname):
            if nickname is not None:
                j["nickname"] = nickname
            else:
                r.append("Nickname")
        if core.is_defined(avatar):
            if avatar is not None:
                j["avatar"] = avatar
            else:
                r.append("Avatar")
        if core.is_defined(roles):
            if roles is not None:
                j["roles"] = [core.resolve_id(e) for e in roles]
            else:
                r.append("Roles")
        if core.is_defined(timeout):
            if timeout is None:
                r.append("Timeout")
            elif isinstance(timeout, datetime):
                j["timeout"] = timeout.isoformat()
            elif isinstance(timeout, timedelta):
                j["timeout"] = (datetime.now() + timeout).isoformat()
            elif isinstance(timeout, (float, int)):
                j["timeout"] = (datetime.now() + timedelta(seconds=timeout)).isoformat()
        if len(r) > 0:
            j["remove"] = r
        return self.state.parser.parse_member(
            await self.request(
                routes.SERVERS_MEMBER_EDIT.compile(
                    server_id=core.resolve_id(server),
                    member_id=core.resolve_id(member),
                ),
                json=j,
            )
        )

    async def query_members_by_name(
        self, server: core.ULIDOr[BaseServer], query: str, /
    ) -> list[Member]:
        """|coro|

        Query members by a given name, this API is not stable and will be removed in the future.
        https://developers.revolt.chat/api/#tag/Server-Members/operation/member_experimental_query_member_experimental_query
        """
        return self.state.parser.parse_members_with_users(
            await self.request(
                routes.SERVERS_MEMBER_EXPERIMENTAL_QUERY.compile(
                    server_id=core.resolve_id(server)
                ),
                params={
                    "query": query,
                    "experimental_api": "true",
                },
            )
        )

    async def get_member(
        self,
        server: core.ULIDOr[BaseServer],
        member: str | BaseUser | BaseMember,
        /,
    ) -> Member:
        """|coro|

        Retrieve a member.
        https://developers.revolt.chat/api/#tag/Server-Members/operation/member_fetch_req
        """
        return self.state.parser.parse_member(
            await self.request(
                routes.SERVERS_MEMBER_FETCH.compile(
                    server_id=core.resolve_id(server),
                    member_id=core.resolve_id(member),
                )
            )
        )

    async def get_members(
        self, server: core.ULIDOr[BaseServer], /, *, exclude_offline: bool | None = None
    ) -> list[Member]:
        """|coro|

        Retrieve all server members.
        https://developers.revolt.chat/api/#tag/Server-Members/operation/member_fetch_all_req

        Parameters
        ----------
        exclude_offline: :class:`bool` | None
            Whether to exclude offline users.
        """
        p: raw.OptionsFetchAllMembers = {}
        if exclude_offline is not None:
            p["exclude_offline"] = utils._bool(exclude_offline)
        return self.state.parser.parse_members_with_users(
            await self.request(
                routes.SERVERS_MEMBER_FETCH_ALL.compile(
                    server_id=core.resolve_id(server)
                ),
                params=p,
            )
        )

    async def get_member_list(
        self, server: core.ULIDOr[BaseServer], /, *, exclude_offline: bool | None = None
    ) -> MemberList:
        """|coro|

        Retrieve server members list.
        https://developers.revolt.chat/api/#tag/Server-Members/operation/member_fetch_all_req

        Parameters
        ----------
        exclude_offline: :class:`bool` | None
            Whether to exclude offline users.
        """
        p: raw.OptionsFetchAllMembers = {}
        if exclude_offline is not None:
            p["exclude_offline"] = utils._bool(exclude_offline)
        return self.state.parser.parse_member_list(
            await self.request(
                routes.SERVERS_MEMBER_FETCH_ALL.compile(
                    server_id=core.resolve_id(server)
                ),
                params=p,
            )
        )

    async def kick_member(
        self, server: core.ULIDOr[BaseServer], member: str | BaseUser | BaseMember, /
    ) -> None:
        """|coro|

        Removes a member from the server.
        https://developers.revolt.chat/api/#tag/Server-Members/operation/member_remove_req

        Raises
        ------
        Forbidden
            You do not have permissions to kick the member.
        APIError
            Kicking the member failed.
        """
        await self.request(
            routes.SERVERS_MEMBER_REMOVE.compile(
                server_id=core.resolve_id(server), member_id=core.resolve_id(member)
            )
        )

    async def set_role_server_permissions(
        self,
        server: core.ULIDOr[BaseServer],
        role: core.ULIDOr[BaseRole],
        /,
        *,
        allow: Permissions = Permissions.NONE,
        deny: Permissions = Permissions.NONE,
    ) -> Server:
        """|coro|

        Sets permissions for the specified role in the server.
        https://developers.revolt.chat/api/#tag/Server-Permissions/operation/permissions_set_req

        Parameters
        ----------
        allow: :class:`permissions.Permissions`
            New allow bit flags.
        deny: :class:`permissions.Permissions`
            New deny bit flags.

        Raises
        ------
        Forbidden
            You do not have permissions to set role permissions on the server.
        APIError
            Setting permissions failed.
        """
        j: raw.DataSetRolePermissions = {
            "permissions": {"allow": int(allow), "deny": int(deny)}
        }
        d: raw.Server = await self.request(
            routes.SERVERS_PERMISSIONS_SET.compile(
                server_id=core.resolve_id(server), role_id=core.resolve_id(role)
            ),
            json=j,
        )

        parser = self.state.parser

        return parser.parse_server(
            d, (True, [parser.parse_id(channel) for channel in d["channels"]])
        )

    async def set_default_role_permissions(
        self,
        server: core.ULIDOr[BaseServer],
        permissions: Permissions | PermissionOverride,
        /,
    ) -> Server:
        """|coro|

        Sets permissions for the default role in this server.
        https://developers.revolt.chat/api/#tag/Server-Permissions/operation/permissions_set_default_req

        Raises
        ------
        Forbidden
            You do not have permissions to set default permissions on the server.
        APIError
            Setting permissions failed.
        """
        j: raw.DataDefaultChannelPermissions = {
            "permissions": (
                permissions.build()
                if isinstance(permissions, PermissionOverride)
                else int(permissions)
            )
        }
        d: raw.Server = await self.request(
            routes.SERVERS_PERMISSIONS_SET_DEFAULT.compile(
                server_id=core.resolve_id(server)
            ),
            json=j,
        )
        return self.state.parser.parse_server(
            d, (True, [self.state.parser.parse_id(c) for c in d["channels"]])
        )

    async def create_role(
        self, server: core.ULIDOr[BaseServer], /, *, name: str, rank: int | None = None
    ) -> Role:
        """|coro|

        Creates a new server role.
        https://developers.revolt.chat/api/#tag/Server-Permissions/operation/roles_create_req


        Parameters
        ----------
        name: :class:`str` | None
            Role name. Should be between 1 and 32 chars long.
        rank: :class:`int` | None
            Ranking position. Smaller values take priority.

        Raises
        ------
        Forbidden
            You do not have permissions to create the role.
        APIError
            Creating the role failed.
        """
        server_id = core.resolve_id(server)
        j: raw.DataCreateRole = {"name": name, "rank": rank}
        d: raw.NewRoleResponse = await self.request(
            routes.SERVERS_ROLES_CREATE.compile(server_id=server_id),
            json=j,
        )
        return self.state.parser.parse_role(
            d["role"], self.state.parser.parse_id(d["id"]), server_id
        )

    async def delete_role(
        self, server: core.ULIDOr[BaseServer], role: core.ULIDOr[BaseRole], /
    ) -> None:
        """|coro|

        Delete a server role.
        https://developers.revolt.chat/api/#tag/Server-Permissions/operation/roles_delete_req

        Raises
        ------
        Forbidden
            You do not have permissions to delete the role.
        APIError
            Deleting the role failed.
        """
        await self.request(
            routes.SERVERS_ROLES_DELETE.compile(
                server_id=core.resolve_id(server), role_id=core.resolve_id(role)
            )
        )

    async def edit_role(
        self,
        server: core.ULIDOr[BaseServer],
        role: core.ULIDOr[BaseRole],
        /,
        *,
        name: core.UndefinedOr[str] = core.UNDEFINED,
        colour: core.UndefinedOr[str | None] = core.UNDEFINED,
        hoist: core.UndefinedOr[bool] = core.UNDEFINED,
        rank: core.UndefinedOr[int] = core.UNDEFINED,
    ) -> Role:
        """|coro|

        Edits the role.
        https://developers.revolt.chat/api/#tag/Server-Permissions/operation/roles_edit_req

        Parameters
        ----------
        name: :class:`core.UndefinedOr`[:class:`str`]
            New role name. Should be between 1 and 32 chars long.
        colour: :class:`core.UndefinedOr`[:class:`str` | None]
            New role colour.
        hoist: :class:`core.UndefinedOr`[:class:`bool`]
            Whether this role should be displayed separately.
        rank: :class:`core.UndefinedOr`[:class:`int`]
            Ranking position. Smaller values take priority.

        Raises
        ------
        Forbidden
            You do not have permissions to edit the role.
        APIError
            Editing the role failed.
        """
        j: raw.DataEditRole = {}
        r: list[raw.FieldsRole] = []
        if core.is_defined(name):
            j["name"] = name
        if core.is_defined(colour):
            if colour is not None:
                j["colour"] = colour
            else:
                r.append("Colour")
        if core.is_defined(hoist):
            j["hoist"] = hoist
        if core.is_defined(rank):
            j["rank"] = rank
        if len(r) > 0:
            j["remove"] = r

        server_id = core.resolve_id(server)
        role_id = core.resolve_id(role)

        return self.state.parser.parse_role(
            await self.request(
                routes.SERVERS_ROLES_EDIT.compile(
                    server_id=core.resolve_id(server), role_id=core.resolve_id(role)
                ),
                json=j,
            ),
            role_id,
            server_id,
        )

    async def get_role(
        self,
        server: core.ULIDOr[BaseServer],
        role: core.ULIDOr[BaseRole],
        /,
    ) -> Role:
        """|coro|

        Get a server role.

        Raises
        ------
        APIError
            Getting the role failed.
        """
        server_id = core.resolve_id(server)
        role_id = core.resolve_id(role)

        return self.state.parser.parse_role(
            await self.request(
                routes.SERVERS_ROLES_FETCH.compile(server_id=server_id, role_id=role_id)
            ),
            role_id,
            server_id,
        )

    async def mark_server_as_read(self, server: core.ULIDOr[BaseServer], /) -> None:
        """|coro|

        Mark all channels in a server as read.
        https://developers.revolt.chat/api/#tag/Server-Information/operation/server_ack_req

        .. note::
            This can only be used by non-bot accounts.
        """
        await self.request(
            routes.SERVERS_SERVER_ACK.compile(server_id=core.resolve_id(server))
        )

    async def create_server(
        self, name: str, /, *, description: str | None = None, nsfw: bool | None = None
    ) -> Server:
        """|coro|

        Create a new server.
        https://developers.revolt.chat/api/#tag/Server-Information/operation/server_create_req

        Parameters
        ----------
        name: :class:`str`
            The server name.
        description: :class:`str`
            The server description.
        nsfw: :class:`bool`
            Whether this server is age-restricted.
        """
        j: raw.DataCreateServer = {"name": name}
        if description is not None:
            j["description"] = description
        if nsfw is not None:
            j["nsfw"] = nsfw
        d: raw.CreateServerLegacyResponse = await self.request(
            routes.SERVERS_SERVER_CREATE.compile(), json=j
        )

        return self.state.parser.parse_server(
            d["server"],
            (False, d["channels"]),
        )

    async def delete_server(self, server: core.ULIDOr[BaseServer], /) -> None:
        """|coro|

        Deletes a server if owner otherwise leaves.
        https://developers.revolt.chat/api/#tag/Server-Information/operation/server_delete_req
        """
        await self.request(
            routes.SERVERS_SERVER_DELETE.compile(server_id=core.resolve_id(server))
        )

    async def leave_server(
        self, server: core.ULIDOr[BaseServer], /, *, silent: bool | None = None
    ) -> None:
        """|coro|

        Leaves the server.
        https://developers.revolt.chat/api/#tag/Server-Information/operation/server_delete_req

        Parameters
        ----------
        leave_silently: :class:`bool`
            Whether to not send a leave message.
        """
        p: raw.OptionsServerDelete = {}
        if silent is not None:
            p["leave_silently"] = utils._bool(silent)
        await self.request(
            routes.SERVERS_SERVER_DELETE.compile(server_id=core.resolve_id(server)),
            params=p,
        )

    async def edit_server(
        self,
        server: core.ULIDOr[BaseServer],
        /,
        *,
        name: core.UndefinedOr[str] = core.UNDEFINED,
        description: core.UndefinedOr[str | None] = core.UNDEFINED,
        icon: core.UndefinedOr[cdn.ResolvableResource | None] = core.UNDEFINED,
        banner: core.UndefinedOr[cdn.ResolvableResource | None] = core.UNDEFINED,
        categories: core.UndefinedOr[list[Category] | None] = core.UNDEFINED,
        system_messages: core.UndefinedOr[
            SystemMessageChannels | None
        ] = core.UNDEFINED,
        flags: core.UndefinedOr[ServerFlags] = core.UNDEFINED,
        discoverable: core.UndefinedOr[bool] = core.UNDEFINED,
        analytics: core.UndefinedOr[bool] = core.UNDEFINED,
    ) -> Server:
        """|coro|

        Edits the server.
        https://developers.revolt.chat/api/#tag/Server-Information/operation/server_edit_req

        Parameters
        ----------
        name: :class:`core.UndefinedOr`[:class:`str`]
            New server name. Should be between 1 and 32 chars long.
        description: :class:`core.UndefinedOr`[:class:`str` | None]
            New server description. Can be 1024 chars maximum long.
        icon: :class:`core.UndefinedOr`[:class:`cdn.ResolvableResource` | None]
            New server icon.
        banner: :class:`core.UndefinedOr`[:class:`cdn.ResolvableResource` | None]
            New server banner.
        categories: :class:`core.UndefinedOr`[:class:`list`[:class:`Category`] | None]
            New category structure for this server.
        system_messsages: :class:`core.UndefinedOr`[:class:`SystemMessageChannels` | None]
            New system message channels configuration.
        flags: :class:`core.UndefinedOr`[:class:`ServerFlags`]
            Bitfield of server flags. Can be passed only if you're privileged user.
        discoverable: :class:`core.UndefinedOr`[:class:`bool`]
            Whether this server is public and should show up on [Revolt Discover](https://rvlt.gg). Can be passed only if you're privileged user.
        analytics: :class:`core.UndefinedOr`[:class:`bool`]
            Whether analytics should be collected for this server. Must be enabled in order to show up on [Revolt Discover](https://rvlt.gg).

        Raises
        ------
        Forbidden
            You do not have permissions to edit the server.
        APIError
            Editing the server failed.
        """
        j: raw.DataEditServer = {}
        r: list[raw.FieldsServer] = []
        if core.is_defined(name):
            j["name"] = name
        if core.is_defined(description):
            if description is not None:
                j["description"] = description
            else:
                r.append("Description")
        if core.is_defined(icon):
            if icon is not None:
                j["icon"] = await cdn.resolve_resource(self.state, icon, tag="icons")
            else:
                r.append("Icon")
        if core.is_defined(banner):
            if banner is not None:
                j["banner"] = await cdn.resolve_resource(
                    self.state, banner, tag="banners"
                )
            else:
                r.append("Banner")
        if core.is_defined(categories):
            if categories is not None:
                j["categories"] = [e.build() for e in categories]
            else:
                r.append("Categories")
        if core.is_defined(system_messages):
            if system_messages is not None:
                j["system_messages"] = system_messages.build()
            else:
                r.append("SystemMessages")
        if core.is_defined(flags):
            j["flags"] = int(flags)
        if core.is_defined(discoverable):
            j["discoverable"] = discoverable
        if core.is_defined(analytics):
            j["analytics"] = analytics
        if len(r) > 0:
            j["remove"] = r

        d: raw.Server = await self.request(
            routes.SERVERS_SERVER_EDIT.compile(server_id=core.resolve_id(server)),
            json=j,
        )
        return self.state.parser.parse_server(
            d, (True, [self.state.parser.parse_id(c) for c in d["channels"]])
        )

    async def get_server(
        self,
        server: core.ULIDOr[BaseServer],
        /,
        *,
        populate_channels: bool | None = None,
    ) -> Server:
        """|coro|

        Get a server.
        https://developers.revolt.chat/api/#tag/Server-Information/operation/server_fetch_req

        Parameters
        ----------
        populate_channels: :class:`bool`
            Whether to include
        """
        p: raw.OptionsFetchServer = {}
        if populate_channels is not None:
            p["include_channels"] = utils._bool(populate_channels)
        d: raw.FetchServerResponse = await self.request(
            routes.SERVERS_SERVER_FETCH.compile(server_id=core.resolve_id(server))
        )
        return self.state.parser.parse_server(
            d,  # type: ignore
            (not populate_channels, d["channels"]),  # type: ignore
        )

    # Sync control
    async def get_user_settings(self, keys: list[str], /) -> UserSettings:
        """|coro|

        Get user settings from server filtered by keys.

        This will return an object with the requested keys, each value is a tuple of `(timestamp, value)`, the value is the previously uploaded data.

        .. note::
            This can only be used by non-bot accounts.
        """
        # Sync endpoints aren't meant to be used with bot accounts
        j: raw.OptionsFetchSettings = {"keys": keys}
        return self.state.parser.parse_user_settings(
            await self.request(routes.SYNC_GET_SETTINGS.compile(), json=j),
        )

    async def get_unreads(self) -> list[ReadState]:
        """|coro|

        Get information about unread state on

        .. note::
            This can only be used by non-bot accounts.
        """
        return [
            self.state.parser.parse_read_state(rs)
            for rs in await self.request(routes.SYNC_GET_UNREADS.compile())
        ]

    @t.overload
    async def edit_user_settings(
        self,
        timestamp: datetime | int | None = ...,
        dict_settings: dict[str, str] = ...,
        /,
        **kw_settings: str,
    ) -> None: ...

    @t.overload
    async def edit_user_settings(
        self,
        dict_settings: dict[str, str] = ...,
        timestamp: datetime | int | None = ...,
        /,
        **kw_settings: str,
    ) -> None: ...

    @t.overload
    async def edit_user_settings(
        self,
        a1: dict[str, str] | datetime | int | None = ...,
        a2: dict[str, str] | datetime | int | None = ...,
        /,
        **kwargs: str,
    ) -> None: ...

    async def edit_user_settings(
        self,
        a1: dict[str, str] | datetime | int | None = None,
        a2: dict[str, str] | datetime | int | None = {},
        /,
        **kwargs: str,
    ) -> None:
        """|coro|

        Modify current user settings.

        .. note::
            This can only be used by non-bot accounts.
        """

        p: raw.OptionsSetSettings = {}

        # probably JavaScript way
        if isinstance(a1, dict):
            if isinstance(a2, dict):
                j: raw.DataSetSettings = a1 | a2
                timestamp: datetime | int | None = None
            else:
                j = a1
                timestamp = a2
        elif isinstance(a2, dict):
            j = a2
            timestamp = a1
        else:
            j = {}
            if a1 is None or isinstance(a1, (datetime, int)):
                timestamp = a1
            elif a2 is None or isinstance(a2, (datetime, int)):
                timestamp = a2
            else:
                timestamp = None

        j |= kwargs
        if timestamp is not None:
            if isinstance(timestamp, datetime):
                timestamp = int(timestamp.timestamp())
            p["timestamp"] = timestamp
        await self.request(routes.SYNC_SET_SETTINGS.compile(), json=j, params=p)

    # Users control
    async def accept_friend_request(self, user: core.ULIDOr[BaseUser], /) -> User:
        """|coro|

        Accept another user's friend request.
        https://developers.revolt.chat/api/#tag/Relationships/operation/add_friend_req

        .. note::
            This can only be used by non-bot accounts.
        """
        return self.state.parser.parse_user(
            await self.request(
                routes.USERS_ADD_FRIEND.compile(user_id=core.resolve_id(user))
            )
        )

    async def block_user(self, user: core.ULIDOr[BaseUser], /) -> User:
        """|coro|

        Block another user by their ID.
        https://developers.revolt.chat/api/#tag/Relationships/operation/block_user_req

        .. note::
            This can only be used by non-bot accounts.
        """
        return self.state.parser.parse_user(
            await self.request(
                routes.USERS_BLOCK_USER.compile(user_id=core.resolve_id(user))
            )
        )

    async def change_username(self, username: str, /, *, password: str) -> User:
        """|coro|

        Change your username.
        https://developers.revolt.chat/api/#tag/User-Information/operation/change_username_req

        .. note::
            This can only be used by non-bot accounts.
        """
        j: raw.DataChangeUsername = {"username": username, "password": password}
        return self.state.parser.parse_user(
            await self.request(
                routes.USERS_CHANGE_USERNAME.compile(),
                json=j,
            )
        )

    async def _edit_user(
        self,
        route: routes.CompiledRoute,
        /,
        *,
        display_name: core.UndefinedOr[str | None] = core.UNDEFINED,
        avatar: core.UndefinedOr[cdn.ResolvableResource | None] = core.UNDEFINED,
        status: core.UndefinedOr[UserStatusEdit] = core.UNDEFINED,
        profile: core.UndefinedOr[UserProfileEdit] = core.UNDEFINED,
        badges: core.UndefinedOr[UserBadges] = core.UNDEFINED,
        flags: core.UndefinedOr[UserFlags] = core.UNDEFINED,
    ) -> User:
        j: raw.DataEditUser = {}
        r: list[raw.FieldsUser] = []
        if core.is_defined(display_name):
            if display_name is None:
                r.append("DisplayName")
            else:
                j["display_name"] = display_name
        if core.is_defined(avatar):
            if avatar is None:
                r.append("Avatar")
            else:
                j["avatar"] = await cdn.resolve_resource(
                    self.state, avatar, tag="avatars"
                )
        if core.is_defined(status):
            j["status"] = status.build()
            r.extend(status.remove)
        if core.is_defined(profile):
            j["profile"] = await profile.build(self.state)
            r.extend(profile.remove)
        if core.is_defined(badges):
            j["badges"] = int(badges)
        if core.is_defined(flags):
            j["flags"] = int(flags)
        if len(r) > 0:
            j["remove"] = r
        d: raw.User = await self.request(route, json=j)
        return self.state.parser.parse_user(d)

    async def edit_self_user(
        self,
        *,
        display_name: core.UndefinedOr[str] = core.UNDEFINED,
        avatar: core.UndefinedOr[cdn.ResolvableResource | None] = core.UNDEFINED,
        status: core.UndefinedOr[UserStatusEdit] = core.UNDEFINED,
        profile: core.UndefinedOr[UserProfileEdit] = core.UNDEFINED,
        badges: core.UndefinedOr[UserBadges] = core.UNDEFINED,
        flags: core.UndefinedOr[UserFlags] = core.UNDEFINED,
    ) -> SelfUser:
        """|coro|

        Edits the user.
        https://developers.revolt.chat/api/#tag/User-Information/operation/edit_user_req

        Parameters
        ----------
        display_name: :class:`core.UndefinedOr`[:class:`str`] | None
            New display name. Pass ``None`` to remove it.
        avatar: :class:`core.UndefinedOr`[:class:`cdn.ResolvableULID`] | None
            New avatar. Pass ``None`` to remove it.
        status: :class:`core.UndefinedOr`[:class:`UserStatusEdit`]
            New user status.
        profile: :class:`core.UndefinedOr`[:class:`UserProfileEdit`]
            New user profile data. This is applied as a partial.
        badges: :class:`core.UndefinedOr`[:class:`UserBadges`]
            Bitfield of new user badges.
        flags: :class:`core.UndefinedOr`[:class:`UserFlags`]
            Bitfield of new user flags.

        Raises
        ------
        APIError
            Editing the user failed.
        """
        user = await self._edit_user(
            routes.USERS_EDIT_SELF_USER.compile(),
            display_name=display_name,
            avatar=avatar,
            status=status,
            profile=profile,
            badges=badges,
            flags=flags,
        )
        return user  # type: ignore

    async def edit_user(
        self,
        user: core.ULIDOr[BaseUser],
        /,
        *,
        display_name: core.UndefinedOr[str] = core.UNDEFINED,
        avatar: core.UndefinedOr[cdn.ResolvableResource | None] = core.UNDEFINED,
        status: core.UndefinedOr[UserStatusEdit] = core.UNDEFINED,
        profile: core.UndefinedOr[UserProfileEdit] = core.UNDEFINED,
        badges: core.UndefinedOr[UserBadges] = core.UNDEFINED,
        flags: core.UndefinedOr[UserFlags] = core.UNDEFINED,
    ) -> User:
        """|coro|

        Edits the user.
        https://developers.revolt.chat/api/#tag/User-Information/operation/edit_user_req

        Parameters
        ----------
        display_name: :class:`core.UndefinedOr`[:class:`str`] | None
            New display name. Pass ``None`` to remove it.
        avatar: :class:`core.UndefinedOr`[:class:`cdn.ResolvableResource`] | None
            New avatar. Pass ``None`` to remove it.
        status: :class:`core.UndefinedOr`[:class:`UserStatusEdit`]
            New user status.
        profile: :class:`core.UndefinedOr`[:class:`UserProfileEdit`]
            New user profile data. This is applied as a partial.
        badges: :class:`core.UndefinedOr`[:class:`UserBadges`]
            Bitfield of new user badges.
        flags: :class:`core.UndefinedOr`[:class:`UserFlags`]
            Bitfield of new user flags.


        Raises
        ------
        Forbidden
            Target user have blocked you.
        APIError
            Editing the user failed.
        """
        return await self._edit_user(
            routes.USERS_EDIT_USER.compile(user_id=core.resolve_id(user)),
            display_name=display_name,
            avatar=avatar,
            status=status,
            profile=profile,
            badges=badges,
            flags=flags,
        )

    async def get_direct_message_channels(
        self,
    ) -> list[DMChannel | GroupChannel]:
        """|coro|

        Get all DMs and groups conversations.
        https://developers.revolt.chat/api/#tag/Direct-Messaging/operation/fetch_dms_req
        """
        return [
            self.state.parser.parse_channel(e)
            for e in await self.request(routes.USERS_FETCH_DMS.compile())
        ]  # type: ignore # The returned channels are always DM/Groups

    async def get_user_profile(self, user: core.ULIDOr[BaseUser], /) -> UserProfile:
        """|coro|

        Retrieve a user's profile data.
        Will fail if you do not have permission to access the other user's profile.
        https://developers.revolt.chat/api/#tag/User-Information/operation/fetch_profile_req
        """
        user_id = core.resolve_id(user)
        return self.state.parser.parse_user_profile(
            await self.request(routes.USERS_FETCH_PROFILE.compile(user_id=user_id))
        )._stateful(self.state, user_id)

    async def get_self_user(self) -> User:
        """|coro|

        Retrieve your user information.
        https://developers.revolt.chat/api/#tag/User-Information/operation/fetch_self_req

        Raises
        ------
        APIError
            Invalid token.
        """
        return self.state.parser.parse_user(
            await self.request(routes.USERS_FETCH_SELF.compile())
        )

    async def get_user(self, user: core.ULIDOr[BaseUser], /) -> User:
        """|coro|

        Retrieve a user's information.
        https://developers.revolt.chat/api/#tag/User-Information/operation/fetch_user_req

        Parameters
        ----------
        user: :class:`core.ResolvableULID`
            The user.

        Raises
        ------
        APIError
            Invalid token, or you been blocked by that user.
        """
        return self.state.parser.parse_user(
            await self.request(
                routes.USERS_FETCH_USER.compile(user_id=core.resolve_id(user))
            )
        )

    async def get_user_flags(self, user: core.ULIDOr[BaseUser], /) -> UserFlags:
        """|coro|

        Retrieve a user's flags.
        https://developers.revolt.chat/api/#tag/User-Information/operation/fetch_user_flags_fetch_user_flags
        """
        return UserFlags(
            (
                await self.request(
                    routes.USERS_FETCH_USER_FLAGS.compile(user_id=core.resolve_id(user))
                )
            )["flags"]
        )

    async def get_mutual_friends_and_servers(
        self, user: core.ULIDOr[BaseUser], /
    ) -> Mutuals:
        """|coro|

        Retrieve a list of mutual friends and servers with another user.
        https://developers.revolt.chat/api/#tag/Relationships/operation/find_mutual_req

        Raises
        ------
        APIError
            Finding mutual friends/servers failed.
        """
        return self.state.parser.parse_mutuals(
            await self.request(
                routes.USERS_FIND_MUTUAL.compile(user_id=core.resolve_id(user))
            )
        )

    async def get_default_avatar(self, user: core.ULIDOr[BaseUser], /) -> bytes:
        """|coro|

        This returns a default avatar based on the given ID.
        https://developers.revolt.chat/api/#tag/User-Information/operation/get_default_avatar_req
        """
        response = await self._request(
            routes.USERS_GET_DEFAULT_AVATAR.compile(user_id=core.resolve_id(user))
        )
        avatar = await response.read()
        if not response.closed:
            response.close()
        return avatar

    async def open_dm(
        self, user: core.ULIDOr[BaseUser], /
    ) -> SavedMessagesChannel | DMChannel:
        """|coro|

        Open a DM with another user. If the target is oneself, a saved messages channel is returned.
        https://developers.revolt.chat/api/#tag/Direct-Messaging/operation/open_dm_req


        Raises
        ------
        APIError
            Opening DM failed.
        """
        channel = self.state.parser.parse_channel(
            await self.request(
                routes.USERS_OPEN_DM.compile(user_id=core.resolve_id(user))
            )
        )
        assert isinstance(channel, (SavedMessagesChannel, DMChannel))
        return channel

    async def deny_friend_request(self, user: core.ULIDOr[BaseUser], /) -> User:
        """|coro|

        Denies another user's friend request.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        APIError
            Denying the friend request failed.
        """
        return self.state.parser.parse_user(
            await self.request(
                routes.USERS_REMOVE_FRIEND.compile(user_id=core.resolve_id(user))
            )
        )

    async def remove_friend(self, user: core.ULIDOr[BaseUser], /) -> User:
        """|coro|

        Removes an existing friend.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        APIError
            Removing the friend failed.
        """
        return self.state.parser.parse_user(
            await self.request(
                routes.USERS_REMOVE_FRIEND.compile(user_id=core.resolve_id(user))
            )
        )

    async def send_friend_request(
        self, username: str, discriminator: str | None = None, /
    ) -> User:
        """|coro|

        Send a friend request to another user.
        https://developers.revolt.chat/api/#tag/Relationships/operation/send_friend_request_req

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        username: :class:`str`
            Username and discriminator combo separated by `#`.

        Raises
        ------
        Forbidden
            Target user have blocked you.
        APIError
            Sending the friend request failed.
        """
        if discriminator is not None:
            username += "#" + discriminator
        j: raw.DataSendFriendRequest = {"username": username}
        return self.state.parser.parse_user(
            await self.request(
                routes.USERS_SEND_FRIEND_REQUEST.compile(),
                json=j,
            )
        )

    async def unblock_user(self, user: core.ULIDOr[BaseUser], /) -> User:
        """|coro|

        Unblock another user by their ID.
        https://developers.revolt.chat/api/#tag/Relationships/operation/unblock_user_req

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        Forbidden
            Target user have blocked you.
        APIError
            Sending the friend request failed.
        """
        return self.state.parser.parse_user(
            await self.request(
                routes.USERS_UNBLOCK_USER.compile(user_id=core.resolve_id(user))
            )
        )

    # Webhooks control
    async def delete_webhook(
        self, webhook: core.ULIDOr[BaseWebhook], /, *, token: str | None = None
    ) -> None:
        """|coro|

        Deletes a webhook. If webhook token wasn't given, the library will attempt delete webhook with current bot/user token.

        Raises
        ------
        Forbidden
            You do not have permissions to delete the webhook.
        APIError
            Deleting the webhook failed.
        """
        if token is None:
            await self.request(
                routes.WEBHOOKS_WEBHOOK_DELETE.compile(
                    webhook_id=core.resolve_id(webhook)
                )
            )
        else:
            await self.request(
                routes.WEBHOOKS_WEBHOOK_DELETE_TOKEN.compile(
                    webhook_id=core.resolve_id(webhook), webhook_token=token
                ),
                authenticated=False,
            )

    async def edit_webhook(
        self,
        webhook: core.ULIDOr[BaseWebhook],
        /,
        *,
        token: str | None = None,
        name: core.UndefinedOr[str] = core.UNDEFINED,
        avatar: core.UndefinedOr[cdn.ResolvableResource | None] = core.UNDEFINED,
        permissions: core.UndefinedOr[Permissions] = core.UNDEFINED,
    ) -> Webhook:
        """|coro|

        Edits a webhook. If webhook token wasn't given, the library will attempt edit webhook with current bot/user token.

        Parameters
        ----------
        name: :class:`core.UndefinedOr`[:class:`str` | None]
            New webhook name. Should be between 1 and 32 chars long.
        avatar: :class:`core.UndefinedOr`[:class:`cdn.ResolvableResource` | None]
            New webhook avatar.
        permissions: :class:`core.UndefinedOr`[:class:`Permissions` | None]
            New webhook permissions.

        Raises
        ------
        Forbidden
            You do not have permissions to edit the webhook.
        APIError
            Editing the webhook failed.
        """
        j: raw.DataEditWebhook = {}
        r: list[raw.FieldsWebhook] = []
        if core.is_defined(name):
            j["name"] = name
        if core.is_defined(avatar):
            if avatar is None:
                r.append("Avatar")
            else:
                j["avatar"] = await cdn.resolve_resource(
                    self.state, avatar, tag="avatars"
                )
        if core.is_defined(permissions):
            j["permissions"] = int(permissions)
        if len(r) > 0:
            j["remove"] = r
        return self.state.parser.parse_webhook(
            await self.request(
                routes.WEBHOOKS_WEBHOOK_EDIT.compile(
                    webhook_id=core.resolve_id(webhook)
                ),
                json=j,
            )
            if token is None
            else await self.request(
                routes.WEBHOOKS_WEBHOOK_EDIT_TOKEN.compile(
                    webhook_id=core.resolve_id(webhook), webhook_token=token
                ),
                json=j,
                authenticated=False,
            )
        )

    async def execute_webhook(
        self,
        webhook: core.ULIDOr[BaseWebhook],
        token: str,
        /,
        content: str | None = None,
        *,
        nonce: str | None = None,
        attachments: list[cdn.ResolvableResource] | None = None,
        replies: list[Reply | core.ULIDOr[BaseMessage]] | None = None,
        embeds: list[SendableEmbed] | None = None,
        masquerade: Masquerade | None = None,
        interactions: Interactions | None = None,
    ) -> Message:
        """|coro|

        Executes a webhook and returns a message.

        Returns
        -------
        :class:`Message`
            The message sent.
        """
        j: raw.DataMessageSend = {}
        if content is not None:
            j["content"] = content
        if attachments is not None:
            j["attachments"] = [
                await cdn.resolve_resource(self.state, attachment, tag="attachments")
                for attachment in attachments
            ]
        if replies is not None:
            j["replies"] = [
                (
                    reply.build()
                    if isinstance(reply, Reply)
                    else {"id": core.resolve_id(reply), "mention": False}
                )
                for reply in replies
            ]
        if embeds is not None:
            j["embeds"] = [await embed.build(self.state) for embed in embeds]
        if masquerade is not None:
            j["masquerade"] = masquerade.build()
        if interactions is not None:
            j["interactions"] = interactions.build()
        headers = {}
        if nonce is not None:
            headers["Idempotency-Key"] = nonce
        return self.state.parser.parse_message(
            await self.request(
                routes.WEBHOOKS_WEBHOOK_EXECUTE.compile(
                    webhook_id=core.resolve_id(webhook), webhook_token=token
                ),
                json=j,
                headers=headers,
                authenticated=False,
            )
        )

    async def get_webhook(
        self,
        webhook: core.ULIDOr[BaseWebhook],
        /,
        *,
        token: str | None = None,
    ) -> Webhook:
        """|coro|

        Gets a webhook. If webhook token wasn't given, the library will attempt get webhook with bot/user token.

        .. note::
            Due to Revolt limitation, the webhook avatar information will be partial. Fields are guaranteed to be non-zero/non-empty: `id` and `user_id`.

        Raises
        ------
        Forbidden
            You do not have permissions to get the webhook.
        APIError
            Getting the webhook failed.
        """

        return self.state.parser.parse_response_webhook(
            await (
                self.request(
                    routes.WEBHOOKS_WEBHOOK_FETCH.compile(
                        webhook_id=core.resolve_id(webhook)
                    )
                )
                if token is None
                else self.request(
                    routes.WEBHOOKS_WEBHOOK_FETCH_TOKEN.compile(
                        webhook_id=core.resolve_id(webhook), webhook_token=token
                    ),
                    authenticated=False,
                )
            )
        )

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
        APIError
            Changing the account password failed.
        """
        j: raw.a.DataChangeEmail = {
            "email": email,
            "current_password": current_password,
        }
        await self.request(
            routes.AUTH_ACCOUNT_CHANGE_EMAIL.compile(),
            json=j,
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
        APIError
            Changing the account password failed.
        """
        j: raw.a.DataChangePassword = {
            "password": new_password,
            "current_password": current_password,
        }
        await self.request(
            routes.AUTH_ACCOUNT_CHANGE_PASSWORD.compile(),
            json=j,
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
        APIError
            Confirming the account deletion failed.
        """
        j: raw.a.DataAccountDeletion = {"token": token}
        await self.request(
            routes.AUTH_ACCOUNT_CONFIRM_DELETION.compile(),
            authenticated=False,
            json=j,
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
        invite: :class:`str` | None
            The instance invite code.
        captcha: :class:`str` | None
            The CAPTCHA verification code.

        Raises
        ------
        APIError
            Registering the account failed.
        """
        j: raw.a.DataCreateAccount = {
            "email": email,
            "password": password,
            "invite": invite,
            "captcha": captcha,
        }
        await self.request(
            routes.AUTH_ACCOUNT_CREATE_ACCOUNT.compile(),
            authenticated=False,
            json=j,
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
        APIError
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
        APIError
            Disabling the account failed.
        """
        await self.request(
            routes.AUTH_ACCOUNT_DISABLE_ACCOUNT.compile(), mfa_ticket=mfa
        )

    async def get_account(self) -> PartialAccount:
        """|coro|

        Get account information from the current session.

        .. note::
            This can only be used by non-bot accounts.

        Raises
        ------
        APIError
            Getting the account data failed.
        """
        return self.state.parser.parse_partial_account(
            await self.request(routes.AUTH_ACCOUNT_FETCH_ACCOUNT.compile())
        )

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
        remove_sessions: :class:`bool` | None
            Whether to logout all sessions.

        Raises
        ------
        APIError
            Sending the email failed.
        """
        j: raw.a.DataPasswordReset = {
            "token": token,
            "password": new_password,
            "remove_sessions": remove_sessions,
        }
        await self.request(
            routes.AUTH_ACCOUNT_PASSWORD_RESET.compile(),
            authenticated=False,
            json=j,
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
        captcha: :class:`str` | None
            The CAPTCHA verification code.

        Raises
        ------
        APIError
            Resending the verification mail failed.
        """
        j: raw.a.DataResendVerification = {"email": email, "captcha": captcha}
        await self.request(
            routes.AUTH_ACCOUNT_RESEND_VERIFICATION.compile(),
            authenticated=False,
            json=j,
        )

    async def send_password_reset(
        self, *, email: str, captcha: str | None = None
    ) -> None:
        """|coro|

        Send an email to reset account password.

        Parameters
        ----------
        email: :class:`str`
            The email associated with the account.
        captcha: :class:`str` | None
            The CAPTCHA verification code.

        Raises
        ------
        APIError
            Sending the email failed.
        """
        j: raw.a.DataSendPasswordReset = {"email": email, "captcha": captcha}
        await self.request(
            routes.AUTH_ACCOUNT_SEND_PASSWORD_RESET.compile(),
            authenticated=False,
            json=j,
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
        APIError
            Verifying the email address failed.
        """
        response = await self.request(
            routes.AUTH_ACCOUNT_VERIFY_EMAIL.compile(code=code), authenticated=False
        )
        if response is not None and isinstance(response, dict) and "ticket" in response:
            return self.state.parser.parse_mfa_ticket(response["ticket"])
        else:
            return None

    # MFA authentication control
    async def _create_mfa_ticket(self, j: raw.a.MFAResponse, /) -> MFATicket:
        return self.state.parser.parse_mfa_ticket(
            await self.request(routes.AUTH_MFA_CREATE_TICKET.compile(), json=j)
        )

    async def create_password_ticket(self, password: str, /) -> MFATicket:
        """|coro|

        Create a new MFA ticket or validate an existing one.
        """
        j: raw.a.PasswordMFAResponse = {"password": password}
        return await self._create_mfa_ticket(j)

    async def create_recovery_code_ticket(self, recovery_code: str, /) -> MFATicket:
        """|coro|

        Create a new MFA ticket or validate an existing one.
        """
        j: raw.a.RecoveryMFAResponse = {"recovery_code": recovery_code}
        return await self._create_mfa_ticket(j)

    async def create_totp_ticket(self, totp_code: str, /) -> MFATicket:
        """|coro|

        Create a new MFA ticket or validate an existing one.
        """
        j: raw.a.TotpMFAResponse = {"totp_code": totp_code}
        return await self._create_mfa_ticket(j)

    async def get_recovery_codes(self) -> list[str]:
        """|coro|

        Gets recovery codes for an account.
        """
        return await self.request(routes.AUTH_MFA_GENERATE_RECOVERY.compile())

    async def mfa_status(self) -> MFAStatus:
        """|coro|

        Gets MFA status of an account.
        """
        return self.state.parser.parse_multi_factor_status(
            await self.request(routes.AUTH_MFA_FETCH_STATUS.compile()),
        )

    async def generate_recovery_codes(self, *, mfa_ticket: str) -> list[str]:
        """|coro|

        Regenerates recovery codes for an account.
        """
        return await self.request(
            routes.AUTH_MFA_GENERATE_RECOVERY.compile(), mfa_ticket=mfa_ticket
        )

    async def get_mfa_methods(self) -> list[MFAMethod]:
        """|coro|

        Gets available MFA methods.
        """
        return [
            MFAMethod(mm)
            for mm in await self.request(routes.AUTH_MFA_GET_MFA_METHODS.compile())
        ]

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
        d: raw.a.ResponseTotpSecret = await self.request(
            routes.AUTH_MFA_TOTP_GENERATE_SECRET.compile(),
            mfa_ticket=mfa_ticket,
        )
        return d["secret"]

    async def edit_session(
        self, session: core.ULIDOr[PartialSession], *, friendly_name: str
    ) -> PartialSession:
        """|coro|

        Edit session information.
        """
        j: raw.a.DataEditSession = {"friendly_name": friendly_name}
        return self.state.parser.parse_partial_session(
            await self.request(
                routes.AUTH_SESSION_EDIT.compile(
                    session_id=core.resolve_id(session), json=j
                )
            )
        )

    async def get_all_sessions(self) -> list[PartialSession]:
        """|coro|

        Get all sessions associated with this account.
        """
        sessions: list[raw.a.SessionInfo] = await self.request(
            routes.AUTH_SESSION_FETCH_ALL.compile()
        )
        return [self.state.parser.parse_partial_session(e) for e in sessions]

    async def login_with_email(
        self, email: str, password: str, /, *, friendly_name: str | None = None
    ) -> LoginResult:
        """|coro|

        Login to an account.
        """
        j: raw.a.EmailDataLogin = {
            "email": email,
            "password": password,
            "friendly_name": friendly_name,
        }
        d: raw.a.ResponseLogin = await self.request(
            routes.AUTH_SESSION_LOGIN.compile(), authenticated=False, json=j
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

        Login to an account.
        """
        j: raw.a.MFADataLogin = {
            "mfa_ticket": ticket,
            "mfa_response": by.build() if by else None,
            "friendly_name": friendly_name,
        }
        d: raw.a.ResponseLogin = await self.request(
            routes.AUTH_SESSION_LOGIN.compile(), authenticated=False, json=j
        )
        p = self.state.parser.parse_response_login(d, friendly_name)
        assert not isinstance(p, MFARequired), "Recursion detected"
        return p

    async def logout(self) -> None:
        """|coro|

        Delete current session.
        """
        await self.request(routes.AUTH_SESSION_LOGOUT.compile())

    async def revoke_session(self, session_id: core.ULIDOr[PartialSession], /) -> None:
        """|coro|

        Delete a specific active session.
        """
        await self.request(
            routes.AUTH_SESSION_REVOKE.compile(session_id=core.resolve_id(session_id))
        )

    async def revoke_all_sessions(self, *, revoke_self: bool | None = None) -> None:
        """|coro|

        Delete all active sessions, optionally including current one.
        """
        p = {}
        if revoke_self is not None:
            p["revoke_self"] = utils._bool(revoke_self)
        await self.request(routes.AUTH_SESSION_REVOKE_ALL.compile(), params=p)


__all__ = ("DEFAULT_HTTP_USER_AGENT", "_STATUS_TO_ERRORS", "HTTPClient")
