"""Contains the FileDownloader class."""

import asyncio
import json
import logging
import re
import sys
import threading
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

from .logger import setup_logging
from .utils import DownloadInfo
from .utils import UnsupportedBrowserTypeError
from .utils import WebDriverNotFoundError

# Rich console object
console = Console()

# Set up logging parameters
setup_logging()


# Path to the logs directory
logs_dir = Path(__file__).parent.parent.joinpath("logs")
logs_dir.mkdir(exist_ok=True)


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
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-logging")
        options.add_argument("--log-level=3")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])


class FileDownloader:
    """Contains main program functionality."""

    def __init__(self: "FileDownloader", browser_type: str) -> None:
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
        self.browser_type = browser_type
        self.config = self.load_config()
        self.driver_path = self.get_driver_path()

        if not self.webdriver_exists(self.driver_path):
            self.webdriver_error()
            sys.exit(1)
        self.web_driver_manager = WebDriverManager(browser_type, self.driver_path)

    def webdriver_error(self) -> None:
        """Print error message and exit."""
        console.print(f"\n[red]Failed to initialize WebDriver for {self.browser_type}.")
        logging.error(f"Failed to initialize WebDriver for {self.browser_type}.")
        console.print("[yellow]Please verify the path in config.json is correct.")
        console.print("Download the WebDriver from the following URLs based on your browser:")
        console.print("- Chrome: https://chromedriver.chromium.org/downloads")
        console.print("- Edge: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/")
        console.print("- Firefox: https://github.com/mozilla/geckodriver")
        console.print("[yellow]Ensure the WebDriver version matches your browser version.")
        logging.error("Exiting due to missing WebDriver.")
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
            filename, _download_path, _extension = self.extract_file_info(download_info.download_url)

            if download_info.download_path.resolve().exists():
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
                if download_info.extension and download_info.extension.lower().endswith(download_info.filetype.lower()):
                    console.print(f"[green][+] Downloading: {download_info.download_path.name}")
                    async with aiofiles.open(download_info.download_path, "wb") as fileobj:
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
            # Wait up to 5 seconds until the body tag is found and page is loaded
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

        async with aiohttp.ClientSession() as session:
            console.print(f"\n[cyan][*] Locating '{filetype}' files...")

            # Use run_selenium_in_thread to fetch HTML content
            html = self.run_selenium_in_thread(url)

            tasks = []
            semaphore = asyncio.Semaphore(max_concurrent_downloads)
            failed_downloads = []

            # Check if the HTML page was retrieved successfully.
            if html is not None:
                async for urlitem in self.link_parser(url, filetype, html):
                    _filename, download_path, extension = self.extract_file_info(urlitem)
                    download_info = DownloadInfo(session, urlitem, download_path, extension, filetype, failed_downloads)
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
                    _filename, download_path, extension = self.extract_file_info(failed)
                    download_info = DownloadInfo(session, failed, download_path, extension, filetype, [])
                    task = asyncio.create_task(self.downloader(semaphore, download_info))
                    tasks.append(task)

                await asyncio.gather(*tasks)
