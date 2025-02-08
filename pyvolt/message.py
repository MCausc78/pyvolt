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


class MessageMasquerade:
    """Represents overrides of name and/or avatar on message.

    Attributes
    ----------
    name: Optional[:class:`str`]
        The name to replace the display name on message with. Must be between 1 and 32 characters long.
    avatar: Optional[:class:`str`]
        The image URL to replace the displayed avatar on message with.
    color: Optional[:class:`str`]
        The CSS color to replace display role color shown on message.
        This must be valid `CSS color <https://developer.mozilla.org/en-US/docs/Web/CSS/color_value)`_.

        You (or webhook) must have :attr:`~Permissions.manage_roles` permission to set this attribute.
    """

    __slots__ = ('name', 'avatar', 'color')

    def __init__(
        self,
        name: typing.Optional[str] = None,
        avatar: typing.Optional[str] = None,
        *,
        color: typing.Optional[str] = None,
    ) -> None:
        self.name: typing.Optional[str] = name
        self.avatar: typing.Optional[str] = avatar
        self.color: typing.Optional[str] = color

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
        The embed's title.
    description: Optional[:class:`str`]
        The embed's description.
    media: Optional[:class:`.ResolvableResource`]
        The file inside the embed.
    color: Optional[:class:`str`]
        The embed color. This must be valid `CSS color <https://developer.mozilla.org/en-US/docs/Web/CSS/color_value)`_.
    """

    __slots__ = ('icon_url', 'url', 'title', 'description', 'media', 'color')

    def __init__(
        self,
        title: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
        *,
        icon_url: typing.Optional[str] = None,
        url: typing.Optional[str] = None,
        media: typing.Optional[ResolvableResource] = None,
        color: typing.Optional[str] = None,
    ) -> None:
        self.icon_url: typing.Optional[str] = icon_url
        self.url: typing.Optional[str] = url
        self.title: typing.Optional[str] = title
        self.description: typing.Optional[str] = description
        self.media: typing.Optional[ResolvableResource] = media
        self.color: typing.Optional[str] = color

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
    """:class:`str`: The webhook's name. Can be between 1 to 32 characters."""

    avatar: typing.Optional[str] = field(repr=True, kw_only=True)
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
    def channel(self) -> typing.Union[TextableChannel, PartialMessageable]:
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
    def server(self) -> typing.Optional[Server]:
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

        You must have :attr:`~Permissions.view_channel` to do this.

        There is an alias for this called :meth:`~.ack`.

        .. note::
            This can only be used by non-bot accounts.

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
        return await self.state.http.acknowledge_message(self.channel_id, self.id)

    async def ack(self) -> None:
        """|coro|

        Marks this message as read.

        This is an alias for :meth:`~.acknowledge`.

        You must have :attr:`~Permissions.view_channel` to do this.

        .. note::
            This can only be used by non-bot accounts.

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
        return await self.acknowledge()

    async def delete(self) -> None:
        """|coro|

        Deletes the message in a channel.

        You must have :attr:`~Permissions.manage_messages` to do this if message is not yours.

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
        return await self.state.http.delete_message(self.channel_id, self.id)

    async def edit(
        self,
        *,
        content: UndefinedOr[str] = UNDEFINED,
        embeds: UndefinedOr[list[SendableEmbed]] = UNDEFINED,
    ) -> Message:
        """|coro|

        Edits the message.

        Parameters
        ----------
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
        :class:`.Message`
            The newly edited message.
        """

        return await self.state.http.edit_message(self.channel_id, self.id, content=content, embeds=embeds)

    async def pin(self) -> None:
        """|coro|

        Pins the message.

        You must have :attr:`~Permissions.manage_messages` to do this.

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
        return await self.state.http.pin_message(self.channel_id, self.id)

    async def react(
        self,
        emoji: ResolvableEmoji,
    ) -> None:
        """|coro|

        React to this message.

        You must have :attr:`~Permissions.react` to do this.

        Parameters
        ----------
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

        return await self.state.http.add_reaction_to_message(self.channel_id, self.id, emoji)

    async def reply(
        self,
        content: typing.Optional[str] = None,
        *,
        nonce: typing.Optional[str] = None,
        attachments: typing.Optional[list[ResolvableResource]] = None,
        embeds: typing.Optional[list[SendableEmbed]] = None,
        masquerade: typing.Optional[MessageMasquerade] = None,
        interactions: typing.Optional[MessageInteractions] = None,
        silent: typing.Optional[bool] = None,
        mention_everyone: typing.Optional[bool] = None,
        mention_online: typing.Optional[bool] = None,
        mention: bool = True,
    ) -> Message:
        """|coro|

        Replies to this message.

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
        mention: :class:`bool`
            Whether to mention author of message you're replying to.

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
        :class:`.Message`
            The message that was sent.
        """
        return await self.state.http.send_message(
            self.channel_id,
            content=content,
            nonce=nonce,
            attachments=attachments,
            replies=[Reply(self.id, mention=mention)],
            embeds=embeds,
            masquerade=masquerade,
            interactions=interactions,
            silent=silent,
            mention_everyone=mention_everyone,
            mention_online=mention_online,
        )

    async def report(
        self,
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

        return await self.state.http.report_message(self.id, reason, additional_context=additional_context)

    async def unpin(self) -> None:
        """|coro|

        Unpins the message.

        You must have :attr:`~Permissions.manage_messages` to do this.

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

        return await self.state.http.unpin_message(self.channel_id, self.id)

    async def unreact(
        self,
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
    _user: typing.Union[User, Member, str] = field(repr=False, kw_only=True, alias='internal_user')

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

    def get_user(self) -> typing.Optional[typing.Union[User, Member]]:
        """Optional[Union[:class:`.User`, :class:`.Member`]]: Tries to get user that was added."""
        if isinstance(self._user, (User, Member)):
            return self._user

    _by: typing.Union[User, Member, str] = field(repr=False, kw_only=True, alias='internal_by')

    @property
    def by_id(self) -> str:
        """:class:`str`: The user's ID that added this user."""
        if isinstance(self._by, (User, Member)):
            return self._by.id
        return self._by

    def get_by(self) -> typing.Optional[typing.Union[User, Member]]:
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

    def get_user(self) -> typing.Optional[typing.Union[User, Member]]:
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
    def user(self) -> typing.Union[User, Member]:
        """Union[:class:`.User`, class:`Member`]: The user that was added."""
        user = self.get_user()
        if not user:
            raise NoData(self.user_id, 'added user')
        return user

    def get_by(self) -> typing.Optional[typing.Union[User, Member]]:
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
    def by(self) -> typing.Union[User, Member]:
        """Union[:class:`.User`, class:`Member`]: The user that added this user."""
        user = self.get_user()
        if not user:
            raise NoData(self.user_id, 'added user')
        return user


@define(slots=True)
class StatelessUserRemovedSystemEvent(BaseSystemEvent):
    _user: typing.Union[User, Member, str] = field(repr=False, kw_only=True, alias='internal_user')

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

    def get_user(self) -> typing.Optional[typing.Union[User, Member]]:
        """Optional[Union[:class:`.User`, :class:`.Member`]]: Tries to get user that was removed."""
        if isinstance(self._user, (User, Member)):
            return self._user

    _by: typing.Union[User, Member, str] = field(repr=False, kw_only=True, alias='internal_by')

    @property
    def by_id(self) -> str:
        """:class:`str`: The user's ID that removed this user."""
        if isinstance(self._by, (User, Member)):
            return self._by.id
        return self._by

    def get_by(self) -> typing.Optional[typing.Union[User, Member]]:
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

    def get_user(self) -> typing.Optional[typing.Union[User, Member]]:
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
    def user(self) -> typing.Union[User, Member]:
        """Union[:class:`.User`, class:`Member`]: The user that was removed."""
        user = self.get_user()
        if not user:
            raise NoData(self.user_id, 'removed user')
        return user

    def get_by(self) -> typing.Optional[typing.Union[User, Member]]:
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
    def by(self) -> typing.Union[User, Member]:
        """Union[:class:`.User`, class:`Member`]: The user that removed this user."""
        user = self.get_user()
        if not user:
            raise NoData(self.user_id, 'remover')
        return user


@define(slots=True)
class StatelessUserJoinedSystemEvent(BaseSystemEvent):
    _user: typing.Union[User, Member, str] = field(repr=False, kw_only=True, alias='internal_user')

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, StatelessUserJoinedSystemEvent) and self.user_id == other.user_id

    @property
    def user_id(self) -> str:
        """:class:`str`: The user's ID that joined this server/group."""
        if isinstance(self._user, (User, Member)):
            return self._user.id
        return self._user

    def get_user(self) -> typing.Optional[typing.Union[User, Member]]:
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

    def get_user(self) -> typing.Optional[typing.Union[User, Member]]:
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
    def user(self) -> typing.Union[User, Member]:
        """Union[:class:`.User`, class:`Member`]: The user that joined this server/group.."""
        user = self.get_user()
        if not user:
            raise NoData(self.user_id, 'joined user')
        return user


@define(slots=True)
class StatelessUserLeftSystemEvent(BaseSystemEvent):
    _user: typing.Union[User, Member, str] = field(repr=False, kw_only=True, alias='internal_user')

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, StatelessUserLeftSystemEvent) and self.user_id == other.user_id

    @property
    def user_id(self) -> str:
        """:class:`str`: The user's ID that left this server/group."""
        if isinstance(self._user, (User, Member)):
            return self._user.id
        return self._user

    def get_user(self) -> typing.Optional[typing.Union[User, Member]]:
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

    def get_user(self) -> typing.Optional[typing.Union[User, Member]]:
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
    def user(self) -> typing.Union[User, Member]:
        """Union[:class:`.User`, class:`Member`]: The user that left this server/group."""
        user = self.get_user()
        if not user:
            raise NoData(self.user_id, 'left user')
        return user


@define(slots=True)
class StatelessUserKickedSystemEvent(BaseSystemEvent):
    _user: typing.Union[User, Member, str] = field(repr=False, kw_only=True, alias='internal_user')

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, StatelessUserKickedSystemEvent) and self.user_id == other.user_id

    @property
    def user_id(self) -> str:
        """:class:`str`: The user's ID that was kicked from this server."""
        if isinstance(self._user, (User, Member)):
            return self._user.id
        return self._user

    def get_user(self) -> typing.Optional[typing.Union[User, Member]]:
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

    def get_user(self) -> typing.Optional[typing.Union[User, Member]]:
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
    def user(self) -> typing.Union[User, Member]:
        """Union[:class:`.User`, class:`Member`]: The user that was kicked from this server."""
        user = self.get_user()
        if not user:
            raise NoData(self.user_id, 'kicked user')
        return user


@define(slots=True)
class StatelessUserBannedSystemEvent(BaseSystemEvent):
    _user: typing.Union[User, Member, str] = field(repr=False, kw_only=True, alias='internal_user')

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, StatelessUserBannedSystemEvent) and self.user_id == other.user_id

    @property
    def user_id(self) -> str:
        """:class:`str`: The user's ID that was banned from this server."""
        if isinstance(self._user, (User, Member)):
            return self._user.id
        return self._user

    def get_user(self) -> typing.Optional[typing.Union[User, Member]]:
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

    def get_user(self) -> typing.Optional[typing.Union[User, Member]]:
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
    def user(self) -> typing.Union[User, Member]:
        """Union[:class:`.User`, class:`Member`]: The user that was banned from this server."""
        user = self.get_user()
        if not user:
            raise NoData(self.user_id, 'banned user')
        return user


@define(slots=True)
class StatelessChannelRenamedSystemEvent(BaseSystemEvent):
    name: str = field(repr=True, kw_only=True)
    """:class:`str`: The new name of this group."""

    _by: typing.Union[User, str] = field(repr=False, kw_only=True, alias='internal_by')

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

    def get_by(self) -> typing.Optional[User]:
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

    def get_by(self) -> typing.Optional[User]:
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
    _by: typing.Union[User, str] = field(repr=False, kw_only=True, alias='internal_by')

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

    def get_by(self) -> typing.Optional[User]:
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

    def get_by(self) -> typing.Optional[User]:
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
    _by: typing.Union[User, str] = field(repr=False, kw_only=True, alias='internal_by')

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, StatelessChannelIconChangedSystemEvent) and self.by_id == other.by_id

    @property
    def by_id(self) -> str:
        """:class:`str`: The user's ID that changed icon of this group."""
        if isinstance(self._by, User):
            return self._by.id
        return self._by

    def get_by(self) -> typing.Optional[User]:
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

    def get_by(self) -> typing.Optional[User]:
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
    _from: typing.Union[User, str] = field(repr=False, kw_only=True, alias='internal_from')
    _to: typing.Union[User, str] = field(repr=False, kw_only=True, alias='internal_to')

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

    def get_from(self) -> typing.Optional[User]:
        """Optional[:class:`.User`]: Tries to get user that was previous owner of this group."""
        if isinstance(self._from, User):
            return self._from

    @property
    def to_id(self) -> str:
        """:class:`str`: The user's ID that became owner of this group."""
        if isinstance(self._from, User):
            return self._from.id
        return self._from

    def get_to(self) -> typing.Optional[User]:
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

    def get_from(self) -> typing.Optional[User]:
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

    def get_to(self) -> typing.Optional[User]:
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

    _by: typing.Union[User, Member, str] = field(repr=False, kw_only=True, alias='internal_by')

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

    def get_by(self) -> typing.Optional[typing.Union[User, Member]]:
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

    def get_by(self) -> typing.Optional[typing.Union[User, Member]]:
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
    def by(self) -> typing.Union[User, Member]:
        """Union[:class:`.User`, class:`Member`]: The user that pinned a message."""
        by = self.get_by()
        if not by:
            raise NoData(self.by_id, 'user')
        return by


@define(slots=True)
class StatelessMessageUnpinnedSystemEvent(BaseSystemEvent):
    unpinned_message_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The ID of the message that was unpinned."""

    _by: typing.Union[User, Member, str] = field(repr=False, kw_only=True, alias='internal_by')

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

    def get_by(self) -> typing.Optional[typing.Union[User, Member]]:
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

    def get_by(self) -> typing.Optional[typing.Union[User, Member]]:
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
    def by(self) -> typing.Union[User, Member]:
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


@define(slots=True)
class StatelessCallStartedSystemEvent(BaseSystemEvent):
    _by: typing.Union[User, str] = field(repr=False, kw_only=True, alias='internal_by')

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, StatelessCallStartedSystemEvent) and self.by_id == other.by_id

    @property
    def by_id(self) -> str:
        """:class:`str`: The user's ID that started a call."""
        if isinstance(self._by, User):
            return self._by.id
        return self._by

    def get_by(self) -> typing.Optional[User]:
        """Optional[:class:`.User`]: Tries to get user that started a call."""
        if isinstance(self._by, User):
            return self._by

    def attach_state(self, message: Message, /) -> CallStartedSystemEvent:
        """:class:`.CallStartedSystemEvent`: Attach a state to system event.

        Parameters
        ----------
        message: :class:`.Message`
            The state to attach.
        """
        return CallStartedSystemEvent(
            message=message,
            internal_by=self._by,
        )

    @property
    def system_content(self) -> str:
        """:class:`str`: The displayed system's content."""

        by = self.get_by()
        if by is None:
            by = '<Unknown User>'

        return f'{by} started a call.'


@define(slots=True)
class CallStartedSystemEvent(StatelessCallStartedSystemEvent):
    message: Message = field(repr=False, kw_only=True, eq=False)
    """:class:`.Message`: The message that holds this system event."""

    def get_by(self) -> typing.Optional[User]:
        """Optional[:class:`.User`]: Tries to get user that started call."""
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
        """:class:`.User`: The user that started a call."""
        by = self.get_by()
        if not by:
            raise NoData(self.by_id, 'user')
        return by


StatelessSystemEvent = typing.Union[
    TextSystemEvent,
    StatelessUserAddedSystemEvent,
    StatelessUserRemovedSystemEvent,
    StatelessUserJoinedSystemEvent,
    StatelessUserLeftSystemEvent,
    StatelessUserKickedSystemEvent,
    StatelessUserBannedSystemEvent,
    StatelessChannelRenamedSystemEvent,
    StatelessChannelDescriptionChangedSystemEvent,
    StatelessChannelIconChangedSystemEvent,
    StatelessChannelOwnershipChangedSystemEvent,
    StatelessMessagePinnedSystemEvent,
    StatelessMessageUnpinnedSystemEvent,
    StatelessCallStartedSystemEvent,
]

SystemEvent = typing.Union[
    TextSystemEvent,
    UserAddedSystemEvent,
    UserRemovedSystemEvent,
    UserJoinedSystemEvent,
    UserLeftSystemEvent,
    UserKickedSystemEvent,
    UserBannedSystemEvent,
    ChannelRenamedSystemEvent,
    ChannelDescriptionChangedSystemEvent,
    ChannelIconChangedSystemEvent,
    ChannelOwnershipChangedSystemEvent,
    MessagePinnedSystemEvent,
    MessageUnpinnedSystemEvent,
    CallStartedSystemEvent,
]


@define(slots=True)
class Message(BaseMessage):
    """Represents a message in channel on Revolt."""

    nonce: typing.Optional[str] = field(repr=True, kw_only=True)
    """Optional[:class:`str`]: The unique value generated by client sending this message."""

    channel_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The channel's ID this message was sent in."""

    _author: typing.Union[User, Member, str] = field(repr=False, kw_only=True, alias='internal_author')

    webhook: typing.Optional[MessageWebhook] = field(repr=True, kw_only=True)
    """Optional[:class:`.MessageWebhook`]: The webhook that sent this message."""

    content: str = field(repr=True, kw_only=True)
    """:class:`str`: The message's content."""

    internal_system_event: typing.Optional[StatelessSystemEvent] = field(repr=True, kw_only=True)
    """Optional[:class:`.StatelessSystemEvent`]: The stateless system event information, occured in this message, if any."""

    internal_attachments: list[StatelessAsset] = field(repr=True, kw_only=True)
    """List[:class:`.StatelessAsset`]: The stateless attachments on this message."""

    edited_at: typing.Optional[datetime] = field(repr=True, kw_only=True)
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

    interactions: typing.Optional[MessageInteractions] = field(repr=True, kw_only=True)
    """Optional[:class:`.MessageInteractions`]: The information about how this message should be interacted with."""

    masquerade: typing.Optional[MessageMasquerade] = field(repr=True, kw_only=True)
    """Optional[:class:`.MessageMasquerade`]: The name and / or avatar overrides for this message."""

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

    def get_author(self) -> typing.Optional[typing.Union[User, Member]]:
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
    def author(self) -> typing.Union[User, Member]:
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
    def system_event(self) -> typing.Optional[SystemEvent]:
        """Optional[:class:`.SystemEvent`]: The system event information, occured in this message, if any."""
        if self.internal_system_event:
            return self.internal_system_event.attach_state(self)

    def is_silent(self) -> bool:
        """:class:`bool`: Whether the message suppresses push notifications."""
        return self.flags.suppress_notifications


Masquerade: typing.TypeAlias = MessageMasquerade

__all__ = (
    'Reply',
    'MessageInteractions',
    'MessageMasquerade',
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
    'StatelessCallStartedSystemEvent',
    'CallStartedSystemEvent',
    'StatelessSystemEvent',
    'SystemEvent',
    'Message',
    # backwards compatibilty
    'Masquerade',
)
