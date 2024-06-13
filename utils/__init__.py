"""Utilities module for web_file_downloader package."""

from .custom_exceptions import UnsupportedBrowserTypeError  # noqa: F401  (suppress unused import)
from .custom_exceptions import UnsupportedOSError  # noqa: F401
from .custom_exceptions import WebDriverNotFoundError  # noqa: F401
from .download_info import DownloadInfo  # noqa: F401
from .file_downloader import FileDownloader  # noqa: F401
from .logger_util import setup_logging  # noqa: F401  # noqa: F401
from .webdriver_manager import WebDriverManager  # noqa: F401

# Banner
__version__ = "0.1.6"
__author__ = "DFIRSec (@pulsecode)"

banner = rf"""
  _____                 _____       _____
 |\    \   _____   ____|\    \  ___|\    \
 | |    | /    /| |    | \    \|    |\    \
 \/     / |    || |    |______/|    | |    |
 /     /_  \   \/ |    |----'\ |    | |    |
|     // \  \   \ |    |_____/ |    | |    |
|    |/   \ |    ||    |       |    | |    |
|\ ___/\   \|   /||____|       |____|/____/|
| |   | \______/ ||    |       |    /    | |
 \|___|/\ |    | ||____|       |____|____|/
    \(   \|____|/   )/           \(    )/
     '      )/      '             '    '
            '
                    v{__version__}
                    by {__author__}
"""
