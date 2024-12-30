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

from attrs import define, field
from datetime import datetime
import typing


from . import cache as caching
from .base import Base
from .channel import BaseServerChannel, ServerChannel, TextableChannel, PartialMessageable
from .cdn import AssetMetadata, StatelessAsset, Asset, ResolvableResource, resolve_resource
from .core import (
    UNDEFINED,
    UndefinedOr,
    ULIDOr,
    resolve_id,
    ZID,
)
from .emoji import ResolvableEmoji
from .enums import AssetMetadataType, ContentReportReason, RelationshipStatus
from .errors import NoData
from .flags import MessageFlags
from .server import Member
from .user import BaseUser, User

if typing.TYPE_CHECKING:
    from . import raw
    from .embed import StatelessEmbed, Embed
    from .server import Server
    from .state import State

_new_message_flags = MessageFlags.__new__


class Reply:
    """Represents a message reply.

    Attributes
    ----------
    id: :class:`str`
        The ID of the message that being replied to.
    mention: :class:`bool`
        Whether to mention author of referenced message or not.
    """

    __slots__ = ('id', 'mention')

    def __init__(self, id: ULIDOr[BaseMessage], mention: bool = False) -> None:
        self.id = resolve_id(id)
        self.mention = mention

    def build(self) -> raw.ReplyIntent:
        return {
            'id': self.id,
            'mention': self.mention,
        }


class MessageInteractions:
    """Represents information how to guide interactions on the message.

    Attributes
    ----------
    reactions: List[:class:`str`]
        The reactions which should always appear and be distinct.
    restrict_reactions: :class:`bool`
        Whether reactions should be restricted to the given list.

        Can only be set to ``True`` if :attr:`.reactions` has at least 1 emoji. Defaults to `False`.
    """

    __slots__ = ('reactions', 'restrict_reactions')

    def __init__(self, reactions: list[str], restrict_reactions: bool = False) -> None:
        self.reactions: list[str] = reactions
        self.restrict_reactions: bool = restrict_reactions

    def build(self) -> raw.Interactions:
        return {
            'reactions': self.reactions,
            'restrict_reactions': self.restrict_reactions,
        }


class Masquerade:
    """Represents a override of name and/or avatar.

    Attributes
    ----------
    name: Optional[:class:`str`]
        Replace the display name shown on this message.
    avatar: Optional[:class:`str`]
        Replace the avatar shown on this message (URL to image file).
    color: Optional[:class:`str`]
        Replace the display role color shown on this message. Can be any valid CSS color.

        You must have :attr:`~Permissions.manage_roles` permission to set this attribute.
    """

    __slots__ = ('name', 'avatar', 'color')

    def __init__(
        self,
        name: str | None = None,
        avatar: str | None = None,
        *,
        color: str | None = None,
    ) -> None:
        self.name: str | None = name
        self.avatar: str | None = avatar
        self.color: str | None = color

    def build(self) -> raw.Masquerade:
        payload: raw.Masquerade = {}
        if self.name is not None:
            payload['name'] = self.name
        if self.avatar is not None:
            payload['avatar'] = self.avatar
        if self.color is not None:
            payload['colour'] = self.color
        return payload


class SendableEmbed:
    """Represents a text embed before it is sent.

    Attributes
    ----------
    icon_url: Optional[:class:`str`]
        The embed icon URL.
    url: Optional[:class:`str`]
        The embed URL.
    title: Optional[:class:`str`]
        The title of the embed.
    description: Optional[:class:`str`]
        The description of the embed.
    media: Optional[:class:`ResolvableResource`]
        The file inside the embed.
    color: Optional[:class:`str`]
        The embed color. This can be any valid `CSS color <https://developer.mozilla.org/en-US/docs/Web/CSS/color_value)`_.
    """

    __slots__ = ('icon_url', 'url', 'title', 'description', 'media', 'color')

    def __init__(
        self,
        title: str | None = None,
        description: str | None = None,
        *,
        icon_url: str | None = None,
        url: str | None = None,
        media: ResolvableResource | None = None,
        color: str | None = None,
    ) -> None:
        self.icon_url: str | None = icon_url
        self.url: str | None = url
        self.title: str | None = title
        self.description: str | None = description
        self.media: ResolvableResource | None = media
        self.color: str | None = color

    async def build(self, state: State, /) -> raw.SendableEmbed:
        payload: raw.SendableEmbed = {}
        if self.icon_url is not None:
            payload['icon_url'] = self.icon_url
        if self.url is not None:
            payload['url'] = self.url
        if self.title is not None:
            payload['title'] = self.title
        if self.description is not None:
            payload['description'] = self.description
        if self.media is not None:
            payload['media'] = await resolve_resource(state, self.media, tag='attachments')
        if self.color is not None:
            payload['colour'] = self.color
        return payload


@define(slots=True)
class MessageWebhook:
    """Information about the webhook bundled with Message."""

    name: str = field(repr=True, kw_only=True)
    """:class:`str`: The webhook's name (from 1 to 32 characters).."""

    avatar: str | None = field(repr=True, kw_only=True)
    """Optional[:class:`str`]: The webhook avatar's ID, if any."""


@define(slots=True)
class BaseMessage(Base):
    """Represents a message in channel on Revolt."""

    channel_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The channel's ID this message was sent in."""

    def __hash__(self) -> int:
        return hash((self.channel_id, self.id))

    def __eq__(self, other: object, /) -> bool:
        return (
            self is other
            or isinstance(other, BaseMessage)
            and self.channel_id == other.channel_id
            and self.id == other.id
        )

    @property
    def channel(self) -> TextableChannel | PartialMessageable:
        """Union[:class:`.TextableChannel`, :class:`.PartialMessageable`]: The channel this message was sent in."""

        cache = self.state.cache
        if not cache:
            return PartialMessageable(state=self.state, id=self.channel_id)

        channel = cache.get_channel(self.channel_id, caching._USER_REQUEST)
        if channel:
            assert isinstance(channel, TextableChannel), 'Cache returned non textable channel'
            return channel

        return PartialMessageable(state=self.state, id=self.channel_id)

    @property
    def server(self) -> Server | None:
        """Optional[:class:`.Server`]: The server this message was sent in."""

        cache = self.state.cache
        if not cache:
            return None

        channel = cache.get_channel(self.channel_id, caching._USER_REQUEST)
        if channel is None:
            return None

        if not isinstance(channel, BaseServerChannel):
            return None

        return cache.get_server(channel.server_id, caching._USER_REQUEST)

    async def acknowledge(self) -> None:
        """|coro|

        Marks this message as read.

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

        Alias to :meth:`.acknowledge`.

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

        Deletes the message.
        You must have :attr:`~Permissions.manage_messages` to do this if message is not your's.

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
        content: UndefinedOr[:class:`str`]
            The new content to replace the message with.
        embeds: UndefinedOr[List[:class:`SendableEmbed`]]
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
        attachments: list[ResolvableResource] | None = None,
        mention: bool = True,
        embeds: list[SendableEmbed] | None = None,
        masquerade: Masquerade | None = None,
        interactions: MessageInteractions | None = None,
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
        user: Optional[ULIDOr[:class:`BaseUser`]]
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
    """Represents partial message in channel on Revolt."""

    content: UndefinedOr[str] = field(repr=True, kw_only=True)
    """UndefinedOr[:class:`str`]: The new message's content."""

    edited_at: UndefinedOr[datetime] = field(repr=True, kw_only=True)
    """UndefinedOr[:class:`~datetime.datetime`]: When the message was edited."""

    internal_embeds: UndefinedOr[list[StatelessEmbed]] = field(repr=True, kw_only=True)
    """UndefinedOr[List[:class:`.StatelessEmbed`]]: The new message embeds."""

    pinned: UndefinedOr[bool] = field(repr=True, kw_only=True)
    """UndefinedOr[:class:`bool`]: Whether the message was just pinned."""

    reactions: UndefinedOr[dict[str, tuple[str, ...]]] = field(repr=True, kw_only=True)
    """UndefinedOr[Dict[:class:`str`, Tuple[:class:`str`, ...]]]: The new message's reactions."""

    @property
    def embeds(self) -> UndefinedOr[list[Embed]]:
        """UndefinedOr[List[:class:`.Embed`]]: The new message embeds."""
        return (
            UNDEFINED
            if self.internal_embeds is UNDEFINED
            else [e.attach_state(self.state) for e in self.internal_embeds]
        )


@define(slots=True)
class MessageAppendData(BaseMessage):
    """Appended data to message in channel on Revolt."""

    internal_embeds: UndefinedOr[list[StatelessEmbed]] = field(repr=True, kw_only=True)
    """UndefinedOr[List[:class:`.StatelessEmbed`]]: The stateless embeds that were appended."""

    @property
    def embeds(self) -> UndefinedOr[list[Embed]]:
        """UndefinedOr[List[:class:`.Embed`]]: The embeds that were appended."""
        return (
            UNDEFINED
            if self.internal_embeds is UNDEFINED
            else [e.attach_state(self.state) for e in self.internal_embeds]
        )


class BaseSystemEvent:
    """Represents system event within message."""

    __slots__ = ()


@define(slots=True, eq=True)
class TextSystemEvent(BaseSystemEvent):
    content: str = field(repr=True, kw_only=True, eq=True)
    """:class:`str`: The event contents."""

    def attach_state(self, message: Message, /) -> TextSystemEvent:
        """:class:`.TextSystemEvent` Attach a state to system event.

        Parameters
        ----------
        message: :class:`.Message`
            The state to attach.
        """
        return self

    @property
    def system_content(self) -> str:
        """:class:`str`: The displayed system's content."""
        return self.content


@define(slots=True)
class StatelessUserAddedSystemEvent(BaseSystemEvent):
    _user: User | Member | str = field(repr=False, kw_only=True, alias='internal_user')

    def __eq__(self, other: object, /) -> bool:
        return (
            self is other
            or isinstance(other, StatelessUserAddedSystemEvent)
            and self.user_id == other.user_id
            and self.by_id == other.by_id
        )

    @property
    def user_id(self) -> str:
        """:class:`str`: The user's ID that was added."""
        if isinstance(self._user, (User, Member)):
            return self._user.id
        return self._user

    def get_user(self) -> User | Member | None:
        """Optional[Union[:class:`.User`, :class:`.Member`]]: Tries to get user that was added."""
        if isinstance(self._user, (User, Member)):
            return self._user

    _by: User | Member | str = field(repr=False, kw_only=True, alias='internal_by')

    @property
    def by_id(self) -> str:
        """:class:`str`: The user's ID that added this user."""
        if isinstance(self._by, (User, Member)):
            return self._by.id
        return self._by

    def get_by(self) -> User | Member | None:
        """Optional[Union[:class:`.User`, :class:`.Member`]]: Tries to get user that added this user."""
        if isinstance(self._by, (User, Member)):
            return self._by

    def attach_state(self, message: Message, /) -> UserAddedSystemEvent:
        """:class:`.UserAddedSystemEvent`: Attach a state to system event.

        Parameters
        ----------
        message: :class:`.Message`
            The state to attach.
        """
        return UserAddedSystemEvent(
            message=message,
            internal_user=self._user,
            internal_by=self._by,
        )

    @property
    def system_content(self) -> str:
        """:class:`str`: The displayed system's content."""

        user = self.get_user()
        if user is None:
            user = '<Unknown User>'

        by = self.get_by()
        if by is None:
            by = '<Unknown User>'

        return f'{user} was added by {by}'


@define(slots=True)
class UserAddedSystemEvent(StatelessUserAddedSystemEvent):
    message: Message = field(repr=False, kw_only=True, eq=False)
    """:class:`.Message`: The message that holds this system event."""

    def get_user(self) -> User | Member | None:
        """Optional[Union[:class:`.User`, :class:`.Member`]]: Tries to get user that was added."""
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
        """Union[:class:`.User`, class:`Member`]: The user that was added."""
        user = self.get_user()
        if not user:
            raise NoData(self.user_id, 'added user')
        return user

    def get_by(self) -> User | Member | None:
        """Optional[Union[:class:`.User`, :class:`.Member`]]: Tries to get user that added this user."""
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
        """Union[:class:`.User`, class:`Member`]: The user that added this user."""
        user = self.get_user()
        if not user:
            raise NoData(self.user_id, 'added user')
        return user


@define(slots=True)
class StatelessUserRemovedSystemEvent(BaseSystemEvent):
    _user: User | Member | str = field(repr=False, kw_only=True, alias='internal_user')

    def __eq__(self, other: object, /) -> bool:
        return (
            self is other
            or isinstance(other, StatelessUserRemovedSystemEvent)
            and self.user_id == other.user_id
            and self.by_id == other.by_id
        )

    @property
    def user_id(self) -> str:
        """:class:`str`: The user's ID that was removed."""
        if isinstance(self._user, (User, Member)):
            return self._user.id
        return self._user

    def get_user(self) -> User | Member | None:
        """Optional[Union[:class:`.User`, :class:`.Member`]]: Tries to get user that was removed."""
        if isinstance(self._user, (User, Member)):
            return self._user

    _by: User | Member | str = field(repr=False, kw_only=True, alias='internal_by')

    @property
    def by_id(self) -> str:
        """:class:`str`: The user's ID that removed this user."""
        if isinstance(self._by, (User, Member)):
            return self._by.id
        return self._by

    def get_by(self) -> User | Member | None:
        """Optional[Union[:class:`.User`, :class:`.Member`]]: Tries to get user that removed this user."""
        if isinstance(self._by, (User, Member)):
            return self._by

    def attach_state(self, message: Message, /) -> UserRemovedSystemEvent:
        """:class:`.UserRemovedSystemEvent`: Attach a state to system event.

        Parameters
        ----------
        message: :class:`.Message`
            The state to attach.
        """
        return UserRemovedSystemEvent(
            message=message,
            internal_user=self._user,
            internal_by=self._by,
        )

    @property
    def system_content(self) -> str:
        """:class:`str`: The displayed system's content."""

        user = self.get_user()
        if user is None:
            user = '<Unknown User>'

        by = self.get_by()
        if by is None:
            by = '<Unknown User>'

        return f'{user} was removed by {by}'


@define(slots=True)
class UserRemovedSystemEvent(StatelessUserRemovedSystemEvent):
    message: Message = field(repr=False, kw_only=True, eq=False)
    """:class:`.Message`: The message that holds this system event."""

    def get_user(self) -> User | Member | None:
        """Optional[Union[:class:`.User`, :class:`.Member`]]: Tries to get user that was removed."""
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
        """Union[:class:`.User`, class:`Member`]: The user that was removed."""
        user = self.get_user()
        if not user:
            raise NoData(self.user_id, 'removed user')
        return user

    def get_by(self) -> User | Member | None:
        """Optional[Union[:class:`.User`, :class:`.Member`]]: Tries to get user that removed this user."""
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
        """Union[:class:`.User`, class:`Member`]: The user that removed this user."""
        user = self.get_user()
        if not user:
            raise NoData(self.user_id, 'remover')
        return user


@define(slots=True)
class StatelessUserJoinedSystemEvent(BaseSystemEvent):
    _user: User | Member | str = field(repr=False, kw_only=True, alias='internal_user')

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, StatelessUserJoinedSystemEvent) and self.user_id == other.user_id

    @property
    def user_id(self) -> str:
        """:class:`str`: The user's ID that joined this server/group."""
        if isinstance(self._user, (User, Member)):
            return self._user.id
        return self._user

    def get_user(self) -> User | Member | None:
        """Optional[Union[:class:`.User`, :class:`.Member`]]: Tries to get user that joined this server/group."""
        if isinstance(self._user, (User, Member)):
            return self._user

    def attach_state(self, message: Message, /) -> UserJoinedSystemEvent:
        """:class:`.UserJoinedSystemEvent`: Attach a state to system event.

        Parameters
        ----------
        message: :class:`.Message`
            The state to attach.
        """
        return UserJoinedSystemEvent(
            message=message,
            internal_user=self._user,
        )

    @property
    def system_content(self) -> str:
        """:class:`str`: The displayed system's content."""

        user = self.get_user()
        if user is None:
            user = '<Unknown User>'

        return f'{user} joined'


@define(slots=True)
class UserJoinedSystemEvent(StatelessUserJoinedSystemEvent):
    message: Message = field(repr=False, kw_only=True)
    """The message that holds this system event."""

    def get_user(self) -> User | Member | None:
        """Optional[Union[:class:`.User`, :class:`.Member`]]: Tries to get user that was added."""
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
        """Union[:class:`.User`, class:`Member`]: The user that joined this server/group.."""
        user = self.get_user()
        if not user:
            raise NoData(self.user_id, 'joined user')
        return user


@define(slots=True)
class StatelessUserLeftSystemEvent(BaseSystemEvent):
    _user: User | Member | str = field(repr=False, kw_only=True, alias='internal_user')

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, StatelessUserLeftSystemEvent) and self.user_id == other.user_id

    @property
    def user_id(self) -> str:
        """:class:`str`: The user's ID that left this server/group."""
        if isinstance(self._user, (User, Member)):
            return self._user.id
        return self._user

    def get_user(self) -> User | Member | None:
        """Optional[Union[:class:`.User`, :class:`.Member`]]: Tries to get user that left this server/group."""
        if isinstance(self._user, (User, Member)):
            return self._user

    def attach_state(self, message: Message, /) -> UserLeftSystemEvent:
        """:class:`.UserLeftSystemEvent`: Attach a state to system event.

        Parameters
        ----------
        message: :class:`.Message`
            The state to attach.
        """
        return UserLeftSystemEvent(
            message=message,
            internal_user=self._user,
        )

    @property
    def system_content(self) -> str:
        """:class:`str`: The displayed system's content."""

        user = self.get_user()
        if user is None:
            user = '<Unknown User>'

        return f'{user} left'


@define(slots=True)
class UserLeftSystemEvent(StatelessUserLeftSystemEvent):
    message: Message = field(repr=False, kw_only=True, eq=False)
    """:class:`.Message`: The message that holds this system event."""

    def get_user(self) -> User | Member | None:
        """Optional[Union[:class:`.User`, :class:`.Member`]]: Tries to get user that left this server/group."""
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
        """Union[:class:`.User`, class:`Member`]: The user that left this server/group."""
        user = self.get_user()
        if not user:
            raise NoData(self.user_id, 'left user')
        return user


@define(slots=True)
class StatelessUserKickedSystemEvent(BaseSystemEvent):
    _user: User | Member | str = field(repr=False, kw_only=True, alias='internal_user')

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, StatelessUserKickedSystemEvent) and self.user_id == other.user_id

    @property
    def user_id(self) -> str:
        """:class:`str`: The user's ID that was kicked from this server."""
        if isinstance(self._user, (User, Member)):
            return self._user.id
        return self._user

    def get_user(self) -> User | Member | None:
        """Optional[Union[:class:`.User`, :class:`.Member`]]: Tries to get user that was kicked from this server."""
        if isinstance(self._user, (User, Member)):
            return self._user

    def attach_state(self, message: Message, /) -> UserKickedSystemEvent:
        """:class:`.UserKickedSystemEvent`: Attach a state to system event.

        Parameters
        ----------
        message: :class:`.Message`
            The state to attach.
        """
        return UserKickedSystemEvent(
            message=message,
            internal_user=self._user,
        )

    @property
    def system_content(self) -> str:
        """:class:`str`: The displayed system's content."""

        user = self.get_user()
        if user is None:
            user = '<Unknown User>'

        return f'{user} was kicked'


@define(slots=True)
class UserKickedSystemEvent(StatelessUserKickedSystemEvent):
    message: Message = field(repr=False, kw_only=True, eq=False)
    """:class:`.Message`: The message that holds this system event."""

    def get_user(self) -> User | Member | None:
        """Optional[Union[:class:`.User`, :class:`.Member`]]: Tries to get user that was kicked from this server."""
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
        """Union[:class:`.User`, class:`Member`]: The user that was kicked from this server."""
        user = self.get_user()
        if not user:
            raise NoData(self.user_id, 'kicked user')
        return user


@define(slots=True)
class StatelessUserBannedSystemEvent(BaseSystemEvent):
    _user: User | Member | str = field(repr=False, kw_only=True, alias='internal_user')

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, StatelessUserBannedSystemEvent) and self.user_id == other.user_id

    @property
    def user_id(self) -> str:
        """:class:`str`: The user's ID that was banned from this server."""
        if isinstance(self._user, (User, Member)):
            return self._user.id
        return self._user

    def get_user(self) -> User | Member | None:
        """Optional[Union[:class:`.User`, :class:`.Member`]]: Tries to get user that was banned from this server."""
        if isinstance(self._user, (User, Member)):
            return self._user

    def attach_state(self, message: Message, /) -> UserBannedSystemEvent:
        """:class:`.UserBannedSystemEvent`: Attach a state to system event.

        Parameters
        ----------
        message: :class:`.Message`
            The state to attach.
        """
        return UserBannedSystemEvent(
            message=message,
            internal_user=self._user,
        )

    @property
    def system_content(self) -> str:
        """:class:`str`: The displayed system's content."""

        user = self.get_user()
        if user is None:
            user = '<Unknown User>'

        return f'{user} was banned'


@define(slots=True)
class UserBannedSystemEvent(StatelessUserBannedSystemEvent):
    message: Message = field(repr=False, kw_only=True, eq=False)
    """:class:`.Message`: The message that holds this system event."""

    def get_user(self) -> User | Member | None:
        """Optional[Union[:class:`.User`, :class:`.Member`]]: Tries to get user that was banned from this server."""
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
        """Union[:class:`.User`, class:`Member`]: The user that was banned from this server."""
        user = self.get_user()
        if not user:
            raise NoData(self.user_id, 'banned user')
        return user


@define(slots=True)
class StatelessChannelRenamedSystemEvent(BaseSystemEvent):
    name: str = field(repr=True, kw_only=True)
    """:class:`str`: The new name of this group."""

    _by: User | str = field(repr=False, kw_only=True, alias='internal_by')

    def __eq__(self, other: object, /) -> bool:
        return (
            self is other
            or isinstance(other, StatelessChannelRenamedSystemEvent)
            and self.name == other.name
            and self.by_id == other.by_id
        )

    @property
    def by_id(self) -> str:
        """:class:`str`: The user's ID that renamed this group."""
        if isinstance(self._by, User):
            return self._by.id
        return self._by

    def get_by(self) -> User | None:
        """Optional[:class:`.User`]: Tries to get user that renamed this group."""
        if isinstance(self._by, User):
            return self._by

    def attach_state(self, message: Message, /) -> ChannelRenamedSystemEvent:
        """:class:`.ChannelRenamedSystemEvent`: Attach a state to system event.

        Parameters
        ----------
        message: :class:`.Message`
            The state to attach.
        """
        return ChannelRenamedSystemEvent(
            message=message,
            name=self.name,
            internal_by=self._by,
        )

    @property
    def system_content(self) -> str:
        """:class:`str`: The displayed system's content."""

        by = self.get_by()
        if by is None:
            by = '<Unknown User>'

        return f'{by} renamed the channel to {self.name}'


@define(slots=True)
class ChannelRenamedSystemEvent(StatelessChannelRenamedSystemEvent):
    message: Message = field(repr=False, kw_only=True, eq=False)
    """:class:`.Message`: The message that holds this system event."""

    def get_by(self) -> User | None:
        """Optional[:class:`.User`: Tries to get user that renamed this group."""
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
        """:class:`.User`: The user that renamed this group."""
        by = self.get_by()
        if not by:
            raise NoData(self.by_id, 'user')
        return by


@define(slots=True)
class StatelessChannelDescriptionChangedSystemEvent(BaseSystemEvent):
    _by: User | str = field(repr=False, kw_only=True, alias='internal_by')

    def __eq__(self, other: object, /) -> bool:
        return (
            self is other
            or isinstance(other, StatelessChannelDescriptionChangedSystemEvent)
            and self.by_id == other.by_id
        )

    @property
    def by_id(self) -> str:
        """:class:`str`: The user's ID that changed description of this group."""
        if isinstance(self._by, User):
            return self._by.id
        return self._by

    def get_by(self) -> User | None:
        """Optional[:class:`.User`]: Tries to get user that changed description of this group."""
        if isinstance(self._by, User):
            return self._by

    def attach_state(self, message: Message, /) -> ChannelDescriptionChangedSystemEvent:
        """:class:`.ChannelDescriptionChangedSystemEvent`: Attach a state to system event.

        Parameters
        ----------
        message: :class:`.Message`
            The state to attach.
        """
        return ChannelDescriptionChangedSystemEvent(
            message=message,
            internal_by=self._by,
        )

    @property
    def system_content(self) -> str:
        """:class:`str`: The displayed system's content."""

        by = self.get_by()
        if by is None:
            by = '<Unknown User>'

        return f'{by} changed the channel description'


@define(slots=True)
class ChannelDescriptionChangedSystemEvent(StatelessChannelDescriptionChangedSystemEvent):
    message: Message = field(repr=False, kw_only=True, eq=False)
    """:class:`.Message`: The message that holds this system event."""

    def get_by(self) -> User | None:
        """Optional[:class:`.User`]: Tries to get user that changed description of this group."""
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
        """:class:`.User`: The user that changed description of this group."""
        by = self.get_by()
        if not by:
            raise NoData(self.by_id, 'user')
        return by


@define(slots=True)
class StatelessChannelIconChangedSystemEvent(BaseSystemEvent):
    _by: User | str = field(repr=False, kw_only=True, alias='internal_by')

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, StatelessChannelIconChangedSystemEvent) and self.by_id == other.by_id

    @property
    def by_id(self) -> str:
        """:class:`str`: The user's ID that changed icon of this group."""
        if isinstance(self._by, User):
            return self._by.id
        return self._by

    def get_by(self) -> User | None:
        """Optional[:class:`.User`]: Tries to get user that changed icon of this group."""
        if isinstance(self._by, User):
            return self._by

    def attach_state(self, message: Message, /) -> ChannelIconChangedSystemEvent:
        """:class:`.ChannelIconChangedSystemEvent`: Attach a state to system event.

        Parameters
        ----------
        message: :class:`.Message`
            The state to attach.
        """
        return ChannelIconChangedSystemEvent(
            message=message,
            internal_by=self._by,
        )

    @property
    def system_content(self) -> str:
        """:class:`str`: The displayed system's content."""

        by = self.get_by()
        if by is None:
            by = '<Unknown User>'

        return f'{by} changed the channel icon'


@define(slots=True)
class ChannelIconChangedSystemEvent(StatelessChannelIconChangedSystemEvent):
    message: Message = field(repr=False, kw_only=True, eq=False)
    """The message that holds this system event."""

    def get_by(self) -> User | None:
        """Optional[:class:`.User`]: Tries to get user that changed icon of this group."""
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
        """:class:`.User`: The user that changed icon of this group."""
        by = self.get_by()
        if not by:
            raise NoData(self.by_id, 'user')
        return by


@define(slots=True)
class StatelessChannelOwnershipChangedSystemEvent(BaseSystemEvent):
    _from: User | str = field(repr=False, kw_only=True, alias='internal_from')
    _to: User | str = field(repr=False, kw_only=True, alias='internal_to')

    def __eq__(self, other: object, /) -> bool:
        return (
            self is other
            or isinstance(other, StatelessChannelOwnershipChangedSystemEvent)
            and self.from_id == other.from_id
            and self.to_id == other.to_id
        )

    @property
    def from_id(self) -> str:
        """:class:`str`: The user's ID that was previous owner of this group."""
        if isinstance(self._from, User):
            return self._from.id
        return self._from

    def get_from(self) -> User | None:
        """Optional[:class:`.User`]: Tries to get user that was previous owner of this group."""
        if isinstance(self._from, User):
            return self._from

    @property
    def to_id(self) -> str:
        """:class:`str`: The user's ID that became owner of this group."""
        if isinstance(self._from, User):
            return self._from.id
        return self._from

    def get_to(self) -> User | None:
        """Optional[:class:`.User`]: Tries to get user that became owner of this group."""
        if isinstance(self._from, User):
            return self._from

    def attach_state(self, message: Message, /) -> ChannelOwnershipChangedSystemEvent:
        """:class:`.ChannelOwnershipChangedSystemEvent`: Attach a state to system event.

        Parameters
        ----------
        message: :class:`.Message`
            The state to attach.
        """
        return ChannelOwnershipChangedSystemEvent(
            message=message,
            internal_from=self._from,
            internal_to=self._to,
        )

    @property
    def system_content(self) -> str:
        """:class:`str`: The displayed system's content."""

        before = self.get_from()
        if before is None:
            before = '<Unknown User>'
        after = self.get_to()
        if after is None:
            after = '<Unknown User>'

        return f'{before} gave {after} group ownership'


@define(slots=True)
class ChannelOwnershipChangedSystemEvent(StatelessChannelOwnershipChangedSystemEvent):
    message: Message = field(repr=False, kw_only=True, eq=False)
    """:class:`.Message`: The message that holds this system event."""

    def get_from(self) -> User | None:
        """Optional[:class:`.User`]: Tries to get user that was previous owner of this group."""
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
        """:class:`.User`: The user that was previous owner of this group."""
        from_ = self.get_from()
        if not from_:
            raise NoData(self.from_id, 'user')
        return from_

    def get_to(self) -> User | None:
        """Optional[:class:`.User`]: Tries to get user that became owner of this group."""
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
        """:class:`.User`: The user that became owner of this group."""
        to = self.get_from()
        if not to:
            raise NoData(self.to_id, 'user')
        return to


@define(slots=True)
class StatelessMessagePinnedSystemEvent(BaseSystemEvent):
    pinned_message_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The ID of the message that was pinned."""

    _by: User | Member | str = field(repr=False, kw_only=True, alias='internal_by')

    def __eq__(self, other: object, /) -> bool:
        return (
            self is other
            or isinstance(other, StatelessMessagePinnedSystemEvent)
            and self.pinned_message_id == other.pinned_message_id
            and self.by_id == other.by_id
        )

    @property
    def by_id(self) -> str:
        """:class:`str`: The user's ID that pinned a message."""
        if isinstance(self._by, (User, Member)):
            return self._by.id
        return self._by

    def get_by(self) -> User | Member | None:
        """Optional[Union[:class:`.User`, :class:`.Member`]]: Tries to get user that pinned a message."""
        if isinstance(self._by, (User, Member)):
            return self._by

    def attach_state(self, message: Message, /) -> MessagePinnedSystemEvent:
        """:class:`.MessagePinnedSystemEvent`: Attach a state to system event.

        Parameters
        ----------
        message: :class:`.Message`
            The state to attach.
        """
        return MessagePinnedSystemEvent(
            message=message,
            pinned_message_id=self.pinned_message_id,
            internal_by=self._by,
        )

    @property
    def system_content(self) -> str:
        """:class:`str`: The displayed system's content."""

        by = self.get_by()
        if by is None:
            by = '<Unknown User>'

        return f'{by} pinned a message to this channel'


@define(slots=True)
class MessagePinnedSystemEvent(StatelessMessagePinnedSystemEvent):
    message: Message = field(repr=False, kw_only=True, eq=False)
    """:class:`.Message`: The message that holds this system event."""

    def get_by(self) -> User | Member | None:
        """Optional[Union[:class:`.User`, :class:`.Member`]]: Tries to get user that pinned a message."""
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
        """Union[:class:`.User`, class:`Member`]: The user that pinned a message."""
        by = self.get_by()
        if not by:
            raise NoData(self.by_id, 'user')
        return by


@define(slots=True)
class StatelessMessageUnpinnedSystemEvent(BaseSystemEvent):
    unpinned_message_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The ID of the message that was unpinned."""

    _by: User | Member | str = field(repr=False, kw_only=True, alias='internal_by')

    def __eq__(self, other: object, /) -> bool:
        return (
            self is other
            or isinstance(other, StatelessMessageUnpinnedSystemEvent)
            and self.unpinned_message_id == other.unpinned_message_id
            and self.by_id == other.by_id
        )

    @property
    def by_id(self) -> str:
        """:class:`str`: The user's ID that unpinned a message."""
        if isinstance(self._by, (User, Member)):
            return self._by.id
        return self._by

    def get_by(self) -> User | Member | None:
        """Optional[Union[:class:`.User`, :class:`.Member`]]: Tries to get user that unpinned a message."""
        if isinstance(self._by, (User, Member)):
            return self._by

    def attach_state(self, message: Message, /) -> MessageUnpinnedSystemEvent:
        """:class:`.MessageUnpinnedSystemEvent`: Attach a state to system event.

        Parameters
        ----------
        message: :class:`.Message`
            The state to attach.
        """
        return MessageUnpinnedSystemEvent(
            message=message,
            unpinned_message_id=self.unpinned_message_id,
            internal_by=self._by,
        )


@define(slots=True)
class MessageUnpinnedSystemEvent(StatelessMessageUnpinnedSystemEvent):
    message: Message = field(repr=False, kw_only=True, eq=False)
    """:class:`.Message`: The message that holds this system event."""

    def get_by(self) -> User | Member | None:
        """Optional[Union[:class:`.User`, :class:`.Member`]]: Tries to get user that unpinned a message."""
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
        """Union[:class:`.User`, class:`Member`]: The user that unpinned a message."""
        by = self.get_by()
        if not by:
            raise NoData(self.by_id, 'user')
        return by

    @property
    def system_content(self) -> str:
        """:class:`str`: The displayed system's content."""

        by = self.get_by()
        if by is None:
            by = '<Unknown User>'

        return f'{by} unpinned a message from this channel'


StatelessSystemEvent = (
    TextSystemEvent
    | StatelessUserAddedSystemEvent
    | StatelessUserRemovedSystemEvent
    | StatelessUserJoinedSystemEvent
    | StatelessUserLeftSystemEvent
    | StatelessUserKickedSystemEvent
    | StatelessUserBannedSystemEvent
    | StatelessChannelRenamedSystemEvent
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
    | ChannelRenamedSystemEvent
    | ChannelDescriptionChangedSystemEvent
    | ChannelIconChangedSystemEvent
    | ChannelOwnershipChangedSystemEvent
    | MessagePinnedSystemEvent
    | MessageUnpinnedSystemEvent
)


@define(slots=True)
class Message(BaseMessage):
    """Represents a message in channel on Revolt."""

    nonce: str | None = field(repr=True, kw_only=True)
    """Optional[:class:`str`]: The unique value generated by client sending this message."""

    channel_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The channel's ID this message was sent in."""

    _author: User | Member | str = field(repr=False, kw_only=True, alias='internal_author')

    webhook: MessageWebhook | None = field(repr=True, kw_only=True)
    """Optional[:class:`.MessageWebhook`]: The webhook that sent this message."""

    content: str = field(repr=True, kw_only=True)
    """:class:`str`: The message's content."""

    internal_system_event: StatelessSystemEvent | None = field(repr=True, kw_only=True)
    """Optional[:class:`.StatelessSystemEvent`]: The stateless system event information, occured in this message, if any."""

    internal_attachments: list[StatelessAsset] = field(repr=True, kw_only=True)
    """List[:class:`.StatelessAsset`]: The stateless attachments on this message."""

    edited_at: datetime | None = field(repr=True, kw_only=True)
    """Optional[:class:`~datetime.datetime`]: Timestamp at which this message was last edited."""

    internal_embeds: list[StatelessEmbed] = field(repr=True, kw_only=True)
    """List[:class:`.StatelessEmbed`]: The attached stateless embeds to this message."""

    mention_ids: list[str] = field(repr=True, kw_only=True)
    """List[:class:`str`]: The user's IDs mentioned in this message."""

    role_mention_ids: list[str] = field(repr=True, kw_only=True)
    """List[:class:`str`]: The role's IDs mentioned in this message."""

    replies: list[str] = field(repr=True, kw_only=True)
    """List[:class:`str`]: The message's IDs this message is replying to."""

    reactions: dict[str, tuple[str, ...]] = field(repr=True, kw_only=True)
    """Dict[:class:`str`, Tuple[:class:`str`, ...]]: The mapping of emojis to list of user IDs."""

    interactions: MessageInteractions | None = field(repr=True, kw_only=True)
    """Optional[:class:`.MessageInteractions`]: The information about how this message should be interacted with."""

    masquerade: Masquerade | None = field(repr=True, kw_only=True)
    """Optional[:class:`.Masquerade`]: The name and / or avatar overrides for this message."""

    pinned: bool = field(repr=True, kw_only=True)
    """:class:`bool`: Whether the message is pinned."""

    raw_flags: int = field(repr=True, kw_only=True)
    """:class:`int`: The message's flags raw value."""

    def locally_append(self, data: MessageAppendData, /) -> None:
        if data.internal_embeds is not UNDEFINED:
            self.internal_embeds.extend(data.internal_embeds)

    def locally_clear_reactions(self, emoji: str, /) -> None:
        self.reactions.pop(emoji, None)

    def locally_react(self, user_id: str, emoji: str, /) -> None:
        try:
            reaction = self.reactions[emoji]
        except KeyError:
            self.reactions[emoji] = (user_id,)
        else:
            self.reactions[emoji] = (*reaction, user_id)

    def locally_unreact(self, user_id: str, emoji: str, /) -> None:
        try:
            reaction = self.reactions[emoji]
        except KeyError:
            self.reactions[emoji] = ()
        else:
            self.reactions[emoji] = tuple(reactor_id for reactor_id in reaction if reactor_id != user_id)

    def locally_update(self, data: PartialMessage, /) -> None:
        """Locally updates message with provided data.

        .. warning::
            This is called by library internally to keep cache up to date.

        Parameters
        ----------
        data: :class:`.PartialMessage`
            The data to update message with.
        """
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

    def get_author(self) -> User | Member | None:
        """Optional[Union[:class:`.User`, :class:`.Member`]]: Tries to get message author."""
        if isinstance(self._author, (User, Member)):
            return self._author

        if self._author == ZID:
            return self.state.system

        state = self.state
        if self.webhook:
            webhook = self.webhook
            webhook_id = self.author_id

            return User(
                state=state,
                id=webhook_id,
                name=webhook.name,
                discriminator='0000',
                internal_avatar=StatelessAsset(
                    id=webhook.avatar,
                    filename='',
                    metadata=AssetMetadata(
                        type=AssetMetadataType.image,
                        width=0,
                        height=0,
                    ),
                    content_type='',
                    size=0,
                    deleted=False,
                    reported=False,
                    message_id=None,
                    user_id=webhook_id,
                    server_id=None,
                    object_id=webhook_id,
                )
                if webhook.avatar
                else None,
                display_name=None,
                raw_badges=0,
                status=None,
                raw_flags=0,
                privileged=False,
                bot=None,
                relationship=RelationshipStatus.none,
                online=False,
            )

        cache = state.cache
        if not cache:
            return None

        channel = self.channel
        if not isinstance(channel, ServerChannel):
            return cache.get_user(
                self._author,
                caching.MessageCacheContext(type=caching.CacheContextType.message, message=self)
                if 'Message.get_author' in state.provide_cache_context_in
                else caching._UNDEFINED,
            )
        return cache.get_server_member(
            channel.server_id,
            self._author,
            caching.MessageCacheContext(type=caching.CacheContextType.message, message=self)
            if 'Message.get_author' in state.provide_cache_context_in
            else caching._UNDEFINED,
        )

    @property
    def attachments(self) -> list[Asset]:
        """List[:class:`.Asset`]: The attachments on this message."""
        return [a.attach_state(self.state, 'attachments') for a in self.internal_attachments]

    @property
    def author(self) -> User | Member:
        """Union[:class:`.User`, :class:`.Member`]: The user that sent this message."""
        author = self.get_author()
        if not author:
            raise NoData(self.author_id, 'message author')
        return author

    @property
    def author_id(self) -> str:
        """:class:`str`: The user's ID or webhook that sent this message."""
        if isinstance(self._author, (User, Member)):
            return self._author.id
        return self._author

    @property
    def embeds(self) -> list[Embed]:
        """List[:class:`.Embed`]: The attached embeds to this message."""
        return [e.attach_state(self.state) for e in self.internal_embeds]

    @property
    def flags(self) -> MessageFlags:
        """:class:`.MessageFlags`: The message's flags."""
        ret = _new_message_flags(MessageFlags)
        ret.value = self.raw_flags
        return ret

    @property
    def system_content(self) -> str:
        """:class:`str`: The displayed message's content."""

        system_event = self.system_event
        if system_event is None:
            return self.content

        return system_event.system_content

    @property
    def system_event(self) -> SystemEvent | None:
        """Optional[:class:`.SystemEvent`]: The system event information, occured in this message, if any."""
        if self.internal_system_event:
            return self.internal_system_event.attach_state(self)

    def is_silent(self) -> bool:
        """:class:`bool`: Whether the message is silent."""
        return self.flags.suppress_notifications


__all__ = (
    'Reply',
    'MessageInteractions',
    'Masquerade',
    'SendableEmbed',
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
    'Message',
)
