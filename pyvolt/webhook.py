from __future__ import annotations

from attrs import define, field

from . import cdn
from .base import Base
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

        Edits a webhook. If webhook token wasn't given, the library will attempt edit webhook with bot/user token.

        Parameters
        ----------
        name: :class:`UndefinedOr`[:class:`str` | `None`]
            New webhook name. Should be between 1 and 32 chars long.
        avatar: :class:`UndefinedOr`[:class:`str` | `None`]
            New webhook avatar. Pass attachment ID given by Autumn.
        permissions: :class:`UndefinedOr`[:class:`Permissions`]
            New webhook permissions.

        Raises
        ------
        Forbidden
            You do not have permissions to edit the webhook.
        HTTPException
            Editing the webhook failed.
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
        attachments: list[cdn.ResolvableResource] | None = None,
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

    internal_avatar: UndefinedOr[cdn.StatelessAsset | None] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The new stateless avatar of the webhook."""

    permissions: UndefinedOr[Permissions] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The new permissions for the webhook."""

    @property
    def avatar(self) -> UndefinedOr[cdn.Asset | None]:
        """The new avatar of the webhook."""
        return self.internal_avatar and self.internal_avatar._stateful(self.state, 'avatars')


@define(slots=True)
class Webhook(BaseWebhook):
    name: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The name of the webhook."""

    internal_avatar: cdn.StatelessAsset | None = field(repr=True, hash=True, kw_only=True, eq=True)
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
    def avatar(self) -> cdn.Asset | None:
        """The avatar of the webhook."""
        return self.internal_avatar and self.internal_avatar._stateful(self.state, 'avatars')


__all__ = (
    'BaseWebhook',
    'PartialWebhook',
    'Webhook',
)
