from __future__ import annotations

import typing as t

from . import files


class Webhook(t.TypedDict):
    id: str
    name: str
    avatar: t.NotRequired[files.File]
    channel_id: str
    permissions: int
    token: str | None


class PartialWebhook(t.TypedDict):
    name: t.NotRequired[str]
    avatar: t.NotRequired[files.File]
    permissions: t.NotRequired[int]


class MessageWebhook(t.TypedDict):
    name: str
    avatar: str | None


class DataEditWebhook(t.TypedDict):
    name: t.NotRequired[str]
    avatar: t.NotRequired[str]
    permissions: t.NotRequired[int]
    remove: t.NotRequired[list[FieldsWebhook]]


class ResponseWebhook(t.TypedDict):
    id: str
    name: str
    avatar: str | None
    channel_id: str
    permissions: int


FieldsWebhook = t.Literal["Avatar"]


class CreateWebhookBody(t.TypedDict):
    name: str
    avatar: t.NotRequired[str | None]


__all__ = (
    "Webhook",
    "PartialWebhook",
    "MessageWebhook",
    "DataEditWebhook",
    "ResponseWebhook",
    "FieldsWebhook",
    "CreateWebhookBody",
)
