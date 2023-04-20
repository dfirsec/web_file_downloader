import asyncio
import os
import platform
import re
import sys
from pathlib import Path
from typing import AsyncIterator
from urllib.parse import urljoin, urlparse

import aiofiles
import aiohttp
import async_timeout
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from rich import print as rprint
from rich.console import Console

CONSOLE = Console()

__author__ = "DFIRSec (@pulsecode)"
__version__ = "0.1.1"
__description__ = "Download web hosted files by filetype/file extension."

ROOT = Path(__file__).parent.resolve()
FILEPATH = ROOT.joinpath("Downloads")
FILEPATH.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"}

MAX_CONCURRENT_DOWNLOADS = 10


async def get_page(session: aiohttp.ClientSession, req_url: str) -> str:
    """
    Aynchronous function that uses aiohttp library to make a GET request
    to a specified URL and returns the response body as a string.

    :param session: aiohttp.ClientSession object used to make the HTTP request
    :type session: aiohttp.ClientSession
    :param req_url: req_url is a string parameter that represents the URL of the webpage that we want to
    retrieve
    :type req_url: str
    :return: a string, which is the HTML content of the requested page.
    """
    async with session.get(req_url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=10)) as response:
        response.raise_for_status()
        html = await response.text()
    return html


async def link_parser(base_url: str, filetype: str, html: str) -> AsyncIterator[str]:
    """
    Extracts links to files of specified type from HTML content and yields
    them as an asynchronous iterator.

    :param base_url: The base URL of the website being parsed
    :type base_url: str
    :param filetype: The file extension/type that the function should search for in the HTML and extract
    links for
    :type filetype: str
    :param html: The HTML content of a webpage that needs to be parsed for links
    :type html: str
    """
    pattern = re.compile(r"https?://\S+" + re.escape(filetype))
    for match in pattern.finditer(html):
        yield match.group()

    soup = BeautifulSoup(html, "lxml")
    for link in soup.find_all("a"):
        href = link.get("href")
        if href and href.lower().endswith(filetype.lower()):
            yield urljoin(base_url, href)

    for img in soup.find_all("img"):
        src = img.get("src")
        data_src = img.get("data-src")
        final_src = data_src or src

        if final_src is not None:
            url = urljoin(base_url, final_src)
            path = urlparse(url).path
            _, ext = os.path.splitext(path)
            ext = ext.split("?")[0]

            if ext.lower() == filetype.lower():
                yield url


async def downloader(semaphore: asyncio.Semaphore, session: ClientSession, download_url: str, filetype: str) -> None:
    """
    Asynchronous function that downloads a file from the given URL if it matches the file type.

    :param semaphore: An asyncio Semaphore object used to limit the number of concurrent downloads
    :type semaphore: asyncio.Semaphore
    :param session: The session parameter is an instance of the aiohttp.ClientSession class, which is
    used to make HTTP requests. It allows for persistent connections and connection pooling, which can
    improve performance when making multiple requests to the same server
    :type session: ClientSession
    :param download_url: The URL of the file to be downloaded
    :type download_url: str
    :param filetype: The parameter 'filetype' is a string that represents the file type that the
    downloader function is looking for. It is used to check if the downloaded file has the same file
    type as the one specified
    :type filetype: str
    """
    async with semaphore:
        try:
            async with async_timeout.timeout(10):
                async with session.get(download_url, headers=HEADERS) as response:
                    path = urlparse(download_url).path
                    _, ext = os.path.splitext(path)
                    if ext.lower().split(".")[1] == filetype.lower():
                        filename = os.path.basename(path)
                        dlpath = Path(FILEPATH / filename)
                        if not dlpath.resolve().exists():
                            rprint(f"[+] Downloading: {filename}")
                            async with aiofiles.open(dlpath, "wb") as fileobj:
                                while True:
                                    chunk = await response.content.read(1024)
                                    if not chunk:
                                        break
                                    await fileobj.write(chunk)
                            await response.release()
                        else:
                            rprint(f"[-] File already exists: {filename}")
                    else:
                        rprint(f"[x] '{download_url}' is not a file of type '{filetype}'.")
        except Exception as err:
            print(f"[!] Error downloading '{download_url}': {type(err).__name__}: {err}")


async def main(url: str, filetype: str):
    """
    Asynchronous function that locates and downloads files of the specified type from the given URL.

    :param url: The URL of the webpage to be scraped for files of a certain filetype
    :type url: str
    :param filetype: The `filetype` parameter is a string that specifies the type of file to be located
    and downloaded. It is used in the `link_parser` function to filter out links that do not match the
    specified file type. It is also passed to the `downloader` function to ensure that only files
    :type filetype: str
    """
    async with aiohttp.ClientSession() as session:
        rprint(f"[+] Locating '{filetype}' files...")
        html = await get_page(session, url)
        tasks = []
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
        async for urlitem in link_parser(url, filetype, html):
            task = asyncio.create_task(downloader(semaphore, session, urlitem, filetype))
            tasks.append(task)
        await asyncio.gather(*tasks)


def is_valid_url(url: str) -> bool:
    """
    Checks if URL is valid by parsing it and checking if it has a scheme and network location.

    :param url: A string representing a URL that needs to be validated
    :type url: str
    :return: The function `is_valid_url` returns a boolean value indicating whether the input `url` is a
    valid URL or not. If the URL is valid, the function returns `True`, otherwise it returns `False`.
    """
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)
    except ValueError:
        return False


if __name__ == "__main__":
    # Check python version.
    if sys.version_info.minor < 8:
        CONSOLE.print(f"Tested on Python version 3.8. May not work with {platform.python_version()}\n")

    # Check if the user has entered the correct number of arguments.
    MAINURL = ""
    FILETYPE = ""

    if len(sys.argv) < 3:
        sys.exit(f"Usage: python {os.path.basename(__file__)} <URL> <FILE TYPE>")
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
    asyncio.run(main(MAINURL, FILETYPE))
