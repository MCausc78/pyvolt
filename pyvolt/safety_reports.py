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

import typing

from attrs import define, field

from .base import Base
from .enums import ReportStatus, ReportedContentType

if typing.TYPE_CHECKING:
    from datetime import datetime

    from .enums import ContentReportReason, UserReportReason


@define(slots=True)
class BaseReport(Base):
    """Represents a user-generated platform moderation report on Revolt."""

    author_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The user's ID who created this report."""

    content: ReportedContent = field(repr=True, kw_only=True)
    """:class:`.ReportedContent`: The reported content."""

    additional_context: typing.Optional[str] = field(repr=True, kw_only=True)
    """Optional[:class:`str`]: The additional context included in report."""

    notes: str = field(repr=True, kw_only=True)
    """:class:`str`: The additional notes included in report."""

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, BaseReport) and self.id == other.id


@define(slots=True)
class CreatedReport(BaseReport):
    """Represents a created report on Revolt."""

    @property
    def status(self) -> typing.Literal[ReportStatus.created]:
        """Literal[:attr:`.ReportStatus.created`]: The report's status."""
        return ReportStatus.created


@define(slots=True)
class RejectedReport(BaseReport):
    """Represents a rejected report on Revolt."""

    rejection_reason: str = field(repr=True, kw_only=True)
    """:class:`str`: The reason why this report was rejected."""

    closed_at: typing.Optional[datetime] = field(repr=True, kw_only=True)
    """Optional[:class:`~datetime.datetime`]: When the report was closed."""

    @property
    def status(self) -> typing.Literal[ReportStatus.rejected]:
        """Literal[:attr:`.ReportStatus.rejected`]: The report's status."""
        return ReportStatus.rejected


@define(slots=True)
class ResolvedReport(BaseReport):
    """Represents a resolved report on Revolt."""

    closed_at: typing.Optional[datetime] = field(repr=True, kw_only=True)
    """Optional[:class:`~datetime.datetime`]: When the report was closed."""

    @property
    def status(self) -> typing.Literal[ReportStatus.resolved]:
        """Literal[:attr:`.ReportStatus.resolved`]: The report's status."""
        return ReportStatus.resolved


Report = typing.Union[CreatedReport, RejectedReport, ResolvedReport]


@define(slots=True)
class BaseReportedContent:
    """Represents content being reported."""

    target_id: str = field(repr=True, kw_only=True)
    """:class:`str`: The target's ID."""


@define(slots=True)
class MessageReportedContent(BaseReportedContent):
    """Represents a message being reported."""

    reason: ContentReportReason = field(repr=True, kw_only=True)
    """:class:`.ContentReportReason`: The reason why message was reported."""

    @property
    def type(self) -> typing.Literal[ReportedContentType.message]:
        """Literal[:attr:`.ReportedContentType.message`]: The content's type."""
        return ReportedContentType.message


@define(slots=True)
class ServerReportedContent(BaseReportedContent):
    """Represents a server being reported."""

    reason: ContentReportReason = field(repr=True, kw_only=True)
    """:class:`.ContentReportReason`: The reason why server was reported."""

    @property
    def type(self) -> typing.Literal[ReportedContentType.server]:
        """Literal[:attr:`.ReportedContentType.server`]: The content's type."""
        return ReportedContentType.server


@define(slots=True)
class UserReportedContent(BaseReportedContent):
    """Represents a user being reported."""

    reason: UserReportReason = field(repr=True, kw_only=True)
    """:class:`.UserReportReason`: The reason why user was reported."""

    message_id: typing.Optional[str] = field(repr=True, kw_only=True)
    """Optional[:class:`str`]: The message's ID with report context."""

    @property
    def type(self) -> typing.Literal[ReportedContentType.user]:
        """Literal[:attr:`.ReportedContentType.user`]: The content's type."""
        return ReportedContentType.user


ReportedContent = typing.Union[MessageReportedContent, ServerReportedContent, UserReportedContent]

__all__ = (
    'BaseReport',
    'CreatedReport',
    'RejectedReport',
    'ResolvedReport',
    'Report',
    'BaseReportedContent',
    'MessageReportedContent',
    'ServerReportedContent',
    'UserReportedContent',
    'ReportedContent',
)
