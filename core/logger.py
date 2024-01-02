"""Logging configuration."""

import logging
from pathlib import Path

logs_dir = Path(__file__).parent.parent.joinpath("logs")
errors_log = logs_dir.joinpath("errors.log")

def setup_logging() -> None:
    """Set up basic logging configuration."""
    logging.basicConfig(
        level=logging.ERROR,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(errors_log)],
    )
