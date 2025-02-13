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

from attrs import define, field

from .base import Base
from .cdn import StatelessAsset, Asset, ResolvableResource
from .core import (
    UNDEFINED,
    UndefinedOr,
    ULIDOr,
)
from .message import (
    Reply,
    MessageInteractions,
    MessageMasquerade,
    SendableEmbed,
    BaseMessage,
    Message,
)
from .permissions import Permissions

_new_permissions = Permissions.__new__


@define(slots=True)
class BaseWebhook(Base):
    """Represents a webhook on Revolt."""

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, BaseWebhook) and self.id == other.id

    def _token(self) -> typing.Optional[str]:
        return None

    async def delete(self, *, by_token: bool = False) -> None:
        """|coro|

        Deletes the webhook.

        Parameters
        ----------
        by_token: :class:`bool`
            Whether to use webhook token, if possible.

            You must have :attr:`~Permissions.manage_webhooks` to provide ``False``.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------+---------------------------------------------------------------------------+
            | Value                | Reason                                                                    |
            +----------------------+---------------------------------------------------------------------------+
            | ``InvalidSession``   | The current bot/user token is invalid.                                    |
            +----------------------+---------------------------------------------------------------------------+
            | ``NotAuthenticated`` | The webhook token is invalid. Only applicable when ``token`` is provided. |
            +----------------------+---------------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+----------------------------+
            | Value        | Reason                     |
            +--------------+----------------------------+
            | ``NotFound`` | The webhook was not found. |
            +--------------+----------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """

        if by_token:
            token = self._token()
            return await self.state.http.delete_webhook(self.id, token=token)
        else:
            return await self.state.http.delete_webhook(self.id)

    async def edit(
        self,
        *,
        by_token: bool = False,
        name: UndefinedOr[str] = UNDEFINED,
        avatar: UndefinedOr[typing.Optional[ResolvableResource]] = UNDEFINED,
        permissions: UndefinedOr[Permissions] = UNDEFINED,
    ) -> Webhook:
        """|coro|

        Edits the webhook.

        Parameters
        ----------
        by_token: :class:`bool`
            Whether to use webhook token, if possible.

            You must have :attr:`~Permissions.manage_webhooks` to provide ``False``.
        name: UndefinedOr[:class:`str`]
            The new webhook name. Must be between 1 and 32 chars long.
        avatar: UndefinedOr[Optional[:class:`.ResolvableResource`]]
            The new webhook avatar.
        permissions: UndefinedOr[:class:`.Permissions`]
            The new webhook permissions.

        Raises
        ------
        :class:`HTTPException`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------+--------------------------+
            | Value                | Reason                   |
            +----------------------+--------------------------+
            | ``FailedValidation`` | The payload was invalid. |
            +----------------------+--------------------------+
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +----------------------+---------------------------------------------------------------------------+
            | Value                | Reason                                                                    |
            +----------------------+---------------------------------------------------------------------------+
            | ``InvalidSession``   | The current bot/user token is invalid.                                    |
            +----------------------+---------------------------------------------------------------------------+
            | ``NotAuthenticated`` | The webhook token is invalid. Only applicable when ``by_`` is provided. |
            +----------------------+---------------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+---------------------------------+
            | Value        | Reason                          |
            +--------------+---------------------------------+
            | ``NotFound`` | The webhook/file was not found. |
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
            The newly updated webhook.
        """

        if by_token:
            token = self._token()

            return await self.state.http.edit_webhook(
                self.id,
                token=token,
                name=name,
                avatar=avatar,
                permissions=permissions,
            )
        else:
            return await self.state.http.edit_webhook(self.id, name=name, avatar=avatar, permissions=permissions)

    async def execute(
        self,
        content: typing.Optional[str] = None,
        *,
        nonce: typing.Optional[str] = None,
        attachments: typing.Optional[list[ResolvableResource]] = None,
        replies: typing.Optional[list[typing.Union[Reply, ULIDOr[BaseMessage]]]] = None,
        embeds: typing.Optional[list[SendableEmbed]] = None,
        masquerade: typing.Optional[MessageMasquerade] = None,
        interactions: typing.Optional[MessageInteractions] = None,
        silent: typing.Optional[bool] = None,
        mention_everyone: typing.Optional[bool] = None,
        mention_online: typing.Optional[bool] = None,
    ) -> Message:
        """|coro|

        Executes a webhook.

        The webhook must have :attr:`~Permissions.send_messages` to do this.

        If message mentions '@everyone' or '@here', the webhook must have :attr:`~Permissions.mention_everyone` to do that.

        If message mentions any roles, the webhook must have :attr:`~Permissions.mention_roles` to do that.

        Parameters
        ----------
        webhook: ULIDOr[:class:`.BaseWebhook`]
            The webhook to execute.
        token: :class:`str`
            The webhook token.
        content: Optional[:class:`str`]
            The message content.
        nonce: Optional[:class:`str`]
            The message nonce.
        attachments: Optional[List[:class:`.ResolvableResource`]]
            The attachments to send the message with.

            Webhook must have :attr:`~Permissions.upload_files` to provide this.
        replies: Optional[List[Union[:class:`.Reply`, ULIDOr[:class:`.BaseMessage`]]]]
            The message replies.
        embeds: Optional[List[:class:`.SendableEmbed`]]
            The embeds to send the message with.

            Webhook must have :attr:`~Permissions.send_embeds` to provide this.
        masquearde: Optional[:class:`.MessagesMasquerade`]
            The masquerade for the message.

            Webhook must have :attr:`~Permissions.use_masquerade` to provide this.

            If :attr:`.Masquerade.color` is provided, :attr:`~Permissions.use_masquerade` is also required.
        interactions: Optional[:class:`.MessageInteractions`]
            The message interactions.

            If :attr:`.MessageInteractions.reactions` is provided, :attr:`~Permissions.react` is required.
        silent: Optional[:class:`bool`]
            Whether to suppress notifications or not.
        mention_everyone: Optional[:class:`bool`]
            Whether to mention all users who can see the channel. This cannot be mixed with ``mention_online`` parameter.
        mention_online: Optional[:class:`bool`]
            Whether to mention all users who are online and can see the channel. This cannot be mixed with ``mention_everyone`` parameter.

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

            +----------------------+-------------------------------+
            | Value                | Reason                        |
            +----------------------+-------------------------------+
            | ``NotAuthenticated`` | The webhook token is invalid. |
            +----------------------+-------------------------------+
        :class:`Forbidden`
            Possible values for :attr:`~HTTPException.type`:

            +-----------------------+------------------------------------------------------------------+
            | Value                 | Reason                                                           |
            +-----------------------+------------------------------------------------------------------+
            | ``MissingPermission`` | The webhook do not have the proper permissions to send messages. |
            +-----------------------+------------------------------------------------------------------+
        :class:`NotFound`
            Possible values for :attr:`~HTTPException.type`:

            +--------------+-----------------------------------------------+
            | Value        | Reason                                        |
            +--------------+-----------------------------------------------+
            | ``NotFound`` | The channel/file/reply/webhook was not found. |
            +--------------+-----------------------------------------------+
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

        token = self._token()
        assert token is not None, 'No token'
        return await self.state.http.execute_webhook(
            self.id,
            token,
            content=content,
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


@define(slots=True)
class PartialWebhook(BaseWebhook):
    """Represents a partial webhook on Revolt.

    Unmodified fields will have :data:`.UNDEFINED` as their value.
    """

    name: UndefinedOr[str] = field(repr=True, hash=True, kw_only=True, eq=True)
    """UndefinedOr[:class:`str`]: The new webhook's name."""

    internal_avatar: UndefinedOr[typing.Optional[StatelessAsset]] = field(repr=True, hash=True, kw_only=True, eq=True)
    """UndefinedOr[Optional[:class:`.StatelessAsset`]]: The new webhook's stateless avatar."""

    raw_permissions: UndefinedOr[int] = field(repr=True, hash=True, kw_only=True, eq=True)
    """:class:`int`: The new webhook's permissions raw value."""

    @property
    def avatar(self) -> UndefinedOr[typing.Optional[Asset]]:
        """UndefinedOr[Optional[:class:`.Asset`]]: The new avatar of the webhook."""
        return self.internal_avatar and self.internal_avatar.attach_state(self.state, 'avatars')

    @property
    def permissions(self) -> UndefinedOr[Permissions]:
        """UndefinedOr[:class:`.Permissions`]: The new webhook's permissions."""
        if self.raw_permissions is UNDEFINED:
            return self.raw_permissions
        ret = _new_permissions(Permissions)
        ret.value = self.raw_permissions
        return ret


@define(slots=True)
class Webhook(BaseWebhook):
    """Represents a webhook on Revolt."""

    name: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """:class:`str`: The webhook's name."""

    internal_avatar: typing.Optional[StatelessAsset] = field(repr=True, hash=True, kw_only=True, eq=True)
    """Optional[:class:`.StatelessAsset`]: The webhook's stateless avatar."""

    creator_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """:class:`str`: The user's ID who created this webhook.
    
    .. warning::

        This is available only since API v0.7.17 and only not from ``GET /webhooks/{webhook.id}`` endpoints.
        The attribute will be empty string if unavailable.
    """

    channel_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """:class:`str`: The channel's ID the webhook in."""

    raw_permissions: int = field(repr=True, hash=True, kw_only=True, eq=True)
    """:class:`int`: The webhook's permissions raw value."""

    token: typing.Optional[str] = field(repr=True, hash=True, kw_only=True, eq=True)
    """Optional[:class:`str`]: The webhook's private token."""

    def locally_update(self, data: PartialWebhook, /) -> None:
        """Locally updates webhook with provided data.

        .. warning::

            This is called by library internally to keep cache up to date.

        Parameters
        ----------
        data: :class:`.PartialWebhook`
            The data to update webhook with.
        """
        if data.name is not UNDEFINED:
            self.name = data.name
        if data.internal_avatar is not UNDEFINED:
            self.internal_avatar = data.internal_avatar
        if data.raw_permissions is not UNDEFINED:
            self.raw_permissions = data.raw_permissions

    @property
    def avatar(self) -> typing.Optional[Asset]:
        """Optional[:class:`.Asset`]: The webhook's avatar."""
        return self.internal_avatar and self.internal_avatar.attach_state(self.state, 'avatars')

    @property
    def permissions(self) -> Permissions:
        """:class:`.Permissions`: The webhook's permissions."""
        ret = _new_permissions(Permissions)
        ret.value = self.raw_permissions
        return ret


__all__ = (
    'BaseWebhook',
    'PartialWebhook',
    'Webhook',
)
