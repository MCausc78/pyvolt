from __future__ import annotations

import typing
import typing_extensions

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
    last_message_id: typing_extensions.NotRequired[str]


class GroupChannel(typing.TypedDict):
    channel_type: typing.Literal['Group']
    _id: str
    name: str
    owner: str
    description: typing_extensions.NotRequired[str]
    recipients: list[str]
    icon: typing_extensions.NotRequired[File]
    last_message_id: typing_extensions.NotRequired[str]
    permissions: typing_extensions.NotRequired[int]
    nsfw: typing_extensions.NotRequired[bool]


class TextChannel(typing.TypedDict):
    channel_type: typing.Literal['TextChannel']
    _id: str
    server: str
    name: str
    description: typing_extensions.NotRequired[str]
    icon: typing_extensions.NotRequired[File]
    last_message_id: typing_extensions.NotRequired[str]
    default_permissions: typing_extensions.NotRequired[OverrideField]
    role_permissions: typing_extensions.NotRequired[dict[str, OverrideField]]
    nsfw: typing_extensions.NotRequired[bool]


class VoiceChannel(typing.TypedDict):
    channel_type: typing.Literal['VoiceChannel']
    _id: str
    server: str
    name: str
    description: typing_extensions.NotRequired[str]
    icon: typing_extensions.NotRequired[File]
    default_permissions: typing_extensions.NotRequired[OverrideField]
    role_permissions: typing_extensions.NotRequired[dict[str, OverrideField]]
    nsfw: typing_extensions.NotRequired[bool]


PrivateChannel = SavedMessagesChannel | DirectMessageChannel | GroupChannel
ServerChannel = TextChannel | VoiceChannel
Channel = PrivateChannel | ServerChannel


class PartialChannel(typing.TypedDict):
    name: typing_extensions.NotRequired[str]
    owner: typing_extensions.NotRequired[str]
    description: typing_extensions.NotRequired[str]
    icon: typing_extensions.NotRequired[File]
    nsfw: typing_extensions.NotRequired[bool]
    active: typing_extensions.NotRequired[bool]
    permissions: typing_extensions.NotRequired[int]
    role_permissions: typing_extensions.NotRequired[dict[str, OverrideField]]
    default_permissions: typing_extensions.NotRequired[OverrideField]
    last_message_id: typing_extensions.NotRequired[str]


FieldsChannel = typing.Literal['Description', 'Icon', 'DefaultPermissions']


class DataEditChannel(typing.TypedDict):
    name: typing_extensions.NotRequired[str]
    description: typing_extensions.NotRequired[str]
    owner: typing_extensions.NotRequired[str]
    icon: typing_extensions.NotRequired[str]
    nsfw: typing_extensions.NotRequired[bool]
    archived: typing_extensions.NotRequired[bool]
    remove: typing_extensions.NotRequired[list[FieldsChannel]]


class DataCreateGroup(typing.TypedDict):
    name: str
    description: typing_extensions.NotRequired[str | None]
    icon: typing_extensions.NotRequired[str | None]
    users: typing_extensions.NotRequired[list[str]]
    nsfw: typing_extensions.NotRequired[bool | None]


LegacyServerChannelType = typing.Literal['Text', 'Voice']


class DataCreateServerChannel(typing.TypedDict):
    type: typing_extensions.NotRequired[LegacyServerChannelType]
    name: str
    description: typing_extensions.NotRequired[str | None]
    nsfw: typing_extensions.NotRequired[bool]


class DataDefaultChannelPermissions(typing.TypedDict):
    permissions: Override | int


class DataSetRolePermissions(typing.TypedDict):
    permissions: Override


class OptionsChannelDelete(typing.TypedDict):
    leave_silently: typing_extensions.NotRequired[Bool]


class LegacyCreateVoiceUserResponse(typing.TypedDict):
    token: str


__all__ = (
    'SavedMessagesChannel',
    'DirectMessageChannel',
    'GroupChannel',
    'TextChannel',
    'VoiceChannel',
    'PrivateChannel',
    'ServerChannel',
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
