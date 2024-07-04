from __future__ import annotations

import typing as t

from . import channels, files, servers, users


class ServerInvite(t.TypedDict):
    type: t.Literal["Server"]
    _id: str
    server: str
    creator: str
    channel: str


class GroupInvite(t.TypedDict):
    type: t.Literal["Group"]
    _id: str
    creator: str
    channel: str


Invite = ServerInvite | GroupInvite


class ServerInviteResponse(t.TypedDict):
    type: t.Literal["Server"]
    code: str
    server_id: str
    server_name: str
    server_icon: t.NotRequired[files.File]
    server_banner: t.NotRequired[files.File]
    server_flags: t.NotRequired[int]
    channel_id: str
    channel_name: str
    channel_description: t.NotRequired[str]
    user_name: str
    user_avatar: t.NotRequired[files.File]
    member_count: int


class GroupInviteResponse(t.TypedDict):
    type: t.Literal["Group"]
    code: str
    channel_id: str
    channel_name: str
    channel_description: t.NotRequired[str]
    user_name: str
    user_avatar: t.NotRequired[files.File]


InviteResponse = ServerInviteResponse | GroupInviteResponse


class ServerInviteJoinResponse(t.TypedDict):
    type: t.Literal["Server"]
    channels: list[channels.Channel]
    server: servers.Server


class GroupInviteJoinResponse(t.TypedDict):
    type: t.Literal["Group"]
    channel: channels.GroupChannel
    users: list[users.User]


InviteJoinResponse = ServerInviteJoinResponse | GroupInviteJoinResponse

__all__ = (
    "ServerInvite",
    "GroupInvite",
    "Invite",
    "ServerInviteResponse",
    "GroupInviteResponse",
    "InviteResponse",
    "ServerInviteJoinResponse",
    "GroupInviteJoinResponse",
    "InviteJoinResponse",
)
