from __future__ import annotations

import abc
from attrs import define, field
import typing

from . import cdn
from .enums import Enum

if typing.TYPE_CHECKING:
    from .state import State


@define(slots=True)
class _BaseEmbed(abc.ABC):
    """The message embed."""

    @abc.abstractmethod
    def _stateful(self, state: State) -> Embed: ...


class EmbedSpecial(abc.ABC):
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

    id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The video ID."""

    timestamp: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The video timestamp."""


class LightspeedContentType(Enum):
    """Type of remote Lightspeed.tv content."""

    channel = "Channel"


@define(slots=True)
class LightspeedEmbedSpecial(EmbedSpecial):
    """Represents information about Lightspeed.tv stream."""

    content_type: LightspeedContentType = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The Lightspeed.tv content type."""

    id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The Lightspeed.tv stream ID."""


class TwitchContentType(Enum):
    """Type of remote Twitch content."""

    channel = "Channel"
    video = "Video"
    clip = "Clip"


@define(slots=True)
class TwitchEmbedSpecial(EmbedSpecial):
    """Represents information about Twitch stream or clip."""

    content_type: TwitchContentType = field(repr=True, hash=True, kw_only=True, eq=True)
    """The Twitch content type."""

    id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The Twitch content ID."""


@define(slots=True)
class SpotifyEmbedSpecial(EmbedSpecial):
    """Represents information about Spotify track."""

    content_type: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The Spotify content type."""

    id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The Spotify content ID."""


class SoundcloudEmbedSpecial(EmbedSpecial):
    """Represents information about Soundcloud track."""


_SOUNDCLOUD_EMBED_SPECIAL = SoundcloudEmbedSpecial()


class BandcampContentType(Enum):
    """Type of remote Bandcamp content."""

    album = "Album"
    track = "Track"


@define(slots=True)
class BandcampEmbedSpecial(EmbedSpecial):
    """Represents information about Bandcamp track."""

    content_type: BandcampContentType = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The Bandcamp content type."""

    id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The Bandcamp content ID."""


@define(slots=True)
class StreamableEmbedSpecial(EmbedSpecial):
    """Represents information about Streamable video."""

    id: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The video ID."""


class ImageSize(Enum):
    """Controls image positioning and size."""

    large = "Large"
    """Show large preview at the bottom of the embed."""

    preview = "Preview"
    """Show small preview to the side of the embed."""


@define(slots=True)
class ImageEmbed(_BaseEmbed):
    """Represents an image in a embed."""

    url: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The URL to the original image."""

    width: int = field(repr=True, hash=True, kw_only=True, eq=True)
    """The width of the image."""

    height: int = field(repr=True, hash=True, kw_only=True, eq=True)
    """The height of the image."""

    size: ImageSize = field(repr=True, hash=True, kw_only=True, eq=True)
    """The positioning and size of the image."""

    def _stateful(self, state: State) -> Embed:
        return self


@define(slots=True)
class VideoEmbed(_BaseEmbed):
    """Represents an video in a embed."""

    url: str = field(repr=True, hash=True, kw_only=True, eq=True)
    """The URL to the original video."""

    width: int = field(repr=True, hash=True, kw_only=True, eq=True)
    """The width of the video."""

    height: int = field(repr=True, hash=True, kw_only=True, eq=True)
    """The height of the video."""

    def _stateful(self, state: State) -> Embed:
        return self


@define(slots=True)
class WebsiteEmbed(_BaseEmbed):
    """Representation of website embed within Revolt message."""

    url: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The direct URL to web page."""

    original_url: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The original direct URL."""

    special: EmbedSpecial | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The remote content."""

    title: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The title of website."""

    description: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The description of website."""

    image: ImageEmbed | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The embedded image."""

    video: VideoEmbed | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The embedded video."""

    site_name: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The site name."""

    icon_url: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The URL to site icon."""

    colour: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The CSS colour of this embed."""

    def _stateful(self, state: State) -> Embed:
        return self


@define(slots=True)
class StatelessTextEmbed(_BaseEmbed):
    """Stateless representation of text embed within Revolt message."""

    icon_url: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The URL to site icon."""

    url: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The direct URL to web page."""

    title: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The title of text embed."""

    description: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The description of text embed."""

    internal_media: cdn.StatelessAsset | None = field(
        repr=True, hash=True, kw_only=True, eq=True
    )
    """The stateless embed media."""

    colour: str | None = field(repr=True, hash=True, kw_only=True, eq=True)
    """The CSS colour of this embed."""

    def _stateful(self, state: State) -> Embed:
        return TextEmbed(
            icon_url=self.icon_url,
            url=self.url,
            title=self.title,
            description=self.description,
            internal_media=self.internal_media,
            colour=self.colour,
            state=state,
        )


@define(slots=True)
class TextEmbed(StatelessTextEmbed):
    """Representation of text embed within Revolt message."""

    state: State = field(repr=False, hash=False, kw_only=True, eq=False)

    @property
    def media(self) -> cdn.Asset | None:
        """The embed media."""
        return (
            self.internal_media._stateful(self.state, "attachments")
            if self.internal_media
            else None
        )


class NoneEmbed(_BaseEmbed):
    """Embed that holds nothing."""

    def _stateful(self, state: State) -> Embed:
        return self


_NONE_EMBED = NoneEmbed()

StatelessEmbed = WebsiteEmbed | ImageEmbed | VideoEmbed | StatelessTextEmbed | NoneEmbed
Embed = WebsiteEmbed | ImageEmbed | VideoEmbed | TextEmbed | NoneEmbed

__all__ = (
    "_BaseEmbed",
    "EmbedSpecial",
    "NoneEmbedSpecial",
    "_NONE_EMBED_SPECIAL",
    "GifEmbedSpecial",
    "_GIF_EMBED_SPECIAL",
    "YouTubeEmbedSpecial",
    "LightspeedContentType",
    "LightspeedEmbedSpecial",
    "TwitchContentType",
    "TwitchEmbedSpecial",
    "SpotifyEmbedSpecial",
    "SoundcloudEmbedSpecial",
    "_SOUNDCLOUD_EMBED_SPECIAL",
    "BandcampContentType",
    "BandcampEmbedSpecial",
    "StreamableEmbedSpecial",
    "ImageSize",
    "ImageEmbed",
    "VideoEmbed",
    "WebsiteEmbed",
    "StatelessTextEmbed",
    "TextEmbed",
    "NoneEmbed",
    "_NONE_EMBED",
    "StatelessEmbed",
    "Embed",
)
