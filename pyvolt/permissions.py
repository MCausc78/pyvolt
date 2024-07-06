from __future__ import annotations

from enum import IntFlag
import typing as t

if t.TYPE_CHECKING:
    from . import raw


class Permissions(IntFlag):
    NONE = 0

    # * Generic premissions

    MANAGE_CHANNEL = 1 << 0
    """Manage the channel or channels on the server."""

    MANAGE_SERVER = 1 << 1
    """Manage the server."""

    MANAGE_PERMISSIONS = 1 << 2
    """Manage permissions on servers or channels."""

    MANAGE_ROLE = 1 << 3
    """Manage roles on server."""

    MANAGE_CUSTOMISATION = 1 << 4
    """Manage server customisation (includes emoji)."""

    # % 1 bit reserved

    # * Member permissions
    KICK_MEMBERS = 1 << 6
    """Kick other members below their ranking."""

    BAN_MEMBERS = 1 << 7
    """Ban other members below their ranking."""

    TIMEOUT_MEMBERS = 1 << 8
    """Timeout other members below their ranking."""

    ASSIGN_ROLES = 1 << 9
    """Assign roles to members below their ranking."""

    CHANGE_NICKNAME = 1 << 10
    """Change own nickname."""

    MANAGE_NICKNAMES = 1 << 11
    """Change or remove other's nicknames below their ranking."""

    CHANGE_AVATAR = 1 << 12
    """Change own avatar."""

    REMOVE_AVATARS = 1 << 13
    """Remove other's avatars below their ranking."""

    # % 7 bits reserved

    # * Channel permissions

    VIEW_CHANNEL = 1 << 20
    """View a channel."""

    READ_MESSAGE_HISTORY = 1 << 21
    """Read a channel's past message history."""

    SEND_MESSAGE = 1 << 22
    """Send a message in a channel."""

    MANAGE_MESSAGES = 1 << 23
    """Delete messages in a channel."""

    MANAGE_WEBHOOKS = 1 << 24
    """Manage webhook entries on a channel."""

    INVITE_OTHERS = 1 << 25
    """Create invites to this channel."""

    SEND_EMBEDS = 1 << 26
    """Send embedded content in this channel."""

    UPLOAD_FILES = 1 << 27
    """Send attachments and media in this channel."""

    MASQUERADE = 1 << 28
    """Masquerade messages using custom nickname and avatar."""

    REACT = 1 << 29
    """React to messages with emojis."""

    # * Voice permissions
    CONNECT = 1 << 30
    """Connect to a voice channel."""

    SPEAK = 1 << 31
    """Speak in a voice call."""

    VIDEO = 1 << 32
    """Share video in a voice call."""

    MUTE_MEMBERS = 1 << 33
    """Mute other members with lower ranking in a voice call."""

    DEAFEN_MEMBERS = 1 << 34
    """Deafen other members with lower ranking in a voice call."""

    MOVE_MEMBERS = 1 << 35
    """Move members between voice channels."""

    ALL = 0xFEFF03FDF
    """All permissions."""


# generating all permissions was done with:
# >>> bits = [0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 20, 21, 22, 23, 24, 25, 26, 27, 29, 29, 30, 31, 32, 33, 34, 35]
# >>> all_permissions = reduce(lambda x, y: x|y, [1<<bit for bit in bits])
# >>> print(hex(all_permissions))
# 0xfeff03fdf


class PermissionOverride:
    """Represents a single permission override."""

    allow: Permissions
    """Allow bit flags."""

    deny: Permissions
    """Disallow bit flags."""

    __slots__ = ("allow", "deny")

    def __init__(
        self,
        allow: Permissions = Permissions.NONE,
        deny: Permissions = Permissions.NONE,
    ) -> None:
        self.allow = allow
        self.deny = deny

    def build(self) -> raw.Override:
        return {"allow": int(self.allow), "deny": int(self.deny)}

    def __repr__(self) -> str:
        return f"PermissionOverride(allow={self.allow!r}, deny={self.deny!r})"


class UserPermissions(IntFlag):
    ACCESS = 1 << 0
    VIEW_PROFILE = 1 << 1
    SEND_MESSAGE = 1 << 2
    INVITE = 1 << 3

    ALL = 15


ALLOW_PERMISSIONS_IN_TIMEOUT = (
    Permissions.VIEW_CHANNEL | Permissions.READ_MESSAGE_HISTORY
)
VIEW_ONLY_PERMISSIONS = Permissions.VIEW_CHANNEL | Permissions.READ_MESSAGE_HISTORY
DEFAULT_PERMISSIONS = (
    VIEW_ONLY_PERMISSIONS
    | Permissions.SEND_MESSAGE
    | Permissions.INVITE_OTHERS
    | Permissions.SEND_EMBEDS
    | Permissions.UPLOAD_FILES
    | Permissions.CONNECT
    | Permissions.SPEAK
)
DEFAULT_SAVED_MESSAGES_PERMISSIONS = Permissions.ALL
DEFAULT_DM_PERMISSIONS = (
    DEFAULT_PERMISSIONS | Permissions.MANAGE_CHANNEL | Permissions.REACT
)
DEFAULT_SERVER_PERMISSIONS = (
    DEFAULT_PERMISSIONS
    | Permissions.REACT
    | Permissions.CHANGE_NICKNAME
    | Permissions.CHANGE_AVATAR
)

__all__ = (
    "Permissions",
    "PermissionOverride",
    "UserPermissions",
    "ALLOW_PERMISSIONS_IN_TIMEOUT",
    "VIEW_ONLY_PERMISSIONS",
    "DEFAULT_PERMISSIONS",
    "DEFAULT_SAVED_MESSAGES_PERMISSIONS",
    "DEFAULT_DM_PERMISSIONS",
    "DEFAULT_SERVER_PERMISSIONS",
)
