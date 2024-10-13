"""
The MIT License (MIT)

Copyright (c) 2024-present MCausc78

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

from copy import copy
from datetime import datetime
import logging
import typing

from . import discovery
from .authentication import (
    PartialAccount,
    MFATicket,
    WebPushSubscription,
    PartialSession,
    Session,
    MFARequired,
    AccountDisabled,
    MFAStatus,
    LoginResult,
)
from .bot import Bot, PublicBot
from .cdn import (
    AssetMetadata,
    StatelessAsset,
)
from .channel import (
    PartialChannel,
    SavedMessagesChannel,
    DMChannel,
    GroupChannel,
    ChannelVoiceMetadata,
    ServerTextChannel,
    VoiceChannel,
    ServerChannel,
    Channel,
)
from .core import UNDEFINED
from .embed import (
    EmbedSpecial,
    NoneEmbedSpecial,
    _NONE_EMBED_SPECIAL,
    GifEmbedSpecial,
    _GIF_EMBED_SPECIAL,
    YouTubeEmbedSpecial,
    LightspeedEmbedSpecial,
    TwitchEmbedSpecial,
    SpotifyEmbedSpecial,
    SoundcloudEmbedSpecial,
    _SOUNDCLOUD_EMBED_SPECIAL,
    BandcampEmbedSpecial,
    AppleMusicEmbedSpecial,
    StreamableEmbedSpecial,
    ImageEmbed,
    VideoEmbed,
    WebsiteEmbed,
    StatelessTextEmbed,
    NoneEmbed,
    _NONE_EMBED,
    Embed,
)
from .emoji import ServerEmoji, DetachedEmoji, Emoji
from .enums import (
    MFAMethod,
    AssetMetadataType,
    ServerActivity,
    BotUsage,
    LightspeedContentType,
    TwitchContentType,
    BandcampContentType,
    ImageSize,
    MemberRemovalIntention,
    Presence,
    RelationshipStatus,
)
from .events import (
    ReadyEvent,
    PrivateChannelCreateEvent,
    ServerChannelCreateEvent,
    ChannelCreateEvent,
    ChannelUpdateEvent,
    ChannelDeleteEvent,
    GroupRecipientAddEvent,
    GroupRecipientRemoveEvent,
    ChannelStartTypingEvent,
    ChannelStopTypingEvent,
    MessageAckEvent,
    MessageCreateEvent,
    MessageUpdateEvent,
    MessageAppendEvent,
    MessageDeleteEvent,
    MessageReactEvent,
    MessageUnreactEvent,
    MessageClearReactionEvent,
    BulkMessageDeleteEvent,
    ServerCreateEvent,
    ServerEmojiCreateEvent,
    ServerEmojiDeleteEvent,
    ServerUpdateEvent,
    ServerDeleteEvent,
    ServerMemberJoinEvent,
    ServerMemberUpdateEvent,
    ServerMemberRemoveEvent,
    RawServerRoleUpdateEvent,
    ServerRoleDeleteEvent,
    UserUpdateEvent,
    UserRelationshipUpdateEvent,
    UserSettingsUpdateEvent,
    UserPlatformWipeEvent,
    WebhookCreateEvent,
    WebhookUpdateEvent,
    WebhookDeleteEvent,
    AuthifierEvent,
    SessionCreateEvent,
    SessionDeleteEvent,
    SessionDeleteAllEvent,
    LogoutEvent,
    AuthenticatedEvent,
)
from .flags import (
    BotFlags,
    MessageFlags,
    Permissions,
    ServerFlags,
    UserBadges,
    UserFlags,
)
from .instance import (
    InstanceCaptchaFeature,
    InstanceGenericFeature,
    InstanceVoiceFeature,
    InstanceFeaturesConfig,
    InstanceBuild,
    Instance,
)
from .invite import (
    BaseInvite,
    ServerPublicInvite,
    GroupPublicInvite,
    UnknownPublicInvite,
    GroupInvite,
    ServerInvite,
    Invite,
)
from .message import (
    Interactions,
    Masquerade,
    MessageWebhook,
    PartialMessage,
    MessageAppendData,
    TextSystemEvent,
    StatelessUserAddedSystemEvent,
    StatelessUserRemovedSystemEvent,
    StatelessUserJoinedSystemEvent,
    StatelessUserLeftSystemEvent,
    StatelessUserKickedSystemEvent,
    StatelessUserBannedSystemEvent,
    StatelessChannelRenamedSystemEvent,
    StatelessChannelDescriptionChangedSystemEvent,
    StatelessChannelIconChangedSystemEvent,
    StatelessChannelOwnershipChangedSystemEvent,
    StatelessMessagePinnedSystemEvent,
    StatelessMessageUnpinnedSystemEvent,
    StatelessSystemEvent,
    Message,
)
from .permissions import Permissions, PermissionOverride
from .read_state import ReadState
from .server import (
    Category,
    SystemMessageChannels,
    PartialRole,
    Role,
    PartialServer,
    Server,
    Ban,
    PartialMember,
    Member,
    MemberList,
)
from .user_settings import UserSettings
from .user import (
    UserStatus,
    UserStatusEdit,
    StatelessUserProfile,
    PartialUserProfile,
    Relationship,
    Mutuals,
    PartialUser,
    DisplayUser,
    BotUserInfo,
    User,
    OwnUser,
)
from .webhook import PartialWebhook, Webhook

if typing.TYPE_CHECKING:
    from . import raw
    from .shard import Shard
    from .state import State

_L = logging.getLogger(__name__)


_EMPTY_DICT: dict[typing.Any, typing.Any] = {}

_new_bot_flags = BotFlags.__new__
_new_message_flags = MessageFlags.__new__
_new_permissions = Permissions.__new__
_new_server_flags = ServerFlags.__new__
_new_user_badges = UserBadges.__new__
_new_user_flags = UserFlags.__new__
_parse_dt = datetime.fromisoformat


class Parser:
    __slots__ = (
        'state',
        '_channel_parsers',
        '_embed_parsers',
        '_embed_special_parsers',
        '_emoji_parsers',
        '_invite_parsers',
        '_message_system_event_parsers',
        '_public_invite_parsers',
    )

    def __init__(self, *, state: State) -> None:
        self.state = state
        self._channel_parsers = {
            'SavedMessages': self.parse_saved_messages_channel,
            'DirectMessage': self.parse_direct_message_channel,
            'Group': self._parse_group_channel,
            'TextChannel': self.parse_text_channel,
            'VoiceChannel': self.parse_voice_channel,
        }
        self._embed_parsers = {
            'Website': self.parse_website_embed,
            'Image': self.parse_image_embed,
            'Video': self.parse_video_embed,
            'Text': self.parse_text_embed,
            'None': self.parse_none_embed,
        }
        self._embed_special_parsers = {
            'None': self.parse_none_embed_special,
            'GIF': self.parse_gif_embed_special,
            'YouTube': self.parse_youtube_embed_special,
            'Lightspeed': self.parse_lightspeed_embed_special,
            'Twitch': self.parse_twitch_embed_special,
            'Spotify': self.parse_spotify_embed_special,
            'Soundcloud': self.parse_soundcloud_embed_special,
            'Bandcamp': self.parse_bandcamp_embed_special,
            'AppleMusic': self.parse_apple_music_embed_special,
            'Streamable': self.parse_streamable_embed_special,
        }
        self._emoji_parsers = {
            'Server': self.parse_server_emoji,
            'Detached': self.parse_detached_emoji,
        }
        self._invite_parsers = {
            'Server': self.parse_server_invite,
            'Group': self.parse_group_invite,
        }
        self._message_system_event_parsers = {
            'text': self.parse_message_text_system_event,
            'user_added': self.parse_message_user_added_system_event,
            'user_remove': self.parse_message_user_remove_system_event,
            'user_joined': self.parse_message_user_joined_system_event,
            'user_left': self.parse_message_user_left_system_event,
            'user_kicked': self.parse_message_user_kicked_system_event,
            'user_banned': self.parse_message_user_banned_system_event,
            'channel_renamed': self.parse_message_channel_renamed_system_event,
            'channel_description_changed': self.parse_message_channel_description_changed_system_event,
            'channel_icon_changed': self.parse_message_channel_icon_changed_system_event,
            'channel_ownership_changed': self.parse_message_channel_ownership_changed_system_event,
            'message_pinned': self.parse_message_message_pinned_system_event,
            'message_unpinned': self.parse_message_message_unpinned_system_event,
        }
        self._public_invite_parsers = {
            'Server': self.parse_server_public_invite,
            'Group': self.parse_group_public_invite,
        }

    # basic start

    def parse_apple_music_embed_special(self, payload: raw.AppleMusicSpecial, /) -> AppleMusicEmbedSpecial:
        return AppleMusicEmbedSpecial(
            album_id=payload['album_id'],
            track_id=payload.get('track_id'),
        )

    def parse_asset_metadata(self, d: raw.Metadata, /) -> AssetMetadata:
        return AssetMetadata(
            type=AssetMetadataType(d['type']),
            width=d.get('width'),
            height=d.get('height'),
        )

    def parse_asset(self, d: raw.File, /) -> StatelessAsset:
        return StatelessAsset(
            id=d['_id'],
            filename=d['filename'],
            metadata=self.parse_asset_metadata(d['metadata']),
            content_type=d['content_type'],
            size=d['size'],
            deleted=d.get('deleted', False),
            reported=d.get('reported', False),
            message_id=d.get('message_id'),
            user_id=d.get('user_id'),
            server_id=d.get('server_id'),
            object_id=d.get('object_id'),
        )

    def parse_auth_event(self, shard: Shard, payload: raw.ClientAuthEvent, /) -> AuthifierEvent:
        if payload['event_type'] == 'CreateSession':
            return SessionCreateEvent(
                shard=shard,
                session=self.parse_session(payload['session']),
            )
        elif payload['event_type'] == 'DeleteSession':
            return SessionDeleteEvent(
                shard=shard,
                current_user_id=payload['user_id'],
                session_id=payload['session_id'],
            )
        elif payload['event_type'] == 'DeleteAllSessions':
            return SessionDeleteAllEvent(
                shard=shard,
                current_user_id=payload['user_id'],
                exclude_session_id=payload.get('exclude_session_id'),
            )
        else:
            raise NotImplementedError('Unimplemented auth event type', payload)

    def parse_authenticated_event(self, shard: Shard, payload: raw.ClientAuthenticatedEvent, /) -> AuthenticatedEvent:
        return AuthenticatedEvent(shard=shard)

    # basic end, internals start

    def _parse_group_channel(self, payload: raw.GroupChannel, /) -> GroupChannel:
        return self.parse_group_channel(
            payload,
            (True, payload['recipients']),
        )

    # internals end

    def parse_ban(self, payload: raw.ServerBan, users: dict[str, DisplayUser], /) -> Ban:
        id = payload['_id']
        user_id = id['user']

        return Ban(
            server_id=id['server'],
            user_id=user_id,
            reason=payload['reason'],
            user=users.get(user_id),
        )

    def parse_bandcamp_embed_special(self, payload: raw.BandcampSpecial, /) -> BandcampEmbedSpecial:
        return BandcampEmbedSpecial(
            content_type=BandcampContentType(payload['content_type']),
            id=payload['id'],
        )

    def parse_bans(self, payload: raw.BanListResult, /) -> list[Ban]:
        banned_users = {bu.id: bu for bu in map(self.parse_display_user, payload['users'])}
        return [self.parse_ban(e, banned_users) for e in payload['bans']]

    def _parse_bot(self, payload: raw.Bot, user: User, /) -> Bot:
        flags = _new_bot_flags(BotFlags)
        flags.value = payload.get('flags', 0)

        return Bot(
            state=self.state,
            id=payload['_id'],
            owner_id=payload['owner'],
            token=payload['token'],
            public=payload['public'],
            analytics=payload.get('analytics', False),
            discoverable=payload.get('discoverable', False),
            interactions_url=payload.get('interactions_url'),
            terms_of_service_url=payload.get('terms_of_service_url'),
            privacy_policy_url=payload.get('privacy_policy_url'),
            flags=flags,
            user=user,
        )

    def parse_bot(self, payload: raw.Bot, user: raw.User, /) -> Bot:
        return self._parse_bot(payload, self.parse_user(user))

    def parse_bot_user_info(self, payload: raw.BotInformation, /) -> BotUserInfo:
        return BotUserInfo(owner_id=payload['owner'])

    def parse_bots(self, payload: raw.OwnedBotsResponse, /) -> list[Bot]:
        bots = payload['bots']
        users = payload['users']

        if len(bots) != len(users):
            raise RuntimeError(f'Expected {len(bots)} users but got {len(users)}')
        return [self.parse_bot(e, users[i]) for i, e in enumerate(bots)]

    def parse_bulk_message_delete_event(
        self, shard: Shard, payload: raw.ClientBulkMessageDeleteEvent, /
    ) -> BulkMessageDeleteEvent:
        return BulkMessageDeleteEvent(
            shard=shard,
            channel_id=payload['channel'],
            message_ids=payload['ids'],
            messages=[],
        )

    def parse_category(self, payload: raw.Category, /) -> Category:
        return Category(
            id=payload['id'],
            title=payload['title'],
            channels=payload['channels'],  # type: ignore
        )

    def parse_channel_ack_event(self, shard: Shard, payload: raw.ClientChannelAckEvent, /) -> MessageAckEvent:
        return MessageAckEvent(
            shard=shard,
            channel_id=payload['id'],
            message_id=payload['message_id'],
            user_id=payload['user'],
        )

    def parse_channel_create_event(self, shard: Shard, payload: raw.ClientChannelCreateEvent, /) -> ChannelCreateEvent:
        channel = self.parse_channel(payload)
        if isinstance(
            channel,
            (SavedMessagesChannel, DMChannel, GroupChannel),
        ):
            return PrivateChannelCreateEvent(shard=shard, channel=channel)
        else:
            return ServerChannelCreateEvent(shard=shard, channel=channel)

    def parse_channel_delete_event(self, shard: Shard, payload: raw.ClientChannelDeleteEvent, /) -> ChannelDeleteEvent:
        return ChannelDeleteEvent(
            shard=shard,
            channel_id=payload['id'],
            channel=None,
        )

    def parse_channel_group_join_event(
        self, shard: Shard, payload: raw.ClientChannelGroupJoinEvent, /
    ) -> GroupRecipientAddEvent:
        return GroupRecipientAddEvent(
            shard=shard,
            channel_id=payload['id'],
            user_id=payload['user'],
            group=None,
        )

    def parse_channel_group_leave_event(
        self, shard: Shard, payload: raw.ClientChannelGroupLeaveEvent, /
    ) -> GroupRecipientRemoveEvent:
        return GroupRecipientRemoveEvent(
            shard=shard,
            channel_id=payload['id'],
            user_id=payload['user'],
            group=None,
        )

    def parse_channel_start_typing_event(
        self, shard: Shard, payload: raw.ClientChannelStartTypingEvent, /
    ) -> ChannelStartTypingEvent:
        return ChannelStartTypingEvent(
            shard=shard,
            channel_id=payload['id'],
            user_id=payload['user'],
        )

    def parse_channel_stop_typing_event(
        self, shard: Shard, payload: raw.ClientChannelStopTypingEvent, /
    ) -> ChannelStopTypingEvent:
        return ChannelStopTypingEvent(
            shard=shard,
            channel_id=payload['id'],
            user_id=payload['user'],
        )

    def parse_channel_unread(self, payload: raw.ChannelUnread, /) -> ReadState:
        id = payload['_id']

        return ReadState(
            state=self.state,
            channel_id=id['channel'],
            user_id=id['user'],
            last_message_id=payload.get('last_id'),
            mentioned_in=payload.get('mentions', []),
        )

    def parse_channel_update_event(self, shard: Shard, payload: raw.ClientChannelUpdateEvent, /) -> ChannelUpdateEvent:
        clear = payload['clear']
        data = payload['data']

        owner = data.get('owner')
        icon = data.get('icon')
        permissions = data.get('permissions')
        role_permissions = data.get('role_permissions')
        default_permissions = data.get('default_permissions')
        last_message_id = data.get('last_message_id')

        return ChannelUpdateEvent(
            shard=shard,
            channel=PartialChannel(
                state=self.state,
                id=payload['id'],
                name=data.get('name', UNDEFINED),
                owner_id=owner if owner else UNDEFINED,
                description=(None if 'Description' in clear else data.get('description', UNDEFINED)),
                internal_icon=(None if 'Icon' in clear else self.parse_asset(icon) if icon else UNDEFINED),
                nsfw=data.get('nsfw', UNDEFINED),
                active=data.get('active', UNDEFINED),
                permissions=(Permissions(permissions) if permissions is not None else UNDEFINED),
                role_permissions=(
                    {k: self.parse_permission_override_field(v) for k, v in role_permissions.items()}
                    if role_permissions is not None
                    else UNDEFINED
                ),
                default_permissions=(
                    self.parse_permission_override_field(default_permissions)
                    if default_permissions is not None
                    else UNDEFINED
                ),
                last_message_id=last_message_id or UNDEFINED,
            ),
            before=None,
            after=None,
        )

    @typing.overload
    def parse_channel(self, payload: raw.SavedMessagesChannel, /) -> SavedMessagesChannel: ...

    @typing.overload
    def parse_channel(self, payload: raw.DirectMessageChannel, /) -> DMChannel: ...

    @typing.overload
    def parse_channel(self, payload: raw.GroupChannel, /) -> GroupChannel: ...

    @typing.overload
    def parse_channel(self, payload: raw.TextChannel, /) -> ServerTextChannel: ...

    @typing.overload
    def parse_channel(self, payload: raw.VoiceChannel, /) -> VoiceChannel: ...

    def parse_channel(self, payload: raw.Channel, /) -> Channel:
        """Parses a channel object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The channel payload to parse.

        Returns
        -------
        :class:`Channel`
            The parsed channel object.
        """

        return self._channel_parsers[payload['channel_type']](payload)

    def parse_detached_emoji(self, payload: raw.DetachedEmoji, /) -> DetachedEmoji:
        return DetachedEmoji(
            state=self.state,
            id=payload['_id'],
            creator_id=payload['creator_id'],
            name=payload['name'],
            animated=payload.get('animated', False),
            nsfw=payload.get('nsfw', False),
        )

    def parse_disabled_response_login(self, payload: raw.a.DisabledResponseLogin, /) -> AccountDisabled:
        return AccountDisabled(user_id=payload['user_id'])

    def parse_direct_message_channel(self, payload: raw.DirectMessageChannel, /) -> DMChannel:
        """Parses a DM channel object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The DM channel payload to parse.

        Returns
        -------
        :class:`DMChannel`
            The parsed DM channel object.
        """

        recipient_ids = payload['recipients']

        return DMChannel(
            state=self.state,
            id=payload['_id'],
            active=payload['active'],
            recipient_ids=(
                recipient_ids[0],
                recipient_ids[1],
            ),
            last_message_id=payload.get('last_message_id'),
        )

    # Discovery
    def parse_discovery_bot(self, payload: raw.DiscoveryBot, /) -> discovery.DiscoveryBot:
        avatar = payload.get('avatar')

        return discovery.DiscoveryBot(
            state=self.state,
            id=payload['_id'],
            name=payload['username'],
            internal_avatar=self.parse_asset(avatar) if avatar else None,
            internal_profile=self.parse_user_profile(payload['profile']),
            tags=payload['tags'],
            server_count=payload['servers'],
            usage=BotUsage(payload['usage']),
        )

    def parse_discovery_bot_search_result(self, payload: raw.DiscoveryBotSearchResult, /) -> discovery.BotSearchResult:
        return discovery.BotSearchResult(
            query=payload['query'],
            count=payload['count'],
            bots=list(map(self.parse_discovery_bot, payload['bots'])),
            related_tags=payload['relatedTags'],
        )

    def parse_discovery_bots_page(self, payload: raw.DiscoveryBotsPage, /) -> discovery.DiscoveryBotsPage:
        return discovery.DiscoveryBotsPage(
            bots=list(map(self.parse_discovery_bot, payload['bots'])),
            popular_tags=payload['popularTags'],
        )

    def parse_discovery_server(self, payload: raw.DiscoveryServer, /) -> discovery.DiscoveryServer:
        icon = payload.get('icon')
        banner = payload.get('banner')

        return discovery.DiscoveryServer(
            state=self.state,
            id=payload['_id'],
            name=payload['name'],
            description=payload.get('description'),
            internal_icon=self.parse_asset(icon) if icon else None,
            internal_banner=self.parse_asset(banner) if banner else None,
            flags=ServerFlags(payload.get('flags') or 0),
            tags=payload['tags'],
            member_count=payload['members'],
            activity=ServerActivity(payload['activity']),
        )

    def parse_discovery_servers_page(self, payload: raw.DiscoveryServersPage, /) -> discovery.DiscoveryServersPage:
        return discovery.DiscoveryServersPage(
            servers=list(map(self.parse_discovery_server, payload['servers'])),
            popular_tags=payload['popularTags'],
        )

    def parse_discovery_server_search_result(
        self, payload: raw.DiscoveryServerSearchResult, /
    ) -> discovery.ServerSearchResult:
        return discovery.ServerSearchResult(
            query=payload['query'],
            count=payload['count'],
            servers=list(map(self.parse_discovery_server, payload['servers'])),
            related_tags=payload['relatedTags'],
        )

    def parse_discovery_theme(self, payload: raw.DiscoveryTheme, /) -> discovery.DiscoveryTheme:
        return discovery.DiscoveryTheme(
            state=self.state,
            name=payload['name'],
            description=payload['description'],
            creator=payload['creator'],
            slug=payload['slug'],
            tags=payload['tags'],
            overrides=payload['variables'],
            version=payload['version'],
            custom_css=payload.get('css'),
        )

    def parse_discovery_theme_search_result(
        self, payload: raw.DiscoveryThemeSearchResult, /
    ) -> discovery.ThemeSearchResult:
        return discovery.ThemeSearchResult(
            query=payload['query'],
            count=payload['count'],
            themes=list(map(self.parse_discovery_theme, payload['themes'])),
            related_tags=payload['relatedTags'],
        )

    def parse_discovery_themes_page(self, payload: raw.DiscoveryThemesPage, /) -> discovery.DiscoveryThemesPage:
        return discovery.DiscoveryThemesPage(
            themes=list(map(self.parse_discovery_theme, payload['themes'])),
            popular_tags=payload['popularTags'],
        )

    def parse_display_user(self, payload: raw.BannedUser, /) -> DisplayUser:
        avatar = payload.get('avatar')

        return DisplayUser(
            state=self.state,
            id=payload['_id'],
            name=payload['username'],
            discriminator=payload['discriminator'],
            internal_avatar=self.parse_asset(avatar) if avatar else None,
        )

    def parse_embed(self, payload: raw.Embed, /) -> Embed:
        return self._embed_parsers[payload['type']](payload)

    def parse_embed_special(self, payload: raw.Special, /) -> EmbedSpecial:
        return self._embed_special_parsers[payload['type']](payload)

    def parse_emoji(self, payload: raw.Emoji, /) -> Emoji:
        return self._emoji_parsers[payload['parent']['type']](payload)

    def parse_emoji_create_event(self, shard: Shard, payload: raw.ClientEmojiCreateEvent, /) -> ServerEmojiCreateEvent:
        return ServerEmojiCreateEvent(
            shard=shard,
            emoji=self.parse_server_emoji(payload),
        )

    def parse_emoji_delete_event(self, shard: Shard, payload: raw.ClientEmojiDeleteEvent, /) -> ServerEmojiDeleteEvent:
        return ServerEmojiDeleteEvent(
            shard=shard,
            emoji=None,
            server_id=None,
            emoji_id=payload['id'],
        )

    def parse_gif_embed_special(self, _: raw.GIFSpecial, /) -> GifEmbedSpecial:
        return _GIF_EMBED_SPECIAL

    def parse_group_channel(
        self,
        payload: raw.GroupChannel,
        recipients: (tuple[typing.Literal[True], list[str]] | tuple[typing.Literal[False], list[User]]),
        /,
    ) -> GroupChannel:
        """Parses a group channel object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The group channel payload to parse.
        recipients: Union[Tuple[Literal[True], List[:class:`str`]], Tuple[Literal[False], List[:class:`User`]]]
            The group's recipients.

        Returns
        -------
        :class:`GroupChannel`
            The parsed group channel object.
        """

        icon = payload.get('icon')
        permissions = payload.get('permissions')

        return GroupChannel(
            state=self.state,
            id=payload['_id'],
            name=payload['name'],
            owner_id=payload['owner'],
            description=payload.get('description'),
            internal_recipients=recipients,
            internal_icon=self.parse_asset(icon) if icon else None,
            last_message_id=payload.get('last_message_id'),
            permissions=None if permissions is None else Permissions(permissions),
            nsfw=payload.get('nsfw', False),
        )

    def parse_group_invite(self, payload: raw.GroupInvite, /) -> GroupInvite:
        return GroupInvite(
            state=self.state,
            code=payload['_id'],
            creator_id=payload['creator'],
            channel_id=payload['channel'],
        )

    def parse_group_public_invite(self, payload: raw.GroupInviteResponse, /) -> GroupPublicInvite:
        user_avatar = payload.get('user_avatar')

        return GroupPublicInvite(
            state=self.state,
            code=payload['code'],
            channel_id=payload['channel_id'],
            channel_name=payload['channel_name'],
            channel_description=payload.get('channel_description'),
            user_name=payload['user_name'],
            internal_user_avatar=self.parse_asset(user_avatar) if user_avatar else None,
        )

    def parse_image_embed(self, payload: raw.Image, /) -> ImageEmbed:
        return ImageEmbed(
            url=payload['url'],
            width=payload['width'],
            height=payload['height'],
            size=ImageSize(payload['size']),
        )

    def parse_instance(self, payload: raw.RevoltConfig, /) -> Instance:
        return Instance(
            version=payload['revolt'],
            features=self.parse_instance_features_config(payload['features']),
            websocket_url=payload['ws'],
            app_url=payload['app'],
            vapid_public_key=payload['vapid'],
            build=self.parse_instance_build(payload['build']),
        )

    def parse_instance_build(self, payload: raw.BuildInformation, /) -> InstanceBuild:
        try:
            committed_at = _parse_dt(payload['commit_timestamp'])
        except Exception:
            committed_at = None

        try:
            built_at = _parse_dt(payload['timestamp'])
        except Exception:
            built_at = None

        return InstanceBuild(
            commit_as_sha=payload['commit_sha'],
            committed_at=committed_at,
            semver=payload['semver'],
            origin_url=payload['origin_url'],
            built_at=built_at,
        )

    def parse_instance_captcha_feature(self, payload: raw.CaptchaFeature, /) -> InstanceCaptchaFeature:
        return InstanceCaptchaFeature(
            enabled=payload['enabled'],
            key=payload['key'],
        )

    def parse_instance_features_config(self, payload: raw.RevoltFeatures, /) -> InstanceFeaturesConfig:
        try:
            voice: raw.VoiceFeature = payload['livekit']  # pyright: ignore[reportTypedDictNotRequiredAccess]
        except KeyError:
            voice = payload['voso']

        return InstanceFeaturesConfig(
            captcha=self.parse_instance_captcha_feature(payload['captcha']),
            email_verification=payload['email'],
            invite_only=payload['invite_only'],
            autumn=self.parse_instance_generic_feature(payload['autumn']),
            january=self.parse_instance_generic_feature(payload['january']),
            voice=self.parse_instance_voice_feature(voice),
        )

    def parse_instance_generic_feature(self, payload: raw.Feature, /) -> InstanceGenericFeature:
        return InstanceGenericFeature(
            enabled=payload['enabled'],
            url=payload['url'],
        )

    def parse_instance_voice_feature(self, payload: raw.VoiceFeature, /) -> InstanceVoiceFeature:
        return InstanceVoiceFeature(
            enabled=payload['enabled'],
            url=payload['url'],
            websocket_url=payload['ws'],
        )

    def parse_invite(self, payload: raw.Invite, /) -> Invite:
        return self._invite_parsers[payload['type']](payload)

    def parse_lightspeed_embed_special(self, payload: raw.LightspeedSpecial, /) -> LightspeedEmbedSpecial:
        return LightspeedEmbedSpecial(
            content_type=LightspeedContentType(payload['content_type']),
            id=payload['id'],
        )

    def parse_logout_event(self, shard: Shard, payload: raw.ClientLogoutEvent, /) -> LogoutEvent:
        return LogoutEvent(shard=shard)

    def parse_member(
        self,
        d: raw.Member,
        user: User | None = None,
        users: dict[str, User] | None = None,
        /,
    ) -> Member:
        if user and users:
            raise ValueError('Cannot specify both user and users')

        id = d['_id']
        user_id = id['user']

        # if user:
        #    assert user.id == user_id, 'IDs do not match'

        avatar = d.get('avatar')
        timeout = d.get('timeout')

        return Member(
            state=self.state,
            _user=user or (users or _EMPTY_DICT).get(user_id) or user_id,
            server_id=id['server'],
            joined_at=_parse_dt(d['joined_at']),
            nick=d.get('nickname'),
            internal_server_avatar=self.parse_asset(avatar) if avatar else None,
            roles=d.get('roles', []),
            timed_out_until=_parse_dt(timeout) if timeout else None,
        )

    def parse_member_list(self, payload: raw.AllMemberResponse, /) -> MemberList:
        return MemberList(
            members=list(map(self.parse_member, payload['members'])),
            users=list(map(self.parse_user, payload['users'])),
        )

    def parse_members_with_users(self, payload: raw.AllMemberResponse, /) -> list[Member]:
        users = list(map(self.parse_user, payload['users']))

        p = self.parse_member
        return [p(e, users[i]) for i, e in enumerate(payload['members'])]

    def parse_message(
        self,
        payload: raw.Message,
        members: dict[str, Member] = {},
        users: dict[str, User] = {},
        cls: type[Message] = Message,
        /,
    ) -> Message:
        """Parses a message object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The message payload to parse.
        members: Dict[:class:`str`, :class:`Member`]
            The mapping of user IDs to member objects. Required for trying populating :attr:`Message.author`.
        users: Dict[:class:`str`, :class:`User`]
            The mapping of user IDs to user objects. Required for trying populating :attr:`Message.author`.
        cls: Type[:class:`Message`]
            The message class to use when constructing final object.
            The constructor of provided class must be compatible with default one.

        Returns
        -------
        :class:`Message`
            The parsed message object.
        """

        author_id = payload['author']
        webhook = payload.get('webhook')
        system = payload.get('system')
        edited_at = payload.get('edited')
        interactions = payload.get('interactions')
        masquerade = payload.get('masquerade')

        member = payload.get('member')
        user = payload.get('user')

        if member:
            if user:
                author = self.parse_member(member, self.parse_user(user))
            else:
                author = self.parse_member(member)
        elif user:
            author = self.parse_user(user)
        else:
            author = members.get(author_id) or users.get(author_id) or author_id

        flags = _new_message_flags(MessageFlags)
        flags.value = payload.get('flags', 0)

        return cls(
            state=self.state,
            id=payload['_id'],
            nonce=payload.get('nonce'),
            channel_id=payload['channel'],
            internal_author=author,
            webhook=self.parse_message_webhook(webhook) if webhook else None,
            content=payload.get('content', ''),
            internal_system_event=self.parse_message_system_event(system, members, users) if system else None,
            internal_attachments=[self.parse_asset(a) for a in payload.get('attachments', ())],
            edited_at=_parse_dt(edited_at) if edited_at else None,
            internal_embeds=[self.parse_embed(e) for e in payload.get('embeds', ())],
            mention_ids=payload.get('mentions', []),
            replies=payload.get('replies', []),
            reactions={k: tuple(v) for k, v in (payload.get('reactions') or {}).items()},
            interactions=(self.parse_message_interactions(interactions) if interactions else None),
            masquerade=(self.parse_message_masquerade(masquerade) if masquerade else None),
            pinned=payload.get('pinned', False),
            flags=flags,
        )

    def parse_message_append_event(self, shard: Shard, payload: raw.ClientMessageAppendEvent, /) -> MessageAppendEvent:
        data = payload['append']
        embeds = data.get('embeds')

        return MessageAppendEvent(
            shard=shard,
            data=MessageAppendData(
                state=self.state,
                id=payload['id'],
                channel_id=payload['channel'],
                internal_embeds=list(map(self.parse_embed, embeds)) if embeds is not None else UNDEFINED,
            ),
            message=None,
        )

    def parse_message_channel_description_changed_system_event(
        self,
        payload: raw.ChannelDescriptionChangedSystemMessage,
        members: dict[str, Member] = {},
        users: dict[str, User] = {},
        /,
    ) -> StatelessChannelDescriptionChangedSystemEvent:
        by_id = payload['by']

        return StatelessChannelDescriptionChangedSystemEvent(internal_by=users.get(by_id, by_id))

    def parse_message_channel_icon_changed_system_event(
        self,
        payload: raw.ChannelIconChangedSystemMessage,
        members: dict[str, Member] = {},
        users: dict[str, User] = {},
        /,
    ) -> StatelessChannelIconChangedSystemEvent:
        by_id = payload['by']

        return StatelessChannelIconChangedSystemEvent(internal_by=users.get(by_id, by_id))

    def parse_message_channel_renamed_system_event(
        self, payload: raw.ChannelRenamedSystemMessage, members: dict[str, Member] = {}, users: dict[str, User] = {}, /
    ) -> StatelessChannelRenamedSystemEvent:
        by_id = payload['by']

        return StatelessChannelRenamedSystemEvent(
            name=payload['name'],
            internal_by=users.get(by_id, by_id),
        )

    def parse_message_channel_ownership_changed_system_event(
        self,
        payload: raw.ChannelOwnershipChangedSystemMessage,
        members: dict[str, Member] = {},
        users: dict[str, User] = {},
        /,
    ) -> StatelessChannelOwnershipChangedSystemEvent:
        from_id = payload['from']
        to_id = payload['to']

        return StatelessChannelOwnershipChangedSystemEvent(
            internal_from=users.get(from_id, from_id),
            internal_to=users.get(to_id, to_id),
        )

    def parse_message_delete_event(self, shard: Shard, payload: raw.ClientMessageDeleteEvent, /) -> MessageDeleteEvent:
        return MessageDeleteEvent(
            shard=shard,
            channel_id=payload['channel'],
            message_id=payload['id'],
            message=None,
        )

    def parse_message_event(self, shard: Shard, payload: raw.ClientMessageEvent, /) -> MessageCreateEvent:
        return MessageCreateEvent(shard=shard, message=self.parse_message(payload))

    def parse_message_interactions(self, payload: raw.Interactions, /) -> Interactions:
        return Interactions(
            reactions=payload.get('reactions', []),
            restrict_reactions=payload.get('restrict_reactions', False),
        )

    def parse_message_masquerade(self, payload: raw.Masquerade, /) -> Masquerade:
        return Masquerade(name=payload.get('name'), avatar=payload.get('avatar'), colour=payload.get('colour'))

    def parse_message_message_pinned_system_event(
        self,
        payload: raw.MessagePinnedSystemMessage,
        members: dict[str, Member] = {},
        users: dict[str, User] = {},
        /,
    ) -> StatelessMessagePinnedSystemEvent:
        pinned_message_id = payload['id']
        by_id = payload['by']

        return StatelessMessagePinnedSystemEvent(
            pinned_message_id=pinned_message_id,
            internal_by=members.get(by_id, users.get(by_id, by_id)),
        )

    def parse_message_message_unpinned_system_event(
        self, payload: raw.MessageUnpinnedSystemMessage, members: dict[str, Member] = {}, users: dict[str, User] = {}, /
    ) -> StatelessMessageUnpinnedSystemEvent:
        unpinned_message_id = payload['id']
        by_id = payload['by']

        return StatelessMessageUnpinnedSystemEvent(
            unpinned_message_id=unpinned_message_id,
            internal_by=members.get(by_id, users.get(by_id, by_id)),
        )

    def parse_message_react_event(self, shard: Shard, payload: raw.ClientMessageReactEvent, /) -> MessageReactEvent:
        return MessageReactEvent(
            shard=shard,
            channel_id=payload['channel_id'],
            message_id=payload['id'],
            user_id=payload['user_id'],
            emoji=payload['emoji_id'],
            message=None,
        )

    def parse_message_remove_reaction_event(
        self, shard: Shard, payload: raw.ClientMessageRemoveReactionEvent, /
    ) -> MessageClearReactionEvent:
        return MessageClearReactionEvent(
            shard=shard,
            channel_id=payload['channel_id'],
            message_id=payload['id'],
            emoji=payload['emoji_id'],
            message=None,
        )

    def parse_message_system_event(
        self,
        payload: raw.SystemMessage,
        members: dict[str, Member],
        users: dict[str, User],
        /,
    ) -> StatelessSystemEvent:
        return self._message_system_event_parsers[payload['type']](payload, members, users)

    def parse_message_text_system_event(
        self,
        payload: raw.TextSystemMessage,
        members: dict[str, Member] = {},
        users: dict[str, User] = {},
        /,
    ) -> TextSystemEvent:
        return TextSystemEvent(content=payload['content'])

    def parse_message_unreact_event(
        self, shard: Shard, payload: raw.ClientMessageUnreactEvent, /
    ) -> MessageUnreactEvent:
        return MessageUnreactEvent(
            shard=shard,
            channel_id=payload['channel_id'],
            message_id=payload['id'],
            user_id=payload['user_id'],
            emoji=payload['emoji_id'],
            message=None,
        )

    def parse_message_update_event(self, shard: Shard, payload: raw.ClientMessageUpdateEvent, /) -> MessageUpdateEvent:
        data = payload['data']
        clear = payload.get('clear', ())

        content = data.get('content')
        edited_at = data.get('edited')
        embeds = data.get('embeds')
        reactions = data.get('reactions')

        return MessageUpdateEvent(
            shard=shard,
            message=PartialMessage(
                state=self.state,
                id=payload['id'],
                channel_id=payload['channel'],
                content=content if content is not None else UNDEFINED,
                edited_at=_parse_dt(edited_at) if edited_at else UNDEFINED,
                internal_embeds=[self.parse_embed(e) for e in embeds] if embeds is not None else UNDEFINED,
                pinned=False if 'Pinned' in clear else data.get('pinned', UNDEFINED),
                reactions={k: tuple(v) for k, v in reactions.items()} if reactions is not None else UNDEFINED,
            ),
            before=None,
            after=None,
        )

    def parse_message_user_added_system_event(
        self,
        payload: raw.UserAddedSystemMessage,
        members: dict[str, Member] = {},
        users: dict[str, User] = {},
        /,
    ) -> StatelessUserAddedSystemEvent:
        user_id = payload['id']
        by_id = payload['by']

        return StatelessUserAddedSystemEvent(
            internal_user=members.get(user_id, users.get(user_id, user_id)),
            internal_by=members.get(by_id, users.get(by_id, by_id)),
        )

    def parse_message_user_banned_system_event(
        self,
        payload: raw.UserBannedSystemMessage,
        members: dict[str, Member] = {},
        users: dict[str, User] = {},
        /,
    ) -> StatelessUserBannedSystemEvent:
        user_id = payload['id']

        return StatelessUserBannedSystemEvent(internal_user=members.get(user_id, users.get(user_id, user_id)))

    def parse_message_user_joined_system_event(
        self,
        payload: raw.UserJoinedSystemMessage,
        members: dict[str, Member] = {},
        users: dict[str, User] = {},
        /,
    ) -> StatelessUserJoinedSystemEvent:
        user_id = payload['id']

        return StatelessUserJoinedSystemEvent(internal_user=members.get(user_id, users.get(user_id, user_id)))

    def parse_message_user_kicked_system_event(
        self,
        payload: raw.UserKickedSystemMessage,
        members: dict[str, Member] = {},
        users: dict[str, User] = {},
        /,
    ) -> StatelessUserKickedSystemEvent:
        user_id = payload['id']

        return StatelessUserKickedSystemEvent(internal_user=members.get(user_id, users.get(user_id, user_id)))

    def parse_message_user_left_system_event(
        self,
        payload: raw.UserLeftSystemMessage,
        members: dict[str, Member] = {},
        users: dict[str, User] = {},
        /,
    ) -> StatelessUserLeftSystemEvent:
        user_id = payload['id']

        return StatelessUserLeftSystemEvent(internal_user=members.get(user_id, users.get(user_id, user_id)))

    def parse_message_user_remove_system_event(
        self,
        payload: raw.UserRemoveSystemMessage,
        members: dict[str, Member] = {},
        users: dict[str, User] = {},
        /,
    ) -> StatelessUserRemovedSystemEvent:
        user_id = payload['id']
        by_id = payload['by']

        return StatelessUserRemovedSystemEvent(
            internal_user=members.get(user_id, users.get(user_id, user_id)),
            internal_by=members.get(by_id, users.get(by_id, by_id)),
        )

    def parse_message_webhook(self, payload: raw.MessageWebhook, /) -> MessageWebhook:
        return MessageWebhook(
            name=payload['name'],
            avatar=payload.get('avatar'),
        )

    def parse_messages(self, payload: raw.BulkMessageResponse, /) -> list[Message]:
        if isinstance(payload, list):
            return list(map(self.parse_message, payload))
        elif isinstance(payload, dict):
            users = list(map(self.parse_user, payload['users']))
            users_mapping = {u.id: u for u in users}

            members = [self.parse_member(e, None, users_mapping) for e in payload.get('members', ())]
            members_mapping = {m.id: m for m in members}

            return [self.parse_message(e, members_mapping, users_mapping) for e in payload['messages']]
        raise RuntimeError('Unreachable')

    def parse_mfa_response_login(self, payload: raw.a.MFAResponseLogin, friendly_name: str | None, /) -> MFARequired:
        return MFARequired(
            ticket=payload['ticket'],
            allowed_methods=list(map(MFAMethod, payload['allowed_methods'])),
            state=self.state,
            internal_friendly_name=friendly_name,
        )

    def parse_mfa_ticket(self, payload: raw.a.MFATicket, /) -> MFATicket:
        return MFATicket(
            id=payload['_id'],
            account_id=payload['account_id'],
            token=payload['token'],
            validated=payload['validated'],
            authorised=payload['authorised'],
            last_totp_code=payload.get('last_totp_code'),
        )

    def parse_multi_factor_status(self, payload: raw.a.MultiFactorStatus, /) -> MFAStatus:
        return MFAStatus(
            totp_mfa=payload['totp_mfa'],
            recovery_active=payload['recovery_active'],
        )

    def parse_mutuals(self, payload: raw.MutualResponse, /) -> Mutuals:
        return Mutuals(
            user_ids=payload['users'],
            server_ids=payload['servers'],
        )

    def parse_none_embed(self, _: raw.NoneEmbed, /) -> NoneEmbed:
        return _NONE_EMBED

    def parse_none_embed_special(self, _: raw.NoneSpecial, /) -> NoneEmbedSpecial:
        return _NONE_EMBED_SPECIAL

    def parse_own_user(self, payload: raw.User, /) -> OwnUser:
        avatar = payload.get('avatar')
        status = payload.get('status')
        # profile = payload.get("profile")
        privileged = payload.get('privileged', False)

        badges = _new_user_badges(UserBadges)
        badges.value = payload.get('badges', 0)

        flags = _new_user_flags(UserFlags)
        flags.value = payload.get('flags', 0)

        bot = payload.get('bot')

        relations = list(map(self.parse_relationship, payload.get('relations', ())))

        return OwnUser(
            state=self.state,
            id=payload['_id'],
            name=payload['username'],
            discriminator=payload['discriminator'],
            display_name=payload.get('display_name'),
            internal_avatar=self.parse_asset(avatar) if avatar else None,
            relations={relation.id: relation for relation in relations},
            badges=badges,
            status=self.parse_user_status(status) if status else None,
            # internal_profile=self.parse_user_profile(profile) if profile else None,
            flags=flags,
            privileged=privileged or False,
            bot=self.parse_bot_user_info(bot) if bot else None,
            relationship=RelationshipStatus(payload['relationship']),
            online=payload['online'],
        )

    def parse_partial_account(self, payload: raw.a.AccountInfo, /) -> PartialAccount:
        return PartialAccount(id=payload['_id'], email=payload['email'])

    def parse_partial_session(self, payload: raw.a.SessionInfo, /) -> PartialSession:
        return PartialSession(state=self.state, id=payload['_id'], name=payload['name'])

    def parse_partial_user_profile(
        self, payload: raw.UserProfile, clear: list[raw.FieldsUser], /
    ) -> PartialUserProfile:
        background = payload.get('background')

        return PartialUserProfile(
            state=self.state,
            content=(None if 'ProfileContent' in clear else payload.get('content') or UNDEFINED),
            internal_background=(
                None if 'ProfileBackground' in clear else self.parse_asset(background) if background else UNDEFINED
            ),
        )

    def parse_permission_override(self, payload: raw.Override, /) -> PermissionOverride:
        allow = _new_permissions(Permissions)
        allow.value = payload['allow']

        deny = _new_permissions(Permissions)
        deny.value = payload['deny']

        return PermissionOverride(allow=allow, deny=deny)

    def parse_permission_override_field(self, payload: raw.OverrideField, /) -> PermissionOverride:
        allow = _new_permissions(Permissions)
        allow.value = payload['a']

        deny = _new_permissions(Permissions)
        deny.value = payload['d']

        return PermissionOverride(allow=allow, deny=deny)

    def parse_public_bot(self, payload: raw.PublicBot, /) -> PublicBot:
        return PublicBot(
            state=self.state,
            id=payload['_id'],
            username=payload['username'],
            internal_avatar_id=payload.get('avatar'),
            description=payload.get('description', ''),
        )

    def parse_public_invite(self, payload: raw.InviteResponse, /) -> BaseInvite:
        return self._public_invite_parsers.get(payload['type'], self.parse_unknown_public_invite)(payload)

    def parse_ready_event(self, shard: Shard, payload: raw.ClientReadyEvent, /) -> ReadyEvent:
        users = list(map(self.parse_user, payload.get('users', ())))
        servers = [self.parse_server(s, (True, s['channels'])) for s in payload.get('servers', ())]
        channels: list[Channel] = list(map(self.parse_channel, payload.get('channels', ())))  # type: ignore
        members = list(map(self.parse_member, payload.get('members', ())))
        emojis = list(map(self.parse_server_emoji, payload.get('emojis', ())))
        user_settings = self.parse_user_settings(payload.get('user_settings', {}), False)
        read_states = list(map(self.parse_channel_unread, payload.get('channel_unreads', ())))

        me = users[-1]
        if me.__class__ is not OwnUser or not isinstance(me, OwnUser):
            for user in users:
                if me.__class__ is not OwnUser or isinstance(me, OwnUser):
                    me = user

        if me.__class__ is not OwnUser or not isinstance(me, OwnUser):
            raise TypeError('Unable to find own user')

        return ReadyEvent(
            shard=shard,
            users=users,
            servers=servers,
            channels=channels,
            members=members,
            emojis=emojis,
            me=me,  # type: ignore
            user_settings=user_settings,
            read_states=read_states,
        )

    def parse_relationship(self, payload: raw.Relationship, /) -> Relationship:
        return Relationship(
            id=payload['_id'],
            status=RelationshipStatus(payload['status']),
        )

    def parse_response_login(self, payload: raw.a.ResponseLogin, friendly_name: str | None, /) -> LoginResult:
        if payload['result'] == 'Success':
            return self.parse_session(payload)
        elif payload['result'] == 'MFA':
            return self.parse_mfa_response_login(payload, friendly_name)
        elif payload['result'] == 'Disabled':
            return self.parse_disabled_response_login(payload)
        else:
            raise NotImplementedError(payload)

    def parse_response_webhook(self, payload: raw.ResponseWebhook, /) -> Webhook:
        id = payload['id']
        avatar = payload.get('avatar')
        permissions = _new_permissions(Permissions)
        permissions.value = payload['permissions']

        return Webhook(
            state=self.state,
            id=id,
            name=payload['name'],
            internal_avatar=(
                StatelessAsset(
                    id=avatar,
                    filename='',
                    metadata=AssetMetadata(
                        type=AssetMetadataType.image,
                        width=None,
                        height=None,
                    ),
                    content_type='',
                    size=0,
                    deleted=False,
                    reported=False,
                    message_id=None,
                    user_id=id,
                    server_id=None,
                    object_id=None,
                )
                if avatar
                else None
            ),
            channel_id=payload['channel_id'],
            permissions=permissions,
            token=None,
        )

    def parse_role(self, payload: raw.Role, role_id: str, server_id: str, /) -> Role:
        return Role(
            state=self.state,
            id=role_id,
            name=payload['name'],
            permissions=self.parse_permission_override_field(payload['permissions']),
            colour=payload.get('colour'),
            hoist=payload.get('hoist', False),
            rank=payload['rank'],
            server_id=server_id,
        )

    def parse_saved_messages_channel(self, payload: raw.SavedMessagesChannel, /) -> SavedMessagesChannel:
        """Parses a saved messages channel object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The saved messages channel payload to parse.

        Returns
        -------
        :class:`SavedMessagesChannel`
            The parsed saved messages channel object.
        """
        return SavedMessagesChannel(
            state=self.state,
            id=payload['_id'],
            user_id=payload['user'],
        )

    def _parse_server(
        self,
        d: raw.Server,
        channels: (tuple[typing.Literal[True], list[str]] | tuple[typing.Literal[False], list[ServerChannel]]),
        /,
    ) -> Server:
        server_id = d['_id']

        categories = d.get('categories', [])
        system_messages = d.get('system_messages')

        roles = {}
        for id, role_data in d.get('roles', {}).items():
            role_id = id
            roles[role_id] = self.parse_role(role_data, role_id, server_id)

        icon = d.get('icon')
        banner = d.get('banner')

        flags = _new_server_flags(ServerFlags)
        flags.value = d.get('flags', 0)

        return Server(
            state=self.state,
            id=server_id,
            owner_id=d['owner'],
            name=d['name'],
            description=d.get('description'),
            internal_channels=channels,
            categories=[self.parse_category(e) for e in categories],
            system_messages=(self.parse_system_message_channels(system_messages) if system_messages else None),
            roles=roles,
            default_permissions=Permissions(d['default_permissions']),
            internal_icon=self.parse_asset(icon) if icon else None,
            internal_banner=self.parse_asset(banner) if banner else None,
            flags=flags,
            nsfw=d.get('nsfw', False),
            analytics=d.get('analytics', False),
            discoverable=d.get('discoverable', False),
        )

    def parse_server(
        self,
        d: raw.Server,
        channels: (tuple[typing.Literal[True], list[str]] | tuple[typing.Literal[False], list[raw.ServerChannel]]),
        /,
    ) -> Server:
        internal_channels: (
            tuple[typing.Literal[True], list[str]] | tuple[typing.Literal[False], list[ServerChannel]]
        ) = (
            (True, [str(i) for i in channels[1]])
            if channels[0]
            else (False, [self.parse_channel(c) for c in channels[1]])  # type: ignore
        )
        return self._parse_server(d, internal_channels)

    def parse_server_create_event(
        self, shard: Shard, d: raw.ClientServerCreateEvent, joined_at: datetime, /
    ) -> ServerCreateEvent:
        return ServerCreateEvent(
            shard=shard,
            joined_at=joined_at,
            server=self.parse_server(d['server'], (False, d['channels'])),
            emojis=[self.parse_server_emoji(e) for e in d['emojis']],
        )

    def parse_server_delete_event(self, shard: Shard, payload: raw.ClientServerDeleteEvent, /) -> ServerDeleteEvent:
        return ServerDeleteEvent(
            shard=shard,
            server_id=payload['id'],
            server=None,
        )

    def parse_server_emoji(self, payload: raw.ServerEmoji, /) -> ServerEmoji:
        return ServerEmoji(
            state=self.state,
            id=payload['_id'],
            server_id=payload['parent']['id'],
            creator_id=payload['creator_id'],
            name=payload['name'],
            animated=payload.get('animated', False),
            nsfw=payload.get('nsfw', False),
        )

    def parse_server_invite(self, payload: raw.ServerInvite, /) -> ServerInvite:
        return ServerInvite(
            state=self.state,
            code=payload['_id'],
            creator_id=payload['creator'],
            server_id=payload['server'],
            channel_id=payload['channel'],
        )

    def parse_server_member_join_event(
        self, shard: Shard, payload: raw.ClientServerMemberJoinEvent, joined_at: datetime, /
    ) -> ServerMemberJoinEvent:
        return ServerMemberJoinEvent(
            shard=shard,
            member=Member(
                state=self.state,
                server_id=payload['id'],
                _user=payload['user'],
                joined_at=joined_at,
                nick=None,
                internal_server_avatar=None,
                roles=[],
                timed_out_until=None,
            ),
        )

    def parse_server_member_leave_event(
        self, shard: Shard, payload: raw.ClientServerMemberLeaveEvent, /
    ) -> ServerMemberRemoveEvent:
        return ServerMemberRemoveEvent(
            shard=shard,
            server_id=payload['id'],
            user_id=payload['user'],
            member=None,
            reason=MemberRemovalIntention(payload['reason']),
        )

    def parse_server_member_update_event(
        self, shard: Shard, payload: raw.ClientServerMemberUpdateEvent, /
    ) -> ServerMemberUpdateEvent:
        id = payload['id']
        data = payload['data']
        clear = payload['clear']

        avatar = data.get('avatar')
        roles = data.get('roles')
        timeout = data.get('timeout')

        return ServerMemberUpdateEvent(
            shard=shard,
            member=PartialMember(
                state=self.state,
                server_id=id['server'],
                _user=id['user'],
                nick=None if 'Nickname' in clear else data.get('nickname', UNDEFINED),
                internal_server_avatar=None if 'Avatar' in clear else self.parse_asset(avatar) if avatar else UNDEFINED,
                roles=[] if 'Roles' in clear else roles if roles is not None else UNDEFINED,
                timed_out_until=(None if 'Timeout' in clear else _parse_dt(timeout) if timeout else UNDEFINED),
            ),
            before=None,  # filled on dispatch
            after=None,  # filled on dispatch
        )

    def parse_server_public_invite(self, payload: raw.ServerInviteResponse, /) -> ServerPublicInvite:
        server_icon = payload.get('server_icon')
        server_banner = payload.get('server_banner')
        server_flags = _new_server_flags(ServerFlags)
        server_flags.value = payload.get('server_flags', 0)

        user_avatar = payload.get('user_avatar')

        return ServerPublicInvite(
            state=self.state,
            code=payload['code'],
            server_id=payload['server_id'],
            server_name=payload['server_name'],
            internal_server_icon=self.parse_asset(server_icon) if server_icon else None,
            internal_server_banner=(self.parse_asset(server_banner) if server_banner else None),
            flags=server_flags,
            channel_id=payload['channel_id'],
            channel_name=payload['channel_name'],
            channel_description=payload.get('channel_description'),
            user_name=payload['user_name'],
            internal_user_avatar=self.parse_asset(user_avatar) if user_avatar else None,
            members_count=payload['member_count'],
        )

    def parse_server_role_delete_event(
        self, shard: Shard, payload: raw.ClientServerRoleDeleteEvent, /
    ) -> ServerRoleDeleteEvent:
        return ServerRoleDeleteEvent(
            shard=shard,
            server_id=payload['id'],
            role_id=payload['role_id'],
            server=None,
            role=None,
        )

    def parse_server_role_update_event(
        self, shard: Shard, payload: raw.ClientServerRoleUpdateEvent, /
    ) -> RawServerRoleUpdateEvent:
        data = payload['data']
        clear = payload['clear']

        permissions = data.get('permissions')

        return RawServerRoleUpdateEvent(
            shard=shard,
            role=PartialRole(
                state=self.state,
                id=payload['role_id'],
                server_id=payload['id'],
                name=data.get('name') or UNDEFINED,
                permissions=(self.parse_permission_override_field(permissions) if permissions else UNDEFINED),
                colour=(None if 'Colour' in clear else data.get('colour', UNDEFINED)),
                hoist=data.get('hoist', UNDEFINED),
                rank=data.get('rank', UNDEFINED),
            ),
            old_role=None,
            new_role=None,
            server=None,
        )

    def parse_server_update_event(self, shard: Shard, payload: raw.ClientServerUpdateEvent, /) -> ServerUpdateEvent:
        data = payload['data']
        clear = payload['clear']

        description = data.get('description')
        categories = data.get('categories')
        system_messages = data.get('system_messages')
        default_permissions = data.get('default_permissions')
        icon = data.get('icon')
        banner = data.get('banner')
        flags = data.get('flags')

        return ServerUpdateEvent(
            shard=shard,
            server=PartialServer(
                state=self.state,
                id=payload['id'],
                owner_id=data.get('owner', UNDEFINED),
                name=data.get('name', UNDEFINED),
                description=(None if 'Description' in clear else description if description is not None else UNDEFINED),
                channel_ids=data.get('channels', UNDEFINED),
                categories=(
                    []
                    if 'Categories' in clear
                    else ([self.parse_category(c) for c in categories] if categories is not None else UNDEFINED)
                ),
                system_messages=(
                    None
                    if 'SystemMessages' in clear
                    else (
                        self.parse_system_message_channels(system_messages)
                        if system_messages is not None
                        else UNDEFINED
                    )
                ),
                default_permissions=(
                    Permissions(default_permissions) if default_permissions is not None else UNDEFINED
                ),
                internal_icon=(None if 'Icon' in clear else self.parse_asset(icon) if icon else UNDEFINED),
                internal_banner=(None if 'Banner' in clear else self.parse_asset(banner) if banner else UNDEFINED),
                flags=(ServerFlags(flags) if flags is not None else UNDEFINED),
                discoverable=data.get('discoverable', UNDEFINED),
                analytics=data.get('analytics', UNDEFINED),
            ),
            before=None,  # filled on dispatch
            after=None,  # filled on dispatch
        )

    def parse_session(self, payload: raw.a.Session, /) -> Session:
        subscription = payload.get('subscription')

        return Session(
            state=self.state,
            id=payload['_id'],
            name=payload['name'],
            user_id=payload['user_id'],
            token=payload['token'],
            subscription=(self.parse_webpush_subscription(subscription) if subscription else None),
        )

    def parse_soundcloud_embed_special(self, _: raw.SoundcloudSpecial, /) -> SoundcloudEmbedSpecial:
        return _SOUNDCLOUD_EMBED_SPECIAL

    def parse_spotify_embed_special(self, payload: raw.SpotifySpecial, /) -> SpotifyEmbedSpecial:
        return SpotifyEmbedSpecial(
            content_type=payload['content_type'],
            id=payload['id'],
        )

    def parse_streamable_embed_special(self, payload: raw.StreamableSpecial, /) -> StreamableEmbedSpecial:
        return StreamableEmbedSpecial(id=payload['id'])

    def parse_system_message_channels(self, payload: raw.SystemMessageChannels, /) -> SystemMessageChannels:
        return SystemMessageChannels(
            user_joined=payload.get('user_joined'),
            user_left=payload.get('user_left'),
            user_kicked=payload.get('user_kicked'),
            user_banned=payload.get('user_banned'),
        )

    def parse_text_channel(self, payload: raw.TextChannel, /) -> ServerTextChannel:
        """Parses a text channel object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The text channel payload to parse.

        Returns
        -------
        :class:`ServerTextChannel`
            The parsed text channel object.
        """

        icon = payload.get('icon')
        default_permissions = payload.get('default_permissions')
        role_permissions = payload.get('role_permissions', {})

        try:
            last_message_id = payload['last_message_id']  # pyright: ignore[reportTypedDictNotRequiredAccess]
        except KeyError:
            last_message_id = None

        voice = payload.get('voice')

        return ServerTextChannel(
            state=self.state,
            id=payload['_id'],
            server_id=payload['server'],
            name=payload['name'],
            description=payload.get('description'),
            internal_icon=self.parse_asset(icon) if icon else None,
            last_message_id=last_message_id,
            default_permissions=(
                None if default_permissions is None else self.parse_permission_override_field(default_permissions)
            ),
            role_permissions={k: self.parse_permission_override_field(v) for k, v in role_permissions.items()},
            nsfw=payload.get('nsfw', False),
            voice=self.parse_voice_information(voice) if voice else None,
        )

    def parse_text_embed(self, payload: raw.TextEmbed, /) -> StatelessTextEmbed:
        media = payload.get('media')

        return StatelessTextEmbed(
            icon_url=payload.get('icon_url'),
            url=payload.get('url'),
            title=payload.get('title'),
            description=payload.get('description'),
            internal_media=self.parse_asset(media) if media else None,
            colour=payload.get('colour'),
        )

    def parse_twitch_embed_special(self, payload: raw.TwitchSpecial, /) -> TwitchEmbedSpecial:
        return TwitchEmbedSpecial(
            content_type=TwitchContentType(payload['content_type']),
            id=payload['id'],
        )

    def parse_unknown_public_invite(self, payload: dict[str, typing.Any], /) -> UnknownPublicInvite:
        return UnknownPublicInvite(state=self.state, code=payload['code'], payload=payload)

    def parse_user(self, payload: raw.User, /) -> User | OwnUser:
        if payload['relationship'] == 'User':
            return self.parse_own_user(payload)

        avatar = payload.get('avatar')
        status = payload.get('status')

        badges = _new_user_badges(UserBadges)
        badges.value = payload.get('badges', 0)

        flags = _new_user_flags(UserFlags)
        flags.value = payload.get('flags', 0)

        bot = payload.get('bot')

        return User(
            state=self.state,
            id=payload['_id'],
            name=payload['username'],
            discriminator=payload['discriminator'],
            display_name=payload.get('display_name'),
            internal_avatar=self.parse_asset(avatar) if avatar else None,
            badges=badges,
            status=self.parse_user_status(status) if status else None,
            # internal_profile=self.parse_user_profile(profile) if profile else None,
            flags=flags,
            privileged=payload.get('privileged', False),
            bot=self.parse_bot_user_info(bot) if bot else None,
            relationship=RelationshipStatus(payload['relationship']),
            online=payload['online'],
        )

    def parse_user_platform_wipe_event(
        self, shard: Shard, payload: raw.ClientUserPlatformWipeEvent, /
    ) -> UserPlatformWipeEvent:
        return UserPlatformWipeEvent(
            shard=shard,
            user_id=payload['user_id'],
            flags=UserFlags(payload['flags']),
            before=None,
            after=None,
        )

    def parse_user_profile(self, payload: raw.UserProfile, /) -> StatelessUserProfile:
        background = payload.get('background')

        return StatelessUserProfile(
            content=payload.get('content'),
            internal_background=self.parse_asset(background) if background else None,
        )

    def parse_user_relationship_event(
        self, shard: Shard, payload: raw.ClientUserRelationshipEvent, /
    ) -> UserRelationshipUpdateEvent:
        return UserRelationshipUpdateEvent(
            shard=shard,
            current_user_id=payload['id'],
            old_user=None,
            new_user=self.parse_user(payload['user']),
            before=None,
        )

    def parse_user_settings(self, payload: raw.UserSettings, partial: bool, /) -> UserSettings:
        return UserSettings(
            data={k: (s1, s2) for (k, (s1, s2)) in payload.items()},
            state=self.state,
            mocked=False,
            partial=partial,
        )

    def parse_user_settings_update_event(
        self, shard: Shard, payload: raw.ClientUserSettingsUpdateEvent, /
    ) -> UserSettingsUpdateEvent:
        partial = self.parse_user_settings(payload['update'], True)

        before = shard.state.settings

        if not before.mocked:
            before = copy(before)
            after = copy(before)
            after._update(partial)
        else:
            after = before

        return UserSettingsUpdateEvent(
            shard=shard,
            current_user_id=payload['id'],
            partial=partial,
            before=before,
            after=after,
        )

    def parse_user_status(self, payload: raw.UserStatus, /) -> UserStatus:
        presence = payload.get('presence')

        return UserStatus(
            text=payload.get('text'),
            presence=Presence(presence) if presence else None,
        )

    def parse_user_status_edit(self, payload: raw.UserStatus, clear: list[raw.FieldsUser], /) -> UserStatusEdit:
        presence = payload.get('presence')

        return UserStatusEdit(
            text=None if 'StatusText' in clear else payload.get('text', UNDEFINED),
            presence=(None if 'StatusPresence' in clear else Presence(presence) if presence else UNDEFINED),
        )

    def parse_user_update_event(self, shard: Shard, payload: raw.ClientUserUpdateEvent, /) -> UserUpdateEvent:
        user_id = payload['id']
        data = payload['data']
        clear = payload['clear']

        avatar = data.get('avatar')
        badges = data.get('badges')
        status = data.get('status')
        profile = data.get('profile')
        flags = data.get('flags')

        return UserUpdateEvent(
            shard=shard,
            user=PartialUser(
                state=self.state,
                id=user_id,
                name=data.get('username', UNDEFINED),
                discriminator=data.get('discriminator', UNDEFINED),
                display_name=(None if 'DisplayName' in clear else data.get('display_name') or UNDEFINED),
                internal_avatar=(None if 'Avatar' in clear else self.parse_asset(avatar) if avatar else UNDEFINED),
                badges=UserBadges(badges) if badges is not None else UNDEFINED,
                status=(self.parse_user_status_edit(status, clear) if status is not None else UNDEFINED),
                internal_profile=(
                    self.parse_partial_user_profile(profile, clear) if profile is not None else UNDEFINED
                ),
                flags=UserFlags(flags) if flags is not None else UNDEFINED,
                online=data.get('online', UNDEFINED),
            ),
            before=None,  # filled on dispatch
            after=None,  # filled on dispatch
        )

    def parse_video_embed(self, payload: raw.Video, /) -> VideoEmbed:
        return VideoEmbed(
            url=payload['url'],
            width=payload['width'],
            height=payload['height'],
        )

    def parse_voice_channel(self, payload: raw.VoiceChannel, /) -> VoiceChannel:
        """Parses a voice channel object.

        .. deprecated:: 0.7.0
            The method was deprecated in favour of :meth:`.parse_text_channel` and
            using :attr:`ServerTextChannel.voice` instead.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The voice channel payload to parse.

        Returns
        -------
        :class:`VoiceChannel`
            The parsed voice channel object.
        """

        icon = payload.get('icon')
        default_permissions = payload.get('default_permissions')
        role_permissions = payload.get('role_permissions', {})

        return VoiceChannel(
            state=self.state,
            id=payload['_id'],
            server_id=payload['server'],
            name=payload['name'],
            description=payload.get('description'),
            internal_icon=self.parse_asset(icon) if icon else None,
            default_permissions=(
                None if default_permissions is None else self.parse_permission_override_field(default_permissions)
            ),
            role_permissions={k: self.parse_permission_override_field(v) for k, v in role_permissions.items()},
            nsfw=payload.get('nsfw', False),
        )

    def parse_voice_information(self, payload: raw.VoiceInformation, /) -> ChannelVoiceMetadata:
        return ChannelVoiceMetadata(max_users=payload.get('max_users') or 0)

    def parse_webhook(self, payload: raw.Webhook, /) -> Webhook:
        avatar = payload.get('avatar')
        permissions = _new_permissions(Permissions)
        permissions.value = payload['permissions']

        return Webhook(
            state=self.state,
            id=payload['id'],
            name=payload['name'],
            internal_avatar=self.parse_asset(avatar) if avatar else None,
            channel_id=payload['channel_id'],
            permissions=permissions,
            token=payload.get('token'),
        )

    def parse_webhook_create_event(self, shard: Shard, payload: raw.ClientWebhookCreateEvent, /) -> WebhookCreateEvent:
        return WebhookCreateEvent(
            shard=shard,
            webhook=self.parse_webhook(payload),
        )

    def parse_webhook_update_event(self, shard: Shard, payload: raw.ClientWebhookUpdateEvent, /) -> WebhookUpdateEvent:
        data = payload['data']
        remove = payload['remove']

        avatar = data.get('avatar')
        permissions = data.get('permissions')

        return WebhookUpdateEvent(
            shard=shard,
            webhook=PartialWebhook(
                state=self.state,
                id=payload['id'],
                name=data.get('name', UNDEFINED),
                internal_avatar=(None if 'Avatar' in remove else self.parse_asset(avatar) if avatar else UNDEFINED),
                permissions=(Permissions(permissions) if permissions is not None else UNDEFINED),
            ),
        )

    def parse_webhook_delete_event(self, shard: Shard, payload: raw.ClientWebhookDeleteEvent, /) -> WebhookDeleteEvent:
        return WebhookDeleteEvent(
            shard=shard,
            webhook=None,
            webhook_id=payload['id'],
        )

    def parse_webpush_subscription(self, payload: raw.a.WebPushSubscription, /) -> WebPushSubscription:
        return WebPushSubscription(
            endpoint=payload['endpoint'],
            p256dh=payload['p256dh'],
            auth=payload['auth'],
        )

    def parse_website_embed(self, payload: raw.WebsiteEmbed, /) -> WebsiteEmbed:
        special = payload.get('special')
        image = payload.get('image')
        video = payload.get('video')

        return WebsiteEmbed(
            url=payload.get('url'),
            original_url=payload.get('original_url'),
            special=self.parse_embed_special(special) if special else None,
            title=payload.get('title'),
            description=payload.get('description'),
            image=self.parse_image_embed(image) if image else None,
            video=self.parse_video_embed(video) if video else None,
            site_name=payload.get('site_name'),
            icon_url=payload.get('icon_url'),
            colour=payload.get('colour'),
        )

    def parse_youtube_embed_special(self, payload: raw.YouTubeSpecial) -> YouTubeEmbedSpecial:
        return YouTubeEmbedSpecial(id=payload['id'], timestamp=payload.get('timestamp'))


__all__ = ('Parser',)
