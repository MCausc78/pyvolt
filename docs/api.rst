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

EmptyCache
~~~~~~~~~~

.. attributetable:: EmptyCache

.. autoclass:: EmptyCache
    :show-inheritance:
    :inherited-members:

MapCache
~~~~~~~~

.. attributetable:: MapCache

.. autoclass:: MapCache
    :show-inheritance:
    :inherited-members:

CacheContextType
~~~~~~~~~~~~~~~~

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
    .. attribute:: voice_channel_move_event

        The context relates to :class:`.VoiceChannelMoveEvent` event.
    .. attribute:: user_voice_state_update_event

        The context relates to :class:`.UserVoiceStateUpdateEvent` event.
    .. attribute:: authenticated_event

        The context relates to :class:`.AuthenticatedEvent` event.

BaseCacheContext
~~~~~~~~~~~~~~~~

.. attributetable:: BaseCacheContext

.. autoclass:: BaseCacheContext
    :members:

UndefinedCacheContext
~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: UndefinedCacheContext

.. autoclass:: UndefinedCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

DetachedEmojiCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: DetachedEmojiCacheContext

.. autoclass:: DetachedEmojiCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

MessageCacheContext
~~~~~~~~~~~~~~~~~~~

.. attributetable:: MessageCacheContext

.. autoclass:: MessageCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

ServerCacheContext
~~~~~~~~~~~~~~~~~~

.. attributetable:: ServerCacheContext

.. autoclass:: ServerCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

ServerEmojiCacheContext
~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ServerEmojiCacheContext

.. autoclass:: ServerEmojiCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

UserCacheContext
~~~~~~~~~~~~~~~~

.. attributetable:: UserCacheContext

.. autoclass:: UserCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

PrivateChannelCreateEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: PrivateChannelCreateEventCacheContext

.. autoclass:: PrivateChannelCreateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

ServerChannelCreateEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ServerChannelCreateEventCacheContext

.. autoclass:: ServerChannelCreateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

ChannelUpdateEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ChannelUpdateEventCacheContext

.. autoclass:: ChannelUpdateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

ChannelDeleteEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ChannelDeleteEventCacheContext

.. autoclass:: ChannelDeleteEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

GroupRecipientAddEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: GroupRecipientAddEventCacheContext

.. autoclass:: GroupRecipientAddEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

GroupRecipientRemoveEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: GroupRecipientRemoveEventCacheContext

.. autoclass:: GroupRecipientRemoveEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

ChannelStartTypingEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ChannelStartTypingEventCacheContext

.. autoclass:: ChannelStartTypingEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

ChannelStopTypingEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ChannelStopTypingEventCacheContext

.. autoclass:: ChannelStopTypingEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

MessageAckEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: MessageAckEventCacheContext

.. autoclass:: MessageAckEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

MessageCreateEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: MessageCreateEventCacheContext

.. autoclass:: MessageCreateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

MessageUpdateEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: MessageUpdateEventCacheContext

.. autoclass:: MessageUpdateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

MessageAppendEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: MessageAppendEventCacheContext

.. autoclass:: MessageAppendEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

MessageDeleteEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: MessageDeleteEventCacheContext

.. autoclass:: MessageDeleteEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

MessageReactEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: MessageReactEventCacheContext

.. autoclass:: MessageReactEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

MessageUnreactEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: MessageUnreactEventCacheContext

.. autoclass:: MessageUnreactEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

MessageClearReactionEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: MessageClearReactionEventCacheContext

.. autoclass:: MessageClearReactionEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

MessageDeleteBulkEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: MessageDeleteBulkEventCacheContext

.. autoclass:: MessageDeleteBulkEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

ServerCreateEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ServerCreateEventCacheContext

.. autoclass:: ServerCreateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

ServerEmojiCreateEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ServerEmojiCreateEventCacheContext

.. autoclass:: ServerEmojiCreateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

ServerEmojiDeleteEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ServerEmojiDeleteEventCacheContext

.. autoclass:: ServerEmojiDeleteEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

ServerUpdateEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ServerUpdateEventCacheContext

.. autoclass:: ServerUpdateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

ServerDeleteEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ServerDeleteEventCacheContext

.. autoclass:: ServerDeleteEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

ServerMemberJoinEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ServerMemberJoinEventCacheContext

.. autoclass:: ServerMemberJoinEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

ServerMemberUpdateEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ServerMemberUpdateEventCacheContext

.. autoclass:: ServerMemberUpdateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

ServerMemberRemoveEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ServerMemberRemoveEventCacheContext

.. autoclass:: ServerMemberRemoveEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

RawServerRoleUpdateEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: RawServerRoleUpdateEventCacheContext

.. autoclass:: RawServerRoleUpdateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

ServerRoleDeleteEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ServerRoleDeleteEventCacheContext

.. autoclass:: ServerRoleDeleteEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

ReportCreateEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ReportCreateEventCacheContext

.. autoclass:: ReportCreateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

UserUpdateEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: UserUpdateEventCacheContext

.. autoclass:: UserUpdateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

UserRelationshipUpdateEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: UserRelationshipUpdateEventCacheContext

.. autoclass:: UserRelationshipUpdateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

UserSettingsUpdateEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: UserSettingsUpdateEventCacheContext

.. autoclass:: UserSettingsUpdateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

UserPlatformWipeEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: UserPlatformWipeEventCacheContext

.. autoclass:: UserPlatformWipeEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

WebhookCreateEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: WebhookCreateEventCacheContext

.. autoclass:: WebhookCreateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

WebhookUpdateEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: WebhookUpdateEventCacheContext

.. autoclass:: WebhookUpdateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

WebhookDeleteEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: WebhookDeleteEventCacheContext

.. autoclass:: WebhookDeleteEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

SessionCreateEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: SessionCreateEventCacheContext

.. autoclass:: SessionCreateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

SessionDeleteEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: SessionDeleteEventCacheContext

.. autoclass:: SessionDeleteEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

SessionDeleteAllEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: SessionDeleteAllEventCacheContext

.. autoclass:: SessionDeleteAllEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

VoiceChannelJoinEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: VoiceChannelJoinEventCacheContext

.. autoclass:: VoiceChannelJoinEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

VoiceChannelLeaveEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: VoiceChannelLeaveEventCacheContext

.. autoclass:: VoiceChannelLeaveEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

VoiceChannelMoveEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: VoiceChannelMoveEventCacheContext

.. autoclass:: VoiceChannelMoveEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

UserVoiceStateUpdateEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: UserVoiceStateUpdateEventCacheContext

.. autoclass:: UserVoiceStateUpdateEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

AuthenticatedEventCacheContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: AuthenticatedEventCacheContext

.. autoclass:: AuthenticatedEventCacheContext
    :show-inheritance:
    :members:
    :inherited-members:

.. _revolt-api-events:

Events
------

BaseEvent
~~~~~~~~~

.. attributetable:: BaseEvent

.. autoclass:: BaseEvent
    :members:
    :inherited-members:

ShardEvent
~~~~~~~~~~

.. attributetable:: ShardEvent

.. autoclass:: ShardEvent
    :members:
    :inherited-members:

.. attributetable:: ReadyEvent

.. autoclass:: ReadyEvent
    :members:
    :inherited-members:

BaseChannelCreateEvent
~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: BaseChannelCreateEvent

.. autoclass:: BaseChannelCreateEvent
    :members:
    :inherited-members:

PrivateChannelCreateEvent
~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: PrivateChannelCreateEvent

.. autoclass:: PrivateChannelCreateEvent
    :show-inheritance:
    :members:
    :inherited-members:

ServerChannelCreateEvent
~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ServerChannelCreateEvent

.. autoclass:: ServerChannelCreateEvent
    :show-inheritance:
    :members:
    :inherited-members:

ChannelCreateEvent
~~~~~~~~~~~~~~~~~~

.. class:: ChannelCreateEvent
    A union of private/server channel create events.
    
    The following classes are included in this union:

    - :class:`.PrivateChannelCreateEvent`
    - :class:`.ServerChannelCreateEvent`

ChannelUpdateEvent
~~~~~~~~~~~~~~~~~~

.. attributetable:: ChannelUpdateEvent

.. autoclass:: ChannelUpdateEvent
    :members:
    :inherited-members:

ChannelDeleteEvent
~~~~~~~~~~~~~~~~~~

.. attributetable:: ChannelDeleteEvent

.. autoclass:: ChannelDeleteEvent
    :members:
    :inherited-members:

GroupRecipientAddEvent
~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: GroupRecipientAddEvent

.. autoclass:: GroupRecipientAddEvent
    :members:
    :inherited-members:

GroupRecipientRemoveEvent
~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: GroupRecipientRemoveEvent

.. autoclass:: GroupRecipientRemoveEvent
    :members:
    :inherited-members:

ChannelStartTypingEvent
~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ChannelStartTypingEvent

.. autoclass:: ChannelStartTypingEvent
    :members:
    :inherited-members:

ChannelStopTypingEvent
~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ChannelStopTypingEvent

.. autoclass:: ChannelStopTypingEvent
    :members:
    :inherited-members:

MessageAckEvent
~~~~~~~~~~~~~~~

.. attributetable:: MessageAckEvent

.. autoclass:: MessageAckEvent
    :members:
    :inherited-members:

MessageCreateEvent
~~~~~~~~~~~~~~~~~~

.. attributetable:: MessageCreateEvent

.. autoclass:: MessageCreateEvent
    :members:
    :inherited-members:

MessageUpdateEvent
~~~~~~~~~~~~~~~~~~

.. attributetable:: MessageUpdateEvent

.. autoclass:: MessageUpdateEvent
    :members:
    :inherited-members:

MessageAppendEvent
~~~~~~~~~~~~~~~~~~

.. attributetable:: MessageAppendEvent

.. autoclass:: MessageAppendEvent
    :members:
    :inherited-members:

MessageDeleteEvent
~~~~~~~~~~~~~~~~~~

.. attributetable:: MessageDeleteEvent

.. autoclass:: MessageDeleteEvent
    :members:
    :inherited-members:

MessageReactEvent
~~~~~~~~~~~~~~~~~

.. attributetable:: MessageReactEvent

.. autoclass:: MessageReactEvent
    :members:
    :inherited-members:

MessageUnreactEvent
~~~~~~~~~~~~~~~~~~~

.. attributetable:: MessageUnreactEvent

.. autoclass:: MessageUnreactEvent
    :members:
    :inherited-members:

MessageClearReactionEvent
~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: MessageClearReactionEvent

.. autoclass:: MessageClearReactionEvent
    :members:
    :inherited-members:

MessageDeleteBulkEvent
~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: MessageDeleteBulkEvent

.. autoclass:: MessageDeleteBulkEvent
    :members:
    :inherited-members:

ServerCreateEvent
~~~~~~~~~~~~~~~~~

.. attributetable:: ServerCreateEvent

.. autoclass:: ServerCreateEvent
    :members:
    :inherited-members:

ServerEmojiCreateEvent
~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ServerEmojiCreateEvent

.. autoclass:: ServerEmojiCreateEvent
    :members:
    :inherited-members:

ServerEmojiDeleteEvent
~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ServerEmojiDeleteEvent

.. autoclass:: ServerEmojiDeleteEvent
    :members:
    :inherited-members:

ServerUpdateEvent
~~~~~~~~~~~~~~~~~

.. attributetable:: ServerUpdateEvent

.. autoclass:: ServerUpdateEvent
    :members:
    :inherited-members:

ServerDeleteEvent
~~~~~~~~~~~~~~~~~

.. attributetable:: ServerDeleteEvent

.. autoclass:: ServerDeleteEvent
    :members:
    :inherited-members:

ServerMemberJoinEvent
~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ServerMemberJoinEvent

.. autoclass:: ServerMemberJoinEvent
    :members:
    :inherited-members:

ServerMemberUpdateEvent
~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ServerMemberUpdateEvent

.. autoclass:: ServerMemberUpdateEvent
    :members:
    :inherited-members:

ServerMemberRemoveEvent
~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ServerMemberRemoveEvent

.. autoclass:: ServerMemberRemoveEvent
    :members:
    :inherited-members:

RawServerRoleUpdateEvent
~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: RawServerRoleUpdateEvent

.. autoclass:: RawServerRoleUpdateEvent
    :members:
    :inherited-members:

ServerRoleDeleteEvent
~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ServerRoleDeleteEvent

.. autoclass:: ServerRoleDeleteEvent
    :members:
    :inherited-members:

ReportCreateEvent
~~~~~~~~~~~~~~~~~

.. attributetable:: ReportCreateEvent

.. autoclass:: ReportCreateEvent
    :members:
    :inherited-members:

UserUpdateEvent
~~~~~~~~~~~~~~~

.. attributetable:: UserUpdateEvent

.. autoclass:: UserUpdateEvent
    :members:
    :inherited-members:

UserRelationshipUpdateEvent
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: UserRelationshipUpdateEvent

.. autoclass:: UserRelationshipUpdateEvent
    :members:
    :inherited-members:

UserSettingsUpdateEvent
~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: UserSettingsUpdateEvent

.. autoclass:: UserSettingsUpdateEvent
    :members:
    :inherited-members:

UserPlatformWipeEvent
~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: UserPlatformWipeEvent

.. autoclass:: UserPlatformWipeEvent
    :members:
    :inherited-members:

WebhookCreateEvent
~~~~~~~~~~~~~~~~~~

.. attributetable:: WebhookCreateEvent

.. autoclass:: WebhookCreateEvent
    :members:
    :inherited-members:

WebhookUpdateEvent
~~~~~~~~~~~~~~~~~~

.. attributetable:: WebhookUpdateEvent

.. autoclass:: WebhookUpdateEvent
    :members:
    :inherited-members:

WebhookDeleteEvent
~~~~~~~~~~~~~~~~~~

.. attributetable:: WebhookDeleteEvent

.. autoclass:: WebhookDeleteEvent
    :members:
    :inherited-members:

AuthifierEvent
~~~~~~~~~~~~~~

.. attributetable:: AuthifierEvent

.. autoclass:: AuthifierEvent
    :members:
    :inherited-members:

SessionCreateEvent
~~~~~~~~~~~~~~~~~~

.. attributetable:: SessionCreateEvent

.. autoclass:: SessionCreateEvent
    :show-inheritance:
    :members:
    :inherited-members:

SessionDeleteEvent
~~~~~~~~~~~~~~~~~~

.. attributetable:: SessionDeleteEvent

.. autoclass:: SessionDeleteEvent
    :show-inheritance:
    :members:
    :inherited-members:

SessionDeleteAllEvent
~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: SessionDeleteAllEvent

.. autoclass:: SessionDeleteAllEvent
    :show-inheritance:
    :members:
    :inherited-members:

LogoutEvent
~~~~~~~~~~~

.. attributetable:: LogoutEvent

.. autoclass:: LogoutEvent
    :members:
    :inherited-members:

VoiceChannelJoinEvent
~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: VoiceChannelJoinEvent

.. autoclass:: VoiceChannelJoinEvent
    :members:
    :inherited-members:

VoiceChannelLeaveEvent
~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: VoiceChannelLeaveEvent

.. autoclass:: VoiceChannelLeaveEvent
    :members:
    :inherited-members:

VoiceChannelMoveEvent
~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: VoiceChannelMoveEvent

.. autoclass:: VoiceChannelMoveEvent
    :members:
    :inherited-members:

UserVoiceStateUpdateEvent
~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: UserVoiceStateUpdateEvent

.. autoclass:: UserVoiceStateUpdateEvent
    :members:
    :inherited-members:

AuthenticatedEvent
~~~~~~~~~~~~~~~~~~

.. attributetable:: AuthenticatedEvent

.. autoclass:: AuthenticatedEvent
    :members:
    :inherited-members:

BeforeConnectEvent
~~~~~~~~~~~~~~~~~~

.. attributetable:: BeforeConnectEvent

.. autoclass:: BeforeConnectEvent
    :members:
    :inherited-members:

AfterConnectEvent
~~~~~~~~~~~~~~~~~

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

StatelessAsset
~~~~~~~~~~~~~~

.. attributetable:: StatelessAsset

.. autoclass:: StatelessAsset
    :members:

Asset
~~~~~

.. attributetable:: Asset

.. autoclass:: Asset
    :show-inheritance:
    :members:
    :inherited-members:

.. attributetable:: AssetMetadata

.. autoclass:: AssetMetadata
    :members:

BaseUser
~~~~~~~~

.. attributetable:: BaseUser

.. autoclass:: BaseUser
    :members:

BotUserMetadata
~~~~~~~~~~~~~~~

.. attributetable:: BotUserMetadata

.. autoclass:: BotUserMetadata
    :members:
    :inherited-members:

DisplayUser
~~~~~~~~~~~

.. attributetable:: DisplayUser

.. autoclass:: DisplayUser
    :members:
    :inherited-members:

PartialUser
~~~~~~~~~~~

.. attributetable:: PartialUser

.. autoclass:: PartialUser
    :members:
    :inherited-members:


User
~~~~

.. attributetable:: User

.. autoclass:: User
    :members:
    :inherited-members:

OwnUser
~~~~~~~

.. attributetable:: OwnUser

.. autoclass:: OwnUser
    :members:
    :inherited-members:
    :exclude-members: accept_friend_request, block, deny_friend_request, mutual_friend_ids, mutual_server_ids, mutuals, remove_friend, report, send_friend_request, unblock

BaseChannel
~~~~~~~~~~~

.. attributetable:: BaseChannel

.. autoclass:: BaseChannel
    :members:

PartialChannel
~~~~~~~~~~~~~~

.. attributetable:: PartialChannel

.. autoclass:: PartialChannel
    :members:
    :inherited-members:

SavedMessagesChannel
~~~~~~~~~~~~~~~~~~~~

.. attributetable:: SavedMessagesChannel

.. autoclass:: SavedMessagesChannel
    :members:
    :inherited-members:

DMChannel
~~~~~~~~~

.. attributetable:: DMChannel

.. autoclass:: DMChannel
    :members:
    :inherited-members:

GroupChannel
~~~~~~~~~~~~

.. attributetable:: GroupChannel

.. autoclass:: GroupChannel
    :members:
    :inherited-members:

BaseServerChannel
~~~~~~~~~~~~~~~~~

.. attributetable:: BaseServerChannel

.. autoclass:: BaseServerChannel
    :members:
    :inherited-members:

ChannelVoiceMetadata
~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ChannelVoiceMetadata

.. autoclass:: ChannelVoiceMetadata
    :members:

TextChannel
~~~~~~~~~~~

.. attributetable:: TextChannel

.. autoclass:: TextChannel
    :members:
    :inherited-members:

VoiceChannel
~~~~~~~~~~~~

.. attributetable:: VoiceChannel

.. autoclass:: VoiceChannel
    :members:
    :inherited-members:

PrivateChannel
~~~~~~~~~~~~~~

.. class:: PrivateChannel
    A union of all channels that do not belong to a server.
    
    The following classes are included in this union:

    - :class:`.SavedMessagesChannel`
    - :class:`.DMChannel`
    - :class:`.GroupChannel`

ServerChannel
~~~~~~~~~~~~~
    
.. class:: ServerChannel
    A union of all channels that belong to a server.
    
    The following classes are included in this union:

    - :class:`.TextChannel`
    - :class:`.VoiceChannel`

TextableChannel
~~~~~~~~~~~~~~~

.. class:: TextableChannel
    A union of all channels that can have messages in them.
    
    The following classes are included in this union:
    
    - :class:`.SavedMessagesChannel`
    - :class:`.DMChannel`
    - :class:`.GroupChannel`
    - :class:`.TextChannel`
    - :class:`.VoiceChannel`

Channel
~~~~~~~

.. class:: Channel
    A union of all channels.

    Union types such as this exist to help determine which exact channel type has some field during development.

    The following classes are included in this union:
    
    - :class:`.SavedMessagesChannel`
    - :class:`.DMChannel`
    - :class:`.GroupChannel`
    - :class:`.TextChannel`
    - :class:`.VoiceChannel`

ChannelVoiceStateContainer
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ChannelVoiceStateContainer

.. autoclass:: ChannelVoiceStateContainer
    :members:

BaseEmbed
~~~~~~~~~

.. attributetable:: BaseEmbed

.. autoclass:: BaseEmbed
    :members:

BaseEmbedSpecial
~~~~~~~~~~~~~~~~

.. attributetable:: BaseEmbedSpecial

.. autoclass:: BaseEmbedSpecial
    :members:

NoneEmbedSpecial
~~~~~~~~~~~~~~~~

.. attributetable:: NoneEmbedSpecial

.. autoclass:: NoneEmbedSpecial
    :members:
    :inherited-members:

GIFEmbedSpecial
~~~~~~~~~~~~~~~

.. attributetable:: GIFEmbedSpecial

.. autoclass:: GIFEmbedSpecial
    :members:
    :inherited-members:

YouTubeEmbedSpecial
~~~~~~~~~~~~~~~~~~~

.. attributetable:: YouTubeEmbedSpecial

.. autoclass:: YouTubeEmbedSpecial
    :members:
    :inherited-members:

LightspeedEmbedSpecial
~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: LightspeedEmbedSpecial

.. autoclass:: LightspeedEmbedSpecial
    :members:
    :inherited-members:

TwitchEmbedSpecial
~~~~~~~~~~~~~~~~~~

.. attributetable:: TwitchEmbedSpecial

.. autoclass:: TwitchEmbedSpecial
    :members:
    :inherited-members:

SpotifyEmbedSpecial
~~~~~~~~~~~~~~~~~~~

.. attributetable:: SpotifyEmbedSpecial

.. autoclass:: SpotifyEmbedSpecial
    :members:
    :inherited-members:

SoundcloudEmbedSpecial
~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: SoundcloudEmbedSpecial

.. autoclass:: SoundcloudEmbedSpecial
    :members:
    :inherited-members:

BandcampEmbedSpecial
~~~~~~~~~~~~~~~~~~~~

.. attributetable:: BandcampEmbedSpecial

.. autoclass:: BandcampEmbedSpecial
    :members:
    :inherited-members:

AppleMusicEmbedSpecial
~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: AppleMusicEmbedSpecial

.. autoclass:: AppleMusicEmbedSpecial
    :members:
    :inherited-members:

StreamableEmbedSpecial
~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: StreamableEmbedSpecial

.. autoclass:: StreamableEmbedSpecial
    :members:
    :inherited-members:

ImageEmbed
~~~~~~~~~~

.. attributetable:: ImageEmbed

.. autoclass:: ImageEmbed
    :members:
    :inherited-members:

VideoEmbed
~~~~~~~~~~

.. attributetable:: VideoEmbed

.. autoclass:: VideoEmbed
    :members:
    :inherited-members:

WebsiteEmbed
~~~~~~~~~~~~

.. attributetable:: WebsiteEmbed

.. autoclass:: WebsiteEmbed
    :members:
    :inherited-members:

StatelessTextEmbed
~~~~~~~~~~~~~~~~~~

.. attributetable:: StatelessTextEmbed

.. autoclass:: StatelessTextEmbed
    :members:
    :inherited-members:

TextEmbed
~~~~~~~~~

.. attributetable:: TextEmbed

.. autoclass:: TextEmbed
    :members:
    :inherited-members:

NoneEmbed
~~~~~~~~~

.. attributetable:: NoneEmbed

.. autoclass:: NoneEmbed
    :members:
    :inherited-members:

EmbedSpecial
~~~~~~~~~~~~

.. class:: EmbedSpecial

    A union of all embed special types.

    The following classes are included in this union:
    
    - :class:`.GIFEmbedSpecial`
    - :class:`.YouTubeEmbedSpecial`
    - :class:`.LightspeedEmbedSpecial`
    - :class:`.TwitchEmbedSpecial`
    - :class:`.SpotifyEmbedSpecial`
    - :class:`.SoundcloudEmbedSpecial`
    - :class:`.BandcampEmbedSpecial`
    - :class:`.AppleMusicEmbedSpecial`
    - :class:`.StreamableEmbedSpecial`

StatelessEmbed
~~~~~~~~~~~~~~

.. class:: StatelessEmbed

    A union of all stateless embed types.

    The following classes are included in this union:
    
    - :class:`.WebsiteEmbed`
    - :class:`.ImageEmbed`
    - :class:`.VideoEmbed`
    - :class:`.StatelessTextEmbed`
    - :class:`.NoneEmbed`

Embed
~~~~~

.. class:: Embed

    A union of all embed types.

    The following classes are included in this union:
    
    - :class:`.WebsiteEmbed`
    - :class:`.ImageEmbed`
    - :class:`.VideoEmbed`
    - :class:`.TextEmbed`
    - :class:`.NoneEmbed`

BaseEmoji
~~~~~~~~~

.. attributetable:: BaseEmoji

.. autoclass:: BaseEmoji
    :members:
    :inherited-members:

ServerEmoji
~~~~~~~~~~~

.. attributetable:: ServerEmoji

.. autoclass:: ServerEmoji
    :members:
    :inherited-members:

DetachedEmoji
~~~~~~~~~~~~~

.. attributetable:: DetachedEmoji

.. autoclass:: DetachedEmoji
    :members:
    :inherited-members:

Emoji
~~~~~

.. class:: Emoji
    A union of all emoji types.

    The following classes are included in this union:
    
    - :class:`.ServerEmoji`
    - :class:`.DetachedEmoji`

ResolvableEmoji
~~~~~~~~~~~~~~~

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

BaseServer
~~~~~~~~~~

.. attributetable:: BaseServer

.. autoclass:: BaseServer
    :members:
    :inherited-members:

PartialServer
~~~~~~~~~~~~~

.. attributetable:: PartialServer

.. autoclass:: PartialServer
    :members:
    :inherited-members:

Server
~~~~~~

.. attributetable:: Server

.. autoclass:: Server
    :members:
    :inherited-members:

Category
~~~~~~~~

.. attributetable:: Category

.. autoclass:: Category
    :members:

.. attributetable:: SystemMessageChannels

.. autoclass:: SystemMessageChannels
    :members:

BaseMember
~~~~~~~~~~

.. attributetable:: BaseMember

.. autoclass:: BaseMember
    :members:
    :inherited-members:

PartialMember
~~~~~~~~~~~~~

.. attributetable:: PartialMember

.. autoclass:: PartialMember
    :members:
    :inherited-members:

Member
~~~~~~

.. attributetable:: Member

.. autoclass:: Member
    :members:
    :inherited-members:

MemberList
~~~~~~~~~~

.. attributetable:: MemberList

.. autoclass:: MemberList
    :members:

BaseSystemEvent
~~~~~~~~~~~~~~~

.. attributetable:: BaseSystemEvent

.. autoclass:: BaseSystemEvent
    :members:

TextSystemEvent
~~~~~~~~~~~~~~~

.. attributetable:: TextSystemEvent

.. autoclass:: TextSystemEvent
    :members:
    :inherited-members:

StatelessUserAddedSystemEvent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: StatelessUserAddedSystemEvent

.. autoclass:: StatelessUserAddedSystemEvent
    :members:
    :inherited-members:

UserAddedSystemEvent
~~~~~~~~~~~~~~~~~~~~

.. attributetable:: UserAddedSystemEvent

.. autoclass:: UserAddedSystemEvent
    :members:
    :inherited-members:

StatelessUserRemovedSystemEvent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: StatelessUserRemovedSystemEvent

.. autoclass:: StatelessUserRemovedSystemEvent
    :members:
    :inherited-members:

UserRemovedSystemEvent
~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: UserRemovedSystemEvent

.. autoclass:: UserRemovedSystemEvent
    :members:
    :inherited-members:

StatelessUserJoinedSystemEvent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: StatelessUserJoinedSystemEvent

.. autoclass:: StatelessUserJoinedSystemEvent
    :members:
    :inherited-members:

UserJoinedSystemEvent
~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: UserJoinedSystemEvent

.. autoclass:: UserJoinedSystemEvent
    :members:
    :inherited-members:

StatelessUserLeftSystemEvent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: StatelessUserLeftSystemEvent

.. autoclass:: StatelessUserLeftSystemEvent
    :members:
    :inherited-members:

UserLeftSystemEvent
~~~~~~~~~~~~~~~~~~~

.. attributetable:: UserLeftSystemEvent

.. autoclass:: UserLeftSystemEvent
    :members:
    :inherited-members:

StatelessUserKickedSystemEvent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: StatelessUserKickedSystemEvent

.. autoclass:: StatelessUserKickedSystemEvent
    :members:
    :inherited-members:

UserKickedSystemEvent
~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: UserKickedSystemEvent

.. autoclass:: UserKickedSystemEvent
    :members:
    :inherited-members:


StatelessUserBannedSystemEvent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: StatelessUserBannedSystemEvent

.. autoclass:: StatelessUserBannedSystemEvent
    :members:
    :inherited-members:


UserBannedSystemEvent
~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: UserBannedSystemEvent

.. autoclass:: UserBannedSystemEvent
    :members:
    :inherited-members:

StatelessChannelRenamedSystemEvent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: StatelessChannelRenamedSystemEvent

.. autoclass:: StatelessChannelRenamedSystemEvent
    :members:
    :inherited-members:

ChannelRenamedSystemEvent
~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ChannelRenamedSystemEvent

.. autoclass:: ChannelRenamedSystemEvent
    :members:
    :inherited-members:

StatelessChannelDescriptionChangedSystemEvent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: StatelessChannelDescriptionChangedSystemEvent

.. autoclass:: StatelessChannelDescriptionChangedSystemEvent
    :members:
    :inherited-members:

ChannelDescriptionChangedSystemEvent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ChannelDescriptionChangedSystemEvent

.. autoclass:: ChannelDescriptionChangedSystemEvent
    :members:
    :inherited-members:

StatelessChannelIconChangedSystemEvent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: StatelessChannelIconChangedSystemEvent

.. autoclass:: StatelessChannelIconChangedSystemEvent
    :members:
    :inherited-members:

ChannelIconChangedSystemEvent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ChannelIconChangedSystemEvent

.. autoclass:: ChannelIconChangedSystemEvent
    :members:
    :inherited-members:

StatelessChannelOwnershipChangedSystemEvent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: StatelessChannelOwnershipChangedSystemEvent

.. autoclass:: StatelessChannelOwnershipChangedSystemEvent
    :members:
    :inherited-members:

ChannelOwnershipChangedSystemEvent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ChannelOwnershipChangedSystemEvent

.. autoclass:: ChannelOwnershipChangedSystemEvent
    :members:
    :inherited-members:

StatelessMessagePinnedSystemEvent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: StatelessMessagePinnedSystemEvent

.. autoclass:: StatelessMessagePinnedSystemEvent
    :members:
    :inherited-members:

MessagePinnedSystemEvent
~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: MessagePinnedSystemEvent

.. autoclass:: MessagePinnedSystemEvent
    :members:
    :inherited-members:

StatelessMessageUnpinnedSystemEvent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: StatelessMessageUnpinnedSystemEvent

.. autoclass:: StatelessMessageUnpinnedSystemEvent
    :members:
    :inherited-members:

MessageUnpinnedSystemEvent
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: MessageUnpinnedSystemEvent

.. autoclass:: MessageUnpinnedSystemEvent
    :members:
    :inherited-members:

StatelessCallStartedSystemEvent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: StatelessCallStartedSystemEvent

.. autoclass:: StatelessCallStartedSystemEvent
    :members:
    :inherited-members:

CallStartedSystemEvent
~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: CallStartedSystemEvent

.. autoclass:: CallStartedSystemEvent
    :members:
    :inherited-members:

StatelessSystemEvent
~~~~~~~~~~~~~~~~~~~~

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
    - :class:`.StatelessCallStartedSystemEvent`

SystemEvent
~~~~~~~~~~~

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
    - :class:`.CallStartedSystemEvent`

BaseMessage
~~~~~~~~~~~

.. attributetable:: BaseMessage

.. autoclass:: BaseMessage
    :members:

PartialMessage
~~~~~~~~~~~~~~

.. attributetable:: PartialMessage

.. autoclass:: PartialMessage
    :members:

MessageAppendData
~~~~~~~~~~~~~~~~~

.. attributetable:: MessageAppendData

.. autoclass:: MessageAppendData
    :members:

Message
~~~~~~~

.. attributetable:: Message

.. autoclass:: Message
    :members:
    :inherited-members:

Reply
~~~~~

.. attributetable:: Reply

.. autoclass:: Reply
    :members:

MessageInteractions
~~~~~~~~~~~~~~~~~~~

.. attributetable:: MessageInteractions

.. autoclass:: MessageInteractions
    :members:

MessageWebhook
~~~~~~~~~~~~~~

.. attributetable:: MessageWebhook

.. autoclass:: MessageWebhook
    :members:

BaseRole
~~~~~~~~

.. attributetable:: BaseRole

.. autoclass:: BaseRole
    :members:
    :inherited-members:

PartialRole
~~~~~~~~~~~

.. attributetable:: PartialRole

.. autoclass:: PartialRole
    :members:
    :inherited-members:

Role
~~~~

.. attributetable:: Role

.. autoclass:: Role
    :members:
    :inherited-members:

BaseWebhook
~~~~~~~~~~~

.. attributetable:: BaseWebhook

.. autoclass:: BaseWebhook
    :members:
    :inherited-members:

PartialWebhook
~~~~~~~~~~~~~~

.. attributetable:: PartialWebhook

.. autoclass:: PartialWebhook
    :members:
    :inherited-members:

Webhook
~~~~~~~

.. attributetable:: Webhook

.. autoclass:: Webhook
    :members:
    :inherited-members:

UserSettings
~~~~~~~~~~~~

.. attributetable:: UserSettings

.. autoclass:: UserSettings
    :members:

AndroidUserSettings
~~~~~~~~~~~~~~~~~~~

.. attributetable:: AndroidUserSettings

.. autoclass:: AndroidUserSettings
    :members:

ReviteNotificationOptions
~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: ReviteNotificationOptions

.. autoclass:: ReviteNotificationOptions
    :members:

ReviteThemeVariable
~~~~~~~~~~~~~~~~~~~

.. attributetable:: ReviteThemeVariable

.. autoclass:: ReviteThemeVariable
    :members:

ReviteUserSettings
~~~~~~~~~~~~~~~~~~

.. attributetable:: ReviteUserSettings

.. autoclass:: ReviteUserSettings
    :members:

JoltUserSettings
~~~~~~~~~~~~~~~~

.. attributetable:: JoltUserSettings

.. autoclass:: JoltUserSettings
    :members:


.. _revolt-api-exceptions:

Exceptions
----------

The following exceptions are thrown by the library.

.. autoexception:: PyvoltException
    :show-inheritance:
    :members:
    :inherited-members:
    :exclude-members: add_note, with_traceback

.. autoexception:: HTTPException
    :show-inheritance:
    :members:
    :inherited-members:

.. autoexception:: Unauthorized
    :show-inheritance:
    :members:
    :inherited-members:

.. autoexception:: Forbidden
    :show-inheritance:
    :members:
    :inherited-members:

.. autoexception:: NotFound
    :show-inheritance:
    :members:
    :inherited-members:

.. autoexception:: Conflict
    :show-inheritance:
    :members:
    :inherited-members:

.. autoexception:: Ratelimited
    :show-inheritance:
    :members:
    :inherited-members:

.. autoexception:: InternalServerError
    :show-inheritance:
    :members:
    :inherited-members:

.. autoexception:: BadGateway
    :show-inheritance:
    :members:
    :inherited-members:

.. autoexception:: ShardError
    :show-inheritance:
    :members:
    :inherited-members:

.. autoexception:: ShardClosedError
    :show-inheritance:
    :members:
    :inherited-members:

.. autoexception:: AuthenticationError
    :show-inheritance:
    :members:
    :inherited-members:

.. autoexception:: ConnectError
    :show-inheritance:
    :members:
    :inherited-members:

.. autoexception:: DiscoverError
    :show-inheritance:
    :members:
    :inherited-members:

.. autoexception:: InvalidData
    :show-inheritance:
    :members:
    :inherited-members:

.. autoexception:: NoData
    :show-inheritance:
    :members:
    :inherited-members:

