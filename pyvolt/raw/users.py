from __future__ import annotations

import typing
import typing_extensions

from .files import File


class User(typing.TypedDict):
    _id: str
    username: str
    discriminator: str
    display_name: typing_extensions.NotRequired[str]
    avatar: typing_extensions.NotRequired[File]
    relations: typing_extensions.NotRequired[list[Relationship]]
    badges: typing_extensions.NotRequired[int]
    status: typing_extensions.NotRequired[UserStatus]
    # profile: typing_extensions.NotRequired[UserProfile]
    flags: typing_extensions.NotRequired[int]
    privileged: typing_extensions.NotRequired[bool]
    bot: typing_extensions.NotRequired[BotInformation]
    relationship: RelationshipStatus
    online: bool


class PartialUser(typing.TypedDict):
    username: typing_extensions.NotRequired[str]
    discriminator: typing_extensions.NotRequired[str]
    display_name: typing_extensions.NotRequired[str]
    avatar: typing_extensions.NotRequired[File]
    badges: typing_extensions.NotRequired[int]
    status: typing_extensions.NotRequired[UserStatus]
    # profile: typing_extensions.NotRequired[UserProfile]
    flags: typing_extensions.NotRequired[int]
    bot: typing_extensions.NotRequired[BotInformation]
    online: typing_extensions.NotRequired[bool]


FieldsUser = typing.Literal[
    'Avatar',
    'StatusText',
    'StatusPresence',
    'ProfileContent',
    'ProfileBackground',
    'DisplayName',
]
RelationshipStatus = typing.Literal['None', 'User', 'Friend', 'Outgoing', 'Incoming', 'Blocked', 'BlockedOther']


class Relationship(typing.TypedDict):
    _id: str
    status: RelationshipStatus


Presence = typing.Literal['Online', 'Idle', 'Focus', 'Busy', 'Invisible']


class UserStatus(typing.TypedDict):
    text: typing_extensions.NotRequired[str]
    presence: typing_extensions.NotRequired[Presence]


class UserProfile(typing.TypedDict):
    content: typing_extensions.NotRequired[str]
    background: typing_extensions.NotRequired[File]


class DataUserProfile(typing.TypedDict):
    content: typing_extensions.NotRequired[str]
    background: typing_extensions.NotRequired[str]


class DataEditUser(typing.TypedDict):
    display_name: typing_extensions.NotRequired[str]
    avatar: typing_extensions.NotRequired[str]
    status: typing_extensions.NotRequired[UserStatus]
    profile: typing_extensions.NotRequired[DataUserProfile]
    badges: typing_extensions.NotRequired[int]
    flags: typing_extensions.NotRequired[int]
    remove: typing_extensions.NotRequired[list[FieldsUser]]


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


class UserVoiceState(typing.TypedDict):
    id: str
    can_receive: bool
    can_publish: bool
    screensharing: bool
    camera: bool


class PartialUserVoiceState(typing.TypedDict):
    can_receive: typing_extensions.NotRequired[bool]
    can_publish: typing_extensions.NotRequired[bool]
    screensharing: typing_extensions.NotRequired[bool]
    camera: typing_extensions.NotRequired[bool]
