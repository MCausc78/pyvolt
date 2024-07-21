from __future__ import annotations

import typing


class BaseReport(typing.TypedDict):
    _id: str
    author_id: str
    content: ReportedContent
    additional_context: str
    notes: str


ContentReportReason = typing.Literal[
    'NoneSpecified',
    'Illegal',
    'IllegalGoods',
    'IllegalExtortion',
    'IllegalPornography',
    'IllegalHacking',
    'ExtremeViolence',
    'PromotesHarm',
    'UnsolicitedSpam',
    'Raid',
    'SpamAbuse',
    'ScamsFraud',
    'Malware',
    'Harassment',
]

UserReportReason = typing.Literal[
    'NoneSpecified',
    'UnsolicitedSpam',
    'SpamAbuse',
    'InappropriateProfile',
    'Impersonation',
    'BanEvasion',
    'Underage',
]


class MessageReportedContent(typing.TypedDict):
    type: typing.Literal['Message']
    id: str
    report_reason: ContentReportReason


class ServerReportedContent(typing.TypedDict):
    type: typing.Literal['Server']
    id: str
    report_reason: ContentReportReason


class UserReportedContent(typing.TypedDict):
    type: typing.Literal['User']
    id: str
    report_reason: UserReportReason
    message_id: typing.NotRequired[str]


ReportedContent = MessageReportedContent | ServerReportedContent | UserReportedContent


class CreatedReport(BaseReport):
    status: typing.Literal['Created']


class RejectedReport(BaseReport):
    status: typing.Literal['Rejected']
    rejection_reason: str
    closed_at: str | None


class ResolvedReport(BaseReport):
    status: typing.Literal['Resolved']
    closed_at: str | None


Report = CreatedReport | RejectedReport | ResolvedReport


class DataReportContent(typing.TypedDict):
    content: ReportedContent
    additional_context: typing.NotRequired[str]


__all__ = (
    'BaseReport',
    'ContentReportReason',
    'UserReportReason',
    'MessageReportedContent',
    'ServerReportedContent',
    'UserReportedContent',
    'ReportedContent',
    'CreatedReport',
    'RejectedReport',
    'ResolvedReport',
    'Report',
    'DataReportContent',
)
