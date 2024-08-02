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


@define(slots=True)
class BaseWebhook(Base):
    """Representation of Revolt webhook."""

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
    name: UndefinedOr[str] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The new name of the webhook."""

    internal_avatar: UndefinedOr[StatelessAsset | None] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The new stateless avatar of the webhook."""

    permissions: UndefinedOr[Permissions] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The new permissions for the webhook."""

    @property
    def avatar(self) -> UndefinedOr[Asset | None]:
        """The new avatar of the webhook."""
        return self.internal_avatar and self.internal_avatar._stateful(self.state, 'avatars')


@define(slots=True)
class Webhook(BaseWebhook):
    name: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The name of the webhook."""

    internal_avatar: StatelessAsset | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The stateless avatar of the webhook."""

    channel_id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The channel this webhook belongs to."""

    permissions: Permissions = field(repr=True, hash=True, kw_only=True, eq=True)
    """The permissions for the webhook."""

    token: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The private token for the webhook."""

    def _update(self, data: PartialWebhook) -> None:
        if data.name is not UNDEFINED:
            self.name = data.name
        if data.internal_avatar is not UNDEFINED:
            self.internal_avatar = data.internal_avatar
        if data.permissions is not UNDEFINED:
            self.permissions = data.permissions

    @property
    def avatar(self) -> Asset | None:
        """Optional[:class:`Asset`]: The avatar of the webhook."""
        return self.internal_avatar and self.internal_avatar._stateful(self.state, 'avatars')


__all__ = (
    'BaseWebhook',
    'PartialWebhook',
    'Webhook',
)
