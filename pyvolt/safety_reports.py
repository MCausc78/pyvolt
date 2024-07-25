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

from .enums import Enum


class ContentReportReason(Enum):
    """The reason for reporting content (message or server)."""

    none = 'NoneSpecified'
    """No reason has been specified."""

    illegal = 'Illegal'
    """Illegal content catch-all reason."""

    illegal_goods = 'IllegalGoods'
    """Selling or facilitating use of drugs or other illegal goods."""

    illegal_extortion = 'IllegalExtortion'
    """Extortion or blackmail."""

    illegal_pornography = 'IllegalPornography'
    """Revenge or child pornography."""

    illegal_hacking = 'IllegalHacking'
    """Illegal hacking activity."""

    extreme_violence = 'ExtremeViolence'
    """Extreme violence, gore, or animal cruelty. With exception to violence potrayed in media / creative arts."""

    promotes_harm = 'PromotesHarm'
    """Content that promotes harm to others / self."""

    unsolicited_spam = 'UnsolicitedSpam'
    """Unsolicited advertisements."""

    raid = 'Raid'
    """This is a raid."""

    spam_abuse = 'SpamAbuse'
    """Spam or platform abuse."""

    scams_fraud = 'ScamsFraud'
    """Scams or fraud."""

    malware = 'Malware'
    """Distribution of malware or malicious links."""

    harassment = 'Harassment'
    """Harassment or abuse targeted at another user."""


class UserReportReason(Enum):
    """Reason for reporting a user."""

    none = 'NoneSpecified'
    """No reason has been specified."""

    unsolicited_spam = 'UnsolicitedSpam'
    """Unsolicited advertisements."""

    spam_abuse = 'SpamAbuse'
    """User is sending spam or otherwise abusing the platform."""

    inappropriate_profile = 'InappropriateProfile'
    """User's profile contains inappropriate content for a general audience."""

    impersonation = 'Impersonation'
    """User is impersonating another user."""

    ban_evasion = 'BanEvasion'
    """User is evading a ban."""

    underage = 'Underage'
    """User is not of minimum age to use the platform."""


__all__ = ('ContentReportReason', 'UserReportReason')
