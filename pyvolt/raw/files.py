from __future__ import annotations

import typing


class File(typing.TypedDict):
    _id: str
    tag: str
    filename: str
    metadata: Metadata
    content_type: str
    size: int
    deleted: typing.NotRequired[bool]
    reported: typing.NotRequired[bool]
    message_id: typing.NotRequired[str]
    user_id: typing.NotRequired[str]
    server_id: typing.NotRequired[str]
    object_id: typing.NotRequired[str]


class FileMetadata(typing.TypedDict):
    type: typing.Literal['File']


class TextMetadata(typing.TypedDict):
    type: typing.Literal['Text']


class ImageMetadata(typing.TypedDict):
    type: typing.Literal['Image']
    width: int
    height: int


class VideoMetadata(typing.TypedDict):
    type: typing.Literal['Video']
    width: int
    height: int


class AudioMetadata(typing.TypedDict):
    type: typing.Literal['Audio']


Metadata = FileMetadata | TextMetadata | ImageMetadata | VideoMetadata | AudioMetadata

__all__ = (
    'File',
    'FileMetadata',
    'TextMetadata',
    'ImageMetadata',
    'VideoMetadata',
    'AudioMetadata',
    'Metadata',
)
