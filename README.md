# Web File Downloader

This program is designed to download files of a specific type from a web-hosted source. Uses the Python asyncio library to provide asynchronous downloading of multiple files simultaneously.

## Requirements

- Python 3.8+
- aiohttp
- async_timeout
- aiofiles
- beautifulsoup4
- rich

These requirements can be installed using pip by running the following command:

`pip install aiohttp async-timeout aiofiles beautifulsoup4 rich`
or
`pip install -r requirements.txt`

## Usage

`python web_file_downloader.py <URL> <FILE_TYPE>`

Where:

- **\<URL\>** is the web URL of the webpage containing the files you wish to download.
- **\<FILE_TYPE\>** is the file extension (excluding the dot '.') of the files you wish to download.

### Example Usage

To download all the `.pdf` files on `https://www.example.com/documents` run the command:

`python web_file_downloader.py https://www.example.com/documents pdf`

## Output

The downloaded files are saved in the `Downloads` folder created in the directory where the `web_file_downloader.py` script is located. If a file with the same name already exists in the folder, the program will skip downloading that file.

The program outputs a status message for each file it attempts to download, including whether the download was successful or not. The program also logs all errors to a file called `error_log.log` located in the same directory as the script.

If a file download fails, the program will retry the download after it has completed downloading all other files.

## License

This program is licensed under the MIT License. For more information, please see the `LICENSE` file.
