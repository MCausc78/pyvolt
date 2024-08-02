from __future__ import annotations

import typing

from .basic import Bool
from .files import File
from .users import User


class Member(typing.TypedDict):
    _id: MemberCompositeKey
    joined_at: str
    nickname: typing.NotRequired[str]
    avatar: typing.NotRequired[File]
    roles: typing.NotRequired[list[str]]
    timeout: typing.NotRequired[str]


class PartialMember(typing.TypedDict):
    nickname: typing.NotRequired[str]
    avatar: typing.NotRequired[File]
    roles: typing.NotRequired[list[str]]
    timeout: typing.NotRequired[str]


class MemberCompositeKey(typing.TypedDict):
    server: str
    user: str


FieldsMember = typing.Literal['Nickname', 'Avatar', 'Roles', 'Timeout']
RemovalIntention = typing.Literal['Leave', 'Kick', 'Ban']


class OptionsFetchAllMembers(typing.TypedDict):
    exclude_offline: typing.NotRequired[Bool]


class AllMemberResponse(typing.TypedDict):
    members: list[Member]
    users: list[User]


class DataMemberEdit(typing.TypedDict):
    nickname: typing.NotRequired[str]
    avatar: typing.NotRequired[str]
    roles: typing.NotRequired[list[str]]
    timeout: typing.NotRequired[str]
    remove: typing.NotRequired[list[FieldsMember]]


__all__ = (
    'Member',
    'PartialMember',
    'MemberCompositeKey',
    'FieldsMember',
    'RemovalIntention',
    'OptionsFetchAllMembers',
    'AllMemberResponse',
    'DataMemberEdit',
)
