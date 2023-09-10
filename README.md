# Web File Downloader

Download files of a specific type from a web-hosted source. Uses the Python asyncio library for asynchronous downloading of multiple files simultaneously.

## Requirements

- Python 3.9+
- [Poetry](https://python-poetry.org/) for dependency management

## Installation

1. Clone the repository:

```text
git clone https://github.com/dfirsec/web_file_downloader.git
```

2. Change to the project directory:

```text
cd web_file_downloader
```

3. Install required packages using poetry:

```text
pip install poetry

poetry install
```

## Usage

`python wfd.py <URL> <FILE_TYPE>`

Where:

- **\<URL\>** is the web URL of the webpage containing the files you wish to download.
- **\<FILE_TYPE\>** is the file extension (excluding the dot '.') of the files you wish to download.

### Example Usage

To download all the `.pdf` files on `https://www.example.com/documents` run the command:

```text
python wfd.py https://www.example.com/documents pdf

  _____                 _____       _____
 |\    \   _____   ____|\    \  ___|\    \
 | |    | /    /| |    | \    \|    |\    \
 \/     / |    || |    |______/|    | |    |
 /     /_  \   \/ |    |----'\ |    | |    |
|     // \  \   \ |    |_____/ |    | |    |
|    |/   \ |    ||    |       |    | |    |
|\ ___/\   \|   /||____|       |____|/____/|
| |   | \______/ ||    |       |    /    | |
 \|___|/\ |    | ||____|       |____|____|/
    \(   \|____|/   )/           \(    )/
     '      )/      '             '    '
            '

[*] Locating 'pdf' files...
[+] Downloading: Document5.pdf
[+] Downloading: Document6.pdf
[+] Downloading: Document7.pdf
[+] Downloading: Document8.pdf
[+] Downloading: Document9.pdf
[+] Downloading: Document10.pdf
[-] File already exists: Document1.pdf
[-] File already exists: Document2.pdf
[-] File already exists: Document3.pdf
[-] File already exists: Document4.pdf
```

## Output

The downloaded files are saved in the `Downloads` folder created in the directory where the `web_file_downloader.py` script is located. If a file with the same name already exists in the folder, the program will skip downloading that file.

The program outputs a status message for each file it attempts to download, including whether the download was successful or not. The program also logs all errors to a file called `errors.log` located in the same directory as the script.

If a file download fails, the program will retry the download after it has completed downloading all other files.

## Dependencies

- **aiofiles**: For asynchronous file read/write operations.
- **aiohttp**: For making asynchronous HTTP requests.
- **async-timeout**: For adding timeouts to asynchronous operations.
- **beautifulsoup4**: For parsing HTML and extracting data.
- **fake-useragent**: For generating random user-agent strings.
- **lxml**: For parsing XML and HTML files.
- **requests**: For making synchronous HTTP requests.
- **rich**: For rich console output.

## License

This program is licensed under the MIT License. For more information, please see the `LICENSE` file.

## Credits

The banner text used in the script is courtesy of [Manytools](https://manytools.org/hacker-tools/ascii-banner/).
