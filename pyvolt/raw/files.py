from __future__ import annotations

import typing as t


class File(t.TypedDict):
    _id: str
    tag: str
    filename: str
    metadata: Metadata
    content_type: str
    size: int
    deleted: t.NotRequired[bool]
    reported: t.NotRequired[bool]
    message_id: t.NotRequired[str]
    user_id: t.NotRequired[str]
    server_id: t.NotRequired[str]
    object: t.NotRequired[str]


class FileMetadata(t.TypedDict):
    type: t.Literal["File"]


class TextMetadata(t.TypedDict):
    type: t.Literal["Text"]


class ImageMetadata(t.TypedDict):
    type: t.Literal["Image"]
    width: int
    height: int


class VideoMetadata(t.TypedDict):
    type: t.Literal["Video"]
    width: int
    height: int


class AudioMetadata(t.TypedDict):
    type: t.Literal["Audio"]


Metadata = FileMetadata | TextMetadata | ImageMetadata | VideoMetadata | AudioMetadata

__all__ = (
    "File",
    "FileMetadata",
    "TextMetadata",
    "ImageMetadata",
    "VideoMetadata",
    "AudioMetadata",
    "Metadata",
)
