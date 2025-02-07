from __future__ import annotations

import typing
import typing_extensions


# >> /models/mfa/mod.rs
class MultiFactorAuthentication(typing.TypedDict):
    totp_token: typing_extensions.NotRequired[Totp]
    recovery_codes: typing_extensions.NotRequired[list[str]]


MFAMethod = typing.Literal['Password', 'Recovery', 'Totp']


class PasswordMFAResponse(typing.TypedDict):
    password: str


class RecoveryMFAResponse(typing.TypedDict):
    recovery_code: str


class TotpMFAResponse(typing.TypedDict):
    totp_code: str


MFAResponse = typing.Union[PasswordMFAResponse, RecoveryMFAResponse, TotpMFAResponse]


# >> /models/mfa/totp.rs
class DisabledTotp(typing.TypedDict):
    status: typing.Literal['Disabled']


class PendingTotp(typing.TypedDict):
    status: typing.Literal['Pending']


class EnabledTotp(typing.TypedDict):
    status: typing.Literal['Enabled']


Totp = typing.Union[DisabledTotp, PendingTotp, EnabledTotp]

# >> /models/account.rs


class VerifiedEmailVerification(typing.TypedDict):
    status: typing.Literal['Verified']


class PendingEmailVerification(typing.TypedDict):
    stauts: typing.Literal['Pending']


class MovingEmailVerification(typing.TypedDict):
    status: typing.Literal['Moving']
    new_email: str
    token: str
    expiry: str


EmailVerification = typing.Union[VerifiedEmailVerification, PendingEmailVerification, MovingEmailVerification]


class PasswordReset(typing.TypedDict):
    token: str
    expiry: str


class WaitingForVerificationDeletionInfo(typing.TypedDict):
    status: typing.Literal['WaitingForVerification']
    token: str
    expiry: str


class ScheduledDeletionInfo(typing.TypedDict):
    status: typing.Literal['Scheduled']
    after: str


class DeletedDeletionInfo(typing.TypedDict):
    status: typing.Literal['Deleted']


DeletionInfo = typing.Union[WaitingForVerificationDeletionInfo, ScheduledDeletionInfo, DeletedDeletionInfo]


class Lockout(typing.TypedDict):
    attempts: int
    expiry: typing.Optional[str]


class Account(typing.TypedDict):
    _id: str
    email: str
    email_normalised: str
    disabled: bool
    verification: EmailVerification
    password_reset: typing.Optional[PasswordReset]
    deletion: typing.Optional[DeletionInfo]
    lockout: typing.Optional[Lockout]
    mfa: MultiFactorAuthentication


# >> /models/session.rs


class WebPushSubscription(typing.TypedDict):
    endpoint: str
    p256dh: str
    auth: str


class Session(typing.TypedDict):
    _id: str
    user_id: str
    token: str
    name: str
    subscription: typing_extensions.NotRequired[WebPushSubscription]


# >> /models/ticket.rs
class MFATicket(typing.TypedDict):
    _id: str
    account_id: str
    token: str
    validated: bool
    authorised: bool
    last_totp_code: typing.Optional[str]


# >> /events/mod.rs
class AuthifierCreateAccountEvent(typing.TypedDict):
    event_type: typing.Literal['CreateAccount']
    account: Account


class AuthifierCreateSessionEvent(typing.TypedDict):
    event_type: typing.Literal['CreateSession']
    session: Session


class AuthifierDeleteSessionEvent(typing.TypedDict):
    event_type: typing.Literal['DeleteSession']
    user_id: str
    session_id: str


class AuthifierDeleteAllSessionsEvent(typing.TypedDict):
    event_type: typing.Literal['DeleteAllSessions']
    user_id: str
    exclude_session_id: typing.Optional[str]


AuthifierEvent = typing.Union[
    AuthifierCreateAccountEvent,
    AuthifierCreateSessionEvent,
    AuthifierDeleteSessionEvent,
    AuthifierDeleteAllSessionsEvent,
]

# HTTP requests/responses


class DataChangeEmail(typing.TypedDict):
    email: str
    current_password: str


class DataChangePassword(typing.TypedDict):
    password: str
    current_password: str


class DataAccountDeletion(typing.TypedDict):
    token: str


class DataCreateAccount(typing.TypedDict):
    email: str
    password: str
    invite: typing.Optional[str]
    captcha: typing.Optional[str]


class AccountInfo(typing.TypedDict):
    _id: str
    email: str


class DataPasswordReset(typing.TypedDict):
    token: str
    password: str
    remove_sessions: typing_extensions.NotRequired[typing.Optional[bool]]


class DataResendVerification(typing.TypedDict):
    email: str
    captcha: typing.Optional[str]


class DataSendPasswordReset(typing.TypedDict):
    email: str
    captcha: typing.Optional[str]


class NoTicketResponseVerify(typing.TypedDict):
    pass


class WithTicketResponseVerify(typing.TypedDict):
    ticket: MFATicket


ResponseVerify = typing.Union[NoTicketResponseVerify, WithTicketResponseVerify]


class MultiFactorStatus(typing.TypedDict):
    email_otp: bool
    trusted_handover: bool
    email_mfa: bool
    totp_mfa: bool
    security_key_mfa: bool
    recovery_active: bool


class ResponseTotpSecret(typing.TypedDict):
    secret: str


class DataEditSession(typing.TypedDict):
    friendly_name: str


class SessionInfo(typing.TypedDict):
    _id: str
    name: str


class EmailDataLogin(typing.TypedDict):
    email: str
    password: str
    friendly_name: typing.Optional[str]


class MFADataLogin(typing.TypedDict):
    mfa_ticket: str
    mfa_response: typing.Optional[MFAResponse]
    friendly_name: typing.Optional[str]


DataLogin = typing.Union[EmailDataLogin, MFADataLogin]


class SuccessResponseLogin(Session):
    result: typing.Literal['Success']


class MFAResponseLogin(typing.TypedDict):
    result: typing.Literal['MFA']
    ticket: str
    allowed_methods: list[MFAMethod]


class DisabledResponseLogin(typing.TypedDict):
    result: typing.Literal['Disabled']
    user_id: str


ResponseLogin = typing.Union[SuccessResponseLogin, MFAResponseLogin, DisabledResponseLogin]
