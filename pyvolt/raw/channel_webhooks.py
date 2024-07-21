from __future__ import annotations

import typing

from .files import File


class Webhook(typing.TypedDict):
    id: str
    name: str
    avatar: typing.NotRequired[File]
    channel_id: str
    permissions: int
    token: str | None


class PartialWebhook(typing.TypedDict):
    name: typing.NotRequired[str]
    avatar: typing.NotRequired[File]
    permissions: typing.NotRequired[int]


class MessageWebhook(typing.TypedDict):
    name: str
    avatar: str | None


class DataEditWebhook(typing.TypedDict):
    name: typing.NotRequired[str]
    avatar: typing.NotRequired[str]
    permissions: typing.NotRequired[int]
    remove: typing.NotRequired[list[FieldsWebhook]]


class ResponseWebhook(typing.TypedDict):
    id: str
    name: str
    avatar: str | None
    channel_id: str
    permissions: int


FieldsWebhook = typing.Literal['Avatar']


class CreateWebhookBody(typing.TypedDict):
    name: str
    avatar: typing.NotRequired[str | None]


__all__ = (
    'Webhook',
    'PartialWebhook',
    'MessageWebhook',
    'DataEditWebhook',
    'ResponseWebhook',
    'FieldsWebhook',
    'CreateWebhookBody',
)
