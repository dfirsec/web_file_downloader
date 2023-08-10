"""Download web hosted files by filetype/file extension."""

import asyncio
import logging
import platform
import re
import sys
from collections.abc import AsyncIterator
from pathlib import Path
from urllib.parse import urljoin
from urllib.parse import urlparse

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
        """Initialize the class."""
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
        """Get the HTML page."""
        async with session.get(req_url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
            response.raise_for_status()
        return await response.text()

    async def link_parser(self, base_url: str, filetype: str, html: str) -> AsyncIterator[str]:
        """Parse the HTML page for links."""
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
                _, ext = Path(path).suffix
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
        """Download the file."""
        async with semaphore:
            path = urlparse(download_url).path
            _, ext = Path(path).suffix
            filename = Path(path).name
            dlpath = Path(self.filepath / filename)

            if dlpath.resolve().exists():
                console.print(f"[grey58][-] File already exists: {filename}")
                return

            try:
                async with async_timeout.timeout(10), session.get(download_url, headers=self.headers) as response:
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
                logging.exception(f"Timeout error when downloading '{download_url}'.")
                failed_downloads.append(download_url)

            except Exception as exc:
                self.console.print(f"[red][!] Error downloading '{download_url}': {type(exc).__name__}: {exc}")
                logging.exception(f"Error downloading '{download_url}': {type(exc).__name__}")

    async def main(self, url: str, filetype: str) -> None:
        """Main program."""
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
    """Check if the URL is valid."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return bool(parsed.scheme and parsed.netloc)


if __name__ == "__main__":
    # Check python version.
    if sys.version_info < (3, 8):
        console.print(f"[plum4]Tested on Python v3.8+. May not work properly with v{platform.python_version()}\n")

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
