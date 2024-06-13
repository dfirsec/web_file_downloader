"""Configuration file for webdrivers."""

from pathlib import Path

from dynaconf import Dynaconf

settings_file_path = Path(__file__).parent.parent / "settings.toml"

# Load settings using Dynaconf
settings = Dynaconf(
    settings_files=[str(settings_file_path)],
)

# Extract default settings
default_settings = settings.get("default")

