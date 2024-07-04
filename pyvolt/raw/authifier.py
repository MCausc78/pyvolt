from __future__ import annotations

import typing as t


# >> /models/mfa/mod.rs
class MultiFactorAuthentication(t.TypedDict):
    totp_token: t.NotRequired[Totp]
    recovery_codes: t.NotRequired[list[str]]


MFAMethod = t.Literal["Password", "Recovery", "Totp"]


class PasswordMFAResponse(t.TypedDict):
    password: str


class RecoveryMFAResponse(t.TypedDict):
    recovery_code: str


class TotpMFAResponse(t.TypedDict):
    totp_code: str


MFAResponse = PasswordMFAResponse | RecoveryMFAResponse | TotpMFAResponse


# >> /models/mfa/totp.rs
class DisabledTotp(t.TypedDict):
    status: t.Literal["Disabled"]


class PendingTotp(t.TypedDict):
    status: t.Literal["Pending"]


class EnabledTotp(t.TypedDict):
    status: t.Literal["Enabled"]


Totp = DisabledTotp | PendingTotp | EnabledTotp

# >> /models/account.rs


class VerifiedEmailVerification(t.TypedDict):
    status: t.Literal["Verified"]


class PendingEmailVerification(t.TypedDict):
    stauts: t.Literal["Pending"]


class MovingEmailVerification(t.TypedDict):
    status: t.Literal["Moving"]
    new_email: str
    token: str
    expiry: str


EmailVerification = (
    VerifiedEmailVerification | PendingEmailVerification | MovingEmailVerification
)


class PasswordReset(t.TypedDict):
    token: str
    expiry: str


class WaitingForVerificationDeletionInfo(t.TypedDict):
    status: t.Literal["WaitingForVerification"]
    token: str
    expiry: str


class ScheduledDeletionInfo(t.TypedDict):
    status: t.Literal["Scheduled"]
    after: str


class DeletedDeletionInfo(t.TypedDict):
    status: t.Literal["Deleted"]


DeletionInfo = (
    WaitingForVerificationDeletionInfo | ScheduledDeletionInfo | DeletedDeletionInfo
)


class Lockout(t.TypedDict):
    attempts: int
    expiry: str | None


class Account(t.TypedDict):
    _id: str
    email: str
    email_normalised: str
    disabled: bool
    verification: EmailVerification
    password_reset: PasswordReset | None
    deletion: DeletionInfo | None
    lockout: Lockout | None
    mfa: "MultiFactorAuthentication"


# >> /models/session.rs


class WebPushSubscription(t.TypedDict):
    endpoint: str
    p256dh: str
    auth: str


class Session(t.TypedDict):
    _id: str
    user_id: str
    token: str
    name: str
    subscription: t.NotRequired[WebPushSubscription]


# >> /models/ticket.rs
class MFATicket(t.TypedDict):
    _id: str
    account_id: str
    token: str
    validated: bool
    authorised: bool
    last_totp_code: str | None


# >> /events/mod.rs
class AuthifierCreateAccountEvent(t.TypedDict):
    event_type: t.Literal["CreateAccount"]
    account: Account


class AuthifierCreateSessionEvent(t.TypedDict):
    event_type: t.Literal["CreateSession"]
    session: Session


class AuthifierDeleteSessionEvent(t.TypedDict):
    event_type: t.Literal["DeleteSession"]
    user_id: str
    session_id: str


class AuthifierDeleteAllSessionsEvent(t.TypedDict):
    event_type: t.Literal["DeleteAllSessions"]
    user_id: str
    exclude_session_id: str | None


AuthifierEvent = (
    AuthifierCreateAccountEvent
    | AuthifierCreateSessionEvent
    | AuthifierDeleteSessionEvent
    | AuthifierDeleteAllSessionsEvent
)

# HTTP requests/responses


class DataChangeEmail(t.TypedDict):
    email: str
    current_password: str


class DataChangePassword(t.TypedDict):
    password: str
    current_password: str


class DataAccountDeletion(t.TypedDict):
    token: str


class DataCreateAccount(t.TypedDict):
    email: str
    password: str
    invite: str | None
    captcha: str | None


class AccountInfo(t.TypedDict):
    _id: str
    email: str


class DataPasswordReset(t.TypedDict):
    token: str
    password: str
    remove_sessions: t.NotRequired[bool | None]


class DataResendVerification(t.TypedDict):
    email: str
    captcha: str | None


class DataSendPasswordReset(t.TypedDict):
    email: str
    captcha: str | None


class NoTicketResponseVerify(t.TypedDict):
    pass


class WithTicketResponseVerify(t.TypedDict):
    ticket: MFATicket


ResponseVerify = NoTicketResponseVerify | WithTicketResponseVerify


class MultiFactorStatus(t.TypedDict):
    email_otp: bool
    trusted_handover: bool
    email_mfa: bool
    totp_mfa: bool
    security_key_mfa: bool
    recovery_active: bool


class ResponseTotpSecret(t.TypedDict):
    secret: str


class DataEditSession(t.TypedDict):
    friendly_name: str


class SessionInfo(t.TypedDict):
    _id: str
    name: str


class EmailDataLogin(t.TypedDict):
    email: str
    password: str
    friendly_name: str | None


class MFADataLogin(t.TypedDict):
    mfa_ticket: str
    mfa_response: MFAResponse | None
    friendly_name: str | None


DataLogin = EmailDataLogin | MFADataLogin


class SuccessResponseLogin(Session):
    result: t.Literal["Success"]


class MFAResponseLogin(t.TypedDict):
    result: t.Literal["MFA"]
    ticket: str
    allowed_methods: list[MFAMethod]


class DisabledResponseLogin(t.TypedDict):
    result: t.Literal["Disabled"]
    user_id: str


ResponseLogin = SuccessResponseLogin | MFAResponseLogin | DisabledResponseLogin

__all__ = (
    "MultiFactorAuthentication",
    "MFAMethod",
    "PasswordMFAResponse",
    "RecoveryMFAResponse",
    "TotpMFAResponse",
    "MFAResponse",
    "DisabledTotp",
    "PendingTotp",
    "EnabledTotp",
    "Totp",
    "VerifiedEmailVerification",
    "PendingEmailVerification",
    "MovingEmailVerification",
    "EmailVerification",
    "PasswordReset",
    "WaitingForVerificationDeletionInfo",
    "ScheduledDeletionInfo",
    "DeletedDeletionInfo",
    "DeletionInfo",
    "Lockout",
    "Account",
    "WebPushSubscription",
    "Session",
    "MFATicket",
    "AuthifierCreateAccountEvent",
    "AuthifierCreateSessionEvent",
    "AuthifierDeleteSessionEvent",
    "AuthifierDeleteAllSessionsEvent",
    "AuthifierEvent",
    "DataChangeEmail",
    "DataChangePassword",
    "DataAccountDeletion",
    "DataCreateAccount",
    "AccountInfo",
    "DataPasswordReset",
    "DataResendVerification",
    "DataSendPasswordReset",
    "NoTicketResponseVerify",
    "WithTicketResponseVerify",
    "ResponseVerify",
    "MultiFactorStatus",
    "ResponseTotpSecret",
    "DataEditSession",
    "SessionInfo",
    "EmailDataLogin",
    "MFADataLogin",
    "DataLogin",
    "SuccessResponseLogin",
    "MFAResponseLogin",
    "DisabledResponseLogin",
    "ResponseLogin",
)
