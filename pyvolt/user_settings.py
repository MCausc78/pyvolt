from __future__ import annotations

from datetime import datetime
import typing

from . import utils
from .core import UNDEFINED, UndefinedOr, is_defined, ULIDOr, resolve_id
from .enums import Enum
from .localization import Language

if typing.TYPE_CHECKING:
    from . import raw
    from .channel import Channel
    from .server import BaseServer
    from .state import State


class UserSettings:
    """Represents Revolt user settings.

    Attributes
    ----------
    state: :class:`State`
        The state that manages current user settings.
    data: Dict[:class:`str`, Tuple[:class:`int`, :class:`str`]]
        The mapping of ``{key: (timestamp, value)}``.
    mocked: :class:`bool`
        Whether user settings are mocked. Mocked user settings are created by library itself, if not logged in, or in HTTP-only mode.
    partial: :class:`bool`
        Whether user settings are partial. This is set to ``True`` when used via :attr:`UserSettingsUpdateEvent.partial`.
    """

    __slots__ = (
        "state",
        "data",
        "mocked",
        "partial",
        "_android",
        "_revite",
    )

    def __init__(
        self,
        *,
        data: dict[str, tuple[int, str]],
        state: State,
        mocked: bool,
        partial: bool,
    ) -> None:
        self.state = state
        self.data = data
        self.mocked = mocked
        self.partial = partial
        self._parse()

    def _parse(self) -> None:
        try:
            self._android: AndroidUserSettings | Exception = AndroidUserSettings(self)
        except Exception as exc:
            self._android = exc

        try:
            self._revite: ReviteUserSettings | Exception = ReviteUserSettings(self)
        except Exception as exc:
            self._revite = exc

    def _update(self, partial: UserSettings) -> None:
        self.data.update(partial.data)
        self._parse()

    @property
    def android(self) -> AndroidUserSettings:
        """:class:`AndroidUserSettings`: The Android user settings.

        Raises
        ------
        Exception
            If ``android`` user setting JSON string is corrupted.
        """
        if isinstance(self._android, Exception):
            raise self._android from None
        return self._android

    @property
    def revite(self) -> ReviteUserSettings:
        """:class:`ReviteUserSettings`: The Revite user settings.

        Raises
        ------
        Exception
            If user settings are corrupted.
        """
        if isinstance(self._revite, Exception):
            raise self._revite from None
        return self._revite

    def __getitem__(self, key: str) -> str:
        return self.data[key][1]

    @typing.overload
    def get(self, key: str) -> str | None: ...

    @typing.overload
    def get(self, key: str, default: str, /) -> str: ...

    def get(self, key: str, *default: str) -> str | None:
        """Get a user setting."""
        if key in self.data:
            return self.data[key][1]
        return default[0] if default else None

    async def edit(
        self,
        dict_settings: dict[str, str | typing.Any] = {},
        timestamp: datetime | int | None = None,
        /,
        **kwargs: str | typing.Any,
    ) -> None:
        """|coro|

        Modify current user settings.

        .. note::
            This can only be used by non-bot accounts.
        """
        return await self.state.http.edit_user_settings(
            dict_settings, timestamp, **kwargs
        )


class AndroidTheme(Enum):
    revolt = "Revolt"
    light = "Light"
    pure_black = "Amoled"
    system = "None"
    material_you = "M3Dynamic"


class AndroidProfilePictureShape(Enum):
    sharp = 0
    rounded = 15
    circular = 50


class AndroidMessageReplyStyle(Enum):
    long_press_to_reply = "None"
    swipe_to_reply = "SwipeFromEnd"
    double_tap_to_reply = "DoubleTap"


class AndroidUserSettings:
    """Represents Android user settings.

    Attributes
    ----------
    parent: :class:`UserSettings`
        The parent.
    """

    __slots__ = (
        "parent",
        "_payload",
        "_theme",
        "_colour_overrides",
        "_reply_style",
        "_avatar_radius",
    )

    def __init__(self, parent: UserSettings) -> None:
        self.parent = parent
        payload: raw.AndroidUserSettings = utils.from_json(parent.get("android", "{}"))
        self._payload = payload

        self._parse(payload)

    def _parse(self, payload: raw.AndroidUserSettings) -> None:
        theme = payload.get("theme")
        if theme:
            self._theme: AndroidTheme | None = AndroidTheme(theme)
        else:
            self._theme = None
        self._colour_overrides: dict[str, int] | None = payload.get("colourOverrides")
        reply_style = payload.get("messageReplyStyle")
        if reply_style:
            self._reply_style: AndroidMessageReplyStyle | None = (
                AndroidMessageReplyStyle(reply_style)
            )
        else:
            self._reply_style = None
        self._avatar_radius: int | None = payload.get("avatarRadius")

    @property
    def theme(self) -> AndroidTheme:
        """:class:`AndroidTheme`: The current theme."""
        return self._theme or AndroidTheme.system

    @property
    def colour_overrides(self) -> dict[str, int]:
        """Dict[:class:`str`, :class:`int`]: The current theme colour overrides."""
        return self._colour_overrides or {}

    @property
    def reply_style(self) -> AndroidMessageReplyStyle:
        """:class:`AndroidMessageReplyStyle`: The current theme."""
        return self._reply_style or AndroidMessageReplyStyle.swipe_to_reply

    @property
    def profile_picture_shape(self) -> int:
        """:class:`int`: The current profile picture shape."""
        return self._avatar_radius or 50

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} theme={self.theme!r} colour_overrides={self.colour_overrides!r} reply_style={self.reply_style!r} profile_picture_shape={self.profile_picture_shape!r}>"

    def payload_for(
        self,
        *,
        theme: UndefinedOr[AndroidTheme | None] = UNDEFINED,
        colour_overrides: UndefinedOr[dict[str, int] | None] = UNDEFINED,
        reply_style: UndefinedOr[AndroidMessageReplyStyle | None] = UNDEFINED,
        avatar_radius: UndefinedOr[AndroidProfilePictureShape | int | None] = UNDEFINED,
    ) -> raw.AndroidUserSettings:
        """|coro|

        Builds a payload for Android user settings. You must pass it as JSON string to :meth:`HTTPClient.edit_user_settings`, like that:

        .. code-block:: python3

            payload = settings.payload_for(theme=AndroidTheme.material_you)
            await http.edit_user_settings(android=payload)

        Parameters
        ----------
        theme: :class:`UndefinedOr`[Optional[:class:`AndroidTheme`]]
            The new theme. Passing ``None`` denotes ``theme`` removal in internal object.
        colour_overrides: :class:`UndefinedOr`[Optional[Dict[:class:`str`, :class:`int`]]]
            The new colour overrides. Passing ``None`` denotes ``colourOverrides`` removal in internal object.
        reply_style: :class:`UndefinedOr`[Optional[:class:`AndroidMessageReplyStyle`]]
            The new message reply style. Passing ``None`` denotes ``messageReplyStyle`` removal in internal object.
        avatar_radius: :class:`UndefinedOr`[Optional[Union[:class:`AndroidProfilePictureShape`, :class:`int`]]]
            The new avatar radius. Passing ``None`` denotes ``avatarRadius`` removal in internal object.
        """
        payload = self._payload
        if is_defined(theme):
            if theme is None:
                try:
                    del payload["theme"]
                except KeyError:
                    pass
            else:
                payload["theme"] = theme.value

        if is_defined(colour_overrides):
            if colour_overrides is None:
                try:
                    del payload["colourOverrides"]
                except KeyError:
                    pass
            else:
                payload["colourOverrides"] = colour_overrides

        if is_defined(reply_style):
            if reply_style is None:
                try:
                    del payload["messageReplyStyle"]
                except KeyError:
                    pass
            else:
                payload["messageReplyStyle"] = reply_style.value

        if is_defined(avatar_radius):
            if avatar_radius is None:
                try:
                    del payload["avatarRadius"]
                except KeyError:
                    pass
            elif isinstance(avatar_radius, AndroidProfilePictureShape):
                payload["avatarRadius"] = avatar_radius.value
            else:
                payload["avatarRadius"] = avatar_radius

        return payload

    async def edit(
        self,
        *,
        theme: UndefinedOr[AndroidTheme | None] = UNDEFINED,
        colour_overrides: UndefinedOr[dict[str, int] | None] = UNDEFINED,
        reply_style: UndefinedOr[AndroidMessageReplyStyle | None] = UNDEFINED,
        avatar_radius: UndefinedOr[AndroidProfilePictureShape | int | None] = UNDEFINED,
    ) -> None:
        """|coro|

        Edits the Android user settings.

        Parameters
        ----------
        theme: :class:`UndefinedOr`[Optional[:class:`AndroidTheme`]]
            The new theme. Passing ``None`` denotes ``theme`` removal in internal object.
        colour_overrides: :class:`UndefinedOr`[Optional[Dict[:class:`str`, :class:`int`]]]
            The new colour overrides. Passing ``None`` denotes ``colourOverrides`` removal in internal object.
        reply_style: :class:`UndefinedOr`[Optional[:class:`AndroidMessageReplyStyle`]]
            The new message reply style. Passing ``None`` denotes ``messageReplyStyle`` removal in internal object.
        avatar_radius: :class:`UndefinedOr`[Optional[Union[:class:`AndroidProfilePictureShape`, :class:`int`]]]
            The new avatar radius. Passing ``None`` denotes ``avatarRadius`` removal in internal object.
        """
        payload = self.payload_for(
            theme=theme,
            colour_overrides=colour_overrides,
            reply_style=reply_style,
            avatar_radius=avatar_radius,
        )
        await self.parent.edit(android=payload)


class ReviteChangelogEntry(Enum):
    mfa_feature = 1
    """Title: Secure your account with 2FA."""

    iar_reporting_feature = 2
    """Title: In-App Reporting Is Here"""

    discriminators_feature = 3
    """Title: Usernames are Changing"""


class ReviteNotificationState(Enum):
    all_messages = "all"
    mentions_only = "mention"
    none = "none"
    muted = "muted"


class ReviteNotificationOptions:
    """Represents Revite notification options.

    Attributes
    ----------
    servers: Dict[:class:`str`, :class:`ReviteNotificationState`]
        The servers.
    channels: Dict[:class:`str`, :class:`ReviteNotificationState`]
        The channels.
    """

    __slots__ = ("servers", "channels")

    def __init__(self, data: raw.ReviteNotificationOptions) -> None:
        self.servers: dict[str, ReviteNotificationState] = {
            server_id: ReviteNotificationState(state)
            for server_id, state in data["server"].items()
        }
        self.channels: dict[str, ReviteNotificationState] = {
            channel_id: ReviteNotificationState(state)
            for channel_id, state in data["channel"].items()
        }


class ReviteEmojiPack(Enum):
    mutant_remix = "mutant"
    twemoji = "twemoji"
    openmoji = "openmoji"
    noto_emoji = "noto"


class ReviteBaseTheme(Enum):
    dark = "dark"
    light = "light"


class ReviteFont(Enum):
    open_sans = "Open Sans"
    opendyslexic = "OpenDyslexic"
    inter = "Inter"
    atkinson_hyperlegible = "Atkinson Hyperlegible"
    roboto = "Roboto"
    noto_sans = "Noto Sans"
    lato = "Lato"
    bitter = "Bitter"
    montserrat = "Montserrat"
    poppins = "Poppins"
    raleway = "Raleway"
    ubuntu = "Ubuntu"
    comic_neue = "Comic Neue"
    lexend = "Lexend"


class ReviteMonoFont(Enum):
    fira_code = "Fira Code"
    roboto_mono = "Robot Mono"
    source_code_pro = "Source Code Pro"
    space_mono = "Space Mono"
    ubuntu_mono = "Ubuntu Mono"
    jetbrains_mono = "JetBrains Mono"


ReviteThemeVariable = raw.ReviteThemeVariable


class ReviteUserSettings:
    """Represents Revite user settings.

    Attributes
    ----------
    parent: :class:`UserSettings`
        The raw user settings.
    last_viewed_changelog_entry: Optional[:class:`ReviteChangelogEntry`]
        The last viewed changelog entry.
    seasonal: Optional[:class:`bool`]
        Whether to display effects in the home tab during holiday seasons or not.
    transparent: Optional[:class:`bool`]
        Whether to enable transparency effects throughout the app or not.
    ligatures: Optional[:class:`bool`]
        Whether to combine characters together or not.
        For example, ``->`` turns into an arrow if this property is ``True``.
        Applicable only for supported fonts (such as :attr:`ReviteFont.inter`).
    """

    __slots__ = (
        "parent",
        "last_viewed_changelog_entry",
        "_language",
        "_notification_options",
        "_ordering",
        "_appearance_emoji_pack",
        "seasonal",
        "transparent",
        "ligatures",
        "_appearance_theme_base",
        "_appearance_theme_css",
        "_appearance_theme_font",
        # "_appearance_theme_light",
        "_appearance_theme_monofont",
        "_appearance_theme_overrides",
    )

    def __init__(self, parent: UserSettings) -> None:
        self.parent = parent
        self._parse()

    def get_language(self) -> Language | None:
        """Optional[:class:`Language`]: The current language."""
        return self._language

    @property
    def language(self) -> Language:
        """:class:`Language`: The current language. Defaults to :attr:`Language.english_simplified` if language is undefined."""
        return self._language or Language.english

    def get_notification_options(self) -> ReviteNotificationOptions | None:
        """Optional[:class:`ReviteNotificationOptions`]: The notification options."""
        return self._notification_options

    @property
    def notification_options(self) -> ReviteNotificationOptions:
        """:class:`ReviteNotificationOptions`: The notification options."""
        return self._notification_options or ReviteNotificationOptions(
            {"server": {}, "channel": {}}
        )

    @property
    def ordering(self) -> list[str]:
        """List[:class:`str`]: The server ordering."""
        return self._ordering or []

    def get_emoji_pack(self) -> ReviteEmojiPack | None:
        """Optional[:class:`ReviteEmojiPack`]: Gets the current emoji pack."""
        return self._appearance_emoji_pack

    @property
    def emoji_pack(self) -> ReviteEmojiPack:
        """:class:`ReviteEmojiPack`: The current emoji pack."""
        return self._appearance_emoji_pack or ReviteEmojiPack.mutant_remix

    def is_seasonal(self) -> bool:
        """:class:`bool`: Whether to display effects in the home tab during holiday seasons or not."""
        return True if self.seasonal is None else self.seasonal

    def is_transparent(self) -> bool:
        """Whether to enable transparency effects throughout the app or not."""
        return True if self.transparent is None else self.transparent

    def is_ligatures_enabled(self) -> bool:
        """:class:`bool`: Whether to combine characters together or not.
        For example, ``->`` turns into an arrow if this property is ``True``.

        Applicable only for supported fonts (such as :attr:`ReviteFont.inter`).
        """
        return True if self.ligatures is None else self.ligatures

    def get_base_theme(self) -> ReviteBaseTheme | None:
        """Optional[:class:`ReviteBaseTheme`]: The current base theme."""
        return self._appearance_theme_base

    @property
    def base_theme(self) -> ReviteBaseTheme:
        """:class:`ReviteBaseTheme`: The current base theme. Defaults to :attr:`ReviteBaseTheme.dark` if base theme is undefined."""
        return self._appearance_theme_base or ReviteBaseTheme.dark

    @property
    def custom_css(self) -> str | None:
        """Optional[:class:`str`]: The custom CSS string."""
        return self._appearance_theme_css

    def get_font(self) -> ReviteFont | None:
        """Optional[:class:`ReviteFont`]: The current Revite font."""
        return self._appearance_theme_font

    @property
    def font(self) -> ReviteFont:
        """:class:`ReviteFont`: The current Revite font. Defaults to :attr:`ReviteFont.open_sans` if font is undefined."""
        return self._appearance_theme_font or ReviteFont.open_sans

    def get_monofont(self) -> ReviteMonoFont | None:
        """Optional[:class:`ReviteMonoFont`]: The current Revite monospace font."""
        return self._appearance_theme_monofont

    @property
    def monofont(self) -> ReviteMonoFont:
        """:class:`ReviteMonoFont`: The current Revite monospace font. Defaults to :attr:`ReviteMonoFont.fira_code` if monofont is undefined."""
        return self._appearance_theme_monofont or ReviteMonoFont.fira_code

    def get_theme_overrides(self) -> dict[ReviteThemeVariable, str] | None:
        """Optional[Dict[:class:`ReviteThemeVariable`, :class:`str`]]: The theme overrides."""
        return self._appearance_theme_overrides

    @property
    def theme_overrides(self) -> dict[ReviteThemeVariable, str]:
        """Dict[:class:`ReviteThemeVariable`, :class:`str`]: The theme overrides."""
        return self._appearance_theme_overrides or {}

    def _parse(self) -> None:
        parent = self.parent

        changelog_json = parent.get("changelog")
        if changelog_json:
            changelog: raw.ReviteChangelog = utils.from_json(changelog_json)
            self.last_viewed_changelog_entry: ReviteChangelogEntry | None = (
                ReviteChangelogEntry(changelog["viewed"])
            )
        else:
            self.last_viewed_changelog_entry = None

        locale_json = parent.get("locale")
        if locale_json:
            locale: raw.ReviteLocaleOptions = utils.from_json(locale_json)
            self._language: Language | None = Language(locale["lang"])
        else:
            self._language = None

        notifications_json = parent.get("notifications")
        if notifications_json:
            notifications: raw.ReviteNotificationOptions = utils.from_json(
                notifications_json
            )
            self._notification_options: ReviteNotificationOptions | None = (
                ReviteNotificationOptions(notifications)
            )
        else:
            self._notification_options = None

        ordering_json = parent.get("ordering")
        if ordering_json:
            ordering: raw.ReviteOrdering = utils.from_json(ordering_json)
            self._ordering: list[str] | None = ordering["servers"]
        else:
            self._ordering = None

        appearance_json = parent.get("appearance")
        if appearance_json:
            appearance: raw.ReviteAppearanceSettings = utils.from_json(appearance_json)

            appearance_emoji_pack = appearance.get("appearance:emoji")
            if appearance_emoji_pack:
                self._appearance_emoji_pack: ReviteEmojiPack | None = ReviteEmojiPack(
                    appearance_emoji_pack
                )
            else:
                self._appearance_emoji_pack = None

            self.seasonal: bool | None = appearance.get("appearance:seasonal")
            self.transparent: bool | None = appearance.get("appearance:transparency")
        else:
            self._appearance_emoji_pack = None
            self.seasonal = None
            self.transparent = None

        theme_json = parent.get("theme")
        if theme_json:
            theme: raw.ReviteThemeSettings = utils.from_json(theme_json)

            self.ligatures: bool | None = theme.get("appearance:ligatures")

            base_theme = theme.get("appearance:theme:base")

            if base_theme:
                self._appearance_theme_base = ReviteBaseTheme(base_theme)
            else:
                self._appearance_theme_base = None
            self._appearance_theme_css = theme.get("appearance:theme:css")

            font = theme.get("appearance:theme:font")
            if font:
                self._appearance_theme_font: ReviteFont | None = ReviteFont(font)
            else:
                self._appearance_theme_font = None

            # Deprecated by base theme
            # self._appearance_theme_light: bool | None = theme.get('appearance:theme:light')

            monofont = theme.get("appearance:theme:monoFont")
            if monofont:
                self._appearance_theme_monofont: ReviteMonoFont | None = ReviteMonoFont(
                    monofont
                )
            else:
                self._appearance_theme_monofont = None
            self._appearance_theme_overrides: dict[ReviteThemeVariable, str] | None = (
                theme.get("appearance:theme:overrides")
            )

        else:
            self.ligatures = None
            self._appearance_theme_base = None
            self._appearance_theme_css = None
            self._appearance_theme_font = None
            # self._appearance_theme_light = None
            self._appearance_theme_monofont = None
            self._appearance_theme_overrides = None

    def payload_for(
        self,
        *,
        last_viewed_changelog_entry: UndefinedOr[
            ReviteChangelogEntry | int
        ] = UNDEFINED,
        language: UndefinedOr[Language] = UNDEFINED,
        notification_servers: UndefinedOr[
            dict[ULIDOr[BaseServer], ReviteNotificationState]
        ] = UNDEFINED,
        merge_notification_servers: bool = True,
        notification_channels: UndefinedOr[
            dict[ULIDOr[Channel], ReviteNotificationState]
        ] = UNDEFINED,
        merge_notification_channels: bool = True,
        ordering: UndefinedOr[list[ULIDOr[BaseServer]]] = UNDEFINED,
        # TODO: Use these parameters.
        emoji_pack: UndefinedOr[ReviteEmojiPack | None] = UNDEFINED,
        seasonal: UndefinedOr[bool | None] = UNDEFINED,
        transparent: UndefinedOr[bool | None] = UNDEFINED,
        ligatures: UndefinedOr[bool | None] = UNDEFINED,
        base_theme: UndefinedOr[ReviteBaseTheme | None] = UNDEFINED,
        css: UndefinedOr[str | None] = UNDEFINED,
        font: UndefinedOr[ReviteFont | None] = UNDEFINED,
        monofont: UndefinedOr[ReviteMonoFont | None] = UNDEFINED,
        overrides: UndefinedOr[dict[ReviteThemeVariable, str] | None] = UNDEFINED,
    ) -> raw.ReviteUserSettingsPayload:
        payload: raw.ReviteUserSettingsPayload = {}

        if is_defined(last_viewed_changelog_entry):
            viewed = (
                last_viewed_changelog_entry.value
                if isinstance(last_viewed_changelog_entry, ReviteChangelogEntry)
                else last_viewed_changelog_entry
            )

            changelog: raw.ReviteChangelog = {
                "viewed": viewed,  # type: ignore
            }

            payload["changelog"] = utils.to_json(changelog)

        if is_defined(language):
            locale: raw.ReviteLocaleOptions = {"lang": language.value}
            payload["locale"] = utils.to_json(locale)

        if is_defined(notification_servers) or is_defined(notification_channels):
            options = self._notification_options
            if options:
                if merge_notification_servers:
                    servers: dict[str, raw.ReviteNotificationState] = {
                        server_id: state.value
                        for server_id, state in options.servers.items()
                    }
                else:
                    servers = {}

                if merge_notification_channels:
                    channels: dict[str, raw.ReviteNotificationState] = {
                        channel_id: state.value
                        for channel_id, state in options.channels.items()
                    }
                else:
                    channels = {}
            else:
                servers = {}
                channels = {}

            notifications: raw.ReviteNotificationOptions = {
                "server": servers,
                "channel": channels,
            }

            if is_defined(notification_servers):
                server = notifications["server"] | {
                    resolve_id(server): state.value
                    for server, state in notification_servers.items()
                }
                notifications["server"] = server  # type: ignore

            if is_defined(notification_channels):
                channel = notifications["channel"] | {
                    resolve_id(channel): state.value
                    for channel, state in notification_channels.items()
                }
                notifications["channel"] = channel  # type: ignore
            payload["notifications"] = utils.to_json(notifications)

        if is_defined(ordering):
            payload["ordering"] = utils.to_json(
                {"servers": [resolve_id(server_id) for server_id in ordering]}
            )

        return payload


__all__ = (
    "UserSettings",
    "AndroidTheme",
    "AndroidProfilePictureShape",
    "AndroidMessageReplyStyle",
    "AndroidUserSettings",
    "ReviteChangelogEntry",
    "ReviteNotificationState",
    "ReviteNotificationOptions",
    "ReviteEmojiPack",
    "ReviteBaseTheme",
    "ReviteFont",
    "ReviteMonoFont",
    "ReviteThemeVariable",
    "ReviteUserSettings",
)
