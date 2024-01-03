"""Contains the FileDownloader class."""

import json
import logging
import math
import re
import sys
import threading
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin
from urllib.parse import urlparse

import httpx
import trio
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from rich.console import Console
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .custom_exceptions import UnsupportedBrowserTypeError
from .custom_exceptions import WebDriverNotFoundError

# Rich console object
console = Console()

# Set up logging parameters
logs_dir = Path(__file__).parent.parent.joinpath("Logs")
error_logger = logging.getLogger("error_logger")
download_logger = logging.getLogger("download_logger")


@dataclass
class DownloadInfo:
    """Contains information about the file to be downloaded.

    Attributes:
        session (httpx.AsyncClient): The HTTP session to be used for downloading the file.
        download_url (str): The URL to download the file from.
        download_path (Path): The path to download the file to.
        extension (str): The extension of the file to be downloaded.
        filetype (str): The type of the file to be downloaded.
        failed_downloads (list[str]): List of URLs that failed to download.
        expected_size (int): The expected size of the file to be downloaded.
    """

    session: httpx.AsyncClient
    download_url: str
    download_path: Path
    extension: str
    filetype: str
    failed_downloads: list[str]
    expected_size: int = 0  # default value


class WebDriverManager:
    """Manages WebDrivers for different browsers."""

    def __init__(self, browser_type: str, driver_path: Path) -> None:
        """Initialize class instance."""
        self.browser_type = browser_type
        self.driver_path = driver_path
        self.ua = UserAgent()

    def get_webdriver(self) -> webdriver.Chrome | webdriver.Firefox | webdriver.Edge | None:
        """Returns the appropriate WebDriver based on the browser type."""
        if self.browser_type == "chrome":
            return self.chrome_webdriver()
        if self.browser_type == "edge":
            return self.edge_webdriver()
        if self.browser_type == "firefox":
            return self.firefox_webdriver()
        raise UnsupportedBrowserTypeError()

    def firefox_webdriver(self) -> webdriver.Firefox:
        """Initialize Firefox WebDriver."""
        options = FirefoxOptions()
        options.add_argument("--headless")
        options.add_argument(f"user-agent={self.ua.random}")

        firefox_log_path = logs_dir / "firefox.log"
        firefox_service = FirefoxService(
            executable_path=self.driver_path,
            service_log_path=str(firefox_log_path),
        )

        return webdriver.Firefox(service=firefox_service, options=options)

    def edge_webdriver(self) -> webdriver.Edge:
        """Initialize Edge WebDriver."""
        options = EdgeOptions()
        self.chrome_edge_prefs(options)

        edge_log_path = logs_dir / "edge.log"
        edge_service = EdgeService(
            executable_path=self.driver_path,
            service_args=[f"--log-path={edge_log_path!s}"],
        )

        return webdriver.Edge(service=edge_service, options=options)

    def chrome_webdriver(self) -> webdriver.Chrome:
        """Initialize Chrome WebDriver."""
        options = ChromeOptions()
        self.chrome_edge_prefs(options)

        chrome_log_path = logs_dir / "chrome.log"
        chrome_service = ChromeService(
            executable_path=self.driver_path,
            service_args=[f"--log-path={chrome_log_path!s}"],
        )
        return webdriver.Chrome(service=chrome_service, options=options)

    def chrome_edge_prefs(self, options: webdriver.edge.options.Options | webdriver.chrome.options.Options) -> None:
        """Set preferences for Chrome and Edge."""
        options.add_argument(f"user-agent={self.ua.random}")
        options.add_argument("--headless=new")
        options.add_argument("--disable-logging")
        options.add_argument("--log-level=3")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])


class FileDownloader:
    """Contains main program functionality."""

    def __init__(self: "FileDownloader") -> None:
        """Initialize class instance.

        Args:
            browser_type (str): Type of browser to use.

        Raises:
            UnsupportedBrowserTypeError: Unsupported browser type.
            WebDriverNotFoundError: WebDriver not found at specified path.
        """
        self.ua = UserAgent()
        self.root = Path(__file__).parent.parent.resolve()
        self.filepath = self.root.joinpath("Downloads")
        self.filepath.mkdir(parents=True, exist_ok=True)
        self.headers = {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        self.config = self.load_config()
        self.browser_type = self.config["preferred_browser"]
        self.driver_path = self.config["webdrivers"][self.browser_type]
        self.driver_path = self.get_driver_path()

        if not self.webdriver_exists(self.driver_path):
            self.webdriver_error()
            sys.exit(1)
        self.web_driver_manager = WebDriverManager(self.browser_type, self.driver_path)

    def webdriver_error(self) -> None:
        """Print error message and exit."""
        console.print(f"\n[red]Failed to initialize WebDriver for {self.browser_type}.")
        error_logger.error(f"Failed to initialize WebDriver for {self.browser_type}.")
        console.print("[yellow]Please verify the path in config.json is correct.")
        console.print("Download the WebDriver from the following URLs based on your browser:")
        console.print("- Chrome: https://chromedriver.chromium.org/downloads")
        console.print("- Edge: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/")
        console.print("- Firefox: https://github.com/mozilla/geckodriver")
        console.print("[yellow]Ensure the WebDriver version matches your browser version.")
        error_logger.error("Exiting due to missing WebDriver.")
        sys.exit("Exiting due to missing WebDriver.")

    def load_config(self) -> dict[str, str]:
        """Load the configuration file.

        Returns:
            dict[str, str]: WebDriver path configuration data.
        """
        with Path.open("config.json") as file:
            return json.load(file)

    def get_driver_path(self) -> str:
        """Get the path to the WebDriver executable.

        Returns:
            str: Path to the WebDriver executable.

        Raises:
            WebDriverNotFoundError: WebDriver not found at specified path.
        """
        try:
            return self.config["webdrivers"][self.browser_type]
        except KeyError as err:
            raise WebDriverNotFoundError(self.browser_type) from err

    def webdriver_exists(self, path: Path) -> bool:
        """Check if the WebDriver exists at specified path."""
        resolved_path = Path(path).resolve()
        return bool(resolved_path.is_file())

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

        # Check for links
        for link in soup.find_all("a"):
            href = link.get("href")
            if href and href.lower().endswith(filetype.lower()):
                yield urljoin(base_url, href)

        # Check for images
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

    async def downloader_with_limiter(self, download_info: DownloadInfo, limiter: trio.CapacityLimiter) -> None:
        """Download the file with a capacity limiter."""
        async with limiter:
            await self.downloader(download_info)

    async def downloader(self, download_info: DownloadInfo) -> None:
        """Download the file.

        Args:
            download_info (DownloadInfo): DownloadInfo object.
        """
        filename, download_path, _extension = self.extract_file_info(download_info.download_url)

        if download_path.resolve().exists():
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
        extension = Path(path).suffix
        filename = Path(path).name
        download_path = Path(self.filepath / filename)
        return filename, download_path, extension

    def calculate_timeout(self, file_size: int, base_timeout: int = 10, max_timeout: int = 30) -> int:
        """Calculate the download timeout based on file size.

        Args:
            file_size (int): The size of the file in bytes.
            base_timeout (int): The base timeout in seconds (for small files).
            max_timeout (int): The maximum allowed timeout.

        Returns:
            int: The calculated timeout in seconds.
        """
        mb_size = file_size / (1024 * 1024)
        additional_time = min(10 * math.log(mb_size + 1, 2), max_timeout - base_timeout)

        return min(base_timeout + additional_time, max_timeout)

    async def download_file(self: "FileDownloader", download_info: DownloadInfo) -> None:
        """Handle the file download using httpx and trio.

        Args:
            download_info (DownloadInfo): DownloadInfo object.
        """
        try:
            timeout_duration = self.calculate_timeout(file_size=download_info.expected_size)

            with trio.move_on_after(timeout_duration):
                async with httpx.AsyncClient(follow_redirects=True) as client:
                    response = await client.get(download_info.download_url)

                    if response.status_code == 404:
                        console.print(f"[red][!] File not found: {download_info.download_url}")
                        error_logger.exception(f"File not found (404): '{download_info.download_url}'")
                        return

                    response.raise_for_status()
                    file_size = int(response.headers.get("Content-Length", 0))

                    console.print(f"[green][+] Downloading: {download_info.download_path.name}")
                    async with await trio.open_file(download_info.download_path, "wb") as fileobj:
                        async for chunk in response.aiter_bytes():
                            await fileobj.write(chunk)

                    download_logger.info(f"Successfully downloaded {download_info.download_path.name}")

                download_info.expected_size = file_size

        except trio.TooSlowError:
            error_logger.exception(f"Timeout error when downloading '{download_info.download_url}'")
            console.print(f"[red][!] Timeout occurred while downloading {download_info.download_url}[/red]")
        except httpx.HTTPStatusError:
            error_logger.exception(f"HTTP error when downloading '{download_info.download_url}'")
            console.print(f"[red][!] HTTP error occurred while downloading {download_info.download_url}")
            download_info.failed_downloads.append(download_info.download_url)
        except Exception:
            error_logger.exception(f"Error downloading '{download_info.download_url}'")
            console.print(f"[red][!] Error occurred while downloading {download_info.download_url}[/red]")

    def get_html(self, url: str) -> str:
        """Use Selenium to fetch the HTML content.

        Args:
            url (str): URL of the web page.

        Returns:
            str: HTML page content.
        """
        driver = self.web_driver_manager.get_webdriver()
        try:
            driver.get(url)
            # Wait 5 seconds until the body tag is found
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except Exception:
            console.print("[red][!] Error in get_html_with_selenium")
            logging.exception("Error in get_html_with_selenium")
            return ""
        else:
            return driver.page_source
        finally:
            driver.quit()

    def run_selenium_in_thread(self, url: str) -> str:
        """Run Selenium in a separate thread to prevent blocking the main async loop.

        Args:
            url (str): URL of the web page.

        Returns:
                str: HTML page content.
        """
        result = []

        def target() -> None:
            """Target function for the thread."""
            result.append(self.get_html(url))

        thread = threading.Thread(target=target)
        thread.start()
        thread.join()
        return result[0] if result else ""

    async def main(self: "FileDownloader", url: str, filetype: str) -> None:
        """Main program.

        Args:
            url (str): URL of the web page.
            filetype (str): File type to be downloaded.
        """
        max_concurrent_downloads = 10

        async with httpx.AsyncClient() as session:
            console.print(f"\n[cyan][*] Locating '{filetype}' files...")

            # Use run_selenium_in_thread to fetch HTML content
            html = self.run_selenium_in_thread(url)

            capacity_limiter = trio.CapacityLimiter(max_concurrent_downloads)

            async with trio.open_nursery() as nursery:
                failed_downloads = []

                # Check if the HTML page was retrieved
                if html is not None:
                    async for urlitem in self.link_parser(url, filetype, html):
                        _filename, download_path, extension = self.extract_file_info(urlitem)
                        download_info = DownloadInfo(
                            session,
                            urlitem,
                            download_path,
                            extension,
                            filetype,
                            failed_downloads,
                        )
                        nursery.start_soon(
                            self.downloader_with_limiter,
                            download_info,
                            capacity_limiter,
                        )

                if failed_downloads:
                    console.print("\n[gold1][!] Retrying failed downloads...")
                    for failed in failed_downloads:
                        _filename, download_path, extension = self.extract_file_info(failed)
                        download_info = DownloadInfo(
                            session,
                            failed,
                            download_path,
                            extension,
                            filetype,
                            [],
                        )
                        nursery.start_soon(
                            self.downloader_with_limiter,
                            download_info,
                            capacity_limiter,
                        )
