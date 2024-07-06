import typing as t

from .files import File
from .server_members import MemberCompositeKey


class ServerBan(t.TypedDict):
    _id: MemberCompositeKey
    reason: str | None


class DataBanCreate(t.TypedDict):
    reason: t.NotRequired[str | None]


class BannedUser(t.TypedDict):
    _id: str
    username: str
    discriminator: str
    avatar: File | None


class BanListResult(t.TypedDict):
    users: list[BannedUser]
    bans: list[ServerBan]


__all__ = ("ServerBan", "DataBanCreate", "BannedUser", "BanListResult")
