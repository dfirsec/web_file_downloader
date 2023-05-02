"""Download web hosted files by filetype/file extension."""

import asyncio
import logging
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
from bs4 import BeautifulSoup
from rich.console import Console

console = Console()

author = "DFIRSec (@pulsecode)"
version = "0.1.2"


class FileDownloader(object):
    """Contains main program functionality."""

    def __init__(self):
        """
        Initializes various variables and settings for the downloader.

        Creates a directory for downloaded files and sets up logging.
        """
        self.console = Console()
        self.root = Path(__file__).parent.resolve()
        self.filepath = self.root.joinpath("Downloads")
        self.filepath.mkdir(parents=True, exist_ok=True)
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"}

        logging.basicConfig(
            level=logging.ERROR,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler("error_log.log")],
        )

    async def get_page(self, session: aiohttp.ClientSession, req_url: str) -> str:
        """
        Aynchronous function that uses aiohttp library to GET the response body as a string.

        Args:
            session (aiohttp.ClientSession):
              ClientSession object used to make the HTTP request.
            req_url (str):
              req_url is a string parameter that represents the URL of the webpage that we want to retrieve.

        Returns:
            str: HTML content of the requested page.
        """
        async with session.get(req_url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
            response.raise_for_status()
            html = await response.text()
        return html

    async def link_parser(self, base_url: str, filetype: str, html: str) -> AsyncIterator[str]:
        """
        Asynchronous generator function that parses HTML content and yields URLs of files.

        Args:
            base_url (str):
              The base URL of the webpage to be used for resolving relative URLs.
            filetype (str):
              The file type to look for when parsing the HTML content.
            html (str):
              The HTML content of the webpage to be parsed.

        Yields:
            str: The URLs of files with the specified file type.
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

    async def downloader(
        self,
        semaphore: asyncio.Semaphore,
        session: aiohttp.ClientSession,
        download_url: str,
        filetype: str,
        failed_downloads: list,
    ) -> None:
        """
        Asynchronous downloader function with error handling for timeouts and incorrect file types.

        Args:
            semaphore (asyncio.Semaphore):
              An asyncio Semaphore object used to limit the number of concurrent downloads.
            session (ClientSession):
              An instance of the aiohttp ClientSession class, used to make HTTP requests.
                It allows for persistent connections and connection pooling, which can improve
                performance when making multiple requests to the same server.
            download_url (str):
              The URL of the file to be downloaded.
            filetype (str):
              The file type that the downloader is looking for. It is used to check if the downloaded
                file matches the expected file type.
            failed_downloads (list):
              A list that keeps track of the URLs that failed to download. If an exception occurs during
                the download process, the URL is added to this list.

        Returns:
            None: The function does not return anything, it is a coroutine that uses async/await syntax to
                perform asynchronous tasks.
        """
        async with semaphore:
            path = urlparse(download_url).path
            _, ext = os.path.splitext(path)
            filename = os.path.basename(path)
            dlpath = Path(self.filepath / filename)

            if dlpath.resolve().exists():
                console.print(f"[grey58][-] File already exists: {filename}")
                return

            try:
                async with async_timeout.timeout(10):
                    async with session.get(download_url, headers=self.headers) as response:
                        if ext and ext.lower().split(".")[1] == filetype.lower() and not dlpath.resolve().exists():
                            self.console.print(f"[green][+] Downloading: {filename}")
                            async with aiofiles.open(dlpath, "wb") as fileobj:
                                while True:
                                    chunk = await response.content.read(1024)
                                    if not chunk:
                                        break
                                    await fileobj.write(chunk)
                            await response.release()

            except asyncio.TimeoutError:
                self.console.print(f"[red][!] Timeout error when downloading '{download_url}'.")
                logging.error(f"Timeout error when downloading '{download_url}'.")
                failed_downloads.append(download_url)

            except Exception as exc:
                self.console.print(f"[red][!] Error downloading '{download_url}': {type(exc).__name__}: {exc}")
                logging.exception(f"Error downloading '{download_url}': {type(exc).__name__}: {exc}")

    async def main(self, url: str, filetype: str) -> None:
        """
        Asynchronous function that locates and downloads files of the specified type from the given URL.

        Args:
            url (str):
              The URL of the webpage to be scraped for files of a certain filetype
            filetype (str):
              The `filetype` parameter is a string that specifies the type of file to be located
                and downloaded. It is used in the `link_parser` function to filter out links that
                do not match the specified file type. It is also passed to the `downloader`
                function to ensure that only files.
        """
        max_concurrent_downloads = 10

        async with aiohttp.ClientSession() as session:
            console.print(f"[cyan][*] Locating '{filetype}' files...")
            html = await self.get_page(session, url)
            tasks = []
            semaphore = asyncio.Semaphore(max_concurrent_downloads)
            failed_downloads = []

            async for urlitem in self.link_parser(url, filetype, html):
                task = asyncio.create_task(self.downloader(semaphore, session, urlitem, filetype, failed_downloads))
                tasks.append(task)

            await asyncio.gather(*tasks)

            if failed_downloads:
                self.console.print("\n[gold1][!] Retrying failed downloads...")
                tasks = []

                for failed in failed_downloads:
                    task = asyncio.create_task(self.downloader(semaphore, session, failed, filetype, []))
                    tasks.append(task)

                await asyncio.gather(*tasks)


def is_valid_url(url: str) -> bool:
    """
    Checks if URL is valid by parsing it and checking if it has a scheme and network location.

    Args:
        url (str):
          A string representing a URL that needs to be validated

    Returns:
        bool: A boolean value indicating whether the input `url` is a valid URL or not.
            If the URL is valid, the function returns `True`, otherwise it returns `False`.
    """
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return bool(parsed.scheme and parsed.netloc)


if __name__ == "__main__":
    # Check python version.
    if sys.version_info.minor < 8:
        console.print(f"[plum4]Tested on Python v3.8+. May not work properly with v{platform.python_version()}\n")

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
    downloader = FileDownloader()
    asyncio.run(downloader.main(MAINURL, FILETYPE))
