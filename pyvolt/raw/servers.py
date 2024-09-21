from __future__ import annotations

import typing
import typing_extensions
from .basic import Bool
from .channels import ServerChannel
from .files import File
from .permissions import Override, OverrideField


# class BaseServer(t.Generic[C], typing.TypedDict):
class BaseServer(typing.TypedDict):
    _id: str
    owner: str
    name: str
    description: typing_extensions.NotRequired[str]
    # channels: list[C]
    categories: typing_extensions.NotRequired[list[Category]]
    system_messages: typing_extensions.NotRequired[SystemMessageChannels]
    roles: typing_extensions.NotRequired[dict[str, Role]]
    default_permissions: int
    icon: typing_extensions.NotRequired[File]
    banner: typing_extensions.NotRequired[File]
    flags: typing_extensions.NotRequired[int]
    nsfw: typing_extensions.NotRequired[bool]
    analytics: typing_extensions.NotRequired[bool]
    discoverable: typing_extensions.NotRequired[bool]


class Server(BaseServer):
    channels: list[str]


class PartialServer(typing.TypedDict):
    owner: typing_extensions.NotRequired[str]
    name: typing_extensions.NotRequired[str]
    description: typing_extensions.NotRequired[str]
    channels: typing_extensions.NotRequired[list[str]]
    categories: typing_extensions.NotRequired[list[Category]]
    system_messages: typing_extensions.NotRequired[SystemMessageChannels]
    default_permissions: typing_extensions.NotRequired[int]
    icon: typing_extensions.NotRequired[File]
    banner: typing_extensions.NotRequired[File]
    flags: typing_extensions.NotRequired[int]
    discoverable: typing_extensions.NotRequired[bool]
    analytics: typing_extensions.NotRequired[bool]


class Role(typing.TypedDict):
    name: str
    permissions: OverrideField
    colour: typing_extensions.NotRequired[str]
    hoist: typing_extensions.NotRequired[bool]
    rank: int


class PartialRole(typing.TypedDict):
    name: typing_extensions.NotRequired[str]
    permissions: typing_extensions.NotRequired[OverrideField]
    colour: typing_extensions.NotRequired[str]
    hoist: typing_extensions.NotRequired[bool]
    rank: typing_extensions.NotRequired[int]


FieldsServer = typing.Literal['Description', 'Categories', 'SystemMessages', 'Icon', 'Banner']
FieldsRole = typing.Literal['Colour']


class Category(typing.TypedDict):
    id: str
    title: str
    channels: list[str]


class SystemMessageChannels(typing.TypedDict):
    user_joined: typing_extensions.NotRequired[str]
    user_left: typing_extensions.NotRequired[str]
    user_kicked: typing_extensions.NotRequired[str]
    user_banned: typing_extensions.NotRequired[str]


class DataCreateServer(typing.TypedDict):
    name: str
    description: typing_extensions.NotRequired[str | None]
    nsfw: typing_extensions.NotRequired[bool]


class DataCreateRole(typing.TypedDict):
    name: str
    rank: typing_extensions.NotRequired[int | None]


class NewRoleResponse(typing.TypedDict):
    id: str
    role: Role


class CreateServerLegacyResponse(typing.TypedDict):
    server: Server
    channels: list[ServerChannel]


class OptionsFetchServer(typing.TypedDict):
    include_channels: typing_extensions.NotRequired[Bool]


class ServerWithChannels(BaseServer):
    channels: list[ServerChannel]


FetchServerResponse = Server | ServerWithChannels


class DataEditServer(typing.TypedDict):
    name: typing_extensions.NotRequired[str]
    description: typing_extensions.NotRequired[str]
    icon: typing_extensions.NotRequired[str]
    banner: typing_extensions.NotRequired[str]
    categories: typing_extensions.NotRequired[list[Category]]
    system_messages: typing_extensions.NotRequired[SystemMessageChannels]
    flags: typing_extensions.NotRequired[int]
    discoverable: typing_extensions.NotRequired[bool]
    analytics: typing_extensions.NotRequired[bool]
    remove: typing_extensions.NotRequired[list[FieldsServer]]


class DataEditRole(typing.TypedDict):
    name: typing_extensions.NotRequired[str]
    colour: typing_extensions.NotRequired[str]
    hoist: typing_extensions.NotRequired[bool]
    rank: typing_extensions.NotRequired[int]
    remove: typing_extensions.NotRequired[list[FieldsRole]]


class DataSetServerRolePermission(typing.TypedDict):
    permissions: Override


class OptionsServerDelete(typing.TypedDict):
    leave_silently: typing_extensions.NotRequired[Bool]


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
