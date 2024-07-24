from __future__ import annotations

import typing
from urllib.parse import quote

Method = typing.Literal['GET', 'POST', 'PATCH', 'DELETE', 'PUT']


class CompiledRoute:
    """Represents compiled Revolt API route."""

    route: Route
    args: dict[str, typing.Any]

    __slots__ = ('route', 'args')

    def __init__(self, route: Route, **args: typing.Any) -> None:
        self.route = route
        self.args = args

    def __repr__(self) -> str:
        return f'<CompiledRoute route={self.route!r} args={self.args!r}>'

    def __str__(self) -> str:
        return f'CompiledRoute(route={self.route}, args={self.args})'

    def build(self) -> str:
        return self.route.path.format(**dict(map(lambda p: (p[0], quote(str(p[1]))), self.args.items())))


class Route:
    """Represents Revolt API route."""

    __slots__ = ('method', 'path')

    def __init__(self, method: Method, path: str, /) -> None:
        self.method: Method = method
        self.path: str = path

    def __repr__(self) -> str:
        return f'<Route method={self.method!r} path={self.path!r}>'

    def __str__(self) -> str:
        return f'Route({self.method!r}, {self.path!r})'

    def compile(self, **args: typing.Any) -> CompiledRoute:
        """Compiles route."""
        return CompiledRoute(self, **args)


ROOT: typing.Final[Route] = Route('GET', '/')


BOTS_CREATE: typing.Final[Route] = Route('POST', '/bots/create')
BOTS_DELETE: typing.Final[Route] = Route('DELETE', '/bots/{bot_id}')
BOTS_EDIT: typing.Final[Route] = Route('PATCH', '/bots/{bot_id}')
BOTS_FETCH: typing.Final[Route] = Route('GET', '/bots/{bot_id}')
BOTS_FETCH_OWNED: typing.Final[Route] = Route('GET', '/bots/@me')
BOTS_FETCH_PUBLIC: typing.Final[Route] = Route('GET', '/bots/{bot_id}/invite')
BOTS_INVITE: typing.Final[Route] = Route('POST', '/bots/{bot_id}/invite')


# Channels control
CHANNELS_CHANNEL_ACK: typing.Final[Route] = Route('PUT', '/channels/{channel_id}/ack/{message_id}')
CHANNELS_CHANNEL_DELETE: typing.Final[Route] = Route('DELETE', '/channels/{channel_id}')
CHANNELS_CHANNEL_EDIT: typing.Final[Route] = Route('PATCH', '/channels/{channel_id}')
CHANNELS_CHANNEL_FETCH: typing.Final[Route] = Route('GET', '/channels/{channel_id}')
CHANNELS_CHANNEL_PINS: typing.Final[Route] = Route('GET', '/channels/{channel_id}/pins')
CHANNELS_GROUP_ADD_MEMBER: typing.Final[Route] = Route('PUT', '/channels/{channel_id}/recipients/{user_id}')
CHANNELS_GROUP_CREATE: typing.Final[Route] = Route('POST', '/channels/create')
CHANNELS_GROUP_REMOVE_MEMBER: typing.Final[Route] = Route('DELETE', '/channels/{channel_id}/recipients/{user_id}')
CHANNELS_INVITE_CREATE: typing.Final[Route] = Route('POST', '/channels/{channel_id}/invites')
CHANNELS_MEMBERS_FETCH: typing.Final[Route] = Route('GET', '/channels/{channel_id}/members')
CHANNELS_MESSAGE_BULK_DELETE: typing.Final[Route] = Route('DELETE', '/channels/{channel_id}/messages/bulk')
CHANNELS_MESSAGE_CLEAR_REACTIONS: typing.Final[Route] = Route(
    'DELETE', '/channels/{channel_id}/messages/{message_id}/reactions'
)
CHANNELS_MESSAGE_DELETE: typing.Final[Route] = Route('DELETE', '/channels/{channel_id}/messages/{message_id}')
CHANNELS_MESSAGE_EDIT: typing.Final[Route] = Route('PATCH', '/channels/{channel_id}/messages/{message_id}')
CHANNELS_MESSAGE_FETCH: typing.Final[Route] = Route('GET', '/channels/{channel_id}/messages/{message_id}')
CHANNELS_MESSAGE_QUERY: typing.Final[Route] = Route('GET', '/channels/{channel_id}/messages')
CHANNELS_MESSAGE_REACT: typing.Final[Route] = Route(
    'PUT', '/channels/{channel_id}/messages/{message_id}/reactions/{emoji}'
)
CHANNELS_MESSAGE_PIN: typing.Final[Route] = Route('POST', '/channels/{channel_id}/messages/{message_id}/pin')
CHANNELS_MESSAGE_SEND: typing.Final[Route] = Route('POST', '/channels/{channel_id}/messages')
CHANNELS_MESSAGE_UNPIN: typing.Final[Route] = Route('DELETE', '/channels/{channel_id}/messages/{message_id}/pin')
CHANNELS_MESSAGE_SEARCH: typing.Final[Route] = Route('POST', '/channels/{channel_id}/search')
CHANNELS_MESSAGE_UNREACT: typing.Final[Route] = Route(
    'DELETE', '/channels/{channel_id}/messages/{message_id}/reactions/{emoji}'
)
CHANNELS_PERMISSIONS_SET: typing.Final[Route] = Route('PUT', '/channels/{channel_id}/permissions/{role_id}')
CHANNELS_PERMISSIONS_SET_DEFAULT: typing.Final[Route] = Route('PUT', '/channels/{channel_id}/permissions/default')
CHANNELS_VOICE_JOIN: typing.Final[Route] = Route('POST', '/channels/{channel_id}/join_call')
CHANNELS_WEBHOOK_CREATE: typing.Final[Route] = Route('POST', '/channels/{channel_id}/webhooks')
CHANNELS_WEBHOOK_FETCH_ALL: typing.Final[Route] = Route('GET', '/channels/{channel_id}/webhooks')


# Customization control (emojis)
CUSTOMISATION_EMOJI_CREATE: typing.Final[Route] = Route('PUT', '/custom/emoji/{attachment_id}')
CUSTOMISATION_EMOJI_DELETE: typing.Final[Route] = Route('DELETE', '/custom/emoji/{emoji_id}')
CUSTOMISATION_EMOJI_FETCH: typing.Final[Route] = Route('GET', '/custom/emoji/{emoji_id}')

# Invites control
INVITES_INVITE_DELETE: typing.Final[Route] = Route('DELETE', '/invites/{invite_code}')
INVITES_INVITE_FETCH: typing.Final[Route] = Route('GET', '/invites/{invite_code}')
INVITES_INVITE_JOIN: typing.Final[Route] = Route('POST', '/invites/{invite_code}')

# Onboarding control
ONBOARD_COMPLETE: typing.Final[Route] = Route('POST', '/onboard/complete')
ONBOARD_HELLO: typing.Final[Route] = Route('GET', '/onboard/hello')

# Web Push subscription control
PUSH_SUBSCRIBE: typing.Final[Route] = Route('POST', '/push/subscribe')
PUSH_UNSUBSCRIBE: typing.Final[Route] = Route('POST', '/push/unsubscribe')

# Safety control
SAFETY_REPORT_CONTENT: typing.Final[Route] = Route('POST', '/safety/report')

# Servers control
SERVERS_BAN_CREATE: typing.Final[Route] = Route('PUT', '/servers/{server_id}/bans/{user_id}')
SERVERS_BAN_LIST: typing.Final[Route] = Route('GET', '/servers/{server_id}/bans')
SERVERS_BAN_REMOVE: typing.Final[Route] = Route('DELETE', '/servers/{server_id}/bans/{user_id}')
SERVERS_CHANNEL_CREATE: typing.Final[Route] = Route('POST', '/servers/{server_id}/channels')
SERVERS_EMOJI_LIST: typing.Final[Route] = Route('GET', '/servers/{server_id}/emojis')
SERVERS_INVITES_FETCH: typing.Final[Route] = Route('GET', '/servers/{server_id}/invites')
SERVERS_MEMBER_EDIT: typing.Final[Route] = Route('PATCH', '/servers/{server_id}/members/{member_id}')
SERVERS_MEMBER_EXPERIMENTAL_QUERY: typing.Final[Route] = Route('GET', '/servers/{server_id}/members_experimental_query')
SERVERS_MEMBER_FETCH: typing.Final[Route] = Route('GET', '/servers/{server_id}/members/{member_id}')
SERVERS_MEMBER_FETCH_ALL: typing.Final[Route] = Route('GET', '/servers/{server_id}/members')
SERVERS_MEMBER_REMOVE: typing.Final[Route] = Route('DELETE', '/servers/{server_id}/members/{member_id}')
SERVERS_PERMISSIONS_SET: typing.Final[Route] = Route('PUT', '/servers/{server_id}/permissions/{role_id}')
SERVERS_PERMISSIONS_SET_DEFAULT: typing.Final[Route] = Route('PUT', '/servers/{server_id}/permissions/default')
SERVERS_ROLES_CREATE: typing.Final[Route] = Route('POST', '/servers/{server_id}/roles')
SERVERS_ROLES_DELETE: typing.Final[Route] = Route('DELETE', '/servers/{server_id}/roles/{role_id}')
SERVERS_ROLES_EDIT: typing.Final[Route] = Route('PATCH', '/servers/{server_id}/roles/{role_id}')
SERVERS_ROLES_FETCH: typing.Final[Route] = Route('GET', '/servers/{channel_id}/roles/{role_id}')
SERVERS_SERVER_ACK: typing.Final[Route] = Route('PUT', '/servers/{server_id}/ack')
SERVERS_SERVER_CREATE: typing.Final[Route] = Route('POST', '/servers/create')
SERVERS_SERVER_DELETE: typing.Final[Route] = Route('DELETE', '/servers/{server_id}')
SERVERS_SERVER_EDIT: typing.Final[Route] = Route('PATCH', '/servers/{server_id}')
SERVERS_SERVER_FETCH: typing.Final[Route] = Route('GET', '/servers/{server_id}')

# Sync control
SYNC_GET_SETTINGS: typing.Final[Route] = Route('POST', '/sync/settings/fetch')
SYNC_GET_UNREADS: typing.Final[Route] = Route('GET', '/sync/unreads')
SYNC_SET_SETTINGS: typing.Final[Route] = Route('POST', '/sync/settings/set')

# Users control
USERS_ADD_FRIEND: typing.Final[Route] = Route('PUT', '/users/{user_id}/friend')
USERS_BLOCK_USER: typing.Final[Route] = Route('PUT', '/users/{user_id}/block')
USERS_CHANGE_USERNAME: typing.Final[Route] = Route('PATCH', '/users/@me/username')
USERS_EDIT_SELF_USER: typing.Final[Route] = Route('PATCH', '/users/@me')
USERS_EDIT_USER: typing.Final[Route] = Route('PATCH', '/users/{user_id}')
USERS_FETCH_DMS: typing.Final[Route] = Route('GET', '/users/dms')
USERS_FETCH_PROFILE: typing.Final[Route] = Route('GET', '/users/{user_id}/profile')
USERS_FETCH_SELF: typing.Final[Route] = Route('GET', '/users/@me')
USERS_FETCH_USER: typing.Final[Route] = Route('GET', '/users/{user_id}')
USERS_FETCH_USER_FLAGS: typing.Final[Route] = Route('GET', '/users/{user_id}/flags')
USERS_FIND_MUTUAL: typing.Final[Route] = Route('GET', '/users/{user_id}/mutual')
USERS_GET_DEFAULT_AVATAR: typing.Final[Route] = Route('GET', '/users/{user_id}/default_avatar')
USERS_OPEN_DM: typing.Final[Route] = Route('GET', '/users/{user_id}/dm')
USERS_REMOVE_FRIEND: typing.Final[Route] = Route('DELETE', '/users/{user_id}/friend')
USERS_SEND_FRIEND_REQUEST: typing.Final[Route] = Route('POST', '/users/friend')
USERS_UNBLOCK_USER: typing.Final[Route] = Route('DELETE', '/users/{user_id}/block')

# Webhooks control
WEBHOOKS_WEBHOOK_DELETE: typing.Final[Route] = Route('DELETE', '/webhooks/{webhook_id}')
WEBHOOKS_WEBHOOK_DELETE_TOKEN: typing.Final[Route] = Route('DELETE', '/webhooks/{webhook_id}/{webhook_token}')
WEBHOOKS_WEBHOOK_EDIT: typing.Final[Route] = Route('PATCH', '/webhooks/{webhook_id}')
WEBHOOKS_WEBHOOK_EDIT_TOKEN: typing.Final[Route] = Route('PATCH', '/webhooks/{webhook_id}/{webhook_token}')
WEBHOOKS_WEBHOOK_EXECUTE: typing.Final[Route] = Route('POST', '/webhooks/{webhook_id}/{webhook_token}')
WEBHOOKS_WEBHOOK_FETCH: typing.Final[Route] = Route('GET', '/webhooks/{webhook_id}')
WEBHOOKS_WEBHOOK_FETCH_TOKEN: typing.Final[Route] = Route('GET', '/webhooks/{webhook_id}/{webhook_token}')

# Account Authentication
AUTH_ACCOUNT_CHANGE_EMAIL: typing.Final[Route] = Route('PATCH', '/auth/account/change/email')
AUTH_ACCOUNT_CHANGE_PASSWORD: typing.Final[Route] = Route('PATCH', '/auth/account/change/password')
AUTH_ACCOUNT_CONFIRM_DELETION: typing.Final[Route] = Route('PUT', '/auth/account/delete')
AUTH_ACCOUNT_CREATE_ACCOUNT: typing.Final[Route] = Route('POST', '/auth/account/create')
AUTH_ACCOUNT_DELETE_ACCOUNT: typing.Final[Route] = Route('POST', '/auth/account/delete')
AUTH_ACCOUNT_DISABLE_ACCOUNT: typing.Final[Route] = Route('POST', '/auth/account/disable')
AUTH_ACCOUNT_FETCH_ACCOUNT: typing.Final[Route] = Route('GET', '/auth/account/')
AUTH_ACCOUNT_PASSWORD_RESET: typing.Final[Route] = Route('PATCH', '/auth/account/reset_password')
AUTH_ACCOUNT_RESEND_VERIFICATION: typing.Final[Route] = Route('POST', '/auth/account/reverify')
AUTH_ACCOUNT_SEND_PASSWORD_RESET: typing.Final[Route] = Route('POST', '/auth/account/reset_password')
AUTH_ACCOUNT_VERIFY_EMAIL: typing.Final[Route] = Route('POST', '/auth/account/verify/{code}')

# MFA Authentication
AUTH_MFA_CREATE_TICKET: typing.Final[Route] = Route('PUT', '/auth/mfa/ticket')
AUTH_MFA_FETCH_RECOVERY: typing.Final[Route] = Route('POST', '/auth/mfa/recovery')
AUTH_MFA_FETCH_STATUS: typing.Final[Route] = Route('GET', '/auth/mfa/')
AUTH_MFA_GENERATE_RECOVERY: typing.Final[Route] = Route('PATCH', '/auth/mfa/recovery')
AUTH_MFA_GET_MFA_METHODS: typing.Final[Route] = Route('GET', '/auth/mfa/methods')
AUTH_MFA_TOTP_DISABLE: typing.Final[Route] = Route('DELETE', '/auth/mfa/totp')
AUTH_MFA_TOTP_ENABLE: typing.Final[Route] = Route('PUT', '/auth/mfa/totp')
AUTH_MFA_TOTP_GENERATE_SECRET: typing.Final[Route] = Route('POST', '/auth/mfa/totp')

# Session Authentication
AUTH_SESSION_EDIT: typing.Final[Route] = Route('PATCH', '/auth/session/{session_id}')
AUTH_SESSION_FETCH_ALL: typing.Final[Route] = Route('GET', '/auth/session/all')
AUTH_SESSION_LOGIN: typing.Final[Route] = Route('POST', '/auth/session/login')
AUTH_SESSION_LOGOUT: typing.Final[Route] = Route('POST', '/auth/session/logout')
AUTH_SESSION_REVOKE: typing.Final[Route] = Route('DELETE', '/auth/session/{session_id}')
AUTH_SESSION_REVOKE_ALL: typing.Final[Route] = Route('DELETE', '/auth/session/all')

__all__ = (
    'Method',
    'CompiledRoute',
    'Route',
    'ROOT',
    'BOTS_CREATE',
    'BOTS_DELETE',
    'BOTS_EDIT',
    'BOTS_FETCH',
    'BOTS_FETCH_OWNED',
    'BOTS_FETCH_PUBLIC',
    'BOTS_INVITE',
    'CHANNELS_CHANNEL_ACK',
    'CHANNELS_CHANNEL_DELETE',
    'CHANNELS_CHANNEL_EDIT',
    'CHANNELS_CHANNEL_FETCH',
    'CHANNELS_CHANNEL_PINS',
    'CHANNELS_GROUP_ADD_MEMBER',
    'CHANNELS_GROUP_CREATE',
    'CHANNELS_GROUP_REMOVE_MEMBER',
    'CHANNELS_INVITE_CREATE',
    'CHANNELS_MEMBERS_FETCH',
    'CHANNELS_MESSAGE_BULK_DELETE',
    'CHANNELS_MESSAGE_CLEAR_REACTIONS',
    'CHANNELS_MESSAGE_DELETE',
    'CHANNELS_MESSAGE_EDIT',
    'CHANNELS_MESSAGE_FETCH',
    'CHANNELS_MESSAGE_QUERY',
    'CHANNELS_MESSAGE_REACT',
    'CHANNELS_MESSAGE_PIN',
    'CHANNELS_MESSAGE_SEND',
    'CHANNELS_MESSAGE_UNPIN',
    'CHANNELS_MESSAGE_SEARCH',
    'CHANNELS_MESSAGE_UNREACT',
    'CHANNELS_PERMISSIONS_SET',
    'CHANNELS_PERMISSIONS_SET_DEFAULT',
    'CHANNELS_VOICE_JOIN',
    'CHANNELS_WEBHOOK_CREATE',
    'CHANNELS_WEBHOOK_FETCH_ALL',
    'CUSTOMISATION_EMOJI_CREATE',
    'CUSTOMISATION_EMOJI_DELETE',
    'CUSTOMISATION_EMOJI_FETCH',
    'INVITES_INVITE_DELETE',
    'INVITES_INVITE_FETCH',
    'INVITES_INVITE_JOIN',
    'ONBOARD_COMPLETE',
    'ONBOARD_HELLO',
    'PUSH_SUBSCRIBE',
    'PUSH_UNSUBSCRIBE',
    'SAFETY_REPORT_CONTENT',
    'SERVERS_BAN_CREATE',
    'SERVERS_BAN_LIST',
    'SERVERS_BAN_REMOVE',
    'SERVERS_CHANNEL_CREATE',
    'SERVERS_EMOJI_LIST',
    'SERVERS_INVITES_FETCH',
    'SERVERS_MEMBER_EDIT',
    'SERVERS_MEMBER_EXPERIMENTAL_QUERY',
    'SERVERS_MEMBER_FETCH',
    'SERVERS_MEMBER_FETCH_ALL',
    'SERVERS_MEMBER_REMOVE',
    'SERVERS_PERMISSIONS_SET',
    'SERVERS_PERMISSIONS_SET_DEFAULT',
    'SERVERS_ROLES_CREATE',
    'SERVERS_ROLES_DELETE',
    'SERVERS_ROLES_EDIT',
    'SERVERS_ROLES_FETCH',
    'SERVERS_SERVER_ACK',
    'SERVERS_SERVER_CREATE',
    'SERVERS_SERVER_DELETE',
    'SERVERS_SERVER_EDIT',
    'SERVERS_SERVER_FETCH',
    'SYNC_GET_SETTINGS',
    'SYNC_GET_UNREADS',
    'SYNC_SET_SETTINGS',
    'USERS_ADD_FRIEND',
    'USERS_BLOCK_USER',
    'USERS_CHANGE_USERNAME',
    'USERS_EDIT_SELF_USER',
    'USERS_EDIT_USER',
    'USERS_FETCH_DMS',
    'USERS_FETCH_PROFILE',
    'USERS_FETCH_SELF',
    'USERS_FETCH_USER',
    'USERS_FETCH_USER_FLAGS',
    'USERS_FIND_MUTUAL',
    'USERS_GET_DEFAULT_AVATAR',
    'USERS_OPEN_DM',
    'USERS_REMOVE_FRIEND',
    'USERS_SEND_FRIEND_REQUEST',
    'USERS_UNBLOCK_USER',
    'WEBHOOKS_WEBHOOK_DELETE',
    'WEBHOOKS_WEBHOOK_DELETE_TOKEN',
    'WEBHOOKS_WEBHOOK_EDIT',
    'WEBHOOKS_WEBHOOK_EDIT_TOKEN',
    'WEBHOOKS_WEBHOOK_EXECUTE',
    'WEBHOOKS_WEBHOOK_FETCH',
    'WEBHOOKS_WEBHOOK_FETCH_TOKEN',
    'AUTH_ACCOUNT_CHANGE_EMAIL',
    'AUTH_ACCOUNT_CHANGE_PASSWORD',
    'AUTH_ACCOUNT_CONFIRM_DELETION',
    'AUTH_ACCOUNT_CREATE_ACCOUNT',
    'AUTH_ACCOUNT_DELETE_ACCOUNT',
    'AUTH_ACCOUNT_DISABLE_ACCOUNT',
    'AUTH_ACCOUNT_FETCH_ACCOUNT',
    'AUTH_ACCOUNT_PASSWORD_RESET',
    'AUTH_ACCOUNT_RESEND_VERIFICATION',
    'AUTH_ACCOUNT_SEND_PASSWORD_RESET',
    'AUTH_ACCOUNT_VERIFY_EMAIL',
    'AUTH_MFA_CREATE_TICKET',
    'AUTH_MFA_FETCH_RECOVERY',
    'AUTH_MFA_FETCH_STATUS',
    'AUTH_MFA_GENERATE_RECOVERY',
    'AUTH_MFA_GET_MFA_METHODS',
    'AUTH_MFA_TOTP_DISABLE',
    'AUTH_MFA_TOTP_ENABLE',
    'AUTH_MFA_TOTP_GENERATE_SECRET',
    'AUTH_SESSION_EDIT',
    'AUTH_SESSION_FETCH_ALL',
    'AUTH_SESSION_LOGIN',
    'AUTH_SESSION_LOGOUT',
    'AUTH_SESSION_REVOKE',
    'AUTH_SESSION_REVOKE_ALL',
)
