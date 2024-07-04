from enum import StrEnum


class ContentReportReason(StrEnum):
    """The reason for reporting content (message or server)."""

    NONE = "NoneSpecified"
    """No reason has been specified."""

    ILLEGAL = "Illegal"
    """Illegal content catch-all reason."""

    ILLEGAL_GOODS = "IllegalGoods"
    """Selling or facilitating use of drugs or other illegal goods."""

    ILLEGAL_EXTORTION = "IllegalExtortion"
    """Extortion or blackmail."""

    ILLEGAL_PORNOGRAPHY = "IllegalPornography"
    """Revenge or child pornography."""

    ILLEGAL_HACKING = "IllegalHacking"
    """Illegal hacking activity."""

    EXTREME_VIOLENCE = "ExtremeViolence"
    """Extreme violence, gore, or animal cruelty. With exception to violence potrayed in media / creative arts."""

    PROMOTES_HARM = "PromotesHarm"
    """Content that promotes harm to others / self."""

    UNSOLICITED_SPAM = "UnsolicitedSpam"
    """Unsolicited advertisements."""

    RAID = "Raid"
    """This is a raid."""

    SPAM_ABUSE = "SpamAbuse"
    """Spam or platform abuse."""

    SCAMS_FRAUD = "ScamsFraud"
    """Scams or fraud."""

    MALWARE = "Malware"
    """Distribution of malware or malicious links."""

    HARASSMENT = "Harassment"
    """Harassment or abuse targeted at another user."""


class UserReportReason(StrEnum):
    """Reason for reporting a user."""

    NONE = "NoneSpecified"
    """No reason has been specified."""

    UNSOLICITED_SPAM = "UnsolicitedSpam"
    """Unsolicited advertisements."""

    SPAM_ABUSE = "SpamAbuse"
    """User is sending spam or otherwise abusing the platform."""

    INAPPROPRIATE_PROFILE = "InappropriateProfile"
    """User's profile contains inappropriate content for a general audience."""

    IMPERSONATION = "Impersonation"
    """User is impersonating another user."""

    BAN_EVASION = "BanEvasion"
    """User is evading a ban."""

    UNDERAGE = "Underage"
    """User is not of minimum age to use the platform."""


__all__ = ("ContentReportReason", "UserReportReason")
