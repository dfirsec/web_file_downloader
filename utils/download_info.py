"""Contains the FileDownloader class."""

from dataclasses import dataclass
from pathlib import Path

import httpx


@dataclass
class DownloadInfo:
    """Contains information about the file to be downloaded.

    Attributes:
        session (httpx.AsyncClient): The HTTP session to be used for downloading the file.
        download_url (str): The URL to download the file from.
        download_path (Path): The path to download the file to.
        extension (str): The extension of the file to be downloaded.
        filetype (str): The type of the file to be downloaded.
        failed_downloads (list[str]): List of URLs that failed to download.
        expected_size (int): The expected size of the file to be downloaded.
    """

    session: httpx.AsyncClient
    download_url: str
    download_path: Path
    extension: str
    filetype: str
    failed_downloads: list[str]
    expected_size: int = 0  # default value


