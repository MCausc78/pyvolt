.. currentmodule:: pyvolt

API Reference
===============

The following section outlines the API of pyvolt.

.. note::

    This module uses the Python logging module to log diagnostic and errors
    in an output independent way.  If the logging module is not configured,
    these logs will not be output anywhere.  See :ref:`logging_setup` for
    more information on how to set up and use the logging module with
    pyvolt.

Version Related Info
---------------------

There are two main ways to query version information about the library. For guarantees, check :ref:`version_guarantees`.

.. data:: version_info

    A named tuple that is similar to :obj:`py:sys.version_info`.

    Just like :obj:`py:sys.version_info` the valid values for ``releaselevel`` are
    'alpha', 'beta', 'candidate' and 'final'.

.. data:: __version__

    A string representation of the version. e.g. ``'1.0.0rc1'``. This is based
    off of :pep:`440`.

Client
------

Client
~~~~~~

.. attributetable:: Client

.. autoclass:: Client
    :members:
    :exclude-members: listen, on

    .. automethod:: Client.listen(event=None, /)
        :decorator:

    .. automethod:: Client.on(event=None, /)
        :decorator:

.. function:: listen(self=None, event=None, /)

   Alias to :meth:`Client.listen`.

   :param self: The event to listen to or client to register listener on.
   :type self: Optional[Union[:class:`Client`, EventT]]
   :param event: The event to listen to.
   :type event: Optional[EventT]

ClientEventHandler
~~~~~~~~~~~~~~~~~~

.. attributetable:: ClientEventHandler

.. autoclass:: ClientEventHandler
    :members:

EventSubscription
~~~~~~~~~~~~~~~~~

.. attributetable:: EventSubscription

.. autoclass:: EventSubscription()
    :members:

TemporarySubscription
~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: TemporarySubscription

.. autoclass:: TemporarySubscription()
    :members:

TemporarySubscriptionList
~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: TemporarySubscriptionList

.. autoclass:: TemporarySubscriptionList()
    :members:

HTTPClient
~~~~~~~~~~

.. attributetable:: HTTPClient

.. autoclass:: HTTPClient
    :members:

Shard
~~~~~

.. attributetable:: Shard

.. autoclass:: Shard
    :members:

EventHandler
~~~~~~~~~~~~

.. attributetable:: EventHandler

.. autoclass:: EventHandler
    :members:

State
~~~~~

.. attributetable:: State

.. autoclass:: State
    :members:

CDNClient
~~~~~~~~~

.. attributetable:: CDNClient

.. autoclass:: CDNClient
    :members:

Tag
~~~

.. class:: Tag
    
    An alias to :class:`typing.Literal` with available CDN tags.

Resource
~~~~~~~~

.. attributetable:: Resource

.. autoclass:: Resource
    :members:
    :inherited-members:

Upload
~~~~~~

.. attributetable:: Upload

.. autoclass:: Upload
    :members:
    :inherited-members:

Content
~~~~~~~

.. class:: Content

    A union of types that can be resolved into content.

    The following classes are included in this union:

    - :class:`bytes`
    - :class:`str`, as asset ID
    - :class:`bytearray`
    - :class:`io.IOBase`

.. autofunction:: resolve_content

ResolvableResource
~~~~~~~~~~~~~~~~~~

.. class:: ResolvableResource

    A union of types that can be resolved into resource.

    The following classes are included in this union:

    - :class:`.Resource`
    - :class:`str`
    - :class:`bytes`
    - Tuple[:class:`str`, :class:`.Content`]

.. autofunction:: resolve_resource

Cache
~~~~~

.. attributetable:: EmptyCache

.. autoclass:: EmptyCache
    :show-inheritance:
    :inherited-members:

.. attributetable:: MapCache

.. autoclass:: MapCache
    :show-inheritance:
    :inherited-members:

.. class:: CacheContextType

    Specifies a type of cache context.

    .. attribute:: undefined

        The context is not provided.
    .. attribute:: user_request

        The end user is asking for object.
    .. attribute:: library_request

        The library needs the object for internal purposes.
    .. attribute:: emoji

        The library asks for object to provide value for ``emoji.get_x()``."""
    .. attribute:: member

        The library asks for object to provide value for ``member.get_x()``."""
    .. attribute:: message

        The library asks for object to provide value for ``message.get_x()``."""
    .. attribute:: role

        The library asks for object to provide value for ``role.get_x()``."""
    .. attribute:: server

        The library asks for object to provide value for ``server.get_x()``."""
    .. attribute:: user

        The library asks for object to provide value for ``user.get_x()``."""
    .. attribute:: webhook

        The library asks for object to provide value for ``webhook.get_x()``."""
    .. attribute:: ready_event

        The context relates to :class:`.ReadyEvent` event.
    .. attribute:: private_channel_create_event

        The context relates to :class:`.PrivateChannelCreateEvent` event.
    .. attribute:: server_channel_create_event

        The context relates to :class:`.ServerChannelCreateEvent` event.
    .. attribute:: channel_update_event

        The context relates to :class:`.ChannelUpdateEvent` event.
    .. attribute:: channel_delete_event

        The context relates to :class:`.ChannelDeleteEvent` event.
    .. attribute:: group_recipient_add_event

        The context relates to :class:`.GroupRecipientAddEvent` event.
    .. attribute:: group_recipient_remove_event

        The context relates to :class:`.GroupRecipientRemoveEvent` event.
    .. attribute:: channel_start_typing_event

        The context relates to :class:`.ChannelStartTypingEvent` event.
    .. attribute:: channel_stop_typing_event

        The context relates to :class:`.ChannelStopTypingEvent` event.
    .. attribute:: message_ack_event

        The context relates to :class:`.MessageAckEvent` event.
    .. attribute:: message_create_event

        The context relates to :class:`.MessageCreateEvent` event.
    .. attribute:: message_update_event

        The context relates to :class:`.MessageUpdateEvent` event.
    .. attribute:: message_append_event

        The context relates to :class:`.MessageAppendEvent` event.
    .. attribute:: message_delete_event

        The context relates to :class:`.MessageDeleteEvent` event.
    .. attribute:: message_react_event

        The context relates to :class:`.MessageReactEvent` event.
    .. attribute:: message_unreact_event

        The context relates to :class:`.MessageUnreactEvent` event.
    .. attribute:: message_clear_reaction_event

        The context relates to :class:`.MessageClearReactionEvent` event.
    .. attribute:: message_delete_bulk_event

        The context relates to :class:`.MessageDeleteBulkEvent` event.
    .. attribute:: server_create_event

        The context relates to :class:`.ServerCreateEvent` event.
    .. attribute:: server_emoji_create_event

        The context relates to :class:`.ServerEmojiCreateEvent` event.
    .. attribute:: server_emoji_delete_event

        The context relates to :class:`.ServerEmojiDeleteEvent` event.
    .. attribute:: server_update_event

        The context relates to :class:`.ServerUpdateEvent` event.
    .. attribute:: server_delete_event

        The context relates to :class:`.ServerDeleteEvent` event.
    .. attribute:: server_member_join_event

        The context relates to :class:`.ServerMemberJoinEvent` event.
    .. attribute:: server_member_update_event

        The context relates to :class:`.ServerMemberUpdateEvent` event.
    .. attribute:: server_member_remove_event

        The context relates to :class:`.ServerMemberRemoveEvent` event.
    .. attribute:: server_role_update_event

        The context relates to :class:`.RawServerRoleUpdateEvent` event.
    .. attribute:: server_role_delete_event

        The context relates to :class:`.ServerRoleDeleteEvent` event.
    .. attribute:: report_create_event

        The context relates to :class:`.ReportCreateEvent` event.
    .. attribute:: user_update_event

        The context relates to :class:`.UserUpdateEvent` event.
    .. attribute:: user_platform_wipe_event

        The context relates to :class:`.UserPlatformWipeEvent` event.
    .. attribute:: user_relationship_update_event

        The context relates to :class:`.UserRelationshipUpdateEvent` event.
    .. attribute:: user_settings_update_event

        The context relates to :class:`.UserSettingsUpdateEvent` event.
    .. attribute:: webhook_create_event
        
        The context relates to :class:`.WebhookCreateEvent` event.
    .. attribute:: webhook_update_event
        
        The context relates to :class:`.WebhookUpdateEvent` event.
    .. attribute:: webhook_delete_event
        
        The context relates to :class:`.WebhookDeleteEvent` event.
    .. attribute:: session_create_event
        
        The context relates to :class:`.SessionCreateEvent` event.
    .. attribute:: session_delete_event
        
        The context relates to :class:`.SessionDeleteEvent` event.
    .. attribute:: session_delete_all_event
        
        The context relates to :class:`.SessionDeleteAllEvent` event.
    .. attribute:: voice_channel_join_event

        The context relates to :class:`.VoiceChannelJoinEvent` event.
    .. attribute:: voice_channel_leave_event

        The context relates to :class:`.VoiceChannelLeaveEvent` event.
    .. attribute:: user_voice_state_update_event

        The context relates to :class:`.UserVoiceStateUpdateEvent` event.
    .. attribute:: authenticated_event

        The context relates to :class:`.AuthenticatedEvent` event.

.. attributetable:: BaseCacheContext

.. autoclass:: BaseCacheContext
    :members:

.. attributetable:: DetachedEmojiCacheContext

.. autoclass:: DetachedEmojiCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: BaseCacheContext

.. autoclass:: BaseCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: UndefinedCacheContext

.. autoclass:: UndefinedCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: DetachedEmojiCacheContext

.. autoclass:: DetachedEmojiCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: MessageCacheContext

.. autoclass:: MessageCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: ServerCacheContext

.. autoclass:: ServerCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: ServerEmojiCacheContext

.. autoclass:: ServerEmojiCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: UserCacheContext

.. autoclass:: UserCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: PrivateChannelCreateEventCacheContext

.. autoclass:: PrivateChannelCreateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: ServerChannelCreateEventCacheContext

.. autoclass:: ServerChannelCreateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: ChannelUpdateEventCacheContext

.. autoclass:: ChannelUpdateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: ChannelDeleteEventCacheContext

.. autoclass:: ChannelDeleteEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: GroupRecipientAddEventCacheContext

.. autoclass:: GroupRecipientAddEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: GroupRecipientRemoveEventCacheContext

.. autoclass:: GroupRecipientRemoveEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: ChannelStartTypingEventCacheContext

.. autoclass:: ChannelStartTypingEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: ChannelStopTypingEventCacheContext

.. autoclass:: ChannelStopTypingEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: MessageAckEventCacheContext

.. autoclass:: MessageAckEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: MessageCreateEventCacheContext

.. autoclass:: MessageCreateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: MessageUpdateEventCacheContext

.. autoclass:: MessageUpdateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: MessageAppendEventCacheContext

.. autoclass:: MessageAppendEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: MessageDeleteEventCacheContext

.. autoclass:: MessageDeleteEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: MessageReactEventCacheContext

.. autoclass:: MessageReactEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: MessageUnreactEventCacheContext

.. autoclass:: MessageUnreactEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: MessageClearReactionEventCacheContext

.. autoclass:: MessageClearReactionEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: MessageDeleteBulkEventCacheContext

.. autoclass:: MessageDeleteBulkEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: ServerCreateEventCacheContext

.. autoclass:: ServerCreateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: ServerEmojiCreateEventCacheContext

.. autoclass:: ServerEmojiCreateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: ServerEmojiDeleteEventCacheContext

.. autoclass:: ServerEmojiDeleteEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: ServerUpdateEventCacheContext

.. autoclass:: ServerUpdateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: ServerDeleteEventCacheContext

.. autoclass:: ServerDeleteEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: ServerMemberJoinEventCacheContext

.. autoclass:: ServerMemberJoinEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: ServerMemberUpdateEventCacheContext

.. autoclass:: ServerMemberUpdateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: ServerMemberRemoveEventCacheContext

.. autoclass:: ServerMemberRemoveEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: RawServerRoleUpdateEventCacheContext

.. autoclass:: RawServerRoleUpdateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: ServerRoleDeleteEventCacheContext

.. autoclass:: ServerRoleDeleteEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: ReportCreateEventCacheContext

.. autoclass:: ReportCreateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: UserUpdateEventCacheContext

.. autoclass:: UserUpdateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: UserRelationshipUpdateEventCacheContext

.. autoclass:: UserRelationshipUpdateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: UserSettingsUpdateEventCacheContext

.. autoclass:: UserSettingsUpdateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: UserPlatformWipeEventCacheContext

.. autoclass:: UserPlatformWipeEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: WebhookCreateEventCacheContext

.. autoclass:: WebhookCreateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: WebhookUpdateEventCacheContext

.. autoclass:: WebhookUpdateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: WebhookDeleteEventCacheContext

.. autoclass:: WebhookDeleteEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: SessionCreateEventCacheContext

.. autoclass:: SessionCreateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: SessionDeleteEventCacheContext

.. autoclass:: SessionDeleteEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: SessionDeleteAllEventCacheContext

.. autoclass:: SessionDeleteAllEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: VoiceChannelJoinEventCacheContext

.. autoclass:: VoiceChannelJoinEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: VoiceChannelLeaveEventCacheContext

.. autoclass:: VoiceChannelLeaveEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: UserVoiceStateUpdateEventCacheContext

.. autoclass:: UserVoiceStateUpdateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: AuthenticatedEventCacheContext

.. autoclass:: AuthenticatedEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. _revolt-api-events:

Events
------

.. attributetable:: BaseEvent

.. autoclass:: BaseEvent
    :members:
    :inherited-members:

.. attributetable:: ShardEvent

.. autoclass:: ShardEvent
    :members:
    :inherited-members:

.. attributetable:: ReadyEvent

.. autoclass:: ReadyEvent
    :members:
    :inherited-members:

.. attributetable:: BaseChannelCreateEvent

.. autoclass:: BaseChannelCreateEvent
    :members:
    :inherited-members:

.. attributetable:: PrivateChannelCreateEvent

.. autoclass:: PrivateChannelCreateEvent
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: ServerChannelCreateEvent

.. autoclass:: ServerChannelCreateEvent
    :show-inheritance:
    :members:
    :inherited-members:

.. class:: ChannelCreateEvent
    A union of private/server channel create events.
    
    The following classes are included in this union:

    - :class:`.PrivateChannelCreateEvent`
    - :class:`.ServerChannelCreateEvent`

.. attributetable:: ChannelUpdateEvent

.. autoclass:: ChannelUpdateEvent
    :members:
    :inherited-members:

.. attributetable:: ChannelDeleteEvent

.. autoclass:: ChannelDeleteEvent
    :members:
    :inherited-members:

.. attributetable:: GroupRecipientAddEvent

.. autoclass:: GroupRecipientAddEvent
    :members:
    :inherited-members:

.. attributetable:: GroupRecipientRemoveEvent

.. autoclass:: GroupRecipientRemoveEvent
    :members:
    :inherited-members:

.. attributetable:: ChannelStartTypingEvent

.. autoclass:: ChannelStartTypingEvent
    :members:
    :inherited-members:

.. attributetable:: ChannelStopTypingEvent

.. autoclass:: ChannelStopTypingEvent
    :members:
    :inherited-members:

.. attributetable:: MessageAckEvent

.. autoclass:: MessageAckEvent
    :members:
    :inherited-members:

.. attributetable:: MessageCreateEvent

.. autoclass:: MessageCreateEvent
    :members:
    :inherited-members:

.. attributetable:: MessageUpdateEvent

.. autoclass:: MessageUpdateEvent
    :members:
    :inherited-members:

.. attributetable:: MessageAppendEvent

.. autoclass:: MessageAppendEvent
    :members:
    :inherited-members:

.. attributetable:: MessageDeleteEvent

.. autoclass:: MessageDeleteEvent
    :members:
    :inherited-members:

.. attributetable:: MessageReactEvent

.. autoclass:: MessageReactEvent
    :members:
    :inherited-members:

.. attributetable:: MessageUnreactEvent

.. autoclass:: MessageUnreactEvent
    :members:
    :inherited-members:

.. attributetable:: MessageClearReactionEvent

.. autoclass:: MessageClearReactionEvent
    :members:
    :inherited-members:

.. attributetable:: MessageDeleteBulkEvent

.. autoclass:: MessageDeleteBulkEvent
    :members:
    :inherited-members:

.. attributetable:: ServerCreateEvent

.. autoclass:: ServerCreateEvent
    :members:
    :inherited-members:

.. attributetable:: ServerEmojiCreateEvent

.. autoclass:: ServerEmojiCreateEvent
    :members:
    :inherited-members:

.. attributetable:: ServerEmojiDeleteEvent

.. autoclass:: ServerEmojiDeleteEvent
    :members:
    :inherited-members:

.. attributetable:: ServerUpdateEvent

.. autoclass:: ServerUpdateEvent
    :members:
    :inherited-members:

.. attributetable:: ServerDeleteEvent

.. autoclass:: ServerDeleteEvent
    :members:
    :inherited-members:

.. attributetable:: ServerMemberJoinEvent

.. autoclass:: ServerMemberJoinEvent
    :members:
    :inherited-members:

.. attributetable:: ServerMemberUpdateEvent

.. autoclass:: ServerMemberUpdateEvent
    :members:
    :inherited-members:

.. attributetable:: ServerMemberRemoveEvent

.. autoclass:: ServerMemberRemoveEvent
    :members:
    :inherited-members:

.. attributetable:: RawServerRoleUpdateEvent

.. autoclass:: RawServerRoleUpdateEvent
    :members:
    :inherited-members:

.. attributetable:: ServerRoleDeleteEvent

.. autoclass:: ServerRoleDeleteEvent
    :members:
    :inherited-members:

.. attributetable:: ReportCreateEvent

.. autoclass:: ReportCreateEvent
    :members:
    :inherited-members:

.. attributetable:: UserUpdateEvent

.. autoclass:: UserUpdateEvent
    :members:
    :inherited-members:

.. attributetable:: UserRelationshipUpdateEvent

.. autoclass:: UserRelationshipUpdateEvent
    :members:
    :inherited-members:

.. attributetable:: UserSettingsUpdateEvent

.. autoclass:: UserSettingsUpdateEvent
    :members:
    :inherited-members:

.. attributetable:: UserPlatformWipeEvent

.. autoclass:: UserPlatformWipeEvent
    :members:
    :inherited-members:

.. attributetable:: WebhookCreateEvent

.. autoclass:: WebhookCreateEvent
    :members:
    :inherited-members:

.. attributetable:: WebhookUpdateEvent

.. autoclass:: WebhookUpdateEvent
    :members:
    :inherited-members:

.. attributetable:: WebhookDeleteEvent

.. autoclass:: WebhookDeleteEvent
    :members:
    :inherited-members:

.. attributetable:: AuthifierEvent

.. autoclass:: AuthifierEvent
    :members:
    :inherited-members:

.. attributetable:: SessionCreateEvent

.. autoclass:: SessionCreateEvent
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: SessionDeleteEvent

.. autoclass:: SessionDeleteEvent
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: SessionDeleteAllEvent

.. autoclass:: SessionDeleteAllEvent
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: LogoutEvent

.. autoclass:: LogoutEvent
    :members:
    :inherited-members:

.. attributetable:: VoiceChannelJoinEvent

.. autoclass:: VoiceChannelJoinEvent
    :members:
    :inherited-members:

.. attributetable:: VoiceChannelLeaveEvent

.. autoclass:: VoiceChannelLeaveEvent
    :members:
    :inherited-members:

.. attributetable:: UserVoiceStateUpdateEvent

.. autoclass:: UserVoiceStateUpdateEvent
    :members:
    :inherited-members:

.. attributetable:: AuthenticatedEvent

.. autoclass:: AuthenticatedEvent
    :members:
    :inherited-members:

.. attributetable:: BeforeConnectEvent

.. autoclass:: BeforeConnectEvent
    :members:
    :inherited-members:

.. attributetable:: AfterConnectEvent

.. autoclass:: AfterConnectEvent
    :members:
    :inherited-members:

.. _revolt-api-permissions-calculator:

Permissions Calculator
----------------------

.. autofunction:: calculate_saved_messages_channel_permissions

.. autofunction:: calculate_dm_channel_permissions

.. autofunction:: calculate_group_channel_permissions

.. autofunction:: calculate_server_channel_permissions

.. autofunction:: calculate_server_permissions

.. autofunction:: calculate_user_permissions

.. _revolt-api-utils:

Utility Functions
-----------------

.. autofunction:: sort_member_roles

.. _revolt-api-enums:

Enumerations
------------

The API provides some enumerations for certain types of strings to avoid the API
from being stringly typed in case the strings change in the future.

All enumerations are subclasses of an custom class which mimics the behaviour
of :class:`enum.Enum`.

Enum
~~~~

.. attributetable:: Enum

.. autoclass:: Enum
    :members:

Authentication
~~~~~~~~~~~~~~

.. class:: MFAMethod

    Specifies the method of MFA.
    
    .. attribute:: password

        The MFA is being done using password.
    .. attribute:: recovery

        The MFA is being done using recovery code.
    .. attribute:: totp

        The MFA is being done using TOTP code.

Asset
~~~~~

.. class:: AssetMetadataType

    Specifies the metadata type of asset.

    .. attribute:: file

        The file is just a generic uncategorized file.
    .. attribute:: text

        The file contains textual data and should be displayed as such.
    .. attribute:: image

        The file is an image with specific dimensions.
    .. attribute:: video

        The file is a video with specific dimensions.
    .. attribute:: audio

        The file is audio.

Channel
~~~~~~~

.. class:: ChannelType
    
    Specifies the type of a channel.

    .. attribute:: saved_messages
        
        A channel accessible only to one user.
    .. attribute:: private

        A private text channel. Also called a direct message.
    .. attribute:: group
        
        A private group text channel.
    .. attribute:: text

        A text channel.
    .. attribute:: voice

        A voice channel.

Discover
~~~~~~~~

.. class:: ServerActivity

    Specifies server activity.
    
    .. attribute:: high

        Server is highly active.
    .. attribute:: medium

        Server is active.
    .. attribute:: low

        Server has too low activity.
    .. attribute:: no

        Server has no activity at all.

.. class:: BotUsage

    Specifies bot's usage.
    
    .. attribute:: high

        Bot is actively used.
    .. attribute:: medium

        Bot is used but not frequently.
    .. attribute:: low

        Bot is frequently unused.

.. class:: LightspeedContentType

    Specifies type of remote Lightspeed.tv content.

    .. attribute:: channel
        
        A Lightspeed.tv channel.
    
.. class:: TwitchContentType
    
    Specifies type of remote Twitch content.

    .. attribute:: channel
        
        A Twitch channel.
    .. attribute:: video
        
        A Twitch video.
    .. attribute:: clip
        
        A Twitch clip.

.. class:: BandcampContentType

    Specifies type of remote Bandcamp content.

    .. attribute:: album
        
        A Bandcamp album.
    .. attribute:: track

        A Bandcamp track.

.. class:: ImageSize

    Specifies image positioning and size.

    .. attribute:: large
        
        Show large preview at the bottom of the embed.
    .. attribute:: preview

        Show small preview to the side of the embed.

.. class:: Language

    Specifies language.

    .. attribute:: en

        English (Traditional)
    .. attribute:: en_US

        English (Simplified)
    .. attribute:: ar

        عربي
    .. attribute:: as

        অসমীয়া
    .. attribute:: az

        Azərbaycan dili
    .. attribute:: be

        Беларуская
    .. attribute:: bg

        Български
    .. attribute:: bn

        বাংলা
    .. attribute:: br

        Brezhoneg
    .. attribute:: ca

        Català
    .. attribute:: ceb

        Bisaya
    .. attribute:: ckb

        کوردی
    .. attribute:: cs

        Čeština
    .. attribute:: da

        Dansk
    .. attribute:: de

        Deutsch
    .. attribute:: el

        Ελληνικά
    .. attribute:: es

        Español
    .. attribute:: es_419

        Español (América Latina)
    .. attribute:: et

        eesti
    .. attribute:: fi

        suomi
    .. attribute:: fil

        Filipino
    .. attribute:: fr

        Français
    .. attribute:: ga

        Gaeilge
    .. attribute:: hi

        हिन्दी
    .. attribute:: hr

        Hrvatski
    .. attribute:: hu

        Magyar
    .. attribute:: hy

        հայերեն
    .. attribute:: id

        Bahasa Indonesia
    .. attribute:: is

        Íslenska
    .. attribute:: it

        Italiano
    .. attribute:: ja

        日本語
    .. attribute:: ko

        한국어
    .. attribute:: lb

        Lëtzebuergesch
    .. attribute:: lt

        Lietuvių
    .. attribute:: lv

        Latviešu
    .. attribute:: mk

        Македонски
    .. attribute:: ms

        Bahasa Melayu
    .. attribute:: nb_NO

        Norsk bokmål
    .. attribute:: nl

        Nederlands
    .. attribute:: fa

        فارسی
    .. attribute:: pl

        Polski
    .. attribute:: pt_BR

        Português (do Brasil)
    .. attribute:: pt_PT

        Português (Portugal)
    .. attribute:: ro

        Română
    .. attribute:: ru

        Русский
    .. attribute:: sk

        Slovensky
    .. attribute:: sl

        Slovenščina
    .. attribute:: sq

        Shqip
    .. attribute:: sr

        Српски
    .. attribute:: si

        සිංහල
    .. attribute:: sv

        Svenska
    .. attribute:: ta

        தமிழ்
    .. attribute:: th

        ไทย
    .. attribute:: tr

        Türkçe
    .. attribute:: ur

        اردو
    .. attribute:: uk

        Українська
    .. attribute:: vec

        Vèneto
    .. attribute:: vi

        Tiếng Việt
    .. attribute:: zh_Hans

        简体中文
    .. attribute:: zh_Hant

        繁體中文
    .. attribute:: tokipona

        Toki Pona
    .. attribute:: eo

        Esperanto
    .. attribute:: owo

        OwO

        .. note::
            This is joke language.
    .. attribute:: pirate

        Pirate

        .. note::
            This is joke language.
    .. attribute:: bottom

        Bottom

        .. note::
            This is joke language.
    .. attribute:: leet

        1337
        
        .. note::
            This is joke language.
    .. attribute:: enchantment_table

        Enchantment Table
        
        .. note::
            This is joke language.
    .. attribute:: piglatin

        Pig Latin
        
        .. note::
            This is joke language.

.. class:: MessageSort
    
    Specifies order of messages.

    .. attribute:: relevance

        Sort messages by relevance.
    .. attribute:: latest
        
        Sort messages by timestamp in descending order.
    .. attribute:: oldest

        Sort messages by timestamp in ascending order.
    
.. class:: ContentReportReason

    Specifies reason for user report.

    .. attribute:: none

        No reason has been specified.
    .. attribute:: unsolicited_spam

        User is sending unsolicited advertisements.
    .. attribute:: spam_abuse

        User is sending spam or abusing the platform.
    .. attribute:: inappropriate_profile

        User's profile contains inappropriate content for a general audience.
    .. attribute:: impersonation

        User is impersonating another user.
    .. attribute:: ban_evasion

        User is evading a ban.
    .. attribute:: underage

        User is not of minimum age to use the platform.

.. class:: MemberRemovalIntention
    
    Specifies reason why member was removed from server.

    .. attribute:: leave

        The member manually left.
    .. attribute:: kick

        The member was kicked.
    .. attribute:: ban

        The member was banned.

.. class:: ShardFormat

    Specifies WebSocket format the shard should communicate in.
    
    .. attribute:: json
        
        Communicate using JSON.
        
        Recommended for testing.
    .. attribute:: msgpack

        Communicate using `MessagePack <https://msgpack.org/index.html>`_ format.

        Recommended for production due to being most efficient format.

.. class:: AndroidTheme

    Specifies client theme for Revolt Android.

    .. attribute:: revolt
        
        Use Revolt colors.
    .. attribute:: light
        
        Represents the Light theme on Revolt Android.
    .. attribute:: pure_black
        
        Represents the AMOLED theme on Revolt Android.
    .. attribute:: system
        
        Use system theme.
    .. attribute:: material_you
        
        Represents the Material You theme on Revolt Android.

.. class:: AndroidProfilePictureShape

    Specifies rounding grade for profile pictures, including in chat and profiles.
    This applies to all users on Revolt Android.

    .. attribute:: sharp
    
        Use sharp rounding grade for profile pictures.
    .. attribute:: rounded

        Use rounded grade for profile pictures.
    .. attribute:: circular

        Use circular rounding grade for profile pictures.

.. class:: AndroidMessageReplyStyle

    Specifies a way to quickly reply on Revolt Android.

    .. attribute:: long_press_to_reply

        Long press message to reply.
    .. attribute:: swipe_to_reply

        Swipe from message end to reply.
    .. attribute:: double_tap_to_reply

        Tap twice a message to reply.

.. class:: ReviteChangelogEntry

    Represents a Revite changelog entry.

    More details about entries may be found `here <https://github.com/revoltchat/revite/blob/478d3751255a441bf39057b81f807ffe96a0e97a/src/assets/changelogs.tsx>`_.

    .. attribute:: mfa_feature
        
        Represents a changelog entry about securing accounts with MFA.
    .. attribute:: iar_reporting_feature

        Represents a changelog entry about in-app reporting messages, servers and users.
    .. attribute:: discriminators_feature
        
        Represents a changelog entry about adding discriminators.
    .. property:: created_at

        When the changelog entry was created.
    .. property:: title

        The changelog entries' title.

.. class:: ReviteNotificationState

    Specifies the notification's state.
    
    .. attribute:: all_messages

        You're always notified unless you're busy.
    .. attribute:: mentions_only

        You're only notified on mentions unless you're busy .
    .. attribute:: none

        State is not specified. Currently same as :attr:`.muted`.
    .. attribute:: muted

        The channel/server is muted.

.. class:: ReviteEmojiPack

    Specifies the emoji pack to render.

    .. attribute:: mutant_remix

        Use 'Mutant Remix' emoji pack.
    .. attribute:: twemoji

        Use 'Twemoji' emoji pack.
    .. attribute:: openmoji

        Use 'Openmoji' emoji pack.
    .. attribute:: noto_emoji

        Use 'Noto Emoji' emoji pack.

.. class:: ReviteBaseTheme

    Represents the Revite client theme.

    .. attribute:: light
        
        Represents the Light theme on Revolt.
    .. attribute:: dark
        
        Represents the Dark theme on Revolt.

.. class:: ReviteFont
    
    Specifies the font in Revite client.
    
    .. attribute:: open_sans

        Represents 'Open Sans' font.
    .. attribute:: opendyslexic
        
        Represents 'OpenDyslexic' font.
    .. attribute:: inter
        
        Represents 'Inter' font.

        .. note::
            This font supports ligatures.
    .. attribute:: atkinson_hyperlegible
        
        Represents 'Atkinson Hyperlegible' font.
    .. attribute:: roboto
        
        Represents 'Roboto' font.
    .. attribute:: noto_sans
        
        Represents 'Noto Sans' font.
    .. attribute:: lato
        
        Represents 'Lato' font.
    .. attribute:: bitter
        
        Represents 'Bitter' font.
    .. attribute:: montserrat
        
        Represents 'Montserrat' font.
    .. attribute:: poppins
        
        Represents 'Poppins' font.
    .. attribute:: raleway
        
        Represents 'Raleway' font.
    .. attribute:: ubuntu
        
        Represents 'Ubuntu' font.
    .. attribute:: comic_neue
        
        Represents 'Comic Neue' font.
    .. attribute:: lexend
        
        Represents 'Lexend' font.

.. class:: ReviteMonoFont
    
    Specifies the font inside codeblocks in Revite client.
    
    .. attribute:: fira_code
        
        Represents 'Fira Code' mont.
    .. attribute:: roboto_mono
        
        Represents 'Roboto Mono' mont.
    .. attribute:: source_code_pro
        
        Represents 'Source Code Pro' mont.
    .. attribute:: space_mono
        
        Represents 'Space Mono' mont.
    .. attribute:: ubuntu_mono
        
        Represents 'Ubuntu Mono' mont.
    .. attribute:: jetbrains_mono
        
        Represents 'JetBrains Mono' mont.

.. class:: Presence
    
    Specifies the presence of a user.

    .. attribute:: online

        The user is online.
    .. attribute:: idle

        The user is currently not available.
    .. attribute:: focus

        The user is focusing and will only receive mentions.
    .. attribute:: busy

        The user is busy and will not receive any notifications.
    .. attribute:: invisible
        The user appears to be offline to other users.

.. class:: RelationshipStatus

    Specifies the relationship of current user and another user (or themselves).

    .. attribute:: none
        
        No relationship.
    .. attribute:: user
        
        This user is you.
    .. attribute:: friend
        
        This user is friends with you.
    .. attribute:: outgoing

        You sent friend request to this user.
    .. attribute:: incoming

        This user sent friend request to you.
    .. attribute:: blocked
        
        You blocked this user.
    .. attribute:: blocked_other

        This user blocked you.

.. class:: ReportStatus

    Specifies the status of a report.

    .. attribute:: created
        
        The report was just created and pending.
    .. attribute:: rejected

        The report was rejected.
    .. attribute:: resolved

        The report was resolved.

.. class:: ReportedContentType

    Specifies the type of reported content.

    .. attribute:: message

        The content being reported is message.
    .. attribute:: server

        The content being reported is server.
    .. attribute:: user

        The content being reported is user.

.. _revolt-api-flags:

Flag Classes
------------

BaseFlags
~~~~~~~~~

.. attributetable:: BaseFlags

.. autoclass:: BaseFlags
    :members:

.. autofunction:: flag

.. autofunction:: doc_flags

BotFlags
~~~~~~~~

.. attributetable:: BotFlags

.. autoclass:: BotFlags
    :members:
    :inherited-members:

MessageFlags
~~~~~~~~~~~~

.. attributetable:: MessageFlags

.. autoclass:: MessageFlags
    :members:
    :inherited-members:

Permissions
~~~~~~~~~~~

.. attributetable:: Permissions

.. autoclass:: Permissions
    :members:
    :inherited-members:

.. data:: ALLOW_PERMISSIONS_IN_TIMEOUT

    The permissions that are only allowed when user is timed out.
.. data:: VIEW_ONLY_PERMISSIONS

    The permissions that are allowed when user can view channel.
.. data:: DEFAULT_PERMISSIONS

    The default permissions.
.. data:: DEFAULT_SAVED_MESSAGES_PERMISSIONS

    The default permissions in :class:`.SavedMessagesChannel`.
.. data:: DEFAULT_DM_PERMISSIONS

    The default permissions in :class:`.DMChannel`.
.. data:: DEFAULT_SERVER_PERMISSIONS

    The default permissions in :class:`.Server`.

UserPermissions
~~~~~~~~~~~~~~~

.. attributetable:: UserPermissions

.. autoclass:: UserPermissions
    :members:
    :inherited-members:

ServerFlags
~~~~~~~~~~~

.. attributetable:: ServerFlags

.. autoclass:: ServerFlags
    :members:
    :inherited-members:

UserBadges
~~~~~~~~~~

.. attributetable:: UserBadges

.. autoclass:: UserBadges
    :members:
    :inherited-members:

UserFlags
~~~~~~~~~

.. attributetable:: UserFlags

.. autoclass:: UserFlags
    :members:
    :inherited-members:

Abstract Base Classes
---------------------

Messageable
~~~~~~~~~~~

.. attributetable:: pyvolt.abc.Messageable

.. autoclass:: pyvolt.abc.Messageable()
    :members:
    :exclude-members: typing

    .. automethod:: pyvolt.abc.Messageable.typing
        :async-with:

Connectable
~~~~~~~~~~~

.. attributetable:: pyvolt.abc.Connectable

.. autoclass:: pyvolt.abc.Connectable
    :members:

Cache
~~~~~

.. attributetable:: Cache

.. autoclass:: Cache
    :members:

.. _revolt-api-models:

Models
------

Asset
~~~~~

.. attributetable:: StatelessAsset

.. autoclass:: StatelessAsset
    :members:

.. attributetable:: Asset

.. autoclass:: Asset
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: AssetMetadata

.. autoclass:: AssetMetadata
    :members:

User
~~~~

.. attributetable:: BaseUser

.. autoclass:: BaseUser
    :members:

.. attributetable:: DisplayUser

.. autoclass:: DisplayUser
    :members:
    :inherited-members:

.. attributetable:: PartialUser

.. autoclass:: PartialUser
    :members:
    :inherited-members:

.. attributetable:: User

.. autoclass:: User
    :members:
    :inherited-members:

.. attributetable:: OwnUser

.. autoclass:: OwnUser
    :members:
    :inherited-members:
    :exclude-members: accept_friend_request, block, deny_friend_request, mutual_friend_ids, mutual_server_ids, mutuals, remove_friend, report, send_friend_request, unblock

Channel
~~~~~~~

.. attributetable:: BaseChannel

.. autoclass:: BaseChannel
    :members:

.. attributetable:: PartialChannel

.. autoclass:: PartialChannel
    :members:
    :inherited-members:

.. attributetable:: SavedMessagesChannel

.. autoclass:: SavedMessagesChannel
    :members:
    :inherited-members:

.. attributetable:: DMChannel

.. autoclass:: DMChannel
    :members:
    :inherited-members:

.. attributetable:: GroupChannel

.. autoclass:: GroupChannel
    :members:
    :inherited-members:

.. attributetable:: BaseServerChannel

.. autoclass:: BaseServerChannel
    :members:
    :inherited-members:

.. attributetable:: ChannelVoiceMetadata

.. autoclass:: ChannelVoiceMetadata
    :members:

.. attributetable:: TextChannel

.. autoclass:: TextChannel
    :members:
    :inherited-members:

.. attributetable:: VoiceChannel

.. autoclass:: VoiceChannel
    :members:
    :inherited-members:

.. class:: PrivateChannel
    A union of all channels that do not belong to a server.
    
    The following classes are included in this union:

    - :class:`.SavedMessagesChannel`
    - :class:`.DMChannel`
    - :class:`.GroupChannel`
    
.. class:: ServerChannel
    A union of all channels that belong to a server.
    
    The following classes are included in this union:

    - :class:`.TextChannel`
    - :class:`.VoiceChannel`

.. class:: TextableChannel
    A union of all channels that can have messages in them.
    
    The following classes are included in this union:
    
    - :class:`.SavedMessagesChannel`
    - :class:`.DMChannel`
    - :class:`.GroupChannel`
    - :class:`.TextChannel`
    - :class:`.VoiceChannel`

.. class:: Channel
    A union of all channels.

    Union types such as this exist to help determine which exact channel type has some field during development.

    The following classes are included in this union:
    
    - :class:`.SavedMessagesChannel`
    - :class:`.DMChannel`
    - :class:`.GroupChannel`
    - :class:`.TextChannel`
    - :class:`.VoiceChannel`

.. attributetable:: ChannelVoiceStateContainer

.. autoclass:: ChannelVoiceStateContainer
    :members:

Embed
~~~~~

.. attributetable:: BaseEmbed

.. autoclass:: BaseEmbed
    :members:

.. attributetable:: BaseEmbedSpecial

.. autoclass:: BaseEmbedSpecial
    :members:

.. attributetable:: NoneEmbedSpecial

.. autoclass:: NoneEmbedSpecial
    :members:
    :inherited-members:

.. attributetable:: GifEmbedSpecial

.. autoclass:: GifEmbedSpecial
    :members:
    :inherited-members:

.. attributetable:: YouTubeEmbedSpecial

.. autoclass:: YouTubeEmbedSpecial
    :members:
    :inherited-members:

.. attributetable:: LightspeedEmbedSpecial

.. autoclass:: LightspeedEmbedSpecial
    :members:
    :inherited-members:

.. attributetable:: TwitchEmbedSpecial

.. autoclass:: TwitchEmbedSpecial
    :members:
    :inherited-members:

.. attributetable:: SpotifyEmbedSpecial

.. autoclass:: SpotifyEmbedSpecial
    :members:
    :inherited-members:

.. attributetable:: SoundcloudEmbedSpecial

.. autoclass:: SoundcloudEmbedSpecial
    :members:
    :inherited-members:

.. attributetable:: BandcampEmbedSpecial

.. autoclass:: BandcampEmbedSpecial
    :members:
    :inherited-members:

.. attributetable:: AppleMusicEmbedSpecial

.. autoclass:: AppleMusicEmbedSpecial
    :members:
    :inherited-members:

.. attributetable:: StreamableEmbedSpecial

.. autoclass:: StreamableEmbedSpecial
    :members:
    :inherited-members:

.. attributetable:: ImageEmbed

.. autoclass:: ImageEmbed
    :members:
    :inherited-members:

.. attributetable:: VideoEmbed

.. autoclass:: VideoEmbed
    :members:
    :inherited-members:

.. attributetable:: WebsiteEmbed

.. autoclass:: WebsiteEmbed
    :members:
    :inherited-members:

.. attributetable:: StatelessTextEmbed

.. autoclass:: StatelessTextEmbed
    :members:
    :inherited-members:

.. attributetable:: TextEmbed

.. autoclass:: TextEmbed
    :members:
    :inherited-members:

.. attributetable:: NoneEmbed

.. autoclass:: NoneEmbed
    :members:
    :inherited-members:

.. class:: EmbedSpecial

    A union of all embed special types.

    The following classes are included in this union:
    
    - :class:`.GifEmbedSpecial`
    - :class:`.YouTubeEmbedSpecial`
    - :class:`.LightspeedEmbedSpecial`
    - :class:`.TwitchEmbedSpecial`
    - :class:`.SpotifyEmbedSpecial`
    - :class:`.SoundcloudEmbedSpecial`
    - :class:`.BandcampEmbedSpecial`
    - :class:`.AppleMusicEmbedSpecial`
    - :class:`.StreamableEmbedSpecial`

.. class:: StatelessEmbed

    A union of all stateless embed types.

    The following classes are included in this union:
    
    - :class:`.WebsiteEmbed`
    - :class:`.ImageEmbed`
    - :class:`.VideoEmbed`
    - :class:`.StatelessTextEmbed`
    - :class:`.NoneEmbed`

.. class:: Embed

    A union of all embed types.

    The following classes are included in this union:
    
    - :class:`.WebsiteEmbed`
    - :class:`.ImageEmbed`
    - :class:`.VideoEmbed`
    - :class:`.TextEmbed`
    - :class:`.NoneEmbed`

Emoji
~~~~~

.. attributetable:: BaseEmoji

.. autoclass:: BaseEmoji
    :members:
    :inherited-members:

.. attributetable:: ServerEmoji

.. autoclass:: ServerEmoji
    :members:
    :inherited-members:

.. attributetable:: DetachedEmoji

.. autoclass:: DetachedEmoji
    :members:
    :inherited-members:

.. class:: Emoji
    A union of all emoji types.

    The following classes are included in this union:
    
    - :class:`.ServerEmoji`
    - :class:`.DetachedEmoji`

.. class:: ResolvableEmoji
    A union of either :class:`.BaseEmoji` or :class:`str`.

.. autofunction:: resolve_emoji

PermissionOverride
~~~~~~~~~~~~~~~~~~

.. attributetable:: PermissionOverride

.. autoclass:: PermissionOverride
    :members:

ReadState
~~~~~~~~~

.. attributetable:: ReadState

.. autoclass:: ReadState
    :members:
    :inherited-members:

Server
~~~~~~

.. attributetable:: BaseServer

.. autoclass:: BaseServer
    :members:
    :inherited-members:

.. attributetable:: PartialServer

.. autoclass:: PartialServer
    :members:
    :inherited-members:

.. attributetable:: Server

.. autoclass:: Server
    :members:
    :inherited-members:

.. attributetable:: Category

.. autoclass:: Category
    :members:

.. attributetable:: SystemMessageChannels

.. autoclass:: SystemMessageChannels
    :members:

Member
~~~~~~

.. attributetable:: BaseMember

.. autoclass:: BaseMember
    :members:
    :inherited-members:

.. attributetable:: PartialMember

.. autoclass:: PartialMember
    :members:
    :inherited-members:

.. attributetable:: Member

.. autoclass:: Member
    :members:
    :inherited-members:

.. attributetable:: MemberList

.. autoclass:: MemberList
    :members:

SystemEvent
~~~~~~~~~~~

.. attributetable:: BaseSystemEvent

.. autoclass:: BaseSystemEvent
    :members:

.. attributetable:: TextSystemEvent

.. autoclass:: TextSystemEvent
    :members:
    :inherited-members:

.. attributetable:: StatelessUserAddedSystemEvent

.. autoclass:: StatelessUserAddedSystemEvent
    :members:
    :inherited-members:

.. attributetable:: UserAddedSystemEvent

.. autoclass:: UserAddedSystemEvent
    :members:
    :inherited-members:

.. attributetable:: StatelessUserRemovedSystemEvent

.. autoclass:: StatelessUserRemovedSystemEvent
    :members:
    :inherited-members:

.. attributetable:: UserRemovedSystemEvent

.. autoclass:: UserRemovedSystemEvent
    :members:
    :inherited-members:

.. attributetable:: StatelessUserJoinedSystemEvent

.. autoclass:: StatelessUserJoinedSystemEvent
    :members:
    :inherited-members:

.. attributetable:: UserJoinedSystemEvent

.. autoclass:: UserJoinedSystemEvent
    :members:
    :inherited-members:

.. attributetable:: StatelessUserLeftSystemEvent

.. autoclass:: StatelessUserLeftSystemEvent
    :members:
    :inherited-members:

.. attributetable:: UserLeftSystemEvent

.. autoclass:: UserLeftSystemEvent
    :members:
    :inherited-members:

.. attributetable:: StatelessUserKickedSystemEvent

.. autoclass:: StatelessUserKickedSystemEvent
    :members:
    :inherited-members:

.. attributetable:: UserKickedSystemEvent

.. autoclass:: UserKickedSystemEvent
    :members:
    :inherited-members:

.. attributetable:: StatelessUserBannedSystemEvent

.. autoclass:: StatelessUserBannedSystemEvent
    :members:
    :inherited-members:

.. attributetable:: UserBannedSystemEvent

.. autoclass:: UserBannedSystemEvent
    :members:
    :inherited-members:

.. attributetable:: StatelessChannelRenamedSystemEvent

.. autoclass:: StatelessChannelRenamedSystemEvent
    :members:
    :inherited-members:

.. attributetable:: ChannelRenamedSystemEvent

.. autoclass:: ChannelRenamedSystemEvent
    :members:
    :inherited-members:

.. attributetable:: StatelessChannelDescriptionChangedSystemEvent

.. autoclass:: StatelessChannelDescriptionChangedSystemEvent
    :members:
    :inherited-members:

.. attributetable:: ChannelDescriptionChangedSystemEvent

.. autoclass:: ChannelDescriptionChangedSystemEvent
    :members:
    :inherited-members:

.. attributetable:: StatelessChannelIconChangedSystemEvent

.. autoclass:: StatelessChannelIconChangedSystemEvent
    :members:
    :inherited-members:

.. attributetable:: ChannelIconChangedSystemEvent

.. autoclass:: ChannelIconChangedSystemEvent
    :members:
    :inherited-members:

.. attributetable:: StatelessChannelOwnershipChangedSystemEvent

.. autoclass:: StatelessChannelOwnershipChangedSystemEvent
    :members:
    :inherited-members:

.. attributetable:: ChannelOwnershipChangedSystemEvent

.. autoclass:: ChannelOwnershipChangedSystemEvent
    :members:
    :inherited-members:

.. attributetable:: StatelessMessagePinnedSystemEvent

.. autoclass:: StatelessMessagePinnedSystemEvent
    :members:
    :inherited-members:

.. attributetable:: MessagePinnedSystemEvent

.. autoclass:: MessagePinnedSystemEvent
    :members:
    :inherited-members:

.. attributetable:: StatelessMessageUnpinnedSystemEvent

.. autoclass:: StatelessMessageUnpinnedSystemEvent
    :members:
    :inherited-members:

.. attributetable:: MessageUnpinnedSystemEvent

.. autoclass:: MessageUnpinnedSystemEvent
    :members:
    :inherited-members:

.. class:: StatelessSystemEvent

    A union of all stateless system events that message may hold.

    The following classes are included in this union:

    - :class:`.TextSystemEvent`
    - :class:`.StatelessUserAddedSystemEvent`
    - :class:`.StatelessUserRemovedSystemEvent`
    - :class:`.StatelessUserJoinedSystemEvent`
    - :class:`.StatelessUserLeftSystemEvent`
    - :class:`.StatelessUserKickedSystemEvent`
    - :class:`.StatelessUserBannedSystemEvent`
    - :class:`.StatelessChannelRenamedSystemEvent`
    - :class:`.StatelessChannelDescriptionChangedSystemEvent`
    - :class:`.StatelessChannelIconChangedSystemEvent`
    - :class:`.StatelessChannelOwnershipChangedSystemEvent`
    - :class:`.StatelessMessagePinnedSystemEvent`
    - :class:`.StatelessMessageUnpinnedSystemEvent`

.. class:: SystemEvent

    A union of all system events that message may hold.

    The following classes are included in this union:

    - :class:`.TextSystemEvent`
    - :class:`.UserAddedSystemEvent`
    - :class:`.UserRemovedSystemEvent`
    - :class:`.UserJoinedSystemEvent`
    - :class:`.UserLeftSystemEvent`
    - :class:`.UserKickedSystemEvent`
    - :class:`.UserBannedSystemEvent`
    - :class:`.ChannelRenamedSystemEvent`
    - :class:`.ChannelDescriptionChangedSystemEvent`
    - :class:`.ChannelIconChangedSystemEvent`
    - :class:`.ChannelOwnershipChangedSystemEvent`
    - :class:`.MessagePinnedSystemEvent`
    - :class:`.MessageUnpinnedSystemEvent`

Message
~~~~~~~

.. attributetable:: BaseMessage

.. autoclass:: BaseMessage
    :members:

.. attributetable:: PartialMessage

.. autoclass:: PartialMessage
    :members:

.. attributetable:: MessageAppendData

.. autoclass:: MessageAppendData
    :members:

.. attributetable:: Message

.. autoclass:: Message
    :members:
    :inherited-members:

.. attributetable:: Reply

.. autoclass:: Reply
    :members:

.. attributetable:: MessageInteractions

.. autoclass:: MessageInteractions
    :members:

.. attributetable:: MessageWebhook

.. autoclass:: MessageWebhook
    :members:

Role
~~~~

.. attributetable:: BaseRole

.. autoclass:: BaseRole
    :members:
    :inherited-members:

.. attributetable:: PartialRole

.. autoclass:: PartialRole
    :members:
    :inherited-members:

.. attributetable:: Role

.. autoclass:: Role
    :members:
    :inherited-members:

Webhook
~~~~~~~

.. attributetable:: BaseWebhook

.. autoclass:: BaseWebhook
    :members:
    :inherited-members:

.. attributetable:: PartialWebhook

.. autoclass:: PartialWebhook
    :members:
    :inherited-members:

.. attributetable:: Webhook

.. autoclass:: Webhook
    :members:
    :inherited-members:

Settings
~~~~~~~~

.. attributetable:: UserSettings

.. autoclass:: UserSettings
    :members:

.. attributetable:: AndroidUserSettings

.. autoclass:: AndroidUserSettings
    :members:

.. attributetable:: ReviteNotificationOptions

.. autoclass:: ReviteNotificationOptions
    :members:

.. attributetable:: ReviteThemeVariable

.. autoclass:: ReviteThemeVariable
    :members:

.. attributetable:: ReviteUserSettings

.. autoclass:: ReviteUserSettings
    :members:

.. attributetable:: JoltUserSettings

.. autoclass:: JoltUserSettings
    :members: