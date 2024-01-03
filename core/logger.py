"""Logging configuration."""

import logging
from pathlib import Path

# Directories and file paths
logs_dir = Path(__file__).parent.parent.joinpath("Logs")
errors_log = logs_dir.joinpath("errors.log")
downloads_log = logs_dir.joinpath("downloads.log")


def setup_logging() -> None:
    """Set up basic logging configuration."""
    # Ensure the logs directory exists
    logs_dir.mkdir(exist_ok=True)

    # Formatter for the log messages
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Error logger setup
    error_logger = logging.getLogger("error_logger")
    error_handler = logging.FileHandler(errors_log)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    error_logger.addHandler(error_handler)
    error_logger.setLevel(logging.ERROR)

    # Download logger setup
    download_logger = logging.getLogger("download_logger")
    download_handler = logging.FileHandler(downloads_log)
    download_handler.setLevel(logging.INFO)
    download_handler.setFormatter(formatter)
    download_logger.addHandler(download_handler)
    download_logger.setLevel(logging.INFO)


setup_logging()
