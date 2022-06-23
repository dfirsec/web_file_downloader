import asyncio
import os
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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
}


def link_parser(req_url, filetype):
    """
    Takes a URL and a file type as arguments, and returns a generator object that yields all the
    links on the page that end with the specified file type

    :param req_url: The URL of the page you want to scrape
    :param ftype: the file type you want to download
    """

    response = requests.get(req_url, headers=headers)
    soup = BeautifulSoup(response.text, "lxml")
    links = soup.find_all("a", href=True)
    results = [x["href"] for x in links]

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
            async with aiofiles.open(filepath / filename, "wb") as fileobj:
                while True:
                    chunk = await response.content.read(1024)
                    if not chunk:
                        break
                    await fileobj.write(chunk)
            return await response.release()


async def main(url, filetype):
    """
    Takes a URL and a file type as arguments, and downloads all files of that type from the URL

    :param url: The URL of the page you want to download from
    :param ftype: The file type you want to download
    """
    if urls := list(link_parser(url, filetype)):
        async with aiohttp.ClientSession() as session:
            for urlitem in urls:
                print(f"[+] Downloading: {urlitem.split('/')[-1]}")
                await downloader(session, urlitem)
    else:
        print(f"[x] File type '{filetype}' does not appear to be available.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(f"Usage: python {os.path.basename(__file__)} <URL> <FILE TYPE>")
    else:
        mainurl = sys.argv[1]
        ftype = sys.argv[2]

    if not validators.url(mainurl):  # type: ignore
        sys.exit(f"[!] {mainurl} is not a valid URL")

    asyncio.run(main(mainurl, ftype))
