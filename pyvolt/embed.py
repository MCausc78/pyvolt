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

from abc import ABC, abstractmethod
from attrs import define, field
import typing


if typing.TYPE_CHECKING:
    from .cdn import StatelessAsset, Asset
    from .enums import LightspeedContentType, TwitchContentType, BandcampContentType, ImageSize
    from .state import State


class BaseEmbed(ABC):
    """Base class for message embeds."""

    __slots__ = ()

    @abstractmethod
    def attach_state(self, state: State, /) -> Embed:
        """:class:`.Embed`: Attach a state to embed.

        Parameters
        ----------
        state: :class:`.State`
            The state to attach.
        """
        ...


@define(slots=True)
class BaseEmbedSpecial:
    """Information about special remote content."""


@define(slots=True)
class NoneEmbedSpecial(BaseEmbedSpecial):
    """No remote content."""


_NONE_EMBED_SPECIAL = NoneEmbedSpecial()


@define(slots=True)
class GIFEmbedSpecial(BaseEmbedSpecial):
    """A content hint that embed contains a GIF. Metadata should be used to find video or image to play."""


_GIF_EMBED_SPECIAL = GIFEmbedSpecial()


@define(slots=True)
class YouTubeEmbedSpecial(BaseEmbedSpecial):
    """Represents information about Youtube video."""

    id: str = field(repr=True, kw_only=True, eq=True)
    """:class:`str`: The video ID."""

    timestamp: typing.Optional[str] = field(repr=True, kw_only=True, eq=True)
    """Optional[:class:`str`]: The video timestamp."""


@define(slots=True)
class LightspeedEmbedSpecial(BaseEmbedSpecial):
    """Represents information about Lightspeed.tv stream."""

    content_type: LightspeedContentType = field(repr=True, kw_only=True, eq=True)
    """:class:`.LightspeedContentType`: The Lightspeed.tv content type."""

    id: str = field(repr=True, kw_only=True, eq=True)
    """:class:`str`: The Lightspeed.tv stream ID."""


@define(slots=True)
class TwitchEmbedSpecial(BaseEmbedSpecial):
    """Represents information about Twitch stream or clip."""

    content_type: TwitchContentType = field(repr=True, kw_only=True, eq=True)
    """:class:`.TwitchContentType`: The Twitch content type."""

    id: str = field(repr=True, kw_only=True, eq=True)
    """:class:`str`: The Twitch content ID."""


@define(slots=True)
class SpotifyEmbedSpecial(BaseEmbedSpecial):
    """Represents information about Spotify track."""

    content_type: str = field(repr=True, kw_only=True, eq=True)
    """:class:`str`: The Spotify content type."""

    id: str = field(repr=True, kw_only=True, eq=True)
    """:class:`str`: The Spotify content ID."""


@define(slots=True)
class SoundcloudEmbedSpecial(BaseEmbedSpecial):
    """Represents information about Soundcloud track."""


_SOUNDCLOUD_EMBED_SPECIAL = SoundcloudEmbedSpecial()


@define(slots=True)
class BandcampEmbedSpecial(BaseEmbedSpecial):
    """Represents information about Bandcamp track."""

    content_type: BandcampContentType = field(repr=True, kw_only=True, eq=True)
    """:class:`.BandcampContentType`: The Bandcamp content type."""

    id: str = field(repr=True, kw_only=True, eq=True)
    """:class:`str`: The Bandcamp content ID."""


@define(slots=True)
class AppleMusicEmbedSpecial(BaseEmbedSpecial):
    """Represents information about Apple Music track."""

    album_id: str = field(repr=True, kw_only=True, eq=True)
    """:class:`str`: The Apple Music album ID."""

    track_id: typing.Optional[str] = field(repr=True, kw_only=True, eq=True)
    """Optional[:class:`str`]: The Apple Music track ID."""


@define(slots=True)
class StreamableEmbedSpecial(BaseEmbedSpecial):
    """Represents information about Streamable video."""

    id: str = field(repr=True, kw_only=True, eq=True)
    """:class:`str`: The video ID."""


@define(slots=True)
class ImageEmbed(BaseEmbed):
    """Represents an image in a embed."""

    url: str = field(repr=True, kw_only=True, eq=True)
    """:class:`str`: The URL to the original image."""

    width: int = field(repr=True, kw_only=True, eq=True)
    """:class:`int`: The width of the image."""

    height: int = field(repr=True, kw_only=True, eq=True)
    """:class:`int`: The height of the image."""

    size: ImageSize = field(repr=True, kw_only=True, eq=True)
    """:class:`.ImageSize`: The positioning and size of the image."""

    def attach_state(self, state: State, /) -> Embed:
        return self


@define(slots=True)
class VideoEmbed(BaseEmbed):
    """Represents an video in a embed."""

    url: str = field(repr=True, kw_only=True, eq=True)
    """:class:`str`: The URL to the original video."""

    width: int = field(repr=True, kw_only=True, eq=True)
    """:class:`int`: The width of the video."""

    height: int = field(repr=True, kw_only=True, eq=True)
    """:class:`int`: The height of the video."""

    def attach_state(self, state: State, /) -> Embed:
        return self


@define(slots=True)
class WebsiteEmbed(BaseEmbed):
    """Represents website embed within Revolt message."""

    url: typing.Optional[str] = field(repr=True, kw_only=True, eq=True)
    """Optional[:class:`str`]: The direct URL to web page."""

    original_url: typing.Optional[str] = field(repr=True, kw_only=True, eq=True)
    """Optional[:class:`str`]: The original direct URL."""

    special: typing.Optional[EmbedSpecial] = field(repr=True, kw_only=True, eq=True)
    """Optional[:class:`.EmbedSpecial`]: The remote content."""

    title: typing.Optional[str] = field(repr=True, kw_only=True, eq=True)
    """Optional[:class:`str`]: The title of website."""

    description: typing.Optional[str] = field(repr=True, kw_only=True, eq=True)
    """Optional[:class:`str`]: The description of website."""

    image: typing.Optional[ImageEmbed] = field(repr=True, kw_only=True, eq=True)
    """Optional[:class:`.ImageEmbed`]: The embedded image."""

    video: typing.Optional[VideoEmbed] = field(repr=True, kw_only=True, eq=True)
    """Optional[:class:`.VideoEmbed`]: The embedded video."""

    site_name: typing.Optional[str] = field(repr=True, kw_only=True, eq=True)
    """Optional[:class:`str`]: The site name."""

    icon_url: typing.Optional[str] = field(repr=True, kw_only=True, eq=True)
    """Optional[:class:`str`]: The URL to site icon."""

    color: typing.Optional[str] = field(repr=True, kw_only=True, eq=True)
    """Optional[:class:`str`]: The embed's CSS color."""

    def attach_state(self, state: State, /) -> Embed:
        return self


@define(slots=True)
class StatelessTextEmbed(BaseEmbed):
    """Represents stateless text embed within Revolt message."""

    icon_url: typing.Optional[str] = field(repr=True, kw_only=True, eq=True)
    """Optional[:class:`str`]: The URL to site icon."""

    url: typing.Optional[str] = field(repr=True, kw_only=True, eq=True)
    """Optional[:class:`str`]: The direct URL to web page."""

    title: typing.Optional[str] = field(repr=True, kw_only=True, eq=True)
    """Optional[:class:`str`]: The embed's title."""

    description: typing.Optional[str] = field(repr=True, kw_only=True, eq=True)
    """Optional[:class:`str`]: The embed's description."""

    internal_media: typing.Optional[StatelessAsset] = field(repr=True, kw_only=True, eq=True)
    """Optional[:class:`.StatelessAsset`]: The stateless embed media."""

    color: typing.Optional[str] = field(repr=True, kw_only=True, eq=True)
    """Optional[:class:`str`]: The embed's CSS color."""

    def attach_state(self, state: State, /) -> Embed:
        return TextEmbed(
            icon_url=self.icon_url,
            url=self.url,
            title=self.title,
            description=self.description,
            internal_media=self.internal_media,
            color=self.color,
            state=state,
        )


@define(slots=True)
class TextEmbed(StatelessTextEmbed):
    """Represents a text embed within Revolt message."""

    state: State = field(repr=False, hash=False, kw_only=True, eq=False)

    @property
    def media(self) -> typing.Optional[Asset]:
        """Optional[:class:`Asset`]: The embed media."""
        return self.internal_media.attach_state(self.state, 'attachments') if self.internal_media else None


class NoneEmbed(BaseEmbed):
    """Embed that holds nothing."""

    def attach_state(self, state: State, /) -> Embed:
        return self


_NONE_EMBED: typing.Final[NoneEmbed] = NoneEmbed()

EmbedSpecial = typing.Union[
    NoneEmbedSpecial,
    GIFEmbedSpecial,
    YouTubeEmbedSpecial,
    LightspeedEmbedSpecial,
    TwitchEmbedSpecial,
    SpotifyEmbedSpecial,
    SoundcloudEmbedSpecial,
    BandcampEmbedSpecial,
    AppleMusicEmbedSpecial,
    StreamableEmbedSpecial,
]
StatelessEmbed = typing.Union[WebsiteEmbed, ImageEmbed, VideoEmbed, StatelessTextEmbed, NoneEmbed]
Embed = typing.Union[WebsiteEmbed, ImageEmbed, VideoEmbed, TextEmbed, NoneEmbed]

__all__ = (
    'BaseEmbed',
    'BaseEmbedSpecial',
    'NoneEmbedSpecial',
    '_NONE_EMBED_SPECIAL',
    'GIFEmbedSpecial',
    '_GIF_EMBED_SPECIAL',
    'YouTubeEmbedSpecial',
    'LightspeedEmbedSpecial',
    'TwitchEmbedSpecial',
    'SpotifyEmbedSpecial',
    'SoundcloudEmbedSpecial',
    '_SOUNDCLOUD_EMBED_SPECIAL',
    'BandcampEmbedSpecial',
    'AppleMusicEmbedSpecial',
    'StreamableEmbedSpecial',
    'ImageEmbed',
    'VideoEmbed',
    'WebsiteEmbed',
    'StatelessTextEmbed',
    'TextEmbed',
    'NoneEmbed',
    '_NONE_EMBED',
    'EmbedSpecial',
    'StatelessEmbed',
    'Embed',
)
