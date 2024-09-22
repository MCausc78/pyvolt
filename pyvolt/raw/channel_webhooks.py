from __future__ import annotations

import typing
import typing_extensions

from .files import File


class Webhook(typing.TypedDict):
    id: str
    name: str
    avatar: typing_extensions.NotRequired[File]
    channel_id: str
    permissions: int
    token: str | None


class PartialWebhook(typing.TypedDict):
    name: typing_extensions.NotRequired[str]
    avatar: typing_extensions.NotRequired[File]
    permissions: typing_extensions.NotRequired[int]


class MessageWebhook(typing.TypedDict):
    name: str
    avatar: str | None


class DataEditWebhook(typing.TypedDict):
    name: typing_extensions.NotRequired[str]
    avatar: typing_extensions.NotRequired[str]
    permissions: typing_extensions.NotRequired[int]
    remove: typing_extensions.NotRequired[list[FieldsWebhook]]


class ResponseWebhook(typing.TypedDict):
    id: str
    name: str
    avatar: str | None
    channel_id: str
    permissions: int


FieldsWebhook = typing.Literal['Avatar']


class CreateWebhookBody(typing.TypedDict):
    name: str
    avatar: typing_extensions.NotRequired[str | None]


__all__ = (
    'Webhook',
    'PartialWebhook',
    'MessageWebhook',
    'DataEditWebhook',
    'ResponseWebhook',
    'FieldsWebhook',
    'CreateWebhookBody',
)
