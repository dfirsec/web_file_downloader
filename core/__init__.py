"""Core package for web_file_downloader."""

from .custom_exceptions import UnsupportedBrowserTypeError  # noqa: F401  (suppress unused import)
from .custom_exceptions import UnsupportedOSError  # noqa: F401
from .custom_exceptions import WebDriverNotFoundError  # noqa: F401
from .downloader import DownloadInfo  # noqa: F401
from .downloader import FileDownloader  # noqa: F401
from .logger import setup_logging  # noqa: F401

__version__ = "0.1.5"
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
