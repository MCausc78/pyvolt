from __future__ import annotations

import typing as t


class Override(t.TypedDict):
    allow: int
    deny: int


class DataPermissionsField(t.TypedDict):
    permissions: Override


class DataPermissionsValue(t.TypedDict):
    permissions: int


DataPermissionPoly = DataPermissionsValue | DataPermissionsField


class OverrideField(t.TypedDict):
    a: int
    d: int


__all__ = (
    "Override",
    "DataPermissionsField",
    "DataPermissionsValue",
    "DataPermissionPoly",
    "OverrideField",
)
