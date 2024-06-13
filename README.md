# Web File Downloader

Download files of a specific type from a web-hosted source. Uses the Python trio library for asynchronous downloading of multiple files simultaneously and Selenium WebDriver for handling dynamic web pages.

## Requirements

- Python 3.10+
- [Poetry](https://python-poetry.org/) for dependency management.

## Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/dfirsec/web_file_downloader.git
    ```

2. Change to the project directory:

    ```sh
    cd web_file_downloader
    ```

3. Install required packages using Poetry:

    ```sh
    pip install poetry
    poetry install
    ```

## Usage

```sh
python wfd.py <URL> <FILE_TYPE>
```

Where:

- **\<URL\>** is the web URL of the webpage containing the files you wish to download.
- **\<FILE_TYPE\>** is the file extension (excluding the dot '.') of the files you wish to download.

### Example Usage

To download all the `.pdf` files from `https://www.example.com/documents` run the command:

```sh
python wfd.py https://www.example.com/documents pdf
```

```text
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

The downloaded files are saved in the `downloads` folder created in the directory where the `wfd.py` script is located. If a file with the same name already exists in the folder, it will skip downloading that file.

A `logs` directory is created at initialization.

A status message is reported for each file it attempts to download, including whether the download was successful or not. All errors are logged to a file called `errors.log` located in the `logs` directory.

If a file download fails, a retry attempt of the download will occur after all other files have been downloaded.

A log file of successful downloads is written to a file called `downloads.log` located in the `logs` directory.

## WebDriver Management

Uses Selenium WebDriver to handle dynamic web content. Ensure the appropriate WebDriver is installed and correctly configured in the `settings.toml` file.  Also, ensure to enter your preferred browser, e.g. `preferred_browser = "edge"`.

### Recommended WebDriver Locations

Common practice is to place the WebDrivers in a directory included in your system's PATH or a dedicated directory within the project.

1. **System PATH**: Add the WebDriver executables to a directory that is included in your system's PATH. This allows them to be accessible from any location without specifying the full path.

    - **Windows**: `C:\WebDrivers\`
    - **macOS/Linux**: `/usr/local/bin/`

2. **Project Directory**: Store the WebDriver executables in a dedicated directory within the project. Update the `settings.toml` file to reflect the correct paths.

    - **Example**: `web_file_downloader/drivers/`

### Download WebDrivers

Download the appropriate WebDriver for your browser from the following links:

- Edge: <https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/>
- Firefox: <https://github.com/mozilla/geckodriver>
- Chrome: <https://chromedriver.chromium.org/downloads>

Ensure the WebDriver version matches your browser version.

## Dependencies

- **beautifulsoup4**: For parsing HTML and extracting data.
- **dynaconf**: For parsing webdriver configuration.
- **fake-useragent**: For generating random user-agent strings.
- **httpx**: For making asynchronous HTTP requests.
- **lxml**: For parsing XML and HTML files.
- **requests**: For making synchronous HTTP requests.
- **rich**: For rich console output.
- **selenium**: Browser automation for dynamic web content.
- **trio**:  For async concurrency and I/O

## License

This program is licensed under the MIT License. For more information, please see the `LICENSE` file.

## Credits

The banner text used in the script is courtesy of [Manytools](https://manytools.org/hacker-tools/ascii-banner/).
