from __future__ import annotations

import typing
import typing_extensions


class Override(typing.TypedDict):
    allow: int
    deny: int


class DataPermissionsField(typing.TypedDict):
    permissions: Override


class DataPermissionsValue(typing.TypedDict):
    permissions: int


DataPermissionPoly = DataPermissionsValue | DataPermissionsField


class OverrideField(typing.TypedDict):
    a: int
    d: int


__all__ = (
    'Override',
    'DataPermissionsField',
    'DataPermissionsValue',
    'DataPermissionPoly',
    'OverrideField',
)
