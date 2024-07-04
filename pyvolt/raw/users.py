from __future__ import annotations

import typing as t

from . import files


class User(t.TypedDict):
    _id: str
    username: str
    discriminator: str
    display_name: t.NotRequired[str]
    avatar: t.NotRequired[files.File]
    relations: t.NotRequired[list[Relationship]]
    badges: t.NotRequired[int]
    status: t.NotRequired[UserStatus]
    profile: t.NotRequired[UserProfile]
    flags: t.NotRequired[int]
    privileged: t.NotRequired[bool]
    bot: t.NotRequired[BotInformation]
    relationship: RelationshipStatus
    online: bool


class PartialUser(t.TypedDict):
    username: t.NotRequired[str]
    discriminator: t.NotRequired[str]
    display_name: t.NotRequired[str]
    avatar: t.NotRequired[files.File]
    badges: t.NotRequired[int]
    status: t.NotRequired[UserStatus]
    # profile: t.NotRequired["UserProfile"]
    flags: t.NotRequired[int]
    online: t.NotRequired[bool]


FieldsUser = t.Literal[
    "Avatar",
    "StatusText",
    "StatusPresence",
    "ProfileContent",
    "ProfileBackground",
    "DisplayName",
]
RelationshipStatus = t.Literal[
    "None", "User", "Friend", "Outgoing", "Incoming", "Blocked", "BlockedOther"
]


class Relationship(t.TypedDict):
    _id: str
    status: RelationshipStatus


Presence = t.Literal["Online", "Idle", "Focus", "Busy", "Invisible"]


class UserStatus(t.TypedDict):
    text: t.NotRequired[str]
    presence: t.NotRequired[Presence]


class UserProfile(t.TypedDict):
    content: t.NotRequired[str]
    background: t.NotRequired[files.File]


class DataUserProfile(t.TypedDict):
    content: t.NotRequired[str]
    background: t.NotRequired[str]


class DataEditUser(t.TypedDict):
    display_name: t.NotRequired[str]
    avatar: t.NotRequired[str]
    status: t.NotRequired[UserStatus]
    profile: t.NotRequired[DataUserProfile]
    badges: t.NotRequired[int]
    flags: t.NotRequired[int]
    remove: t.NotRequired[list[FieldsUser]]


class FlagResponse(t.TypedDict):
    flags: int


class MutualResponse(t.TypedDict):
    users: list[str]
    servers: list[str]


class BotInformation(t.TypedDict):
    owner: str


class DataSendFriendRequest(t.TypedDict):
    username: str


# delta types


class DataChangeUsername(t.TypedDict):
    username: str
    password: str


class DataHello(t.TypedDict):
    onboarding: bool


class DataOnboard(t.TypedDict):
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
