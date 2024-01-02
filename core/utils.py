"""Utility functions and classes for web_dl_by_type."""


import logging
from pathlib import Path
from typing import NamedTuple
from urllib.parse import urlparse

import aiohttp

from .logger import setup_logging

# Call the function to set up logging
setup_logging()


class WebDriverNotFoundError(KeyError):
    """Raised when the WebDriver for a specific browser type is not found in the configuration."""

    def __init__(self, browser_type: str) -> None:
        """Initialize the exception."""
        self.browser_type = browser_type

    def __str__(self) -> str:
        """Return error message."""
        logging.error(f"Path for {self.browser_type} not found in config.")
        return f"Path for {self.browser_type} not found in config."


class UnsupportedOSError(OSError):
    """Raised when an unsupported operating system is used."""

    def __str__(self) -> str:
        """Return error message."""
        logging.error("Unsupported operating system")
        return "Unsupported operating system"


class UnsupportedBrowserTypeError(ValueError):
    """Raised when an unsupported browser type is used."""

    def __str__(self) -> str:
        """Return error message."""
        logging.error("Unsupported browser type")
        return "Unsupported browser type"


class DownloadInfo(NamedTuple):
    """Contains information about the file to be downloaded.

    Attributes:
        session (aiohttp.ClientSession): The aiohttp session.
        download_url (str): The URL to download the file from.
        download_path (Path): The path to download the file to.
        extension (str): The extension of the file to be downloaded.
        filetype (str): The type of the file to be downloaded.
        failed_downloads (list[str]): List of URLs that failed to download.
    """

    session: aiohttp.ClientSession
    download_url: str
    download_path: Path
    extension: str
    filetype: str
    failed_downloads: list[str]


def is_valid_url(url: str) -> bool:
    """Check if the URL is valid.

    Args:
        url (str): URL to be checked.

    Returns:
        bool: True if the URL is valid, False otherwise.
    """
    try:
        parsed = urlparse(url)
    except ValueError:
        logging.exception(f"{url} is not a valid URL")
        return False
    return bool(parsed.scheme and parsed.netloc)
