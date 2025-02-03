from __future__ import annotations

import typing


class Override(typing.TypedDict):
    allow: int
    deny: int


class DataPermissionsField(typing.TypedDict):
    permissions: Override


class DataPermissionsValue(typing.TypedDict):
    permissions: int


DataPermissionPoly = typing.Union[DataPermissionsValue, DataPermissionsField]


class OverrideField(typing.TypedDict):
    a: int
    d: int
