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

import typing

from .context_managers import Typing

if typing.TYPE_CHECKING:
    from collections.abc import Mapping
    from livekit.rtc import Room  # type: ignore

    from . import cache as caching
    from .cdn import ResolvableResource
    from .core import ULIDOr
    from .enums import MessageSort
    from .message import Reply, MessageInteractions, Masquerade, SendableEmbed, BaseMessage, Message
    from .state import State


class Messageable:
    __slots__ = ()

    state: State

    def _get_state(self) -> State:
        return self.state

    async def fetch_channel_id(self) -> str:
        """:class:`str`: Retrieves the channel's ID."""
        return self.get_channel_id()

    def get_channel_id(self) -> str:
        """:class:`str`: Retrieves the channel's ID, if possible."""
        return ''

    def get_message(self, message_id: str, /) -> Message | None:
        """Retrieves a channel message from cache.

        Parameters
        ----------
        message_id: :class:`str`
            The message ID.

        Returns
        -------
        Optional[:class:`Message`]
            The message or ``None`` if not found.
        """
        state = self._get_state()
        cache = state.cache
        if not cache:
            return
        return cache.get_message(self.get_channel_id(), message_id, caching._USER_REQUEST)

    @property
    def messages(self) -> Mapping[str, Message]:
        """Mapping[:class:`str`, :class:`Message`]: Returns all messages in this channel."""
        cache = self.state.cache
        if cache:
            return cache.get_messages_mapping_of(self.get_channel_id(), caching._USER_REQUEST) or {}
        return {}

    async def begin_typing(self) -> None:
        """Begins typing in channel, until :meth:`end_typing` is called."""
        state = self._get_state()
        channel_id = await self.fetch_channel_id()
        return await state.shard.begin_typing(channel_id)

    async def end_typing(self) -> None:
        """Ends typing in channel."""
        state = self._get_state()
        channel_id = await self.fetch_channel_id()
        await state.shard.end_typing(channel_id)

    async def search(
        self,
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

        Searches for messages in this channel.

        For ``query`` and ``pinned``, only one parameter can be provided, otherwise a :class:`HTTPException` will
        be thrown with ``InvalidOperation`` type.

        You must have :attr:`~Permissions.read_message_history` to do this.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
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

        state = self._get_state()
        channel_id = await self.fetch_channel_id()

        return await state.http.search_for_messages(
            channel_id,
            query=query,
            pinned=pinned,
            limit=limit,
            before=before,
            after=after,
            sort=sort,
            populate_users=populate_users,
        )

    async def send(
        self,
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

        Sends a message to this channel.

        You must have :attr:`~Permissions.send_messages` to do this.

        If message mentions '@everyone' or '@here', you must have :attr:`~Permissions.mention_everyone` to do that.
        If message mentions any roles, you must :attr:`~Permission.mention_roles` to do that.

        Parameters
        ----------
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

        state = self._get_state()
        channel_id = await self.fetch_channel_id()

        return await state.http.send_message(
            channel_id,
            content,
            nonce=nonce,
            attachments=attachments,
            replies=replies,
            embeds=embeds,
            masquerade=masquerade,
            interactions=interactions,
            silent=silent,
            mention_everyone=mention_everyone,
            mention_online=mention_online,
        )

    def typing(self) -> Typing:
        """:class:`Typing`: Returns an asynchronous context manager that allows you to send a typing indicator in channel for an indefinite period of time."""

        return Typing(
            destination=self,
            shard=self._get_state().shard,
        )


class Connectable:
    __slots__ = ()

    state: State

    async def fetch_channel_id(self) -> str:
        """:class:`str`: Retrieves the channel's ID."""
        return self.get_channel_id()

    def get_channel_id(self) -> str:
        """:class:`str`: Retrieves the channel's ID, if possible."""
        return ''

    async def connect(self) -> Room:
        """:class:`Room`: Connects to a voice channel."""

        try:
            from livekit.rtc import Room  # type: ignore
        except ImportError:
            raise TypeError('Livekit is unavailable') from None
        else:
            channel_id = await self.fetch_channel_id()

            state = self.state

            room = Room()

            url = state.voice_url
            if not url:
                instance = await state.http.query_node()
                url = instance.features.voice.url
                state.voice_url = url

            token = await state.http.join_call(channel_id)

            await room.connect(url, token)
            return room


__all__ = (
    'Messageable',
    'Connectable',
)
