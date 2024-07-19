from __future__ import annotations

import typing as t
from urllib.parse import quote

Method = t.Literal["GET", "POST", "PATCH", "DELETE", "PUT"]


class CompiledRoute:
    """Represents compiled Revolt API route."""

    route: Route
    args: dict[str, t.Any]

    __slots__ = ("route", "args")

    def __init__(self, route: Route, **args: t.Any) -> None:
        self.route = route
        self.args = args

    def __repr__(self) -> str:
        return f"<CompiledRoute route={self.route!r} args={self.args!r}>"

    def __str__(self) -> str:
        return f"CompiledRoute(route={self.route}, args={self.args})"

    def build(self) -> str:
        return self.route.path.format(
            **dict(map(lambda p: (p[0], quote(str(p[1]))), self.args.items()))
        )


class Route:
    """Represents Revolt API route."""

    method: Method
    path: str

    __slots__ = ("method", "path")

    def __init__(self, method: Method, path: str, /) -> None:
        self.method = method
        self.path = path

    def __repr__(self) -> str:
        return f"<Route method={self.method!r} path={self.path!r}>"

    def __str__(self) -> str:
        return f"Route({self.method!r}, {self.path!r})"

    def compile(self, **args: t.Any) -> CompiledRoute:
        """Compiles route."""
        return CompiledRoute(self, **args)


ROOT: t.Final[Route] = Route("GET", "/")


BOTS_CREATE: t.Final[Route] = Route("POST", "/bots/create")
BOTS_DELETE: t.Final[Route] = Route("DELETE", "/bots/{bot_id}")
BOTS_EDIT: t.Final[Route] = Route("PATCH", "/bots/{bot_id}")
BOTS_FETCH: t.Final[Route] = Route("GET", "/bots/{bot_id}")
BOTS_FETCH_OWNED: t.Final[Route] = Route("GET", "/bots/@me")
BOTS_FETCH_PUBLIC: t.Final[Route] = Route("GET", "/bots/{bot_id}/invite")
BOTS_INVITE: t.Final[Route] = Route("POST", "/bots/{bot_id}/invite")


# Channels control
CHANNELS_CHANNEL_ACK: t.Final[Route] = Route(
    "PUT", "/channels/{channel_id}/ack/{message_id}"
)
CHANNELS_CHANNEL_DELETE: t.Final[Route] = Route("DELETE", "/channels/{channel_id}")
CHANNELS_CHANNEL_EDIT: t.Final[Route] = Route("PATCH", "/channels/{channel_id}")
CHANNELS_CHANNEL_FETCH: t.Final[Route] = Route("GET", "/channels/{channel_id}")
CHANNELS_CHANNEL_PINS: t.Final[Route] = Route("GET", "/channels/{channel_id}/pins")
CHANNELS_GROUP_ADD_MEMBER: t.Final[Route] = Route(
    "PUT", "/channels/{channel_id}/recipients/{user_id}"
)
CHANNELS_GROUP_CREATE: t.Final[Route] = Route("POST", "/channels/create")
CHANNELS_GROUP_REMOVE_MEMBER: t.Final[Route] = Route(
    "DELETE", "/channels/{channel_id}/recipients/{user_id}"
)
CHANNELS_INVITE_CREATE: t.Final[Route] = Route("POST", "/channels/{channel_id}/invites")
CHANNELS_MEMBERS_FETCH: t.Final[Route] = Route("GET", "/channels/{channel_id}/members")
CHANNELS_MESSAGE_BULK_DELETE: t.Final[Route] = Route(
    "DELETE", "/channels/{channel_id}/messages/bulk"
)
CHANNELS_MESSAGE_CLEAR_REACTIONS: t.Final[Route] = Route(
    "DELETE", "/channels/{channel_id}/messages/{message_id}/reactions"
)
CHANNELS_MESSAGE_DELETE: t.Final[Route] = Route(
    "DELETE", "/channels/{channel_id}/messages/{message_id}"
)
CHANNELS_MESSAGE_EDIT: t.Final[Route] = Route(
    "PATCH", "/channels/{channel_id}/messages/{message_id}"
)
CHANNELS_MESSAGE_FETCH: t.Final[Route] = Route(
    "GET", "/channels/{channel_id}/messages/{message_id}"
)
CHANNELS_MESSAGE_QUERY: t.Final[Route] = Route("GET", "/channels/{channel_id}/messages")
CHANNELS_MESSAGE_REACT: t.Final[Route] = Route(
    "PUT", "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}"
)
CHANNELS_MESSAGE_PIN: t.Final[Route] = Route(
    "POST", "/channels/{channel_id}/messages/{message_id}/pin"
)
CHANNELS_MESSAGE_SEND: t.Final[Route] = Route("POST", "/channels/{channel_id}/messages")
CHANNELS_MESSAGE_UNPIN: t.Final[Route] = Route(
    "POST", "/channels/{channel_id}/messages/{message_id}/unpin"
)
CHANNELS_MESSAGE_SEARCH: t.Final[Route] = Route("POST", "/channels/{channel_id}/search")
CHANNELS_MESSAGE_UNREACT: t.Final[Route] = Route(
    "DELETE", "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}"
)
CHANNELS_PERMISSIONS_SET: t.Final[Route] = Route(
    "PUT", "/channels/{channel_id}/permissions/{role_id}"
)
CHANNELS_PERMISSIONS_SET_DEFAULT: t.Final[Route] = Route(
    "PUT", "/channels/{channel_id}/permissions/default"
)
CHANNELS_VOICE_JOIN: t.Final[Route] = Route("POST", "/channels/{channel_id}/join_call")
CHANNELS_WEBHOOK_CREATE: t.Final[Route] = Route(
    "POST", "/channels/{channel_id}/webhooks"
)
CHANNELS_WEBHOOK_FETCH_ALL: t.Final[Route] = Route(
    "GET", "/channels/{channel_id}/webhooks"
)


# Customization control (emojis)
CUSTOMISATION_EMOJI_CREATE: t.Final[Route] = Route(
    "PUT", "/custom/emoji/{attachment_id}"
)
CUSTOMISATION_EMOJI_DELETE: t.Final[Route] = Route("DELETE", "/custom/emoji/{emoji_id}")
CUSTOMISATION_EMOJI_FETCH: t.Final[Route] = Route("GET", "/custom/emoji/{emoji_id}")

# Invites control
INVITES_INVITE_DELETE: t.Final[Route] = Route("DELETE", "/invites/{invite_code}")
INVITES_INVITE_FETCH: t.Final[Route] = Route("GET", "/invites/{invite_code}")
INVITES_INVITE_JOIN: t.Final[Route] = Route("POST", "/invites/{invite_code}")

# Onboarding control
ONBOARD_COMPLETE: t.Final[Route] = Route("POST", "/onboard/complete")
ONBOARD_HELLO: t.Final[Route] = Route("GET", "/onboard/hello")

# Web Push subscription control
PUSH_SUBSCRIBE: t.Final[Route] = Route("POST", "/push/subscribe")
PUSH_UNSUBSCRIBE: t.Final[Route] = Route("POST", "/push/unsubscribe")

# Safety control
SAFETY_REPORT_CONTENT: t.Final[Route] = Route("POST", "/safety/report")

# Servers control
SERVERS_BAN_CREATE: t.Final[Route] = Route("PUT", "/servers/{server_id}/bans/{user_id}")
SERVERS_BAN_LIST: t.Final[Route] = Route("GET", "/servers/{server_id}/bans")
SERVERS_BAN_REMOVE: t.Final[Route] = Route(
    "DELETE", "/servers/{server_id}/bans/{user_id}"
)
SERVERS_CHANNEL_CREATE: t.Final[Route] = Route("POST", "/servers/{server_id}/channels")
SERVERS_EMOJI_LIST: t.Final[Route] = Route("GET", "/servers/{server_id}/emojis")
SERVERS_INVITES_FETCH: t.Final[Route] = Route("GET", "/servers/{server_id}/invites")
SERVERS_MEMBER_EDIT: t.Final[Route] = Route(
    "PATCH", "/servers/{server_id}/members/{member_id}"
)
SERVERS_MEMBER_EXPERIMENTAL_QUERY: t.Final[Route] = Route(
    "GET", "/servers/{server_id}/members_experimental_query"
)
SERVERS_MEMBER_FETCH: t.Final[Route] = Route(
    "GET", "/servers/{server_id}/members/{member_id}"
)
SERVERS_MEMBER_FETCH_ALL: t.Final[Route] = Route("GET", "/servers/{server_id}/members")
SERVERS_MEMBER_REMOVE: t.Final[Route] = Route(
    "DELETE", "/servers/{server_id}/members/{member_id}"
)
SERVERS_PERMISSIONS_SET: t.Final[Route] = Route(
    "PUT", "/servers/{server_id}/permissions/{role_id}"
)
SERVERS_PERMISSIONS_SET_DEFAULT: t.Final[Route] = Route(
    "PUT", "/servers/{server_id}/permissions/default"
)
SERVERS_ROLES_CREATE: t.Final[Route] = Route("POST", "/servers/{server_id}/roles")
SERVERS_ROLES_DELETE: t.Final[Route] = Route(
    "DELETE", "/servers/{server_id}/roles/{role_id}"
)
SERVERS_ROLES_EDIT: t.Final[Route] = Route(
    "PATCH", "/servers/{server_id}/roles/{role_id}"
)
SERVERS_ROLES_FETCH: t.Final[Route] = Route(
    "GET", "/servers/{channel_id}/roles/{role_id}"
)
SERVERS_SERVER_ACK: t.Final[Route] = Route("PUT", "/servers/{server_id}/ack")
SERVERS_SERVER_CREATE: t.Final[Route] = Route("POST", "/servers/create")
SERVERS_SERVER_DELETE: t.Final[Route] = Route("DELETE", "/servers/{server_id}")
SERVERS_SERVER_EDIT: t.Final[Route] = Route("PATCH", "/servers/{server_id}")
SERVERS_SERVER_FETCH: t.Final[Route] = Route("GET", "/servers/{server_id}")

# Sync control
SYNC_GET_SETTINGS: t.Final[Route] = Route("POST", "/sync/settings/fetch")
SYNC_GET_UNREADS: t.Final[Route] = Route("GET", "/sync/unreads")
SYNC_SET_SETTINGS: t.Final[Route] = Route("POST", "/sync/settings/set")

# Users control
USERS_ADD_FRIEND: t.Final[Route] = Route("PUT", "/users/{user_id}/friend")
USERS_BLOCK_USER: t.Final[Route] = Route("PUT", "/users/{user_id}/block")
USERS_CHANGE_USERNAME: t.Final[Route] = Route("PATCH", "/users/@me/username")
USERS_EDIT_SELF_USER: t.Final[Route] = Route("PATCH", "/users/@me")
USERS_EDIT_USER: t.Final[Route] = Route("PATCH", "/users/{user_id}")
USERS_FETCH_DMS: t.Final[Route] = Route("GET", "/users/dms")
USERS_FETCH_PROFILE: t.Final[Route] = Route("GET", "/users/{user_id}/profile")
USERS_FETCH_SELF: t.Final[Route] = Route("GET", "/users/@me")
USERS_FETCH_USER: t.Final[Route] = Route("GET", "/users/{user_id}")
USERS_FETCH_USER_FLAGS: t.Final[Route] = Route("GET", "/users/{user_id}/flags")
USERS_FIND_MUTUAL: t.Final[Route] = Route("GET", "/users/{user_id}/mutual")
USERS_GET_DEFAULT_AVATAR: t.Final[Route] = Route(
    "GET", "/users/{user_id}/default_avatar"
)
USERS_OPEN_DM: t.Final[Route] = Route("GET", "/users/{user_id}/dm")
USERS_REMOVE_FRIEND: t.Final[Route] = Route("DELETE", "/users/{user_id}/friend")
USERS_SEND_FRIEND_REQUEST: t.Final[Route] = Route("POST", "/users/friend")
USERS_UNBLOCK_USER: t.Final[Route] = Route("DELETE", "/users/{user_id}/block")

# Webhooks control
WEBHOOKS_WEBHOOK_DELETE: t.Final[Route] = Route("DELETE", "/webhooks/{webhook_id}")
WEBHOOKS_WEBHOOK_DELETE_TOKEN: t.Final[Route] = Route(
    "DELETE", "/webhooks/{webhook_id}/{webhook_token}"
)
WEBHOOKS_WEBHOOK_EDIT: t.Final[Route] = Route("PATCH", "/webhooks/{webhook_id}")
WEBHOOKS_WEBHOOK_EDIT_TOKEN: t.Final[Route] = Route(
    "PATCH", "/webhooks/{webhook_id}/{webhook_token}"
)
WEBHOOKS_WEBHOOK_EXECUTE: t.Final[Route] = Route(
    "POST", "/webhooks/{webhook_id}/{webhook_token}"
)
WEBHOOKS_WEBHOOK_FETCH: t.Final[Route] = Route("GET", "/webhooks/{webhook_id}")
WEBHOOKS_WEBHOOK_FETCH_TOKEN: t.Final[Route] = Route(
    "GET", "/webhooks/{webhook_id}/{webhook_token}"
)

# Account Authentication
AUTH_ACCOUNT_CHANGE_EMAIL: t.Final[Route] = Route("PATCH", "/auth/account/change/email")
AUTH_ACCOUNT_CHANGE_PASSWORD: t.Final[Route] = Route(
    "PATCH", "/auth/account/change/password"
)
AUTH_ACCOUNT_CONFIRM_DELETION: t.Final[Route] = Route("PUT", "/auth/account/delete")
AUTH_ACCOUNT_CREATE_ACCOUNT: t.Final[Route] = Route("POST", "/auth/account/create")
AUTH_ACCOUNT_DELETE_ACCOUNT: t.Final[Route] = Route("POST", "/auth/account/delete")
AUTH_ACCOUNT_DISABLE_ACCOUNT: t.Final[Route] = Route("POST", "/auth/account/disable")
AUTH_ACCOUNT_FETCH_ACCOUNT: t.Final[Route] = Route("GET", "/auth/account/")
AUTH_ACCOUNT_PASSWORD_RESET: t.Final[Route] = Route(
    "PATCH", "/auth/account/reset_password"
)
AUTH_ACCOUNT_RESEND_VERIFICATION: t.Final[Route] = Route(
    "POST", "/auth/account/reverify"
)
AUTH_ACCOUNT_SEND_PASSWORD_RESET: t.Final[Route] = Route(
    "POST", "/auth/account/reset_password"
)
AUTH_ACCOUNT_VERIFY_EMAIL: t.Final[Route] = Route("POST", "/auth/account/verify/{code}")

# MFA Authentication
AUTH_MFA_CREATE_TICKET: t.Final[Route] = Route("PUT", "/auth/mfa/ticket")
AUTH_MFA_FETCH_RECOVERY: t.Final[Route] = Route("POST", "/auth/mfa/recovery")
AUTH_MFA_FETCH_STATUS: t.Final[Route] = Route("GET", "/auth/mfa/")
AUTH_MFA_GENERATE_RECOVERY: t.Final[Route] = Route("PATCH", "/auth/mfa/recovery")
AUTH_MFA_GET_MFA_METHODS: t.Final[Route] = Route("GET", "/auth/mfa/methods")
AUTH_MFA_TOTP_DISABLE: t.Final[Route] = Route("DELETE", "/auth/mfa/totp")
AUTH_MFA_TOTP_ENABLE: t.Final[Route] = Route("PUT", "/auth/mfa/totp")
AUTH_MFA_TOTP_GENERATE_SECRET: t.Final[Route] = Route("POST", "/auth/mfa/totp")

# Session Authentication
AUTH_SESSION_EDIT: t.Final[Route] = Route("PATCH", "/auth/session/{session_id}")
AUTH_SESSION_FETCH_ALL: t.Final[Route] = Route("GET", "/auth/session/all")
AUTH_SESSION_LOGIN: t.Final[Route] = Route("POST", "/auth/session/login")
AUTH_SESSION_LOGOUT: t.Final[Route] = Route("POST", "/auth/session/logout")
AUTH_SESSION_REVOKE: t.Final[Route] = Route("DELETE", "/auth/session/{session_id}")
AUTH_SESSION_REVOKE_ALL: t.Final[Route] = Route("DELETE", "/auth/session/all")

__all__ = (
    "Method",
    "CompiledRoute",
    "Route",
    "ROOT",
    "BOTS_CREATE",
    "BOTS_DELETE",
    "BOTS_EDIT",
    "BOTS_FETCH",
    "BOTS_FETCH_OWNED",
    "BOTS_FETCH_PUBLIC",
    "BOTS_INVITE",
    "CHANNELS_CHANNEL_ACK",
    "CHANNELS_CHANNEL_DELETE",
    "CHANNELS_CHANNEL_EDIT",
    "CHANNELS_CHANNEL_FETCH",
    "CHANNELS_CHANNEL_PINS",
    "CHANNELS_GROUP_ADD_MEMBER",
    "CHANNELS_GROUP_CREATE",
    "CHANNELS_GROUP_REMOVE_MEMBER",
    "CHANNELS_INVITE_CREATE",
    "CHANNELS_MEMBERS_FETCH",
    "CHANNELS_MESSAGE_BULK_DELETE",
    "CHANNELS_MESSAGE_CLEAR_REACTIONS",
    "CHANNELS_MESSAGE_DELETE",
    "CHANNELS_MESSAGE_EDIT",
    "CHANNELS_MESSAGE_FETCH",
    "CHANNELS_MESSAGE_QUERY",
    "CHANNELS_MESSAGE_REACT",
    "CHANNELS_MESSAGE_PIN",
    "CHANNELS_MESSAGE_SEND",
    "CHANNELS_MESSAGE_UNPIN",
    "CHANNELS_MESSAGE_SEARCH",
    "CHANNELS_MESSAGE_UNREACT",
    "CHANNELS_PERMISSIONS_SET",
    "CHANNELS_PERMISSIONS_SET_DEFAULT",
    "CHANNELS_VOICE_JOIN",
    "CHANNELS_WEBHOOK_CREATE",
    "CHANNELS_WEBHOOK_FETCH_ALL",
    "CUSTOMISATION_EMOJI_CREATE",
    "CUSTOMISATION_EMOJI_DELETE",
    "CUSTOMISATION_EMOJI_FETCH",
    "INVITES_INVITE_DELETE",
    "INVITES_INVITE_FETCH",
    "INVITES_INVITE_JOIN",
    "ONBOARD_COMPLETE",
    "ONBOARD_HELLO",
    "PUSH_SUBSCRIBE",
    "PUSH_UNSUBSCRIBE",
    "SAFETY_REPORT_CONTENT",
    "SERVERS_BAN_CREATE",
    "SERVERS_BAN_LIST",
    "SERVERS_BAN_REMOVE",
    "SERVERS_CHANNEL_CREATE",
    "SERVERS_EMOJI_LIST",
    "SERVERS_INVITES_FETCH",
    "SERVERS_MEMBER_EDIT",
    "SERVERS_MEMBER_EXPERIMENTAL_QUERY",
    "SERVERS_MEMBER_FETCH",
    "SERVERS_MEMBER_FETCH_ALL",
    "SERVERS_MEMBER_REMOVE",
    "SERVERS_PERMISSIONS_SET",
    "SERVERS_PERMISSIONS_SET_DEFAULT",
    "SERVERS_ROLES_CREATE",
    "SERVERS_ROLES_DELETE",
    "SERVERS_ROLES_EDIT",
    "SERVERS_ROLES_FETCH",
    "SERVERS_SERVER_ACK",
    "SERVERS_SERVER_CREATE",
    "SERVERS_SERVER_DELETE",
    "SERVERS_SERVER_EDIT",
    "SERVERS_SERVER_FETCH",
    "SYNC_GET_SETTINGS",
    "SYNC_GET_UNREADS",
    "SYNC_SET_SETTINGS",
    "USERS_ADD_FRIEND",
    "USERS_BLOCK_USER",
    "USERS_CHANGE_USERNAME",
    "USERS_EDIT_SELF_USER",
    "USERS_EDIT_USER",
    "USERS_FETCH_DMS",
    "USERS_FETCH_PROFILE",
    "USERS_FETCH_SELF",
    "USERS_FETCH_USER",
    "USERS_FETCH_USER_FLAGS",
    "USERS_FIND_MUTUAL",
    "USERS_GET_DEFAULT_AVATAR",
    "USERS_OPEN_DM",
    "USERS_REMOVE_FRIEND",
    "USERS_SEND_FRIEND_REQUEST",
    "USERS_UNBLOCK_USER",
    "WEBHOOKS_WEBHOOK_DELETE",
    "WEBHOOKS_WEBHOOK_DELETE_TOKEN",
    "WEBHOOKS_WEBHOOK_EDIT",
    "WEBHOOKS_WEBHOOK_EDIT_TOKEN",
    "WEBHOOKS_WEBHOOK_EXECUTE",
    "WEBHOOKS_WEBHOOK_FETCH",
    "WEBHOOKS_WEBHOOK_FETCH_TOKEN",
    "AUTH_ACCOUNT_CHANGE_EMAIL",
    "AUTH_ACCOUNT_CHANGE_PASSWORD",
    "AUTH_ACCOUNT_CONFIRM_DELETION",
    "AUTH_ACCOUNT_CREATE_ACCOUNT",
    "AUTH_ACCOUNT_DELETE_ACCOUNT",
    "AUTH_ACCOUNT_DISABLE_ACCOUNT",
    "AUTH_ACCOUNT_FETCH_ACCOUNT",
    "AUTH_ACCOUNT_PASSWORD_RESET",
    "AUTH_ACCOUNT_RESEND_VERIFICATION",
    "AUTH_ACCOUNT_SEND_PASSWORD_RESET",
    "AUTH_ACCOUNT_VERIFY_EMAIL",
    "AUTH_MFA_CREATE_TICKET",
    "AUTH_MFA_FETCH_RECOVERY",
    "AUTH_MFA_FETCH_STATUS",
    "AUTH_MFA_GENERATE_RECOVERY",
    "AUTH_MFA_GET_MFA_METHODS",
    "AUTH_MFA_TOTP_DISABLE",
    "AUTH_MFA_TOTP_ENABLE",
    "AUTH_MFA_TOTP_GENERATE_SECRET",
    "AUTH_SESSION_EDIT",
    "AUTH_SESSION_FETCH_ALL",
    "AUTH_SESSION_LOGIN",
    "AUTH_SESSION_LOGOUT",
    "AUTH_SESSION_REVOKE",
    "AUTH_SESSION_REVOKE_ALL",
)
