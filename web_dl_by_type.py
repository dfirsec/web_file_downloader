import asyncio
import os
import platform
import sys
from pathlib import Path
from urllib.parse import urljoin

import aiofiles
import aiohttp
import async_timeout
import requests
import validators
from bs4 import BeautifulSoup

__author__ = "DFIRSec (@pulsecode)"
__version__ = "0.1"
__description__ = "Download web hosted files by filetype/file extension."

root = Path(__file__).parent.resolve()
filepath = root.joinpath("Downloads")
filepath.mkdir(parents=True, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
}


def link_parser(req_url, filetype):
    """
    Takes a URL and a file type as arguments, and returns a generator object that yields all the
    links on the page that end with the specified file type

    :param req_url: The URL of the page you want to scrape
    :param ftype: the file type you want to download
    """
    try:
        response = requests.get(req_url, headers=headers)
        response.raise_for_status()
    except (ConnectionError, requests.exceptions.HTTPError) as error:
        sys.exit(f"[x] {error}")
    else:
        soup = BeautifulSoup(response.text, "lxml")
        if results := [link.get("href") for link in soup.find_all("a") if link.get("href") is not None]:
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
        async with session.get(download_url, headers=headers) as response:
            filename = os.path.basename(download_url)
            dlpath = Path(filepath / filename)
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


async def main(url, filetype):
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

    if sys.version_info.minor < 7:
        print(f"[!] Tested on Python version 3.7+. May not work with {platform.python_version()}\n")

    if len(sys.argv) < 3:
        sys.exit(f"Usage: python {os.path.basename(__file__)} <URL> <FILE TYPE>")
    else:
        mainurl = sys.argv[1]
        ftype = sys.argv[2]

    if not validators.url(mainurl):  # type: ignore
        sys.exit(f"[!] {mainurl} is not a valid URL")

    # Resolves issue: https://github.com/encode/httpx/issues/914
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main(mainurl, ftype))
