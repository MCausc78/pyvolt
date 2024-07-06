from __future__ import annotations

import typing as t

from .basic import Bool
from .files import File
from .permissions import Override, OverrideField


class SavedMessagesChannel(t.TypedDict):
    channel_type: t.Literal["SavedMessages"]
    _id: str
    user: str


class DirectMessageChannel(t.TypedDict):
    channel_type: t.Literal["DirectMessage"]
    _id: str
    active: bool
    recipients: list[str]
    last_message_id: t.NotRequired[str]


class GroupChannel(t.TypedDict):
    channel_type: t.Literal["Group"]
    _id: str
    name: str
    owner: str
    description: t.NotRequired[str]
    recipients: list[str]
    icon: t.NotRequired[File]
    last_message_id: t.NotRequired[str]
    permissions: t.NotRequired[int]
    nsfw: t.NotRequired[bool]


class TextChannel(t.TypedDict):
    channel_type: t.Literal["TextChannel"]
    _id: str
    server: str
    name: str
    description: t.NotRequired[str]
    icon: t.NotRequired[File]
    last_message_id: t.NotRequired[str]
    default_permissions: t.NotRequired[OverrideField]
    role_permissions: t.NotRequired[dict[str, OverrideField]]
    nsfw: t.NotRequired[bool]


class VoiceChannel(t.TypedDict):
    channel_type: t.Literal["VoiceChannel"]
    _id: str
    server: str
    name: str
    description: t.NotRequired[str]
    icon: t.NotRequired[File]
    default_permissions: t.NotRequired[OverrideField]
    role_permissions: t.NotRequired[dict[str, OverrideField]]
    nsfw: t.NotRequired[bool]


Channel = (
    SavedMessagesChannel
    | DirectMessageChannel
    | GroupChannel
    | TextChannel
    | VoiceChannel
)


class PartialChannel(t.TypedDict):
    name: t.NotRequired[str]
    owner: t.NotRequired[str]
    description: t.NotRequired[str]
    icon: t.NotRequired[File]
    nsfw: t.NotRequired[bool]
    active: t.NotRequired[bool]
    permissions: t.NotRequired[int]
    role_permissions: t.NotRequired[dict[str, OverrideField]]
    default_permissions: t.NotRequired[OverrideField]
    last_message_id: t.NotRequired[str]


FieldsChannel = t.Literal["Description", "Icon", "DefaultPermissions"]


class DataEditChannel(t.TypedDict):
    name: t.NotRequired[str]
    description: t.NotRequired[str]
    owner: t.NotRequired[str]
    icon: t.NotRequired[str]
    nsfw: t.NotRequired[bool]
    archived: t.NotRequired[bool]
    remove: t.NotRequired[list[FieldsChannel]]


class DataCreateGroup(t.TypedDict):
    name: str
    description: t.NotRequired[str | None]
    icon: t.NotRequired[str | None]
    users: t.NotRequired[list[str]]
    nsfw: t.NotRequired[bool | None]


LegacyServerChannelType = t.Literal["Text", "Voice"]


class DataCreateServerChannel(t.TypedDict):
    type: t.NotRequired[LegacyServerChannelType]
    name: str
    description: t.NotRequired[str | None]
    nsfw: t.NotRequired[bool]


class DataDefaultChannelPermissions(t.TypedDict):
    permissions: Override | int


class DataSetRolePermissions(t.TypedDict):
    permissions: Override


class OptionsChannelDelete(t.TypedDict):
    leave_silently: t.NotRequired[Bool]


class LegacyCreateVoiceUserResponse(t.TypedDict):
    token: str


__all__ = (
    "SavedMessagesChannel",
    "DirectMessageChannel",
    "GroupChannel",
    "TextChannel",
    "VoiceChannel",
    "Channel",
    "PartialChannel",
    "FieldsChannel",
    "DataEditChannel",
    "DataCreateGroup",
    "LegacyServerChannelType",
    "DataCreateServerChannel",
    "DataDefaultChannelPermissions",
    "DataSetRolePermissions",
    "OptionsChannelDelete",
    "LegacyCreateVoiceUserResponse",
)
