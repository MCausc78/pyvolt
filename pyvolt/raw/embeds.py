from __future__ import annotations

import typing as t

from .files import File

ImageSize = t.Literal["Large", "Preview"]


class Image(t.TypedDict):
    url: str
    width: int
    height: int
    size: ImageSize


class Video(t.TypedDict):
    url: str
    width: int
    height: int


TwitchType = t.Literal["Channel", "Video", "Clip"]
LightspeedType = t.Literal["Channel"]
BandcampType = t.Literal["Album", "Track"]


class NoneSpecial(t.TypedDict):
    type: t.Literal["None"]


class GIFSpecial(t.TypedDict):
    type: t.Literal["GIF"]


class YouTubeSpecial(t.TypedDict):
    type: t.Literal["YouTube"]
    id: str
    timestamp: t.NotRequired[str]


class LightspeedSpecial(t.TypedDict):
    type: t.Literal["Lightspeed"]
    content_type: LightspeedType
    id: str


class TwitchSpecial(t.TypedDict):
    type: t.Literal["Twitch"]
    content_type: TwitchType
    id: str


class SpotifySpecial(t.TypedDict):
    type: t.Literal["Spotify"]
    content_type: str
    id: str


class SoundcloudSpecial(t.TypedDict):
    type: t.Literal["Soundcloud"]


class BandcampSpecial(t.TypedDict):
    type: t.Literal["Bandcamp"]
    content_type: BandcampType
    id: str


class StreamableSpecial(t.TypedDict):
    type: t.Literal["Streamable"]
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


class WebsiteMetadata(t.TypedDict):
    url: t.NotRequired[str]
    original_url: t.NotRequired[str]
    special: t.NotRequired[Special]
    title: t.NotRequired[str]
    description: t.NotRequired[str]
    image: t.NotRequired[Image]
    video: t.NotRequired[Video]
    site_name: t.NotRequired[str]
    icon_url: t.NotRequired[str]
    colour: t.NotRequired[str]


class Text(t.TypedDict):
    icon_url: t.NotRequired[str]
    url: t.NotRequired[str]
    title: t.NotRequired[str]
    description: t.NotRequired[str]
    media: t.NotRequired[File]
    colour: t.NotRequired[str]


class WebsiteEmbed(WebsiteMetadata):
    type: t.Literal["Website"]


class ImageEmbed(Image):
    type: t.Literal["Image"]


class VideoEmbed(Video):
    type: t.Literal["Video"]


class TextEmbed(Text):
    type: t.Literal["Text"]


class NoneEmbed(t.TypedDict):
    type: t.Literal["None"]


Embed = WebsiteEmbed | ImageEmbed | VideoEmbed | TextEmbed | NoneEmbed

__all__ = (
    "ImageSize",
    "Image",
    "Video",
    "TwitchType",
    "LightspeedType",
    "BandcampType",
    "NoneSpecial",
    "GIFSpecial",
    "YouTubeSpecial",
    "LightspeedSpecial",
    "TwitchSpecial",
    "SpotifySpecial",
    "SoundcloudSpecial",
    "BandcampSpecial",
    "StreamableSpecial",
    "Special",
    "WebsiteMetadata",
    "Text",
    "WebsiteEmbed",
    "ImageEmbed",
    "VideoEmbed",
    "TextEmbed",
    "NoneEmbed",
    "Embed",
)
