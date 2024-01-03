"""Download web hosted files by filetype/file extension."""

import re
import sys
from pathlib import Path

import trio
from core import FileDownloader
from core import banner
from rich.console import Console

# Rich console object
console = Console()


def is_valid_url(url: str) -> bool:
    """Check if the URL is valid using regex.

    Args:
        url (str): URL to be checked.

    Returns:
        bool: True if the URL is valid, False otherwise.
    """
    url_pattern = re.compile(r"^(https?)://[^\s/$.?#].[^\s]*$", re.IGNORECASE)
    return bool(url_pattern.match(url))


def main() -> None:
    """Main function."""
    console.print(f"[sea_green2]{banner}", highlight=False)

    if len(sys.argv) < 3:
        console.print(f"Usage: python {Path(__file__).name} <URL> <FILE TYPE>", style="bright_red", highlight=False)
        return

    url = sys.argv[1]
    file_type = sys.argv[2]

    if not is_valid_url(url):
        console.print(f"[bright_red][!] '{url}' is not a valid URL")
        return

    downloader = FileDownloader()
    trio.run(downloader.main, url, file_type)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("[red]Keyboard interrupt")
    except Exception as e:
        console.print(f"[red]An unexpected error occurred: {e}")
        sys.exit(1)
