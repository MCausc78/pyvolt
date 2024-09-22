import typing
import typing_extensions

from .files import File
from .server_members import MemberCompositeKey


class ServerBan(typing.TypedDict):
    _id: MemberCompositeKey
    reason: str | None


class DataBanCreate(typing.TypedDict):
    reason: typing_extensions.NotRequired[str | None]


class BannedUser(typing.TypedDict):
    _id: str
    username: str
    discriminator: str
    avatar: File | None


class BanListResult(typing.TypedDict):
    users: list[BannedUser]
    bans: list[ServerBan]


__all__ = ('ServerBan', 'DataBanCreate', 'BannedUser', 'BanListResult')
