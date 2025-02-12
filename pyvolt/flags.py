from __future__ import annotations

import inspect
import typing

from .utils import MISSING

if typing.TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from typing_extensions import Self

from .utils import MISSING

BF = typing.TypeVar('BF', bound='BaseFlags')


class flag(typing.Generic[BF]):
    __slots__ = (
        '__doc__',
        '_func',
        '_parent',
        'name',
        'value',
        'alias',
        'inverted',
        'use_any',
    )

    def __init__(self, *, inverted: bool = False, use_any: bool = False, alias: bool = False) -> None:
        self.__doc__: typing.Optional[str] = None
        self._func: Callable[[BF], int] = MISSING
        self._parent: type[BF] = MISSING
        self.name: str = ''
        self.value: int = 0
        self.alias: bool = alias
        self.inverted: bool = inverted
        self.use_any: bool = use_any

    def __call__(self, func: Callable[[BF], int], /) -> Self:
        self._func = func
        self.__doc__ = func.__doc__
        self.name = func.__name__
        return self

    @typing.overload
    def __get__(self, instance: None, owner: type[BF], /) -> Self: ...

    @typing.overload
    def __get__(self, instance: BF, owner: type[BF], /) -> bool: ...

    def __get__(self, instance: typing.Optional[BF], owner: type[BF], /) -> typing.Union[bool, Self]:
        if instance is None:
            return self
        else:
            return instance._get(self)

    def __set__(self, instance: BF, value: bool, /) -> None:
        instance._set(self, value)

    def __and__(self, other: typing.Union[BF, flag[BF], int], /) -> BF:
        return self._parent(self.value) & other

    def __int___(self) -> int:
        return self.value

    def __or__(self, other: typing.Union[BF, flag[BF], int], /) -> BF:
        return self._parent(self.value) | other

    def __xor__(self, other: typing.Union[BF, flag[BF], int], /) -> BF:
        return self._parent(self.value) ^ other

    def __int__(self) -> int:
        return self.value


class BaseFlags:
    """Base class for flags."""

    if typing.TYPE_CHECKING:
        ALL_VALUE: typing.ClassVar[int]
        INVERTED: typing.ClassVar[bool]
        NONE_VALUE: typing.ClassVar[int]
        VALID_FLAGS: typing.ClassVar[dict[str, int]]

        ALL: typing.ClassVar[Self]
        NONE: typing.ClassVar[Self]
        FLAGS: typing.ClassVar[dict[str, flag]]

    __slots__ = ('value',)

    def __init_subclass__(cls, *, inverted: bool = False, support_kwargs: bool = True) -> None:
        valid_flags = {}
        flags = {}
        for _, f in inspect.getmembers(cls):
            if isinstance(f, flag):
                f.value = f._func(cls)
                if f.alias:
                    continue
                valid_flags[f.name] = f.value
                flags[f.name] = f
                f._parent = cls

        default = 0
        if inverted:
            all = 0
            for value in valid_flags.values():
                default |= value
        else:
            all = 0
            for value in valid_flags.values():
                all |= value

        cls.ALL_VALUE = all
        cls.INVERTED = inverted
        cls.NONE_VALUE = default
        cls.VALID_FLAGS = valid_flags

        if support_kwargs:

            def init_with_kwargs(self, value: int = cls.NONE_VALUE, /, **kwargs: bool) -> None:
                self.value = value

                if kwargs:
                    for k, f in kwargs.items():
                        if k not in self.VALID_FLAGS:
                            raise TypeError(f'Unknown flag {k}')
                        setattr(self, k, f)

            cls.__init__ = init_with_kwargs
        else:

            def init_without_kwargs(self, value: int = cls.NONE_VALUE, /) -> None:
                self.value = value

            cls.__init__ = init_without_kwargs  # type: ignore

        if cls.INVERTED:
            cls._get = cls._get1
            cls._set = cls._set1
        else:
            cls._get = cls._get2
            cls._set = cls._set2
        cls.ALL = cls(cls.ALL_VALUE)
        cls.NONE = cls(cls.NONE_VALUE)
        cls.FLAGS = flags

    if typing.TYPE_CHECKING:

        def __init__(self, value: int = 0, /, **kwargs: bool) -> None:
            pass

        def _get(self, _other: flag[Self], /) -> bool:
            return False

        def _set(self, flag: flag[Self], value: bool, /) -> None:
            pass

    # used if flag is inverted
    def _get1(self, other: flag[Self], /) -> bool:
        if other.use_any and other.inverted:
            # (ANY & INVERTED)
            return (~self.value & ~other.value) != 0
        elif other.use_any:
            # (ANY)
            return (~self.value & other.value) != 0
        elif other.inverted:
            # (INVERTED)
            ov = other.value
            return (~self.value & ~ov) == ov
        else:
            # ()
            ov = other.value
            return (~self.value & ov) == ov

    # used if flag is uninverted
    def _get2(self, other: flag[Self], /) -> bool:
        if other.use_any and other.inverted:
            # (ANY & INVERTED)
            return (self.value & ~other.value) != 0
        elif other.use_any:
            # (ANY)
            return (self.value & other.value) != 0
        elif other.inverted:
            # (INVERTED)
            ov = other.value
            return (self.value & ~ov) == ov
        else:
            # ()
            ov = other.value
            return (self.value & ov) == ov

    # used if flag is inverted
    def _set1(self, flag: flag[Self], value: bool, /) -> None:
        if flag.inverted ^ value:
            self.value &= ~flag.value
        else:
            self.value |= flag.value

    # used if flag is uninverted
    def _set2(self, flag: flag[Self], value: bool, /) -> None:
        if flag.inverted ^ value:
            self.value |= flag.value
        else:
            self.value &= ~flag.value

    @classmethod
    def all(cls) -> Self:
        """Returns instance with all flags."""
        return cls(cls.ALL_VALUE)

    @classmethod
    def none(cls) -> Self:
        """Returns instance with no flags."""
        return cls(cls.NONE_VALUE)

    @classmethod
    def from_value(cls, value: int, /) -> Self:
        self = cls.__new__(cls)
        self.value = value
        return self

    def __hash__(self) -> int:
        return hash(self.value)

    def __iter__(self) -> Iterator[tuple[str, bool]]:
        for name, value in self.__class__.__dict__.items():
            if isinstance(value, flag):
                if value.alias:
                    continue
                yield (name, getattr(self, name))

    def __repr__(self, /) -> str:
        return f'<{self.__class__.__name__}: {self.value}>'

    def copy(self) -> Self:
        """Copies the flag value."""
        return self.__class__(self.value)

    def _value_of(self, other: typing.Union[Self, flag[Self], int], /) -> int:
        if isinstance(other, int):
            return other
        elif isinstance(other, (flag, self.__class__)):
            return other.value
        else:
            raise TypeError(f'cannot get {other.__class__.__name__} value')

    def is_subset(self, other: typing.Union[Self, flag[Self], int], /) -> bool:
        """:class:`bool`: Returns ``True`` if self has the same or fewer flags as other."""
        return (self.value & self._value_of(other)) == self.value

    def is_superset(self, other: typing.Union[Self, flag[Self], int], /) -> bool:
        """:class:`bool`: Returns ``True`` if self has the same or more flags as other."""
        return (self.value | self._value_of(other)) == self.value

    def is_strict_subset(self, other: typing.Union[Self, flag[Self], int], /) -> bool:
        """:class:`bool`: Returns ``True`` if the flags on other are a strict subset of those on self."""
        return self.is_subset(other) and self != other

    def is_strict_superset(self, other: typing.Union[Self, flag[Self], int], /) -> bool:
        """:class:`bool`: Returns ``True`` if the flags on other are a strict superset of those on self."""
        return self.is_superset(other) and self != other

    __le__ = is_subset
    __ge__ = is_superset
    __lt__ = is_strict_subset
    __gt__ = is_strict_superset

    def __and__(self, other: typing.Union[Self, flag[Self], int], /) -> Self:
        return self.__class__(self.value & self._value_of(other))

    def __bool__(self) -> bool:
        return self.value != self.NONE_VALUE

    def __contains__(self, other: typing.Union[Self, flag[Self], int], /) -> bool:
        ov = self._value_of(other)
        return (self.value & ov) == ov

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, self.__class__) and self.value == other.value

    def __iand__(self, other: typing.Union[Self, flag[Self], int], /) -> Self:
        self.value &= self._value_of(other)
        return self

    def __int___(self) -> int:
        return self.value

    def __invert__(self) -> Self:
        max_bits = max(self.VALID_FLAGS.values()).bit_length()
        max_value = -1 + (1 << max_bits)
        return self.from_value(self.value ^ max_value)

    def __ior__(self, other: typing.Union[Self, flag[Self], int], /) -> Self:
        self.value |= self._value_of(other)
        return self

    def __ixor__(self, other: typing.Union[Self, flag[Self], int], /) -> Self:
        self.value ^= self._value_of(other)
        return self

    def __ne__(self, other: object, /) -> bool:
        return not self.__eq__(other)

    def __or__(self, other: typing.Union[Self, flag[Self], int], /) -> Self:
        return self.__class__(self.value | self._value_of(other))

    def __xor__(self, other: typing.Union[Self, flag[Self], int], /) -> Self:
        return self.__class__(self.value ^ self._value_of(other))


def doc_flags(
    intro: str,
    /,
    *,
    added_in: typing.Optional[str] = None,
) -> Callable[[type[BF]], type[BF]]:
    """Document flag classes.

    Parameters
    ----------
    intro: :class:`str`
        The intro.
    added_in: Optional[:class:`str`]
        The version the flags were added in.

    Returns
    -------
    Callable[[Type[BF]], Type[BF]]
        The documented class.
    """

    def decorator(cls: type[BF]) -> type[BF]:
        directives = ''

        if added_in:
            directives += '    \n    .. versionadded:: {}\n'.format(added_in)
        cls.__doc__ = f"""{intro}
{directives}
    .. container:: operations

        .. describe:: x == y

            Checks if two flags are equal.
        .. describe:: x != y

            Checks if two flags are not equal.
        .. describe:: x | y, x |= y

            Returns a {cls.__name__} instance with all enabled flags from
            both x and y.
        .. describe:: x & y, x &= y

            Returns a {cls.__name__} instance with only flags enabled on
            both x and y.
        .. describe:: x ^ y, x ^= y

            Returns a {cls.__name__} instance with only flags enabled on
            only one of x or y, not on both.
        .. describe:: ~x

            Returns a {cls.__name__} instance with all flags inverted from x.
        .. describe:: hash(x)

            Return the flag's hash.
        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
        .. describe:: bool(b)

            Returns whether any flag is set to ``True``.

    Attributes
    ----------
    value: :class:`int`
        The raw value. This value is a bit array field of a 53-bit integer
        representing the currently available flags. You should query
        flags via the properties rather than using this raw value.
"""
        return cls

    return decorator


@doc_flags('Wraps up a Revolt Bot flag value.')
class BotFlags(BaseFlags, support_kwargs=False):
    __slots__ = ()

    @flag()
    def verified(cls) -> int:
        """:class:`bool`: Whether the bot is verified."""
        return 1 << 0

    @flag()
    def official(cls) -> int:
        """:class:`bool`: Whether the bot is created by Revolt."""
        return 1 << 1


@doc_flags('Wraps up a Message flag value.')
class MessageFlags(BaseFlags, support_kwargs=False):
    __slots__ = ()

    @flag()
    def suppress_notifications(cls) -> int:
        """:class:`bool`: Whether the message will not send push/desktop notifications."""
        return 1 << 0

    @flag()
    def mention_everyone(cls) -> int:
        """:class:`bool`: Whether the message will mention all users who can see the channel."""
        return 1 << 1

    @flag()
    def mention_online(cls) -> int:
        """:class:`bool`: Whether the message will mention all users who are online and can see the channel.

        .. note::
            If this is ``True``, then :attr:`.mention_everyone` cannot be ``True`` either.
        """
        return 1 << 2


@doc_flags('Wraps up a Permission flag value.', added_in='8.0')
class Permissions(BaseFlags, support_kwargs=True):
    __slots__ = ()

    # * Generic permissions
    @flag()
    def manage_channels(cls) -> int:
        """:class:`bool`: Whether the user can edit, delete, or create channels in the server.

        This also corresponds to the "Manage Channel" channel-specific override.
        """
        return 1 << 0

    @flag()
    def manage_server(cls) -> int:
        """:class:`bool`: Whether the user can edit server properties."""
        return 1 << 1

    @flag()
    def manage_permissions(cls) -> int:
        """:class:`bool`: Whether the user can manage permissions on server or channels."""
        return 1 << 2

    @flag()
    def manage_roles(cls) -> int:
        """:class:`bool`: Whether the user can manage roles on server."""
        return 1 << 3

    @flag()
    def manage_customization(cls) -> int:
        """:class:`bool`: Whether the user can manage server customization (includes emoji)."""
        return 1 << 4

    @classmethod
    def generic(cls) -> Self:
        """:class:`Permissions`: Returns generic permissions."""
        return cls(0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00011111)

    # % 1 bit reserved

    # * Member permissions

    @flag()
    def kick_members(cls) -> int:
        """:class:`bool`: Whether the user can kick other members below their ranking."""
        return 1 << 6

    @flag()
    def ban_members(cls) -> int:
        """:class:`bool`: Whether the user can ban other members below their ranking."""
        return 1 << 7

    @flag()
    def timeout_members(cls) -> int:
        """:class:`bool`: Whether the user can timeout other members below their ranking."""
        return 1 << 8

    @flag()
    def assign_roles(cls) -> int:
        """:class:`bool`: Whether the user can assign roles to members below their ranking."""
        return 1 << 9

    @flag()
    def change_nickname(cls) -> int:
        """:class:`bool`: Whether the user can change own nick."""
        return 1 << 10

    @flag()
    def manage_nicknames(cls) -> int:
        """:class:`bool`: Whether the user can change or remove other's nicknames below their ranking."""
        return 1 << 11

    @flag()
    def change_avatar(cls) -> int:
        """:class:`bool`: Whether the user can change own avatar."""
        return 1 << 12

    @flag()
    def remove_avatars(cls) -> int:
        """:class:`bool`: Whether the user can remove other's avatars below their ranking."""
        return 1 << 13

    @classmethod
    def member(cls) -> Self:
        """:class:`Permissions`: Returns member-related permissions."""
        return cls(0b00000000_00000000_00000000_00000000_00000000_00000000_00111111_11000000)

    # % 7 bits reserved

    # * Channel permissions

    @flag()
    def view_channel(cls) -> int:
        """:class:`bool`: Whether the user can view a channel."""
        return 1 << 20

    @flag()
    def read_message_history(cls) -> int:
        """:class:`bool`: Whether the user can read a channel's past message history."""
        return 1 << 21

    @flag()
    def send_messages(cls) -> int:
        """:class:`bool`: Whether the user can send messages."""
        return 1 << 22

    @flag()
    def manage_messages(cls) -> int:
        """:class:`bool`: Whether the user can delete other's messages (or pin them) in a channel."""
        return 1 << 23

    @flag()
    def manage_webhooks(cls) -> int:
        """:class:`bool`: Whether user can manage webhooks that belong to a channel."""
        return 1 << 24

    @flag()
    def create_invites(cls) -> int:
        """:class:`bool`: Whether user can create invites to this channel."""
        return 1 << 25

    @flag()
    def send_embeds(cls) -> int:
        """:class:`bool`: Whether user can send embedded content in this channel."""
        return 1 << 26

    @flag()
    def upload_files(cls) -> int:
        """:class:`bool`: Whether user can send attachments and media in this channel."""
        return 1 << 27

    @flag()
    def use_masquerade(cls) -> int:
        """:class:`bool`: Whether the user can use masquerade on own messages with custom nickname and avatar."""
        return 1 << 28

    @flag()
    def react(cls) -> int:
        """:class:`bool`: Whether the user can react to messages with emojis."""
        return 1 << 29

    @flag()
    def mention_everyone(cls) -> int:
        """:class:`bool`: Whether the user can mention everyone and online members."""
        return 1 << 37

    @flag()
    def mention_roles(cls) -> int:
        """:class:`bool`: Whether the user can mention roles."""
        return 1 << 38

    @classmethod
    def channel(cls) -> Self:
        """:class:`Permissions`: Returns channel-related permissions."""
        return cls(0b00000000_00000000_00000000_01110000_00111111_11110000_00000000_00000000)

    # * Voice permissions

    @flag()
    def connect(cls) -> int:
        """:class:`bool`: Whether the user can connect to a voice channel."""
        return 1 << 30

    @flag()
    def speak(cls) -> int:
        """:class:`bool`: Whether the user can speak in a voice call."""
        return 1 << 31

    @flag()
    def video(cls) -> int:
        """:class:`bool`: Whether the user can share video in a voice call."""
        return 1 << 32

    @flag()
    def mute_members(cls) -> int:
        """:class:`bool`: Whether user can mute other members with lower ranking in a voice call."""
        return 1 << 33

    @flag()
    def deafen_members(cls) -> int:
        """:class:`bool`: Whether user can deafen other members with lower ranking in a voice call."""
        return 1 << 34

    @flag()
    def move_members(cls) -> int:
        """:class:`bool`: Whether the user can move members between voice channels."""
        return 1 << 35

    @flag()
    def listen(cls) -> int:
        """:class:`bool`: Whether the user can listen to other users in voice channel."""
        return 1 << 36

    @classmethod
    def voice(cls) -> Self:
        """:class:`Permissions`: Returns voice-related permissions."""
        return cls(0b00000000_00000000_00000000_00011111_11000000_00000000_00000000_00000000)

    # * Misc. permissions
    # % Bits 36 to 52: free area
    # % Bits 53 to 64: do not use


ALLOW_PERMISSIONS_IN_TIMEOUT: typing.Final[Permissions] = Permissions(
    view_channel=True,
    read_message_history=True,
)
VIEW_ONLY_PERMISSIONS: typing.Final[Permissions] = Permissions(
    view_channel=True,
    read_message_history=True,
)
DEFAULT_PERMISSIONS: typing.Final[Permissions] = VIEW_ONLY_PERMISSIONS | Permissions(
    send_messages=True,
    create_invites=True,
    send_embeds=True,
    upload_files=True,
    connect=True,
    speak=True,
    listen=True,
)
DEFAULT_SAVED_MESSAGES_PERMISSIONS: typing.Final[Permissions] = Permissions.all()
DEFAULT_DM_PERMISSIONS: typing.Final[Permissions] = DEFAULT_PERMISSIONS | Permissions(manage_channels=True, react=True)
DEFAULT_SERVER_PERMISSIONS: typing.Final[Permissions] = DEFAULT_PERMISSIONS | Permissions(
    react=True,
    change_nickname=True,
    change_avatar=True,
)


@doc_flags('Wraps up a user permission flag value.')
class UserPermissions(BaseFlags, support_kwargs=True):
    __slots__ = ()

    @flag()
    def access(cls) -> int:
        """:class:`bool`: Whether the user can access data of this user."""
        return 1 << 0

    @flag()
    def view_profile(cls) -> int:
        """:class:`bool`: Whether the user can view this user's profile."""
        return 1 << 1

    @flag()
    def send_messages(cls) -> int:
        """:class:`bool`: Whether the user can send messages to this user."""
        return 1 << 2

    @flag()
    def invite(cls) -> int:
        """:class:`bool`: Whether the user can invite this user to groups."""
        return 1 << 3


@doc_flags('Wraps up a server flag value.')
class ServerFlags(BaseFlags, support_kwargs=True):
    __slots__ = ()

    @flag()
    def verified(cls) -> int:
        """:class:`bool`: Whether the server is verified."""
        return 1 << 0

    @flag()
    def official(cls) -> int:
        """:class:`bool`: Whether the server is ran by Revolt team."""
        return 1 << 1


@doc_flags('Wraps up a User Badges flag value.')
class UserBadges(BaseFlags, support_kwargs=True):
    __slots__ = ()

    @flag()
    def developer(cls) -> int:
        """:class:`bool`: Whether user is Revolt developer."""
        return 1 << 0

    @flag()
    def translator(cls) -> int:
        """:class:`bool`: Whether the user helped translate Revolt."""
        return 1 << 1

    @flag()
    def supporter(cls) -> int:
        """:class:`bool`: Whether the user monetarily supported Revolt."""
        return 1 << 2

    @flag()
    def responsible_disclosure(cls) -> int:
        """:class:`bool`: Whether the user have responsibly disclosed a security issue."""
        return 1 << 3

    @flag()
    def founder(cls) -> int:
        """:class:`bool`: Whether the user is a Revolt founder."""
        return 1 << 4

    @flag()
    def platform_moderation(cls) -> int:
        """:class:`bool`: Whether the user is a platform moderator."""
        return 1 << 5

    @flag()
    def active_supporter(cls) -> int:
        """:class:`bool`: Whether the user is active monetary supporter."""
        return 1 << 6

    @flag()
    def paw(cls) -> int:
        """:class:`bool`: Whether the user likes 🦊 and 🦝."""
        return 1 << 7

    @flag()
    def early_adopter(cls) -> int:
        """:class:`bool`: Whether the user joined as one of the first 1000 users in 2021."""
        return 1 << 8

    @flag()
    def reserved_relevant_joke_badge_1(cls) -> int:
        """:class:`bool`: Whether the user is have given some funny joke.

        This is displayed as amogus (with 'sus' label) in Revite.
        """
        return 1 << 9

    @flag()
    def reserved_relevant_joke_badge_2(cls) -> int:
        """:class:`bool`: Whether the user is have given some funny joke.

        This is displayed as amorbus (Amogus with Morbin texture) in Revite,
        and as 'Low resolution troll face' in new client.
        """
        return 1 << 10


@doc_flags('Wraps up a User Flags flag value.')
class UserFlags(BaseFlags, support_kwargs=True):
    __slots__ = ()

    @flag()
    def suspended(cls) -> int:
        """:class:`bool`: Whether the user has been suspended from the platform."""
        return 1 << 0

    @flag()
    def deleted(cls) -> int:
        """:class:`bool`: Whether the user has deleted their account."""
        return 1 << 1

    @flag()
    def banned(cls) -> int:
        """:class:`bool`: Whether the user was banned off the platform."""
        return 1 << 2

    @flag()
    def spam(cls) -> int:
        """:class:`bool`: Whether the user was marked as spam and removed from platform."""
        return 1 << 3


__all__ = (
    'flag',
    'BaseFlags',
    'doc_flags',
    'BotFlags',
    'MessageFlags',
    'Permissions',
    'ALLOW_PERMISSIONS_IN_TIMEOUT',
    'VIEW_ONLY_PERMISSIONS',
    'DEFAULT_PERMISSIONS',
    'DEFAULT_SAVED_MESSAGES_PERMISSIONS',
    'DEFAULT_DM_PERMISSIONS',
    'DEFAULT_SERVER_PERMISSIONS',
    'UserPermissions',
    'ServerFlags',
    'UserBadges',
    'UserFlags',
)
