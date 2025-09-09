from typing import Optional

import httpx


class WorkflowyError(Exception):
    """Base exception for all workflowy-py errors."""

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        response: Optional[httpx.Response] = None,
    ):
        if message is None and response is not None:
            message = f"Request failed with status code {response.status_code}"
        super().__init__(message)
        self.response = response


class AuthError(WorkflowyError):
    """Raised for authentication errors (401)."""

class NotFoundError(WorkflowyError):
    """Raised when a resource is not found (404)."""

class RateLimitError(WorkflowyError):
    """Raised for rate limit errors (429)."""

class ClientError(WorkflowyError):
    """Raised for other client-side errors (4xx)."""

class ServerError(WorkflowyError):
    """Raised for server-side errors (5xx)."""
