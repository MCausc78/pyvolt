from __future__ import annotations

import typing
import typing_extensions

from .basic import Bool
from .files import File
from .users import User


class Member(typing.TypedDict):
    _id: MemberCompositeKey
    joined_at: str
    nickname: typing_extensions.NotRequired[str]
    avatar: typing_extensions.NotRequired[File]
    roles: typing_extensions.NotRequired[list[str]]
    timeout: typing_extensions.NotRequired[str]


class PartialMember(typing.TypedDict):
    nickname: typing_extensions.NotRequired[str]
    avatar: typing_extensions.NotRequired[File]
    roles: typing_extensions.NotRequired[list[str]]
    timeout: typing_extensions.NotRequired[str]


class MemberCompositeKey(typing.TypedDict):
    server: str
    user: str


FieldsMember = typing.Literal['Nickname', 'Avatar', 'Roles', 'Timeout']
RemovalIntention = typing.Literal['Leave', 'Kick', 'Ban']


class OptionsFetchAllMembers(typing.TypedDict):
    exclude_offline: typing_extensions.NotRequired[Bool]


class AllMemberResponse(typing.TypedDict):
    members: list[Member]
    users: list[User]


class DataMemberEdit(typing.TypedDict):
    nickname: typing_extensions.NotRequired[str]
    avatar: typing_extensions.NotRequired[str]
    roles: typing_extensions.NotRequired[list[str]]
    timeout: typing_extensions.NotRequired[str]
    remove: typing_extensions.NotRequired[list[FieldsMember]]


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
