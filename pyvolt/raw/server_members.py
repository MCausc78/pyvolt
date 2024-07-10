from __future__ import annotations

import typing as t

from .basic import Bool
from .files import File
from .users import User


class Member(t.TypedDict):
    _id: MemberCompositeKey
    joined_at: str
    nickname: t.NotRequired[str]
    avatar: t.NotRequired[File]
    roles: t.NotRequired[list[str]]
    timeout: t.NotRequired[str]


class PartialMember(t.TypedDict):
    nickname: t.NotRequired[str]
    avatar: t.NotRequired[File]
    roles: t.NotRequired[list[str]]
    timeout: t.NotRequired[str]


class MemberCompositeKey(t.TypedDict):
    server: str
    user: str


FieldsMember = t.Literal["Nickname", "Avatar", "Roles", "Timeout"]
RemovalIntention = t.Literal["Leave", "Kick", "Ban"]


class OptionsFetchAllMembers(t.TypedDict):
    exclude_offline: t.NotRequired[Bool]


class AllMemberResponse(t.TypedDict):
    members: list[Member]
    users: list[User]


class DataMemberEdit(t.TypedDict):
    nickname: t.NotRequired[str]
    avatar: t.NotRequired[str]
    roles: t.NotRequired[list[str]]
    timeout: t.NotRequired[str]
    remove: t.NotRequired[list[FieldsMember]]


__all__ = (
    "Member",
    "PartialMember",
    "MemberCompositeKey",
    "FieldsMember",
    "RemovalIntention",
    "OptionsFetchAllMembers",
    "AllMemberResponse",
    "DataMemberEdit",
)
