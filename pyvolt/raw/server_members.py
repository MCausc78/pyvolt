from __future__ import annotations

import typing as t

from . import basic, files, users


class Member(t.TypedDict):
    _id: MemberCompositeKey
    joined_at: str
    nickname: t.NotRequired[str]
    avatar: t.NotRequired[files.File]
    roles: t.NotRequired[list[str]]
    timeout: t.NotRequired[str]


class PartialMember(t.TypedDict):
    nickname: t.NotRequired[str]
    avatar: t.NotRequired[files.File]
    roles: t.NotRequired[list[str]]
    timeout: t.NotRequired[str]


class MemberCompositeKey(t.TypedDict):
    server: str
    user: str


FieldsMember = t.Literal["Nickname", "Avatar", "Roles", "Timeout"]


class OptionsFetchAllMembers(t.TypedDict):
    exclude_offline: t.NotRequired[basic.Bool]


class AllMemberResponse(t.TypedDict):
    members: list[Member]
    users: list[users.User]


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
    "OptionsFetchAllMembers",
    "AllMemberResponse",
    "DataMemberEdit",
)
