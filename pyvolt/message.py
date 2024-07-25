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
from attrs import define, field
from datetime import datetime
from enum import IntFlag
import typing


from . import cache as caching, cdn
from .base import Base
from .channel import TextChannel, ServerChannel
from .core import (
    UNDEFINED,
    UndefinedOr,
    ULIDOr,
    resolve_id,
    ZID,
)
from .embed import StatelessEmbed, Embed
from .emoji import ResolvableEmoji
from .enums import Enum
from .errors import NoData
from .safety_reports import ContentReportReason
from .server import Member
from .user import BaseUser, User

if typing.TYPE_CHECKING:
    from . import raw
    from .state import State


class Reply:
    id: str
    """The message ID reply to."""

    mention: bool
    """Whether to mention author of that message."""

    __slots__ = ('id', 'mention')

    def __init__(self, id: ULIDOr[BaseMessage], mention: bool = False) -> None:
        self.id = resolve_id(id)
        self.mention = mention

    def build(self) -> raw.ReplyIntent:
        return {
            'id': self.id,
            'mention': self.mention,
        }


class Interactions:
    """Information to guide interactions on this message."""

    reactions: list[str]
    """Reactions which should always appear and be distinct."""

    restrict_reactions: bool
    """Whether reactions should be restricted to the given list. Can only be set to `True` if `reactions` list is of at least length 1. Defaults to `False`."""

    __slots__ = ('reactions', 'restrict_reactions')

    def __init__(self, reactions: list[str], restrict_reactions: bool = False) -> None:
        self.reactions = reactions
        self.restrict_reactions = restrict_reactions

    def build(self) -> raw.Interactions:
        return {
            'reactions': self.reactions,
            'restrict_reactions': self.restrict_reactions,
        }


class Masquerade:
    """Name and / or avatar override information.

    Parameters
    ----------
    name: Optional[:class:`str`]
        Replace the display name shown on this message.
    avatar: Optional[:class:`str`]
        Replace the avatar shown on this message (URL to image file).
    colour: Optional[:class:`str`]
        Replace the display role colour shown on this message. Can be any valid CSS colour.
        Must have `ManageRole` permission to use.
    """

    __slots__ = ('name', 'avatar', 'colour')

    def __init__(
        self,
        name: str | None = None,
        avatar: str | None = None,
        *,
        colour: str | None = None,
    ) -> None:
        self.name = name
        self.avatar = avatar
        self.colour = colour

    def build(self) -> raw.Masquerade:
        j: raw.Masquerade = {}
        if self.name is not None:
            j['name'] = self.name
        if self.avatar is not None:
            j['avatar'] = self.avatar
        if self.colour is not None:
            j['colour'] = self.colour
        return j


class SendableEmbed:
    """Representation of a text embed before it is sent.

    Parameters
    ----------
    icon_url: Optional[:class:`str`]
        The embed icon URL.
    url: Optional[:class:`str`]
        The embed URL.
    title: Optional[:class:`str`]
        The title of the embed.
    description: Optional[:class:`str`]
        The description of the embed.
    media: Optional[:class:`cdn.ResolvableResource`]
        The file inside the embed, this is the ID of the file.
    colour: Optional[:class:`str`]
        The embed color. This can be any valid [CSS color](https://developer.mozilla.org/en-US/docs/Web/CSS/color_value).

    """

    icon_url: str | None
    url: str | None
    title: str | None
    description: str | None
    media: cdn.ResolvableResource | None
    colour: str | None

    __slots__ = ('icon_url', 'url', 'title', 'description', 'media', 'colour')

    def __init__(
        self,
        icon_url: str | None = None,
        url: str | None = None,
        title: str | None = None,
        description: str | None = None,
        media: cdn.ResolvableResource | None = None,
        colour: str | None = None,
    ) -> None:
        self.icon_url = icon_url
        self.url = url
        self.title = title
        self.description = description
        self.media = media
        self.colour = colour

    async def build(self, state: State) -> raw.SendableEmbed:
        j: raw.SendableEmbed = {}
        if self.icon_url is not None:
            j['icon_url'] = self.icon_url
        if self.url is not None:
            j['url'] = self.url
        if self.title is not None:
            j['title'] = self.title
        if self.description is not None:
            j['description'] = self.description
        if self.media is not None:
            j['media'] = await cdn.resolve_resource(state, self.media, tag='attachments')
        if self.colour is not None:
            j['colour'] = self.colour
        return j


class MessageSort(Enum):
    relevance = 'Relevance'
    latest = 'Latest'
    oldest = 'Oldest'


@define(slots=True)
class MessageWebhook:
    """Information about the webhook bundled with Message."""

    name: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The name of the webhook - 1 to 32 chars."""

    avatar: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The ID of the avatar of the webhook, if it has one."""


@define(slots=True)
class BaseMessage(Base):
    """Base representation of message in channel on Revolt."""

    channel_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """ID of the channel this message was sent in."""

    @property
    def channel(self) -> TextChannel:
        """The channel this message was sent in."""

        cache = self.state.cache
        if not cache:
            return TextChannel(state=self.state, id=self.channel_id)
        channel = cache.get_channel(self.channel_id, caching._USER_REQUEST)
        if channel:
            assert isinstance(channel, TextChannel), 'Cache returned non textable channel'
            return channel
        return TextChannel(state=self.state, id=self.channel_id)

    async def acknowledge(self) -> None:
        """|coro|

        Lets the server and all other clients know that we've seen this message in this channel.

        Raises
        ------
        Forbidden
            You do not have permissions to see that message.
        HTTPException
            Acknowledging message failed.
        """
        return await self.state.http.acknowledge_message(self.channel_id, self.id)

    async def ack(self) -> None:
        """|coro|

        Alias to :meth:`BaseMessage.acknowledge`.

        Raises
        ------
        Forbidden
            You do not have permissions to see that message.
        HTTPException
            Acknowledging message failed.
        """
        return await self.acknowledge()

    async def delete(self) -> None:
        """|coro|

        Delete a message you've sent or one you have permission to delete.

        Raises
        ------
        Forbidden
            You do not have permissions to delete message.
        HTTPException
            Deleting the message failed.
        """
        return await self.state.http.delete_message(self.channel_id, self.id)

    async def edit(
        self,
        *,
        content: UndefinedOr[str] = UNDEFINED,
        embeds: UndefinedOr[list[SendableEmbed]] = UNDEFINED,
    ) -> Message:
        """|coro|

        Edits the message that you've previously sent.

        Parameters
        ----------
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
        return await self.state.http.edit_message(self.channel_id, self.id, content=content, embeds=embeds)

    async def pin(self) -> None:
        """|coro|

        Pins a message.
        You must have `ManageMessages` permission.

        Raises
        ------
        Forbidden
            You do not have permissions to pin messages.
        HTTPException
            Pinning the message failed.
        """
        return await self.state.http.pin_message(self.channel_id, self.id)

    async def react(
        self,
        emoji: ResolvableEmoji,
    ) -> None:
        """|coro|

        Reacts to the message with given emoji.

        Parameters
        ----------
        emoji: :class:`emojis.ResolvableEmoji`
            The emoji to react with.

        Raises
        ------
        Forbidden
            You do not have permissions to react to message.
        HTTPException
            Reacting to message failed.
        """
        return await self.state.http.add_reaction_to_message(self.channel_id, self.id, emoji)

    async def reply(
        self,
        content: str | None = None,
        *,
        idempotency_key: str | None = None,
        attachments: list[cdn.ResolvableResource] | None = None,
        mention: bool = True,
        embeds: list[SendableEmbed] | None = None,
        masquerade: Masquerade | None = None,
        interactions: Interactions | None = None,
        silent: bool | None = None,
    ) -> Message:
        """|coro|

        Replies to this message.
        You must have `SendMessages` permission.

        Returns
        -------
        :class:`Message`
            The message sent.

        Raises
        ------
        Forbidden
            You do not have permissions to send messages.
        HTTPException
            Sending the message failed.
        """
        return await self.state.http.send_message(
            self.channel_id,
            content,
            nonce=idempotency_key,
            attachments=attachments,
            replies=[Reply(id=self.id, mention=mention)],
            embeds=embeds,
            masquerade=masquerade,
            interactions=interactions,
            silent=silent,
        )

    async def report(
        self,
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
        return await self.state.http.report_message(self.id, reason, additional_context=additional_context)

    async def unpin(self) -> None:
        """|coro|

        Unpins a message.
        You must have `ManageMessages` permission.

        Raises
        ------
        Forbidden
            You do not have permissions to unpin messages.
        HTTPException
            Unpinning the message failed.
        """
        return await self.state.http.unpin_message(self.channel_id, self.id)

    async def unreact(
        self,
        emoji: ResolvableEmoji,
        *,
        user: ULIDOr[BaseUser] | None = None,
        remove_all: bool | None = None,
    ) -> None:
        """|coro|

        Remove your own, someone else's or all of a given reaction.
        Requires `ManageMessages` permission if changing other's reactions.

        Parameters
        ----------
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
        return await self.state.http.remove_reactions_from_message(
            self.channel_id, self.id, emoji, user=user, remove_all=remove_all
        )


@define(slots=True)
class PartialMessage(BaseMessage):
    """Partial representation of message in channel on Revolt."""

    content: UndefinedOr[str] = field(repr=True, hash=True, kw_only=True, eq=True)
    """New message content."""

    edited_at: UndefinedOr[datetime] = field(repr=True, hash=True, kw_only=True, eq=True)
    """When message was edited."""

    internal_embeds: UndefinedOr[list[StatelessEmbed]] = field(repr=True, hash=True, kw_only=True, eq=True)
    """New message embeds."""

    pinned: UndefinedOr[bool] = field(repr=True, hash=True, kw_only=True, eq=True)
    """Whether the message was just pinned."""

    reactions: UndefinedOr[dict[str, tuple[str, ...]]] = field(repr=True, hash=True, kw_only=True, eq=True)
    """New message reactions."""

    @property
    def embeds(self) -> UndefinedOr[list[Embed]]:
        """:class:`UndefinedOr`[List[:class:`Embed`]]: New message embeds."""
        return (
            [e._stateful(self.state) for e in self.internal_embeds]
            if self.internal_embeds is not UNDEFINED
            else UNDEFINED
        )


@define(slots=True)
class MessageAppendData(BaseMessage):
    """Appended data to message in channel on Revolt."""

    internal_embeds: UndefinedOr[list[StatelessEmbed]] = field(repr=True, hash=True, kw_only=True, eq=True)
    """New message appended stateless embeds."""

    @property
    def embeds(self) -> UndefinedOr[list[Embed]]:
        """New message appended embeds."""
        return (
            [e._stateful(self.state) for e in self.internal_embeds]
            if self.internal_embeds is not UNDEFINED
            else UNDEFINED
        )


class BaseSystemEvent(abc.ABC):
    """Representation of system event within message."""


@define(slots=True)
class TextSystemEvent(BaseSystemEvent):
    content: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The event contents."""

    def _stateful(self, message: Message) -> TextSystemEvent:
        return self


@define(slots=True)
class StatelessUserAddedSystemEvent(BaseSystemEvent):
    _user: User | Member | str = field(repr=False, hash=True, kw_only=True, eq=True, alias='internal_user')

    @property
    def user_id(self) -> str:
        """:class:`str`: The ID of the user that was added."""
        if isinstance(self._user, (User, Member)):
            return self._user.id
        return self._user

    def get_user(self) -> User | Member | None:
        """Optional[Union[:class:`User`, :class:`Member`]]: Tries to get user that was added."""
        if isinstance(self._user, (User, Member)):
            return self._user

    _by: User | Member | str = field(repr=False, hash=True, kw_only=True, eq=True, alias='internal_by')

    @property
    def by_id(self) -> str:
        """:class:`str`: The ID of the user that added this user."""
        if isinstance(self._by, (User, Member)):
            return self._by.id
        return self._by

    def get_by(self) -> User | Member | None:
        """Optional[Union[:class:`User`, :class:`Member`]]: Tries to get user that added this user."""
        if isinstance(self._by, (User, Member)):
            return self._by

    def _stateful(self, message: Message) -> UserAddedSystemEvent:
        return UserAddedSystemEvent(
            message=message,
            internal_user=self._user,
            internal_by=self._by,
        )


@define(slots=True)
class UserAddedSystemEvent(StatelessUserAddedSystemEvent):
    message: Message = field(repr=False, hash=False, kw_only=True, eq=False)
    """The message that holds this system event."""

    def get_user(self) -> User | Member | None:
        """Optional[Union[:class:`User`, :class:`Member`]]: Tries to get user that was added."""
        if isinstance(self._user, (User, Member)):
            return self._user
        state = self.message.state
        if not state.cache:
            return
        channel = self.message.channel
        if not isinstance(channel, ServerChannel):
            return state.cache.get_user(
                self._user,
                caching._UNDEFINED,
            )
        return state.cache.get_server_member(
            channel.server_id,
            self._user,
            caching._UNDEFINED,
        )

    @property
    def user(self) -> User | Member:
        """Union[:class:`User`, class:`Member`]: The user that was added."""
        user = self.get_user()
        if not user:
            raise NoData(self.user_id, 'added user')
        return user

    def get_by(self) -> User | Member | None:
        """Optional[Union[:class:`User`, :class:`Member`]]: Tries to get user that added this user."""
        if isinstance(self._by, (User, Member)):
            return self._by
        state = self.message.state
        if not state.cache:
            return
        channel = self.message.channel
        if not isinstance(channel, ServerChannel):
            return state.cache.get_user(
                self._by,
                caching._UNDEFINED,
            )
        return state.cache.get_server_member(
            channel.server_id,
            self._by,
            caching._UNDEFINED,
        )

    @property
    def by(self) -> User | Member:
        """Union[:class:`User`, class:`Member`]: The user that added this user."""
        user = self.get_user()
        if not user:
            raise NoData(self.user_id, 'added user')
        return user


@define(slots=True)
class StatelessUserRemovedSystemEvent(BaseSystemEvent):
    _user: User | Member | str = field(repr=False, hash=True, kw_only=True, eq=True, alias='internal_user')

    @property
    def user_id(self) -> str:
        """:class:`str`: The ID of the user that was removed."""
        if isinstance(self._user, (User, Member)):
            return self._user.id
        return self._user

    def get_user(self) -> User | Member | None:
        """Optional[Union[:class:`User`, :class:`Member`]]: Tries to get user that was removed."""
        if isinstance(self._user, (User, Member)):
            return self._user

    _by: User | Member | str = field(repr=False, hash=True, kw_only=True, eq=True, alias='internal_by')

    @property
    def by_id(self) -> str:
        """:class:`str`: The ID of the user that removed this user."""
        if isinstance(self._by, (User, Member)):
            return self._by.id
        return self._by

    def get_by(self) -> User | Member | None:
        """Optional[Union[:class:`User`, :class:`Member`]]: Tries to get user that removed this user."""
        if isinstance(self._by, (User, Member)):
            return self._by

    def _stateful(self, message: Message) -> UserRemovedSystemEvent:
        return UserRemovedSystemEvent(
            message=message,
            internal_user=self._user,
            internal_by=self._by,
        )


@define(slots=True)
class UserRemovedSystemEvent(StatelessUserRemovedSystemEvent):
    message: Message = field(repr=False, hash=False, kw_only=True, eq=False)
    """The message that holds this system event."""

    def get_user(self) -> User | Member | None:
        """Optional[Union[:class:`User`, :class:`Member`]]: Tries to get user that was removed."""
        if isinstance(self._user, (User, Member)):
            return self._user
        state = self.message.state
        if not state.cache:
            return
        channel = self.message.channel
        if not isinstance(channel, ServerChannel):
            return state.cache.get_user(
                self._user,
                caching._UNDEFINED,
            )
        return state.cache.get_server_member(
            channel.server_id,
            self._user,
            caching._UNDEFINED,
        )

    @property
    def user(self) -> User | Member:
        """Union[:class:`User`, class:`Member`]: The user that was removed."""
        user = self.get_user()
        if not user:
            raise NoData(self.user_id, 'removed user')
        return user

    def get_by(self) -> User | Member | None:
        """Optional[Union[:class:`User`, :class:`Member`]]: Tries to get user that removed this user."""
        if isinstance(self._by, (User, Member)):
            return self._by
        state = self.message.state
        if not state.cache:
            return
        channel = self.message.channel
        if not isinstance(channel, ServerChannel):
            return state.cache.get_user(
                self._by,
                caching._UNDEFINED,
            )
        return state.cache.get_server_member(
            channel.server_id,
            self._by,
            caching._UNDEFINED,
        )

    @property
    def by(self) -> User | Member:
        """Union[:class:`User`, class:`Member`]: The user that removed this user."""
        user = self.get_user()
        if not user:
            raise NoData(self.user_id, 'remover')
        return user


@define(slots=True)
class StatelessUserJoinedSystemEvent(BaseSystemEvent):
    _user: User | Member | str = field(repr=False, hash=True, kw_only=True, eq=True, alias='internal_user')

    @property
    def user_id(self) -> str:
        """:class:`str`: The ID of the user that joined this server/group."""
        if isinstance(self._user, (User, Member)):
            return self._user.id
        return self._user

    def get_user(self) -> User | Member | None:
        """Optional[Union[:class:`User`, :class:`Member`]]: Tries to get user that joined this server/group."""
        if isinstance(self._user, (User, Member)):
            return self._user

    def _stateful(self, message: Message) -> UserJoinedSystemEvent:
        return UserJoinedSystemEvent(
            message=message,
            internal_user=self._user,
        )


@define(slots=True)
class UserJoinedSystemEvent(StatelessUserJoinedSystemEvent):
    message: Message = field(repr=False, hash=False, kw_only=True, eq=False)
    """The message that holds this system event."""

    def get_user(self) -> User | Member | None:
        """Optional[Union[:class:`User`, :class:`Member`]]: Tries to get user that was added."""
        if isinstance(self._user, (User, Member)):
            return self._user
        state = self.message.state
        if not state.cache:
            return
        channel = self.message.channel
        if not isinstance(channel, ServerChannel):
            return state.cache.get_user(
                self._user,
                caching._UNDEFINED,
            )
        return state.cache.get_server_member(
            channel.server_id,
            self._user,
            caching._UNDEFINED,
        )

    @property
    def user(self) -> User | Member:
        """Union[:class:`User`, class:`Member`]: The user that joined this server/group.."""
        user = self.get_user()
        if not user:
            raise NoData(self.user_id, 'joined user')
        return user


@define(slots=True)
class StatelessUserLeftSystemEvent(BaseSystemEvent):
    _user: User | Member | str = field(repr=False, hash=True, kw_only=True, eq=True, alias='internal_user')

    @property
    def user_id(self) -> str:
        """:class:`str`: The ID of the user that left this server/group."""
        if isinstance(self._user, (User, Member)):
            return self._user.id
        return self._user

    def get_user(self) -> User | Member | None:
        """Optional[Union[:class:`User`, :class:`Member`]]: Tries to get user that left this server/group."""
        if isinstance(self._user, (User, Member)):
            return self._user

    def _stateful(self, message: Message) -> UserLeftSystemEvent:
        return UserLeftSystemEvent(
            message=message,
            internal_user=self._user,
        )


@define(slots=True)
class UserLeftSystemEvent(StatelessUserLeftSystemEvent):
    message: Message = field(repr=False, hash=False, kw_only=True, eq=False)
    """The message that holds this system event."""

    def get_user(self) -> User | Member | None:
        """Optional[Union[:class:`User`, :class:`Member`]]: Tries to get user that left this server/group."""
        if isinstance(self._user, (User, Member)):
            return self._user
        state = self.message.state
        if not state.cache:
            return
        channel = self.message.channel
        if not isinstance(channel, ServerChannel):
            return state.cache.get_user(
                self._user,
                caching._UNDEFINED,
            )
        return state.cache.get_server_member(
            channel.server_id,
            self._user,
            caching._UNDEFINED,
        )

    @property
    def user(self) -> User | Member:
        """Union[:class:`User`, class:`Member`]: The user that left this server/group.."""
        user = self.get_user()
        if not user:
            raise NoData(self.user_id, 'left user')
        return user


@define(slots=True)
class StatelessUserKickedSystemEvent(BaseSystemEvent):
    _user: User | Member | str = field(repr=False, hash=True, kw_only=True, eq=True, alias='internal_user')

    @property
    def user_id(self) -> str:
        """:class:`str`: The ID of the user that was kicked from this server."""
        if isinstance(self._user, (User, Member)):
            return self._user.id
        return self._user

    def get_user(self) -> User | Member | None:
        """Optional[Union[:class:`User`, :class:`Member`]]: Tries to get user that was kicked from this server."""
        if isinstance(self._user, (User, Member)):
            return self._user

    def _stateful(self, message: Message) -> UserKickedSystemEvent:
        return UserKickedSystemEvent(
            message=message,
            internal_user=self._user,
        )


@define(slots=True)
class UserKickedSystemEvent(StatelessUserKickedSystemEvent):
    message: Message = field(repr=False, hash=False, kw_only=True, eq=False)
    """The message that holds this system event."""

    def get_user(self) -> User | Member | None:
        """Optional[Union[:class:`User`, :class:`Member`]]: Tries to get user that was kicked from this server."""
        if isinstance(self._user, (User, Member)):
            return self._user
        state = self.message.state
        if not state.cache:
            return
        channel = self.message.channel
        if not isinstance(channel, ServerChannel):
            return state.cache.get_user(
                self._user,
                caching._UNDEFINED,
            )
        return state.cache.get_server_member(
            channel.server_id,
            self._user,
            caching._UNDEFINED,
        )

    @property
    def user(self) -> User | Member:
        """Union[:class:`User`, class:`Member`]: The user that was kicked from this server."""
        user = self.get_user()
        if not user:
            raise NoData(self.user_id, 'kicked user')
        return user


@define(slots=True)
class StatelessUserBannedSystemEvent(BaseSystemEvent):
    _user: User | Member | str = field(repr=False, hash=True, kw_only=True, eq=True, alias='internal_user')

    @property
    def user_id(self) -> str:
        """:class:`str`: The ID of the user that was banned from this server."""
        if isinstance(self._user, (User, Member)):
            return self._user.id
        return self._user

    def get_user(self) -> User | Member | None:
        """Optional[Union[:class:`User`, :class:`Member`]]: Tries to get user that was banned from this server."""
        if isinstance(self._user, (User, Member)):
            return self._user

    def _stateful(self, message: Message) -> UserBannedSystemEvent:
        return UserBannedSystemEvent(
            message=message,
            internal_user=self._user,
        )


@define(slots=True)
class UserBannedSystemEvent(StatelessUserBannedSystemEvent):
    message: Message = field(repr=False, hash=False, kw_only=True, eq=False)
    """The message that holds this system event."""

    def get_user(self) -> User | Member | None:
        """Optional[Union[:class:`User`, :class:`Member`]]: Tries to get user that was banned from this server."""
        if isinstance(self._user, (User, Member)):
            return self._user
        state = self.message.state
        if not state.cache:
            return
        channel = self.message.channel
        if not isinstance(channel, ServerChannel):
            return state.cache.get_user(
                self._user,
                caching._UNDEFINED,
            )
        return state.cache.get_server_member(
            channel.server_id,
            self._user,
            caching._UNDEFINED,
        )

    @property
    def user(self) -> User | Member:
        """Union[:class:`User`, class:`Member`]: The user that was banned from this server."""
        user = self.get_user()
        if not user:
            raise NoData(self.user_id, 'banned user')
        return user


@define(slots=True)
class StatelessChannelRenamedSystemEvent(BaseSystemEvent):
    name: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The new name of this group."""

    _by: User | str = field(repr=False, hash=True, kw_only=True, eq=True, alias='internal_by')

    @property
    def by_id(self) -> str:
        """:class:`str`: The ID of the user that renamed this group."""
        if isinstance(self._by, User):
            return self._by.id
        return self._by

    def get_by(self) -> User | None:
        """Optional[:class:`User`]: Tries to get user that renamed this group."""
        if isinstance(self._by, User):
            return self._by

    def _stateful(self, message: Message) -> ChannelRenamedSystemEvent:
        return ChannelRenamedSystemEvent(
            message=message,
            name=self.name,
            internal_by=self._by,
        )


@define(slots=True)
class ChannelRenamedSystemEvent(StatelessChannelRenamedSystemEvent):
    message: Message = field(repr=False, hash=False, kw_only=True, eq=False)
    """The message that holds this system event."""

    def get_by(self) -> User | None:
        """Optional[:class:`User`: Tries to get user that renamed this group."""
        if isinstance(self._by, User):
            return self._by
        state = self.message.state
        if not state.cache:
            return
        return state.cache.get_user(
            self._by,
            caching._UNDEFINED,
        )

    @property
    def by(self) -> User:
        """Union[:class:`User`]: The user that renamed this group."""
        by = self.get_by()
        if not by:
            raise NoData(self.by_id, 'user')
        return by


@define(slots=True)
class StatelessChannelDescriptionChangedSystemEvent(BaseSystemEvent):
    _by: User | str = field(repr=False, hash=True, kw_only=True, eq=True, alias='internal_by')

    @property
    def by_id(self) -> str:
        """:class:`str`: The ID of the user that changed description of this group."""
        if isinstance(self._by, User):
            return self._by.id
        return self._by

    def get_by(self) -> User | None:
        """Optional[:class:`User`]: Tries to get user that changed description of this group."""
        if isinstance(self._by, User):
            return self._by

    def _stateful(self, message: Message) -> ChannelDescriptionChangedSystemEvent:
        return ChannelDescriptionChangedSystemEvent(
            message=message,
            internal_by=self._by,
        )


@define(slots=True)
class ChannelDescriptionChangedSystemEvent(StatelessChannelDescriptionChangedSystemEvent):
    message: Message = field(repr=False, hash=False, kw_only=True, eq=False)
    """The message that holds this system event."""

    def get_by(self) -> User | None:
        """Optional[:class:`User`]: Tries to get user that changed description of this group."""
        if isinstance(self._by, User):
            return self._by
        state = self.message.state
        if not state.cache:
            return
        return state.cache.get_user(
            self._by,
            caching._UNDEFINED,
        )

    @property
    def by(self) -> User:
        """:class:`User`: The user that changed description of this group."""
        by = self.get_by()
        if not by:
            raise NoData(self.by_id, 'user')
        return by


@define(slots=True)
class StatelessChannelIconChangedSystemEvent(BaseSystemEvent):
    _by: User | str = field(repr=False, hash=True, kw_only=True, eq=True, alias='internal_by')

    @property
    def by_id(self) -> str:
        """:class:`str`: The ID of the user that changed icon of this group."""
        if isinstance(self._by, User):
            return self._by.id
        return self._by

    def get_by(self) -> User | None:
        """Optional[:class:`User`]: Tries to get user that changed icon of this group."""
        if isinstance(self._by, User):
            return self._by

    def _stateful(self, message: Message) -> ChannelIconChangedSystemEvent:
        return ChannelIconChangedSystemEvent(
            message=message,
            internal_by=self._by,
        )


@define(slots=True)
class ChannelIconChangedSystemEvent(StatelessChannelIconChangedSystemEvent):
    message: Message = field(repr=False, hash=False, kw_only=True, eq=False)
    """The message that holds this system event."""

    def get_by(self) -> User | None:
        """Optional[:class:`User`]: Tries to get user that changed icon of this group."""
        if isinstance(self._by, User):
            return self._by
        state = self.message.state
        if not state.cache:
            return
        return state.cache.get_user(
            self._by,
            caching._UNDEFINED,
        )

    @property
    def by(self) -> User:
        """:class:`User`: The user that changed icon of this group."""
        by = self.get_by()
        if not by:
            raise NoData(self.by_id, 'user')
        return by


@define(slots=True)
class StatelessChannelOwnershipChangedSystemEvent(BaseSystemEvent):
    _from: User | str = field(repr=False, hash=True, kw_only=True, eq=True, alias='internal_from')
    _to: User | str = field(repr=False, hash=True, kw_only=True, eq=True, alias='internal_to')

    @property
    def from_id(self) -> str:
        """:class:`str`: The ID of the user that was previous owner of this group."""
        if isinstance(self._from, User):
            return self._from.id
        return self._from

    def get_from(self) -> User | None:
        """Optional[:class:`User`]: Tries to get user that was previous owner of this group."""
        if isinstance(self._from, User):
            return self._from

    @property
    def to_id(self) -> str:
        """:class:`str`: The ID of the user that became owner of this group."""
        if isinstance(self._from, User):
            return self._from.id
        return self._from

    def get_to(self) -> User | None:
        """Optional[:class:`User`]: Tries to get user that became owner of this group."""
        if isinstance(self._from, User):
            return self._from

    def _stateful(self, message: Message) -> ChannelOwnershipChangedSystemEvent:
        return ChannelOwnershipChangedSystemEvent(
            message=message,
            internal_from=self._from,
            internal_to=self._to,
        )


@define(slots=True)
class ChannelOwnershipChangedSystemEvent(StatelessChannelOwnershipChangedSystemEvent):
    message: Message = field(repr=False, hash=False, kw_only=True, eq=False)
    """The message that holds this system event."""

    def get_from(self) -> User | None:
        """Optional[:class:`User`]: Tries to get user that was previous owner of this group."""
        if isinstance(self._from, User):
            return self._from
        state = self.message.state
        if not state.cache:
            return
        return state.cache.get_user(
            self._from,
            caching._UNDEFINED,
        )

    @property
    def from_(self) -> User:
        """:class:`User`: The user that was previous owner of this group."""
        from_ = self.get_from()
        if not from_:
            raise NoData(self.from_id, 'user')
        return from_

    def get_to(self) -> User | None:
        """Optional[:class:`User`]: Tries to get user that became owner of this group."""
        if isinstance(self._to, User):
            return self._to
        state = self.message.state
        if not state.cache:
            return
        return state.cache.get_user(
            self._to,
            caching._UNDEFINED,
        )

    @property
    def to(self) -> User:
        """:class:`User`: The user that became owner of this group."""
        to = self.get_from()
        if not to:
            raise NoData(self.to_id, 'user')
        return to


@define(slots=True)
class StatelessMessagePinnedSystemEvent(BaseSystemEvent):
    pinned_message_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The ID of the message that was pinned."""

    _by: User | Member | str = field(repr=False, hash=True, kw_only=True, eq=True, alias='internal_by')

    @property
    def by_id(self) -> str:
        """:class:`str`: The ID of the user that pinned a message."""
        if isinstance(self._by, (User, Member)):
            return self._by.id
        return self._by

    def get_by(self) -> User | Member | None:
        """Optional[Union[:class:`User`, :class:`Member`]]: Tries to get user that pinned a message."""
        if isinstance(self._by, (User, Member)):
            return self._by

    def _stateful(self, message: Message) -> MessagePinnedSystemEvent:
        return MessagePinnedSystemEvent(
            message=message,
            pinned_message_id=self.pinned_message_id,
            internal_by=self._by,
        )


@define(slots=True)
class MessagePinnedSystemEvent(StatelessMessagePinnedSystemEvent):
    message: Message = field(repr=False, hash=False, kw_only=True, eq=False)
    """The message that holds this system event."""

    def get_by(self) -> User | Member | None:
        """Optional[Union[:class:`User`, :class:`Member`]]: Tries to get user that pinned a message."""
        if isinstance(self._by, (User, Member)):
            return self._by
        state = self.message.state
        if not state.cache:
            return
        channel = self.message.channel
        if not isinstance(channel, ServerChannel):
            return state.cache.get_user(
                self._by,
                caching._UNDEFINED,
            )
        return state.cache.get_server_member(
            channel.server_id,
            self._by,
            caching._UNDEFINED,
        )

    @property
    def by(self) -> User | Member:
        """Union[:class:`User`, class:`Member`]: The user that pinned a message."""
        by = self.get_by()
        if not by:
            raise NoData(self.by_id, 'user')
        return by


@define(slots=True)
class StatelessMessageUnpinnedSystemEvent(BaseSystemEvent):
    unpinned_message_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The ID of the message that was unpinned."""

    _by: User | Member | str = field(repr=False, hash=True, kw_only=True, eq=True, alias='internal_by')

    @property
    def by_id(self) -> str:
        """:class:`str`: The ID of the user that unpinned a message."""
        if isinstance(self._by, (User, Member)):
            return self._by.id
        return self._by

    def get_by(self) -> User | Member | None:
        """Optional[Union[:class:`User`, :class:`Member`]]: Tries to get user that unpinned a message."""
        if isinstance(self._by, (User, Member)):
            return self._by

    def _stateful(self, message: Message) -> MessageUnpinnedSystemEvent:
        return MessageUnpinnedSystemEvent(
            message=message,
            unpinned_message_id=self.unpinned_message_id,
            internal_by=self._by,
        )


@define(slots=True)
class MessageUnpinnedSystemEvent(StatelessMessageUnpinnedSystemEvent):
    message: Message = field(repr=False, hash=False, kw_only=True, eq=False)
    """The message that holds this system event."""

    def get_by(self) -> User | Member | None:
        """Optional[Union[:class:`User`, :class:`Member`]]: Tries to get user that unpinned a message."""
        if isinstance(self._by, (User, Member)):
            return self._by
        state = self.message.state
        if not state.cache:
            return
        channel = self.message.channel
        if not isinstance(channel, ServerChannel):
            return state.cache.get_user(
                self._by,
                caching._UNDEFINED,
            )
        return state.cache.get_server_member(
            channel.server_id,
            self._by,
            caching._UNDEFINED,
        )

    @property
    def by(self) -> User | Member:
        """Union[:class:`User`, class:`Member`]: The user that unpinned a message."""
        by = self.get_by()
        if not by:
            raise NoData(self.by_id, 'user')
        return by


StatelessSystemEvent = (
    TextSystemEvent
    | StatelessUserAddedSystemEvent
    | StatelessUserRemovedSystemEvent
    | StatelessUserJoinedSystemEvent
    | StatelessUserLeftSystemEvent
    | StatelessUserKickedSystemEvent
    | StatelessUserBannedSystemEvent
    | StatelessChannelDescriptionChangedSystemEvent
    | StatelessChannelIconChangedSystemEvent
    | StatelessChannelOwnershipChangedSystemEvent
    | StatelessMessagePinnedSystemEvent
    | StatelessMessageUnpinnedSystemEvent
)

SystemEvent = (
    TextSystemEvent
    | UserAddedSystemEvent
    | UserRemovedSystemEvent
    | UserJoinedSystemEvent
    | UserLeftSystemEvent
    | UserKickedSystemEvent
    | UserBannedSystemEvent
    | ChannelDescriptionChangedSystemEvent
    | ChannelIconChangedSystemEvent
    | ChannelOwnershipChangedSystemEvent
    | MessagePinnedSystemEvent
    | MessageUnpinnedSystemEvent
)


class MessageFlags(IntFlag):
    SUPPRESS_NOTIFICATIONS = 1 << 0
    """Whether the message will not send push/desktop notifications."""


@define(slots=True)
class Message(BaseMessage):
    """Representation of message in channel on Revolt."""

    nonce: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """Unique value generated by client sending this message."""

    channel_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """ID of the channel this message was sent in."""

    _author: User | Member | str = field(repr=False, hash=True, kw_only=True, eq=True, alias='internal_author')

    webhook: MessageWebhook | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The webhook that sent this message."""

    content: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The message content."""

    internal_system_event: StatelessSystemEvent | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The stateless system event information, occured in this message, if any."""

    internal_attachments: list[cdn.StatelessAsset] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The stateless attachments on this message."""

    edited_at: datetime | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """Timestamp at which this message was last edited."""

    internal_embeds: list[StatelessEmbed] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The attached stateless embeds to this message."""

    mention_ids: list[str] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The list of user IDs mentioned in this message."""

    replies: list[str] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The list of message ID this message is replying to."""

    reactions: dict[str, tuple[str, ...]] = field(repr=True, hash=True, kw_only=True, eq=True)
    """Mapping of emojis to array of user IDs."""

    interactions: Interactions | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The information about how this message should be interacted with."""

    masquerade: Masquerade | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The name and / or avatar overrides for this message."""

    pinned: bool = field(repr=True, hash=True, kw_only=True, eq=True)
    """Whether this message is pinned."""

    flags: MessageFlags = field(repr=True, hash=True, kw_only=True, eq=True)
    """The message flags."""

    def _append(self, data: MessageAppendData) -> None:
        if data.internal_embeds is not UNDEFINED:
            self.internal_embeds.extend(data.internal_embeds)

    def _update(self, data: PartialMessage) -> None:
        if data.content is not UNDEFINED:
            self.content = data.content
        if data.edited_at is not UNDEFINED:
            self.edited_at = data.edited_at
        if data.internal_embeds is not UNDEFINED:
            self.internal_embeds = data.internal_embeds
        if data.pinned is not UNDEFINED:
            self.pinned = data.pinned
        if data.reactions is not UNDEFINED:
            self.reactions = data.reactions

    def _react(self, user_id: str, emoji: str) -> None:
        try:
            reaction = self.reactions[emoji]
        except KeyError:
            self.reactions[emoji] = (user_id,)
        else:
            self.reactions[emoji] = (*reaction, user_id)

    def _unreact(self, user_id: str, emoji: str) -> None:
        try:
            reaction = self.reactions[emoji]
        except KeyError:
            self.reactions[emoji] = ()
        else:
            self.reactions[emoji] = tuple(reactor_id for reactor_id in reaction if reactor_id != user_id)

    def _clear(self, emoji: str) -> None:
        self.reactions.pop(emoji, None)

    def get_author(self) -> User | Member | None:
        """Optional[Union[:class:`User`, :class:`Member`]]: Tries to get message author."""
        if isinstance(self._author, (User, Member)):
            return self._author
        if self._author == ZID:
            return self.state.system
        if not self.state.cache:
            return None

        cache = self.state.cache
        channel = self.channel
        if not isinstance(channel, ServerChannel):
            return cache.get_user(
                self._author,
                # PROVIDE_CTX: caching.MessageContext(type=caching.ContextType.MESSAGE, message=self),
                caching._UNDEFINED,
            )
        return cache.get_server_member(
            channel.server_id,
            self._author,
            # PROVIDE_CTX: caching.MessageContext(type=caching.ContextType.MESSAGE, message=self),
            caching._UNDEFINED,
        )

    def system_event(self) -> SystemEvent | None:
        """Optional[:class:`SystemEvent`]: The system event information, occured in this message, if any."""
        if self.internal_system_event:
            return self.internal_system_event._stateful(self)

    @property
    def attachments(self) -> list[cdn.Asset]:
        """List[:class:`~cdn.Asset`]: The attachments on this message."""
        return [a._stateful(self.state, 'attachments') for a in self.internal_attachments]

    @property
    def author(self) -> User | Member:
        author = self.get_author()
        if not author:
            raise NoData(self.author_id, 'message author')
        return author

    @property
    def author_id(self) -> str:
        """:class:`str`: The ID of the user or webhook that sent this message."""
        if isinstance(self._author, (User, Member)):
            return self._author.id
        return self._author

    @property
    def embeds(self) -> list[Embed]:
        """List[:class:`Embed`]: The attached embeds to this message."""
        return [e._stateful(self.state) for e in self.internal_embeds]

    def is_silent(self) -> bool:
        """:class:`bool`: Whether the message is silent."""
        return MessageFlags.SUPPRESS_NOTIFICATIONS in self.flags


__all__ = (
    'Reply',
    'Interactions',
    'Masquerade',
    'SendableEmbed',
    'MessageSort',
    'MessageWebhook',
    'BaseMessage',
    'PartialMessage',
    'MessageAppendData',
    'BaseSystemEvent',
    'TextSystemEvent',
    'StatelessUserAddedSystemEvent',
    'UserAddedSystemEvent',
    'StatelessUserRemovedSystemEvent',
    'UserRemovedSystemEvent',
    'StatelessUserJoinedSystemEvent',
    'UserJoinedSystemEvent',
    'StatelessUserLeftSystemEvent',
    'UserLeftSystemEvent',
    'StatelessUserKickedSystemEvent',
    'UserKickedSystemEvent',
    'StatelessUserBannedSystemEvent',
    'UserBannedSystemEvent',
    'StatelessChannelRenamedSystemEvent',
    'ChannelRenamedSystemEvent',
    'StatelessChannelDescriptionChangedSystemEvent',
    'ChannelDescriptionChangedSystemEvent',
    'StatelessChannelIconChangedSystemEvent',
    'ChannelIconChangedSystemEvent',
    'StatelessChannelOwnershipChangedSystemEvent',
    'ChannelOwnershipChangedSystemEvent',
    'StatelessMessagePinnedSystemEvent',
    'MessagePinnedSystemEvent',
    'StatelessMessageUnpinnedSystemEvent',
    'MessageUnpinnedSystemEvent',
    'StatelessSystemEvent',
    'SystemEvent',
    'MessageFlags',
    'Message',
)
