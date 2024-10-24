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

import abc
from attrs import define, field
import typing


if typing.TYPE_CHECKING:
    from .cdn import StatelessAsset, Asset
    from .enums import LightspeedContentType, TwitchContentType, BandcampContentType, ImageSize
    from .state import State


@define(slots=True)
class _BaseEmbed(abc.ABC):
    """The message embed."""

    @abc.abstractmethod
    def _stateful(self, state: State, /) -> Embed: ...


@define(slots=True)
class EmbedSpecial:
    """Information about special remote content."""


class NoneEmbedSpecial(EmbedSpecial):
    """No remote content."""


_NONE_EMBED_SPECIAL = NoneEmbedSpecial()


class GifEmbedSpecial(EmbedSpecial):
    """This is content hint that embed contains a GIF. Use metadata to find video or image to play."""


_GIF_EMBED_SPECIAL = GifEmbedSpecial()


@define(slots=True)
class YouTubeEmbedSpecial(EmbedSpecial):
    """Represents information about Youtube video."""

    id: str = field(repr=True, kw_only=True, eq=True)
    """The video ID."""

    timestamp: str | None = field(repr=True, kw_only=True, eq=True)
    """The video timestamp."""


@define(slots=True)
class LightspeedEmbedSpecial(EmbedSpecial):
    """Represents information about Lightspeed.tv stream."""

    content_type: LightspeedContentType = field(repr=True, kw_only=True, eq=True)
    """The Lightspeed.tv content type."""

    id: str = field(repr=True, kw_only=True, eq=True)
    """The Lightspeed.tv stream ID."""


@define(slots=True)
class TwitchEmbedSpecial(EmbedSpecial):
    """Represents information about Twitch stream or clip."""

    content_type: TwitchContentType = field(repr=True, kw_only=True, eq=True)
    """The Twitch content type."""

    id: str = field(repr=True, kw_only=True, eq=True)
    """The Twitch content ID."""


@define(slots=True)
class SpotifyEmbedSpecial(EmbedSpecial):
    """Represents information about Spotify track."""

    content_type: str = field(repr=True, kw_only=True, eq=True)
    """The Spotify content type."""

    id: str = field(repr=True, kw_only=True, eq=True)
    """The Spotify content ID."""


class SoundcloudEmbedSpecial(EmbedSpecial):
    """Represents information about Soundcloud track."""


_SOUNDCLOUD_EMBED_SPECIAL = SoundcloudEmbedSpecial()


@define(slots=True)
class BandcampEmbedSpecial(EmbedSpecial):
    """Represents information about Bandcamp track."""

    content_type: BandcampContentType = field(repr=True, kw_only=True, eq=True)
    """The Bandcamp content type."""

    id: str = field(repr=True, kw_only=True, eq=True)
    """The Bandcamp content ID."""


@define(slots=True)
class AppleMusicEmbedSpecial(EmbedSpecial):
    """Represents information about Apple Music track."""

    album_id: str = field(repr=True, kw_only=True, eq=True)
    """The Apple Music album ID."""

    track_id: str | None = field(repr=True, kw_only=True, eq=True)
    """The Apple Music track ID."""


@define(slots=True)
class StreamableEmbedSpecial(EmbedSpecial):
    """Represents information about Streamable video."""

    id: str = field(repr=True, kw_only=True, eq=True)
    """The video ID."""


@define(slots=True)
class ImageEmbed(_BaseEmbed):
    """Represents an image in a embed."""

    url: str = field(repr=True, kw_only=True, eq=True)
    """The URL to the original image."""

    width: int = field(repr=True, kw_only=True, eq=True)
    """The width of the image."""

    height: int = field(repr=True, kw_only=True, eq=True)
    """The height of the image."""

    size: ImageSize = field(repr=True, kw_only=True, eq=True)
    """The positioning and size of the image."""

    def _stateful(self, state: State, /) -> Embed:
        return self


@define(slots=True)
class VideoEmbed(_BaseEmbed):
    """Represents an video in a embed."""

    url: str = field(repr=True, kw_only=True, eq=True)
    """The URL to the original video."""

    width: int = field(repr=True, kw_only=True, eq=True)
    """The width of the video."""

    height: int = field(repr=True, kw_only=True, eq=True)
    """The height of the video."""

    def _stateful(self, state: State, /) -> Embed:
        return self


@define(slots=True)
class WebsiteEmbed(_BaseEmbed):
    """Represents website embed within Revolt message."""

    url: str | None = field(repr=True, kw_only=True, eq=True)
    """The direct URL to web page."""

    original_url: str | None = field(repr=True, kw_only=True, eq=True)
    """The original direct URL."""

    special: EmbedSpecial | None = field(repr=True, kw_only=True, eq=True)
    """The remote content."""

    title: str | None = field(repr=True, kw_only=True, eq=True)
    """The title of website."""

    description: str | None = field(repr=True, kw_only=True, eq=True)
    """The description of website."""

    image: ImageEmbed | None = field(repr=True, kw_only=True, eq=True)
    """The embedded image."""

    video: VideoEmbed | None = field(repr=True, kw_only=True, eq=True)
    """The embedded video."""

    site_name: str | None = field(repr=True, kw_only=True, eq=True)
    """The site name."""

    icon_url: str | None = field(repr=True, kw_only=True, eq=True)
    """The URL to site icon."""

    color: str | None = field(repr=True, kw_only=True, eq=True)
    """The embed's CSS color."""

    def _stateful(self, state: State, /) -> Embed:
        return self


@define(slots=True)
class StatelessTextEmbed(_BaseEmbed):
    """Stateless representation of text embed within Revolt message."""

    icon_url: str | None = field(repr=True, kw_only=True, eq=True)
    """The URL to site icon."""

    url: str | None = field(repr=True, kw_only=True, eq=True)
    """The direct URL to web page."""

    title: str | None = field(repr=True, kw_only=True, eq=True)
    """The embed's title."""

    description: str | None = field(repr=True, kw_only=True, eq=True)
    """The embed's description."""

    internal_media: StatelessAsset | None = field(repr=True, kw_only=True, eq=True)
    """The stateless embed media."""

    color: str | None = field(repr=True, kw_only=True, eq=True)
    """The embed's CSS color."""

    def _stateful(self, state: State, /) -> Embed:
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
    """Representation of text embed within Revolt message."""

    state: State = field(repr=False, hash=False, kw_only=True, eq=False)

    @property
    def media(self) -> Asset | None:
        """Optional[:class:`Asset`]: The embed media."""
        return self.internal_media._stateful(self.state, 'attachments') if self.internal_media else None


class NoneEmbed(_BaseEmbed):
    """Embed that holds nothing."""

    def _stateful(self, state: State, /) -> Embed:
        return self


_NONE_EMBED = NoneEmbed()

StatelessEmbed = WebsiteEmbed | ImageEmbed | VideoEmbed | StatelessTextEmbed | NoneEmbed
Embed = WebsiteEmbed | ImageEmbed | VideoEmbed | TextEmbed | NoneEmbed

__all__ = (
    '_BaseEmbed',
    'EmbedSpecial',
    'NoneEmbedSpecial',
    '_NONE_EMBED_SPECIAL',
    'GifEmbedSpecial',
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
    'StatelessEmbed',
    'Embed',
)
