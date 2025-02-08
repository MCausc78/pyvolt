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
import typing

from . import utils
from .core import UNDEFINED, UndefinedOr, ULIDOr, resolve_id
from .enums import (
    Language,
    AndroidTheme,
    AndroidMessageReplyStyle,
    AndroidProfilePictureShape,
    ReviteNotificationState,
    ReviteEmojiPack,
    ReviteBaseTheme,
    ReviteFont,
    ReviteMonoFont,
    ReviteChangelogEntry,
)

if typing.TYPE_CHECKING:
    from . import raw
    from .channel import Channel
    from .server import BaseServer
    from .state import State

D = typing.TypeVar('D')


class UserSettings:
    """Represents Revolt user settings.

    Attributes
    ----------
    state: :class:`.State`
        The state that manages current user settings.
    data: Dict[:class:`str`, Tuple[:class:`int`, :class:`str`]]
        The mapping of ``{key: (timestamp, value)}``.
    mocked: :class:`bool`
        Whether user settings are mocked. Mocked user settings are created by library itself, if not logged in, or in HTTP-only mode.
    partial: :class:`bool`
        Whether user settings are partial. This is set to ``True`` when used via :attr:`.UserSettingsUpdateEvent.partial`.
    """

    __slots__ = (
        'state',
        'data',
        'mocked',
        'partial',
        '_android',
        '_revite',
        '_jolt',
    )

    def __init__(
        self,
        *,
        data: dict[str, tuple[int, str]],
        state: State,
        mocked: bool,
        partial: bool,
    ) -> None:
        self.state: State = state
        self.data: dict[str, tuple[int, str]] = data
        self.mocked: bool = mocked
        self.partial: bool = partial
        self._parse(partial=None)

    def as_dict(self) -> dict[str, str]:
        """Dict[:class:`str`, :class:`str`]: The dictionary of `{key -> value}`."""
        return {k: v for k, (_, v) in self.data.items()}

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} data={self.data!r} mocked={self.mocked!r} partial={self.partial!r}>'

    def _parse(self, *, partial: typing.Optional[UserSettings]) -> None:
        if partial:
            if isinstance(self._android, AndroidUserSettings) and 'android' in partial.data:
                android_payload: raw.AndroidUserSettings = utils.from_json(partial['android'])
                self._android.locally_update(android_payload)
            if isinstance(self._revite, ReviteUserSettings):
                self._revite.locally_update(partial, full=False)
            if isinstance(self._jolt, JoltUserSettings):
                self._jolt.locally_update(partial, full=False)
        else:
            try:
                self._android: typing.Union[AndroidUserSettings, Exception] = AndroidUserSettings(self)
            except Exception as exc:
                self._android = exc

            try:
                self._revite: typing.Union[ReviteUserSettings, Exception] = ReviteUserSettings(self)
            except Exception as exc:
                self._revite = exc

            try:
                self._jolt: typing.Union[JoltUserSettings, Exception] = JoltUserSettings(self)
            except Exception as exc:
                self._jolt = exc

    def locally_update(self, partial: UserSettings, /) -> None:
        """Locally updates user settings with provided data.

        .. warning::
            This is called by library internally to keep settings up to date.

        Parameters
        ----------
        partial: :class:`.UserSettings`
            The data to update settings with.
        """
        self.data.update(partial.data)
        self._parse(partial=partial)

    @property
    def android(self) -> AndroidUserSettings:
        """:class:`.AndroidUserSettings`: The Android user settings.

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
        """:class:`.ReviteUserSettings`: The Revite user settings.

        Raises
        ------
        Exception
            If user settings are corrupted.
        """
        if isinstance(self._revite, Exception):
            raise self._revite from None
        return self._revite

    @property
    def jolt(self) -> JoltUserSettings:
        """:class:`.JoltUserSettings`: The Jolt user settings.

        Raises
        ------
        Exception
            If user settings are corrupted.
        """
        if isinstance(self._jolt, Exception):
            raise self._jolt from None
        return self._jolt

    def __getitem__(self, key: str) -> str:
        return self.data[key][1]

    def get(self, key: str, default: D = None) -> typing.Union[str, D]:
        """Union[:class:`str`, D]: Get a user setting."""
        if key in self.data:
            return self.data[key][1]
        return default

    async def edit(
        self,
        partial: dict[str, str],
        edited_at: typing.Optional[typing.Union[datetime, int]] = None,
    ) -> None:
        """|coro|

        Edits the current user settings.

        .. note::
            This can only be used by non-bot accounts.

        Parameters
        ----------
        partial: Dict[:class:`str`, :class:`str`]
            The dict to merge into the current user settings.
        edited_at: Optional[Union[:class:`~datetime.datetime`, :class:`int`]]
            The revision.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """
        return await self.state.http.edit_user_settings(partial=partial, edited_at=edited_at)


class AndroidUserSettings:
    """Represents Android user settings.

    Attributes
    ----------
    parent: :class:`.UserSettings`
        The parent.
    """

    __slots__ = (
        'parent',
        '_payload',
        '_special_embed_settings_payload',
        '_theme',
        '_color_overrides',
        '_reply_style',
        '_avatar_radius',
    )

    def __init__(self, parent: UserSettings, /) -> None:
        self.parent: UserSettings = parent
        payload: raw.AndroidUserSettings = utils.from_json(parent.get('android', '{}'))
        self._payload: raw.AndroidUserSettings = payload

        self.locally_update(payload)

    def locally_update(self, payload: raw.AndroidUserSettings, /) -> None:
        """Locally updates user settings with provided data.

        .. warning::
            This is called by library internally to keep settings up to date.

        Parameters
        ----------
        payload: raw.AndroidUserSettings
            The data to update settings with.
        """
        theme = payload.get('theme')

        if theme:
            self._theme: typing.Optional[AndroidTheme] = AndroidTheme(theme)
        else:
            self._theme = None

        self._color_overrides: typing.Optional[dict[str, int]] = payload.get('colourOverrides')
        reply_style = payload.get('messageReplyStyle')

        if reply_style:
            self._reply_style: typing.Optional[AndroidMessageReplyStyle] = AndroidMessageReplyStyle(reply_style)
        else:
            self._reply_style = None

        self._avatar_radius: typing.Optional[int] = payload.get('avatarRadius')

        special_embed_settings = payload.get('specialEmbedSettings')

        if special_embed_settings:
            self._special_embed_settings_payload: typing.Optional[raw.AndroidUserSettingsSpecialEmbedSettings] = (
                special_embed_settings
            )
        else:
            self._special_embed_settings_payload = None

    @property
    def theme(self) -> AndroidTheme:
        """:class:`.AndroidTheme`: The current theme."""
        return self._theme or AndroidTheme.system

    @property
    def color_overrides(self) -> dict[str, int]:
        """Dict[:class:`str`, :class:`int`]: The current theme color overrides."""
        return self._color_overrides or {}

    @property
    def reply_style(self) -> AndroidMessageReplyStyle:
        """:class:`.AndroidMessageReplyStyle`: The current theme."""
        return self._reply_style or AndroidMessageReplyStyle.swipe_to_reply

    @property
    def profile_picture_shape(self) -> int:
        """:class:`int`: The current profile picture shape."""
        return self._avatar_radius or 50

    @property
    def embed_youtube(self) -> bool:
        """:class:`bool`: Whether to render special YouTube embeds."""

        if self._special_embed_settings_payload is None:
            return True
        return self._special_embed_settings_payload['embedYouTube']

    @property
    def embed_apple_music(self) -> bool:
        """:class:`bool`: Whether to render special Apple Music embeds."""

        if self._special_embed_settings_payload is None:
            return True
        return self._special_embed_settings_payload['embedAppleMusic']

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} theme={self.theme!r} color_overrides={self.color_overrides!r} reply_style={self.reply_style!r} profile_picture_shape={self.profile_picture_shape!r}>'

    def payload_for(
        self,
        *,
        initial_payload: UndefinedOr[raw.AndroidUserSettings] = UNDEFINED,
        theme: UndefinedOr[typing.Optional[AndroidTheme]] = UNDEFINED,
        color_overrides: UndefinedOr[typing.Optional[dict[str, int]]] = UNDEFINED,
        reply_style: UndefinedOr[typing.Optional[AndroidMessageReplyStyle]] = UNDEFINED,
        avatar_radius: UndefinedOr[typing.Optional[typing.Union[AndroidProfilePictureShape, int]]] = UNDEFINED,
        embed_youtube: UndefinedOr[bool] = UNDEFINED,
        embed_apple_music: UndefinedOr[bool] = UNDEFINED,
        initial_special_embed_settings_payload: UndefinedOr[
            typing.Optional[raw.AndroidUserSettingsSpecialEmbedSettings]
        ] = UNDEFINED,
    ) -> raw.AndroidUserSettings:
        """Builds a payload for Android user settings. You must pass it as JSON string to :meth:`HTTPClient.edit_user_settings`, like so:

        .. code-block:: python3

            payload = settings.payload_for(theme=AndroidTheme.material_you)
            await http.edit_user_settings(android=json.dumps(payload))

        Parameters
        ----------
        initial_payload: UndefinedOr[raw.AndroidUserSettings]
            The initial payload.
        theme: UndefinedOr[Optional[:class:`.AndroidTheme`]]
            The new theme.  Could be ``None`` to remove it from internal object.
        color_overrides: UndefinedOr[Optional[Dict[:class:`str`, :class:`int`]]]
            The new color overrides. Passing ``None`` denotes ``colourOverrides`` removal in internal object.
        reply_style: UndefinedOr[Optional[:class:`.AndroidMessageReplyStyle`]]
            The new message reply style. Passing ``None`` denotes ``messageReplyStyle`` removal in internal object.
        avatar_radius: UndefinedOr[Optional[Union[:class:`.AndroidProfilePictureShape`, :class:`int`]]]
            The new avatar radius. Passing ``None`` denotes ``avatarRadius`` removal in internal object.
        initial_special_embed_settings_payload: UndefinedOr[Optional[raw.AndroidUserSettingsSpecialEmbedSettings]]
            The initial payload. Could be ``None`` to remove it from internal object.
        embed_youtube: UndefinedOr[:class:`bool`]
            Whether to render special YouTube embeds.
        embed_apple_music: UndefinedOr[:class:`bool`]
            Whether to render special Apple Music embeds.
        """

        if initial_payload is not UNDEFINED:
            payload = copy(initial_payload)
        else:
            payload = copy(self._payload)

        if theme is not UNDEFINED:
            if theme is None:
                payload.pop('theme', None)
            else:
                payload['theme'] = theme.value

        if color_overrides is not UNDEFINED:
            if color_overrides is None:
                payload.pop('colourOverrides', None)
            else:
                payload['colourOverrides'] = color_overrides

        if reply_style is not UNDEFINED:
            if reply_style is None:
                payload.pop('messageReplyStyle', None)
            else:
                payload['messageReplyStyle'] = reply_style.value

        if avatar_radius is not UNDEFINED:
            if avatar_radius is None:
                payload.pop('avatarRadius', None)
            elif isinstance(avatar_radius, AndroidProfilePictureShape):
                payload['avatarRadius'] = avatar_radius.value
            else:
                payload['avatarRadius'] = avatar_radius

        if initial_special_embed_settings_payload is UNDEFINED:
            special_embed_settings_payload: typing.Optional[raw.AndroidUserSettingsSpecialEmbedSettings] = (
                self._special_embed_settings_payload
            )
        elif initial_special_embed_settings_payload is None:
            special_embed_settings_payload = payload.pop('specialEmbedSettings', None)
        else:
            special_embed_settings_payload = self._special_embed_settings_payload

        if embed_youtube is not UNDEFINED or embed_apple_music is not UNDEFINED:
            if special_embed_settings_payload is None:
                special_embed_settings_payload = {
                    'embedYouTube': True if embed_youtube is UNDEFINED else embed_youtube,
                    'embedAppleMusic': True if embed_apple_music is UNDEFINED else embed_apple_music,
                }
            else:
                special_embed_settings_payload = special_embed_settings_payload | {
                    'embedYouTube': True if embed_youtube is UNDEFINED else embed_youtube,
                    'embedAppleMusic': True if embed_apple_music is UNDEFINED else embed_apple_music,
                }

        if special_embed_settings_payload is not None:
            payload['specialEmbedSettings'] = special_embed_settings_payload

        return payload

    async def edit(
        self,
        *,
        edited_at: typing.Optional[typing.Union[datetime, int]] = None,
        theme: UndefinedOr[typing.Optional[AndroidTheme]] = UNDEFINED,
        color_overrides: UndefinedOr[typing.Optional[dict[str, int]]] = UNDEFINED,
        reply_style: UndefinedOr[typing.Optional[AndroidMessageReplyStyle]] = UNDEFINED,
        avatar_radius: UndefinedOr[typing.Optional[typing.Union[AndroidProfilePictureShape, int]]] = UNDEFINED,
        embed_youtube: UndefinedOr[bool] = UNDEFINED,
        embed_apple_music: UndefinedOr[bool] = UNDEFINED,
        initial_special_embed_settings_payload: UndefinedOr[
            typing.Optional[raw.AndroidUserSettingsSpecialEmbedSettings]
        ] = UNDEFINED,
    ) -> None:
        """|coro|

        Edits the Android user settings.

        Parameters
        ----------
        edited_at: Optional[Union[:class:`~datetime.datetime`, :class:`int`]]
            External parameter to pass in :meth:`.HTTPClient.edit_user_settings`.
        theme: UndefinedOr[Optional[:class:`.AndroidTheme`]]
            The new theme.  Could be ``None`` to remove it from internal object.
        color_overrides: UndefinedOr[Optional[Dict[:class:`str`, :class:`int`]]]
            The new color overrides. Passing ``None`` denotes ``colourOverrides`` removal in internal object.
        reply_style: UndefinedOr[Optional[:class:`.AndroidMessageReplyStyle`]]
            The new message reply style. Passing ``None`` denotes ``messageReplyStyle`` removal in internal object.
        avatar_radius: UndefinedOr[Optional[Union[:class:`.AndroidProfilePictureShape`, :class:`int`]]]
            The new avatar radius. Passing ``None`` denotes ``avatarRadius`` removal in internal object.
        initial_special_embed_settings_payload: UndefinedOr[Optional[raw.AndroidUserSettingsSpecialEmbedSettings]]
            The initial payload. Could be ``None`` to remove it from internal object.
        embed_youtube: UndefinedOr[:class:`bool`]
            Whether to render special YouTube embeds.
        embed_apple_music: UndefinedOr[:class:`bool`]
            Whether to render special Apple Music embeds.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """
        payload = self.payload_for(
            theme=theme,
            color_overrides=color_overrides,
            reply_style=reply_style,
            avatar_radius=avatar_radius,
            embed_youtube=embed_youtube,
            embed_apple_music=embed_apple_music,
            initial_special_embed_settings_payload=initial_special_embed_settings_payload,
        )
        await self.parent.edit({'android': utils.to_json(payload)}, edited_at)


class ReviteNotificationOptions:
    """Represents Revite notification options.

    Attributes
    ----------
    servers: Dict[:class:`str`, :class:`.ReviteNotificationState`]
        The servers.
    channels: Dict[:class:`str`, :class:`.ReviteNotificationState`]
        The channels.
    """

    __slots__ = ('servers', 'channels')

    def __init__(self, data: raw.ReviteNotificationOptions) -> None:
        self.servers: dict[str, ReviteNotificationState] = {
            server_id: ReviteNotificationState(state) for server_id, state in data['server'].items()
        }
        self.channels: dict[str, ReviteNotificationState] = {
            channel_id: ReviteNotificationState(state) for channel_id, state in data['channel'].items()
        }

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} servers={self.servers!r} channels={self.channels!r}>'


ReviteThemeVariable: typing.TypeAlias = 'raw.ReviteThemeVariable'


class ReviteUserSettings:
    """Represents Revite user settings.

    Attributes
    ----------
    parent: :class:`.UserSettings`
        The raw user settings.
    last_viewed_changelog_entry: Optional[:class:`.ReviteChangelogEntry`]
        The last viewed changelog entry.
    seasonal: Optional[:class:`bool`]
        Whether to display effects in the home tab during holiday seasons or not.
    transparent: Optional[:class:`bool`]
        Whether to enable transparency effects throughout the app or not.
    ligatures: Optional[:class:`bool`]
        Whether to combine characters together or not.
        For example, ``->`` turns into an arrow if this property is ``True``.
        Applicable only for supported fonts (such as :attr:`.ReviteFont.inter`).
    """

    __slots__ = (
        'parent',
        '_changelog_payload',
        'last_viewed_changelog_entry',
        '_locale_payload',
        '_language',
        '_notifications_payload',
        '_notification_options',
        '_ordering_payload',
        '_ordering',
        '_appearance_payload',
        '_appearance_emoji_pack',
        'seasonal',
        'transparent',
        'ligatures',
        '_theme_payload',
        '_appearance_theme_base',
        '_appearance_theme_css',
        '_appearance_theme_font',
        # "_appearance_theme_light",
        '_appearance_theme_monofont',
        '_appearance_theme_overrides',
    )

    def __init__(self, parent: UserSettings, /) -> None:
        self.parent: UserSettings = parent
        self.locally_update(parent, full=True)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} last_viewed_changelog_entry={self.last_viewed_changelog_entry!r} language={self.language!r} notification_options={self._notification_options!r} ordering={self.ordering!r} emoji_pack={self.emoji_pack!r} seasonal={self.seasonal!r} transparent={self.transparent!r} ligatures={self.ligatures!r} base_theme={self.base_theme!r} custom_css={self.custom_css!r} font={self.font!r} monofont={self.monofont!r} theme_overrides={self.theme_overrides!r}>'

    def get_language(self) -> typing.Optional[Language]:
        """Optional[:class:`.Language`]: The current language."""
        return self._language

    @property
    def language(self) -> Language:
        """:class:`.Language`: The current language. Defaults to :attr:`.Language.english_simplified` if language is undefined."""
        return self._language or Language.english

    def get_notification_options(self) -> typing.Optional[ReviteNotificationOptions]:
        """Optional[:class:`.ReviteNotificationOptions`]: The notification options."""
        return self._notification_options

    @property
    def notification_options(self) -> ReviteNotificationOptions:
        """:class:`.ReviteNotificationOptions`: The notification options."""
        return self._notification_options or ReviteNotificationOptions({'server': {}, 'channel': {}})

    @property
    def ordering(self) -> list[str]:
        """List[:class:`str`]: The server ordering."""
        return self._ordering or []

    def get_emoji_pack(self) -> typing.Optional[ReviteEmojiPack]:
        """Optional[:class:`.ReviteEmojiPack`]: Gets the current emoji pack."""
        return self._appearance_emoji_pack

    @property
    def emoji_pack(self) -> ReviteEmojiPack:
        """:class:`.ReviteEmojiPack`: The current emoji pack."""
        return self._appearance_emoji_pack or ReviteEmojiPack.mutant_remix

    def is_seasonal(self) -> bool:
        """:class:`bool`: Whether to display effects in the home tab during holiday seasons or not."""
        return self.seasonal is not False

    def is_transparent(self) -> bool:
        """Whether to enable transparency effects throughout the app or not."""
        return self.transparent is not False

    def is_ligatures_enabled(self) -> bool:
        """:class:`bool`: Whether to combine characters together or not.
        For example, ``->`` turns into an arrow if this property is ``True``.

        Applicable only for supported fonts (such as :attr:`.ReviteFont.inter`).
        """
        return self.ligatures is not False

    def get_base_theme(self) -> typing.Optional[ReviteBaseTheme]:
        """Optional[:class:`.ReviteBaseTheme`]: The current base theme."""
        return self._appearance_theme_base

    @property
    def base_theme(self) -> ReviteBaseTheme:
        """:class:`.ReviteBaseTheme`: The current base theme. Defaults to :attr:`.ReviteBaseTheme.dark` if base theme is undefined."""
        return self._appearance_theme_base or ReviteBaseTheme.dark

    @property
    def custom_css(self) -> typing.Optional[str]:
        """Optional[:class:`str`]: The custom CSS string."""
        return self._appearance_theme_css

    def get_font(self) -> typing.Optional[ReviteFont]:
        """Optional[:class:`.ReviteFont`]: The current Revite font."""
        return self._appearance_theme_font

    @property
    def font(self) -> ReviteFont:
        """:class:`.ReviteFont`: The current Revite font. Defaults to :attr:`.ReviteFont.open_sans` if font is undefined."""
        return self._appearance_theme_font or ReviteFont.open_sans

    def get_monofont(self) -> typing.Optional[ReviteMonoFont]:
        """Optional[:class:`.ReviteMonoFont`]: The current Revite monospace font."""
        return self._appearance_theme_monofont

    @property
    def monofont(self) -> ReviteMonoFont:
        """:class:`.ReviteMonoFont`: The current Revite monospace font. Defaults to :attr:`.ReviteMonoFont.fira_code` if monofont is undefined."""
        return self._appearance_theme_monofont or ReviteMonoFont.fira_code

    def get_theme_overrides(self) -> typing.Optional[dict[ReviteThemeVariable, str]]:
        """Optional[Dict[:class:`.ReviteThemeVariable`, :class:`str`]]: The theme overrides."""
        return self._appearance_theme_overrides

    @property
    def theme_overrides(self) -> dict[ReviteThemeVariable, str]:
        """Dict[:class:`.ReviteThemeVariable`, :class:`str`]: The theme overrides."""
        return self._appearance_theme_overrides or {}

    def _on_changelog(self, changelog: raw.ReviteChangelog, /) -> None:
        self._changelog_payload: typing.Optional[raw.ReviteChangelog] = changelog
        self.last_viewed_changelog_entry: typing.Optional[ReviteChangelogEntry] = ReviteChangelogEntry(
            changelog['viewed']
        )

    def _on_locale(self, locale: raw.ReviteLocaleOptions, /) -> None:
        self._locale_payload: typing.Optional[raw.ReviteLocaleOptions] = locale
        self._language: typing.Optional[Language] = Language(locale['lang'])

    def _on_notifications(self, notifications: raw.ReviteNotificationOptions, /) -> None:
        self._notifications_payload: typing.Optional[raw.ReviteNotificationOptions] = notifications
        self._notification_options: typing.Optional[ReviteNotificationOptions] = ReviteNotificationOptions(
            notifications
        )

    def _on_ordering(self, ordering: raw.ReviteOrdering, /) -> None:
        self._ordering_payload: typing.Optional[raw.ReviteOrdering] = ordering
        self._ordering: typing.Optional[list[str]] = ordering['servers']

    def _on_appearance(self, appearance: raw.ReviteAppearanceSettings, /) -> None:
        self._appearance_payload: typing.Optional[raw.ReviteAppearanceSettings] = appearance

        appearance_emoji_pack = appearance.get('appearance:emoji')
        if appearance_emoji_pack:
            self._appearance_emoji_pack: typing.Optional[ReviteEmojiPack] = ReviteEmojiPack(appearance_emoji_pack)
        else:
            self._appearance_emoji_pack = None

        self.seasonal: typing.Optional[bool] = appearance.get('appearance:seasonal')
        self.transparent: typing.Optional[bool] = appearance.get('appearance:transparency')

    def _on_theme(self, theme: raw.ReviteThemeSettings, /) -> None:
        self._theme_payload: typing.Optional[raw.ReviteThemeSettings] = theme

        self.ligatures: typing.Optional[bool] = theme.get('appearance:ligatures')

        base_theme = theme.get('appearance:theme:base')

        if base_theme:
            self._appearance_theme_base = ReviteBaseTheme(base_theme)
        else:
            self._appearance_theme_base = None
        self._appearance_theme_css = theme.get('appearance:theme:css')

        font = theme.get('appearance:theme:font')
        if font:
            self._appearance_theme_font: typing.Optional[ReviteFont] = ReviteFont(font)
        else:
            self._appearance_theme_font = None

        # Deprecated by base theme
        # self._appearance_theme_light: typing.Optional[bool] = theme.get('appearance:theme:light')

        monofont = theme.get('appearance:theme:monoFont')
        if monofont:
            self._appearance_theme_monofont: typing.Optional[ReviteMonoFont] = ReviteMonoFont(monofont)
        else:
            self._appearance_theme_monofont = None
        self._appearance_theme_overrides: typing.Optional[dict[ReviteThemeVariable, str]] = theme.get(
            'appearance:theme:overrides'
        )

    def locally_update(self, payload: UserSettings, /, *, full: bool) -> None:
        """Locally updates user settings with provided data.

        .. warning::
            This is called by library internally to keep settings up to date.

        Parameters
        ----------
        payload: :class:`.UserSettings`
            The data to update settings with.
        full: :class:`bool`
            Whether the payload is full.
        """
        changelog_json = payload.get('changelog')
        if changelog_json:
            changelog: raw.ReviteChangelog = utils.from_json(changelog_json)
            self._on_changelog(changelog)
        elif full:
            self._changelog_payload = None
            self.last_viewed_changelog_entry = None

        locale_json = payload.get('locale')
        if locale_json:
            locale: raw.ReviteLocaleOptions = utils.from_json(locale_json)
            self._on_locale(locale)
        elif full:
            self._locale_payload = None
            self._language = None

        notifications_json = payload.get('notifications')
        if notifications_json:
            notifications: raw.ReviteNotificationOptions = utils.from_json(notifications_json)
            self._on_notifications(notifications)
        elif full:
            self._notifications_payload = None
            self._notification_options = None

        ordering_json = payload.get('ordering')
        if ordering_json:
            ordering: raw.ReviteOrdering = utils.from_json(ordering_json)
            self._on_ordering(ordering)
        elif full:
            self._ordering_payload = None
            self._ordering = None

        appearance_json = payload.get('appearance')
        if appearance_json:
            appearance: raw.ReviteAppearanceSettings = utils.from_json(appearance_json)
            self._on_appearance(appearance)
        elif full:
            self._appearance_payload = None
            self._appearance_emoji_pack = None
            self.seasonal = None
            self.transparent = None

        theme_json = payload.get('theme')
        if theme_json:
            theme: raw.ReviteThemeSettings = utils.from_json(theme_json)
            self._on_theme(theme)
        elif full:
            self._theme_payload = None
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
        initial_changelog_payload: UndefinedOr[raw.ReviteChangelog] = UNDEFINED,
        last_viewed_changelog_entry: UndefinedOr[typing.Union[ReviteChangelogEntry, int]] = UNDEFINED,
        initial_locale_payload: UndefinedOr[raw.ReviteLocaleOptions] = UNDEFINED,
        language: UndefinedOr[Language] = UNDEFINED,
        initial_notifications_payload: UndefinedOr[raw.ReviteNotificationOptions] = UNDEFINED,
        server_notifications: UndefinedOr[dict[ULIDOr[BaseServer], ReviteNotificationState]] = UNDEFINED,
        merge_server_notifications: bool = True,
        channel_notifications: UndefinedOr[dict[ULIDOr[Channel], ReviteNotificationState]] = UNDEFINED,
        merge_channel_notifications: bool = True,
        initial_ordering_payload: UndefinedOr[raw.ReviteOrdering] = UNDEFINED,
        ordering: UndefinedOr[list[ULIDOr[BaseServer]]] = UNDEFINED,
        initial_appearance_payload: UndefinedOr[raw.ReviteAppearanceSettings] = UNDEFINED,
        emoji_pack: UndefinedOr[typing.Optional[ReviteEmojiPack]] = UNDEFINED,
        seasonal: UndefinedOr[typing.Optional[bool]] = UNDEFINED,
        transparent: UndefinedOr[typing.Optional[bool]] = UNDEFINED,
        initial_theme_payload: UndefinedOr[raw.ReviteThemeSettings] = UNDEFINED,
        ligatures: UndefinedOr[typing.Optional[bool]] = UNDEFINED,
        base_theme: UndefinedOr[typing.Optional[ReviteBaseTheme]] = UNDEFINED,
        custom_css: UndefinedOr[typing.Optional[str]] = UNDEFINED,
        font: UndefinedOr[typing.Optional[ReviteFont]] = UNDEFINED,
        monofont: UndefinedOr[typing.Optional[ReviteMonoFont]] = UNDEFINED,
        overrides: UndefinedOr[typing.Optional[dict[ReviteThemeVariable, str]]] = UNDEFINED,
    ) -> raw.ReviteUserSettingsPayload:
        """Builds a payload for Revite user settings. You must pass it as first argument to :meth:`.HTTPClient.edit_user_settings`, like so:

        .. code-block:: python3

            payload = settings.payload_for(language=Language.russian)
            await http.edit_user_settings(payload)

        Parameters
        ----------
        initial_changelog_payload: UndefinedOr[raw.ReviteChangelog]
            The initial ``changelog`` payload.
        last_viewed_changelog_entry: UndefinedOr[Union[:class:`.ReviteChangelogEntry`, :class:`int`]]
            The last viewed changelog entry.
        initial_locale_payload: UndefinedOr[raw.ReviteLocaleOptions]
            The initial ``locale`` payload.
        language: UndefinedOr[:class:`.Language`]
            The language.
        initial_notifications_payload: UndefinedOr[raw.ReviteNotificationOptions]
            The initial ``notifications`` payload.
        server_notifications: UndefinedOr[Dict[ULIDOr[:class:`.BaseServer`], :class:`.ReviteNotificationState`]]
            The notification options for servers.
        merge_server_notifications: :class:`bool`
            Whether to merge new servers notifications options into existing ones. Defaults to ``True``.
        channel_notifications: UndefinedOr[Dict[ULIDOr[:class:`.Channel`], :class:`.ReviteNotificationState`]]
            The notification options for channels.
        merge_channel_notifications: :class:`bool`
            Whether to merge new channels notifications options into existing ones. Defaults to ``True``.
        initial_ordering_payload: UndefinedOr[raw.ReviteOrdering]
            The initial ``ordering`` payload.
        ordering: UndefinedOr[List[ULIDOr[:class:`.BaseServer`]]]
            The servers tab order.
        initial_appearance_payload: UndefinedOr[raw.ReviteAppearanceSettings]
            The initial ``appearance`` payload.
        emoji_pack: UndefinedOr[Optional[:class:`.ReviteEmojiPack`]]
            The new emoji pack to use. Passing ``None`` denotes ``appearance.appearance:emoji`` removal in internal object.
        seasonal: UndefinedOr[Optional[:class:`bool`]]
            To display effects in the home tab during holiday seasons or not.
            Passing ``None`` denotes ``appearance.appearance:seasonal`` removal in internal object.
        transparent: UndefinedOr[Optional[:class:`bool`]]
            To enable transparency effects throughout the app or not.
            Passing ``None`` denotes ``appearance.appearance:transparency`` removal in internal object.
        initial_theme_payload: UndefinedOr[raw.ReviteThemeSettings]
            The initial ``theme`` payload.
        ligatures: UndefinedOr[Optional[:class:`bool`]]
            To combine characters together or not. More details in :attr:`.ReviteUserSettings.ligatures`.
            Passing ``None`` denotes ``theme.appearance:ligatures`` removal in internal object.
        base_theme: UndefinedOr[Optional[:class:`.ReviteBaseTheme`]]
            The base theme to use.
            Passing ``None`` denotes ``theme.appearance:theme:base`` removal in internal object.
        custom_css: UndefinedOr[Optional[:class:`str`]]
            The CSS string.
            Passing ``None`` denotes ``theme.appearance:theme:css`` removal in internal object.
        font: UndefinedOr[Optional[:class:`.ReviteFont`]]
            The font to use across the app.
            Passing ``None`` denotes ``theme.appearance:theme:font`` removal in internal object.
        monofont: UndefinedOr[Optional[:class:`.ReviteMonoFont`]]
            The monospace font to use in codeblocks.
            Passing ``None`` denotes ``theme.appearance:theme:monoFont`` removal in internal object.
        overrides: UndefinedOr[Optional[Dict[:class:`.ReviteThemeVariable`, :class:`str`]]]
            The theme overrides.
            Passing ``None`` denotes ``theme.appearance:theme:overrides`` removal in internal object.

        Returns
        -------
        Dict[:class:`str`, Any]
            The payload that must to be passed in :meth:`.HTTPClient.edit_user_settings`.
        """
        payload: raw.ReviteUserSettingsPayload = {}

        if last_viewed_changelog_entry is not UNDEFINED:
            changelog_payload = (
                self._changelog_payload if initial_changelog_payload is UNDEFINED else initial_changelog_payload
            )

            viewed = (
                last_viewed_changelog_entry.value
                if isinstance(last_viewed_changelog_entry, ReviteChangelogEntry)
                else last_viewed_changelog_entry
            )

            if changelog_payload is not None:
                changelog: raw.ReviteChangelog = changelog_payload | {'viewed': viewed}
            else:
                changelog = {'viewed': viewed}

            payload['changelog'] = utils.to_json(changelog)

        if language is not UNDEFINED:
            locale_payload = self._locale_payload if initial_locale_payload is UNDEFINED else initial_locale_payload

            if locale_payload is not None:
                locale: raw.ReviteLocaleOptions = locale_payload | {'lang': language.value}
            else:
                locale = {'lang': language.value}
            payload['locale'] = utils.to_json(locale)

        if server_notifications is not UNDEFINED or channel_notifications is not UNDEFINED:
            notifications_payload = (
                self._notifications_payload
                if initial_notifications_payload is UNDEFINED
                else initial_notifications_payload
            )

            options = self._notification_options
            if options:
                if merge_server_notifications:
                    servers: dict[str, raw.ReviteNotificationState] = {
                        server_id: state.value for server_id, state in options.servers.items()
                    }
                else:
                    servers = {}

                if merge_channel_notifications:
                    channels: dict[str, raw.ReviteNotificationState] = {
                        channel_id: state.value for channel_id, state in options.channels.items()
                    }
                else:
                    channels = {}
            else:
                servers = {}
                channels = {}

            if notifications_payload is not None:
                notifications: raw.ReviteNotificationOptions = notifications_payload | {
                    'server': servers,
                    'channel': channels,
                }
            else:
                notifications: raw.ReviteNotificationOptions = {
                    'server': servers,
                    'channel': channels,
                }

            if server_notifications is not UNDEFINED:
                server_payload = notifications['server'] | {
                    resolve_id(server): state.value for server, state in server_notifications.items()
                }
                # I literally don't know why it errors...
                notifications['server'] = server_payload  # type: ignore
            if channel_notifications is not UNDEFINED:
                channel_payload = notifications['channel'] | {
                    resolve_id(channel): state.value for channel, state in channel_notifications.items()
                }
                notifications['channel'] = channel_payload  # type: ignore
            payload['notifications'] = utils.to_json(notifications)

        if ordering is not UNDEFINED:
            existing_ordering_payload = (
                self._ordering_payload if initial_ordering_payload is UNDEFINED else initial_ordering_payload
            )

            if existing_ordering_payload is not None:
                ordering_payload: raw.ReviteOrdering = existing_ordering_payload | {
                    'servers': [resolve_id(server_id) for server_id in ordering]
                }
            else:
                ordering_payload: raw.ReviteOrdering = {'servers': [resolve_id(server_id) for server_id in ordering]}
            payload['ordering'] = utils.to_json(ordering_payload)

        if emoji_pack is not UNDEFINED or seasonal is not UNDEFINED or transparent is not UNDEFINED:
            if initial_appearance_payload is UNDEFINED:
                if self._appearance_payload is not None:
                    appearance_payload: raw.ReviteAppearanceSettings = copy(self._appearance_payload)
                else:
                    appearance_payload = {}
            else:
                appearance_payload = initial_appearance_payload

            if emoji_pack is None:
                appearance_payload.pop('appearance:emoji', None)
            elif emoji_pack is not UNDEFINED:
                appearance_payload['appearance:emoji'] = emoji_pack.value

            if seasonal is None:
                appearance_payload.pop('appearance:seasonal', None)
            elif seasonal is not UNDEFINED:
                appearance_payload['appearance:seasonal'] = seasonal

            if transparent is None:
                appearance_payload.pop('appearance:transparency', None)
            elif transparent is not UNDEFINED:
                appearance_payload['appearance:transparency'] = transparent

            payload['appearance'] = utils.to_json(appearance_payload)

        if (
            ligatures is not UNDEFINED
            or base_theme is not UNDEFINED
            or custom_css is not UNDEFINED
            or font is not UNDEFINED
            or monofont is not UNDEFINED
            or overrides is not UNDEFINED
        ):
            if initial_theme_payload is UNDEFINED:
                if self._theme_payload is not None:
                    theme_payload: raw.ReviteThemeSettings = copy(self._theme_payload)
                else:
                    theme_payload = {}
            else:
                theme_payload = copy(initial_theme_payload)

            if ligatures is None:
                theme_payload.pop('appearance:ligatures', None)
            elif ligatures is not UNDEFINED:
                theme_payload['appearance:ligatures'] = ligatures

            if base_theme is None:
                theme_payload.pop('appearance:theme:base', None)
            elif base_theme is not UNDEFINED:
                theme_payload['appearance:theme:base'] = base_theme.value

            if custom_css is None:
                theme_payload.pop('appearance:theme:css', None)
            elif custom_css is not UNDEFINED:
                theme_payload['appearance:theme:css'] = custom_css

            if font is None:
                theme_payload.pop('appearance:theme:font', None)
            elif font is not UNDEFINED:
                theme_payload['appearance:theme:font'] = font.value

            if monofont is None:
                theme_payload.pop('appearance:theme:monoFont', None)
            elif monofont is not UNDEFINED:
                theme_payload['appearance:theme:monoFont'] = monofont.value

            if overrides is None:
                theme_payload.pop('appearance:theme:overrides', None)
            elif overrides is not UNDEFINED:
                theme_payload['appearance:theme:overrides'] = overrides

            payload['theme'] = utils.to_json(theme_payload)

        return payload

    async def edit(
        self,
        *,
        edited_at: typing.Optional[typing.Union[datetime, int]] = None,
        initial_changelog_payload: UndefinedOr[raw.ReviteChangelog] = UNDEFINED,
        last_viewed_changelog_entry: UndefinedOr[typing.Union[ReviteChangelogEntry, int]] = UNDEFINED,
        initial_locale_payload: UndefinedOr[raw.ReviteLocaleOptions] = UNDEFINED,
        language: UndefinedOr[Language] = UNDEFINED,
        initial_notifications_payload: UndefinedOr[raw.ReviteNotificationOptions] = UNDEFINED,
        server_notifications: UndefinedOr[dict[ULIDOr[BaseServer], ReviteNotificationState]] = UNDEFINED,
        merge_server_notifications: bool = True,
        channel_notifications: UndefinedOr[dict[ULIDOr[Channel], ReviteNotificationState]] = UNDEFINED,
        merge_channel_notifications: bool = True,
        initial_ordering_payload: UndefinedOr[raw.ReviteOrdering] = UNDEFINED,
        ordering: UndefinedOr[list[ULIDOr[BaseServer]]] = UNDEFINED,
        initial_appearance_payload: UndefinedOr[raw.ReviteAppearanceSettings] = UNDEFINED,
        emoji_pack: UndefinedOr[typing.Optional[ReviteEmojiPack]] = UNDEFINED,
        seasonal: UndefinedOr[typing.Optional[bool]] = UNDEFINED,
        transparent: UndefinedOr[typing.Optional[bool]] = UNDEFINED,
        initial_theme_payload: UndefinedOr[raw.ReviteThemeSettings] = UNDEFINED,
        ligatures: UndefinedOr[typing.Optional[bool]] = UNDEFINED,
        base_theme: UndefinedOr[typing.Optional[ReviteBaseTheme]] = UNDEFINED,
        custom_css: UndefinedOr[typing.Optional[str]] = UNDEFINED,
        font: UndefinedOr[typing.Optional[ReviteFont]] = UNDEFINED,
        monofont: UndefinedOr[typing.Optional[ReviteMonoFont]] = UNDEFINED,
        overrides: UndefinedOr[typing.Optional[dict[ReviteThemeVariable, str]]] = UNDEFINED,
    ) -> None:
        """|coro|

        Edits the Revite user settings.

        Parameters
        ----------
        edited_at: Optional[Union[:class:`~datetime.datetime`, :class:`int`]]
            External parameter to pass in :meth:`.HTTPClient.edit_user_settings`.
        initial_changelog_payload: UndefinedOr[raw.ReviteChangelog]
            The initial ``changelog`` payload.
        last_viewed_changelog_entry: UndefinedOr[Union[:class:`.ReviteChangelogEntry`, :class:`int`]]
            The last viewed changelog entry.
        initial_locale_payload: UndefinedOr[raw.ReviteLocaleOptions]
            The initial ``locale`` payload.
        language: UndefinedOr[:class:`.Language`]
            The language.
        initial_notifications_payload: UndefinedOr[raw.ReviteNotificationOptions]
            The initial ``notifications`` payload.
        server_notifications: UndefinedOr[Dict[ULIDOr[:class:`.BaseServer`], :class:`.ReviteNotificationState`]]
            The notification options for servers.
        merge_server_notifications: :class:`bool`
            Whether to merge new servers notifications options into existing ones. Defaults to ``True``.
        channel_notifications: UndefinedOr[Dict[ULIDOr[:class:`.Channel`], :class:`.ReviteNotificationState`]]
            The notification options for channels.
        merge_channel_notifications: :class:`bool`
            Whether to merge new channels notifications options into existing ones. Defaults to ``True``.
        initial_ordering_payload: UndefinedOr[raw.ReviteOrdering]
            The initial ``ordering`` payload.
        ordering: UndefinedOr[List[ULIDOr[:class:`.BaseServer`]]]
            The servers tab order.
        initial_appearance_payload: UndefinedOr[raw.ReviteAppearanceSettings]
            The initial ``appearance`` payload.
        emoji_pack: UndefinedOr[Optional[:class:`.ReviteEmojiPack`]]
            The new emoji pack to use. Passing ``None`` denotes ``appearance.appearance:emoji`` removal in internal object.
        seasonal: UndefinedOr[Optional[:class:`bool`]]
            To display effects in the home tab during holiday seasons or not.
            Passing ``None`` denotes ``appearance.appearance:seasonal`` removal in internal object.
        transparent: UndefinedOr[Optional[:class:`bool`]]
            To enable transparency effects throughout the app or not.
            Passing ``None`` denotes ``appearance.appearance:transparency`` removal in internal object.
        initial_theme_payload: UndefinedOr[raw.ReviteThemeSettings]
            The initial ``theme`` payload.
        ligatures: UndefinedOr[Optional[:class:`bool`]]
            To combine characters together or not. More details in :attr:`.ReviteUserSettings.ligatures`.
            Passing ``None`` denotes ``theme.appearance:ligatures`` removal in internal object.
        base_theme: UndefinedOr[Optional[:class:`.ReviteBaseTheme`]]
            The base theme to use.
            Passing ``None`` denotes ``theme.appearance:theme:base`` removal in internal object.
        custom_css: UndefinedOr[Optional[:class:`str`]]
            The CSS string.
            Passing ``None`` denotes ``theme.appearance:theme:css`` removal in internal object.
        font: UndefinedOr[Optional[:class:`.ReviteFont`]]
            The font to use across the app.
            Passing ``None`` denotes ``theme.appearance:theme:font`` removal in internal object.
        monofont: UndefinedOr[Optional[:class:`.ReviteMonoFont`]]
            The monospace font to use in codeblocks.
            Passing ``None`` denotes ``theme.appearance:theme:monoFont`` removal in internal object.
        overrides: UndefinedOr[Optional[Dict[:class:`.ReviteThemeVariable`, :class:`str`]]]
            The theme overrides.
            Passing ``None`` denotes ``theme.appearance:theme:overrides`` removal in internal object.

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """

        payload: raw.ReviteUserSettingsPayload = self.payload_for(
            initial_changelog_payload=initial_changelog_payload,
            last_viewed_changelog_entry=last_viewed_changelog_entry,
            initial_locale_payload=initial_locale_payload,
            language=language,
            initial_notifications_payload=initial_notifications_payload,
            server_notifications=server_notifications,
            merge_server_notifications=merge_server_notifications,
            channel_notifications=channel_notifications,
            merge_channel_notifications=merge_channel_notifications,
            initial_ordering_payload=initial_ordering_payload,
            ordering=ordering,
            initial_appearance_payload=initial_appearance_payload,
            emoji_pack=emoji_pack,
            seasonal=seasonal,
            transparent=transparent,
            initial_theme_payload=initial_theme_payload,
            ligatures=ligatures,
            base_theme=base_theme,
            custom_css=custom_css,
            font=font,
            monofont=monofont,
            overrides=overrides,
        )

        # TypedDict whose values are all NotRequired[str] is compatible with Dict[str, str]
        await self.parent.edit(payload, edited_at)  # type: ignore


class JoltUserSettings:
    """Represents Jolt user settings.

    Attributes
    ----------
    parent: :class:`.UserSettings`
        The raw user settings.
    low_data_mode: Optional[:class:`bool`]
        Whether Jolt should NOT load images and fetch users if not found in cache.
    compact_mode: Optional[:class:`bool`]
        Whether to hide user profile pictures in chats. Easier on the eyes.
    send_typing_indicators: Optional[:class:`bool`]
        Whether to send typing indicators when writing messages.
    receive_typing_indicators: Optional[:class:`bool`]
        Whether to show typing indicators ('<user> is typing...').
    """

    __slots__ = (
        'parent',
        'low_data_mode',
        'compact_mode',
        'send_typing_indicators',
        'receive_typing_indicators',
    )

    def __init__(self, parent: UserSettings, /) -> None:
        self.parent: UserSettings = parent
        self.locally_update(parent, full=True)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} >'

    def is_low_data_mode_enabled(self) -> bool:
        """:class:`bool`: Whether Jolt should NOT load images and fetch users if not found in cache."""
        return self.low_data_mode is True

    def is_compact_mode_enabled(self) -> bool:
        """:class:`bool`: Whether to hide user profile pictures in chats. Easier on the eyes."""
        return self.compact_mode is True

    def is_send_typing_indicators(self) -> bool:
        """:class:`bool`: Whether to send typing indicators when writing messages."""
        return self.send_typing_indicators is not False

    def is_receive_typing_indicators(self) -> bool:
        """:class:`bool`: Whether to show typing indicators ('<user> is typing...')."""
        return self.receive_typing_indicators is not False

    def locally_update(self, payload: UserSettings, /, *, full: bool) -> None:
        """Locally updates user settings with provided data.

        .. warning::
            This is called by library internally to keep settings up to date.

        Parameters
        ----------
        payload: :class:`.UserSettings`
            The data to update settings with.
        full: :class:`bool`
            Whether the payload is full.
        """
        low_data_mode = payload.get('jolt:low-data-mode')
        if low_data_mode is None:
            if full:
                self.low_data_mode: typing.Optional[bool] = None
        else:
            self.low_data_mode = bool(utils.decode_bool(low_data_mode))

        compact_mode = payload.get('jolt:compact-mode')
        if compact_mode is None:
            if full:
                self.compact_mode: typing.Optional[bool] = None
        else:
            self.compact_mode = bool(utils.decode_bool(compact_mode))

        send_typing_indicators = payload.get('jolt:send-typing-indicators')
        if send_typing_indicators is None:
            if full:
                self.send_typing_indicators: typing.Optional[bool] = None
        else:
            self.send_typing_indicators = bool(utils.decode_bool(send_typing_indicators))

        receive_typing_indicators = payload.get('jolt:receive-typing-indicators')
        if receive_typing_indicators is None:
            if full:
                self.receive_typing_indicators: typing.Optional[bool] = None
        else:
            self.receive_typing_indicators = bool(utils.decode_bool(receive_typing_indicators))

    def payload_for(
        self,
        *,
        low_data_mode: UndefinedOr[bool] = UNDEFINED,
        compact_mode: UndefinedOr[bool] = UNDEFINED,
        send_typing_indicators: UndefinedOr[bool] = UNDEFINED,
        receive_typing_indicators: UndefinedOr[bool] = UNDEFINED,
    ) -> raw.JoltUserSettings:
        """Builds a payload for Jolt user settings. You must pass it as first argument to :meth:`.HTTPClient.edit_user_settings`, like so:

        .. code-block:: python3

            payload = settings.payload_for(low_data_mode=True)
            await http.edit_user_settings(payload)

        Parameters
        ----------
        low_data_mode: UndefinedOr[:class:`bool`]
            Whether Jolt should NOT load images and fetch users if not found in cache.
        compact_mode: UndefinedOr[:class:`bool`]
            Whether to hide user profile pictures in chats. Easier on the eyes.
        send_typing_indicators: UndefinedOr[:class:`bool`]
            Whether to send typing indicators when writing messages.
        receive_typing_indicators: UndefinedOr[:class:`bool`]
            Whether to show typing indicators ('<user> is typing...').

        Returns
        -------
        Dict[:class:`str`, Any]
            The payload that must to be passed in :meth:`.HTTPClient.edit_user_settings`.
        """
        payload: raw.JoltUserSettings = {}
        if low_data_mode is not UNDEFINED:
            payload['jolt:low-data-mode'] = utils._bool(low_data_mode)
        if compact_mode is not UNDEFINED:
            payload['jolt:compact-mode'] = utils._bool(compact_mode)
        if send_typing_indicators is not UNDEFINED:
            payload['jolt:send-typing-indicators'] = utils._bool(send_typing_indicators)
        if receive_typing_indicators is not UNDEFINED:
            payload['jolt:receive-typing-indicators'] = utils._bool(receive_typing_indicators)
        return payload

    async def edit(
        self,
        *,
        edited_at: typing.Optional[typing.Union[datetime, int]] = None,
        low_data_mode: UndefinedOr[bool] = UNDEFINED,
        compact_mode: UndefinedOr[bool] = UNDEFINED,
        send_typing_indicators: UndefinedOr[bool] = UNDEFINED,
        receive_typing_indicators: UndefinedOr[bool] = UNDEFINED,
    ) -> None:
        """|coro|

        Edits the Jolt user settings.

        Parameters
        ----------
        edited_at: Optional[Union[:class:`~datetime.datetime`, :class:`int`]]
            External parameter to pass in :meth:`.HTTPClient.edit_user_settings`.
        low_data_mode: UndefinedOr[:class:`bool`]
            Whether Jolt should NOT load images and fetch users if not found in cache.
        compact_mode: UndefinedOr[:class:`bool`]
            Whether to hide user profile pictures in chats. Easier on the eyes.
        send_typing_indicators: UndefinedOr[:class:`bool`]
            Whether to send typing indicators when writing messages.
        receive_typing_indicators: UndefinedOr[:class:`bool`]
            Whether to show typing indicators ('<user> is typing...').

        Raises
        ------
        :class:`Unauthorized`
            Possible values for :attr:`~HTTPException.type`:

            +--------------------+----------------------------------------+
            | Value              | Reason                                 |
            +--------------------+----------------------------------------+
            | ``InvalidSession`` | The current bot/user token is invalid. |
            +--------------------+----------------------------------------+
        :class:`InternalServerError`
            Possible values for :attr:`~HTTPException.type`:

            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | Value             | Reason                                         | Populated attributes                                                |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
            | ``DatabaseError`` | Something went wrong during querying database. | :attr:`~HTTPException.collection`, :attr:`~HTTPException.operation` |
            +-------------------+------------------------------------------------+---------------------------------------------------------------------+
        """
        payload = self.payload_for(
            low_data_mode=low_data_mode,
            compact_mode=compact_mode,
            send_typing_indicators=send_typing_indicators,
            receive_typing_indicators=receive_typing_indicators,
        )
        # TypedDict whose values are all NotRequired[str] is compatible with Dict[str, str]
        await self.parent.edit(payload, edited_at)  # type: ignore


__all__ = (
    'UserSettings',
    'AndroidUserSettings',
    'ReviteNotificationOptions',
    'ReviteThemeVariable',
    'ReviteUserSettings',
    'JoltUserSettings',
)
