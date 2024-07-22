from __future__ import annotations

from copy import copy
from datetime import datetime
import logging
import typing

from . import core, discovery
from .auth import (
    PartialAccount,
    MFATicket,
    WebPushSubscription,
    PartialSession,
    Session,
    MFAMethod,
    MFARequired,
    AccountDisabled,
    MFAStatus,
    LoginResult,
)
from .bot import BotFlags, Bot, PublicBot
from .cdn import (
    AssetMetadataType,
    AssetMetadata,
    StatelessAsset,
)
from .channel import (
    PartialChannel,
    SavedMessagesChannel,
    DMChannel,
    GroupChannel,
    ServerTextChannel,
    VoiceChannel,
    ServerChannel,
    Channel,
)
from .embed import (
    EmbedSpecial,
    NoneEmbedSpecial,
    _NONE_EMBED_SPECIAL,
    GifEmbedSpecial,
    _GIF_EMBED_SPECIAL,
    YouTubeEmbedSpecial,
    LightspeedContentType,
    LightspeedEmbedSpecial,
    TwitchContentType,
    TwitchEmbedSpecial,
    SpotifyEmbedSpecial,
    SoundcloudEmbedSpecial,
    _SOUNDCLOUD_EMBED_SPECIAL,
    BandcampContentType,
    BandcampEmbedSpecial,
    StreamableEmbedSpecial,
    ImageSize,
    ImageEmbed,
    VideoEmbed,
    WebsiteEmbed,
    StatelessTextEmbed,
    NoneEmbed,
    _NONE_EMBED,
    Embed,
)
from .emoji import ServerEmoji, DetachedEmoji, Emoji
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
    UserAddedSystemEvent,
    UserRemovedSystemEvent,
    UserJoinedSystemEvent,
    UserLeftSystemEvent,
    UserKickedSystemEvent,
    UserBannedSystemEvent,
    ChannelRenamedSystemEvent,
    ChannelDescriptionChangedSystemEvent,
    ChannelIconChangedSystemEvent,
    ChannelOwnershipChangedSystemEvent,
    MessagePinnedSystemEvent,
    MessageUnpinnedSystemEvent,
    SystemEvent,
    MessageFlags,
    Message,
)
from .permissions import Permissions, PermissionOverride
from .read_state import ReadState
from .server import (
    ServerFlags,
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
    MemberRemovalIntention,
)
from .user_settings import UserSettings
from .user import (
    Presence,
    UserStatus,
    UserStatusEdit,
    StatelessUserProfile,
    PartialUserProfile,
    UserBadges,
    UserFlags,
    RelationshipStatus,
    Relationship,
    Mutuals,
    PartialUser,
    DisplayUser,
    BotUserInfo,
    User,
    SelfUser,
)
from .webhook import PartialWebhook, Webhook

if typing.TYPE_CHECKING:
    from . import raw
    from .shard import Shard
    from .state import State

_L = logging.getLogger(__name__)


_EMPTY_DICT: dict[typing.Any, typing.Any] = {}


class Parser:
    def __init__(self, state: State) -> None:
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

    def parse_asset_metadata(self, d: raw.Metadata) -> AssetMetadata:
        return AssetMetadata(
            type=AssetMetadataType(d['type']),
            width=d.get('width'),
            height=d.get('height'),
        )

    def parse_asset(self, d: raw.File) -> StatelessAsset:
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

    def parse_auth_event(self, shard: Shard, d: raw.ClientAuthEvent) -> AuthifierEvent:
        if d['event_type'] == 'CreateSession':
            return SessionCreateEvent(
                shard=shard,
                session=self.parse_session(d['session']),
            )
        elif d['event_type'] == 'DeleteSession':
            return SessionDeleteEvent(
                shard=shard,
                user_id=d['user_id'],
                session_id=d['session_id'],
            )
        elif d['event_type'] == 'DeleteAllSessions':
            return SessionDeleteAllEvent(
                shard=shard,
                user_id=d['user_id'],
                exclude_session_id=d.get('exclude_session_id'),
            )
        else:
            raise NotImplementedError('Unimplemented auth event type', d)

    def parse_authenticated_event(self, shard: Shard, d: raw.ClientAuthenticatedEvent) -> AuthenticatedEvent:
        return AuthenticatedEvent(shard=shard)

    # basic end, internals start

    def _parse_group_channel(self, d: raw.GroupChannel) -> GroupChannel:
        return self.parse_group_channel(
            d,
            (
                True,
                d['recipients'],
            ),
        )

    # internals end

    def parse_ban(self, d: raw.ServerBan, users: dict[str, DisplayUser]) -> Ban:
        id = d['_id']
        user_id = id['user']

        return Ban(
            server_id=id['server'],
            user_id=user_id,
            reason=d['reason'],
            user=users.get(user_id),
        )

    def parse_bandcamp_embed_special(self, d: raw.BandcampSpecial) -> BandcampEmbedSpecial:
        return BandcampEmbedSpecial(
            content_type=BandcampContentType(d['content_type']),
            id=d['id'],
        )

    def parse_bans(self, d: raw.BanListResult) -> list[Ban]:
        banned_users = {bu.id: bu for bu in (self.parse_display_user(e) for e in d['users'])}
        return [self.parse_ban(e, banned_users) for e in d['bans']]

    def _parse_bot(self, d: raw.Bot, user: User) -> Bot:
        return Bot(
            state=self.state,
            id=d['_id'],
            owner_id=d['owner'],
            token=d['token'],
            public=d['public'],
            analytics=d.get('analytics', False),
            discoverable=d.get('discoverable', False),
            interactions_url=d.get('interactions_url'),
            terms_of_service_url=d.get('terms_of_service_url'),
            privacy_policy_url=d.get('privacy_policy_url'),
            flags=BotFlags(d.get('flags', 0)),
            user=user,
        )

    def parse_bot(self, d: raw.Bot, user: raw.User) -> Bot:
        return self._parse_bot(d, self.parse_user(user))

    def parse_bot_user_info(self, d: raw.BotInformation) -> BotUserInfo:
        return BotUserInfo(owner_id=d['owner'])

    def parse_bots(self, d: raw.OwnedBotsResponse) -> list[Bot]:
        bots = d['bots']
        users = d['users']

        if len(bots) != len(users):
            raise RuntimeError(f'Expected {len(bots)} users but got {len(users)}')
        return [self.parse_bot(e, users[i]) for i, e in enumerate(bots)]

    def parse_bulk_message_delete_event(
        self, shard: Shard, d: raw.ClientBulkMessageDeleteEvent
    ) -> BulkMessageDeleteEvent:
        return BulkMessageDeleteEvent(
            shard=shard,
            channel_id=d['channel'],
            message_ids=d['ids'],
        )

    def parse_category(self, d: raw.Category) -> Category:
        return Category(
            id=d['id'],
            title=d['title'],
            channels=d['channels'],  # type: ignore
        )

    def parse_channel_ack_event(self, shard: Shard, d: raw.ClientChannelAckEvent) -> MessageAckEvent:
        return MessageAckEvent(
            shard=shard,
            channel_id=d['id'],
            message_id=d['message_id'],
            user_id=d['user'],
        )

    def parse_channel_create_event(self, shard: Shard, d: raw.ClientChannelCreateEvent) -> ChannelCreateEvent:
        channel = self.parse_channel(d)
        if isinstance(
            channel,
            (SavedMessagesChannel, DMChannel, GroupChannel),
        ):
            return PrivateChannelCreateEvent(shard=shard, channel=channel)
        else:
            return ServerChannelCreateEvent(shard=shard, channel=channel)

    def parse_channel_delete_event(self, shard: Shard, d: raw.ClientChannelDeleteEvent) -> ChannelDeleteEvent:
        return ChannelDeleteEvent(
            shard=shard,
            channel_id=d['id'],
            channel=None,
        )

    def parse_channel_group_join_event(
        self, shard: Shard, d: raw.ClientChannelGroupJoinEvent
    ) -> GroupRecipientAddEvent:
        return GroupRecipientAddEvent(
            shard=shard,
            channel_id=d['id'],
            user_id=d['user'],
            group=None,
        )

    def parse_channel_group_leave_event(
        self, shard: Shard, d: raw.ClientChannelGroupLeaveEvent
    ) -> GroupRecipientRemoveEvent:
        return GroupRecipientRemoveEvent(
            shard=shard,
            channel_id=d['id'],
            user_id=d['user'],
            group=None,
        )

    def parse_channel_start_typing_event(
        self, shard: Shard, d: raw.ClientChannelStartTypingEvent
    ) -> ChannelStartTypingEvent:
        return ChannelStartTypingEvent(
            shard=shard,
            channel_id=d['id'],
            user_id=d['user'],
        )

    def parse_channel_stop_typing_event(
        self, shard: Shard, d: raw.ClientChannelStopTypingEvent
    ) -> ChannelStopTypingEvent:
        return ChannelStopTypingEvent(
            shard=shard,
            channel_id=d['id'],
            user_id=d['user'],
        )

    def parse_channel_update_event(self, shard: Shard, d: raw.ClientChannelUpdateEvent) -> ChannelUpdateEvent:
        clear = d['clear']
        data = d['data']

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
                id=d['id'],
                name=data.get('name', core.UNDEFINED),
                owner_id=owner if owner else core.UNDEFINED,
                description=(None if 'Description' in clear else data.get('description', core.UNDEFINED)),
                internal_icon=(None if 'Icon' in clear else self.parse_asset(icon) if icon else core.UNDEFINED),
                nsfw=data.get('nsfw', core.UNDEFINED),
                active=data.get('active', core.UNDEFINED),
                permissions=(Permissions(permissions) if permissions is not None else core.UNDEFINED),
                role_permissions=(
                    {k: self.parse_permission_override_field(v) for k, v in role_permissions.items()}
                    if role_permissions is not None
                    else core.UNDEFINED
                ),
                default_permissions=(
                    self.parse_permission_override_field(default_permissions)
                    if default_permissions is not None
                    else core.UNDEFINED
                ),
                last_message_id=last_message_id or core.UNDEFINED,
            ),
            before=None,
            after=None,
        )

    def parse_channel(self, d: raw.Channel) -> Channel:
        return self._channel_parsers[d['channel_type']](d)

    def parse_detached_emoji(self, d: raw.DetachedEmoji) -> DetachedEmoji:
        return DetachedEmoji(
            state=self.state,
            id=d['_id'],
            creator_id=d['creator_id'],
            name=d['name'],
            animated=d.get('animated', False),
            nsfw=d.get('nsfw', False),
        )

    def parse_disabled_response_login(self, d: raw.a.DisabledResponseLogin) -> AccountDisabled:
        return AccountDisabled(user_id=core.resolve_id(d['user_id']))

    def parse_direct_message_channel(self, d: raw.DirectMessageChannel) -> DMChannel:
        recipient_ids = d['recipients']

        return DMChannel(
            state=self.state,
            id=d['_id'],
            active=d['active'],
            recipient_ids=(
                recipient_ids[0],
                recipient_ids[1],
            ),
            last_message_id=d.get('last_message_id'),
        )

    # Discovery
    def parse_discovery_bot(self, d: raw.DiscoveryBot) -> discovery.DiscoveryBot:
        avatar = d.get('avatar')

        return discovery.DiscoveryBot(
            state=self.state,
            id=d['_id'],
            name=d['username'],
            internal_avatar=self.parse_asset(avatar) if avatar else None,
            internal_profile=self.parse_user_profile(d['profile']),
            tags=d['tags'],
            server_count=d['servers'],
            usage=discovery.BotUsage(d['usage']),
        )

    def parse_discovery_bot_search_result(self, d: raw.DiscoveryBotSearchResult) -> discovery.BotSearchResult:
        return discovery.BotSearchResult(
            query=d['query'],
            count=d['count'],
            bots=[self.parse_discovery_bot(s) for s in d['bots']],
            related_tags=d['relatedTags'],
        )

    def parse_discovery_bots_page(self, d: raw.DiscoveryBotsPage) -> discovery.DiscoveryBotsPage:
        return discovery.DiscoveryBotsPage(
            bots=[self.parse_discovery_bot(b) for b in d['bots']],
            popular_tags=d['popularTags'],
        )

    def parse_discovery_server(self, d: raw.DiscoveryServer) -> discovery.DiscoveryServer:
        icon = d.get('icon')
        banner = d.get('banner')

        return discovery.DiscoveryServer(
            state=self.state,
            id=d['_id'],
            name=d['name'],
            description=d.get('description'),
            internal_icon=self.parse_asset(icon) if icon else None,
            internal_banner=self.parse_asset(banner) if banner else None,
            flags=ServerFlags(d.get('flags') or 0),
            tags=d['tags'],
            member_count=d['members'],
            activity=discovery.ServerActivity(d['activity']),
        )

    def parse_discovery_servers_page(self, d: raw.DiscoveryServersPage) -> discovery.DiscoveryServersPage:
        return discovery.DiscoveryServersPage(
            servers=[self.parse_discovery_server(s) for s in d['servers']],
            popular_tags=d['popularTags'],
        )

    def parse_discovery_server_search_result(self, d: raw.DiscoveryServerSearchResult) -> discovery.ServerSearchResult:
        return discovery.ServerSearchResult(
            query=d['query'],
            count=d['count'],
            servers=[self.parse_discovery_server(s) for s in d['servers']],
            related_tags=d['relatedTags'],
        )

    def parse_discovery_theme(self, d: raw.DiscoveryTheme) -> discovery.DiscoveryTheme:
        return discovery.DiscoveryTheme(
            state=self.state,
            name=d['name'],
            description=d['description'],
            creator=d['creator'],
            slug=d['slug'],
            tags=d['tags'],
            variables=d['variables'],
            version=d['version'],
            css=d.get('css'),
        )

    def parse_discovery_theme_search_result(self, d: raw.DiscoveryThemeSearchResult) -> discovery.ThemeSearchResult:
        return discovery.ThemeSearchResult(
            query=d['query'],
            count=d['count'],
            themes=[self.parse_discovery_theme(s) for s in d['themes']],
            related_tags=d['relatedTags'],
        )

    def parse_discovery_themes_page(self, d: raw.DiscoveryThemesPage) -> discovery.DiscoveryThemesPage:
        return discovery.DiscoveryThemesPage(
            themes=[self.parse_discovery_theme(b) for b in d['themes']],
            popular_tags=d['popularTags'],
        )

    def parse_display_user(self, d: raw.BannedUser) -> DisplayUser:
        avatar = d.get('avatar')

        return DisplayUser(
            state=self.state,
            id=d['_id'],
            name=d['username'],
            discriminator=d['discriminator'],
            internal_avatar=self.parse_asset(avatar) if avatar else None,
        )

    def parse_embed(self, d: raw.Embed) -> Embed:
        return self._embed_parsers[d['type']](d)

    def parse_embed_special(self, d: raw.Special) -> EmbedSpecial:
        return self._embed_special_parsers[d['type']](d)

    def parse_emoji(self, d: raw.Emoji) -> Emoji:
        return self._emoji_parsers[d['parent']['type']](d)

    def parse_emoji_create_event(self, shard: Shard, d: raw.ClientEmojiCreateEvent) -> ServerEmojiCreateEvent:
        return ServerEmojiCreateEvent(
            shard=shard,
            emoji=self.parse_server_emoji(d),
        )

    def parse_emoji_delete_event(self, shard: Shard, d: raw.ClientEmojiDeleteEvent) -> ServerEmojiDeleteEvent:
        return ServerEmojiDeleteEvent(
            shard=shard,
            emoji=None,
            server_id=None,
            emoji_id=d['id'],
        )

    def parse_gif_embed_special(self, _: raw.GIFSpecial) -> GifEmbedSpecial:
        return _GIF_EMBED_SPECIAL

    def parse_group_channel(
        self,
        d: raw.GroupChannel,
        recipients: (tuple[typing.Literal[True], list[str]] | tuple[typing.Literal[False], list[User]]),
    ) -> GroupChannel:
        icon = d.get('icon')
        permissions = d.get('permissions')

        return GroupChannel(
            state=self.state,
            id=d['_id'],
            name=d['name'],
            owner_id=d['owner'],
            description=d.get('description'),
            internal_recipients=recipients,
            internal_icon=self.parse_asset(icon) if icon else None,
            last_message_id=d.get('last_message_id'),
            permissions=None if permissions is None else Permissions(permissions),
            nsfw=d.get('nsfw', False),
        )

    def parse_group_invite(self, d: raw.GroupInvite) -> GroupInvite:
        return GroupInvite(
            state=self.state,
            code=d['_id'],
            creator_id=d['creator'],
            channel_id=d['channel'],
        )

    def parse_group_public_invite(self, d: raw.GroupInviteResponse) -> GroupPublicInvite:
        user_avatar = d.get('user_avatar')

        return GroupPublicInvite(
            state=self.state,
            code=d['code'],
            channel_id=d['channel_id'],
            channel_name=d['channel_name'],
            channel_description=d.get('channel_description'),
            user_name=d['user_name'],
            internal_user_avatar=self.parse_asset(user_avatar) if user_avatar else None,
        )

    def parse_image_embed(self, d: raw.Image) -> ImageEmbed:
        return ImageEmbed(
            url=d['url'],
            width=d['width'],
            height=d['height'],
            size=ImageSize(d['size']),
        )

    def parse_invite(self, d: raw.Invite) -> Invite:
        return self._invite_parsers[d['type']](d)

    def parse_lightspeed_embed_special(self, d: raw.LightspeedSpecial) -> LightspeedEmbedSpecial:
        return LightspeedEmbedSpecial(
            content_type=LightspeedContentType(d['content_type']),
            id=d['id'],
        )

    def parse_logout_event(self, shard: Shard, d: raw.ClientLogoutEvent) -> LogoutEvent:
        return LogoutEvent(shard=shard)

    def parse_member(
        self,
        d: raw.Member,
        *,
        user: User | None = None,
        users: dict[str, User] | None = None,
    ) -> Member:
        if user and users:
            raise ValueError('Cannot specify both user and users')

        id = d['_id']
        user_id = id['user']

        if user:
            assert user.id == user_id, 'IDs do not match'

        avatar = d.get('avatar')
        timeout = d.get('timeout')

        return Member(
            state=self.state,
            _user=user or (users or _EMPTY_DICT).get(user_id) or user_id,
            server_id=id['server'],
            joined_at=datetime.fromisoformat(d['joined_at']),
            nick=d.get('nickname'),
            internal_avatar=self.parse_asset(avatar) if avatar else None,
            roles=d.get('roles') or [],
            timed_out_until=datetime.fromisoformat(timeout) if timeout else None,
        )

    def parse_member_list(self, d: raw.AllMemberResponse) -> MemberList:
        return MemberList(
            members=[self.parse_member(m) for m in d['members']],
            users=[self.parse_user(u) for u in d['users']],
        )

    def parse_members_with_users(self, d: raw.AllMemberResponse) -> list[Member]:
        users = [self.parse_user(u) for u in d['users']]

        return [self.parse_member(e, user=users[i]) for i, e in enumerate(d['members'])]

    def parse_message(
        self,
        d: raw.Message,
        *,
        members: dict[str, Member] = {},
        users: dict[str, User] = {},
    ) -> Message:
        author_id = d['author']
        webhook = d.get('webhook')
        system = d.get('system')
        edited_at = d.get('edited')
        interactions = d.get('interactions')
        masquerade = d.get('masquerade')

        member = d.get('member')
        user = d.get('user')

        if member:
            if user:
                author = self.parse_member(member, user=self.parse_user(user))
            else:
                author = self.parse_member(member)
        elif user:
            author = self.parse_user(user)
        else:
            author = members.get(author_id) or users.get(author_id) or author_id

        return Message(
            state=self.state,
            id=d['_id'],
            nonce=d.get('nonce'),
            channel_id=d['channel'],
            internal_author=author,
            webhook=self.parse_message_webhook(webhook) if webhook else None,
            content=d.get('content', ''),
            system_event=self.parse_message_system_event(system) if system else None,
            internal_attachments=[self.parse_asset(a) for a in d.get('attachments', [])],
            edited_at=datetime.fromisoformat(edited_at) if edited_at else None,
            internal_embeds=[self.parse_embed(e) for e in d.get('embeds', [])],
            mention_ids=d.get('mentions', []),
            replies=d.get('replies', []),
            reactions={k: tuple(v) for k, v in (d.get('reactions') or {}).items()},
            interactions=(self.parse_message_interactions(interactions) if interactions else None),
            masquerade=(self.parse_message_masquerade(masquerade) if masquerade else None),
            pinned=d.get('pinned', False),
            flags=MessageFlags(d.get('flags', 0)),
        )

    def parse_message_append_event(self, shard: Shard, d: raw.ClientMessageAppendEvent) -> MessageAppendEvent:
        data = d['append']
        embeds = data.get('embeds')

        return MessageAppendEvent(
            shard=shard,
            data=MessageAppendData(
                state=self.state,
                id=d['id'],
                channel_id=d['channel'],
                internal_embeds=([self.parse_embed(e) for e in embeds] if embeds is not None else core.UNDEFINED),
            ),
        )

    def parse_message_channel_description_changed_system_event(
        self, d: raw.ChannelDescriptionChangedSystemMessage
    ) -> ChannelDescriptionChangedSystemEvent:
        return ChannelDescriptionChangedSystemEvent(by_id=d['by'])

    def parse_message_channel_icon_changed_system_event(
        self, d: raw.ChannelIconChangedSystemMessage
    ) -> ChannelIconChangedSystemEvent:
        return ChannelIconChangedSystemEvent(by_id=d['by'])

    def parse_message_channel_renamed_system_event(
        self, d: raw.ChannelRenamedSystemMessage
    ) -> ChannelRenamedSystemEvent:
        return ChannelRenamedSystemEvent(
            by_id=d['by'],
        )

    def parse_message_channel_ownership_changed_system_event(
        self, d: raw.ChannelOwnershipChangedSystemMessage
    ) -> ChannelOwnershipChangedSystemEvent:
        return ChannelOwnershipChangedSystemEvent(
            from_id=d['from'],
            to_id=d['to'],
        )

    def parse_message_delete_event(self, shard: Shard, d: raw.ClientMessageDeleteEvent) -> MessageDeleteEvent:
        return MessageDeleteEvent(
            shard=shard,
            channel_id=d['channel'],
            message_id=d['id'],
        )

    def parse_message_event(self, shard: Shard, d: raw.ClientMessageEvent) -> MessageCreateEvent:
        return MessageCreateEvent(shard=shard, message=self.parse_message(d))

    def parse_message_interactions(self, d: raw.Interactions) -> Interactions:
        return Interactions(
            reactions=d.get('reactions', []),
            restrict_reactions=d.get('restrict_reactions', False),
        )

    def parse_message_masquerade(self, d: raw.Masquerade) -> Masquerade:
        return Masquerade(name=d.get('name'), avatar=d.get('avatar'), colour=d.get('colour'))

    def parse_message_message_pinned_system_event(self, d: raw.MessagePinnedSystemMessage) -> MessagePinnedSystemEvent:
        return MessagePinnedSystemEvent(
            message_id=d['id'],
            by_id=d['by'],
        )

    def parse_message_message_unpinned_system_event(
        self, d: raw.MessageUnpinnedSystemMessage
    ) -> MessageUnpinnedSystemEvent:
        return MessageUnpinnedSystemEvent(
            message_id=d['id'],
            by_id=d['by'],
        )

    def parse_message_react_event(self, shard: Shard, d: raw.ClientMessageReactEvent) -> MessageReactEvent:
        return MessageReactEvent(
            shard=shard,
            channel_id=d['channel_id'],
            message_id=d['id'],
            user_id=d['user_id'],
            emoji=d['emoji_id'],
        )

    def parse_message_remove_reaction_event(
        self, shard: Shard, d: raw.ClientMessageRemoveReactionEvent
    ) -> MessageClearReactionEvent:
        return MessageClearReactionEvent(
            shard=shard,
            channel_id=d['channel_id'],
            message_id=d['id'],
            emoji=d['emoji_id'],
        )

    def parse_message_system_event(self, d: raw.SystemMessage) -> SystemEvent:
        return self._message_system_event_parsers[d['type']](d)

    def parse_message_text_system_event(self, d: raw.TextSystemMessage) -> TextSystemEvent:
        return TextSystemEvent(content=d['content'])

    def parse_message_unreact_event(self, shard: Shard, d: raw.ClientMessageUnreactEvent) -> MessageUnreactEvent:
        return MessageUnreactEvent(
            shard=shard,
            channel_id=d['channel_id'],
            message_id=d['id'],
            user_id=d['user_id'],
            emoji=d['emoji_id'],
        )

    def parse_message_update_event(self, shard: Shard, d: raw.ClientMessageUpdateEvent) -> MessageUpdateEvent:
        data = d['data']
        clear = d['clear']

        content = data.get('content')
        edited_at = data.get('edited')
        embeds = data.get('embeds')
        reactions = data.get('reactions')

        return MessageUpdateEvent(
            shard=shard,
            message=PartialMessage(
                state=self.state,
                id=d['id'],
                channel_id=d['channel'],
                content=content if content is not None else core.UNDEFINED,
                edited_at=datetime.fromisoformat(edited_at) if edited_at else core.UNDEFINED,
                internal_embeds=[self.parse_embed(e) for e in embeds] if embeds is not None else core.UNDEFINED,
                pinned=False if 'Pinned' in clear else data.get('pinned', core.UNDEFINED),
                reactions={k: tuple(v) for k, v in reactions.items()} if reactions is not None else core.UNDEFINED,
            ),
            before=None,
            after=None,
        )

    def parse_message_user_added_system_event(self, d: raw.UserAddedSystemMessage) -> UserAddedSystemEvent:
        return UserAddedSystemEvent(user_id=d['id'], by_id=d['by'])

    def parse_message_user_banned_system_event(self, d: raw.UserBannedSystemMessage) -> UserBannedSystemEvent:
        return UserBannedSystemEvent(user_id=d['id'])

    def parse_message_user_joined_system_event(self, d: raw.UserJoinedSystemMessage) -> UserJoinedSystemEvent:
        return UserJoinedSystemEvent(user_id=d['id'])

    def parse_message_user_kicked_system_event(self, d: raw.UserKickedSystemMessage) -> UserKickedSystemEvent:
        return UserKickedSystemEvent(user_id=d['id'])

    def parse_message_user_left_system_event(self, d: raw.UserLeftSystemMessage) -> UserLeftSystemEvent:
        return UserLeftSystemEvent(user_id=d['id'])

    def parse_message_user_remove_system_event(self, d: raw.UserRemoveSystemMessage) -> UserRemovedSystemEvent:
        return UserRemovedSystemEvent(
            user_id=d['id'],
            by_id=d['by'],
        )

    def parse_message_webhook(self, d: raw.MessageWebhook) -> MessageWebhook:
        return MessageWebhook(
            name=d['name'],
            avatar=d.get('avatar'),
        )

    def parse_messages(self, d: raw.BulkMessageResponse) -> list[Message]:
        if isinstance(d, list):
            return [self.parse_message(e) for e in d]
        elif isinstance(d, dict):
            users = [self.parse_user(e) for e in d['users']]
            users_mapping = {u.id: u for u in users}

            members = [self.parse_member(e, users=users_mapping) for e in d.get('members') or {}]
            members_mapping = {m.id: m for m in members}

            return [self.parse_message(e, members=members_mapping, users=users_mapping) for e in d['messages']]
        raise RuntimeError('Unreachable')

    def parse_mfa_response_login(self, d: raw.a.MFAResponseLogin, friendly_name: str | None) -> MFARequired:
        return MFARequired(
            ticket=d['ticket'],
            allowed_methods=[MFAMethod(m) for m in d['allowed_methods']],
            state=self.state,
            internal_friendly_name=friendly_name,
        )

    def parse_mfa_ticket(self, d: raw.a.MFATicket) -> MFATicket:
        return MFATicket(
            id=d['_id'],
            account_id=d['account_id'],
            token=d['token'],
            validated=d['validated'],
            authorised=d['authorised'],
            last_totp_code=d.get('last_totp_code'),
        )

    def parse_multi_factor_status(self, d: raw.a.MultiFactorStatus) -> MFAStatus:
        return MFAStatus(
            totp_mfa=d['totp_mfa'],
            recovery_active=d['recovery_active'],
        )

    def parse_mutuals(self, d: raw.MutualResponse) -> Mutuals:
        return Mutuals(
            user_ids=d['users'],
            server_ids=d['servers'],
        )

    def parse_none_embed(self, _: raw.NoneEmbed) -> NoneEmbed:
        return _NONE_EMBED

    def parse_none_embed_special(self, _: raw.NoneSpecial) -> NoneEmbedSpecial:
        return _NONE_EMBED_SPECIAL

    def parse_partial_account(self, d: raw.a.AccountInfo) -> PartialAccount:
        return PartialAccount(id=d['_id'], email=d['email'])

    def parse_partial_session(self, d: raw.a.SessionInfo) -> PartialSession:
        return PartialSession(state=self.state, id=d['_id'], name=d['name'])

    def parse_partial_user_profile(self, d: raw.UserProfile, clear: list[raw.FieldsUser]) -> PartialUserProfile:
        background = d.get('background')

        return PartialUserProfile(
            state=self.state,
            content=(None if 'ProfileContent' in clear else d.get('content') or core.UNDEFINED),
            internal_background=(
                None if 'ProfileBackground' in clear else self.parse_asset(background) if background else core.UNDEFINED
            ),
        )

    def parse_permission_override(self, d: raw.Override) -> PermissionOverride:
        return PermissionOverride(
            allow=Permissions(d['allow']),
            deny=Permissions(d['deny']),
        )

    def parse_permission_override_field(self, d: raw.OverrideField) -> PermissionOverride:
        return PermissionOverride(
            allow=Permissions(d['a']),
            deny=Permissions(d['d']),
        )

    def parse_public_bot(self, d: raw.PublicBot) -> PublicBot:
        return PublicBot(
            state=self.state,
            id=d['_id'],
            username=d['username'],
            internal_avatar_id=d.get('avatar'),
            description=d.get('description', ''),
        )

    def parse_public_invite(self, d: raw.InviteResponse) -> BaseInvite:
        return self._public_invite_parsers.get(d['type'], self.parse_unknown_public_invite)(d)

    def parse_read_state(self, d: raw.ChannelUnread) -> ReadState:
        id = d['_id']
        last_id = d.get('last_id')

        return ReadState(
            state=self.state,
            channel_id=id['channel'],
            user_id=id['user'],
            last_message_id=last_id if last_id else None,
            mentioned_in=d.get('mentions') or [],
        )

    def parse_ready_event(self, shard: Shard, d: raw.ClientReadyEvent) -> ReadyEvent:
        users = [self.parse_user(u) for u in d.get('users', [])]
        servers = [self.parse_server(s, (True, s['channels'])) for s in d.get('servers', [])]
        channels = [self.parse_channel(c) for c in d.get('channels', [])]
        members = [self.parse_member(m) for m in d.get('members', [])]
        emojis = [self.parse_server_emoji(e) for e in d.get('emojis', [])]
        user_settings = self.parse_user_settings(d.get('user_settings', {}), False)
        read_states = [self.parse_read_state(rs) for rs in d.get('channel_unreads', [])]

        me = users[-1]
        if me.__class__ is not SelfUser or not isinstance(me, SelfUser):
            for user in users:
                if me.__class__ is not SelfUser or isinstance(me, SelfUser):
                    me = user

        if me.__class__ is not SelfUser or not isinstance(me, SelfUser):
            raise TypeError('Unable to find self user')

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

    def parse_relationship(self, d: raw.Relationship) -> Relationship:
        return Relationship(
            id=d['_id'],
            status=RelationshipStatus(d['status']),
        )

    def parse_response_login(self, d: raw.a.ResponseLogin, friendly_name: str | None) -> LoginResult:
        if d['result'] == 'Success':
            return self.parse_session(d)
        elif d['result'] == 'MFA':
            return self.parse_mfa_response_login(d, friendly_name)
        elif d['result'] == 'Disabled':
            return self.parse_disabled_response_login(d)
        else:
            raise NotImplementedError(d)

    def parse_response_webhook(self, d: raw.ResponseWebhook) -> Webhook:
        avatar = d.get('avatar')
        webhook_id = d['id']

        return Webhook(
            state=self.state,
            id=webhook_id,
            name=d['name'],
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
                    user_id=webhook_id,
                    server_id=None,
                    object_id=None,
                )
                if avatar
                else None
            ),
            channel_id=d['channel_id'],
            permissions=Permissions(d['permissions']),
            token=None,
        )

    def parse_role(self, d: raw.Role, role_id: str, server_id: str) -> Role:
        return Role(
            state=self.state,
            id=role_id,
            name=d['name'],
            permissions=self.parse_permission_override_field(d['permissions']),
            colour=d.get('colour'),
            hoist=d.get('hoist', False),
            rank=d['rank'],
            server_id=server_id,
        )

    def parse_saved_messages_channel(self, d: raw.SavedMessagesChannel) -> SavedMessagesChannel:
        return SavedMessagesChannel(
            state=self.state,
            id=d['_id'],
            user_id=d['user'],
        )

    def parse_self_user(self, d: raw.User) -> SelfUser:
        avatar = d.get('avatar')
        status = d.get('status')
        # profile = d.get("profile")
        privileged = d.get('privileged')
        bot = d.get('bot')

        relations = [self.parse_relationship(r) for r in d.get('relations', [])]

        return SelfUser(
            state=self.state,
            id=d['_id'],
            name=d['username'],
            discriminator=d['discriminator'],
            display_name=d.get('display_name'),
            internal_avatar=self.parse_asset(avatar) if avatar else None,
            relations={relation.id: relation for relation in relations},
            badges=UserBadges(d.get('badges', 0)),
            status=self.parse_user_status(status) if status else None,
            # internal_profile=self.parse_user_profile(profile) if profile else None,
            flags=UserFlags(d.get('flags', 0)),
            privileged=privileged or False,
            bot=self.parse_bot_user_info(bot) if bot else None,
            relationship=RelationshipStatus(d['relationship']),
            online=d['online'],
        )

    def _parse_server(
        self,
        d: raw.Server,
        channels: (tuple[typing.Literal[True], list[str]] | tuple[typing.Literal[False], list[ServerChannel]]),
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
            flags=ServerFlags(d.get('flags', 0)),
            nsfw=d.get('nsfw', False),
            analytics=d.get('analytics', False),
            discoverable=d.get('discoverable', False),
        )

    def parse_server(
        self,
        d: raw.Server,
        channels: (tuple[typing.Literal[True], list[str]] | tuple[typing.Literal[False], list[raw.Channel]]),
    ) -> Server:
        internal_channels: (
            tuple[typing.Literal[True], list[str]] | tuple[typing.Literal[False], list[ServerChannel]]
        ) = (
            (True, [str(i) for i in channels[1]])
            if channels[0]
            else (False, [self.parse_channel(c) for c in channels[1]])  # type: ignore
        )
        return self._parse_server(d, internal_channels)

    def parse_server_create_event(self, shard: Shard, d: raw.ClientServerCreateEvent) -> ServerCreateEvent:
        return ServerCreateEvent(
            shard=shard,
            server=self.parse_server(d['server'], (False, d['channels'])),
            emojis=[self.parse_server_emoji(e) for e in d['emojis']],
        )

    def parse_server_delete_event(self, shard: Shard, d: raw.ClientServerDeleteEvent) -> ServerDeleteEvent:
        return ServerDeleteEvent(
            shard=shard,
            server_id=d['id'],
            server=None,
        )

    def parse_server_emoji(self, d: raw.ServerEmoji) -> ServerEmoji:
        return ServerEmoji(
            state=self.state,
            id=d['_id'],
            server_id=d['parent']['id'],
            creator_id=d['creator_id'],
            name=d['name'],
            animated=d.get('animated', False),
            nsfw=d.get('nsfw', False),
        )

    def parse_server_invite(self, d: raw.ServerInvite) -> ServerInvite:
        return ServerInvite(
            state=self.state,
            code=d['_id'],
            creator_id=d['creator'],
            server_id=d['server'],
            channel_id=d['channel'],
        )

    def parse_server_member_join_event(
        self, shard: Shard, d: raw.ClientServerMemberJoinEvent, joined_at: datetime
    ) -> ServerMemberJoinEvent:
        return ServerMemberJoinEvent(
            shard=shard,
            member=Member(
                state=self.state,
                server_id=d['id'],
                _user=d['user'],
                joined_at=joined_at,
                nick=None,
                internal_avatar=None,
                roles=[],
                timed_out_until=None,
            ),
        )

    def parse_server_member_leave_event(
        self, shard: Shard, d: raw.ClientServerMemberLeaveEvent
    ) -> ServerMemberRemoveEvent:
        return ServerMemberRemoveEvent(
            shard=shard,
            server_id=d['id'],
            user_id=d['user'],
            member=None,
            reason=MemberRemovalIntention(d['reason']),
        )

    def parse_server_member_update_event(
        self, shard: Shard, d: raw.ClientServerMemberUpdateEvent
    ) -> ServerMemberUpdateEvent:
        id = d['id']
        data = d['data']
        clear = d['clear']

        avatar = data.get('avatar')
        roles = data.get('roles')
        timeout = data.get('timeout')

        return ServerMemberUpdateEvent(
            shard=shard,
            member=PartialMember(
                state=self.state,
                server_id=id['server'],
                _user=id['user'],
                nick=(None if 'Nickname' in clear else data.get('nickname', core.UNDEFINED)),
                internal_avatar=(None if 'Avatar' in clear else self.parse_asset(avatar) if avatar else core.UNDEFINED),
                roles=([] if 'Roles' in clear else (roles if roles is not None else core.UNDEFINED)),
                timed_out_until=(
                    None if 'Timeout' in clear else datetime.fromisoformat(timeout) if timeout else core.UNDEFINED
                ),
            ),
            before=None,  # filled on dispatch
            after=None,  # filled on dispatch
        )

    def parse_server_public_invite(self, d: raw.ServerInviteResponse) -> ServerPublicInvite:
        server_icon = d.get('server_icon')
        server_banner = d.get('server_banner')
        user_avatar = d.get('user_avatar')

        return ServerPublicInvite(
            state=self.state,
            code=d['code'],
            server_id=d['server_id'],
            server_name=d['server_name'],
            internal_server_icon=self.parse_asset(server_icon) if server_icon else None,
            internal_server_banner=(self.parse_asset(server_banner) if server_banner else None),
            flags=ServerFlags(d.get('server_flags', 0)),
            channel_id=d['channel_id'],
            channel_name=d['channel_name'],
            channel_description=d.get('channel_description'),
            user_name=d['user_name'],
            internal_user_avatar=self.parse_asset(user_avatar) if user_avatar else None,
            members_count=d['member_count'],
        )

    def parse_server_role_delete_event(self, shard: Shard, d: raw.ClientServerRoleDeleteEvent) -> ServerRoleDeleteEvent:
        return ServerRoleDeleteEvent(
            shard=shard,
            server_id=d['id'],
            role_id=d['role_id'],
            server=None,
            role=None,
        )

    def parse_server_role_update_event(
        self, shard: Shard, d: raw.ClientServerRoleUpdateEvent
    ) -> RawServerRoleUpdateEvent:
        data = d['data']
        clear = d['clear']

        permissions = data.get('permissions')

        return RawServerRoleUpdateEvent(
            shard=shard,
            role=PartialRole(
                state=self.state,
                id=d['role_id'],
                server_id=d['id'],
                name=data.get('name') or core.UNDEFINED,
                permissions=(self.parse_permission_override_field(permissions) if permissions else core.UNDEFINED),
                colour=(None if 'Colour' in clear else data.get('colour', core.UNDEFINED)),
                hoist=data.get('hoist', core.UNDEFINED),
                rank=data.get('rank', core.UNDEFINED),
            ),
            old_role=None,
            new_role=None,
            server=None,
        )

    def parse_server_update_event(self, shard: Shard, d: raw.ClientServerUpdateEvent) -> ServerUpdateEvent:
        data = d['data']
        clear = d['clear']

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
                id=d['id'],
                owner_id=d.get('owner', core.UNDEFINED),
                name=data.get('name', core.UNDEFINED),
                description=(
                    None if 'Description' in clear else description if description is not None else core.UNDEFINED
                ),
                channel_ids=data.get('channels', core.UNDEFINED),
                categories=(
                    []
                    if 'Categories' in clear
                    else ([self.parse_category(c) for c in categories] if categories is not None else core.UNDEFINED)
                ),
                system_messages=(
                    None
                    if 'SystemMessages' in clear
                    else (
                        self.parse_system_message_channels(system_messages)
                        if system_messages is not None
                        else core.UNDEFINED
                    )
                ),
                default_permissions=(
                    Permissions(default_permissions) if default_permissions is not None else core.UNDEFINED
                ),
                internal_icon=(None if 'Icon' in clear else self.parse_asset(icon) if icon else core.UNDEFINED),
                internal_banner=(None if 'Banner' in clear else self.parse_asset(banner) if banner else core.UNDEFINED),
                flags=(ServerFlags(flags) if flags is not None else core.UNDEFINED),
                discoverable=d.get('discoverable', core.UNDEFINED),
                analytics=d.get('analytics', core.UNDEFINED),
            ),
            before=None,  # filled on dispatch
            after=None,  # filled on dispatch
        )

    def parse_session(self, d: raw.a.Session) -> Session:
        subscription = d.get('subscription')

        return Session(
            state=self.state,
            id=d['_id'],
            name=d['name'],
            user_id=d['user_id'],
            token=d['token'],
            subscription=(self.parse_webpush_subscription(subscription) if subscription else None),
        )

    def parse_soundcloud_embed_special(self, _: raw.SoundcloudSpecial) -> SoundcloudEmbedSpecial:
        return _SOUNDCLOUD_EMBED_SPECIAL

    def parse_spotify_embed_special(self, d: raw.SpotifySpecial) -> SpotifyEmbedSpecial:
        return SpotifyEmbedSpecial(
            content_type=d['content_type'],
            id=d['id'],
        )

    def parse_streamable_embed_special(self, d: raw.StreamableSpecial) -> StreamableEmbedSpecial:
        return StreamableEmbedSpecial(id=d['id'])

    def parse_system_message_channels(
        self,
        d: raw.SystemMessageChannels,
    ) -> SystemMessageChannels:
        return SystemMessageChannels(
            user_joined=d.get('user_joined'),
            user_left=d.get('user_left'),
            user_kicked=d.get('user_kicked'),
            user_banned=d.get('user_banned'),
        )

    def parse_text_channel(self, d: raw.TextChannel) -> ServerTextChannel:
        icon = d.get('icon')
        default_permissions = d.get('default_permissions')
        role_permissions = d.get('role_permissions', {})

        try:
            last_message_id = d['last_message_id']  # type: ignore # I really hope that Eric will allow that
        except KeyError:
            last_message_id = None

        return ServerTextChannel(
            state=self.state,
            id=d['_id'],
            server_id=d['server'],
            name=d['name'],
            description=d.get('description'),
            internal_icon=self.parse_asset(icon) if icon else None,
            last_message_id=last_message_id,
            default_permissions=(
                None if default_permissions is None else self.parse_permission_override_field(default_permissions)
            ),
            role_permissions={k: self.parse_permission_override_field(v) for k, v in role_permissions.items()},
            nsfw=d.get('nsfw', False),
        )

    def parse_text_embed(self, d: raw.TextEmbed) -> StatelessTextEmbed:
        media = d.get('media')

        return StatelessTextEmbed(
            icon_url=d.get('icon_url'),
            url=d.get('url'),
            title=d.get('title'),
            description=d.get('description'),
            internal_media=self.parse_asset(media) if media else None,
            colour=d.get('colour'),
        )

    def parse_twitch_embed_special(self, d: raw.TwitchSpecial) -> TwitchEmbedSpecial:
        return TwitchEmbedSpecial(
            content_type=TwitchContentType(d['content_type']),
            id=d['id'],
        )

    def parse_unknown_public_invite(self, d: dict[str, typing.Any]) -> UnknownPublicInvite:
        return UnknownPublicInvite(state=self.state, code=d['code'], payload=d)

    def parse_user(self, d: raw.User) -> User | SelfUser:
        if d['relationship'] == 'User':
            return self.parse_self_user(d)

        avatar = d.get('avatar')
        status = d.get('status')
        # profile = d.get('profile')
        bot = d.get('bot')

        return User(
            state=self.state,
            id=d['_id'],
            name=d['username'],
            discriminator=d['discriminator'],
            display_name=d.get('display_name'),
            internal_avatar=self.parse_asset(avatar) if avatar else None,
            badges=UserBadges(d.get('badges', 0)),
            status=self.parse_user_status(status) if status else None,
            # internal_profile=self.parse_user_profile(profile) if profile else None,
            flags=UserFlags(d.get('flags', 0)),
            privileged=d.get('privileged', False),
            bot=self.parse_bot_user_info(bot) if bot else None,
            relationship=RelationshipStatus(d['relationship']),
            online=d['online'],
        )

    def parse_user_platform_wipe_event(self, shard: Shard, d: raw.ClientUserPlatformWipeEvent) -> UserPlatformWipeEvent:
        return UserPlatformWipeEvent(
            shard=shard,
            user_id=d['user_id'],
            flags=UserFlags(d['flags']),
        )

    def parse_user_profile(self, d: raw.UserProfile) -> StatelessUserProfile:
        background = d.get('background')

        return StatelessUserProfile(
            content=d.get('content'),
            internal_background=self.parse_asset(background) if background else None,
        )

    def parse_user_relationship_event(
        self, shard: Shard, d: raw.ClientUserRelationshipEvent
    ) -> UserRelationshipUpdateEvent:
        return UserRelationshipUpdateEvent(
            shard=shard,
            current_user_id=d['id'],
            old_user=None,
            new_user=self.parse_user(d['user']),
            before=None,
        )

    def parse_user_settings(self, d: raw.UserSettings, partial: bool) -> UserSettings:
        return UserSettings(
            data={k: (s1, s2) for (k, (s1, s2)) in d.items()},
            state=self.state,
            mocked=False,
            partial=partial,
        )

    def parse_user_settings_update_event(
        self, shard: Shard, d: raw.ClientUserSettingsUpdateEvent
    ) -> UserSettingsUpdateEvent:
        partial = self.parse_user_settings(d['update'], True)

        before = shard.state.settings

        if not before.mocked:
            before = copy(before)
            after = copy(before)
            after._update(partial)
        else:
            after = before

        return UserSettingsUpdateEvent(
            shard=shard,
            current_user_id=d['id'],
            partial=partial,
            before=before,
            after=after,
        )

    def parse_user_status(self, d: raw.UserStatus) -> UserStatus:
        presence = d.get('presence')

        return UserStatus(
            text=d.get('text'),
            presence=Presence(presence) if presence else None,
        )

    def parse_user_status_edit(self, d: raw.UserStatus, clear: list[raw.FieldsUser]) -> UserStatusEdit:
        presence = d.get('presence')

        return UserStatusEdit(
            text=None if 'StatusText' in clear else d.get('text', core.UNDEFINED),
            presence=(None if 'StatusPresence' in clear else Presence(presence) if presence else core.UNDEFINED),
        )

    def parse_user_update_event(self, shard: Shard, d: raw.ClientUserUpdateEvent) -> UserUpdateEvent:
        user_id = d['id']
        data = d['data']
        clear = d['clear']

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
                name=data.get('username', core.UNDEFINED),
                discriminator=data.get('discriminator', core.UNDEFINED),
                display_name=(None if 'DisplayName' in clear else data.get('display_name') or core.UNDEFINED),
                internal_avatar=(None if 'Avatar' in clear else self.parse_asset(avatar) if avatar else core.UNDEFINED),
                badges=UserBadges(badges) if badges is not None else core.UNDEFINED,
                status=(self.parse_user_status_edit(status, clear) if status is not None else core.UNDEFINED),
                profile=(self.parse_partial_user_profile(profile, clear) if profile is not None else core.UNDEFINED),
                flags=UserFlags(flags) if flags is not None else core.UNDEFINED,
                online=d.get('online', core.UNDEFINED),
            ),
            before=None,  # filled on dispatch
            after=None,  # filled on dispatch
        )

    def parse_video_embed(self, d: raw.Video) -> VideoEmbed:
        return VideoEmbed(
            url=d['url'],
            width=d['width'],
            height=d['height'],
        )

    def parse_voice_channel(self, d: raw.VoiceChannel) -> VoiceChannel:
        icon = d.get('icon')
        default_permissions = d.get('default_permissions')
        role_permissions = d.get('role_permissions', {})

        return VoiceChannel(
            state=self.state,
            id=d['_id'],
            server_id=d['server'],
            name=d['name'],
            description=d.get('description'),
            internal_icon=self.parse_asset(icon) if icon else None,
            default_permissions=(
                None if default_permissions is None else self.parse_permission_override_field(default_permissions)
            ),
            role_permissions={k: self.parse_permission_override_field(v) for k, v in role_permissions.items()},
            nsfw=d.get('nsfw', False),
        )

    def parse_webhook(self, d: raw.Webhook) -> Webhook:
        avatar = d.get('avatar')

        return Webhook(
            state=self.state,
            id=d['id'],
            name=d['name'],
            internal_avatar=self.parse_asset(avatar) if avatar else None,
            channel_id=d['channel_id'],
            permissions=Permissions(d['permissions']),
            token=d.get('token'),
        )

    def parse_webhook_create_event(self, shard: Shard, d: raw.ClientWebhookCreateEvent) -> WebhookCreateEvent:
        return WebhookCreateEvent(
            shard=shard,
            webhook=self.parse_webhook(d),
        )

    def parse_webhook_update_event(self, shard: Shard, d: raw.ClientWebhookUpdateEvent) -> WebhookUpdateEvent:
        data = d['data']
        remove = d['remove']

        avatar = data.get('avatar')
        permissions = data.get('permissions')

        return WebhookUpdateEvent(
            shard=shard,
            new_webhook=PartialWebhook(
                state=self.state,
                id=d['id'],
                name=data.get('name', core.UNDEFINED),
                internal_avatar=(
                    None if 'Avatar' in remove else self.parse_asset(avatar) if avatar else core.UNDEFINED
                ),
                permissions=(Permissions(permissions) if permissions is not None else core.UNDEFINED),
            ),
        )

    def parse_webhook_delete_event(self, shard: Shard, d: raw.ClientWebhookDeleteEvent) -> WebhookDeleteEvent:
        return WebhookDeleteEvent(
            shard=shard,
            webhook=None,
            webhook_id=d['id'],
        )

    def parse_webpush_subscription(self, d: raw.a.WebPushSubscription) -> WebPushSubscription:
        return WebPushSubscription(
            endpoint=d['endpoint'],
            p256dh=d['p256dh'],
            auth=d['auth'],
        )

    def parse_website_embed(self, d: raw.WebsiteEmbed) -> WebsiteEmbed:
        special = d.get('special')
        image = d.get('image')
        video = d.get('video')

        return WebsiteEmbed(
            url=d.get('url'),
            original_url=d.get('original_url'),
            special=self.parse_embed_special(special) if special else None,
            title=d.get('title'),
            description=d.get('description'),
            image=self.parse_image_embed(image) if image else None,
            video=self.parse_video_embed(video) if video else None,
            site_name=d.get('site_name'),
            icon_url=d.get('icon_url'),
            colour=d.get('colour'),
        )

    def parse_youtube_embed_special(self, d: raw.YouTubeSpecial) -> YouTubeEmbedSpecial:
        return YouTubeEmbedSpecial(id=d['id'], timestamp=d.get('timestamp'))


__all__ = ('Parser',)
