"""Download web hosted files by filetype/file extension."""

import asyncio
import platform
import sys
from pathlib import Path

from rich.console import Console
from utils import is_valid_url

from downloader import FileDownloader

console = Console()

author = "DFIRSec (@pulsecode)"
version = "0.1.3"


if __name__ == "__main__":
    banner = """
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
"""

    console.print(f"[sea_green2]{banner}")
    # "Patorjk's Cheese" font by patorjk (patorjk@gmail.com) and x98.

    # Check python version.
    if sys.version_info < (3, 9):
        console.print(f"[plum4]Tested on Python v3.9+. May not work properly with v{platform.python_version()}\n")

    # Check if the user has entered the correct number of arguments.
    MAINURL = ""
    FILETYPE = ""

    if len(sys.argv) < 3:
        sys.exit(f"Usage: python {Path(__file__).name} <URL> <FILE TYPE>")
    else:
        MAINURL = sys.argv[1]
        FILETYPE = sys.argv[2]

    # Check if the URL is valid.
    if not is_valid_url(MAINURL):
        sys.exit(f"[!] {MAINURL} is not a valid URL")

    # Resolves issue: https://github.com/encode/httpx/issues/914
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Running the main function asynchronously.
    downloader = FileDownloader()
    asyncio.run(downloader.main(MAINURL, FILETYPE))
