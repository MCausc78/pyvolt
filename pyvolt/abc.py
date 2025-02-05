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
        cache = self.state.cache
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
        channel_id = await self.fetch_channel_id()
        return await self.state.shard.begin_typing(channel_id)

    async def end_typing(self) -> None:
        """Ends typing in channel."""
        channel_id = await self.fetch_channel_id()
        await self.state.shard.end_typing(channel_id)

    async def search(
        self,
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
        query: Optional[:class:`str`]
            Full-text search query. See `MongoDB documentation <https://docs.mongodb.com/manual/text-search/#-text-operator>`_ for more information.
        pinned: Optional[:class:`bool`]
            Whether to search for (un-)pinned messages or not.
        limit: Optional[:class:`int`]
            Maximum number of messages to fetch.
        before: Optional[ULIDOr[:class:`BaseMessage`]]
            The message before which messages should be fetched.
        after: Optional[ULIDOr[:class:`BaseMessage`]]
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

        channel_id = await self.fetch_channel_id()

        return await self.state.http.search_for_messages(
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
        content: str | None = None,
        *,
        nonce: str | None = None,
        attachments: list[ResolvableResource] | None = None,
        replies: list[Reply | ULIDOr[BaseMessage]] | None = None,
        embeds: list[SendableEmbed] | None = None,
        masquerade: Masquerade | None = None,
        interactions: MessageInteractions | None = None,
        silent: bool | None = None,
    ) -> Message:
        """|coro|

        Sends a message to the given channel.
        You must have `SendMessages` permission.

        Parameters
        ----------
        content: Optional[:class:`str`]
            The message content.
        nonce: Optional[:class:`str`]
            The message nonce.
        attachments: Optional[List[:class:`ResolvableResource`]]
            The message attachments.
        replies: Optional[List[Union[:class:`Reply`, ULIDOr[:class:`BaseMessage`]]]]
            The message replies.
        embeds: Optional[List[:class:`SendableEmbed`]]
            The message embeds.
        masquearde: Optional[:class:`Masquerade`]
            The message masquerade.
        interactions: Optional[:class:`MessageInteractions`]
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

        channel_id = await self.fetch_channel_id()

        return await self.state.http.send_message(
            channel_id,
            content,
            nonce=nonce,
            attachments=attachments,
            replies=replies,
            embeds=embeds,
            masquerade=masquerade,
            interactions=interactions,
            silent=silent,
        )

    def typing(self) -> Typing:
        """:class:`Typing`: Returns an asynchronous context manager that allows you to send a typing indicator in channel for an indefinite period of time."""

        return Typing(
            destination=self,
            shard=self.state.shard,
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
