# ruff: noqa
"""
A clean, typed, sync Python client for the WorkFlowy API.
"""

# SPDX-FileCopyrightText: 2023-present Rodolfo J. O. <rodolfo@example.com>
#
# SPDX-License-Identifier: MIT
__version__ = "0.0.1"

from .client import WorkflowyClient
from .errors import (
    AuthError,
    ClientError,
    NotFoundError,
    RateLimitError,
    ServerError,
    WorkflowyError,
)
from .models import Node

__all__ = [
    "WorkflowyClient",
    "Node",
    "WorkflowyError",
    "AuthError",
    "NotFoundError",
    "RateLimitError",
    "ClientError",
    "ServerError",
]
