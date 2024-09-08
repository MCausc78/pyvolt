from __future__ import annotations

import typing

from .localization import Language

UserSettings = dict[str, tuple[int, str]]


class OptionsFetchSettings(typing.TypedDict):
    keys: list[str]


class OptionsSetSettings(typing.TypedDict):
    timestamp: typing.NotRequired[int]


DataSetSettings = dict[str, str]


# Android User Settings
AndroidTheme = typing.Literal['Revolt', 'Light', 'Amoled', 'None', 'M3Dynamic']
AndroidProfilePictureShape = int
AndroidMessageReplyStyle = typing.Literal['None', 'SwipeFromEnd', 'DoubleTap']


class AndroidUserSettings(typing.TypedDict):
    theme: typing.NotRequired[AndroidTheme]
    colourOverrides: typing.NotRequired[dict[str, int]]
    # If not provided, defaults to SwipeFromEnd
    messageReplyStyle: typing.NotRequired[AndroidMessageReplyStyle]
    # If not provided, defaults to 50
    avatarRadius: typing.NotRequired[AndroidProfilePictureShape]


# Revite User Settings
ReviteChangelogEntryID = typing.Literal[1, 2, 3] | int


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
        'appearance:emoji': typing.NotRequired[ReviteAppearanceEmojiPack],
        'appearance:seasonal': typing.NotRequired[bool],
        'appearance:transparency': typing.NotRequired[bool],
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
        'appearance:ligatures': typing.NotRequired[bool],
        'appearance:theme:base': typing.NotRequired[ReviteAppearanceTheme],
        'appearance:theme:css': typing.NotRequired[str],
        'appearance:theme:font': typing.NotRequired[ReviteAppearanceFont],
        # Deprecated by `base`
        # 'appearance:theme:light': typing.NotRequired[bool],
        'appearance:theme:monoFont': typing.NotRequired[ReviteAppearanceMonoFont],
        'appearance:theme:overrides': typing.NotRequired[dict[ReviteThemeVariable, str]],
    },
)


class ReviteUserSettingsPayload(typing.TypedDict):
    # changelog: typing.NotRequired[ReviteChangelog]
    # locale: typing.NotRequired[ReviteLocaleOptions]
    # notifications: typing.NotRequired[ReviteNotificationOptions]
    # ordering: typing.NotRequired[ReviteOrdering]
    # appearance: typing.NotRequired[ReviteAppearanceSettings]
    # theme: typing.NotRequired[ReviteThemeSettings]
    changelog: typing.NotRequired[str]
    locale: typing.NotRequired[str]
    notifications: typing.NotRequired[str]
    ordering: typing.NotRequired[str]
    appearance: typing.NotRequired[str]
    theme: typing.NotRequired[str]


JoltUserSettings = typing.TypedDict(
    'JoltUserSettings',
    {
        'jolt:low-data-mode': typing.NotRequired[typing.Literal['true', 'false']],
        'jolt:compact-mode': typing.NotRequired[typing.Literal['true', 'false']],
        'jolt:send-typing-indicators': typing.NotRequired[typing.Literal['true', 'false']],
        'jolt:receive-typing-indicators': typing.NotRequired[typing.Literal['true', 'false']],
    },
)


__all__ = (
    'UserSettings',
    'OptionsFetchSettings',
    'OptionsSetSettings',
    'DataSetSettings',
    'AndroidTheme',
    'AndroidProfilePictureShape',
    'AndroidMessageReplyStyle',
    'AndroidUserSettings',
    'ReviteChangelogEntryID',
    'ReviteChangelog',
    'ReviteLocaleOptions',
    'ReviteNotificationState',
    'ReviteNotificationOptions',
    'ReviteOrdering',
    'ReviteAppearanceEmojiPack',
    'ReviteAppearanceSettings',
    'ReviteAppearanceTheme',
    'ReviteAppearanceFont',
    'ReviteAppearanceMonoFont',
    'ReviteThemeVariable',
    'ReviteThemeSettings',
    'ReviteUserSettingsPayload',
    'JoltUserSettings',
)
