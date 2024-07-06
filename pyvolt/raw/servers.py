from __future__ import annotations

import typing as t

from .basic import Bool
from .channels import Channel
from .files import File
from .permissions import Override, OverrideField


# class BaseServer(t.Generic[C], t.TypedDict):
class BaseServer(t.TypedDict):
    _id: str
    owner: str
    name: str
    description: t.NotRequired[str]
    # channels: list[C]
    categories: t.NotRequired[list[Category]]
    system_messages: t.NotRequired[SystemMessageChannels]
    roles: t.NotRequired[dict[str, Role]]
    default_permissions: int
    icon: t.NotRequired[File]
    banner: t.NotRequired[File]
    flags: t.NotRequired[int]
    nsfw: t.NotRequired[bool]
    analytics: t.NotRequired[bool]
    discoverable: t.NotRequired[bool]


class Server(BaseServer):
    channels: list[str]


class PartialServer(t.TypedDict):
    owner: t.NotRequired[str]
    name: t.NotRequired[str]
    description: t.NotRequired[str]
    channels: t.NotRequired[list[str]]
    categories: t.NotRequired[list[Category]]
    system_messages: t.NotRequired[SystemMessageChannels]
    default_permissions: t.NotRequired[int]
    icon: t.NotRequired[File]
    banner: t.NotRequired[File]
    flags: t.NotRequired[int]
    discoverable: t.NotRequired[bool]
    analytics: t.NotRequired[bool]


class Role(t.TypedDict):
    name: str
    permissions: OverrideField
    colour: t.NotRequired[str]
    hoist: t.NotRequired[bool]
    rank: int


class PartialRole(t.TypedDict):
    name: t.NotRequired[str]
    permissions: t.NotRequired[OverrideField]
    colour: t.NotRequired[str]
    hoist: t.NotRequired[bool]
    rank: t.NotRequired[int]


FieldsServer = t.Literal[
    "Description", "Categories", "SystemMessages", "Icon", "Banner"
]
FieldsRole = t.Literal["Colour"]


class Category(t.TypedDict):
    id: str
    title: str
    channels: list[str]


class SystemMessageChannels(t.TypedDict):
    user_joined: t.NotRequired[str]
    user_left: t.NotRequired[str]
    user_kicked: t.NotRequired[str]
    user_banned: t.NotRequired[str]


class DataCreateServer(t.TypedDict):
    name: str
    description: t.NotRequired[str | None]
    nsfw: t.NotRequired[bool]


class DataCreateRole(t.TypedDict):
    name: str
    rank: t.NotRequired[int | None]


class NewRoleResponse(t.TypedDict):
    id: str
    role: Role


class CreateServerLegacyResponse(t.TypedDict):
    server: Server
    channels: list[Channel]


class OptionsFetchServer(t.TypedDict):
    include_channels: t.NotRequired[Bool]


class ServerWithChannels(BaseServer):
    channels: list[Channel]


FetchServerResponse = Server | ServerWithChannels


class DataEditServer(t.TypedDict):
    name: t.NotRequired[str]
    description: t.NotRequired[str]
    icon: t.NotRequired[str]
    banner: t.NotRequired[str]
    categories: t.NotRequired[list[Category]]
    system_messages: t.NotRequired[SystemMessageChannels]
    flags: t.NotRequired[int]
    discoverable: t.NotRequired[bool]
    analytics: t.NotRequired[bool]
    remove: t.NotRequired[list[FieldsServer]]


class DataEditRole(t.TypedDict):
    name: t.NotRequired[str]
    colour: t.NotRequired[str]
    hoist: t.NotRequired[bool]
    rank: t.NotRequired[int]
    remove: t.NotRequired[list[FieldsRole]]


class DataSetServerRolePermission(t.TypedDict):
    permissions: Override


class OptionsServerDelete(t.TypedDict):
    leave_silently: t.NotRequired[Bool]


__all__ = (
    "BaseServer",
    "Server",
    "PartialServer",
    "Role",
    "PartialRole",
    "FieldsServer",
    "FieldsRole",
    "Category",
    "SystemMessageChannels",
    "DataCreateServer",
    "DataCreateRole",
    "NewRoleResponse",
    "CreateServerLegacyResponse",
    "OptionsFetchServer",
    "ServerWithChannels",
    "FetchServerResponse",
    "DataEditServer",
    "DataEditRole",
    "DataSetServerRolePermission",
    "OptionsServerDelete",
)
