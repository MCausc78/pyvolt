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
import sys
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
    TextChannel,
    VoiceChannel,
    ServerChannel,
    Channel,
    ChannelVoiceStateContainer,
)
from .core import UNDEFINED
from .embed import (
    EmbedSpecial,
    NoneEmbedSpecial,
    _NONE_EMBED_SPECIAL,
    GIFEmbedSpecial,
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
    ContentReportReason,
    UserReportReason,
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
    MessageDeleteBulkEvent,
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
    ReportCreateEvent,
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
    VoiceChannelJoinEvent,
    VoiceChannelLeaveEvent,
    VoiceChannelMoveEvent,
    UserVoiceStateUpdateEvent,
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
    ServerPublicInvite,
    GroupPublicInvite,
    UnknownPublicInvite,
    PublicInvite,
    GroupInvite,
    ServerInvite,
    Invite,
)
from .message import (
    MessageInteractions,
    MessageMasquerade,
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
    StatelessCallStartedSystemEvent,
    StatelessSystemEvent,
    Message,
)
from .permissions import PermissionOverride
from .read_state import ReadState
from .safety_reports import (
    CreatedReport,
    RejectedReport,
    ResolvedReport,
    Report,
    MessageReportedContent,
    ServerReportedContent,
    UserReportedContent,
    ReportedContent,
)

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
from .settings import UserSettings
from .user import (
    UserStatus,
    UserStatusEdit,
    StatelessUserProfile,
    PartialUserProfile,
    Relationship,
    Mutuals,
    PartialUser,
    DisplayUser,
    BotUserMetadata,
    User,
    OwnUser,
    UserVoiceState,
    PartialUserVoiceState,
)
from .utils import _UTC
from .webhook import PartialWebhook, Webhook

if typing.TYPE_CHECKING:
    from . import raw
    from .shard import Shard
    from .state import State

_new_category = Category.__new__
_new_permission_override = PermissionOverride.__new__

if sys.version_info >= (3, 11):
    _parse_dt = datetime.fromisoformat
else:
    # datetime.fromisoformat in Python 3.10 doesn't parse ISO8601 timestamps, so we have to do it ourselves
    # Example: 2025-02-03T19:39:34.263Z

    _strptime = datetime.strptime

    def _parse_dt(date_string: str, /) -> datetime:
        return _strptime(date_string, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=_UTC)


class Parser:
    """An factory that produces wrapper objects from raw data.

    Attributes
    ----------
    state: :class:`.State`
        The state the parser is attached to.
    """

    __slots__ = (
        'state',
        '_channel_parsers',
        '_embed_parsers',
        '_embed_special_parsers',
        '_emoji_parsers',
        '_invite_parsers',
        '_message_system_event_parsers',
        '_public_invite_parsers',
        '_report_parsers',
        '_reported_content_parsers',
    )

    def __init__(self, *, state: State) -> None:
        self.state: State = state
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
            'call_started': self.parse_message_call_started_system_event,
        }
        self._public_invite_parsers = {
            'Server': self.parse_server_public_invite,
            'Group': self.parse_group_public_invite,
        }
        self._report_parsers = {
            'Created': self.parse_created_report,
            'Rejected': self.parse_rejected_report,
            'Resolved': self.parse_resolved_report,
        }
        self._reported_content_parsers = {
            'Message': self.parse_message_reported_content,
            'Server': self.parse_server_reported_content,
            'User': self.parse_user_reported_content,
        }

    # basic start

    def parse_apple_music_embed_special(self, payload: raw.AppleMusicSpecial, /) -> AppleMusicEmbedSpecial:
        """Parses a Apple Music embed special content object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The Apple Music embed special content payload to parse.

        Returns
        -------
        :class:`AppleMusicEmbedSpecial`
            The parsed Apple Music embed special content object.
        """
        return AppleMusicEmbedSpecial(
            album_id=payload['album_id'],
            track_id=payload.get('track_id'),
        )

    def parse_asset_metadata(self, d: raw.Metadata, /) -> AssetMetadata:
        """Parses a asset metadata object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The asset metadata payload to parse.

        Returns
        -------
        :class:`AssetMetadata`
            The parsed asset metadata object.
        """
        return AssetMetadata(
            type=AssetMetadataType(d['type']),
            width=d.get('width'),
            height=d.get('height'),
        )

    def parse_asset(self, d: raw.File, /) -> StatelessAsset:
        """Parses a asset object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The asset payload to parse.

        Returns
        -------
        :class:`StatelessAsset`
            The parsed asset object.
        """
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
        """Parses a Auth event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`AuthifierEvent`
            The parsed authifier event object.
        """
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
        """Parses a Authenticated event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`AuthenticatedEvent`
            The parsed authenticated event object.
        """
        return AuthenticatedEvent(shard=shard)

    # basic end, internals start

    def _parse_group_channel(self, payload: raw.GroupChannel, /) -> GroupChannel:
        """Parses a group channel object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The group channel payload to parse.

        Returns
        -------
        :class:`GroupChannel`
            The parsed group channel object.
        """
        return self.parse_group_channel(
            payload,
            (True, payload['recipients']),
        )

    # internals end

    def parse_ban(self, payload: raw.ServerBan, users: dict[str, DisplayUser], /) -> Ban:
        """Parses a ban object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The ban payload to parse.
        users: Dict[:class:`str`, :class:`DisplayUser`]
            The users associated with the ban.

        Returns
        -------
        :class:`Ban`
            The parsed ban object.
        """
        id = payload['_id']
        user_id = id['user']

        return Ban(
            server_id=id['server'],
            user_id=user_id,
            reason=payload['reason'],
            user=users.get(user_id),
        )

    def parse_bandcamp_embed_special(self, payload: raw.BandcampSpecial, /) -> BandcampEmbedSpecial:
        """Parses a Bandcamp embed special content object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The Bandcamp embed special content payload to parse.

        Returns
        -------
        :class:`BandcampEmbedSpecial`
            The parsed Bandcamp embed special content object.
        """
        return BandcampEmbedSpecial(
            content_type=BandcampContentType(payload['content_type']),
            id=payload['id'],
        )

    def parse_bans(self, payload: raw.BanListResult, /) -> list[Ban]:
        """Parses a object with bans and associated banned users.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The list payload to parse.

        Returns
        -------
        List[:class:`Ban`]
            The parsed ban objects.
        """
        banned_users = {bu.id: bu for bu in map(self.parse_display_user, payload['users'])}
        return [self.parse_ban(e, banned_users) for e in payload['bans']]

    def _parse_bot(self, payload: raw.Bot, user: User, /) -> Bot:
        """Parses a bot object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The bot payload to parse.
        user: :class:`User`
            The user associated with the bot.

        Returns
        -------
        :class:`Bot`
            The parsed bot object.
        """
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
            raw_flags=payload.get('flags', 0),
            user=user,
        )

    def parse_bot(self, payload: raw.Bot, user: raw.User, /) -> Bot:
        """Parses a bot object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The bot payload to parse.
        user: raw.User
            The user associated with the bot.

        Returns
        -------
        :class:`Bot`
            The parsed bot object.
        """
        return self._parse_bot(payload, self.parse_user(user))

    def parse_bot_user_metadata(self, payload: raw.BotInformation, /) -> BotUserMetadata:
        """Parses a bot user metadata.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The bot payload to parse.
        user: raw.User
            The user associated with the bot.

        Returns
        -------
        :class:`BotUserMetadata`
            The parsed bot user metadata object.
        """
        return BotUserMetadata(owner_id=payload['owner'])

    def parse_bots(self, payload: raw.OwnedBotsResponse, /) -> list[Bot]:
        """Parses a object with bots and associated bot users.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The list payload to parse.

        Returns
        -------
        List[:class:`Bot`]
            The parsed bot objects.
        """
        bots = payload['bots']
        users = payload['users']

        if len(bots) != len(users):
            raise RuntimeError(f'Expected {len(bots)} users but got {len(users)}')
        return [self.parse_bot(e, users[i]) for i, e in enumerate(bots)]

    def parse_bulk_message_delete_event(
        self, shard: Shard, payload: raw.ClientBulkMessageDeleteEvent, /
    ) -> MessageDeleteBulkEvent:
        """Parses a BulkMessageDelete event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`MessageDeleteBulkEvent`
            The parsed message bulk delete event object.
        """
        return MessageDeleteBulkEvent(
            shard=shard,
            channel_id=payload['channel'],
            message_ids=payload['ids'],
            messages=[],
        )

    def parse_category(self, payload: raw.Category, /) -> Category:
        """Parses a category object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The category payload to parse.

        Returns
        -------
        :class:`Category`
            The parsed category object.
        """

        ret = _new_category(Category)
        ret.id = payload['id']
        ret.title = payload['title']
        ret.channels = payload['channels']
        return ret

    def parse_channel_ack_event(self, shard: Shard, payload: raw.ClientChannelAckEvent, /) -> MessageAckEvent:
        """Parses a ChannelAck event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`MessageAckEvent`
            The parsed message ack event object.
        """
        return MessageAckEvent(
            shard=shard,
            channel_id=payload['id'],
            message_id=payload['message_id'],
            user_id=payload['user'],
        )

    def parse_channel_create_event(self, shard: Shard, payload: raw.ClientChannelCreateEvent, /) -> ChannelCreateEvent:
        """Parses a ChannelCreate event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`ChannelCreateEvent`
            The parsed channel create event object.
        """
        channel = self.parse_channel(payload)
        if isinstance(
            channel,
            (SavedMessagesChannel, DMChannel, GroupChannel),
        ):
            return PrivateChannelCreateEvent(shard=shard, channel=channel)
        else:
            return ServerChannelCreateEvent(shard=shard, channel=channel)

    def parse_channel_delete_event(self, shard: Shard, payload: raw.ClientChannelDeleteEvent, /) -> ChannelDeleteEvent:
        """Parses a ChannelDelete event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`ChannelDeleteEvent`
            The parsed channel delete event object.
        """
        return ChannelDeleteEvent(
            shard=shard,
            channel_id=payload['id'],
            channel=None,
        )

    def parse_channel_group_join_event(
        self, shard: Shard, payload: raw.ClientChannelGroupJoinEvent, /
    ) -> GroupRecipientAddEvent:
        """Parses a ChannelGroupJoin event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`GroupRecipientAddEvent`
            The parsed group recipient add event object.
        """
        return GroupRecipientAddEvent(
            shard=shard,
            channel_id=payload['id'],
            user_id=payload['user'],
            group=None,
        )

    def parse_channel_group_leave_event(
        self, shard: Shard, payload: raw.ClientChannelGroupLeaveEvent, /
    ) -> GroupRecipientRemoveEvent:
        """Parses a ChannelGroupLeave event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`GroupRecipientRemoveEvent`
            The parsed group recipient remove event object.
        """
        return GroupRecipientRemoveEvent(
            shard=shard,
            channel_id=payload['id'],
            user_id=payload['user'],
            group=None,
        )

    def parse_channel_start_typing_event(
        self, shard: Shard, payload: raw.ClientChannelStartTypingEvent, /
    ) -> ChannelStartTypingEvent:
        """Parses a ChannelStartTyping event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`ChannelStartTypingEvent`
            The parsed channel typing start event object.
        """
        return ChannelStartTypingEvent(
            shard=shard,
            channel_id=payload['id'],
            user_id=payload['user'],
        )

    def parse_channel_stop_typing_event(
        self, shard: Shard, payload: raw.ClientChannelStopTypingEvent, /
    ) -> ChannelStopTypingEvent:
        """Parses a ChannelStopTyping event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`ChannelStopTypingEvent`
            The parsed channel typing stop event object.
        """

        return ChannelStopTypingEvent(
            shard=shard,
            channel_id=payload['id'],
            user_id=payload['user'],
        )

    def parse_channel_unread(self, payload: raw.ChannelUnread, /) -> ReadState:
        """Parses a channel unread object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The channel unread payload to parse.

        Returns
        -------
        :class:`ReadState`
            The parsed channel unread object.
        """
        id = payload['_id']

        return ReadState(
            state=self.state,
            channel_id=id['channel'],
            user_id=id['user'],
            last_acked_message_id=payload.get('last_id'),
            mentioned_in=payload.get('mentions', []),
        )

    def parse_channel_update_event(self, shard: Shard, payload: raw.ClientChannelUpdateEvent, /) -> ChannelUpdateEvent:
        """Parses a ChannelUpdate event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`ChannelUpdateEvent`
            The parsed channel update event object.
        """

        clear = payload['clear']
        data = payload['data']

        icon = data.get('icon')
        role_permissions = data.get('role_permissions')
        default_permissions = data.get('default_permissions')

        return ChannelUpdateEvent(
            shard=shard,
            channel=PartialChannel(
                state=self.state,
                id=payload['id'],
                name=data.get('name', UNDEFINED),
                owner_id=data.get('owner', UNDEFINED),
                description=None if 'Description' in clear else data.get('description', UNDEFINED),
                internal_icon=None if 'Icon' in clear else (UNDEFINED if icon is None else self.parse_asset(icon)),
                nsfw=data.get('nsfw', UNDEFINED),
                active=data.get('active', UNDEFINED),
                raw_permissions=data.get('permissions', UNDEFINED),
                role_permissions=(
                    UNDEFINED
                    if role_permissions is None
                    else {k: self.parse_permission_override_field(v) for k, v in role_permissions.items()}
                ),
                default_permissions=(
                    UNDEFINED
                    if default_permissions is None
                    else self.parse_permission_override_field(default_permissions)
                ),
                last_message_id=data.get('last_message_id', UNDEFINED),
            ),
            before=None,
            after=None,
        )

    def parse_channel_voice_state(self, payload: raw.ChannelVoiceState, /) -> ChannelVoiceStateContainer:
        """Parses a channel voice state container object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The channel voice state container payload to parse.

        Returns
        -------
        :class:`ChannelVoiceStateContainer`
            The parsed channel voice state container object.
        """
        return ChannelVoiceStateContainer(
            channel_id=payload['id'],
            participants={s.user_id: s for s in map(self.parse_user_voice_state, payload['participants'])},
        )

    @typing.overload
    def parse_channel(self, payload: raw.SavedMessagesChannel, /) -> SavedMessagesChannel: ...

    @typing.overload
    def parse_channel(self, payload: raw.DirectMessageChannel, /) -> DMChannel: ...

    @typing.overload
    def parse_channel(self, payload: raw.GroupChannel, /) -> GroupChannel: ...

    @typing.overload
    def parse_channel(self, payload: raw.TextChannel, /) -> TextChannel: ...

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

    def parse_created_report(self, payload: raw.CreatedReport, /) -> CreatedReport:
        """Parses a created report object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The created report payload to parse.

        Returns
        -------
        :class:`CreatedReport`
            The parsed created report object.
        """

        return CreatedReport(
            state=self.state,
            id=payload['_id'],
            author_id=payload['author_id'],
            content=self.parse_reported_content(payload['content']),
            additional_context=payload['additional_context'],
            notes=payload.get('notes', ''),
        )

    def parse_detached_emoji(self, payload: raw.DetachedEmoji, /) -> DetachedEmoji:
        """Parses a detached emoji object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The detached emoji payload to parse.

        Returns
        -------
        :class:`DetachedEmoji`
            The parsed detached emoji object.
        """

        return DetachedEmoji(
            state=self.state,
            id=payload['_id'],
            creator_id=payload['creator_id'],
            name=payload['name'],
            animated=payload.get('animated', False),
            nsfw=payload.get('nsfw', False),
        )

    def parse_disabled_response_login(self, payload: raw.a.DisabledResponseLogin, /) -> AccountDisabled:
        """Parses a "Account Disabled" login response object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The login response payload to parse.

        Returns
        -------
        :class:`AccountDisabled`
            The parsed "Account Disabled" login response object.
        """
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
    def parse_discoverable_bot(self, payload: raw.DiscoverableBot, /) -> discovery.DiscoverableBot:
        """Parses a discoverable bot object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The discoverable bot payload to parse.

        Returns
        -------
        :class:`~discovery.DiscoverableBot`
            The parsed bot object.
        """
        avatar = payload.get('avatar')

        return discovery.DiscoverableBot(
            state=self.state,
            id=payload['_id'],
            name=payload['username'],
            internal_avatar=None if avatar is None else self.parse_asset(avatar),
            internal_profile=self.parse_user_profile(payload['profile']),
            tags=payload['tags'],
            server_count=payload['servers'],
            usage=BotUsage(payload['usage']),
        )

    def parse_discoverable_bot_search_result(
        self, payload: raw.DiscoverableBotSearchResult, /
    ) -> discovery.BotSearchResult:
        """Parses a bot search results object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The bot search results payload to parse.

        Returns
        -------
        :class:`~discovery.BotSearchResult`
            The parsed bot search results object.
        """
        return discovery.BotSearchResult(
            query=payload['query'],
            count=payload['count'],
            bots=list(map(self.parse_discoverable_bot, payload['bots'])),
            related_tags=payload['relatedTags'],
        )

    def parse_discoverable_bots_page(self, payload: raw.DiscoverableBotsPage, /) -> discovery.DiscoverableBotsPage:
        """Parses a discoverable bots page object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The discoverable bots page payload to parse.

        Returns
        -------
        :class:`~discovery.DiscoverableBotsPage`
            The parsed discoverable bots page object.
        """
        return discovery.DiscoverableBotsPage(
            bots=list(map(self.parse_discoverable_bot, payload['bots'])),
            popular_tags=payload['popularTags'],
        )

    def parse_discoverable_server(self, payload: raw.DiscoverableServer, /) -> discovery.DiscoverableServer:
        """Parses a discoverable server object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The discoverable server payload to parse.

        Returns
        -------
        :class:`~discovery.DiscoverableServer`
            The parsed server object.
        """
        icon = payload.get('icon')
        banner = payload.get('banner')

        return discovery.DiscoverableServer(
            state=self.state,
            id=payload['_id'],
            name=payload['name'],
            description=payload.get('description'),
            internal_icon=None if icon is None else self.parse_asset(icon),
            internal_banner=None if banner is None else self.parse_asset(banner),
            raw_flags=payload.get('flags') or 0,
            tags=payload['tags'],
            member_count=payload['members'],
            activity=ServerActivity(payload['activity']),
        )

    def parse_discoverable_servers_page(
        self, payload: raw.DiscoverableServersPage, /
    ) -> discovery.DiscoverableServersPage:
        """Parses a discoverable servers page object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The discoverable servers page payload to parse.

        Returns
        -------
        :class:`~discovery.DiscoverableServersPage`
            The parsed discoverable servers page object.
        """
        return discovery.DiscoverableServersPage(
            servers=list(map(self.parse_discoverable_server, payload['servers'])),
            popular_tags=payload['popularTags'],
        )

    def parse_discoverable_server_search_result(
        self, payload: raw.DiscoverableServerSearchResult, /
    ) -> discovery.ServerSearchResult:
        """Parses a server search results object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The server search results payload to parse.

        Returns
        -------
        :class:`~discovery.ServerSearchResult`
            The parsed server search results object.
        """
        return discovery.ServerSearchResult(
            query=payload['query'],
            count=payload['count'],
            servers=list(map(self.parse_discoverable_server, payload['servers'])),
            related_tags=payload['relatedTags'],
        )

    def parse_discoverable_theme(self, payload: raw.DiscoverableTheme, /) -> discovery.DiscoverableTheme:
        """Parses a discoverable theme object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The discoverable theme payload to parse.

        Returns
        -------
        :class:`~discovery.DiscoverableTheme`
            The parsed theme object.
        """
        return discovery.DiscoverableTheme(
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

    def parse_discoverable_theme_search_result(
        self, payload: raw.DiscoverableThemeSearchResult, /
    ) -> discovery.ThemeSearchResult:
        """Parses a theme search results object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The theme search results payload to parse.

        Returns
        -------
        :class:`~discovery.ThemeSearchResult`
            The parsed theme search results object.
        """
        return discovery.ThemeSearchResult(
            query=payload['query'],
            count=payload['count'],
            themes=list(map(self.parse_discoverable_theme, payload['themes'])),
            related_tags=payload['relatedTags'],
        )

    def parse_discoverable_themes_page(
        self, payload: raw.DiscoverableThemesPage, /
    ) -> discovery.DiscoverableThemesPage:
        """Parses a discoverable themes page object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The discoverable themes page payload to parse.

        Returns
        -------
        :class:`~discovery.DiscoverableThemesPage`
            The parsed discoverable themes page object.
        """
        return discovery.DiscoverableThemesPage(
            themes=list(map(self.parse_discoverable_theme, payload['themes'])),
            popular_tags=payload['popularTags'],
        )

    def parse_display_user(self, payload: raw.BannedUser, /) -> DisplayUser:
        """Parses a display user object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The display user payload to parse.

        Returns
        -------
        :class:`DisplayUser`
            The parsed user object.
        """
        avatar = payload.get('avatar')

        return DisplayUser(
            state=self.state,
            id=payload['_id'],
            name=payload['username'],
            discriminator=payload['discriminator'],
            internal_avatar=None if avatar is None else self.parse_asset(avatar),
        )

    def parse_embed(self, payload: raw.Embed, /) -> Embed:
        """Parses a embed object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The embed payload to parse.

        Returns
        -------
        :class:`Embed`
            The parsed embed object.
        """
        return self._embed_parsers[payload['type']](payload)

    def parse_embed_special(self, payload: raw.Special, /) -> EmbedSpecial:
        """Parses a embed special remote content object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The embed special remote content payload to parse.

        Returns
        -------
        :class:`EmbedSpecial`
            The parsed embed special remote content object.
        """
        return self._embed_special_parsers[payload['type']](payload)

    def parse_emoji(self, payload: raw.Emoji, /) -> Emoji:
        """Parses a emoji object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The emoji payload to parse.

        Returns
        -------
        :class:`Emoji`
            The parsed emoji object.
        """
        return self._emoji_parsers[payload['parent']['type']](payload)

    def parse_emoji_create_event(self, shard: Shard, payload: raw.ClientEmojiCreateEvent, /) -> ServerEmojiCreateEvent:
        """Parses a EmojiCreate event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`EmojiCreateEvent`
            The parsed emoji create event object.
        """
        return ServerEmojiCreateEvent(
            shard=shard,
            emoji=self.parse_server_emoji(payload),
        )

    def parse_emoji_delete_event(self, shard: Shard, payload: raw.ClientEmojiDeleteEvent, /) -> ServerEmojiDeleteEvent:
        """Parses a EmojiDelete event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`ServerEmojiDeleteEvent`
            The parsed server emoji delete event object.
        """
        return ServerEmojiDeleteEvent(
            shard=shard,
            emoji=None,
            server_id=None,
            emoji_id=payload['id'],
        )

    def parse_gif_embed_special(self, _: raw.GIFSpecial, /) -> GIFEmbedSpecial:
        """Parses a GIF embed special content object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The GIF embed special content payload to parse.

        Returns
        -------
        :class:`GIFEmbedSpecial`
            The parsed GIF embed special content object.
        """
        return _GIF_EMBED_SPECIAL

    def parse_group_channel(
        self,
        payload: raw.GroupChannel,
        recipients: typing.Union[
            tuple[typing.Literal[True], list[str]],
            tuple[typing.Literal[False], list[User]],
        ],
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
        raw_permissions = payload.get('permissions')

        return GroupChannel(
            state=self.state,
            id=payload['_id'],
            name=payload['name'],
            owner_id=payload['owner'],
            description=payload.get('description'),
            internal_recipients=recipients,
            internal_icon=None if icon is None else self.parse_asset(icon),
            last_message_id=payload.get('last_message_id'),
            raw_permissions=raw_permissions,
            nsfw=payload.get('nsfw', False),
        )

    def parse_group_invite(self, payload: raw.GroupInvite, /) -> GroupInvite:
        """Parses a group invite object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The group invite payload to parse.

        Returns
        -------
        :class:`GroupInvite`
            The parsed group invite object.
        """
        return GroupInvite(
            state=self.state,
            code=payload['_id'],
            creator_id=payload['creator'],
            channel_id=payload['channel'],
        )

    def parse_group_public_invite(self, payload: raw.GroupInviteResponse, /) -> GroupPublicInvite:
        """Parses a group public invite object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The group public invite payload to parse.

        Returns
        -------
        :class:`GroupPublicInvite`
            The parsed group public invite object.
        """
        user_avatar = payload.get('user_avatar')

        return GroupPublicInvite(
            state=self.state,
            code=payload['code'],
            channel_id=payload['channel_id'],
            channel_name=payload['channel_name'],
            channel_description=payload.get('channel_description'),
            user_name=payload['user_name'],
            internal_user_avatar=None if user_avatar is None else self.parse_asset(user_avatar),
        )

    def parse_image_embed(self, payload: raw.Image, /) -> ImageEmbed:
        """Parses a image embed object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The image embed payload to parse.

        Returns
        -------
        :class:`ImageEmbed`
            The parsed image embed object.
        """
        return ImageEmbed(
            url=payload['url'],
            width=payload['width'],
            height=payload['height'],
            size=ImageSize(payload['size']),
        )

    def parse_instance(self, payload: raw.RevoltConfig, /) -> Instance:
        """Parses a instance object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The instance payload to parse.

        Returns
        -------
        :class:`Instance`
            The parsed instance object.
        """
        return Instance(
            version=payload['revolt'],
            features=self.parse_instance_features_config(payload['features']),
            websocket_url=payload['ws'],
            app_url=payload['app'],
            vapid_public_key=payload['vapid'],
            build=self.parse_instance_build(payload['build']),
        )

    def parse_instance_build(self, payload: raw.BuildInformation, /) -> InstanceBuild:
        """Parses a instance build object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The instance build payload to parse.

        Returns
        -------
        :class:`InstanceBuild`
            The parsed instance build object.
        """
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
        """Parses a instance CAPTCHA feature object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The instance CAPTCHA feature payload to parse.

        Returns
        -------
        :class:`InstanceCaptchaFeature`
            The parsed instance CAPTCHA feature object.
        """
        return InstanceCaptchaFeature(
            enabled=payload['enabled'],
            key=payload['key'],
        )

    def parse_instance_features_config(self, payload: raw.RevoltFeatures, /) -> InstanceFeaturesConfig:
        """Parses a instance features config object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The instance features config payload to parse.

        Returns
        -------
        :class:`InstanceFeaturesConfig`
            The parsed instance features config object.
        """

        livekit: bool
        try:
            voice: raw.VoiceFeature = payload['livekit']  # pyright: ignore[reportTypedDictNotRequiredAccess]
            livekit = True
        except KeyError:
            voice = payload['voso']
            livekit = False

        return InstanceFeaturesConfig(
            captcha=self.parse_instance_captcha_feature(payload['captcha']),
            email_verification=payload['email'],
            invite_only=payload['invite_only'],
            autumn=self.parse_instance_generic_feature(payload['autumn']),
            january=self.parse_instance_generic_feature(payload['january']),
            voice=self.parse_instance_voice_feature(voice),
            livekit_voice=livekit,
        )

    def parse_instance_generic_feature(self, payload: raw.Feature, /) -> InstanceGenericFeature:
        """Parses a instance generic feature object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The instance generic feature payload to parse.

        Returns
        -------
        :class:`InstanceGenericFeature`
            The parsed instance generic feature object.
        """
        return InstanceGenericFeature(
            enabled=payload['enabled'],
            url=payload['url'],
        )

    def parse_instance_voice_feature(self, payload: raw.VoiceFeature, /) -> InstanceVoiceFeature:
        """Parses a instance voice feature object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The instance voice feature payload to parse.

        Returns
        -------
        :class:`InstanceVoiceFeature`
            The parsed instance voice feature object.
        """
        return InstanceVoiceFeature(
            enabled=payload['enabled'],
            url=payload['url'],
            websocket_url=payload['ws'],
        )

    def parse_invite(self, payload: raw.Invite, /) -> Invite:
        """Parses a invite object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The invite payload to parse.

        Returns
        -------
        :class:`Invite`
            The parsed invite object.
        """
        return self._invite_parsers[payload['type']](payload)

    def parse_lightspeed_embed_special(self, payload: raw.LightspeedSpecial, /) -> LightspeedEmbedSpecial:
        """Parses a Lightspeed.tv embed special content object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The Lightspeed.tv embed special content payload to parse.

        Returns
        -------
        :class:`LightspeedEmbedSpecial`
            The parsed Lightspeed.tv embed special content object.
        """
        return LightspeedEmbedSpecial(
            content_type=LightspeedContentType(payload['content_type']),
            id=payload['id'],
        )

    def parse_logout_event(self, shard: Shard, payload: raw.ClientLogoutEvent, /) -> LogoutEvent:
        """Parses a Logout event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`LogoutEvent`
            The parsed logout event object.
        """
        return LogoutEvent(shard=shard)

    def parse_member(
        self,
        payload: raw.Member,
        user: typing.Optional[User] = None,
        users: dict[str, User] = {},
        /,
    ) -> Member:
        """Parses a member object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The member payload to parse.
        user: Optional[:class:`User`]
            The user.
        users: Dict[:class:`str`, :class:`User`]
            The mapping of user IDs to user objects. Required for trying populating :attr:`Member.user`.

        Returns
        -------
        :class:`Member`
            The parsed member object.
        """
        assert not (user and users)

        id = payload['_id']
        user_id = id['user']

        # if user:
        #    assert user.id == user_id, 'IDs do not match'

        avatar = payload.get('avatar')
        timeout = payload.get('timeout')

        return Member(
            state=self.state,
            _user=user or users.get(user_id, user_id),
            server_id=id['server'],
            joined_at=_parse_dt(payload['joined_at']),
            nick=payload.get('nickname'),
            internal_server_avatar=None if avatar is None else self.parse_asset(avatar),
            roles=payload.get('roles', []),
            timed_out_until=None if timeout is None else _parse_dt(timeout),
            can_publish=payload.get('can_publish', True),
            can_receive=payload.get('can_receive', True),
        )

    def parse_member_list(self, payload: raw.AllMemberResponse, /) -> MemberList:
        """Parses a member list object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The member list payload to parse.

        Returns
        -------
        :class:`MemberList`
            The parsed member list object.
        """
        return MemberList(
            members=list(map(self.parse_member, payload['members'])),
            users=list(map(self.parse_user, payload['users'])),
        )

    def parse_members_with_users(self, payload: raw.AllMemberResponse, /) -> list[Member]:
        """Parses a object with members and associated users.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The list payload to parse.

        Returns
        -------
        List[:class:`Member`]
            The parsed member objects.
        """
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

        if member is not None:
            if user is not None:
                author = self.parse_member(member, self.parse_user(user))
            else:
                author = self.parse_member(member)
        elif user is not None:
            author = self.parse_user(user)
        else:
            author = members.get(author_id) or users.get(author_id) or author_id

        reactions = payload.get('reactions')

        return cls(
            state=self.state,
            id=payload['_id'],
            nonce=payload.get('nonce'),
            channel_id=payload['channel'],
            internal_author=author,
            webhook=None if webhook is None else self.parse_message_webhook(webhook),
            content=payload.get('content', ''),
            internal_system_event=None if system is None else self.parse_message_system_event(system, members, users),
            internal_attachments=list(map(self.parse_asset, payload.get('attachments', ()))),
            edited_at=None if edited_at is None else _parse_dt(edited_at),
            internal_embeds=list(map(self.parse_embed, payload.get('embeds', ()))),  # type: ignore
            mention_ids=payload.get('mentions', []),
            role_mention_ids=payload.get('role_mentions', []),
            replies=payload.get('replies', []),
            reactions={} if reactions is None else {k: tuple(v) for k, v in reactions.items()},
            interactions=None if interactions is None else self.parse_message_interactions(interactions),
            masquerade=None if masquerade is None else self.parse_message_masquerade(masquerade),
            pinned=payload.get('pinned', False),
            raw_flags=payload.get('flags', 0),
        )

    def parse_message_append_event(self, shard: Shard, payload: raw.ClientMessageAppendEvent, /) -> MessageAppendEvent:
        """Parses a MessageAppend event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`MessageAppendEvent`
            The parsed message append event object.
        """
        data = payload['append']
        embeds = data.get('embeds')

        return MessageAppendEvent(
            shard=shard,
            data=MessageAppendData(
                state=self.state,
                id=payload['id'],
                channel_id=payload['channel'],
                internal_embeds=UNDEFINED if embeds is None else list(map(self.parse_embed, embeds)),
            ),
            message=None,
        )

    def parse_message_call_started_system_event(
        self,
        payload: raw.CallStartedSystemMessage,
        members: dict[str, Member] = {},
        users: dict[str, User] = {},
        /,
    ) -> StatelessCallStartedSystemEvent:
        """Parses a "Call Started" message system event object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The message system event payload to parse.
        members: Dict[:class:`str`, :class:`Member`]
            Should be empty for :class:`StatelessCallStartedSystemEvent`.
        users: Dict[:class:`str`, :class:`User`]
            The mapping of user IDs to user objects. Required for trying populating :attr:`StatelessCallStartedSystemEvent.by`.

        Returns
        -------
        :class:`StatelessCallStartedSystemEvent`
            The parsed "Call Started" message system event object.
        """

        by_id = payload['by']

        return StatelessCallStartedSystemEvent(internal_by=users.get(by_id, by_id))

    def parse_message_channel_description_changed_system_event(
        self,
        payload: raw.ChannelDescriptionChangedSystemMessage,
        members: dict[str, Member] = {},
        users: dict[str, User] = {},
        /,
    ) -> StatelessChannelDescriptionChangedSystemEvent:
        """Parses a "Channel Description Changed" message system event object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The message system event payload to parse.
        members: Dict[:class:`str`, :class:`Member`]
            Should be empty for :class:`StatelessChannelDescriptionChangedSystemEvent`.
        users: Dict[:class:`str`, :class:`User`]
            The mapping of user IDs to user objects. Required for trying populating :attr:`StatelessChannelDescriptionChangedSystemEvent.by`.

        Returns
        -------
        :class:`StatelessChannelDescriptionChangedSystemEvent`
            The parsed "Channel Description Changed" message system event object.
        """

        by_id = payload['by']

        return StatelessChannelDescriptionChangedSystemEvent(internal_by=users.get(by_id, by_id))

    def parse_message_channel_icon_changed_system_event(
        self,
        payload: raw.ChannelIconChangedSystemMessage,
        members: dict[str, Member] = {},
        users: dict[str, User] = {},
        /,
    ) -> StatelessChannelIconChangedSystemEvent:
        """Parses a "Channel Icon Changed" message system event object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The message system event payload to parse.
        members: Dict[:class:`str`, :class:`Member`]
            Should be empty for :class:`StatelessChannelIconChangedSystemEvent`.
        users: Dict[:class:`str`, :class:`User`]
            The mapping of user IDs to user objects. Required for trying populating :attr:`StatelessChannelIconChangedSystemEvent.by`.

        Returns
        -------
        :class:`StatelessChannelIconChangedSystemEvent`
            The parsed "Channel Icon Changed" message system event object.
        """

        by_id = payload['by']

        return StatelessChannelIconChangedSystemEvent(internal_by=users.get(by_id, by_id))

    def parse_message_channel_renamed_system_event(
        self, payload: raw.ChannelRenamedSystemMessage, members: dict[str, Member] = {}, users: dict[str, User] = {}, /
    ) -> StatelessChannelRenamedSystemEvent:
        """Parses a "Channel Renamed" message system event object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The message system event payload to parse.
        members: Dict[:class:`str`, :class:`Member`]
            Should be empty for :class:`StatelessChannelRenamedSystemEvent`.
        users: Dict[:class:`str`, :class:`User`]
            The mapping of user IDs to user objects. Required for trying populating :attr:`StatelessChannelRenamedSystemEvent.by`.

        Returns
        -------
        :class:`StatelessChannelRenamedSystemEvent`
            The parsed "Channel Renamed" message system event object.
        """

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
        """Parses a "Channel Ownership Changed" message system event object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The message system event payload to parse.
        members: Dict[:class:`str`, :class:`Member`]
            Should be empty for :class:`StatelessChannelOwnershipChangedSystemEvent`.
        users: Dict[:class:`str`, :class:`User`]
            The mapping of user IDs to user objects. Required for trying populating :attr:`StatelessChannelOwnershipChangedSystemEvent.from_` and :attr:`StatelessChannelOwnershipChangedSystemEvent.to`.

        Returns
        -------
        :class:`StatelessChannelOwnershipChangedSystemEvent`
            The parsed "Channel Ownership Changed" message system event object.
        """
        from_id = payload['from']
        to_id = payload['to']

        return StatelessChannelOwnershipChangedSystemEvent(
            internal_from=users.get(from_id, from_id),
            internal_to=users.get(to_id, to_id),
        )

    def parse_message_delete_event(self, shard: Shard, payload: raw.ClientMessageDeleteEvent, /) -> MessageDeleteEvent:
        """Parses a MessageDelete event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`MessageDeleteEvent`
            The parsed message delete event object.
        """
        return MessageDeleteEvent(
            shard=shard,
            channel_id=payload['channel'],
            message_id=payload['id'],
            message=None,
        )

    def parse_message_event(self, shard: Shard, payload: raw.ClientMessageEvent, /) -> MessageCreateEvent:
        """Parses a Message event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`MessageCreateEvent`
            The parsed message create event object.
        """
        return MessageCreateEvent(shard=shard, message=self.parse_message(payload))

    def parse_message_interactions(self, payload: raw.Interactions, /) -> MessageInteractions:
        """Parses a message interactions object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The message interactions payload to parse.

        Returns
        -------
        :class:`MessageInteractions`
            The parsed message interactions object.
        """

        return MessageInteractions(
            reactions=payload.get('reactions', []),
            restrict_reactions=payload.get('restrict_reactions', False),
        )

    def parse_message_masquerade(self, payload: raw.Masquerade, /) -> MessageMasquerade:
        """Parses a message masquerade object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The message masquerade payload to parse.

        Returns
        -------
        :class:`MessageMasquerade`
            The parsed message masquerade object.
        """

        return MessageMasquerade(name=payload.get('name'), avatar=payload.get('avatar'), color=payload.get('colour'))

    def parse_message_message_pinned_system_event(
        self,
        payload: raw.MessagePinnedSystemMessage,
        members: dict[str, Member] = {},
        users: dict[str, User] = {},
        /,
    ) -> StatelessMessagePinnedSystemEvent:
        """Parses a "Message Pinned" message system event object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The message system event payload to parse.
        members: Dict[:class:`str`, :class:`Member`]
            The mapping of user IDs to member objects. Required for trying populating :attr:`StatelessMessagePinnedSystemEvent.by`.
        users: Dict[:class:`str`, :class:`User`]
            The mapping of user IDs to user objects. Required for trying populating :attr:`StatelessMessagePinnedSystemEvent.by`.

        Returns
        -------
        :class:`StatelessMessagePinnedSystemEvent`
            The parsed "Message Pinned" message system event object.
        """
        pinned_message_id = payload['id']
        by_id = payload['by']

        return StatelessMessagePinnedSystemEvent(
            pinned_message_id=pinned_message_id,
            internal_by=members.get(by_id, users.get(by_id, by_id)),
        )

    def parse_message_message_unpinned_system_event(
        self, payload: raw.MessageUnpinnedSystemMessage, members: dict[str, Member] = {}, users: dict[str, User] = {}, /
    ) -> StatelessMessageUnpinnedSystemEvent:
        """Parses a "Message Unpinned" message system event object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The message system event payload to parse.
        members: Dict[:class:`str`, :class:`Member`]
            The mapping of user IDs to member objects. Required for trying populating :attr:`StatelessMessageUnpinnedSystemEvent.by`.
        users: Dict[:class:`str`, :class:`User`]
            The mapping of user IDs to user objects. Required for trying populating :attr:`StatelessMessageUnpinnedSystemEvent.by`.

        Returns
        -------
        :class:`StatelessMessageUnpinnedSystemEvent`
            The parsed "Message Unpinned" message system event object.
        """
        unpinned_message_id = payload['id']
        by_id = payload['by']

        return StatelessMessageUnpinnedSystemEvent(
            unpinned_message_id=unpinned_message_id,
            internal_by=members.get(by_id, users.get(by_id, by_id)),
        )

    def parse_message_react_event(self, shard: Shard, payload: raw.ClientMessageReactEvent, /) -> MessageReactEvent:
        """Parses a MessageReact event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`MessageReactEvent`
            The parsed message react event object.
        """
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
        """Parses a MessageRemoveReaction event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`MessageClearReactionEvent`
            The parsed message clear reaction event object.
        """
        return MessageClearReactionEvent(
            shard=shard,
            channel_id=payload['channel_id'],
            message_id=payload['id'],
            emoji=payload['emoji_id'],
            message=None,
        )

    def parse_message_reported_content(self, payload: raw.MessageReportedContent, /) -> MessageReportedContent:
        """Parses a message reported content object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The message reported content payload to parse.

        Returns
        -------
        :class:`MessageReportedContent`
            The parsed message reported content object.
        """

        return MessageReportedContent(
            target_id=payload['id'],
            reason=ContentReportReason(payload['report_reason']),
        )

    def parse_message_system_event(
        self,
        payload: raw.SystemMessage,
        members: dict[str, Member],
        users: dict[str, User],
        /,
    ) -> StatelessSystemEvent:
        """Parses a message system event object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The message system event payload to parse.
        members: Dict[:class:`str`, :class:`Member`]
            The mapping of user IDs to member objects. Required for trying populating various user-related attributes.
        users: Dict[:class:`str`, :class:`User`]
            The mapping of user IDs to user objects. Required for trying populating various user-related attributes.

        Returns
        -------
        :class:`StatelessSystemEvent`
            The parsed message system event object.
        """

        return self._message_system_event_parsers[payload['type']](payload, members, users)

    def parse_message_text_system_event(
        self,
        payload: raw.TextSystemMessage,
        members: dict[str, Member] = {},
        users: dict[str, User] = {},
        /,
    ) -> TextSystemEvent:
        """Parses a text message system event object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The message system event payload to parse.
        members: Dict[:class:`str`, :class:`Member`]
            Should be empty for :class:`TextSystemEvent`.
        users: Dict[:class:`str`, :class:`User`]
            Should be empty for :class:`TextSystemEvent`.

        Returns
        -------
        :class:`TextSystemEvent`
            The parsed text message system event object.
        """

        return TextSystemEvent(content=payload['content'])

    def parse_message_unreact_event(
        self, shard: Shard, payload: raw.ClientMessageUnreactEvent, /
    ) -> MessageUnreactEvent:
        """Parses a MessageUnreact event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`MessageUnreactEvent`
            The parsed message unreact event object.
        """
        return MessageUnreactEvent(
            shard=shard,
            channel_id=payload['channel_id'],
            message_id=payload['id'],
            user_id=payload['user_id'],
            emoji=payload['emoji_id'],
            message=None,
        )

    def parse_message_update_event(self, shard: Shard, payload: raw.ClientMessageUpdateEvent, /) -> MessageUpdateEvent:
        """Parses a MessageUpdate event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`MessageUpdateEvent`
            The parsed message update event object.
        """
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
                content=UNDEFINED if content is None else content,
                edited_at=UNDEFINED if edited_at is None else _parse_dt(edited_at),
                internal_embeds=UNDEFINED if embeds is None else list(map(self.parse_embed, embeds)),
                pinned=False if 'Pinned' in clear else data.get('pinned', UNDEFINED),
                reactions=UNDEFINED if reactions is None else {k: tuple(v) for k, v in reactions.items()},
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
        """Parses a "User Added" message system event object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The message system event payload to parse.
        members: Dict[:class:`str`, :class:`Member`]
            Should be empty for :class:`StatelessUserAddedSystemEvent`.
        users: Dict[:class:`str`, :class:`User`]
            The mapping of user IDs to user objects. Required for trying populating :attr:`StatelessUserAddedSystemEvent.user` and :attr:`StatelessUserAddedSystemEvent.by`.

        Returns
        -------
        :class:`StatelessUserAddedSystemEvent`
            The parsed "User Added" message system event object.
        """

        user_id = payload['id']
        by_id = payload['by']

        return StatelessUserAddedSystemEvent(
            internal_user=users.get(user_id, user_id),
            internal_by=users.get(by_id, by_id),
        )

    def parse_message_user_banned_system_event(
        self,
        payload: raw.UserBannedSystemMessage,
        members: dict[str, Member] = {},
        users: dict[str, User] = {},
        /,
    ) -> StatelessUserBannedSystemEvent:
        """Parses a "User Banned" message system event object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The message system event payload to parse.
        members: Dict[:class:`str`, :class:`Member`]
            The mapping of user IDs to member objects. Required for trying populating :attr:`StatelessUserBannedSystemEvent.user`.
        users: Dict[:class:`str`, :class:`User`]
            The mapping of user IDs to user objects. Required for trying populating :attr:`StatelessUserBannedSystemEvent.user`.

        Returns
        -------
        :class:`StatelessUserBannedSystemEvent`
            The parsed "User Banned" message system event object.
        """

        user_id = payload['id']

        return StatelessUserBannedSystemEvent(internal_user=members.get(user_id, users.get(user_id, user_id)))

    def parse_message_user_joined_system_event(
        self,
        payload: raw.UserJoinedSystemMessage,
        members: dict[str, Member] = {},
        users: dict[str, User] = {},
        /,
    ) -> StatelessUserJoinedSystemEvent:
        """Parses a "User Joined" message system event object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The message system event payload to parse.
        members: Dict[:class:`str`, :class:`Member`]
            The mapping of user IDs to member objects. Required for trying populating :attr:`StatelessUserJoinedSystemEvent.user`.
        users: Dict[:class:`str`, :class:`User`]
            The mapping of user IDs to user objects. Required for trying populating :attr:`StatelessUserJoinedSystemEvent.user`.

        Returns
        -------
        :class:`StatelessUserJoinedSystemEvent`
            The parsed "User Joined" message system event object.
        """
        user_id = payload['id']

        return StatelessUserJoinedSystemEvent(internal_user=members.get(user_id, users.get(user_id, user_id)))

    def parse_message_user_kicked_system_event(
        self,
        payload: raw.UserKickedSystemMessage,
        members: dict[str, Member] = {},
        users: dict[str, User] = {},
        /,
    ) -> StatelessUserKickedSystemEvent:
        """Parses a "User Kicked" message system event object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The message system event payload to parse.
        members: Dict[:class:`str`, :class:`Member`]
            The mapping of user IDs to member objects. Required for trying populating :attr:`StatelessUserKickedSystemEvent.user`.
        users: Dict[:class:`str`, :class:`User`]
            The mapping of user IDs to user objects. Required for trying populating :attr:`StatelessUserKickedSystemEvent.user`.

        Returns
        -------
        :class:`StatelessUserKickedSystemEvent`
            The parsed "User Kicked" message system event object.
        """
        user_id = payload['id']

        return StatelessUserKickedSystemEvent(internal_user=members.get(user_id, users.get(user_id, user_id)))

    def parse_message_user_left_system_event(
        self,
        payload: raw.UserLeftSystemMessage,
        members: dict[str, Member] = {},
        users: dict[str, User] = {},
        /,
    ) -> StatelessUserLeftSystemEvent:
        """Parses a "User Left" message system event object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The message system event payload to parse.
        members: Dict[:class:`str`, :class:`Member`]
            The mapping of user IDs to member objects. Required for trying populating :attr:`StatelessUserLeftSystemEvent.user`.
        users: Dict[:class:`str`, :class:`User`]
            The mapping of user IDs to user objects. Required for trying populating :attr:`StatelessUserLeftSystemEvent.user`.

        Returns
        -------
        :class:`StatelessUserLeftSystemEvent`
            The parsed "User Left" message system event object.
        """
        user_id = payload['id']

        return StatelessUserLeftSystemEvent(internal_user=members.get(user_id, users.get(user_id, user_id)))

    def parse_message_user_remove_system_event(
        self,
        payload: raw.UserRemoveSystemMessage,
        members: dict[str, Member] = {},
        users: dict[str, User] = {},
        /,
    ) -> StatelessUserRemovedSystemEvent:
        """Parses a "User Removed" message system event object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The message system event payload to parse.
        members: Dict[:class:`str`, :class:`Member`]
            The mapping of user IDs to member objects. Required for trying populating :attr:`StatelessUserRemovedSystemEvent.user` and :attr:`StatelessUserRemovedSystemEvent.by`.
        users: Dict[:class:`str`, :class:`User`]
            The mapping of user IDs to user objects. Required for trying populating :attr:`StatelessUserRemovedSystemEvent.user` and :attr:`StatelessUserRemovedSystemEvent.by`.

        Returns
        -------
        :class:`StatelessUserRemovedSystemEvent`
            The parsed "User Removed" message system event object.
        """

        user_id = payload['id']
        by_id = payload['by']

        return StatelessUserRemovedSystemEvent(
            internal_user=members.get(user_id, users.get(user_id, user_id)),
            internal_by=members.get(by_id, users.get(by_id, by_id)),
        )

    def parse_message_webhook(self, payload: raw.MessageWebhook, /) -> MessageWebhook:
        """Parses a message webhook object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The message webhook payload to parse.

        Returns
        -------
        :class:`MessageWebhook`
            The parsed message webhook object.
        """

        return MessageWebhook(
            name=payload['name'],
            avatar=payload.get('avatar'),
        )

    def parse_messages(self, payload: raw.BulkMessageResponse, /) -> list[Message]:
        """Parses a object with messages and associated users/members.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The list payload to parse.

        Returns
        -------
        List[:class:`Message`]
            The parsed message objects.
        """
        if isinstance(payload, list):
            return list(map(self.parse_message, payload))
        elif isinstance(payload, dict):
            users = list(map(self.parse_user, payload['users']))
            users_mapping = {u.id: u for u in users}

            members = [self.parse_member(e, None, users_mapping) for e in payload.get('members', ())]
            members_mapping = {m.id: m for m in members}

            return [self.parse_message(e, members_mapping, users_mapping) for e in payload['messages']]
        raise RuntimeError('Unreachable')

    def parse_mfa_response_login(
        self, payload: raw.a.MFAResponseLogin, friendly_name: typing.Optional[str], /
    ) -> MFARequired:
        """Parses a "MFA required" login response object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The login response payload to parse.
        friendly_name: Optional[:class:`str`]
            The user-friendly name of client.

        Returns
        -------
        :class:`MFARequired`
            The parsed "MFA required" login response object.
        """
        return MFARequired(
            ticket=payload['ticket'],
            allowed_methods=list(map(MFAMethod, payload['allowed_methods'])),
            state=self.state,
            internal_friendly_name=friendly_name,
        )

    def parse_mfa_ticket(self, payload: raw.a.MFATicket, /) -> MFATicket:
        """Parses a MFA ticket object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The MFA ticket payload to parse.

        Returns
        -------
        :class:`MFATicket`
            The parsed MFA ticket object.
        """
        return MFATicket(
            id=payload['_id'],
            account_id=payload['account_id'],
            token=payload['token'],
            validated=payload['validated'],
            authorised=payload['authorised'],
            last_totp_code=payload.get('last_totp_code'),
        )

    def parse_multi_factor_status(self, payload: raw.a.MultiFactorStatus, /) -> MFAStatus:
        """Parses a MFA status object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The MFA status payload to parse.

        Returns
        -------
        :class:`MFAStatus`
            The parsed MFA status object.
        """
        return MFAStatus(
            totp_mfa=payload['totp_mfa'],
            recovery_active=payload['recovery_active'],
        )

    def parse_mutuals(self, payload: raw.MutualResponse, /) -> Mutuals:
        """Parses a mutual response object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The mutual response payload to parse.

        Returns
        -------
        :class:`Mutuals`
            The parsed mutual response object.
        """
        return Mutuals(
            user_ids=payload['users'],
            server_ids=payload['servers'],
        )

    def parse_none_embed(self, _: raw.NoneEmbed, /) -> NoneEmbed:
        """Parses a empty embed object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The empty embed payload to parse.

        Returns
        -------
        :class:`NoneEmbed`
            The parsed empty embed object.
        """
        return _NONE_EMBED

    def parse_none_embed_special(self, _: raw.NoneSpecial, /) -> NoneEmbedSpecial:
        """Parses a empty embed special content object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The empty embed special content payload to parse.

        Returns
        -------
        :class:`NoneEmbedSpecial`
            The parsed empty embed special content object.
        """
        return _NONE_EMBED_SPECIAL

    def parse_own_user(self, payload: raw.User, /) -> OwnUser:
        """Parses a own user object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The own user payload to parse.

        Returns
        -------
        :class:`OwnUser`
            The parsed user object.
        """

        avatar = payload.get('avatar')
        status = payload.get('status')
        # profile = payload.get('profile')
        privileged = payload.get('privileged', False)

        bot = payload.get('bot')

        relations = list(map(self.parse_relationship, payload.get('relations', ())))

        return OwnUser(
            state=self.state,
            id=payload['_id'],
            name=payload['username'],
            discriminator=payload['discriminator'],
            display_name=payload.get('display_name'),
            internal_avatar=None if avatar is None else self.parse_asset(avatar),
            relations={relation.id: relation for relation in relations},
            raw_badges=payload.get('badges', 0),
            status=None if status is None else self.parse_user_status(status),
            # internal_profile=None if profile is None else self.parse_user_profile(profile),
            raw_flags=payload.get('flags', 0),
            privileged=privileged,
            bot=None if bot is None else self.parse_bot_user_metadata(bot),
            relationship=RelationshipStatus(payload['relationship']),
            online=payload['online'],
        )

    def parse_partial_account(self, payload: raw.a.AccountInfo, /) -> PartialAccount:
        """Parses a partial account object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The partial account payload to parse.

        Returns
        -------
        :class:`PartialAccount`
            The parsed partial account object.
        """
        return PartialAccount(id=payload['_id'], email=payload['email'])

    def parse_partial_session(self, payload: raw.a.SessionInfo, /) -> PartialSession:
        """Parses a partial session object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The partial session payload to parse.

        Returns
        -------
        :class:`PartialSession`
            The parsed partial session object.
        """

        return PartialSession(state=self.state, id=payload['_id'], name=payload['name'])

    def parse_partial_user_profile(
        self, payload: raw.UserProfile, clear: list[raw.FieldsUser], /
    ) -> PartialUserProfile:
        """Parses a partial user profile object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The partial user profile payload to parse.
        clear: List[raw.FieldsUser]
            The fields that were cleared.

        Returns
        -------
        :class:`PartialUserProfile`
            The parsed partial user profile object.
        """
        background = payload.get('background')

        return PartialUserProfile(
            state=self.state,
            content=None if 'ProfileContent' in clear else payload.get('content', UNDEFINED),
            internal_background=None
            if 'ProfileBackground' in clear
            else (UNDEFINED if background is None else self.parse_asset(background)),
        )

    def parse_permission_override(self, payload: raw.Override, /) -> PermissionOverride:
        """Parses a permission override object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The permission override payload to parse.

        Returns
        -------
        :class:`PermissionOverride`
            The parsed permission override object.
        """
        ret = _new_permission_override(PermissionOverride)
        ret.raw_allow = payload['allow']
        ret.raw_deny = payload['deny']
        return ret

    def parse_permission_override_field(self, payload: raw.OverrideField, /) -> PermissionOverride:
        """Parses a permission override field object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The permission override field payload to parse.

        Returns
        -------
        :class:`PermissionOverride`
            The parsed permission override object.
        """
        ret = _new_permission_override(PermissionOverride)
        ret.raw_allow = payload['a']
        ret.raw_deny = payload['d']
        return ret

    def parse_public_bot(self, payload: raw.PublicBot, /) -> PublicBot:
        """Parses a public bot object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The public bot payload to parse.

        Returns
        -------
        :class:`PublicBot`
            The parsed public bot object.
        """

        return PublicBot(
            state=self.state,
            id=payload['_id'],
            name=payload['username'],
            internal_avatar_id=payload.get('avatar'),
            description=payload.get('description', ''),
        )

    def parse_public_invite(self, payload: raw.InviteResponse, /) -> PublicInvite:
        """Parses a public invite object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The public invite payload to parse.

        Returns
        -------
        :class:`PublicInvite`
            The parsed public invite object.
        """
        return self._public_invite_parsers.get(payload['type'], self.parse_unknown_public_invite)(payload)

    def parse_ready_event(self, shard: Shard, payload: raw.ClientReadyEvent, /) -> ReadyEvent:
        """Parses a Ready event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`ReadyEvent`
            The parsed ready event object.
        """

        users = list(map(self.parse_user, payload.get('users', ())))
        me = users[-1]
        if me.__class__ is not OwnUser or not isinstance(me, OwnUser):
            for user in users:
                if me.__class__ is not OwnUser or isinstance(me, OwnUser):
                    me = user

        if me.__class__ is not OwnUser or not isinstance(me, OwnUser):
            raise TypeError('Unable to find own user')

        servers = [self.parse_server(s, (True, s['channels'])) for s in payload.get('servers', ())]
        channels: list[Channel] = list(map(self.parse_channel, payload.get('channels', ())))  # type: ignore
        members = list(map(self.parse_member, payload.get('members', ())))
        emojis = list(map(self.parse_server_emoji, payload.get('emojis', ())))
        user_settings = self.parse_user_settings(payload.get('user_settings', {}), False)
        read_states = list(map(self.parse_channel_unread, payload.get('channel_unreads', ())))
        voice_states = list(map(self.parse_channel_voice_state, payload.get('voice_states', ())))

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
            voice_states=voice_states,
        )

    def parse_rejected_report(self, payload: raw.RejectedReport, /) -> RejectedReport:
        """Parses a rejected report object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The rejected report payload to parse.

        Returns
        -------
        :class:`RejectedReport`
            The parsed rejected report object.
        """

        closed_at = payload.get('closed_at')

        return RejectedReport(
            state=self.state,
            id=payload['_id'],
            author_id=payload['author_id'],
            content=self.parse_reported_content(payload['content']),
            additional_context=payload['additional_context'],
            notes=payload.get('notes', ''),
            rejection_reason=payload['rejection_reason'],
            closed_at=None if closed_at is None else _parse_dt(closed_at),
        )

    def parse_relationship(self, payload: raw.Relationship, /) -> Relationship:
        """Parses a relationship object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The relationship payload to parse.

        Returns
        -------
        :class:`Relationship`
            The parsed relationship object.
        """
        return Relationship(
            id=payload['_id'],
            status=RelationshipStatus(payload['status']),
        )

    @typing.overload
    def parse_report(self, payload: raw.CreatedReport, /) -> CreatedReport: ...

    @typing.overload
    def parse_report(self, payload: raw.RejectedReport, /) -> RejectedReport: ...

    @typing.overload
    def parse_report(self, payload: raw.ResolvedReport, /) -> ResolvedReport: ...

    def parse_report(self, payload: raw.Report, /) -> Report:
        """Parses a report object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The report payload to parse.

        Returns
        -------
        :class:`Report`
            The parsed report object.
        """

        return self._report_parsers[payload['status']](payload)

    def parse_report_create_event(self, shard: Shard, payload: raw.ClientReportCreateEvent, /) -> ReportCreateEvent:
        """Parses a ReportCreate event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`ReportCreateEvent`
            The parsed report create event object.
        """

        return ReportCreateEvent(
            shard=shard,
            report=self.parse_created_report(payload),
        )

    def parse_reported_content(self, payload: raw.ReportedContent, /) -> ReportedContent:
        """Parses a reported content object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The reported content payload to parse.

        Returns
        -------
        :class:`ReportedContent`
            The parsed reported content object.
        """

        return self._reported_content_parsers[payload['type']](payload)

    def parse_resolved_report(self, payload: raw.ResolvedReport, /) -> ResolvedReport:
        """Parses a resolved report object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The resolved report payload to parse.

        Returns
        -------
        :class:`ResolvedReport`
            The parsed resolved report object.
        """

        closed_at = payload.get('closed_at')

        return ResolvedReport(
            state=self.state,
            id=payload['_id'],
            author_id=payload['author_id'],
            content=self.parse_reported_content(payload['content']),
            additional_context=payload['additional_context'],
            notes=payload.get('notes', ''),
            closed_at=None if closed_at is None else _parse_dt(closed_at),
        )

    def parse_response_login(self, payload: raw.a.ResponseLogin, friendly_name: typing.Optional[str], /) -> LoginResult:
        """Parses a login response object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The login response payload to parse.
        friendly_name: Optional[:class:`str`]
            The user-friendly name of client.

        Returns
        -------
        :class:`LoginResult`
            The parsed login response object.
        """
        if payload['result'] == 'Success':
            return self.parse_session(payload)
        elif payload['result'] == 'MFA':
            return self.parse_mfa_response_login(payload, friendly_name)
        elif payload['result'] == 'Disabled':
            return self.parse_disabled_response_login(payload)
        else:
            raise NotImplementedError(payload)

    def parse_response_webhook(self, payload: raw.ResponseWebhook, /) -> Webhook:
        """Parses a "webhook as response" object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The webhook payload to parse.

        Returns
        -------
        :class:`Webhook`
            The parsed webhook object.
        """
        id = payload['id']
        avatar = payload.get('avatar')

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
            creator_id='',
            channel_id=payload['channel_id'],
            raw_permissions=payload['permissions'],
            token=None,
        )

    def parse_role(self, payload: raw.Role, role_id: str, server_id: str, /) -> Role:
        """Parses a role object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The role payload to parse.
        role_id: :class:`str`
            The role's ID.
        server_id: :class:`str`
            The server's ID the role belongs to.


        Returns
        -------
        :class:`Role`
            The parsed role object.
        """
        return Role(
            state=self.state,
            id=role_id,
            name=payload['name'],
            permissions=self.parse_permission_override_field(payload['permissions']),
            color=payload.get('colour'),
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
        payload: raw.Server,
        channels: typing.Union[
            tuple[typing.Literal[True], list[str]],
            tuple[typing.Literal[False], list[ServerChannel]],
        ],
        /,
    ) -> Server:
        """Parses a server object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The server payload to parse.
        channels: Union[Tuple[Literal[True], List[:class:`str`]], Tuple[Literal[False], List[:class:`ServerChannel`]]]
            The server's channels.

        Returns
        -------
        :class:`Server`
            The parsed server object.
        """
        server_id = payload['_id']

        system_messages = payload.get('system_messages')

        roles = {}
        for id, role_data in payload.get('roles', {}).items():
            role_id = id
            roles[role_id] = self.parse_role(role_data, role_id, server_id)

        icon = payload.get('icon')
        banner = payload.get('banner')

        return Server(
            state=self.state,
            id=server_id,
            owner_id=payload['owner'],
            name=payload['name'],
            description=payload.get('description'),
            internal_channels=channels,
            categories=list(map(self.parse_category, payload.get('categories', ()))),
            system_messages=None if system_messages is None else self.parse_system_message_channels(system_messages),
            roles=roles,
            raw_default_permissions=payload['default_permissions'],
            internal_icon=None if icon is None else self.parse_asset(icon),
            internal_banner=None if banner is None else self.parse_asset(banner),
            raw_flags=payload.get('flags', 0),
            nsfw=payload.get('nsfw', False),
            analytics=payload.get('analytics', False),
            discoverable=payload.get('discoverable', False),
        )

    def parse_server(
        self,
        payload: raw.Server,
        channels: typing.Union[
            tuple[typing.Literal[True], list[str]],
            tuple[typing.Literal[False], list[raw.ServerChannel]],
        ],
        /,
    ) -> Server:
        """Parses a server object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The server payload to parse.
        channels: Union[Tuple[Literal[True], List[:class:`str`]], Tuple[Literal[False], List[raw.ServerChannel]]]
            The server's channels.

        Returns
        -------
        :class:`Server`
            The parsed server object.
        """
        internal_channels: typing.Union[
            tuple[typing.Literal[True], list[str]],
            tuple[typing.Literal[False], list[ServerChannel]],
        ] = channels if channels[0] else (False, list(map(self.parse_channel, channels[1])))  # type: ignore
        return self._parse_server(payload, internal_channels)

    def parse_server_create_event(
        self, shard: Shard, payload: raw.ClientServerCreateEvent, joined_at: datetime, /
    ) -> ServerCreateEvent:
        """Parses a server create event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`ServerCreateEvent`
            The parsed server create event object.
        """
        return ServerCreateEvent(
            shard=shard,
            joined_at=joined_at,
            server=self.parse_server(payload['server'], (False, payload['channels'])),
            emojis=list(map(self.parse_server_emoji, payload['emojis'])),
            voice_states=list(map(self.parse_channel_voice_state, payload.get('voice_states', ()))),
        )

    def parse_server_delete_event(self, shard: Shard, payload: raw.ClientServerDeleteEvent, /) -> ServerDeleteEvent:
        """Parses a server delete event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`ServerDeleteEvent`
            The parsed server delete event object.
        """
        return ServerDeleteEvent(
            shard=shard,
            server_id=payload['id'],
            server=None,
        )

    def parse_server_emoji(self, payload: raw.ServerEmoji, /) -> ServerEmoji:
        """Parses a server emoji object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The server emoji payload to parse.

        Returns
        -------
        :class:`ServerEmoji`
            The parsed server emoji object.
        """
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
        """Parses a server private invite object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The server private invite payload to parse.

        Returns
        -------
        :class:`ServerPrivateInvite`
            The parsed server private invite object.
        """

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
        """Parses a server member join event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`ServerMemberJoinEvent`
            The parsed server member join event object.
        """
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
                can_publish=True,
                can_receive=True,
            ),
        )

    def parse_server_member_leave_event(
        self, shard: Shard, payload: raw.ClientServerMemberLeaveEvent, /
    ) -> ServerMemberRemoveEvent:
        """Parses a server member remove event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`ServerMemberRemoveEvent`
            The parsed server member remove event object.
        """
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
        """Parses a server member update event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`ServerMemberUpdateEvent`
            The parsed server member update event object.
        """
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
                internal_server_avatar=None
                if 'Avatar' in clear
                else (UNDEFINED if avatar is None else self.parse_asset(avatar)),
                roles=[] if 'Roles' in clear else (UNDEFINED if roles is None else roles),
                timed_out_until=None if 'Timeout' in clear else (UNDEFINED if timeout is None else _parse_dt(timeout)),
                can_publish=data.get('can_publish', UNDEFINED),
                can_receive=data.get('can_receive', UNDEFINED),
            ),
            before=None,  # filled on dispatch
            after=None,  # filled on dispatch
        )

    def parse_server_public_invite(self, payload: raw.ServerInviteResponse, /) -> ServerPublicInvite:
        """Parses a server public invite object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The server public invite payload to parse.

        Returns
        -------
        :class:`ServerPublicInvite`
            The parsed server public invite object.
        """

        server_icon = payload.get('server_icon')
        server_banner = payload.get('server_banner')

        user_avatar = payload.get('user_avatar')

        return ServerPublicInvite(
            state=self.state,
            code=payload['code'],
            server_id=payload['server_id'],
            server_name=payload['server_name'],
            internal_server_icon=None if server_icon is None else self.parse_asset(server_icon),
            internal_server_banner=None if server_banner is None else self.parse_asset(server_banner),
            raw_server_flags=payload.get('server_flags', 0),
            channel_id=payload['channel_id'],
            channel_name=payload['channel_name'],
            channel_description=payload.get('channel_description'),
            user_name=payload['user_name'],
            internal_user_avatar=None if user_avatar is None else self.parse_asset(user_avatar),
            member_count=payload['member_count'],
        )

    def parse_server_reported_content(self, payload: raw.ServerReportedContent, /) -> ServerReportedContent:
        """Parses a server reported content object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The server reported content payload to parse.

        Returns
        -------
        :class:`ServerReportedContent`
            The parsed server reported content object.
        """

        return ServerReportedContent(
            target_id=payload['id'],
            reason=ContentReportReason(payload['report_reason']),
        )

    def parse_server_role_delete_event(
        self, shard: Shard, payload: raw.ClientServerRoleDeleteEvent, /
    ) -> ServerRoleDeleteEvent:
        """Parses a ServerRoleDelete event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`ServerRoleDeleteEvent`
            The parsed server role delete event object.
        """
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
        """Parses a ServerRoleUpdate event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`RawServerRoleUpdateEvent`
            The parsed server role create/update event object.
        """
        data = payload['data']
        clear = payload['clear']

        permissions = data.get('permissions')

        return RawServerRoleUpdateEvent(
            shard=shard,
            role=PartialRole(
                state=self.state,
                id=payload['role_id'],
                server_id=payload['id'],
                name=data.get('name', UNDEFINED),
                permissions=UNDEFINED if permissions is None else self.parse_permission_override_field(permissions),
                color=None if 'Colour' in clear else data.get('colour', UNDEFINED),
                hoist=data.get('hoist', UNDEFINED),
                rank=data.get('rank', UNDEFINED),
            ),
            old_role=None,
            new_role=None,
            server=None,
        )

    def parse_server_update_event(self, shard: Shard, payload: raw.ClientServerUpdateEvent, /) -> ServerUpdateEvent:
        """Parses a ServerUpdate event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`ServerUpdateEvent`
            The parsed server update event object.
        """
        data = payload['data']
        clear = payload['clear']

        description = data.get('description')
        categories = data.get('categories')
        system_messages = data.get('system_messages')
        icon = data.get('icon')
        banner = data.get('banner')

        return ServerUpdateEvent(
            shard=shard,
            server=PartialServer(
                state=self.state,
                id=payload['id'],
                owner_id=data.get('owner', UNDEFINED),
                name=data.get('name', UNDEFINED),
                description=None if 'Description' in clear else (UNDEFINED if description is None else description),
                channel_ids=data.get('channels', UNDEFINED),
                categories=(
                    []
                    if 'Categories' in clear
                    else (UNDEFINED if categories is None else list(map(self.parse_category, categories)))
                ),
                system_messages=(
                    None
                    if 'SystemMessages' in clear
                    else (UNDEFINED if system_messages is None else self.parse_system_message_channels(system_messages))
                ),
                raw_default_permissions=data.get('default_permissions', UNDEFINED),
                internal_icon=None if 'Icon' in clear else (UNDEFINED if icon is None else self.parse_asset(icon)),
                internal_banner=None
                if 'banner' in clear
                else (UNDEFINED if banner is None else self.parse_asset(banner)),
                raw_flags=data.get('flags', UNDEFINED),
                discoverable=data.get('discoverable', UNDEFINED),
                analytics=data.get('analytics', UNDEFINED),
            ),
            before=None,  # filled on dispatch
            after=None,  # filled on dispatch
        )

    def parse_session(self, payload: raw.a.Session, /) -> Session:
        """Parses a session object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The session payload to parse.

        Returns
        -------
        :class:`Session`
            The parsed session object.
        """
        subscription = payload.get('subscription')

        return Session(
            state=self.state,
            id=payload['_id'],
            name=payload['name'],
            user_id=payload['user_id'],
            token=payload['token'],
            subscription=None if subscription is None else self.parse_webpush_subscription(subscription),
        )

    def parse_soundcloud_embed_special(self, _: raw.SoundcloudSpecial, /) -> SoundcloudEmbedSpecial:
        """Parses a Soundcloud embed special content object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The Soundcloud embed special content payload to parse.

        Returns
        -------
        :class:`SoundcloudEmbedSpecial`
            The parsed Soundcloud embed special content object.
        """
        return _SOUNDCLOUD_EMBED_SPECIAL

    def parse_spotify_embed_special(self, payload: raw.SpotifySpecial, /) -> SpotifyEmbedSpecial:
        """Parses a Spotify embed special content object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The Spotify embed special content payload to parse.

        Returns
        -------
        :class:`SpotifyEmbedSpecial`
            The parsed Spotify embed special content object.
        """
        return SpotifyEmbedSpecial(
            content_type=payload['content_type'],
            id=payload['id'],
        )

    def parse_streamable_embed_special(self, payload: raw.StreamableSpecial, /) -> StreamableEmbedSpecial:
        """Parses a Streamable embed special content object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The Streamable embed special content payload to parse.

        Returns
        -------
        :class:`StreamableEmbedSpecial`
            The parsed Streamable embed special content object.
        """
        return StreamableEmbedSpecial(id=payload['id'])

    def parse_system_message_channels(self, payload: raw.SystemMessageChannels, /) -> SystemMessageChannels:
        """Parses a system message channels object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The system message channels payload to parse.

        Returns
        -------
        :class:`SystemMessageChannels`
            The parsed system message channels object.
        """

        return SystemMessageChannels(
            user_joined=payload.get('user_joined'),
            user_left=payload.get('user_left'),
            user_kicked=payload.get('user_kicked'),
            user_banned=payload.get('user_banned'),
        )

    def parse_text_channel(self, payload: raw.TextChannel, /) -> TextChannel:
        """Parses a text channel object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The text channel payload to parse.

        Returns
        -------
        :class:`TextChannel`
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

        return TextChannel(
            state=self.state,
            id=payload['_id'],
            server_id=payload['server'],
            name=payload['name'],
            description=payload.get('description'),
            internal_icon=None if icon is None else self.parse_asset(icon),
            last_message_id=last_message_id,
            default_permissions=(
                None if default_permissions is None else self.parse_permission_override_field(default_permissions)
            ),
            role_permissions={k: self.parse_permission_override_field(v) for k, v in role_permissions.items()},
            nsfw=payload.get('nsfw', False),
            voice=None if voice is None else self.parse_voice_information(voice),
        )

    def parse_text_embed(self, payload: raw.TextEmbed, /) -> StatelessTextEmbed:
        """Parses a text embed object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The text embed payload to parse.

        Returns
        -------
        :class:`TextEmbed`
            The parsed text embed object.
        """
        media = payload.get('media')

        return StatelessTextEmbed(
            icon_url=payload.get('icon_url'),
            url=payload.get('url'),
            title=payload.get('title'),
            description=payload.get('description'),
            internal_media=None if media is None else self.parse_asset(media),
            color=payload.get('colour'),
        )

    def parse_twitch_embed_special(self, payload: raw.TwitchSpecial, /) -> TwitchEmbedSpecial:
        """Parses a Twitch embed special content object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The Twitch embed special content payload to parse.

        Returns
        -------
        :class:`TwitchEmbedSpecial`
            The parsed Twitch embed special content object.
        """
        return TwitchEmbedSpecial(
            content_type=TwitchContentType(payload['content_type']),
            id=payload['id'],
        )

    def parse_unknown_public_invite(self, payload: dict[str, typing.Any], /) -> UnknownPublicInvite:
        """Parses a unknown public invite object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The unknown public invite payload to parse.

        Returns
        -------
        :class:`UnknownPublicInvite`
            The parsed unknown public invite object.
        """
        return UnknownPublicInvite(state=self.state, code=payload['code'], payload=payload)

    def parse_user(self, payload: raw.User, /) -> typing.Union[User, OwnUser]:
        """Parses a user object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The user payload to parse.

        Returns
        -------
        Union[:class:`User`, :class:`OwnUser`]
            The parsed user object.
        """

        if payload['relationship'] == 'User':
            return self.parse_own_user(payload)

        avatar = payload.get('avatar')
        # profile = payload.get('profile')
        status = payload.get('status')

        bot = payload.get('bot')

        return User(
            state=self.state,
            id=payload['_id'],
            name=payload['username'],
            discriminator=payload['discriminator'],
            display_name=payload.get('display_name'),
            internal_avatar=None if avatar is None else self.parse_asset(avatar),
            raw_badges=payload.get('badges', 0),
            status=None if status is None else self.parse_user_status(status),
            # internal_profile=None if profile is None else self.parse_user_profile(profile),
            raw_flags=payload.get('flags', 0),
            privileged=payload.get('privileged', False),
            bot=None if bot is None else self.parse_bot_user_metadata(bot),
            relationship=RelationshipStatus(payload['relationship']),
            online=payload['online'],
        )

    def parse_user_platform_wipe_event(
        self, shard: Shard, payload: raw.ClientUserPlatformWipeEvent, /
    ) -> UserPlatformWipeEvent:
        """Parses a UserPlatformWipe event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`UserPlatformWipeEvent`
            The parsed user platform wipe event object.
        """

        return UserPlatformWipeEvent(
            shard=shard,
            user_id=payload['user_id'],
            raw_flags=payload['flags'],
            before=None,
            after=None,
        )

    def parse_user_profile(self, payload: raw.UserProfile, /) -> StatelessUserProfile:
        """Parses a user profile object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The user profile payload to parse.

        Returns
        -------
        :class:`UserProfile`
            The parsed user profile object.
        """
        background = payload.get('background')

        return StatelessUserProfile(
            content=payload.get('content'),
            internal_background=None if background is None else self.parse_asset(background),
        )

    def parse_user_relationship_event(
        self, shard: Shard, payload: raw.ClientUserRelationshipEvent, /
    ) -> UserRelationshipUpdateEvent:
        """Parses a UserRelationship event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`UserRelationshipUpdateEvent`
            The parsed user relationship event object.
        """
        return UserRelationshipUpdateEvent(
            shard=shard,
            current_user_id=payload['id'],
            old_user=None,
            new_user=self.parse_user(payload['user']),
            before=None,
        )

    def parse_user_reported_content(self, payload: raw.UserReportedContent, /) -> UserReportedContent:
        """Parses a user reported content object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The user reported content payload to parse.

        Returns
        -------
        :class:`UserReportedContent`
            The parsed user reported content object.
        """

        return UserReportedContent(
            target_id=payload['id'],
            reason=UserReportReason(payload['report_reason']),
            message_id=payload.get('message_id'),
        )

    def parse_user_settings(self, payload: raw.UserSettings, partial: bool, /) -> UserSettings:
        """Parses a user settings object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The user settings payload to parse.
        partial: :class:`bool`
            Whether the user settings are partial.

        Returns
        -------
        :class:`UserSettings`
            The parsed user settings object.
        """
        return UserSettings(
            data={k: (s1, s2) for (k, (s1, s2)) in payload.items()},
            state=self.state,
            mocked=False,
            partial=partial,
        )

    def parse_user_settings_update_event(
        self, shard: Shard, payload: raw.ClientUserSettingsUpdateEvent, /
    ) -> UserSettingsUpdateEvent:
        """Parses a UserSettingsUpdate event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`UserSettingsUpdateEvent`
            The parsed user settings update event object.
        """
        partial = self.parse_user_settings(payload['update'], True)

        before = shard.state.settings

        if not before.mocked:
            before = copy(before)
            after = copy(before)
            after.locally_update(partial)
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
        """Parses a user status object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The user status payload to parse.

        Returns
        -------
        :class:`UserStatus`
            The parsed user status object.
        """
        presence = payload.get('presence')

        return UserStatus(
            text=payload.get('text'),
            presence=None if presence is None else Presence(presence),
        )

    def parse_user_status_edit(self, payload: raw.UserStatus, clear: list[raw.FieldsUser], /) -> UserStatusEdit:
        """Parses a user status edit object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The user status payload to parse.
        clear: List[raw.FieldsUser]
            The fields that were cleared.

        Returns
        -------
        :class:`UserStatusEdit`
            The parsed user status edit object.
        """
        presence = payload.get('presence')

        return UserStatusEdit(
            text=None if 'StatusText' in clear else payload.get('text', UNDEFINED),
            presence=None if 'StatusPresence' in clear else (UNDEFINED if presence is None else Presence(presence)),
        )

    def parse_user_update_event(self, shard: Shard, payload: raw.ClientUserUpdateEvent, /) -> UserUpdateEvent:
        """Parses a UserUpdate event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`UserUpdateEvent`
            The parsed user update event object.
        """
        user_id = payload['id']
        data = payload['data']
        clear = payload['clear']

        avatar = data.get('avatar')
        status = data.get('status')
        bot = data.get('bot')

        return UserUpdateEvent(
            shard=shard,
            user=PartialUser(
                state=self.state,
                id=user_id,
                name=data.get('username', UNDEFINED),
                discriminator=data.get('discriminator', UNDEFINED),
                display_name=None if 'DisplayName' in clear else data.get('display_name', UNDEFINED),
                internal_avatar=None
                if 'Avatar' in clear
                else (UNDEFINED if avatar is None else self.parse_asset(avatar)),
                raw_badges=data.get('badges', UNDEFINED),
                status=UNDEFINED if status is None else self.parse_user_status_edit(status, clear),
                # internal_profile=(
                #     self.parse_partial_user_profile(profile, clear) if profile is not None else UNDEFINED
                # ),
                raw_flags=data.get('flags', UNDEFINED),
                bot=UNDEFINED if bot is None else self.parse_bot_user_metadata(bot),
                online=data.get('online', UNDEFINED),
            ),
            before=None,  # filled on dispatch
            after=None,  # filled on dispatch
        )

    def parse_user_voice_state(self, payload: raw.UserVoiceState, /) -> UserVoiceState:
        """Parses a user voice state object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The user voice state payload to parse.

        Returns
        -------
        :class:`UserVoiceState`
            The parsed user voice state object.
        """
        return UserVoiceState(
            user_id=payload['id'],
            can_publish=payload['can_publish'],
            can_receive=payload['can_receive'],
            screensharing=payload['screensharing'],
            camera=payload['camera'],
        )

    def parse_user_voice_state_update_event(
        self, shard: Shard, payload: raw.ClientUserVoiceStateUpdateEvent, /
    ) -> UserVoiceStateUpdateEvent:
        """Parses a user voice state update event.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`UserVoiceStateUpdateEvent`
            The parsed user voice state update object.
        """

        data = payload['data']

        return UserVoiceStateUpdateEvent(
            shard=shard,
            channel_id=payload['channel_id'],
            container=None,
            state=PartialUserVoiceState(
                user_id=payload['id'],
                can_publish=data.get('can_publish', UNDEFINED),
                can_receive=data.get('can_receive', UNDEFINED),
                screensharing=data.get('screensharing', UNDEFINED),
                camera=data.get('camera', UNDEFINED),
            ),
            before=None,
            after=None,
        )

    def parse_video_embed(self, payload: raw.Video, /) -> VideoEmbed:
        """Parses a video embed object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The video embed payload to parse.

        Returns
        -------
        :class:`VideoEmbed`
            The parsed video embed object.
        """
        return VideoEmbed(
            url=payload['url'],
            width=payload['width'],
            height=payload['height'],
        )

    def parse_voice_channel(self, payload: raw.VoiceChannel, /) -> VoiceChannel:
        """Parses a voice channel object.

        .. deprecated:: 0.7.0
            The method was deprecated in favour of :meth:`.parse_text_channel` and
            using :attr:`TextChannel.voice` instead.

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
            internal_icon=None if icon is None else self.parse_asset(icon),
            default_permissions=(
                None if default_permissions is None else self.parse_permission_override_field(default_permissions)
            ),
            role_permissions={k: self.parse_permission_override_field(v) for k, v in role_permissions.items()},
            nsfw=payload.get('nsfw', False),
        )

    def parse_voice_channel_join_event(
        self, shard: Shard, payload: raw.ClientVoiceChannelJoinEvent, /
    ) -> VoiceChannelJoinEvent:
        """Parses a voice channel join event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`VoiceChannelJoinEvent`
            The parsed voice channel join event object.
        """

        return VoiceChannelJoinEvent(
            shard=shard,
            channel_id=payload['id'],
            state=self.parse_user_voice_state(payload['state']),
        )

    def parse_voice_channel_leave_event(
        self, shard: Shard, payload: raw.ClientVoiceChannelLeaveEvent, /
    ) -> VoiceChannelLeaveEvent:
        """Parses a voice channel leave event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`VoiceChannelLeaveEvent`
            The parsed voice channel leave event object.
        """

        return VoiceChannelLeaveEvent(
            shard=shard,
            channel_id=payload['id'],
            user_id=payload['user'],
            container=None,
            state=None,
        )

    def parse_voice_channel_move_event(
        self, shard: Shard, payload: raw.ClientVoiceChannelMoveEvent, /
    ) -> VoiceChannelMoveEvent:
        """Parses a voice channel move event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`VoiceChannelMoveEvent`
            The parsed voice channel move event object.
        """

        return VoiceChannelMoveEvent(
            shard=shard,
            user_id=payload['user'],
            from_=payload['from'],
            to=payload['to'],
            old_container=None,
            new_container=None,
        )

    def parse_voice_information(self, payload: raw.VoiceInformation, /) -> ChannelVoiceMetadata:
        """Parses a channel voice metadata object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The channel voice metadata payload to parse.

        Returns
        -------
        :class:`ChannelVoiceMetadata`
            The parsed channel voice metadata object.
        """
        return ChannelVoiceMetadata(max_users=payload.get('max_users') or 0)

    def parse_webhook(self, payload: raw.Webhook, /) -> Webhook:
        """Parses a webhook object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The webhook payload to parse.

        Returns
        -------
        :class:`Webhook`
            The parsed webhook object.
        """
        avatar = payload.get('avatar')

        return Webhook(
            state=self.state,
            id=payload['id'],
            name=payload['name'],
            internal_avatar=None if avatar is None else self.parse_asset(avatar),
            creator_id=payload.get('creator_id', ''),
            channel_id=payload['channel_id'],
            raw_permissions=payload['permissions'],
            token=payload.get('token'),
        )

    def parse_webhook_create_event(self, shard: Shard, payload: raw.ClientWebhookCreateEvent, /) -> WebhookCreateEvent:
        """Parses a WebhookCreate event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`WebhookCreateEvent`
            The parsed webhook create event object.
        """
        return WebhookCreateEvent(
            shard=shard,
            webhook=self.parse_webhook(payload),
        )

    def parse_webhook_update_event(self, shard: Shard, payload: raw.ClientWebhookUpdateEvent, /) -> WebhookUpdateEvent:
        """Parses a WebhookUpdate event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`WebhookUpdateEvent`
            The parsed webhook update event object.
        """
        data = payload['data']
        remove = payload['remove']

        avatar = data.get('avatar')

        return WebhookUpdateEvent(
            shard=shard,
            webhook=PartialWebhook(
                state=self.state,
                id=payload['id'],
                name=data.get('name', UNDEFINED),
                internal_avatar=None
                if 'Avatar' in remove
                else (UNDEFINED if avatar is None else self.parse_asset(avatar)),
                raw_permissions=data.get('permissions', UNDEFINED),
            ),
        )

    def parse_webhook_delete_event(self, shard: Shard, payload: raw.ClientWebhookDeleteEvent, /) -> WebhookDeleteEvent:
        """Parses a WebhookDelete event.

        Parameters
        ----------
        shard: :class:`Shard`
            The shard the event arrived on.
        payload: Dict[:class:`str`, Any]
            The event payload to parse.

        Returns
        -------
        :class:`WebhookDeleteEvent`
            The parsed webhook delete event object.
        """
        return WebhookDeleteEvent(
            shard=shard,
            webhook=None,
            webhook_id=payload['id'],
        )

    def parse_webpush_subscription(self, payload: raw.a.WebPushSubscription, /) -> WebPushSubscription:
        """Parses a WebPush subscription object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The WebPush subscription payload to parse.

        Returns
        -------
        :class:`WebPushSubscription`
            The parsed WebPush subscription object.
        """
        return WebPushSubscription(
            endpoint=payload['endpoint'],
            p256dh=payload['p256dh'],
            auth=payload['auth'],
        )

    def parse_website_embed(self, payload: raw.WebsiteEmbed, /) -> WebsiteEmbed:
        """Parses a website embed object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The website embed payload to parse.

        Returns
        -------
        :class:`WebsiteEmbed`
            The parsed website embed object.
        """
        special = payload.get('special')
        image = payload.get('image')
        video = payload.get('video')

        return WebsiteEmbed(
            url=payload.get('url'),
            original_url=payload.get('original_url'),
            special=None if special is None else self.parse_embed_special(special),
            title=payload.get('title'),
            description=payload.get('description'),
            image=None if image is None else self.parse_image_embed(image),
            video=None if video is None else self.parse_video_embed(video),
            site_name=payload.get('site_name'),
            icon_url=payload.get('icon_url'),
            color=payload.get('colour'),
        )

    def parse_youtube_embed_special(self, payload: raw.YouTubeSpecial) -> YouTubeEmbedSpecial:
        """Parses a YouTube embed special content object.

        Parameters
        ----------
        payload: Dict[:class:`str`, Any]
            The YouTube embed special content payload to parse.

        Returns
        -------
        :class:`YouTubeEmbedSpecial`
            The parsed YouTube embed special content object.
        """
        return YouTubeEmbedSpecial(id=payload['id'], timestamp=payload.get('timestamp'))


__all__ = ('Parser',)
