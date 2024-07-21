from __future__ import annotations

import typing

from .files import File

ImageSize = typing.Literal['Large', 'Preview']


class Image(typing.TypedDict):
    url: str
    width: int
    height: int
    size: ImageSize


class Video(typing.TypedDict):
    url: str
    width: int
    height: int


TwitchType = typing.Literal['Channel', 'Video', 'Clip']
LightspeedType = typing.Literal['Channel']
BandcampType = typing.Literal['Album', 'Track']


class NoneSpecial(typing.TypedDict):
    type: typing.Literal['None']


class GIFSpecial(typing.TypedDict):
    type: typing.Literal['GIF']


class YouTubeSpecial(typing.TypedDict):
    type: typing.Literal['YouTube']
    id: str
    timestamp: typing.NotRequired[str]


class LightspeedSpecial(typing.TypedDict):
    type: typing.Literal['Lightspeed']
    content_type: LightspeedType
    id: str


class TwitchSpecial(typing.TypedDict):
    type: typing.Literal['Twitch']
    content_type: TwitchType
    id: str


class SpotifySpecial(typing.TypedDict):
    type: typing.Literal['Spotify']
    content_type: str
    id: str


class SoundcloudSpecial(typing.TypedDict):
    type: typing.Literal['Soundcloud']


class BandcampSpecial(typing.TypedDict):
    type: typing.Literal['Bandcamp']
    content_type: BandcampType
    id: str


class StreamableSpecial(typing.TypedDict):
    type: typing.Literal['Streamable']
    id: str


Special = (
    NoneSpecial
    | GIFSpecial
    | YouTubeSpecial
    | LightspeedSpecial
    | TwitchSpecial
    | SpotifySpecial
    | BandcampSpecial
    | StreamableSpecial
)


class WebsiteMetadata(typing.TypedDict):
    url: typing.NotRequired[str]
    original_url: typing.NotRequired[str]
    special: typing.NotRequired[Special]
    title: typing.NotRequired[str]
    description: typing.NotRequired[str]
    image: typing.NotRequired[Image]
    video: typing.NotRequired[Video]
    site_name: typing.NotRequired[str]
    icon_url: typing.NotRequired[str]
    colour: typing.NotRequired[str]


class Text(typing.TypedDict):
    icon_url: typing.NotRequired[str]
    url: typing.NotRequired[str]
    title: typing.NotRequired[str]
    description: typing.NotRequired[str]
    media: typing.NotRequired[File]
    colour: typing.NotRequired[str]


class WebsiteEmbed(WebsiteMetadata):
    type: typing.Literal['Website']


class ImageEmbed(Image):
    type: typing.Literal['Image']


class VideoEmbed(Video):
    type: typing.Literal['Video']


class TextEmbed(Text):
    type: typing.Literal['Text']


class NoneEmbed(typing.TypedDict):
    type: typing.Literal['None']


Embed = WebsiteEmbed | ImageEmbed | VideoEmbed | TextEmbed | NoneEmbed

__all__ = (
    'ImageSize',
    'Image',
    'Video',
    'TwitchType',
    'LightspeedType',
    'BandcampType',
    'NoneSpecial',
    'GIFSpecial',
    'YouTubeSpecial',
    'LightspeedSpecial',
    'TwitchSpecial',
    'SpotifySpecial',
    'SoundcloudSpecial',
    'BandcampSpecial',
    'StreamableSpecial',
    'Special',
    'WebsiteMetadata',
    'Text',
    'WebsiteEmbed',
    'ImageEmbed',
    'VideoEmbed',
    'TextEmbed',
    'NoneEmbed',
    'Embed',
)
