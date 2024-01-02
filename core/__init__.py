"""Core package for web_file_downloader."""

__version__ = "0.1.4"
__author__ = "DFIRSec (@pulsecode)"

from .downloader import FileDownloader  # noqa: F401 (suppress unused import)
from .logger import setup_logging  # noqa: F401
from .utils import DownloadInfo  # noqa: F401
from .utils import UnsupportedBrowserTypeError  # noqa: F401
from .utils import UnsupportedOSError  # noqa: F401
from .utils import WebDriverNotFoundError  # noqa: F401
from .utils import is_valid_url  # noqa: F401
