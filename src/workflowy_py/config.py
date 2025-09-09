import os
from pathlib import Path
from typing import Optional

DEFAULT_BASE_URL = "https://workflowy.com/api/v1"
DEFAULT_TIMEOUT = 10.0
ENV_TOKEN_NAME = "WORKFLOWY_API_TOKEN"
CONFIG_FILE = Path.home() / ".workflowy" / "config"

def discover_token(token: Optional[str] = None) -> Optional[str]:
    """
    Discover the WorkFlowy API token from explicit arg, env var, or config file.
    """
    if token:
        return token
    if ENV_TOKEN_NAME in os.environ:
        return os.environ[ENV_TOKEN_NAME]
    if CONFIG_FILE.exists():
        return CONFIG_FILE.read_text().strip()
    return None
