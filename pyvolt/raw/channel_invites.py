from __future__ import annotations

import typing
import typing_extensions

from .channels import GroupChannel, ServerChannel
from .files import File
from .servers import Server
from .users import User


class ServerInvite(typing.TypedDict):
    type: typing.Literal['Server']
    _id: str
    server: str
    creator: str
    channel: str


class GroupInvite(typing.TypedDict):
    type: typing.Literal['Group']
    _id: str
    creator: str
    channel: str


Invite = typing.Union[ServerInvite, GroupInvite]


class ServerInviteResponse(typing.TypedDict):
    type: typing.Literal['Server']
    code: str
    server_id: str
    server_name: str
    server_icon: typing_extensions.NotRequired[File]
    server_banner: typing_extensions.NotRequired[File]
    server_flags: typing_extensions.NotRequired[int]
    channel_id: str
    channel_name: str
    channel_description: typing_extensions.NotRequired[str]
    user_name: str
    user_avatar: typing_extensions.NotRequired[File]
    member_count: int


class GroupInviteResponse(typing.TypedDict):
    type: typing.Literal['Group']
    code: str
    channel_id: str
    channel_name: str
    channel_description: typing_extensions.NotRequired[str]
    user_name: str
    user_avatar: typing_extensions.NotRequired[File]


InviteResponse = typing.Union[ServerInviteResponse, GroupInviteResponse]


class ServerInviteJoinResponse(typing.TypedDict):
    type: typing.Literal['Server']
    channels: list[ServerChannel]
    server: Server


class GroupInviteJoinResponse(typing.TypedDict):
    type: typing.Literal['Group']
    channel: GroupChannel
    users: list[User]


InviteJoinResponse = typing.Union[ServerInviteJoinResponse, GroupInviteJoinResponse]
