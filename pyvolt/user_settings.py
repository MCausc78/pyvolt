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
    """Whether user settings are fake. Fake user settings are created by Pyvolt, if not logged in, or in HTTP-only mode."""

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
        return await self.state.http.edit_user_settings(
            a1, a2, **kwargs
        )

__all__ = ("UserSettings",)
