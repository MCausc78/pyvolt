from __future__ import annotations

from attrs import define, field

from . import (
    base,
    cdn,
    core,
    message as messages,
    permissions as permissions_,
)


@define(slots=True)
class BaseWebhook(base.Base):
    """Representation of Revolt webhook."""

    def _token(self) -> str | None:
        return None

    async def delete(self, *, by_token: bool = False) -> None:
        """|coro|

        Deletes a webhook. If webhook token wasn't given, the library will attempt delete webhook with bot/user token.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to delete the webhook.
        :class:`APIError`
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
        name: core.UndefinedOr[str] = core.UNDEFINED,
        avatar: core.UndefinedOr[str | None] = core.UNDEFINED,
        permissions: core.UndefinedOr[permissions_.Permissions] = core.UNDEFINED,
    ) -> Webhook:
        """|coro|

        Edits a webhook. If webhook token wasn't given, the library will attempt edit webhook with bot/user token.

        Parameters
        ----------
        name: :class:`UndefinedOr`[:class:`str` | `None`]
            New webhook name. Should be between 1 and 32 chars long.
        avatar: :class:`UndefinedOr`[:class:`str` | `None`]
            New webhook avatar. Pass attachment ID given by Autumn.
        permissions: :class:`UndefinedOr`[:class:`permission.Permissions`]
            New webhook permissions.

        Raises
        ------
        :class:`Forbidden`
            You do not have permissions to edit the webhook.
        :class:`APIError`
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
            return await self.state.http.edit_webhook(
                self.id, name=name, avatar=avatar, permissions=permissions
            )

    async def execute(
        self,
        content: str | None = None,
        *,
        nonce: str | None = None,
        attachments: list[cdn.ResolvableResource] | None = None,
        replies: list[messages.Reply | core.ResolvableULID] | None = None,
        embeds: list[messages.SendableEmbed] | None = None,
        masquerade: messages.Masquerade | None = None,
        interactions: messages.Interactions | None = None,
    ) -> messages.Message:
        """|coro|

        Executes a webhook and returns a message.

        Returns
        -------
        :class:`Message`
            The message sent.
        """
        token = self._token()
        assert token, "No token"
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
    name: core.UndefinedOr[str] = field(repr=True, hash=True, kw_only=True, eq=True)
    """The new name of the webhook."""

    internal_avatar: core.UndefinedOr[cdn.StatelessAsset | None] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The new stateless avatar of the webhook."""

    permissions: core.UndefinedOr[permissions_.Permissions] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The new permissions for the webhook."""

    @property
    def avatar(self) -> core.UndefinedOr[cdn.Asset | None]:
        """The new avatar of the webhook."""
        return self.internal_avatar and self.internal_avatar._stateful(
            self.state, "avatars"
        )


@define(slots=True)
class Webhook(BaseWebhook):
    name: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The name of the webhook."""

    internal_avatar: cdn.StatelessAsset | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The stateless avatar of the webhook."""

    channel_id: core.ULID = field(repr=True, hash=True, kw_only=True, eq=True)
    """The channel this webhook belongs to."""

    permissions: permissions_.Permissions = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The permissions for the webhook."""

    token: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The private token for the webhook."""

    def _update(self, data: PartialWebhook) -> None:
        if core.is_defined(data.name):
            self.name = data.name
        if core.is_defined(data.internal_avatar):
            self.internal_avatar = data.internal_avatar
        if core.is_defined(data.permissions):
            self.permissions = data.permissions

    @property
    def avatar(self) -> cdn.Asset | None:
        """The avatar of the webhook."""
        return self.internal_avatar and self.internal_avatar._stateful(
            self.state, "avatars"
        )


__all__ = (
    "BaseWebhook",
    "Webhook",
)
