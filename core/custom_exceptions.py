"""Custom exceptions."""

import logging

# Set up error logger
error_logger = logging.getLogger("error_logger")


class WebDriverNotFoundError(KeyError):
    """Raised when the WebDriver for a specific browser type is not found in the configuration."""

    def __init__(self, browser_type: str) -> None:
        """Initialize the exception."""
        self.browser_type = browser_type

    def __str__(self) -> str:
        """Return error message."""
        error_logger.error(f"Path for {self.browser_type} not found in config.")
        return f"Path for {self.browser_type} not found in config."


class UnsupportedOSError(OSError):
    """Raised when an unsupported operating system is used."""

    def __str__(self) -> str:
        """Return error message."""
        error_logger.error("Unsupported operating system")
        return "Unsupported operating system"


class UnsupportedBrowserTypeError(ValueError):
    """Raised when an unsupported browser type is used."""

    def __str__(self) -> str:
        """Return error message."""
        error_logger.error("Unsupported browser type")
        return "Unsupported browser type"
