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

from .base import Base
from .cdn import StatelessAsset, Asset, ResolvableResource
from .core import (
    UNDEFINED,
    UndefinedOr,
    ULIDOr,
)
from .message import (
    Reply,
    Interactions,
    Masquerade,
    SendableEmbed,
    BaseMessage,
    Message,
)
from .permissions import Permissions

_new_permissions = Permissions.__new__


@define(slots=True)
class BaseWebhook(Base):
    """Representation of Revolt webhook."""

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, BaseWebhook) and self.id == other.id

    def _token(self) -> str | None:
        return None

    async def delete(self, *, by_token: bool = False) -> None:
        """|coro|

        Deletes a webhook. If webhook token wasn't given, the library will attempt delete webhook with bot/user token.

        Raises
        ------
        Forbidden
            You do not have permissions to delete the webhook.
        HTTPException
            Deleting the webhook failed.
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
        avatar: UndefinedOr[str | None] = UNDEFINED,
        permissions: UndefinedOr[Permissions] = UNDEFINED,
    ) -> Webhook:
        """|coro|

        Edits a webhook. If webhook token wasn't given, the library will attempt edit webhook with current bot/user token.

        Parameters
        ----------
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
        content: str | None = None,
        *,
        nonce: str | None = None,
        attachments: list[ResolvableResource] | None = None,
        replies: list[Reply | ULIDOr[BaseMessage]] | None = None,
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
        token = self._token()
        assert token, 'No token'
        return await self.state.http.execute_webhook(
            self.id,
            token,
            content,
            nonce=nonce,
            attachments=attachments,
            replies=replies,
            embeds=embeds,
            masquerade=masquerade,
            interactions=interactions,
        )


@define(slots=True)
class PartialWebhook(BaseWebhook):
    """Represents a partial webhook on Revolt.

    Unmodified fields will have ``UNDEFINED`` value.
    """

    name: UndefinedOr[str] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The new webhook's name."""

    internal_avatar: UndefinedOr[StatelessAsset | None] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The new webhook's stateless avatar."""

    raw_permissions: UndefinedOr[int] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The new webhook's permissions raw value."""

    @property
    def avatar(self) -> UndefinedOr[Asset | None]:
        """:class:`UndefinedOr`[Optional[:class:`Asset`]]: The new avatar of the webhook."""
        return self.internal_avatar and self.internal_avatar._stateful(self.state, 'avatars')

    @property
    def permissions(self) -> UndefinedOr[Permissions]:
        """:class:`UndefinedOr`[:clsas:`Permissions`]: The new webhook's permissions."""
        if self.raw_permissions is UNDEFINED:
            return self.raw_permissions
        ret = _new_permissions(Permissions)
        ret.value = self.raw_permissions
        return ret


@define(slots=True)
class Webhook(BaseWebhook):
    """Represents a webhook on Revolt."""

    name: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The webhook's name."""

    internal_avatar: StatelessAsset | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The webhook's stateless avatar."""

    channel_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The channel the webhook belongs to."""

    raw_permissions: int = field(repr=True, hash=True, kw_only=True, eq=True)
    """The webhook's permissions raw value."""

    token: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The webhook's private token."""

    def locally_update(self, data: PartialWebhook, /) -> None:
        """Locally updates webhook with provided data.

        .. warn::
            This is called by library internally to keep cache up to date.

        Parameters
        ----------
        data: :class:`PartialWebhook`
            The data to update webhook with.
        """
        if data.name is not UNDEFINED:
            self.name = data.name
        if data.internal_avatar is not UNDEFINED:
            self.internal_avatar = data.internal_avatar
        if data.raw_permissions is not UNDEFINED:
            self.raw_permissions = data.raw_permissions

    @property
    def avatar(self) -> Asset | None:
        """Optional[:class:`Asset`]: The webhook's avatar."""
        return self.internal_avatar and self.internal_avatar._stateful(self.state, 'avatars')

    @property
    def permissions(self) -> Permissions:
        """:class:`Permissions`: The webhook's permissions."""
        ret = _new_permissions(Permissions)
        ret.value = self.raw_permissions
        return ret


__all__ = (
    'BaseWebhook',
    'PartialWebhook',
    'Webhook',
)
