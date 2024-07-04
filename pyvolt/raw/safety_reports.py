from __future__ import annotations

import typing as t


class BaseReport(t.TypedDict):
    _id: str
    author_id: str
    content: ReportedContent
    additional_context: str
    notes: str


ContentReportReason = t.Literal[
    "NoneSpecified",
    "Illegal",
    "IllegalGoods",
    "IllegalExtortion",
    "IllegalPornography",
    "IllegalHacking",
    "ExtremeViolence",
    "PromotesHarm",
    "UnsolicitedSpam",
    "Raid",
    "SpamAbuse",
    "ScamsFraud",
    "Malware",
    "Harassment",
]

UserReportReason = t.Literal[
    "NoneSpecified",
    "UnsolicitedSpam",
    "SpamAbuse",
    "InappropriateProfile",
    "Impersonation",
    "BanEvasion",
    "Underage",
]


class MessageReportedContent(t.TypedDict):
    type: t.Literal["Message"]
    id: str
    report_reason: ContentReportReason


class ServerReportedContent(t.TypedDict):
    type: t.Literal["Server"]
    id: str
    report_reason: ContentReportReason


class UserReportedContent(t.TypedDict):
    type: t.Literal["User"]
    id: str
    report_reason: UserReportReason
    message_id: t.NotRequired[str]


ReportedContent = MessageReportedContent | ServerReportedContent | UserReportedContent


class CreatedReport(BaseReport):
    status: t.Literal["Created"]


class RejectedReport(BaseReport):
    status: t.Literal["Rejected"]
    rejection_reason: str
    closed_at: str | None


class ResolvedReport(BaseReport):
    status: t.Literal["Resolved"]
    closed_at: str | None


Report = CreatedReport | RejectedReport | ResolvedReport


class DataReportContent(t.TypedDict):
    content: ReportedContent
    additional_context: t.NotRequired[str]


__all__ = (
    "BaseReport",
    "ContentReportReason",
    "UserReportReason",
    "MessageReportedContent",
    "ServerReportedContent",
    "UserReportedContent",
    "ReportedContent",
    "CreatedReport",
    "RejectedReport",
    "ResolvedReport",
    "Report",
    "DataReportContent",
)
