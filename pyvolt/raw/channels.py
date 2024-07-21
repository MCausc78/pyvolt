from __future__ import annotations

import typing

from .basic import Bool
from .files import File
from .permissions import Override, OverrideField


class SavedMessagesChannel(typing.TypedDict):
    channel_type: typing.Literal['SavedMessages']
    _id: str
    user: str


class DirectMessageChannel(typing.TypedDict):
    channel_type: typing.Literal['DirectMessage']
    _id: str
    active: bool
    recipients: list[str]
    last_message_id: typing.NotRequired[str]


class GroupChannel(typing.TypedDict):
    channel_type: typing.Literal['Group']
    _id: str
    name: str
    owner: str
    description: typing.NotRequired[str]
    recipients: list[str]
    icon: typing.NotRequired[File]
    last_message_id: typing.NotRequired[str]
    permissions: typing.NotRequired[int]
    nsfw: typing.NotRequired[bool]


class TextChannel(typing.TypedDict):
    channel_type: typing.Literal['TextChannel']
    _id: str
    server: str
    name: str
    description: typing.NotRequired[str]
    icon: typing.NotRequired[File]
    last_message_id: typing.NotRequired[str]
    default_permissions: typing.NotRequired[OverrideField]
    role_permissions: typing.NotRequired[dict[str, OverrideField]]
    nsfw: typing.NotRequired[bool]


class VoiceChannel(typing.TypedDict):
    channel_type: typing.Literal['VoiceChannel']
    _id: str
    server: str
    name: str
    description: typing.NotRequired[str]
    icon: typing.NotRequired[File]
    default_permissions: typing.NotRequired[OverrideField]
    role_permissions: typing.NotRequired[dict[str, OverrideField]]
    nsfw: typing.NotRequired[bool]


Channel = SavedMessagesChannel | DirectMessageChannel | GroupChannel | TextChannel | VoiceChannel


class PartialChannel(typing.TypedDict):
    name: typing.NotRequired[str]
    owner: typing.NotRequired[str]
    description: typing.NotRequired[str]
    icon: typing.NotRequired[File]
    nsfw: typing.NotRequired[bool]
    active: typing.NotRequired[bool]
    permissions: typing.NotRequired[int]
    role_permissions: typing.NotRequired[dict[str, OverrideField]]
    default_permissions: typing.NotRequired[OverrideField]
    last_message_id: typing.NotRequired[str]


FieldsChannel = typing.Literal['Description', 'Icon', 'DefaultPermissions']


class DataEditChannel(typing.TypedDict):
    name: typing.NotRequired[str]
    description: typing.NotRequired[str]
    owner: typing.NotRequired[str]
    icon: typing.NotRequired[str]
    nsfw: typing.NotRequired[bool]
    archived: typing.NotRequired[bool]
    remove: typing.NotRequired[list[FieldsChannel]]


class DataCreateGroup(typing.TypedDict):
    name: str
    description: typing.NotRequired[str | None]
    icon: typing.NotRequired[str | None]
    users: typing.NotRequired[list[str]]
    nsfw: typing.NotRequired[bool | None]


LegacyServerChannelType = typing.Literal['Text', 'Voice']


class DataCreateServerChannel(typing.TypedDict):
    type: typing.NotRequired[LegacyServerChannelType]
    name: str
    description: typing.NotRequired[str | None]
    nsfw: typing.NotRequired[bool]


class DataDefaultChannelPermissions(typing.TypedDict):
    permissions: Override | int


class DataSetRolePermissions(typing.TypedDict):
    permissions: Override


class OptionsChannelDelete(typing.TypedDict):
    leave_silently: typing.NotRequired[Bool]


class LegacyCreateVoiceUserResponse(typing.TypedDict):
    token: str


__all__ = (
    'SavedMessagesChannel',
    'DirectMessageChannel',
    'GroupChannel',
    'TextChannel',
    'VoiceChannel',
    'Channel',
    'PartialChannel',
    'FieldsChannel',
    'DataEditChannel',
    'DataCreateGroup',
    'LegacyServerChannelType',
    'DataCreateServerChannel',
    'DataDefaultChannelPermissions',
    'DataSetRolePermissions',
    'OptionsChannelDelete',
    'LegacyCreateVoiceUserResponse',
)
