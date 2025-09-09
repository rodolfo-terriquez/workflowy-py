import os
from unittest import mock

import pytest
from workflowy_py import config


@pytest.fixture(autouse=True)
def clear_env_and_config_file():
    """Ensure a clean slate for each test."""
    with mock.patch.dict(os.environ, {}, clear=True):
        with mock.patch("pathlib.Path.exists", return_value=False):
            with mock.patch("pathlib.Path.read_text", return_value=""):
                yield


def test_discover_token_explicit():
    """Explicitly passed token should be used."""
    token = "explicit_token"
    assert config.discover_token(token) == token


def test_discover_token_from_env():
    """Token should be read from the environment variable."""
    token = "env_token"
    os.environ[config.ENV_TOKEN_NAME] = token
    assert config.discover_token() == token


def test_discover_token_from_file():
    """Token should be read from the config file."""
    token = "file_token"
    with mock.patch("pathlib.Path.exists", return_value=True):
        with mock.patch("pathlib.Path.read_text", return_value=token):
            assert config.discover_token() == token


def test_discover_token_priority():
    """Token discovery should follow the correct priority."""
    explicit_token = "explicit"
    env_token = "env"
    file_token = "file"

    os.environ[config.ENV_TOKEN_NAME] = env_token
    with mock.patch("pathlib.Path.exists", return_value=True):
        with mock.patch("pathlib.Path.read_text", return_value=file_token):
            # Explicit > env > file
            assert config.discover_token(explicit_token) == explicit_token

            # env > file
            assert config.discover_token() == env_token

    # Just file
    os.environ.pop(config.ENV_TOKEN_NAME, None)
    with mock.patch("pathlib.Path.exists", return_value=True):
        with mock.patch("pathlib.Path.read_text", return_value=file_token):
            assert config.discover_token() == file_token


def test_discover_token_not_found():
    """Should return None if no token is found."""
    assert config.discover_token() is None
