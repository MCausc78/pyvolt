"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

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

from inspect import Parameter as InspectParameter, isclass, ismethod
import re
import types
import typing

import pyvolt
from pyvolt import BaseServerChannel

from .cache import (
    MemberConverterCacheContext,
    UserConverterCacheContext,
    ServerConverterCacheContext,
    MessageConverterCacheContext,
    ServerChannelConverterCacheContext,
    TextChannelConverterCacheContext,
    VoiceChannelConverterCacheContext,
    EmojiConverterCacheContext,
)
from .errors import (
    CommandError,
    BadArgument,
    MemberNotFound,
    ServerNotFound,
    UserNotFound,
    MessageNotFound,
    ChannelIDNotReadable,
    ChannelNotFound,
    InvalidChannelType,
    ChannelNotInServer,
    CategoryNotFound,
    RoleNotFound,
    BadInviteArgument,
    EmojiNotFound,
    BadBoolArgument,
    BadUnionArgument,
    BadLiteralArgument,
)

if typing.TYPE_CHECKING:
    from ._types import BotT
    from .context import Context
    from .parameters import Parameter

T = typing.TypeVar('T')
T_co = typing.TypeVar('T_co', covariant=True)


CT = typing.TypeVar('CT', bound=pyvolt.BaseServerChannel)


@typing.runtime_checkable
class Converter(typing.Protocol[T_co]):
    """The base class of custom converters that require the :class:`.Context`
    to be passed to be useful.

    This allows you to implement converters that function similar to the
    special cased ``pyvolt`` classes.

    Classes that derive from this should override the :meth:`~.Converter.convert`
    method to do its conversion logic. This method must be a :ref:`coroutine <coroutine>`.
    """

    async def convert(self, ctx: Context[BotT], argument: str, /) -> T_co:
        """|coro|

        The method to override to do conversion logic.

        If an error is found while converting, it is recommended to
        raise a :exc:`.CommandError` derived exception as it will
        properly propagate to the error handlers.

        Note that if this method is called manually, :exc:`Exception`
        should be caught to handle the cases where a subclass does
        not explicitly inherit from :exc:`.CommandError`.

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context that the argument is being used in.
        argument: :class:`str`
            The argument that is being converted.

        Raises
        -------
        :class:`CommandError`
            A generic exception occurred when converting the argument.
        :class:`BadArgument`
            The converter failed to convert the argument.
        """
        raise NotImplementedError('Derived classes need to implement this.')


RE_ID: typing.Final[re.Pattern[str]] = re.compile(r'([0-9A-Z]{26})$')
RE_MENTION_ANY: typing.Final[re.Pattern[str]] = re.compile(r'<[ru:]?:?[@#][!&]?([0-9A-Z]{26})>')
RE_MENTION_CHANNEL: typing.Final[re.Pattern[str]] = re.compile(r'<c?#([0-9A-Z]{26})>')
RE_MENTION_ROLE: typing.Final[re.Pattern[str]] = re.compile(r'<r?@&?([0-9A-Z]{26})>')
RE_MENTION_USER: typing.Final[re.Pattern[str]] = re.compile(r'<u?@!?([0-9A-Z]{26})>')
RE_ID_PAIR: typing.Final[re.Pattern[str]] = re.compile(
    r'(?:(?P<first_id>[0-9A-Z]{26})[ -:])?(?P<second_id>[0-9A-Z]{26})$'
)

RE_CHANNEL_LINK: typing.Final[re.Pattern[str]] = re.compile(
    r'(https?:)?(\/\/)?((beta|ap[ip])\.)?revolu?t\.chat(\/ap[ip])?(\/(guild|server)s?/(?P<server_id>(@?me|[0-9A-Z]{26})))?\/channels?\/(?P<channel_id>[0-9A-Z]{26})'
)
RE_MESSAGE_LINK: typing.Final[re.Pattern[str]] = re.compile(
    r'(https?:)?(\/\/)?((beta|ap[ip])\.)?revolu?t\.chat(\/ap[ip])?(\/(guild|server)s?/(?P<server_id>(@?me|[0-9A-Z]{26})))?\/channels?\/(?P<channel_id>[0-9A-Z]{26})(\/messages?)?\/(?P<message_id>[0-9A-Z]{26})'
)
RE_EMOJI: typing.Final[re.Pattern[str]] = re.compile(r':([0-9A-Z]{26}):')


class IDConverter(Converter[T_co]):
    @staticmethod
    def _get_id_match(argument: str, /) -> typing.Optional[re.Match[str]]:
        return RE_ID.match(argument)


class BaseConverter(IDConverter[pyvolt.Base]):
    """Converts to a :class:`~pyvolt.Base`.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by member, role, or channel mention.
    """

    async def convert(self, ctx: Context[BotT], argument: str, /) -> pyvolt.Base:
        match = self._get_id_match(argument) or RE_MENTION_ANY.match(argument)

        if match is None:
            raise BadArgument(argument)

        return pyvolt.Base(
            state=ctx.shard.state,
            id=match.group(1),
        )


class MemberConverter(IDConverter[pyvolt.Member]):
    """Converts to a :class:`~pyvolt.Member`.

    All lookups are done via the local server. If in a DM context, then the lookup
    fails.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by username#discriminator (deprecated).
    5. Lookup by user name.
    6. Lookup by global name.
    7. Lookup by server nickname.
    """

    async def query_member_named(
        self,
        ctx: Context[BotT],
        cache_context: typing.Optional[MemberConverterCacheContext],
        server: pyvolt.Server,
        argument: str,
        /,
    ) -> tuple[typing.Optional[MemberConverterCacheContext], typing.Optional[pyvolt.Member]]:
        cache = server.state.cache

        username, _, discriminator = argument.rpartition('#')

        # If # isn't found then "discriminator" actually has the username
        if not username:
            discriminator, username = username, discriminator

        if discriminator == '0' or (len(discriminator) == 4 and discriminator.isdigit()):
            lookup = username
            predicate = lambda m, /: m.name == username and m.discriminator == discriminator
        else:
            lookup = argument
            predicate = lambda m, /: m.name == argument or m.global_name == argument or m.nick == argument

        members = await server.state.http.query_members_by_name(server, lookup)
        cache_context = None
        if cache is not None:
            cache_context = (
                MemberConverterCacheContext(
                    type=pyvolt.CacheContextType.custom,
                    argument=argument,
                    context=ctx,
                    server=server,
                )
                if cache_context is None
                else cache_context
            )
            cache.bulk_store_server_members(server.id, {member.id: member for member in members}, cache_context)

        for member in members:
            if predicate(member):
                return cache_context, member

        return cache_context, None

    async def query_member_by_id(
        self,
        ctx: Context[BotT],
        cache_context: typing.Optional[MemberConverterCacheContext],
        server: pyvolt.Server,
        argument: str,
        user_id: str,
        /,
    ) -> tuple[typing.Optional[MemberConverterCacheContext], typing.Optional[pyvolt.Member]]:
        cache = server.state.cache

        try:
            member = await server.state.http.get_member(server, user_id)
        except pyvolt.HTTPException:
            return cache_context, None

        if cache is not None:
            cache_context = (
                MemberConverterCacheContext(
                    type=pyvolt.CacheContextType.custom,
                    argument=argument,
                    context=ctx,
                    server=server,
                )
                if cache_context is None
                else cache_context
            )
            cache.store_server_member(member, cache_context)

        return cache_context, member

    async def convert(self, ctx: Context[BotT], argument: str, /) -> pyvolt.Member:
        server = ctx.server
        if server is None:
            raise MemberNotFound(argument=argument)

        cache = ctx.bot.state.cache
        cache_context = None
        match = self._get_id_match(argument) or re.match(r'<@!?([0-9]{15,20})>$', argument)
        result = None
        user_id = None

        if match is None:
            # not a mention...
            result = None

            if cache is not None:
                cache_context = MemberConverterCacheContext(
                    type=pyvolt.CacheContextType.custom,
                    argument=argument,
                    context=ctx,
                    server=server,
                )

                members = cache.get_server_members_mapping_of(server.id, cache_context) or {}
                username, _, discriminator = argument.rpartition('#')
                if not username:
                    discriminator, username = username, discriminator

                if len(discriminator) == 4 and discriminator.isdigit():
                    for member in members.values():
                        user = member.get_user()
                        if user is None:
                            continue

                        if user.name == username and user.discriminator == discriminator:
                            result = member
                            break
                else:
                    for member in members.values():
                        if member.nick == argument:
                            result = member
                            break
                        user = member.get_user()
                        if user is None:
                            continue
                        if user.display_name == argument or user.name == argument:
                            result = member
        else:
            user_id = match.group(1)
            if cache is not None:
                cache_context = MemberConverterCacheContext(
                    type=pyvolt.CacheContextType.custom,
                    argument=argument,
                    context=ctx,
                    server=server,
                )
                result = server.get_member(user_id)

        if result is None:
            if user_id is None:
                cache_context, result = await self.query_member_named(ctx, cache_context, server, argument)
            else:
                cache_context, result = await self.query_member_by_id(ctx, cache_context, server, argument, user_id)

        if result is None:
            raise MemberNotFound(argument=argument)

        return result


class UserConverter(IDConverter[pyvolt.User]):
    """Converts to a :class:`~pyvolt.User`.

    All lookups are done via the global user cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by username#discriminator (deprecated).
    4. Lookup by username#0 (deprecated, only gets users that migrated from their discriminator).
    5. Lookup by user name.
    6. Lookup by global name.
    """

    async def convert(self, ctx: Context[BotT], argument: str, /) -> pyvolt.User:
        cache = ctx.bot.state.cache
        match = self._get_id_match(argument) or re.match(r'<@!?([0-9]{15,20})>$', argument)
        result = None

        if match is not None:
            user_id = match.group(1)
            result = ctx.bot.get_user(user_id)
            if result is None:
                try:
                    result = await ctx.bot.http.get_user(user_id)
                except pyvolt.HTTPException:
                    raise UserNotFound(argument=argument) from None

                if cache is not None:
                    cache_context = UserConverterCacheContext(
                        type=pyvolt.CacheContextType.custom,
                        argument=argument,
                        context=ctx,
                    )
                    cache.store_user(result, cache_context)

            return result  # type: ignore

        if cache is None:
            raise UserNotFound(argument=argument)

        username, _, discriminator = argument.rpartition('#')

        # If # isn't found then "discriminator" actually has the username
        if not username:
            discriminator, username = username, discriminator

        if discriminator == '0' or (len(discriminator) == 4 and discriminator.isdigit()):
            predicate = lambda u, /: u.name == username and u.discriminator == discriminator
        else:
            predicate = lambda u, /: u.name == argument or u.global_name == argument

        users = cache.get_users_mapping()
        for user in users.values():
            if predicate(user):
                return user
        raise UserNotFound(argument=argument)


class ServerConverter(IDConverter[pyvolt.Server]):
    """Converts to a :class:`~pyvolt.Server`.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by name. (There is no disambiguation for Servers with multiple matching names).
    """

    async def convert(self, ctx: Context[BotT], argument: str, /) -> pyvolt.Server:
        cache = ctx.bot.state.cache
        match = self._get_id_match(argument)
        result = None

        if match is None:
            for server in ctx.bot.servers.values():
                if server.name == argument:
                    return server
        elif cache is not None:
            server_id = match.group(1)
            cache_context = ServerConverterCacheContext(
                type=pyvolt.CacheContextType.custom,
                argument=argument,
                context=ctx,
            )
            result = cache.get_server(server_id, cache_context)

        if result is None:
            raise ServerNotFound(argument=argument)

        return result


class BaseMessageConverter(Converter[pyvolt.BaseMessage]):
    """Converts to a :class:`pyvolt.BaseMessage`.

    The creation strategy is as follows (in order):

    1. By "{channel ID}-{message ID}" (retrieved by shift-clicking on "Copy ID")
    2. By message ID (The message is assumed to be in the context channel.)
    3. By message URL
    """

    @staticmethod
    def _get_id_matches(ctx: Context[BotT], argument: str, /) -> tuple[str, str, str]:
        match = RE_ID_PAIR.match(argument)
        if match is not None:
            return '', match.group('first_id') or ctx.channel.id, match.group('second_id')

        match = RE_MESSAGE_LINK.match(argument)
        if match is None:
            raise MessageNotFound(argument=argument)

        server_id = match['server_id']
        if server_id in ('@me', 'me'):
            server_id = ''

        channel_id = match['channel_id']
        message_id = match['message_id']

        return server_id, channel_id, message_id

    async def convert(self, ctx: Context[BotT], argument: str, /) -> pyvolt.BaseMessage:
        _, channel_id, message_id = self._get_id_matches(ctx, argument)

        return pyvolt.BaseMessage(
            state=ctx.bot.state,
            id=message_id,
            channel_id=channel_id,
        )


class MessageConverter(IDConverter[pyvolt.Message]):
    """Converts to a :class:`pyvolt.Message`.

    The lookup strategy is as follows (in order):

    1. Lookup by "{channel ID}-{message ID}" (retrieved by shift-clicking on "Copy ID")
    2. Lookup by message ID (the message **must** be in the context channel)
    3. Lookup by message URL
    """

    async def convert(self, ctx: Context[BotT], argument: str, /) -> pyvolt.Message:
        server_id, channel_id, message_id = BaseMessageConverter._get_id_matches(ctx, argument)

        cache = ctx.bot.state.cache
        if cache is not None:
            cache_context = MessageConverterCacheContext(
                type=pyvolt.CacheContextType.custom,
                context=ctx,
                argument=argument,
                server_id=server_id,
            )
            result = cache.get_message(channel_id, message_id, cache_context)
            if result is not None:
                return result

        try:
            return await ctx.bot.http.get_message(channel_id, message_id)
        except pyvolt.NotFound as exc:
            if exc.location is None or exc.location.startswith('crates/core/database/src/models/messages/'):
                raise MessageNotFound(argument=argument)
            raise ChannelNotFound(argument=argument)
        except pyvolt.Forbidden:
            raise ChannelIDNotReadable(argument=channel_id)


class ServerChannelConverter(IDConverter[pyvolt.ServerChannel]):
    """Converts to a :class:`~pyvolt.ServerChannel`.

    All lookups are via the local server. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by channel URL.
    4. Lookup by name.
    """

    async def convert(self, ctx: Context[BotT], argument: str, /) -> pyvolt.ServerChannel:
        _, channel = await self._resolve_channel(
            ctx, argument, ServerChannelConverterCacheContext, pyvolt.BaseServerChannel
        )
        if isinstance(channel, pyvolt.ServerChannel):
            return channel
        raise InvalidChannelType(argument=argument, channel=channel)

    @staticmethod
    def _parse_from_url(argument: str, /) -> str:
        match = RE_CHANNEL_LINK.match(argument)
        if match is None:
            return ''
        return match['channel_id']

    @typing.overload
    @staticmethod
    async def _resolve_channel(
        ctx: Context[BotT],
        argument: str,
        cache_context_type: type[ServerChannelConverterCacheContext],
        type: type[CT],
        /,
        *,
        fetch: bool = True,
    ) -> tuple[typing.Optional[ServerChannelConverterCacheContext], BaseServerChannel]: ...

    @typing.overload
    @staticmethod
    async def _resolve_channel(
        ctx: Context[BotT],
        argument: str,
        cache_context_type: type[TextChannelConverterCacheContext],
        type: type[CT],
        /,
        *,
        fetch: bool = True,
    ) -> tuple[typing.Optional[TextChannelConverterCacheContext], BaseServerChannel]: ...

    @typing.overload
    @staticmethod
    async def _resolve_channel(
        ctx: Context[BotT],
        argument: str,
        cache_context_type: type[VoiceChannelConverterCacheContext],
        type: type[CT],
        /,
        *,
        fetch: bool = True,
    ) -> tuple[typing.Optional[VoiceChannelConverterCacheContext], BaseServerChannel]: ...

    @staticmethod
    async def _resolve_channel(
        ctx: Context[BotT],
        argument: str,
        cache_context_type: typing.Union[
            type[ServerChannelConverterCacheContext],
            type[TextChannelConverterCacheContext],
            type[VoiceChannelConverterCacheContext],
        ],
        type: type[CT],
        /,
        *,
        fetch: bool = True,
    ) -> tuple[
        typing.Optional[
            typing.Union[
                ServerChannelConverterCacheContext, TextChannelConverterCacheContext, VoiceChannelConverterCacheContext
            ]
        ],
        BaseServerChannel,
    ]:
        bot = ctx.bot
        cache = bot.state.cache

        match = (
            IDConverter._get_id_match(argument)
            or RE_MENTION_CHANNEL.match(argument)
            or ServerChannelConverter._parse_from_url(argument)
        )

        result = None
        server = ctx.server

        cache_context = None

        if match is None:
            # not a mention
            if server is None:
                if cache is None:
                    raise ChannelNotFound(argument=argument)
                for channel in cache.get_channels_mapping().values():
                    if isinstance(channel, type) and channel.name == argument:
                        return None, channel
            elif cache is None:
                # I'm unsure how we can get here...
                channels = server.channels
                for channel in channels:
                    if isinstance(channel, type) and channel.name == argument:
                        return None, channel
                raise ChannelNotFound(argument=argument)
            else:
                for channel in cache.get_channels_mapping().values():
                    if isinstance(channel, type) and channel.name == argument:
                        return None, channel
        elif cache is None:
            raise ChannelNotFound(argument=argument)
        else:
            if isinstance(match, str):
                channel_id = match
            else:
                channel_id = match.group(1)

            if server is None:
                cache_context = cache_context_type(
                    type=pyvolt.CacheContextType.custom,
                    argument=argument,
                    context=ctx,
                    server_id='',
                )
                result = cache.get_channel(channel_id, cache_context)

            else:
                cache_context = cache_context_type(
                    type=pyvolt.CacheContextType.custom,
                    argument=argument,
                    context=ctx,
                    server_id=server.id,
                )
                result = cache.get_channel(channel_id, cache_context)
                if result is None:
                    if fetch:
                        try:
                            result = await bot.http.get_channel(channel_id)
                        except pyvolt.Forbidden:
                            raise ChannelIDNotReadable(argument=argument)
                        except pyvolt.NotFound:
                            pass
                    raise ChannelNotFound(argument=argument)

                if not isinstance(result, pyvolt.ServerChannel):
                    raise InvalidChannelType(argument=argument, channel=result)
                if result.server_id != server.id:
                    raise ChannelNotInServer(argument=argument, channel=result)

        if result is None:
            raise ChannelNotFound(argument=argument)

        if not isinstance(result, type):
            raise InvalidChannelType(argument=argument, channel=result)

        return cache_context, result


class TextChannelConverter(IDConverter[pyvolt.TextChannel]):
    """Converts to a :class:`~pyvolt.TextChannel`.

    All lookups are via the local server. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by channel URL.
    4. Lookup by name
    """

    async def convert(self, ctx: Context[BotT], argument: str, /) -> pyvolt.TextChannel:
        _, channel = await ServerChannelConverter._resolve_channel(
            ctx, argument, TextChannelConverterCacheContext, pyvolt.TextChannel
        )
        if isinstance(channel, pyvolt.TextChannel):
            return channel
        raise InvalidChannelType(argument=argument, channel=channel)


class VoiceChannelConverter(IDConverter[pyvolt.VoiceChannel]):
    """Converts to a :class:`~pyvolt.VoiceChannel`.

    All lookups are via the local server. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by channel URL.
    4. Lookup by name
    """

    async def convert(self, ctx: Context[BotT], argument: str, /) -> pyvolt.VoiceChannel:
        _, channel = await ServerChannelConverter._resolve_channel(
            ctx, argument, VoiceChannelConverterCacheContext, pyvolt.VoiceChannel
        )
        if isinstance(channel, pyvolt.VoiceChannel):
            return channel
        raise InvalidChannelType(argument=argument, channel=channel)


class CategoryConverter(IDConverter[pyvolt.Category]):
    """Converts to a :class:`~pyvolt.Category`.

    All lookups are via the local server. If in a DM context, then the lookup
    fails.

    The lookup strategy is as follows (in order):

    1. Lookup by ID
    2. Lookup by title
    """

    async def convert(self, ctx: Context[BotT], argument: str, /) -> pyvolt.Category:
        server = ctx.server
        if server is None:
            raise CategoryNotFound(argument=argument)

        categories = server.categories
        if categories is None:
            raise CategoryNotFound(argument=argument)

        for category in categories:
            if category.id == argument:
                return category

        for category in categories:
            if category.title == argument:
                return category

        raise CategoryNotFound(argument=argument)


class RoleConverter(IDConverter[pyvolt.Role]):
    """Converts to a :class:`~pyvolt.Role`.

    All lookups are via the local server. If in a DM context, the converter raises
    :exc:`.NoPrivateMessage` exception.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name
    """

    async def convert(self, ctx: Context[BotT], argument: str, /) -> pyvolt.Role:
        server = ctx.server
        if server is None:
            raise RoleNotFound(argument=argument)

        match = self._get_id_match(argument) or RE_MENTION_ROLE.match(argument)
        if match is None:
            for role in pyvolt.sort_member_roles(list(server.roles), safe=True, server_roles=server.roles):
                if role.name == argument:
                    return role
            raise RoleNotFound(argument=argument)
        else:
            result = server.roles.get(match.group(1))

        if result is None:
            raise RoleNotFound(argument=argument)

        return result


class InviteConverter(Converter[pyvolt.PublicInvite]):
    """Converts to a :class:`~pyvolt.PublicInvite`.

    This is done via an HTTP request using :meth:`pyvolt.HTTPClient.get_invite`.
    """

    async def convert(self, ctx: Context[BotT], argument: str, /) -> pyvolt.PublicInvite:
        try:
            return await ctx.bot.http.get_invite(argument)
        except Exception as exc:
            raise BadInviteArgument(argument=argument) from exc


class EmojiConverter(IDConverter[pyvolt.Emoji]):
    """Converts to a :class:`~pyvolt.Emoji`.

    All lookups are done for the local server first, if available. If that lookup
    fails, then it checks the client's global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by extracting ID from the emoji.
    3. Lookup by name
    """

    async def convert(self, ctx: Context[BotT], argument: str, /) -> pyvolt.Emoji:
        result = None

        cache = ctx.bot.state.cache
        cache_context = None
        server = ctx.server

        match = self._get_id_match(argument) or RE_EMOJI.match(argument)

        if match is None:
            if len(argument) == 26 and all(ch.isalnum() and ch.isupper() for ch in argument):
                if cache is not None:
                    cache_context = (
                        EmojiConverterCacheContext(
                            type=pyvolt.CacheContextType.custom,
                            context=ctx,
                            argument=argument,
                        )
                        if cache_context is None
                        else cache_context
                    )
                    result = cache.get_emoji(argument, cache_context)
                if result is None:
                    try:
                        return await ctx.bot.http.get_emoji(argument)
                    except pyvolt.NotFound:
                        pass
            else:
                if server is not None:
                    if cache is None:
                        raise EmojiNotFound(argument=argument)

                    cache_context = (
                        EmojiConverterCacheContext(
                            type=pyvolt.CacheContextType.custom,
                            context=ctx,
                            argument=argument,
                        )
                        if cache_context is None
                        else cache_context
                    )

                    emojis = cache.get_server_emojis_mapping_of(server.id, cache_context)
                    if emojis is not None:
                        for emoji in emojis.values():
                            if emoji.name == argument:
                                result = emoji
                                break
                    if result is None:
                        for emoji in cache.get_emojis_mapping().values():
                            if emoji.name == argument:
                                result = emoji
                                break
                elif cache is None:
                    # No cache at all...
                    raise EmojiNotFound(argument=argument)

                for emoji in cache.get_emojis_mapping().values():
                    if emoji.name == argument:
                        result = emoji
                        break

        if result is not None:
            return result

        emoji_id = argument if match is None else match.group(1)

        if cache is not None:
            cache_context = (
                EmojiConverterCacheContext(
                    type=pyvolt.CacheContextType.custom,
                    context=ctx,
                    argument=argument,
                )
                if cache_context is None
                else cache_context
            )
            result = cache.get_emoji(argument, cache_context)

        if result is None:
            try:
                result = await ctx.bot.http.get_emoji(emoji_id)
            except pyvolt.NotFound:
                result = None

        if result is None:
            raise EmojiNotFound(argument=argument)

        return result


class Greedy(list[T]):
    r"""A special converter that greedily consumes arguments until it can't.
    As a consequence of this behaviour, most input errors are silently discarded,
    since it is used as an indicator of when to stop parsing.

    When a parser error is met the greedy converter stops converting, undoes the
    internal string parsing routine, and continues parsing regularly.

    For example, in the following code:

    .. code-block:: python3

        @commands.command()
        async def test(ctx, numbers: Greedy[int], reason: str):
            await ctx.send('numbers: {}, reason: {}'.format(numbers, reason))

    An invocation of ``[p]test 1 2 3 4 5 6 hello`` would pass ``numbers`` with
    ``[1, 2, 3, 4, 5, 6]`` and ``reason`` with ``hello``\.

    For more information, check :ref:`ext_commands_special_converters`.
    """

    __slots__ = ('converter',)

    def __init__(self, *, converter: T) -> None:
        self.converter: T = converter

    def __repr__(self) -> str:
        converter = getattr(self.converter, '__name__', repr(self.converter))
        return f'Greedy[{converter}]'

    def __class_getitem__(cls, params: typing.Union[tuple[T], T], /) -> Greedy[T]:  # type: ignore
        if not isinstance(params, tuple):
            params = (params,)
        if len(params) != 1:
            raise TypeError('Greedy[...] only takes a single argument')
        converter = params[0]

        args = getattr(converter, '__args__', ())
        if converter.__class__ is types.UnionType:
            converter = typing.Union[args]

        origin = getattr(converter, '__origin__', None)

        if not (callable(converter) or isinstance(converter, Converter) or origin is not None):
            raise TypeError('Greedy[...] expects a type or a Converter instance.')

        if converter in (str, type(None)) or origin is Greedy:
            raise TypeError(f'Greedy[{converter.__name__}] is invalid.')  # type: ignore

        if origin is typing.Union and type(None) in args:
            raise TypeError(f'Greedy[{converter!r}] is invalid.')

        return cls(converter=converter)  # type: ignore

    @property
    def constructed_converter(self) -> typing.Any:
        # Only construct a converter once in order to maintain state between convert calls
        if isclass(self.converter) and issubclass(self.converter, Converter) and not ismethod(self.converter.convert):
            return self.converter()
        return self.converter


def _convert_to_bool(argument: str, /) -> bool:
    v = pyvolt.utils.decode_bool(argument)
    if v is None:
        raise BadBoolArgument(argument=argument)
    return v


_GenericAlias = type(list[T])  # type: ignore


def is_generic_type(tp: typing.Any, /, *, _GenericAlias: type = _GenericAlias) -> bool:
    return isinstance(tp, type) and issubclass(tp, typing.Generic) or isinstance(tp, _GenericAlias)


CONVERTER_MAPPING: dict[typing.Any, typing.Any] = {
    pyvolt.Base: BaseConverter,
    pyvolt.Member: MemberConverter,
    pyvolt.User: UserConverter,
    pyvolt.Message: MessageConverter,
    pyvolt.BaseMessage: BaseMessageConverter,
    pyvolt.TextChannel: TextChannelConverter,
    pyvolt.PublicInvite: InviteConverter,
    pyvolt.Server: ServerConverter,
    pyvolt.Role: RoleConverter,
    pyvolt.VoiceChannel: VoiceChannelConverter,
    pyvolt.Emoji: EmojiConverter,
    pyvolt.Category: CategoryConverter,
    pyvolt.ServerChannel: ServerChannelConverter,
}


async def _actual_conversion(
    ctx: Context[BotT], converter: typing.Any, argument: str, param: InspectParameter, /
) -> typing.Any:
    if converter is bool:
        return _convert_to_bool(argument)

    try:
        module = converter.__module__
    except AttributeError:
        pass
    else:
        if module is not None and (module.startswith('pyvolt.') and not module.endswith('converter')):
            converter = CONVERTER_MAPPING.get(converter, converter)

    try:
        if isclass(converter) and issubclass(converter, Converter):
            if ismethod(converter.convert):
                return await converter.convert(ctx, argument)
            else:
                return await converter().convert(ctx, argument)
        elif isinstance(converter, Converter):
            return await converter.convert(ctx, argument)  # type: ignore
    except CommandError:
        raise
    except Exception as exc:
        raise ConversionError(converter, exc) from exc  # type: ignore

    try:
        return converter(argument)  # type: ignore
    except CommandError:
        raise
    except Exception as exc:
        try:
            name = converter.__name__
        except AttributeError:
            name = converter.__class__.__name__

        raise BadArgument(f'Converting to "{name}" failed for parameter "{param.name}".') from exc


@typing.overload
async def run_converters(
    ctx: Context[BotT], converter: typing.Union[type[Converter[T]], Converter[T]], argument: str, param: Parameter, /
) -> T: ...


@typing.overload
async def run_converters(
    ctx: Context[BotT], converter: typing.Any, argument: str, param: Parameter, /
) -> typing.Any: ...


async def run_converters(ctx: Context[BotT], converter: typing.Any, argument: str, param: Parameter, /) -> typing.Any:
    """|coro|

    Runs converters for a given converter, argument, and parameter.

    This function does the same work that the library does under the hood.

    Parameters
    ------------
    ctx: :class:`Context`
        The invocation context to run the converters under.
    converter: Any
        The converter to run, this corresponds to the annotation in the function.
    argument: :class:`str`
        The argument to convert to.
    param: :class:`Parameter`
        The parameter being converted. This is mainly for error reporting.

    Raises
    -------
    :class:`CommandError`
        The converter failed to convert.

    Returns
    --------
    Any
        The resulting conversion.
    """
    origin = getattr(converter, '__origin__', None)

    if origin is typing.Union:
        errors = []
        _NoneType = type(None)
        union_args = converter.__args__
        for conv in union_args:
            # if we got to this part in the code, then the previous conversions have failed
            # so we should just undo the view, return the default, and allow parsing to continue
            # with the other parameters
            if conv is _NoneType and param.kind != param.VAR_POSITIONAL:
                ctx.view.undo()
                return None if param.required else await param.get_default(ctx)

            try:
                value = await run_converters(ctx, conv, argument, param)
            except CommandError as exc:
                errors.append(exc)
            else:
                return value

        # if we're here, then we failed all the converters
        raise BadUnionArgument(param=param, converters=union_args, errors=errors)

    if origin is typing.Literal:
        errors = []
        conversions = {}
        literal_args = converter.__args__
        for literal in literal_args:
            literal_type = type(literal)
            try:
                value = conversions[literal_type]
            except KeyError:
                try:
                    value = await _actual_conversion(ctx, literal_type, argument, param)
                except CommandError as exc:
                    errors.append(exc)
                    conversions[literal_type] = object()
                    continue
                else:
                    conversions[literal_type] = value

            if value == literal:
                return value

        # if we're here, then we failed to match all the literals
        raise BadLiteralArgument(param=param, literals=literal_args, errors=errors, argument=argument)

    # This must be the last if-clause in the chain of origin checking
    # Nearly every type is a generic type within the typing library
    # So care must be taken to make sure a more specialised origin handle
    # isn't overwritten by the widest if clause
    if origin is not None and is_generic_type(converter):
        converter = origin

    return await _actual_conversion(ctx, converter, argument, param)


__all__ = (
    'Converter',
    'RE_ID',
    'RE_MENTION_ANY',
    'RE_MENTION_CHANNEL',
    'RE_MENTION_ROLE',
    'RE_MENTION_USER',
    'RE_ID_PAIR',
    'RE_CHANNEL_LINK',
    'RE_MESSAGE_LINK',
    'RE_EMOJI',
    'IDConverter',
    'BaseConverter',
    'MemberConverter',
    'UserConverter',
    'ServerConverter',
    'BaseMessageConverter',
    'MessageConverter',
    'CategoryConverter',
    'RoleConverter',
    'InviteConverter',
    'EmojiConverter',
    'Greedy',
    '_convert_to_bool',
    '_GenericAlias',
    'is_generic_type',
    'CONVERTER_MAPPING',
    '_actual_conversion',
    'run_converters',
)
