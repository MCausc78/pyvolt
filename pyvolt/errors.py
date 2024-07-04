from typing import Any

import aiohttp

Response = aiohttp.ClientResponse


class PyvoltError(Exception):
    pass


class APIError(PyvoltError):
    response: Response
    type: str
    retry_after: float | None
    error: str | None
    max: int | None
    permission: str | None
    operation: str | None
    collection: str | None
    location: str | None
    with_: str | None

    def __init__(
        self,
        response: Response,
        data: dict[str, Any] | str,
        *,
        message: str | None = None,
    ) -> None:
        self.response = response
        self.data = data
        errors = []
        if message is not None:
            errors.append(message)
        if isinstance(data, str):
            self.type = "NonJSON"
            self.retry_after = None
            self.err = data
            errors.append(data)
            self.max = None
            self.permission = None
            self.operation = None
            self.collection = None
            self.location = None
            self.with_ = None
        else:
            self.type = data.get("type", "Unknown")
            self.retry_after = data.get("retry_after")
            if self.retry_after is not None:
                errors.append(f"retry_after={self.retry_after}")
            self.error = data.get("error")
            if self.error is not None:
                errors.append(f"error={self.error}")
            self.max = data.get("max")
            if self.max is not None:
                errors.append(f"max={self.max}")
            self.permission = data.get("permission")
            if self.permission is not None:
                errors.append(f"permission={self.permission}")
            self.operation = data.get("operation")
            if self.operation is not None:
                errors.append(f"operation={self.operation}")
            self.collection = data.get("collection")
            if self.collection is not None:
                errors.append(f"collection={self.collection}")
            self.location = data.get("location")
            if self.location is not None:
                errors.append(f"location={self.location}")
            self.with_ = data.get("with")
            if self.with_ is not None:
                errors.append(f"with={self.with_}")
        super().__init__(
            self.type
            if len(errors) == 0
            else f"{self.type}: {' '.join(errors)} (raw={data})\n"
        )


class Unauthorized(APIError):
    pass


class Forbidden(APIError):
    pass


class NotFound(APIError):
    pass


class Ratelimited(APIError):
    pass


class InternalServerError(APIError):
    pass


class BadGateway(APIError):
    pass


class ShardError(PyvoltError):
    pass


class AuthenticationError(ShardError):
    def __init__(self, a: Any) -> None:
        super().__init__("Failed to connect shard", a)


class ConnectError(ShardError):
    def __init__(self, tries: int, errors: list[Exception]) -> None:
        self.errors = errors
        super().__init__(f"Giving up, after {tries} tries, last 3 errors:", errors[-3:])


class DiscoveryError(PyvoltError):
    def __init__(
        self,
        response: aiohttp.ClientResponse,
        status: int,
        data: str,
    ) -> None:
        self.response = response
        self.status = status
        self.data = data
        super().__init__(status, data)


class NoData(PyvoltError):
    def __init__(self, what: str, type: str) -> None:
        self.what = what
        self.type = type
        super().__init__(f"Unable to find {type} {what} in cache")


__all__ = (
    "PyvoltError",
    "APIError",
    "Unauthorized",
    "Forbidden",
    "NotFound",
    "Ratelimited",
    "InternalServerError",
    "BadGateway",
    "ShardError",
    "AuthenticationError",
    "ConnectError",
    "DiscoveryError",
    "NoData",
)
