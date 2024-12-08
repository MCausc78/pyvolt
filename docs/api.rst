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

State
~~~~~

.. attributetable:: State

.. autoclass:: State
    :members:

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

    'ServerActivity',
    'BotUsage',
    'LightspeedContentType',
    'TwitchContentType',
    'BandcampContentType',
    'ImageSize',
    'Language',
    'MessageSort',
    'ContentReportReason',
    'UserReportReason',
    'MemberRemovalIntention',
    'ShardFormat',
    'AndroidTheme',
    'AndroidProfilePictureShape',
    'AndroidMessageReplyStyle',
    'ReviteChangelogEntry',
    'ReviteNotificationState',
    'ReviteEmojiPack',
    'ReviteBaseTheme',
    'ReviteFont',
    'ReviteMonoFont',
    'Presence',
    'RelationshipStatus',
    'ReportStatus',
    'ReportedContentType',

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

.. _revolt-api-models:

Models
------

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

.. attributetable:: SavedMessagesChannel

.. autoclass:: SavedMessagesChannel
    :members:

.. attributetable:: DMChannel

.. autoclass:: DMChannel
    :members:

.. attributetable:: GroupChannel

.. autoclass:: GroupChannel
    :members:

.. attributetable:: PrivateChannel

.. autoclass:: PrivateChannel
    :members:

.. attributetable:: BaseServerChannel

.. autoclass:: BaseServerChannel
    :members:

.. attributetable:: ChannelVoiceMetadata

.. autoclass:: ChannelVoiceMetadata
    :members:

.. attributetable:: TextChannel

.. autoclass:: TextChannel
    :members:

.. attributetable:: VoiceChannel

.. autoclass:: VoiceChannel
    :members:

.. attributetable:: ServerChannel

.. autoclass:: ServerChannel
    :members:

.. attributetable:: TextableChannel

.. autoclass:: TextableChannel
    :members:

.. attributetable:: Channel

.. autoclass:: Channel
    :members:

.. attributetable:: ChannelVoiceStateContainer

.. autoclass:: ChannelVoiceStateContainer
    :members:

Server
~~~~~~

.. attributetable:: BaseServer

.. autoclass:: BaseServer
    :members:

.. attributetable:: PartialServer

.. autoclass:: PartialServer
    :members:

.. attributetable:: Server

.. autoclass:: Server
    :members:

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

.. attributetable:: PartialMember

.. autoclass:: PartialMember
    :members:

.. attributetable:: Member

.. autoclass:: Member
    :members:

.. attributetable:: MemberList

.. autoclass:: MemberList
    :members:

Role
~~~~

.. attributetable:: BaseRole

.. autoclass:: BaseRole
    :members:

.. attributetable:: PartialRole

.. autoclass:: PartialRole
    :members:

.. attributetable:: Role

.. autoclass:: Role
    :members:
