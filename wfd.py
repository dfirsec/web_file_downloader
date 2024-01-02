"""Download web hosted files by filetype/file extension."""

import asyncio
import platform
import sys
from pathlib import Path

from core import FileDownloader
from core import __author__
from core import __version__
from core import is_valid_url
from rich.console import Console

# Rich console object
console = Console()


def get_browser_choice() -> str:
    """Get browser choice from user input."""
    browsers = ["chrome", "edge", "firefox"]
    while True:
        try:
            console.print("[cyan]Select a browser:")
            for i, browser in enumerate(browsers, start=1):
                console.print(f"{i}. {browser.title()}", highlight=False)
            console.print("[yellow]Q. Quit")

            choice = input("Enter your choice (1-3): ")
            if choice.isdigit() and 1 <= int(choice) <= 3:
                return browsers[int(choice) - 1]
            if choice in ["q", "Q", "quit", "Quit"]:
                console.print("[green]Exiting...")
                return None
            console.print("[yellow]Please enter a number between 1 and 3, or 'q' to quit.")
        except KeyboardInterrupt:
            console.print("\n[red][!] Exiting...")
            return None


def main() -> None:
    """Main function."""
    console.print(f"[sea_green2]{banner}")

    if len(sys.argv) < 3:
        console.print(f"Usage: python {Path(__file__).name} <URL> <FILE TYPE>", style="red")
        return

    main_url = sys.argv[1]
    file_type = sys.argv[2]

    if not is_valid_url(main_url):
        console.print(f"[red][!] {main_url} is not a valid URL")
        return

    browser_choice = get_browser_choice()
    if browser_choice is None:
        return

    downloader = FileDownloader(browser_type=browser_choice)
    asyncio.run(downloader.main(main_url, file_type))


if __name__ == "__main__":
    banner = fr"""
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

    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        main()
    except Exception as e:
        console.print(f"[red]An error occurred: {e}")
        sys.exit(1)
