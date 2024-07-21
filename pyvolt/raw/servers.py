from __future__ import annotations

import typing

from .basic import Bool
from .channels import Channel
from .files import File
from .permissions import Override, OverrideField


# class BaseServer(t.Generic[C], typing.TypedDict):
class BaseServer(typing.TypedDict):
    _id: str
    owner: str
    name: str
    description: typing.NotRequired[str]
    # channels: list[C]
    categories: typing.NotRequired[list[Category]]
    system_messages: typing.NotRequired[SystemMessageChannels]
    roles: typing.NotRequired[dict[str, Role]]
    default_permissions: int
    icon: typing.NotRequired[File]
    banner: typing.NotRequired[File]
    flags: typing.NotRequired[int]
    nsfw: typing.NotRequired[bool]
    analytics: typing.NotRequired[bool]
    discoverable: typing.NotRequired[bool]


class Server(BaseServer):
    channels: list[str]


class PartialServer(typing.TypedDict):
    owner: typing.NotRequired[str]
    name: typing.NotRequired[str]
    description: typing.NotRequired[str]
    channels: typing.NotRequired[list[str]]
    categories: typing.NotRequired[list[Category]]
    system_messages: typing.NotRequired[SystemMessageChannels]
    default_permissions: typing.NotRequired[int]
    icon: typing.NotRequired[File]
    banner: typing.NotRequired[File]
    flags: typing.NotRequired[int]
    discoverable: typing.NotRequired[bool]
    analytics: typing.NotRequired[bool]


class Role(typing.TypedDict):
    name: str
    permissions: OverrideField
    colour: typing.NotRequired[str]
    hoist: typing.NotRequired[bool]
    rank: int


class PartialRole(typing.TypedDict):
    name: typing.NotRequired[str]
    permissions: typing.NotRequired[OverrideField]
    colour: typing.NotRequired[str]
    hoist: typing.NotRequired[bool]
    rank: typing.NotRequired[int]


FieldsServer = typing.Literal['Description', 'Categories', 'SystemMessages', 'Icon', 'Banner']
FieldsRole = typing.Literal['Colour']


class Category(typing.TypedDict):
    id: str
    title: str
    channels: list[str]


class SystemMessageChannels(typing.TypedDict):
    user_joined: typing.NotRequired[str]
    user_left: typing.NotRequired[str]
    user_kicked: typing.NotRequired[str]
    user_banned: typing.NotRequired[str]


class DataCreateServer(typing.TypedDict):
    name: str
    description: typing.NotRequired[str | None]
    nsfw: typing.NotRequired[bool]


class DataCreateRole(typing.TypedDict):
    name: str
    rank: typing.NotRequired[int | None]


class NewRoleResponse(typing.TypedDict):
    id: str
    role: Role


class CreateServerLegacyResponse(typing.TypedDict):
    server: Server
    channels: list[Channel]


class OptionsFetchServer(typing.TypedDict):
    include_channels: typing.NotRequired[Bool]


class ServerWithChannels(BaseServer):
    channels: list[Channel]


FetchServerResponse = Server | ServerWithChannels


class DataEditServer(typing.TypedDict):
    name: typing.NotRequired[str]
    description: typing.NotRequired[str]
    icon: typing.NotRequired[str]
    banner: typing.NotRequired[str]
    categories: typing.NotRequired[list[Category]]
    system_messages: typing.NotRequired[SystemMessageChannels]
    flags: typing.NotRequired[int]
    discoverable: typing.NotRequired[bool]
    analytics: typing.NotRequired[bool]
    remove: typing.NotRequired[list[FieldsServer]]


class DataEditRole(typing.TypedDict):
    name: typing.NotRequired[str]
    colour: typing.NotRequired[str]
    hoist: typing.NotRequired[bool]
    rank: typing.NotRequired[int]
    remove: typing.NotRequired[list[FieldsRole]]


class DataSetServerRolePermission(typing.TypedDict):
    permissions: Override


class OptionsServerDelete(typing.TypedDict):
    leave_silently: typing.NotRequired[Bool]


__all__ = (
    'BaseServer',
    'Server',
    'PartialServer',
    'Role',
    'PartialRole',
    'FieldsServer',
    'FieldsRole',
    'Category',
    'SystemMessageChannels',
    'DataCreateServer',
    'DataCreateRole',
    'NewRoleResponse',
    'CreateServerLegacyResponse',
    'OptionsFetchServer',
    'ServerWithChannels',
    'FetchServerResponse',
    'DataEditServer',
    'DataEditRole',
    'DataSetServerRolePermission',
    'OptionsServerDelete',
)
