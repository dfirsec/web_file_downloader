import asyncio
import os
import platform
import sys
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin

import aiofiles
import aiohttp
import async_timeout
import requests
import validators
from bs4 import BeautifulSoup

__author__ = "DFIRSec (@pulsecode)"
__version__ = "0.1.0"
__description__ = "Download web hosted files by filetype/file extension."

# Creates "Downloads" directory in the same directory as the script.
ROOT = Path(__file__).parent.resolve()
FILEPATH = ROOT.joinpath("Downloads")
FILEPATH.mkdir(parents=True, exist_ok=True)

_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
}


def link_parser(req_url: str, filetype: str) -> Iterable:
    """
    Takes a URL and a filetype as arguments, and returns a generator object that yields all the links
    on the page that end with the specified filetype

    :param req_url: The URL to parse
    :param filetype: The filetype you want to search for
    """
    try:
        response = requests.get(req_url, headers=_headers, timeout=10)
        response.raise_for_status()
    except (ConnectionError, requests.exceptions.HTTPError) as error:
        sys.exit(f"[x] {error}")
    else:
        soup = BeautifulSoup(response.text, "html.parser")
        if results := {link.get("href") for link in soup.find_all("a") if link.get("href") is not None}:
            for link in results:
                if os.path.basename(link).split(".")[-1] == filetype:
                    yield urljoin(req_url, link) if req_url not in link else link


async def downloader(session, download_url):
    """
    Downloads the file from the URL and saves it to the filepath

    :param session: the aiohttp session object
    :param download_url: The URL of the file to download
    :return: The response object is being returned.
    """
    async with async_timeout.timeout(10):
        async with session.get(download_url, headers=_headers) as response:
            filename = os.path.basename(download_url)
            dlpath = Path(FILEPATH / filename)
            if not dlpath.resolve().exists():
                print(f"[+] Downloading: {filename}")
                async with aiofiles.open(dlpath, "wb") as fileobj:
                    while True:
                        chunk = await response.content.read(1024)
                        if not chunk:
                            break
                        await fileobj.write(chunk)
                return await response.release()

            print(f"[-] File already exists: {filename}")


async def main(url: str, filetype: str):
    """
    Takes a URL and a file type as arguments, and downloads all files of that type from the URL

    :param url: The URL of the page you want to download from
    :param ftype: The file type you want to download
    """
    if urls := list(link_parser(url, filetype)):
        async with aiohttp.ClientSession() as session:
            print(f"[+] Located {len(urls)} '{filetype}' files...")
            for urlitem in urls:
                await downloader(session, urlitem)
    else:
        print(f"[x] File type '{filetype}' does not appear to be available, or URL is is incorrect.")


if __name__ == "__main__":

    # Check python version.
    if sys.version_info.minor < 8:
        print(f"[!] Tested on Python version 3.8+. May not work with {platform.python_version()}\n")

    # Check if the user has entered the correct number of arguments.
    if len(sys.argv) < 3:
        sys.exit(f"Usage: python {os.path.basename(__file__)} <URL> <FILE TYPE>")
    else:
        MAINURL = sys.argv[1]
        FILETYPE = sys.argv[2]

    # Check if the URL is valid.
    if not validators.url(MAINURL):  # type: ignore
        sys.exit(f"[!] {MAINURL} is not a valid URL")

    # Resolves issue: https://github.com/encode/httpx/issues/914
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Running the main function asynchronously.
    asyncio.run(main(MAINURL, FILETYPE))
