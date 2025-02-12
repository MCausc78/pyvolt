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

import typing

from .flags import Permissions

if typing.TYPE_CHECKING:
    from . import raw

_new_permissions = Permissions.__new__


class PermissionOverride:
    """Represents a single permission override.

    Attributes
    ----------
    raw_allow: :class:`int`
        The raw value of permissions to allow.
    raw_deny: :class:`int`
        The raw value of permissions to deny.
    """

    __slots__ = (
        'raw_allow',
        'raw_deny',
    )

    def __init__(
        self,
        *,
        allow: Permissions = Permissions.none(),
        deny: Permissions = Permissions.none(),
    ) -> None:
        self.raw_allow: int = allow.value
        self.raw_deny: int = deny.value

    @property
    def allow(self) -> Permissions:
        """:class:`.Permissions`: The permissions to allow."""
        ret = _new_permissions(Permissions)
        ret.value = self.raw_allow
        return ret

    @allow.setter
    def allow(self, allow: Permissions, /) -> None:
        self.raw_allow = allow.value

    @property
    def deny(self) -> Permissions:
        """:class:`.Permissions`: The permissions to deny."""
        ret = _new_permissions(Permissions)
        ret.value = self.raw_deny
        return ret

    @deny.setter
    def deny(self, deny: Permissions, /) -> None:
        self.raw_deny = deny.value

    def build(self) -> raw.Override:
        return {'allow': self.raw_allow, 'deny': self.raw_deny}

    def __repr__(self) -> str:
        return f'<PermissionOverride allow={self.allow!r} deny={self.deny!r}>'


__all__ = ('PermissionOverride',)
