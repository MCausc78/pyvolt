from __future__ import annotations

import typing

from .channels import GroupChannel, Channel
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


Invite = ServerInvite | GroupInvite


class ServerInviteResponse(typing.TypedDict):
    type: typing.Literal['Server']
    code: str
    server_id: str
    server_name: str
    server_icon: typing.NotRequired[File]
    server_banner: typing.NotRequired[File]
    server_flags: typing.NotRequired[int]
    channel_id: str
    channel_name: str
    channel_description: typing.NotRequired[str]
    user_name: str
    user_avatar: typing.NotRequired[File]
    member_count: int


class GroupInviteResponse(typing.TypedDict):
    type: typing.Literal['Group']
    code: str
    channel_id: str
    channel_name: str
    channel_description: typing.NotRequired[str]
    user_name: str
    user_avatar: typing.NotRequired[File]


InviteResponse = ServerInviteResponse | GroupInviteResponse


class ServerInviteJoinResponse(typing.TypedDict):
    type: typing.Literal['Server']
    channels: list[Channel]
    server: Server


class GroupInviteJoinResponse(typing.TypedDict):
    type: typing.Literal['Group']
    channel: GroupChannel
    users: list[User]


InviteJoinResponse = ServerInviteJoinResponse | GroupInviteJoinResponse

__all__ = (
    'ServerInvite',
    'GroupInvite',
    'Invite',
    'ServerInviteResponse',
    'GroupInviteResponse',
    'InviteResponse',
    'ServerInviteJoinResponse',
    'GroupInviteJoinResponse',
    'InviteJoinResponse',
)
