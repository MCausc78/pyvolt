from __future__ import annotations

import typing
import typing_extensions

from .files import File


class Webhook(typing.TypedDict):
    id: str
    name: str
    avatar: typing_extensions.NotRequired[File]
    creator_id: str  # Only available since API v0.7.17
    channel_id: str
    permissions: int
    token: typing.Optional[str]


class PartialWebhook(typing.TypedDict):
    name: typing_extensions.NotRequired[str]
    avatar: typing_extensions.NotRequired[File]
    permissions: typing_extensions.NotRequired[int]


class MessageWebhook(typing.TypedDict):
    name: str
    avatar: typing.Optional[str]


class DataEditWebhook(typing.TypedDict):
    name: typing_extensions.NotRequired[str]
    avatar: typing_extensions.NotRequired[str]
    permissions: typing_extensions.NotRequired[int]
    remove: typing_extensions.NotRequired[list[FieldsWebhook]]


class ResponseWebhook(typing.TypedDict):
    id: str
    name: str
    avatar: typing.Optional[str]
    channel_id: str
    permissions: int


FieldsWebhook = typing.Literal['Avatar']


class CreateWebhookBody(typing.TypedDict):
    name: str
    avatar: typing_extensions.NotRequired[typing.Optional[str]]
