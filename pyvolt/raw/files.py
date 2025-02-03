from __future__ import annotations

import typing
import typing_extensions


class File(typing.TypedDict):
    _id: str
    tag: str
    filename: str
    metadata: Metadata
    content_type: str
    size: int
    deleted: typing_extensions.NotRequired[bool]
    reported: typing_extensions.NotRequired[bool]
    message_id: typing_extensions.NotRequired[str]
    user_id: typing_extensions.NotRequired[str]
    server_id: typing_extensions.NotRequired[str]
    object_id: typing_extensions.NotRequired[str]


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


Metadata = typing.Union[
    FileMetadata,
    TextMetadata,
    ImageMetadata,
    VideoMetadata,
    AudioMetadata,
]
