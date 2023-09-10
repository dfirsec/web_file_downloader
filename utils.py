"""Utility functions and classes for web_dl_by_type."""

from pathlib import Path
from typing import NamedTuple
from urllib.parse import urlparse

import aiohttp


class CustomClientError(aiohttp.ClientError):
    """Custom ClientError exception."""

    def __init__(self: "CustomClientError") -> None:
        """Raised when a possible anti-scraping measure is detected.

        Attributes:
        - `message` : Error message.
        """
        super().__init__("Possible anti-scraping measure detected")


class DownloadInfo(NamedTuple):
    """Contains information about the file to be downloaded.

    Attributes:
    - `session` : Instance of `ClientSession` from `aiohttp` module.
    - `download_url` : URL of the file to be downloaded.
    - `dlpath` : Path to the file to be downloaded.
    - `ext` : File extension of the file to be downloaded.
    - `filetype` : File type of the file to be downloaded.
    - `failed_downloads` : List of failed downloads.
    """

    session: aiohttp.ClientSession
    download_url: str
    dlpath: Path
    ext: str
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
        return False
    return bool(parsed.scheme and parsed.netloc)
