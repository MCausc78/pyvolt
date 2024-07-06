from __future__ import annotations

from datetime import datetime
import logging
import typing as t


from . import (
    auth,
    bot as bots,
    cdn,
    channel as channels,
    core,
    discovery,
    embed as embeds,
    emoji as emojis,
    events,
    invite as invites,
    message as messages,
    permissions as permissions_,
    server as servers,
    user_settings,
    user as users,
    webhook as webhooks,
)
from .read_state import ReadState


if t.TYPE_CHECKING:
    from . import raw
    from .shard import Shard
    from .state import State

_L = logging.getLogger(__name__)


_EMPTY_LIST: list[t.Any] = []
_EMPTY_DICT: dict[t.Any, t.Any] = {}


class Parser:
    def __init__(self, state: State) -> None:
        self.state = state

    # basic start

    def parse_id(self, d: t.Any) -> core.ULID:
        return core.ULID(d)

    def parse_asset_metadata(self, d: raw.Metadata) -> cdn.AssetMetadata:
        return cdn.AssetMetadata(
            type=cdn.AssetMetadataType(d["type"]),
            width=d.get("width"),
            height=d.get("height"),
        )

    def parse_asset(self, d: raw.File) -> cdn.StatelessAsset:
        deleted = d.get("deleted")
        reported = d.get("reported")

        return cdn.StatelessAsset(
            id=self.parse_id(d["_id"]),
            filename=d["filename"],
            metadata=self.parse_asset_metadata(d["metadata"]),
            content_type=d["content_type"],
            size=d["size"],
            deleted=deleted or False,
            reported=reported or False,
            message_id=self.parse_id(d["message_id"]) if "message_id" in d else None,
            user_id=self.parse_id(d["user_id"]) if "user_id" in d else None,
            server_id=self.parse_id(d["server_id"]) if "server_id" in d else None,
            object_id=self.parse_id(d["object_id"]) if "object_id" in d else None,
        )

    def parse_auth_event(
        self, shard: Shard, d: raw.ClientAuthEvent
    ) -> events.AuthifierEvent:
        if d["event_type"] == "CreateSession":
            return events.SessionCreateEvent(
                shard=shard,
                session=self.parse_session(d["session"]),
            )
        elif d["event_type"] == "DeleteSession":
            return events.SessionDeleteEvent(
                shard=shard,
                user_id=self.parse_id(d["user_id"]),
                session_id=self.parse_id(d["session_id"]),
            )
        elif d["event_type"] == "DeleteAllSessions":
            exclude_session_id = d.get("exclude_session_id")
            return events.SessionDeleteAllEvent(
                shard=shard,
                user_id=self.parse_id(d["user_id"]),
                exclude_session_id=(
                    self.parse_id(exclude_session_id) if exclude_session_id else None
                ),
            )
        else:
            raise NotImplementedError("Unimplemented auth event type", d)

    # basic end, internals start

    def _parse_group_channel(self, d: raw.GroupChannel) -> channels.GroupChannel:
        return self.parse_group_channel(
            d,
            (
                True,
                [self.parse_id(recipient_id) for recipient_id in d["recipients"]],
            ),
        )

    # internals end

    def parse_ban(
        self, d: raw.ServerBan, users: dict[core.ULID, users.DisplayUser]
    ) -> servers.Ban:
        id = d["_id"]
        user_id = self.parse_id(id["user"])

        return servers.Ban(
            server_id=self.parse_id(id["server"]),
            user_id=user_id,
            reason=d["reason"],
            user=users.get(user_id),
        )

    def parse_bandcamp_embed_special(
        self, d: raw.BandcampSpecial
    ) -> embeds.BandcampEmbedSpecial:
        return embeds.BandcampEmbedSpecial(
            content_type=embeds.BandcampContentType(d["content_type"]),
            id=d["id"],
        )

    def parse_bans(self, d: raw.BanListResult) -> list[servers.Ban]:
        banned_users = {
            bu.id: bu for bu in (self.parse_display_user(e) for e in d["users"])
        }
        return [self.parse_ban(e, banned_users) for e in d["bans"]]

    def _parse_bot(self, d: raw.Bot, user: users.User) -> bots.Bot:
        return bots.Bot(
            state=self.state,
            id=self.parse_id(d["_id"]),
            owner_id=self.parse_id(d["owner"]),
            token=d["token"],
            public=d["public"],
            analytics=d.get("analytics", False),
            discoverable=d.get("discoverable", False),
            interactions_url=d.get("interactions_url"),
            terms_of_service_url=d.get("terms_of_service_url"),
            privacy_policy_url=d.get("privacy_policy_url"),
            flags=bots.BotFlags(d.get("flags") or 0),
            user=user,
        )

    def parse_bot(self, d: raw.Bot, user: raw.User) -> bots.Bot:
        return self._parse_bot(d, self.parse_user(user))

    def parse_bot_user_info(self, d: raw.BotInformation) -> users.BotUserInfo:
        return users.BotUserInfo(owner_id=self.parse_id(d["owner"]))

    def parse_bots(self, d: raw.OwnedBotsResponse) -> list[bots.Bot]:
        bots = d["bots"]
        users = d["users"]

        if len(bots) != len(users):
            raise RuntimeError(f"Expected {len(bots)} users but got {len(users)}")
        return [self.parse_bot(e, users[i]) for i, e in enumerate(bots)]

    def parse_bulk_message_delete_event(
        self, shard: Shard, d: raw.ClientBulkMessageDeleteEvent
    ) -> events.BulkMessageDeleteEvent:
        return events.BulkMessageDeleteEvent(
            shard=shard,
            channel_id=self.parse_id(d["channel"]),
            message_ids=[self.parse_id(m) for m in d["ids"]],
        )

    def parse_category(self, d: raw.Category) -> servers.Category:
        return servers.Category(
            id=self.parse_id(d["id"]),
            title=d["title"],
            channels=d["channels"],  # type: ignore
        )

    def parse_channel_ack_event(
        self, shard: Shard, d: raw.ClientChannelAckEvent
    ) -> events.MessageAckEvent:
        return events.MessageAckEvent(
            shard=shard,
            channel_id=self.parse_id(d["id"]),
            message_id=self.parse_id(d["message_id"]),
            user_id=self.parse_id(d["user"]),
        )

    def parse_channel_create_event(
        self, shard: Shard, d: raw.ClientChannelCreateEvent
    ) -> events.ChannelCreateEvent:
        channel = self.parse_channel(d)
        if isinstance(
            channel,
            (channels.SavedMessagesChannel, channels.DMChannel, channels.GroupChannel),
        ):
            return events.PrivateChannelCreateEvent(shard=shard, channel=channel)
        else:
            return events.ServerChannelCreateEvent(shard=shard, channel=channel)

    def parse_channel_delete_event(
        self, shard: Shard, d: raw.ClientChannelDeleteEvent
    ) -> events.ChannelDeleteEvent:
        return events.ChannelDeleteEvent(
            shard=shard,
            channel_id=self.parse_id(d["id"]),
            channel=None,
        )

    def parse_channel_group_join_event(
        self, shard: Shard, d: raw.ClientChannelGroupJoinEvent
    ) -> events.GroupRecipientAddEvent:
        return events.GroupRecipientAddEvent(
            shard=shard,
            channel_id=self.parse_id(d["id"]),
            user_id=self.parse_id(d["user"]),
            group=None,
        )

    def parse_channel_group_leave_event(
        self, shard: Shard, d: raw.ClientChannelGroupLeaveEvent
    ) -> events.GroupRecipientRemoveEvent:
        return events.GroupRecipientRemoveEvent(
            shard=shard,
            channel_id=self.parse_id(d["id"]),
            user_id=self.parse_id(d["user"]),
            group=None,
        )

    def parse_channel_start_typing_event(
        self, shard: Shard, d: raw.ClientChannelStartTypingEvent
    ) -> events.ChannelStartTypingEvent:
        return events.ChannelStartTypingEvent(
            shard=shard,
            channel_id=self.parse_id(d["id"]),
            user_id=self.parse_id(d["user"]),
        )

    def parse_channel_stop_typing_event(
        self, shard: Shard, d: raw.ClientChannelStopTypingEvent
    ) -> events.ChannelStopTypingEvent:
        return events.ChannelStopTypingEvent(
            shard=shard,
            channel_id=self.parse_id(d["id"]),
            user_id=self.parse_id(d["user"]),
        )

    def parse_channel_update_event(
        self, shard: Shard, d: raw.ClientChannelUpdateEvent
    ) -> events.ChannelUpdateEvent:
        clear = d["clear"]
        data = d["data"]

        owner = data.get("owner")
        icon = data.get("icon")
        permissions = data.get("permissions")
        role_permissions = data.get("role_permissions")
        default_permissions = data.get("default_permissions")
        last_message_id = data.get("last_message_id")

        return events.ChannelUpdateEvent(
            shard=shard,
            channel=channels.PartialChannel(
                state=self.state,
                id=self.parse_id(d["id"]),
                name=data.get("name", core.UNDEFINED),
                owner_id=self.parse_id(owner) if owner else core.UNDEFINED,
                description=(
                    None
                    if "Description" in clear
                    else data.get("description", core.UNDEFINED)
                ),
                internal_icon=(
                    None
                    if "Icon" in clear
                    else self.parse_asset(icon) if icon else core.UNDEFINED
                ),
                nsfw=data.get("nsfw", core.UNDEFINED),
                active=data.get("active", core.UNDEFINED),
                permissions=(
                    permissions_.Permissions(permissions)
                    if permissions is not None
                    else core.UNDEFINED
                ),
                role_permissions=(
                    {
                        self.parse_id(k): self.parse_permission_override_field(v)
                        for k, v in role_permissions.items()
                    }
                    if role_permissions is not None
                    else core.UNDEFINED
                ),
                default_permissions=(
                    self.parse_permission_override_field(default_permissions)
                    if default_permissions is not None
                    else core.UNDEFINED
                ),
                last_message_id=(
                    self.parse_id(last_message_id)
                    if last_message_id
                    else core.UNDEFINED
                ),
            ),
            before=None,
            after=None,
        )

    def parse_channel(self, d: raw.Channel) -> channels.Channel:
        return {
            "SavedMessages": self.parse_saved_messages_channel,
            "DirectMessage": self.parse_direct_message_channel,
            "Group": self._parse_group_channel,
            "TextChannel": self.parse_text_channel,
            "VoiceChannel": self.parse_voice_channel,
        }[d["channel_type"]](d)

    def parse_detached_emoji(self, d: raw.DetachedEmoji) -> emojis.DetachedEmoji:
        animated = d.get("animated")
        nsfw = d.get("nsfw")

        return emojis.DetachedEmoji(
            state=self.state,
            id=self.parse_id(d["_id"]),
            creator_id=self.parse_id(d["creator_id"]),
            name=d["name"],
            animated=animated or False,
            nsfw=nsfw or False,
        )

    def parse_disabled_response_login(
        self, d: raw.a.DisabledResponseLogin
    ) -> auth.AccountDisabled:
        return auth.AccountDisabled(user_id=core.resolve_ulid(d["user_id"]))

    def parse_direct_message_channel(
        self, d: raw.DirectMessageChannel
    ) -> channels.DMChannel:
        recipient_ids = d["recipients"]
        last_message_id = d.get("last_message_id")

        return channels.DMChannel(
            state=self.state,
            id=self.parse_id(d["_id"]),
            active=d["active"],
            recipient_ids=(
                self.parse_id(recipient_ids[0]),
                self.parse_id(recipient_ids[1]),
            ),
            last_message_id=self.parse_id(last_message_id) if last_message_id else None,
        )

    # Discovery
    def parse_discovery_bot(self, d: raw.DiscoveryBot) -> discovery.DiscoveryBot:
        avatar = d.get("avatar")

        return discovery.DiscoveryBot(
            state=self.state,
            id=self.parse_id(d["_id"]),
            name=d["username"],
            internal_avatar=self.parse_asset(avatar) if avatar else None,
            internal_profile=self.parse_user_profile(d["profile"]),
            tags=d["tags"],
            server_count=d["servers"],
            usage=discovery.BotUsage(d["usage"]),
        )

    def parse_discovery_bot_search_result(
        self, d: raw.DiscoveryBotSearchResult
    ) -> discovery.BotSearchResult:
        return discovery.BotSearchResult(
            query=d["query"],
            count=d["count"],
            bots=[self.parse_discovery_bot(s) for s in d["bots"]],
            related_tags=d["relatedTags"],
        )

    def parse_discovery_bots_page(
        self, d: raw.DiscoveryBotsPage
    ) -> discovery.DiscoveryBotsPage:
        return discovery.DiscoveryBotsPage(
            bots=[self.parse_discovery_bot(b) for b in d["bots"]],
            popular_tags=d["popularTags"],
        )

    def parse_discovery_server(
        self, d: raw.DiscoveryServer
    ) -> discovery.DiscoveryServer:
        icon = d.get("icon")
        banner = d.get("banner")

        return discovery.DiscoveryServer(
            state=self.state,
            id=self.parse_id(d["_id"]),
            name=d["name"],
            description=d.get("description"),
            internal_icon=self.parse_asset(icon) if icon else None,
            internal_banner=self.parse_asset(banner) if banner else None,
            flags=servers.ServerFlags(d.get("flags") or 0),
            tags=d["tags"],
            member_count=d["members"],
            activity=discovery.ServerActivity(d["activity"]),
        )

    def parse_discovery_servers_page(
        self, d: raw.DiscoveryServersPage
    ) -> discovery.DiscoveryServersPage:
        return discovery.DiscoveryServersPage(
            servers=[self.parse_discovery_server(s) for s in d["servers"]],
            popular_tags=d["popularTags"],
        )

    def parse_discovery_server_search_result(
        self, d: raw.DiscoveryServerSearchResult
    ) -> discovery.ServerSearchResult:
        return discovery.ServerSearchResult(
            query=d["query"],
            count=d["count"],
            servers=[self.parse_discovery_server(s) for s in d["servers"]],
            related_tags=d["relatedTags"],
        )

    def parse_discovery_theme(self, d: raw.DiscoveryTheme) -> discovery.DiscoveryTheme:
        return discovery.DiscoveryTheme(
            state=self.state,
            name=d["name"],
            description=d["description"],
            creator=d["creator"],
            slug=d["slug"],
            tags=d["tags"],
            variables=d["variables"],
            version=d["version"],
            css=d.get("css"),
        )

    def parse_discovery_theme_search_result(
        self, d: raw.DiscoveryThemeSearchResult
    ) -> discovery.ThemeSearchResult:
        return discovery.ThemeSearchResult(
            query=d["query"],
            count=d["count"],
            themes=[self.parse_discovery_theme(s) for s in d["themes"]],
            related_tags=d["relatedTags"],
        )

    def parse_discovery_themes_page(
        self, d: raw.DiscoveryThemesPage
    ) -> discovery.DiscoveryThemesPage:
        return discovery.DiscoveryThemesPage(
            themes=[self.parse_discovery_theme(b) for b in d["themes"]],
            popular_tags=d["popularTags"],
        )

    def parse_display_user(self, d: raw.BannedUser) -> users.DisplayUser:
        avatar = d.get("avatar")

        return users.DisplayUser(
            state=self.state,
            id=self.parse_id(d["_id"]),
            name=d["username"],
            discriminator=d["discriminator"],
            internal_avatar=self.parse_asset(avatar) if avatar else None,
        )

    def parse_embed(self, d: raw.Embed) -> embeds.Embed:
        return {
            "Website": self.parse_website_embed,
            "Image": self.parse_image_embed,
            "Video": self.parse_video_embed,
            "Text": self.parse_text_embed,
            "None": self.parse_none_embed,
        }[d["type"]](d)

    def parse_embed_special(self, d: raw.Special) -> embeds.EmbedSpecial:
        return {
            "None": self.parse_none_embed_special,
            "GIF": self.parse_gif_embed_special,
            "YouTube": self.parse_youtube_embed_special,
            "Lightspeed": self.parse_lightspeed_embed_special,
            "Twitch": self.parse_twitch_embed_special,
            "Spotify": self.parse_spotify_embed_special,
            "Soundcloud": self.parse_soundcloud_embed_special,
            "Bandcamp": self.parse_bandcamp_embed_special,
            "Streamable": self.parse_streamable_embed_special,
        }[d["type"]](d)

    def parse_emoji(self, d: raw.Emoji) -> emojis.Emoji:
        return {
            "Server": self.parse_server_emoji,
            "Detached": self.parse_detached_emoji,
        }[d["parent"]["type"]](d)

    def parse_emoji_create_event(
        self, shard: Shard, d: raw.ClientEmojiCreateEvent
    ) -> events.ServerEmojiCreateEvent:
        return events.ServerEmojiCreateEvent(
            shard=shard,
            emoji=self.parse_server_emoji(d),
        )

    def parse_emoji_delete_event(
        self, shard: Shard, d: raw.ClientEmojiDeleteEvent
    ) -> events.ServerEmojiDeleteEvent:
        return events.ServerEmojiDeleteEvent(
            shard=shard,
            emoji=None,
            server_id=None,
            emoji_id=self.parse_id(d["id"]),
        )

    def parse_gif_embed_special(self, _: raw.GIFSpecial) -> embeds.GifEmbedSpecial:
        return embeds._GIF_EMBED_SPECIAL

    def parse_group_channel(
        self,
        d: raw.GroupChannel,
        recipients: (
            tuple[t.Literal[True], list[core.ULID]]
            | tuple[t.Literal[False], list[users.User]]
        ),
    ) -> channels.GroupChannel:
        icon = d.get("icon")
        last_message_id = d.get("last_message_id")
        permissions = d.get("permissions")
        nsfw = d.get("nsfw")

        return channels.GroupChannel(
            state=self.state,
            id=self.parse_id(d["_id"]),
            name=d["name"],
            owner_id=self.parse_id(d["owner"]),
            description=d.get("description"),
            internal_recipients=recipients,
            internal_icon=self.parse_asset(icon) if icon else None,
            last_message_id=self.parse_id(last_message_id) if last_message_id else None,
            permissions=(
                None if permissions is None else permissions_.Permissions(permissions)
            ),
            nsfw=nsfw or False,
        )

    def parse_group_invite(self, d: raw.GroupInvite) -> invites.GroupInvite:
        return invites.GroupInvite(
            state=self.state,
            code=d["_id"],
            creator_id=self.parse_id(d["creator"]),
            channel_id=self.parse_id(d["channel"]),
        )

    def parse_group_public_invite(
        self, d: raw.GroupInviteResponse
    ) -> invites.GroupPublicInvite:
        user_avatar = d.get("user_avatar")

        return invites.GroupPublicInvite(
            state=self.state,
            code=d["code"],
            channel_id=self.parse_id(d["channel_id"]),
            channel_name=d["channel_name"],
            channel_description=d.get("channel_description", None),
            user_name=d["user_name"],
            internal_user_avatar=self.parse_asset(user_avatar) if user_avatar else None,
        )

    def parse_image_embed(self, d: raw.Image) -> embeds.ImageEmbed:
        return embeds.ImageEmbed(
            url=d["url"],
            width=d["width"],
            height=d["height"],
            size=embeds.ImageSize(d["size"]),
        )

    def parse_invite(self, d: raw.Invite) -> invites.Invite:
        return {
            "Server": self.parse_server_invite,
            "Group": self.parse_group_invite,
        }[
            d["type"]
        ](d)

    def parse_lightspeed_embed_special(
        self, d: raw.LightspeedSpecial
    ) -> embeds.LightspeedEmbedSpecial:
        return embeds.LightspeedEmbedSpecial(
            content_type=embeds.LightspeedContentType(d["content_type"]),
            id=d["id"],
        )

    def parse_logout_event(
        self, shard: Shard, d: raw.ClientLogoutEvent
    ) -> events.LogoutEvent:
        return events.LogoutEvent(shard=shard)

    def parse_member(
        self,
        d: raw.Member,
        *,
        user: users.User | None = None,
        users: dict[core.ULID, users.User] | None = None,
    ) -> servers.Member:
        if user and users:
            raise ValueError("Cannot specify both user and users")

        id = d["_id"]
        user_id = self.parse_id(id["user"])

        if user:
            assert user.id == user_id, "IDs do not match"

        avatar = d.get("avatar")
        timeout = d.get("timeout")

        return servers.Member(
            state=self.state,
            _user=user or (users or _EMPTY_DICT).get(user_id) or user_id,
            server_id=self.parse_id(id["server"]),
            joined_at=datetime.fromisoformat(d["joined_at"]),
            nick=d.get("nickname"),
            internal_avatar=self.parse_asset(avatar) if avatar else None,
            roles=[self.parse_id(role_id) for role_id in d.get("roles") or []],
            timeout=datetime.fromisoformat(timeout) if timeout else None,
        )

    def parse_member_list(self, d: raw.AllMemberResponse) -> servers.MemberList:
        return servers.MemberList(
            members=[self.parse_member(m) for m in d.get("members") or []],
            users=[self.parse_user(u) for u in d.get("users") or []],
        )

    def parse_members_with_users(
        self, d: raw.AllMemberResponse
    ) -> list[servers.Member]:
        users = [self.parse_user(u) for u in d.get("users") or []]

        return [self.parse_member(e, user=users[i]) for i, e in enumerate(d["members"])]

    def parse_message(
        self,
        d: raw.Message,
        *,
        members: dict[core.ULID, servers.Member] = {},
        users: dict[core.ULID, users.User] = {},
    ) -> messages.Message:
        author_id = self.parse_id(d["author"])
        webhook = d.get("webhook")
        system = d.get("system")
        edited_at = d.get("edited")
        interactions = d.get("interactions")
        masquerade = d.get("masquerade")

        member = d.get("member")
        user = d.get("user")

        if member:
            if user:
                author = self.parse_member(member, user=self.parse_user(user))
            else:
                author = self.parse_member(member)
        elif user:
            author = self.parse_user(user)
        else:
            author = members.get(author_id) or users.get(author_id) or author_id

        return messages.Message(
            state=self.state,
            id=self.parse_id(d["_id"]),
            nonce=d.get("nonce"),
            channel_id=self.parse_id(d["channel"]),
            internal_author=author,
            webhook=self.parse_message_webhook(webhook) if webhook else None,
            content=d.get("content") or "",
            system_event=self.parse_message_system_event(system) if system else None,
            internal_attachments=[
                self.parse_asset(a) for a in d.get("attachments") or []
            ],
            edited_at=datetime.fromisoformat(edited_at) if edited_at else None,
            internal_embeds=[self.parse_embed(e) for e in d.get("embeds") or []],
            mention_ids=[self.parse_id(m) for m in d.get("mentions") or []],
            replies=[self.parse_id(r) for r in d.get("replies") or []],
            reactions={
                k: tuple(self.parse_id(u) for u in v)
                for k, v in (d.get("reactions") or {}).items()
            },
            interactions=(
                self.parse_message_interactions(interactions) if interactions else None
            ),
            masquerade=(
                self.parse_message_masquerade(masquerade) if masquerade else None
            ),
            pinned=d.get("pinned") or False,
            flags=messages.MessageFlags(d.get("flags", 0)),
        )

    def parse_message_append_event(
        self, shard: Shard, d: raw.ClientMessageAppendEvent
    ) -> events.MessageAppendEvent:
        data = d["append"]
        embeds = data.get("embeds")

        return events.MessageAppendEvent(
            shard=shard,
            data=messages.MessageAppendData(
                state=self.state,
                id=self.parse_id(d["id"]),
                channel_id=self.parse_id(d["channel"]),
                internal_embeds=(
                    [self.parse_embed(e) for e in embeds]
                    if embeds is not None
                    else core.UNDEFINED
                ),
            ),
        )

    def parse_message_channel_description_changed_system_event(
        self, d: raw.ChannelDescriptionChangedSystemMessage
    ) -> messages.ChannelDescriptionChangedSystemEvent:
        return messages.ChannelDescriptionChangedSystemEvent(by=self.parse_id(d["by"]))

    def parse_message_channel_icon_changed_system_event(
        self, d: raw.ChannelIconChangedSystemMessage
    ) -> messages.ChannelIconChangedSystemEvent:
        return messages.ChannelIconChangedSystemEvent(by=self.parse_id(d["by"]))

    def parse_message_channel_renamed_system_event(
        self, d: raw.ChannelRenamedSystemMessage
    ) -> messages.ChannelRenamedSystemEvent:
        return messages.ChannelRenamedSystemEvent(
            by=self.parse_id(d["by"]),
        )

    def parse_message_channel_ownership_changed_system_event(
        self, d: raw.ChannelOwnershipChangedSystemMessage
    ) -> messages.ChannelOwnershipChangedSystemEvent:
        return messages.ChannelOwnershipChangedSystemEvent(
            from_=self.parse_id(d["from"]),
            to=self.parse_id(d["to"]),
        )

    def parse_message_delete_event(
        self, shard: Shard, d: raw.ClientMessageDeleteEvent
    ) -> events.MessageDeleteEvent:
        return events.MessageDeleteEvent(
            shard=shard,
            channel_id=self.parse_id(d["channel"]),
            message_id=self.parse_id(d["id"]),
        )

    def parse_message_event(
        self, shard: Shard, d: raw.ClientMessageEvent
    ) -> events.MessageCreateEvent:
        return events.MessageCreateEvent(shard=shard, message=self.parse_message(d))

    def parse_message_interactions(self, d: raw.Interactions) -> messages.Interactions:
        return messages.Interactions(
            reactions=d.get("reactions", []),
            restrict_reactions=d.get("restrict_reactions", False),
        )

    def parse_message_masquerade(self, d: raw.Masquerade) -> messages.Masquerade:
        return messages.Masquerade(
            name=d.get("name"), avatar=d.get("avatar"), colour=d.get("colour")
        )

    def parse_message_react_event(
        self, shard: Shard, d: raw.ClientMessageReactEvent
    ) -> events.MessageReactEvent:
        return events.MessageReactEvent(
            shard=shard,
            channel_id=self.parse_id(d["channel_id"]),
            message_id=self.parse_id(d["id"]),
            user_id=self.parse_id(d["user_id"]),
            emoji=d["emoji_id"],
        )

    def parse_message_remove_reaction_event(
        self, shard: Shard, d: raw.ClientMessageRemoveReactionEvent
    ) -> events.MessageClearReactionEvent:
        return events.MessageClearReactionEvent(
            shard=shard,
            channel_id=self.parse_id(d["channel_id"]),
            message_id=self.parse_id(d["id"]),
            emoji=d["emoji_id"],
        )

    def parse_message_system_event(self, d: raw.SystemMessage) -> messages.SystemEvent:
        return {
            "text": self.parse_message_text_system_event,
            "user_added": self.parse_message_user_added_system_event,
            "user_remove": self.parse_message_user_remove_system_event,
            "user_joined": self.parse_message_user_joined_system_event,
            "user_left": self.parse_message_user_left_system_event,
            "user_kicked": self.parse_message_user_kicked_system_event,
            "user_banned": self.parse_message_user_banned_system_event,
            "channel_renamed": self.parse_message_channel_renamed_system_event,
            "channel_description_changed": self.parse_message_channel_description_changed_system_event,
            "channel_icon_changed": self.parse_message_channel_icon_changed_system_event,
            "channel_ownership_changed": self.parse_message_channel_ownership_changed_system_event,
        }[d["type"]](d)

    def parse_message_text_system_event(
        self, d: raw.TextSystemMessage
    ) -> messages.TextSystemEvent:
        return messages.TextSystemEvent(content=d["content"])

    def parse_message_unreact_event(
        self, shard: Shard, d: raw.ClientMessageUnreactEvent
    ) -> events.MessageUnreactEvent:
        return events.MessageUnreactEvent(
            shard=shard,
            channel_id=self.parse_id(d["channel_id"]),
            message_id=self.parse_id(d["id"]),
            user_id=self.parse_id(d["user_id"]),
            emoji=d["emoji_id"],
        )

    def parse_message_update_event(
        self, shard: Shard, d: raw.ClientMessageUpdateEvent
    ) -> events.MessageUpdateEvent:
        data = d["data"]

        content = data.get("content")
        edited_at = data.get("edited")
        embeds = data.get("embeds")
        reactions = data.get("reactions")

        return events.MessageUpdateEvent(
            shard=shard,
            message=messages.PartialMessage(
                state=self.state,
                id=self.parse_id(d["id"]),
                channel_id=self.parse_id(d["channel"]),
                content=content if content is not None else core.UNDEFINED,
                edited_at=(
                    datetime.fromisoformat(edited_at) if edited_at else core.UNDEFINED
                ),
                internal_embeds=(
                    [self.parse_embed(e) for e in embeds]
                    if embeds is not None
                    else core.UNDEFINED
                ),
                reactions=(
                    {
                        k: tuple(self.parse_id(u) for u in v)
                        for k, v in reactions.items()
                    }
                    if reactions is not None
                    else core.UNDEFINED
                ),
            ),
            before=None,
            after=None,
        )

    def parse_message_user_added_system_event(
        self, d: raw.UserAddedSystemMessage
    ) -> messages.UserAddedSystemEvent:
        return messages.UserAddedSystemEvent(
            id=self.parse_id(d["id"]), by=self.parse_id(d["by"])
        )

    def parse_message_user_banned_system_event(
        self, d: raw.UserBannedSystemMessage
    ) -> messages.UserBannedSystemEvent:
        return messages.UserBannedSystemEvent(id=self.parse_id(d["id"]))

    def parse_message_user_joined_system_event(
        self, d: raw.UserJoinedSystemMessage
    ) -> messages.UserJoinedSystemEvent:
        return messages.UserJoinedSystemEvent(id=self.parse_id(d["id"]))

    def parse_message_user_kicked_system_event(
        self, d: raw.UserKickedSystemMessage
    ) -> messages.UserKickedSystemEvent:
        return messages.UserKickedSystemEvent(id=self.parse_id(d["id"]))

    def parse_message_user_left_system_event(
        self, d: raw.UserLeftSystemMessage
    ) -> messages.UserLeftSystemEvent:
        return messages.UserLeftSystemEvent(id=self.parse_id(d["id"]))

    def parse_message_user_remove_system_event(
        self, d: raw.UserRemoveSystemMessage
    ) -> messages.UserRemovedSystemEvent:
        return messages.UserRemovedSystemEvent(
            id=self.parse_id(d["id"]), by=self.parse_id(d["by"])
        )

    def parse_message_webhook(self, d: raw.MessageWebhook) -> messages.MessageWebhook:
        return messages.MessageWebhook(
            name=d["name"],
            avatar=d.get("avatar"),
        )

    def parse_messages(self, d: raw.BulkMessageResponse) -> list[messages.Message]:
        if isinstance(d, list):
            return [self.parse_message(e) for e in d]
        elif isinstance(d, dict):
            users = [self.parse_user(e) for e in d["users"]]
            users_mapping = {u.id: u for u in users}

            members = [
                self.parse_member(e, users=users_mapping)
                for e in d.get("members") or {}
            ]
            members_mapping = {m.id: m for m in members}

            return [
                self.parse_message(e, members=members_mapping, users=users_mapping)
                for e in d["messages"]
            ]
        raise RuntimeError("Unreachable")

    def parse_mfa_response_login(
        self, d: raw.a.MFAResponseLogin, friendly_name: str | None
    ) -> auth.MFARequired:
        return auth.MFARequired(
            ticket=d["ticket"],
            allowed_methods=[auth.MFAMethod(m) for m in d["allowed_methods"]],
            internal_friendly_name=friendly_name,
            state=self.state,
        )

    def parse_mfa_ticket(self, d: raw.a.MFATicket) -> auth.MFATicket:
        return auth.MFATicket(
            id=self.parse_id(d["_id"]),
            account_id=self.parse_id(d["account_id"]),
            token=d["token"],
            validated=d["validated"],
            authorised=d["authorised"],
            last_totp_code=d.get("last_totp_code"),
        )

    def parse_multi_factor_status(
        self, d: raw.a.MultiFactorStatus
    ) -> auth.MultiFactorStatus:
        return auth.MultiFactorStatus(
            totp_mfa=d["totp_mfa"],
            recovery_active=d["recovery_active"],
        )

    def parse_mutuals(self, d: raw.MutualResponse) -> users.Mutuals:
        return users.Mutuals(
            user_ids=[self.parse_id(e) for e in d.get("users", [])],
            server_ids=[self.parse_id(e) for e in d.get("servers", [])],
        )

    def parse_none_embed(self, _: raw.NoneEmbed) -> embeds.NoneEmbed:
        return embeds._NONE_EMBED

    def parse_none_embed_special(self, _: raw.NoneSpecial) -> embeds.NoneEmbedSpecial:
        return embeds._NONE_EMBED_SPECIAL

    def parse_partial_account(self, d: raw.a.AccountInfo) -> auth.PartialAccount:
        return auth.PartialAccount(id=self.parse_id(d["_id"]), email=d["email"])

    def parse_partial_session(self, d: raw.a.SessionInfo) -> auth.PartialSession:
        return auth.PartialSession(
            state=self.state, id=self.parse_id(d["_id"]), name=d["name"]
        )

    def parse_partial_user_profile(
        self, d: raw.UserProfile, clear: list[raw.FieldsUser]
    ) -> users.PartialUserProfile:
        background = d.get("background")

        return users.PartialUserProfile(
            state=self.state,
            content=(
                None
                if "ProfileContent" in clear
                else d.get("content") or core.UNDEFINED
            ),
            internal_background=(
                None
                if "ProfileBackground" in clear
                else self.parse_asset(background) if background else core.UNDEFINED
            ),
        )

    def parse_permission_override(
        self, d: raw.Override
    ) -> permissions_.PermissionOverride:
        return permissions_.PermissionOverride(
            allow=permissions_.Permissions(d["allow"]),
            deny=permissions_.Permissions(d["deny"]),
        )

    def parse_permission_override_field(
        self, d: raw.OverrideField
    ) -> permissions_.PermissionOverride:
        return permissions_.PermissionOverride(
            allow=permissions_.Permissions(d["a"]),
            deny=permissions_.Permissions(d["d"]),
        )

    def parse_public_bot(self, d: raw.PublicBot) -> bots.PublicBot:
        return bots.PublicBot(
            state=self.state,
            id=self.parse_id(d["_id"]),
            username=d["username"],
            internal_avatar_id=d.get("avatar"),
            description=d.get("description") or "",
        )

    def parse_public_invite(self, d: raw.InviteResponse) -> invites.BaseInvite:
        return {
            "Server": self.parse_server_public_invite,
            "Group": self.parse_group_public_invite,
        }.get(d["type"], self.parse_unknown_public_invite)(d)

    def parse_read_state(self, d: raw.ChannelUnread) -> ReadState:
        id = d["_id"]
        last_id = d.get("last_id")

        return ReadState(
            state=self.state,
            channel_id=self.parse_id(id["channel"]),
            user_id=self.parse_id(id["user"]),
            last_message_id=self.parse_id(last_id) if last_id else None,
            mentioned_in=[self.parse_id(m) for m in d.get("mentions") or []],
        )

    def parse_ready_event(
        self, shard: Shard, d: raw.ClientReadyEvent
    ) -> events.ReadyEvent:
        read_states = [self.parse_read_state(rs) for rs in d["unreads"]]

        return events.ReadyEvent(
            shard=shard,
            users=[self.parse_user(u) for u in d["users"]],
            servers=[
                self.parse_server(s, (True, [self.parse_id(c) for c in s["channels"]]))
                for s in d["servers"]
            ],
            channels=[self.parse_channel(c) for c in d["channels"]],
            members=[self.parse_member(m) for m in d["members"]],
            emojis=[self.parse_server_emoji(e) for e in d["emojis"]],
            me=self.parse_self_user(d["me"]),
            settings=self.parse_user_settings(d["settings"]),
            read_states=[self.parse_read_state(rs) for rs in d["unreads"]],
        )

    def parse_relationship(self, d: raw.Relationship) -> users.Relationship:
        return users.Relationship(
            user_id=self.parse_id(d["_id"]),
            status=users.RelationshipStatus(d["status"]),
        )

    def parse_response_login(
        self, d: raw.a.ResponseLogin, friendly_name: str | None
    ) -> auth.LoginResult:
        if d["result"] == "Success":
            return self.parse_session(d)
        elif d["result"] == "MFA":
            return self.parse_mfa_response_login(d, friendly_name)
        elif d["result"] == "Disabled":
            return self.parse_disabled_response_login(d)
        else:
            raise NotImplementedError(d)

    def parse_response_webhook(self, d: raw.ResponseWebhook) -> webhooks.Webhook:
        avatar = d.get("avatar")
        webhook_id = self.parse_id(d["id"])

        return webhooks.Webhook(
            state=self.state,
            id=webhook_id,
            name=d["name"],
            internal_avatar=(
                cdn.StatelessAsset(
                    id=avatar,
                    filename="",
                    metadata=cdn.AssetMetadata(
                        type=cdn.AssetMetadataType.IMAGE,
                        width=None,
                        height=None,
                    ),
                    content_type="",
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
            channel_id=self.parse_id(d["channel_id"]),
            permissions=permissions_.Permissions(d["permissions"]),
            token=None,
        )

    def parse_role(
        self, d: raw.Role, role_id: core.ULID, server_id: core.ULID
    ) -> servers.Role:
        return servers.Role(
            state=self.state,
            id=role_id,
            name=d["name"],
            permissions=self.parse_permission_override_field(d["permissions"]),
            colour=d.get("colour"),
            hoist=d.get("hoist", False),
            rank=d["rank"],
            server_id=server_id,
        )

    def parse_saved_messages_channel(
        self, d: raw.SavedMessagesChannel
    ) -> channels.SavedMessagesChannel:
        return channels.SavedMessagesChannel(
            state=self.state,
            id=self.parse_id(d["_id"]),
            user_id=self.parse_id(d["user"]),
        )

    def parse_self_user(self, d: raw.User) -> users.SelfUser:
        avatar = d.get("avatar")
        status = d.get("status")
        profile = d.get("profile")
        privileged = d.get("privileged")
        bot = d.get("bot")

        return users.SelfUser(
            state=self.state,
            id=self.parse_id(d["_id"]),
            name=d["username"],
            discriminator=d["discriminator"],
            display_name=d.get("display_name"),
            internal_avatar=self.parse_asset(avatar) if avatar else None,
            relations=[self.parse_relationship(r) for r in d.get("relations", [])],
            badges=users.UserBadges(d.get("badges") or 0),
            status=self.parse_user_status(status) if status else None,
            # internal_profile=self.parse_user_profile(profile) if profile else None,
            flags=users.UserFlags(d.get("flags") or 0),
            privileged=privileged or False,
            bot=self.parse_bot_user_info(bot) if bot else None,
            relationship=users.RelationshipStatus(d["relationship"]),
            online=d["online"],
        )

    def _parse_server(
        self,
        d: raw.Server,
        channels: (
            tuple[t.Literal[True], list[core.ULID]]
            | tuple[t.Literal[False], list[channels.ServerChannel]]
        ),
    ) -> servers.Server:
        server_id = self.parse_id(d["_id"])

        categories = d.get("categories") or []
        system_messages = d.get("system_messages")

        roles = {}
        for id, role_data in (d.get("roles") or {}).items():
            role_id = self.parse_id(id)
            roles[role_id] = self.parse_role(role_data, role_id, server_id)

        icon = d.get("icon")
        banner = d.get("banner")
        nsfw = d.get("nsfw")
        analytics = d.get("analytics")
        discoverable = d.get("discoverable")

        return servers.Server(
            state=self.state,
            id=server_id,
            owner_id=self.parse_id(d["owner"]),
            name=d["name"],
            description=d.get("description"),
            internal_channels=channels,
            categories=[self.parse_category(e) for e in categories],
            system_messages=(
                self.parse_system_message_channels(system_messages)
                if system_messages
                else None
            ),
            roles=roles,
            default_permissions=permissions_.Permissions(d["default_permissions"]),
            internal_icon=self.parse_asset(icon) if icon else None,
            internal_banner=self.parse_asset(banner) if banner else None,
            flags=servers.ServerFlags(d.get("flags") or 0),
            nsfw=nsfw or False,
            analytics=analytics or False,
            discoverable=discoverable or False,
        )

    def parse_server(
        self,
        d: raw.Server,
        channels: (
            tuple[t.Literal[True], list[str]]
            | tuple[t.Literal[False], list[raw.Channel]]
        ),
    ) -> servers.Server:
        internal_channels: (
            tuple[t.Literal[True], list[core.ULID]]
            | tuple[t.Literal[False], list[channels.ServerChannel]]
        ) = (
            (True, [core.ULID(i) for i in channels[1]])
            if channels[0]
            else (False, [self.parse_channel(c) for c in channels[1]])  # type: ignore
        )
        return self._parse_server(d, internal_channels)

    def parse_server_create_event(
        self, shard: Shard, d: raw.ClientServerCreateEvent
    ) -> events.ServerCreateEvent:
        return events.ServerCreateEvent(
            shard=shard,
            server=self.parse_server(d["server"], (False, d["channels"])),
            emojis=[self.parse_server_emoji(e) for e in d["emojis"]],
        )

    def parse_server_delete_event(
        self, shard: Shard, d: raw.ClientServerDeleteEvent
    ) -> events.ServerDeleteEvent:
        return events.ServerDeleteEvent(
            shard=shard,
            server_id=self.parse_id(d["id"]),
            server=None,
        )

    def parse_server_emoji(self, d: raw.ServerEmoji) -> emojis.ServerEmoji:
        animated = d.get("animated")
        nsfw = d.get("nsfw")

        return emojis.ServerEmoji(
            state=self.state,
            id=self.parse_id(d["_id"]),
            server_id=self.parse_id(d["parent"]["id"]),
            creator_id=self.parse_id(d["creator_id"]),
            name=d["name"],
            animated=animated or False,
            nsfw=nsfw or False,
        )

    def parse_server_invite(self, d: raw.ServerInvite) -> invites.ServerInvite:
        return invites.ServerInvite(
            state=self.state,
            code=d["_id"],
            creator_id=self.parse_id(d["creator"]),
            server_id=self.parse_id(d["server"]),
            channel_id=self.parse_id(d["channel"]),
        )

    def parse_server_member_join_event(
        self, shard: Shard, d: raw.ClientServerMemberJoinEvent, joined_at: datetime
    ) -> events.ServerMemberJoinEvent:
        return events.ServerMemberJoinEvent(
            shard=shard,
            member=servers.Member(
                state=self.state,
                server_id=self.parse_id(d["id"]),
                _user=self.parse_id(d["user"]),
                joined_at=joined_at,
                nick=None,
                internal_avatar=None,
                roles=[],
                timeout=None,
            ),
        )

    def parse_server_member_leave_event(
        self, shard: Shard, d: raw.ClientServerMemberLeaveEvent
    ) -> events.ServerMemberLeaveEvent:
        return events.ServerMemberLeaveEvent(
            shard=shard,
            server_id=self.parse_id(d["id"]),
            user_id=self.parse_id(d["user"]),
            member=None,
        )

    def parse_server_member_update_event(
        self, shard: Shard, d: raw.ClientServerMemberUpdateEvent
    ) -> events.ServerMemberUpdateEvent:
        id = d["id"]
        data = d["data"]
        clear = d["clear"]

        avatar = data.get("avatar")
        roles = data.get("roles")
        timeout = data.get("timeout")

        return events.ServerMemberUpdateEvent(
            shard=shard,
            member=servers.PartialMember(
                state=self.state,
                server_id=self.parse_id(id["server"]),
                _user=self.parse_id(id["user"]),
                nick=(
                    None
                    if "Nickname" in clear
                    else data.get("nickname") or core.UNDEFINED
                ),
                internal_avatar=(
                    None
                    if "Avatar" in clear
                    else self.parse_asset(avatar) if avatar else core.UNDEFINED
                ),
                roles=(
                    []
                    if "Roles" in clear
                    else (
                        [self.parse_id(role) for role in roles]
                        if roles is not None
                        else core.UNDEFINED
                    )
                ),
                timeout=(
                    None
                    if "Timeout" in clear
                    else datetime.fromisoformat(timeout) if timeout else core.UNDEFINED
                ),
            ),
            before=None,  # filled on dispatch
            after=None,  # filled on dispatch
        )

    def parse_server_public_invite(
        self, d: raw.ServerInviteResponse
    ) -> invites.ServerPublicInvite:
        server_icon = d.get("server_icon")
        server_banner = d.get("server_banner")
        user_avatar = d.get("user_avatar")

        return invites.ServerPublicInvite(
            state=self.state,
            code=d["code"],
            server_id=self.parse_id(d["server_id"]),
            server_name=d["server_name"],
            internal_server_icon=self.parse_asset(server_icon) if server_icon else None,
            internal_server_banner=(
                self.parse_asset(server_banner) if server_banner else None
            ),
            flags=servers.ServerFlags(d.get("server_flags") or 0),
            channel_id=self.parse_id(d["channel_id"]),
            channel_name=d["channel_name"],
            channel_description=d.get("channel_description", None),
            user_name=d["user_name"],
            internal_user_avatar=self.parse_asset(user_avatar) if user_avatar else None,
            members_count=d["member_count"],
        )

    def parse_server_role_delete_event(
        self, shard: Shard, d: raw.ClientServerRoleDeleteEvent
    ) -> events.ServerRoleDeleteEvent:
        return events.ServerRoleDeleteEvent(
            shard=shard,
            server_id=self.parse_id(d["id"]),
            role_id=self.parse_id(d["role_id"]),
            server=None,
            role=None,
        )

    def parse_server_role_update_event(
        self, shard: Shard, d: raw.ClientServerRoleUpdateEvent
    ) -> events.RawServerRoleUpdateEvent:
        data = d["data"]
        clear = d["clear"]

        permissions = data.get("permissions")
        hoist = data.get("hoist")
        rank = data.get("rank")

        return events.RawServerRoleUpdateEvent(
            shard=shard,
            role=servers.PartialRole(
                state=self.state,
                id=self.parse_id(d["role_id"]),
                server_id=self.parse_id(d["id"]),
                name=data.get("name") or core.UNDEFINED,
                permissions=(
                    self.parse_permission_override_field(permissions)
                    if permissions
                    else core.UNDEFINED
                ),
                colour=(
                    None if "Colour" in clear else data.get("colour") or core.UNDEFINED
                ),
                hoist=hoist if hoist is not None else core.UNDEFINED,
                rank=rank if rank is not None else core.UNDEFINED,
            ),
            old_role=None,
            new_role=None,
            server=None,
        )

    def parse_server_update_event(
        self, shard: Shard, d: raw.ClientServerUpdateEvent
    ) -> events.ServerUpdateEvent:
        data = d["data"]
        clear = d["clear"]

        owner_id = data.get("owner_id")
        description = data.get("description")
        channels = data.get("channels")
        categories = data.get("categories")
        system_messages = data.get("system_messages")
        default_permissions = data.get("default_permissions")
        icon = data.get("icon")
        banner = data.get("banner")
        flags = data.get("flags")
        discoverable = data.get("discoverable")
        analytics = data.get("analytics")

        return events.ServerUpdateEvent(
            shard=shard,
            server=servers.PartialServer(
                state=self.state,
                id=self.parse_id(d["id"]),
                owner_id=(
                    self.parse_id(owner_id) if owner_id is not None else core.UNDEFINED
                ),
                name=data.get("name") or core.UNDEFINED,
                description=(
                    None
                    if "Description" in clear
                    else description if description is not None else core.UNDEFINED
                ),
                channel_ids=(
                    [self.parse_id(c) for c in channels]
                    if channels is not None
                    else core.UNDEFINED
                ),
                categories=(
                    []
                    if "Categories" in clear
                    else (
                        [self.parse_category(c) for c in categories]
                        if categories is not None
                        else core.UNDEFINED
                    )
                ),
                system_messages=(
                    None
                    if "SystemMessages" in clear
                    else (
                        self.parse_system_message_channels(system_messages)
                        if system_messages is not None
                        else core.UNDEFINED
                    )
                ),
                default_permissions=(
                    permissions_.Permissions(default_permissions)
                    if default_permissions is not None
                    else core.UNDEFINED
                ),
                internal_icon=(
                    None
                    if "Icon" in clear
                    else self.parse_asset(icon) if icon else core.UNDEFINED
                ),
                internal_banner=(
                    None
                    if "Banner" in clear
                    else self.parse_asset(banner) if banner else core.UNDEFINED
                ),
                flags=(
                    servers.ServerFlags(flags) if flags is not None else core.UNDEFINED
                ),
                discoverable=(
                    discoverable if discoverable is not None else core.UNDEFINED
                ),
                analytics=analytics if analytics is not None else core.UNDEFINED,
            ),
            before=None,  # filled on dispatch
            after=None,  # filled on dispatch
        )

    def parse_session(self, d: raw.a.Session) -> auth.Session:
        subscription = d.get("subscription")

        return auth.Session(
            state=self.state,
            id=self.parse_id(d["_id"]),
            name=d["name"],
            user_id=self.parse_id(d["user_id"]),
            token=d["token"],
            subscription=(
                self.parse_webpush_subscription(subscription) if subscription else None
            ),
        )

    def parse_soundcloud_embed_special(
        self, _: raw.SoundcloudSpecial
    ) -> embeds.SoundcloudEmbedSpecial:
        return embeds._SOUNDCLOUD_EMBED_SPECIAL

    def parse_spotify_embed_special(
        self, d: raw.SpotifySpecial
    ) -> embeds.SpotifyEmbedSpecial:
        return embeds.SpotifyEmbedSpecial(
            content_type=d["content_type"],
            id=d["id"],
        )

    def parse_streamable_embed_special(
        self, d: raw.StreamableSpecial
    ) -> embeds.StreamableEmbedSpecial:
        return embeds.StreamableEmbedSpecial(id=d["id"])

    def parse_system_message_channels(
        self,
        d: raw.SystemMessageChannels,
    ) -> servers.SystemMessageChannels:
        return servers.SystemMessageChannels(
            user_joined=d.get("user_joined"),
            user_left=d.get("user_left"),
            user_kicked=d.get("user_kicked"),
            user_banned=d.get("user_banned"),
        )

    def parse_text_channel(self, d: raw.TextChannel) -> channels.ServerTextChannel:
        icon = d.get("icon")
        last_message_id = d.get("last_message_id")
        default_permissions = d.get("default_permissions")
        role_permissions = d.get("role_permissions") or {}
        nsfw = d.get("nsfw")

        return channels.ServerTextChannel(
            state=self.state,
            id=self.parse_id(d["_id"]),
            server_id=self.parse_id(d["server"]),
            name=d["name"],
            description=d.get("description"),
            internal_icon=self.parse_asset(icon) if icon else None,
            last_message_id=self.parse_id(last_message_id) if last_message_id else None,
            default_permissions=(
                None
                if default_permissions is None
                else self.parse_permission_override_field(default_permissions)
            ),
            role_permissions={
                self.parse_id(k): self.parse_permission_override_field(v)
                for k, v in role_permissions.items()
            },
            nsfw=nsfw or False,
        )

    def parse_text_embed(self, d: raw.TextEmbed) -> embeds.StatelessTextEmbed:
        media = d.get("media")

        return embeds.StatelessTextEmbed(
            icon_url=d.get("icon_url"),
            url=d.get("url"),
            title=d.get("title"),
            description=d.get("description"),
            internal_media=self.parse_asset(media) if media else None,
            colour=d.get("colour"),
        )

    def parse_twitch_embed_special(
        self, d: raw.TwitchSpecial
    ) -> embeds.TwitchEmbedSpecial:
        return embeds.TwitchEmbedSpecial(
            content_type=embeds.TwitchContentType(d["content_type"]),
            id=d["id"],
        )

    def parse_unknown_public_invite(
        self, d: dict[str, t.Any]
    ) -> invites.UnknownPublicInvite:
        return invites.UnknownPublicInvite(state=self.state, code=d["code"], d=d)

    def parse_user(self, d: raw.User) -> users.User | users.SelfUser:
        if d["relationship"] == "User":
            return self.parse_self_user(d)

        avatar = d.get("avatar")
        status = d.get("status")
        profile = d.get("profile")
        privileged = d.get("privileged")
        bot = d.get("bot")

        return users.User(
            state=self.state,
            id=self.parse_id(d["_id"]),
            name=d["username"],
            discriminator=d["discriminator"],
            display_name=d.get("display_name"),
            internal_avatar=self.parse_asset(avatar) if avatar else None,
            badges=users.UserBadges(d.get("badges") or 0),
            status=self.parse_user_status(status) if status else None,
            # internal_profile=self.parse_user_profile(profile) if profile else None,
            flags=users.UserFlags(d.get("flags") or 0),
            privileged=privileged or False,
            bot=self.parse_bot_user_info(bot) if bot else None,
            relationship=users.RelationshipStatus(d["relationship"]),
            online=d.get("online") or False,
        )

    def parse_user_platform_wipe_event(
        self, shard: Shard, d: raw.ClientUserPlatformWipeEvent
    ) -> events.UserPlatformWipeEvent:
        return events.UserPlatformWipeEvent(
            shard=shard,
            user_id=self.parse_id(d["user_id"]),
            flags=users.UserFlags(d["flags"]),
        )

    def parse_user_profile(self, d: raw.UserProfile) -> users.StatelessUserProfile:
        background = d.get("background")

        return users.StatelessUserProfile(
            content=d.get("content"),
            internal_background=self.parse_asset(background) if background else None,
        )

    def parse_user_relationship_event(
        self, shard: Shard, d: raw.ClientUserRelationshipEvent
    ) -> events.UserRelationshipUpdateEvent:
        return events.UserRelationshipUpdateEvent(
            shard=shard,
            current_user_id=self.parse_id(d["id"]),
            old_user=None,
            new_user=self.parse_user(d["user"]),
            before=None,
        )

    def parse_user_settings(self, d: raw.UserSettings) -> user_settings.UserSettings:
        return user_settings.UserSettings(
            state=self.state,
            value={k: (s1, s2) for (k, (s1, s2)) in d.items()},
            fake=False,
        )

    def parse_user_settings_update_event(
        self, shard: Shard, d: raw.ClientUserSettingsUpdateEvent
    ) -> events.UserSettingsUpdateEvent:
        return events.UserSettingsUpdateEvent(
            shard=shard,
            current_user_id=self.parse_id(d["id"]),
            before=self.state.settings,
            after=self.parse_user_settings(d["update"]),
        )

    def parse_user_status(self, d: raw.UserStatus) -> users.UserStatus:
        presence = d.get("presence")

        return users.UserStatus(
            text=d.get("text"),
            presence=users.Presence(presence) if presence else None,
        )

    def parse_user_status_edit(
        self, d: raw.UserStatus, clear: list[raw.FieldsUser]
    ) -> users.UserStatusEdit:
        presence = d.get("presence")

        return users.UserStatusEdit(
            text=None if "StatusText" in clear else d.get("text") or core.UNDEFINED,
            presence=(
                None
                if "StatusPresence" in clear
                else users.Presence(presence) if presence else core.UNDEFINED
            ),
        )

    def parse_user_update_event(
        self, shard: Shard, d: raw.ClientUserUpdateEvent
    ) -> events.UserUpdateEvent:
        user_id = self.parse_id(d["id"])
        data = d["data"]
        clear = d["clear"]

        avatar = data.get("avatar")
        badges = data.get("badges")
        status = data.get("status")
        profile = data.get("profile")
        flags = data.get("flags")
        online = data.get("online")

        return events.UserUpdateEvent(
            shard=shard,
            user=users.PartialUser(
                state=self.state,
                id=user_id,
                name=data.get("username") or core.UNDEFINED,
                discriminator=data.get("discriminator") or core.UNDEFINED,
                display_name=(
                    None
                    if "DisplayName" in clear
                    else data.get("display_name") or core.UNDEFINED
                ),
                internal_avatar=(
                    None
                    if "Avatar" in clear
                    else self.parse_asset(avatar) if avatar else core.UNDEFINED
                ),
                badges=(
                    users.UserBadges(badges) if badges is not None else core.UNDEFINED
                ),
                status=(
                    self.parse_user_status_edit(status, clear)
                    if status is not None
                    else core.UNDEFINED
                ),
                profile=(
                    self.parse_partial_user_profile(profile, clear)
                    if profile is not None
                    else core.UNDEFINED
                ),
                flags=users.UserFlags(flags) if flags is not None else core.UNDEFINED,
                online=online if online is not None else core.UNDEFINED,
            ),
            before=None,  # filled on dispatch
            after=None,  # filled on dispatch
        )

    def parse_video_embed(self, d: raw.Video) -> embeds.VideoEmbed:
        return embeds.VideoEmbed(
            url=d["url"],
            width=d["width"],
            height=d["height"],
        )

    def parse_voice_channel(self, d: raw.VoiceChannel) -> channels.VoiceChannel:
        icon = d.get("icon")
        default_permissions = d.get("default_permissions")
        role_permissions = d.get("role_permissions") or {}
        nsfw = d.get("nsfw")

        return channels.VoiceChannel(
            state=self.state,
            id=self.parse_id(d["_id"]),
            server_id=self.parse_id(d["server"]),
            name=d["name"],
            description=d.get("description"),
            internal_icon=self.parse_asset(icon) if icon else None,
            default_permissions=(
                None
                if default_permissions is None
                else self.parse_permission_override_field(default_permissions)
            ),
            role_permissions={
                self.parse_id(k): self.parse_permission_override_field(v)
                for k, v in role_permissions.items()
            },
            nsfw=nsfw or False,
        )

    def parse_webhook(self, d: raw.Webhook) -> webhooks.Webhook:
        avatar = d.get("avatar")

        return webhooks.Webhook(
            state=self.state,
            id=self.parse_id(d["id"]),
            name=d["name"],
            internal_avatar=self.parse_asset(avatar) if avatar else None,
            channel_id=self.parse_id(d["channel_id"]),
            permissions=permissions_.Permissions(d["permissions"]),
            token=d.get("token"),
        )

    def parse_webhook_create_event(
        self, shard: Shard, d: raw.ClientWebhookCreateEvent
    ) -> events.WebhookCreateEvent:
        return events.WebhookCreateEvent(
            shard=shard,
            webhook=self.parse_webhook(d),
        )

    def parse_webhook_update_event(
        self, shard: Shard, d: raw.ClientWebhookUpdateEvent
    ) -> events.WebhookUpdateEvent:
        data = d["data"]
        remove = d["remove"]

        avatar = data.get("avatar")
        permissions = data.get("permissions")

        return events.WebhookUpdateEvent(
            shard=shard,
            webhook=webhooks.PartialWebhook(
                state=self.state,
                id=self.parse_id(d["id"]),
                name=data.get("name") or core.UNDEFINED,
                internal_avatar=(
                    None
                    if "Avatar" in remove
                    else self.parse_asset(avatar) if avatar else core.UNDEFINED
                ),
                permissions=(
                    permissions_.Permissions(permissions)
                    if permissions is not None
                    else core.UNDEFINED
                ),
            ),
        )

    def parse_webhook_delete_event(
        self, shard: Shard, d: raw.ClientWebhookDeleteEvent
    ) -> events.WebhookDeleteEvent:
        return events.WebhookDeleteEvent(
            shard=shard,
            webhook=None,
            webhook_id=self.parse_id(d["id"]),
        )

    def parse_webpush_subscription(
        self, d: raw.a.WebPushSubscription
    ) -> auth.WebPushSubscription:
        return auth.WebPushSubscription(
            endpoint=d["endpoint"],
            p256dh=d["p256dh"],
            auth=d["auth"],
        )

    def parse_website_embed(self, d: raw.WebsiteEmbed) -> embeds.WebsiteEmbed:
        special = d.get("special")
        image = d.get("image")
        video = d.get("video")

        return embeds.WebsiteEmbed(
            url=d.get("url"),
            original_url=d.get("original_url"),
            special=self.parse_embed_special(special) if special else None,
            title=d.get("title"),
            description=d.get("description"),
            image=self.parse_image_embed(image) if image else None,
            video=self.parse_video_embed(video) if video else None,
            site_name=d.get("site_name"),
            icon_url=d.get("icon_url"),
            colour=d.get("colour"),
        )

    def parse_youtube_embed_special(
        self, d: raw.YouTubeSpecial
    ) -> embeds.YouTubeEmbedSpecial:
        return embeds.YouTubeEmbedSpecial(id=d["id"], timestamp=d.get("timestamp"))


__all__ = ("Parser",)
