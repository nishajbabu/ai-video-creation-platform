"""
Application startup and environment initialization.

This module is responsible for loading environment configuration
before the rest of the application initializes its services.

The LLM configuration layer deliberately does not load .env itself.
That responsibility belongs here.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_FILE = PROJECT_ROOT / ".env"


# ---------------------------------------------------------------------------
# Environment initialization
# ---------------------------------------------------------------------------

def load_environment(
    env_file: Optional[Path] = None,
) -> Path:
    """
    Load application environment variables.

    Args:
        env_file:
            Optional custom environment file.

            When omitted, the project's root .env file is used.

    Returns:
        Path to the environment file that was requested.

    Notes:
        Existing process environment variables are not overwritten.
        This prevents externally supplied deployment variables from
        being unexpectedly replaced by values from .env.
    """

    path = env_file or ENV_FILE

    load_dotenv(
        dotenv_path=path,
        override=False,
    )

    return path


# ---------------------------------------------------------------------------
# Environment helpers
# ---------------------------------------------------------------------------

def get_environment(
    name: str,
    default: Optional[str] = None,
) -> Optional[str]:
    """
    Read one environment variable.

    Args:
        name:
            Environment variable name.

        default:
            Value returned when the variable is not configured.

    Returns:
        Environment variable value or default.
    """

    value = os.getenv(name)

    if value is None:
        return default

    return value


def is_environment_configured(
    name: str,
) -> bool:
    """
    Determine whether an environment variable has a
    non-empty value.

    The actual secret value is never returned.
    """

    value = os.getenv(name)

    if value is None:
        return False

    return bool(value.strip())


# ---------------------------------------------------------------------------
# LLM environment initialization
# ---------------------------------------------------------------------------

def initialize_llm_environment() -> Path:
    """
    Initialize the environment required by the LLM subsystem.

    This is intentionally kept separate from LLMConfig so that:

        startup.py
            ↓
        environment
            ↓
        LLMConfig
            ↓
        KeyManager
            ↓
        LLMService

    Returns:
        Path to the loaded .env file.
    """

    return load_environment()


# ---------------------------------------------------------------------------
# Application startup
# ---------------------------------------------------------------------------

def initialize_application() -> None:
    """
    Perform application-wide environment initialization.

    This function is intentionally lightweight.

    Service construction will happen in the application's
    dependency/bootstrap layer rather than inside this module.
    """

    initialize_llm_environment()