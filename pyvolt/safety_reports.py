from .enums import Enum


class ContentReportReason(Enum):
    """The reason for reporting content (message or server)."""

    none = "NoneSpecified"
    """No reason has been specified."""

    illegal = "Illegal"
    """Illegal content catch-all reason."""

    illegal_goods = "IllegalGoods"
    """Selling or facilitating use of drugs or other illegal goods."""

    illegal_extortion = "IllegalExtortion"
    """Extortion or blackmail."""

    illegal_pornography = "IllegalPornography"
    """Revenge or child pornography."""

    illegal_hacking = "IllegalHacking"
    """Illegal hacking activity."""

    extreme_violence = "ExtremeViolence"
    """Extreme violence, gore, or animal cruelty. With exception to violence potrayed in media / creative arts."""

    promotes_harm = "PromotesHarm"
    """Content that promotes harm to others / self."""

    unsolicited_spam = "UnsolicitedSpam"
    """Unsolicited advertisements."""

    raid = "Raid"
    """This is a raid."""

    spam_abuse = "SpamAbuse"
    """Spam or platform abuse."""

    scams_fraud = "ScamsFraud"
    """Scams or fraud."""

    malware = "Malware"
    """Distribution of malware or malicious links."""

    harassment = "Harassment"
    """Harassment or abuse targeted at another user."""


class UserReportReason(Enum):
    """Reason for reporting a user."""

    none = "NoneSpecified"
    """No reason has been specified."""

    unsolicited_spam = "UnsolicitedSpam"
    """Unsolicited advertisements."""

    spam_abuse = "SpamAbuse"
    """User is sending spam or otherwise abusing the platform."""

    inappropriate_profile = "InappropriateProfile"
    """User's profile contains inappropriate content for a general audience."""

    impersonation = "Impersonation"
    """User is impersonating another user."""

    ban_evasion = "BanEvasion"
    """User is evading a ban."""

    underage = "Underage"
    """User is not of minimum age to use the platform."""


__all__ = ("ContentReportReason", "UserReportReason")
