import typing
import typing_extensions

from .files import File
from .server_members import MemberCompositeKey


class ServerBan(typing.TypedDict):
    _id: MemberCompositeKey
    reason: typing.Optional[str]


class DataBanCreate(typing.TypedDict):
    reason: typing_extensions.NotRequired[typing.Optional[str]]


class BannedUser(typing.TypedDict):
    _id: str
    username: str
    discriminator: str
    avatar: typing.Optional[File]


class BanListResult(typing.TypedDict):
    users: list[BannedUser]
    bans: list[ServerBan]
