from __future__ import annotations

import typing

from .files import File


class User(typing.TypedDict):
    _id: str
    username: str
    discriminator: str
    display_name: typing.NotRequired[str]
    avatar: typing.NotRequired[File]
    relations: typing.NotRequired[list[Relationship]]
    badges: typing.NotRequired[int]
    status: typing.NotRequired[UserStatus]
    profile: typing.NotRequired[UserProfile]
    flags: typing.NotRequired[int]
    privileged: typing.NotRequired[bool]
    bot: typing.NotRequired[BotInformation]
    relationship: RelationshipStatus
    online: bool


class PartialUser(typing.TypedDict):
    username: typing.NotRequired[str]
    discriminator: typing.NotRequired[str]
    display_name: typing.NotRequired[str]
    avatar: typing.NotRequired[File]
    badges: typing.NotRequired[int]
    status: typing.NotRequired[UserStatus]
    # profile: typing.NotRequired[UserProfile]
    flags: typing.NotRequired[int]
    online: typing.NotRequired[bool]


FieldsUser = typing.Literal[
    "Avatar",
    "StatusText",
    "StatusPresence",
    "ProfileContent",
    "ProfileBackground",
    "DisplayName",
]
RelationshipStatus = typing.Literal[
    "None", "User", "Friend", "Outgoing", "Incoming", "Blocked", "BlockedOther"
]


class Relationship(typing.TypedDict):
    _id: str
    status: RelationshipStatus


Presence = typing.Literal["Online", "Idle", "Focus", "Busy", "Invisible"]


class UserStatus(typing.TypedDict):
    text: typing.NotRequired[str]
    presence: typing.NotRequired[Presence]


class UserProfile(typing.TypedDict):
    content: typing.NotRequired[str]
    background: typing.NotRequired[File]


class DataUserProfile(typing.TypedDict):
    content: typing.NotRequired[str]
    background: typing.NotRequired[str]


class DataEditUser(typing.TypedDict):
    display_name: typing.NotRequired[str]
    avatar: typing.NotRequired[str]
    status: typing.NotRequired[UserStatus]
    profile: typing.NotRequired[DataUserProfile]
    badges: typing.NotRequired[int]
    flags: typing.NotRequired[int]
    remove: typing.NotRequired[list[FieldsUser]]


class FlagResponse(typing.TypedDict):
    flags: int


class MutualResponse(typing.TypedDict):
    users: list[str]
    servers: list[str]


class BotInformation(typing.TypedDict):
    owner: str


class DataSendFriendRequest(typing.TypedDict):
    username: str


# delta types


class DataChangeUsername(typing.TypedDict):
    username: str
    password: str


class DataHello(typing.TypedDict):
    onboarding: bool


class DataOnboard(typing.TypedDict):
    username: str


__all__ = (
    "User",
    "PartialUser",
    "FieldsUser",
    "RelationshipStatus",
    "Relationship",
    "Presence",
    "UserStatus",
    "UserProfile",
    "DataUserProfile",
    "DataEditUser",
    "FlagResponse",
    "MutualResponse",
    "BotInformation",
    "DataSendFriendRequest",
    "DataChangeUsername",
    "DataHello",
    "DataOnboard",
)
