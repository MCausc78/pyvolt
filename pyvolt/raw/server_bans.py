import typing as t

from . import files, server_members


class ServerBan(t.TypedDict):
    _id: server_members.MemberCompositeKey
    reason: str | None


class DataBanCreate(t.TypedDict):
    reason: t.NotRequired[str | None]


class BannedUser(t.TypedDict):
    _id: str
    username: str
    discriminator: str
    avatar: files.File | None


class BanListResult(t.TypedDict):
    users: list[BannedUser]
    bans: list[ServerBan]


__all__ = ("ServerBan", "DataBanCreate", "BannedUser", "BanListResult")
