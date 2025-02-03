from __future__ import annotations

import typing
import typing_extensions

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
    timestamp: typing_extensions.NotRequired[str]


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


class AppleMusicSpecial(typing.TypedDict):
    type: typing.Literal['AppleMusic']
    album_id: str
    track_id: typing_extensions.NotRequired[str]


class StreamableSpecial(typing.TypedDict):
    type: typing.Literal['Streamable']
    id: str


Special = typing.Union[
    NoneSpecial,
    GIFSpecial,
    YouTubeSpecial,
    LightspeedSpecial,
    TwitchSpecial,
    SpotifySpecial,
    BandcampSpecial,
    AppleMusicSpecial,
    StreamableSpecial,
]


class WebsiteMetadata(typing.TypedDict):
    url: typing_extensions.NotRequired[str]
    original_url: typing_extensions.NotRequired[str]
    special: typing_extensions.NotRequired[Special]
    title: typing_extensions.NotRequired[str]
    description: typing_extensions.NotRequired[str]
    image: typing_extensions.NotRequired[Image]
    video: typing_extensions.NotRequired[Video]
    site_name: typing_extensions.NotRequired[str]
    icon_url: typing_extensions.NotRequired[str]
    colour: typing_extensions.NotRequired[str]


class Text(typing.TypedDict):
    icon_url: typing_extensions.NotRequired[str]
    url: typing_extensions.NotRequired[str]
    title: typing_extensions.NotRequired[str]
    description: typing_extensions.NotRequired[str]
    media: typing_extensions.NotRequired[File]
    colour: typing_extensions.NotRequired[str]


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


Embed = typing.Union[WebsiteEmbed, ImageEmbed, VideoEmbed, TextEmbed, NoneEmbed]
