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
    """Event contents."""


@define(slots=True)
class UserAddedSystemEvent(BaseSystemEvent):
    user_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """ID of the user that was added."""

    by_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """ID of the user that added this user."""


@define(slots=True)
class UserRemovedSystemEvent(BaseSystemEvent):
    user_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The ID of the user that was removed."""

    by_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The ID of the user that removed this user."""


@define(slots=True)
class UserJoinedSystemEvent(BaseSystemEvent):
    user_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The ID of the user that joined this server/group."""


@define(slots=True)
class UserLeftSystemEvent(BaseSystemEvent):
    user_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The ID of the user that left this server/group."""


@define(slots=True)
class UserKickedSystemEvent(BaseSystemEvent):
    user_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The ID of the user that was kicked from this server."""


@define(slots=True)
class UserBannedSystemEvent(BaseSystemEvent):
    user_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The ID of the user that was banned from this server."""


@define(slots=True)
class ChannelRenamedSystemEvent(BaseSystemEvent):
    by_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The ID of the user that renamed this group."""


@define(slots=True)
class ChannelDescriptionChangedSystemEvent(BaseSystemEvent):
    by_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The ID of the user that changed description of this group."""


@define(slots=True)
class ChannelIconChangedSystemEvent(BaseSystemEvent):
    by_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The ID of the user that changed icon of this group."""


@define(slots=True)
class ChannelOwnershipChangedSystemEvent(BaseSystemEvent):
    from_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The ID of the user that was previous owner of this group."""

    to_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The ID of the user that became owner of this group."""


@define(slots=True)
class MessagePinnedSystemEvent(BaseSystemEvent):
    message_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The ID of the message that was pinned."""

    by_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The ID of the user that pinned the message."""


@define(slots=True)
class MessageUnpinnedSystemEvent(BaseSystemEvent):
    message_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The ID of the message that was pinned."""

    by_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The ID of the user that pinned the message."""


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

    system_event: SystemEvent | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The system event information, occured in this message, if any."""

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
        """Try get message author."""
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

    @property
    def attachments(self) -> list[cdn.Asset]:
        """The attachments on this message."""
        return [a._stateful(self.state, 'attachments') for a in self.internal_attachments]

    @property
    def author(self) -> User | Member:
        author = self.get_author()
        if not author:
            raise NoData(self.author_id, 'message author')
        return author

    @property
    def author_id(self) -> str:
        """The ID of the user or webhook that sent this message."""
        if isinstance(self._author, (User, Member)):
            return self._author.id
        return self._author

    @property
    def embeds(self) -> list[Embed]:
        """The attached embeds to this message."""
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
    'UserAddedSystemEvent',
    'UserRemovedSystemEvent',
    'UserJoinedSystemEvent',
    'UserLeftSystemEvent',
    'UserKickedSystemEvent',
    'UserBannedSystemEvent',
    'ChannelRenamedSystemEvent',
    'ChannelDescriptionChangedSystemEvent',
    'ChannelIconChangedSystemEvent',
    'ChannelOwnershipChangedSystemEvent',
    'MessagePinnedSystemEvent',
    'MessageUnpinnedSystemEvent',
    'SystemEvent',
    'MessageFlags',
    'Message',
)
