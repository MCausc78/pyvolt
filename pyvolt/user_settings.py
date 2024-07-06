from __future__ import annotations

from attrs import define, field
from datetime import datetime
import typing as t

if t.TYPE_CHECKING:
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
    """Whether these user settings are fake."""

    def __getitem__(self, key: str) -> str:
        return self.value[key][1]

    @t.overload
    def get(self, key: str) -> str | None: ...

    @t.overload
    def get(self, key: str, default: str, /) -> str: ...

    def get(self, key: str, *default: str) -> str | None:
        """Get a user setting."""
        if key in self.value:
            return self.value[key][1]
        return default[0] if default else None

    async def edit(
        self,
        timestamp: datetime | int | None = None,
        dict_settings: dict[str, str] = {},
        /,
        **kw_settings: str,
    ) -> None:
        """|coro|

        Modify current user settings.

        .. note::
            This can only be used by non-bot accounts.
        """
        return await self.state.http.set_user_settings(
            timestamp, dict_settings, **kw_settings
        )


__all__ = ("UserSettings",)
