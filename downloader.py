"""Contains the FileDownloader class."""

import asyncio
import logging
import re
from collections.abc import AsyncIterator
from pathlib import Path
from urllib.parse import urljoin
from urllib.parse import urlparse

import aiofiles
import aiohttp
import async_timeout
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from rich.console import Console
from utils import CustomClientError
from utils import DownloadInfo

console = Console()


class FileDownloader:
    """Contains main program functionality."""

    def __init__(self: "FileDownloader") -> None:
        """Initialize the class instance.

        Attributes:
        - `ue` : Instance of `UserAgent` from `fake_useragent` module.
        - `root` : Resolved path to the directory containing the current file.
        - `filepath` : Path to the "Downloads" directory located within the root directory.
                    If this directory doesn't exist, it's created.
        - `headers` : A dictionary containing request headers, including a randomly generated
                    User-Agent, Accept types, and Accept-Language specifications.
        """
        self.ua = UserAgent()
        self.root = Path(__file__).parent.resolve()
        self.filepath = self.root.joinpath("Downloads")
        self.filepath.mkdir(parents=True, exist_ok=True)
        self.headers = {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        logging.basicConfig(
            level=logging.ERROR,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler("errors.log")],
        )

    async def get_page(self: "FileDownloader", session: aiohttp.ClientSession, req_url: str) -> str | None:
        """Get the HTML page.

        Args:
            session (aiohttp.ClientSession): Instance of `ClientSession` from `aiohttp` module.
            req_url (str): URL of the web page.

        Returns:
            str | None: HTML page if successful, None otherwise.
        """
        max_retries = 3

        async def raise_client_error() -> None:
            """Raise a ClientError exception.

            Raises:
                CustomClientError: Custom ClientError exception.
            """
            raise CustomClientError()

        for retry in range(max_retries):
            try:
                async with session.get(
                    req_url,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    response.raise_for_status()

                    # Check if status is 403 Forbidden or the content length is too small
                    if response.status == 403 or len(await response.text()) < 100:
                        console.print("[red][!] The server might be blocking our requests.")
                        await raise_client_error()

                    return await response.text()

            except (aiohttp.ClientError, asyncio.TimeoutError):
                if retry == max_retries - 1:
                    await raise_client_error()
        return None

    async def link_parser(self: "FileDownloader", base_url: str, filetype: str, html: str) -> AsyncIterator[str]:
        """Parse the HTML page for links.

        Args:
            base_url (str): Base URL of the web page.
            filetype (str): File type to be downloaded.
            html (str): HTML page to be parsed.

        Yields:
            str: The URL of the file.
        """
        pattern = re.compile(r"https?://\S+" + re.escape(filetype))
        for match in pattern.finditer(html):
            yield match.group()

        soup = BeautifulSoup(html, "lxml")

        # Check for links.
        for link in soup.find_all("a"):
            href = link.get("href")
            if href and href.lower().endswith(filetype.lower()):
                yield urljoin(base_url, href)

        # Check for images.
        for img in soup.find_all("img"):
            src = img.get("src")
            data_src = img.get("data-src")
            final_src = data_src or src

            if final_src is not None:
                url = urljoin(base_url, final_src)
                path = urlparse(url).path
                ext = Path(path).suffix
                ext = ext.split("?")[0]

                if ext.lower() == filetype.lower():
                    yield url

    async def downloader(self: "FileDownloader", semaphore: asyncio.Semaphore, download_info: DownloadInfo) -> None:
        """Download the file.

        Args:
            semaphore (asyncio.Semaphore): Semaphore object.
            download_info (DownloadInfo): DownloadInfo object.
        """
        async with semaphore:
            filename, _, _ = self.extract_file_info(download_info.download_url)

            if download_info.dlpath.resolve().exists():
                console.print(f"[grey58][-] File already exists: {filename}")
                return

            await self.download_file(download_info)

    def extract_file_info(self: "FileDownloader", download_url: str) -> tuple[str, Path, str]:
        """Extract file-related information from the given URL.

        Args:
            download_url (str): URL of the file to be downloaded.

        Returns:
            tuple[str, Path, str]: A tuple containing the filename, download path, and file extension.
        """
        path = urlparse(download_url).path
        ext = Path(path).suffix
        filename = Path(path).name
        dlpath = Path(self.filepath / filename)
        return filename, dlpath, ext

    async def download_file(self: "FileDownloader", download_info: DownloadInfo) -> None:
        """Handle the actual file download.

        Args:
            download_info (DownloadInfo): DownloadInfo object.
        """
        try:
            async with async_timeout.timeout(10), download_info.session.get(
                download_info.download_url,
                headers=self.headers,
            ) as response:
                # Check file extension and that the file doesn't exist already
                if download_info.ext and download_info.ext.lower().endswith(download_info.filetype.lower()):
                    console.print(f"[green][+] Downloading: {download_info.dlpath.name}")
                    async with aiofiles.open(download_info.dlpath, "wb") as fileobj:
                        while True:
                            chunk = await response.content.read(1024)
                            if not chunk:
                                break
                            await fileobj.write(chunk)
                    await response.release()

        except asyncio.TimeoutError:
            msg = f"Timeout error when downloading '{download_info.download_url}'."
            console.print(f"[red][!] {msg}")
            logging.exception(msg)
            download_info.failed_downloads.append(download_info.download_url)

        except Exception as exc:
            msg = f"Error downloading '{download_info.download_url}': {type(exc).__name__}: {exc}"
            console.print(f"[red][!] {msg}")
            logging.exception(f"Error downloading '{download_info.download_url}': {type(exc).__name__}")

    async def main(self: "FileDownloader", url: str, filetype: str) -> None:
        """Main program.

        Args:
            url (str): URL of the web page.
            filetype (str): File type to be downloaded.
        """
        max_concurrent_downloads = 10

        async with aiohttp.ClientSession() as session:
            console.print(f"[cyan][*] Locating '{filetype}' files...")
            html = await self.get_page(session, url)
            tasks = []
            semaphore = asyncio.Semaphore(max_concurrent_downloads)
            failed_downloads = []

            # Check if the HTML page was retrieved successfully.
            if html is not None:
                async for urlitem in self.link_parser(url, filetype, html):
                    _filename, dlpath, ext = self.extract_file_info(urlitem)
                    download_info = DownloadInfo(session, urlitem, dlpath, ext, filetype, failed_downloads)
                    task = asyncio.create_task(self.downloader(semaphore, download_info))
                    tasks.append(task)

            else:
                console.print(f"[red][!] Error retrieving HTML page from '{url}'")
                logging.error(f"Error retrieving HTML page from '{url}'")

            # Download the files.
            await asyncio.gather(*tasks)

            if failed_downloads:
                console.print("\n[gold1][!] Retrying failed downloads...")
                tasks = []

                for failed in failed_downloads:
                    _filename, dlpath, ext = self.extract_file_info(failed)
                    download_info = DownloadInfo(session, failed, dlpath, ext, filetype, [])
                    task = asyncio.create_task(self.downloader(semaphore, download_info))
                    tasks.append(task)

                await asyncio.gather(*tasks)
