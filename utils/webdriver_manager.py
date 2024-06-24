"""This module contains the WebDriverManager class."""

import platform
from pathlib import Path

from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService

from .custom_exceptions import UnsupportedBrowserTypeError
from .logger_util import logs_dir


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

        if platform.system() == "Windows":
            # disable popen creation flag 'DevTools listening on ws://127.0.0.1...'
            edge_service = EdgeService(
                executable_path=self.driver_path,
                service_args=[f"--log-path={edge_log_path!s}"],
                popen_kw={"creation_flags": 0x08000000},
            )
        else:
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
