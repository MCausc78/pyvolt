import typing


class CaptchaFeature(typing.TypedDict):
    enabled: bool
    key: str


class Feature(typing.TypedDict):
    enabled: bool
    url: str


class VoiceFeature(typing.TypedDict):
    enabled: bool
    url: str
    ws: str


class RevoltFeatures(typing.TypedDict):
    captcha: CaptchaFeature
    email: bool
    invite_only: bool
    autumn: Feature
    january: Feature
    voso: VoiceFeature


class BuildInformation(typing.TypedDict):
    commit_sha: str
    commit_timestamp: str
    semver: str
    origin_url: str
    timestamp: str


class RevoltConfig(typing.TypedDict):
    revolt: str
    features: RevoltFeatures
    ws: str
    app: str
    vapid: str
    build: BuildInformation


__all__ = ('CaptchaFeature', 'Feature', 'VoiceFeature', 'RevoltFeatures', 'BuildInformation', 'RevoltConfig')
