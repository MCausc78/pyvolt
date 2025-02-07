from __future__ import annotations

import typing
import typing_extensions

from .localization import Language

UserSettings = dict[str, tuple[int, str]]


class OptionsFetchSettings(typing.TypedDict):
    keys: list[str]


class OptionsSetSettings(typing.TypedDict):
    timestamp: typing_extensions.NotRequired[int]


DataSetSettings = dict[str, str]


# Android User Settings
AndroidTheme = typing.Literal['Revolt', 'Light', 'Amoled', 'None', 'M3Dynamic']
AndroidProfilePictureShape = int
AndroidMessageReplyStyle = typing.Literal['None', 'SwipeFromEnd', 'DoubleTap']


class AndroidUserSettingsSpecialEmbedSettings(typing.TypedDict):
    embedYouTube: bool
    embedAppleMusic: bool


class AndroidUserSettings(typing.TypedDict):
    theme: typing_extensions.NotRequired[AndroidTheme]
    colourOverrides: typing_extensions.NotRequired[dict[str, int]]
    # If not provided, defaults to SwipeFromEnd
    messageReplyStyle: typing_extensions.NotRequired[AndroidMessageReplyStyle]
    # If not provided, defaults to 50
    avatarRadius: typing_extensions.NotRequired[AndroidProfilePictureShape]
    specialEmbedSettings: typing_extensions.NotRequired[AndroidUserSettingsSpecialEmbedSettings]


# Revite User Settings
ReviteChangelogEntryID = typing.Union[typing.Literal[1, 2, 3], int]


class ReviteChangelog(typing.TypedDict):
    viewed: ReviteChangelogEntryID


class ReviteLocaleOptions(typing.TypedDict):
    lang: Language


ReviteNotificationState = typing.Literal['all', 'mention', 'none', 'muted']


class ReviteNotificationOptions(typing.TypedDict):
    server: dict[str, ReviteNotificationState]
    channel: dict[str, ReviteNotificationState]


class ReviteOrdering(typing.TypedDict):
    servers: list[str]


ReviteAppearanceEmojiPack = typing.Literal['mutant', 'twemoji', 'openmoji', 'noto']
ReviteAppearanceSettings = typing.TypedDict(
    'ReviteAppearanceSettings',
    {
        'appearance:emoji': typing_extensions.NotRequired[ReviteAppearanceEmojiPack],
        'appearance:seasonal': typing_extensions.NotRequired[bool],
        'appearance:transparency': typing_extensions.NotRequired[bool],
    },
)

ReviteAppearanceTheme = typing.Literal['dark', 'light']
ReviteAppearanceFont = typing.Literal[
    'Open Sans',
    'OpenDyslexic',
    'Inter',
    'Atkinson Hyperlegible',
    'Roboto',
    'Noto Sans',
    'Lato',
    'Bitter',
    'Montserrat',
    'Poppins',
    'Raleway',
    'Ubuntu',
    'Comic Neue',
    'Lexend',
]
ReviteAppearanceMonoFont = typing.Literal[
    'Fira Code',
    'Roboto Mono',
    'Source Code Pro',
    'Space Mono',
    'Ubuntu Mono',
    'JetBrains Mono',
]
ReviteThemeVariable = typing.Literal[
    'accent',
    'background',
    'foreground',
    'block',
    'message-box',
    'mention',
    'success',
    'warning',
    'error',
    'hover',
    'scrollbar-thumb',
    'scrollbar-track',
    'primary-background',
    'primary-header',
    'secondary-background',
    'secondary-foreground',
    'secondary-header',
    'tertiary-background',
    'tertiary-foreground',
    'tooltip',
    'status-online',
    'status-away',
    'status-focus',
    'status-busy',
    'status-streaming',
    'status-invisible',
]
ReviteThemeSettings = typing.TypedDict(
    'ReviteThemeSettings',
    {
        'appearance:ligatures': typing_extensions.NotRequired[bool],
        'appearance:theme:base': typing_extensions.NotRequired[ReviteAppearanceTheme],
        'appearance:theme:css': typing_extensions.NotRequired[str],
        'appearance:theme:font': typing_extensions.NotRequired[ReviteAppearanceFont],
        # Deprecated by `base`
        # 'appearance:theme:light': typing_extensions.NotRequired[bool],
        'appearance:theme:monoFont': typing_extensions.NotRequired[ReviteAppearanceMonoFont],
        'appearance:theme:overrides': typing_extensions.NotRequired[dict[ReviteThemeVariable, str]],
    },
)


class ReviteUserSettingsPayload(typing.TypedDict):
    # changelog: typing_extensions.NotRequired[ReviteChangelog]
    # locale: typing_extensions.NotRequired[ReviteLocaleOptions]
    # notifications: typing_extensions.NotRequired[ReviteNotificationOptions]
    # ordering: typing_extensions.NotRequired[ReviteOrdering]
    # appearance: typing_extensions.NotRequired[ReviteAppearanceSettings]
    # theme: typing_extensions.NotRequired[ReviteThemeSettings]
    changelog: typing_extensions.NotRequired[str]
    locale: typing_extensions.NotRequired[str]
    notifications: typing_extensions.NotRequired[str]
    ordering: typing_extensions.NotRequired[str]
    appearance: typing_extensions.NotRequired[str]
    theme: typing_extensions.NotRequired[str]


JoltUserSettings = typing.TypedDict(
    'JoltUserSettings',
    {
        'jolt:low-data-mode': typing_extensions.NotRequired[typing.Literal['true', 'false']],
        'jolt:compact-mode': typing_extensions.NotRequired[typing.Literal['true', 'false']],
        'jolt:send-typing-indicators': typing_extensions.NotRequired[typing.Literal['true', 'false']],
        'jolt:receive-typing-indicators': typing_extensions.NotRequired[typing.Literal['true', 'false']],
    },
)
