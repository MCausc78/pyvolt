from __future__ import annotations

from attrs import define, field
from datetime import datetime
import typing

from . import utils
from .core import UNDEFINED, UndefinedOr, is_defined
from .enums import Enum

if typing.TYPE_CHECKING:
    from . import raw
    from .state import State


@define(slots=True)
class UserSettings:
    """The user settings."""

    state: State = field(repr=False, hash=False, kw_only=True, eq=False)
    """The state that manages current user settings."""

    value: dict[str, tuple[int, str]] = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The {user_setting_key: (timestamp, value)} mapping."""

    fake: bool = field(repr=False, hash=False, kw_only=True, eq=False)
    """Whether user settings are fake. Fake user settings are created by Pyvolt, if not logged in, or in HTTP-only mode."""

    def __getitem__(self, key: str) -> str:
        return self.value[key][1]

    @typing.overload
    def get(self, key: str) -> str | None: ...

    @typing.overload
    def get(self, key: str, default: str, /) -> str: ...

    def get(self, key: str, *default: str) -> str | None:
        """Get a user setting."""
        if key in self.value:
            return self.value[key][1]
        return default[0] if default else None

    def as_android(self) -> AndroidUserSettings:
        """:class:`AndroidUserSettings`: Casts user settings to Android's ones."""
        return AndroidUserSettings(self)

    async def edit(
        self,
        a1: dict[str, str] | datetime | int | None = None,
        a2: dict[str, str] | datetime | int | None = {},
        /,
        **kwargs: str,
    ) -> None:
        """|coro|

        Modify current user settings.

        .. note::
            This can only be used by non-bot accounts.
        """
        return await self.state.http.edit_user_settings(a1, a2, **kwargs)


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
    __slots__ = (
        "parent",
        "_theme",
        "_colour_overrides",
        "_reply_style",
        "_avatar_radius",
    )

    def __init__(self, parent: UserSettings) -> None:
        self.parent = parent
        self._parse(utils.from_json(parent.get("android", "{}")))

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
            await http.edit_user_settings(android=json.dumps(payload))

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
        payload: raw.AndroidUserSettings = {}
        if self._theme is not None:
            payload["theme"] = self._theme.value
        if is_defined(theme):
            if theme is None:
                try:
                    del payload["theme"]
                except KeyError:
                    pass
            else:
                payload["theme"] = theme.value

        if self._colour_overrides is not None:
            payload["colourOverrides"] = self._colour_overrides
        if is_defined(colour_overrides):
            if colour_overrides is None:
                try:
                    del payload["colourOverrides"]
                except KeyError:
                    pass
            else:
                payload["colourOverrides"] = colour_overrides

        if self._reply_style is not None:
            payload["messageReplyStyle"] = self._reply_style.value
        if is_defined(reply_style):
            if reply_style is None:
                try:
                    del payload["messageReplyStyle"]
                except KeyError:
                    pass
            else:
                payload["messageReplyStyle"] = reply_style.value

        if self._avatar_radius is not None:
            payload["avatarRadius"] = self._avatar_radius
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
        await self.parent.edit({"android": utils.to_json(payload)})


__all__ = (
    "UserSettings",
    "AndroidTheme",
    "AndroidProfilePictureShape",
    "AndroidMessageReplyStyle",
    "AndroidUserSettings",
)
